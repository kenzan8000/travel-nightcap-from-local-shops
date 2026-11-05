#!/usr/bin/env python3
"""Render a nightcap list (local drinks and snacks) from JSON to Markdown.

Checks each item's image candidates in order and keeps the first one that loads
as an image, computes grams of pure alcohol per container, and prints Markdown
for the chat. Warnings go to stderr.

Usage:
    python3 scripts/render_nightcap.py list.json
    python3 scripts/render_nightcap.py list.json -o list.md --no-check-images
"""

from __future__ import annotations

import argparse
import concurrent.futures
import json
import sys
import urllib.error
import urllib.parse
import urllib.request

ETHANOL_DENSITY = 0.789
GRAMS_PER_DRINK = 10
USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
)

DEFAULT_LABELS = {
    "buying_rules": "Buying rules",
    "drinks": "Drinks",
    "snacks": "Snacks",
    "shop_phrases": "Shop phrases",
    "sources": "Sources",
    "rejected_sources": "Rejected sources",
    "typically": "typically",
    "drinks_unit": "drinks",
    "alcohol_note": "g = grams of pure alcohol per container; 1 drink = {grams} g.",
    "sizes": "Sizes",
    "where_to_buy": "Where to buy",
    "opening": "Opening",
    "made_from": "Made from",
    "how_made": "How it's made",
    "taste": "Taste",
    "goes_with": "Goes with",
    "look_for": "Look for on the label",
    "examples": "Examples",
    "tips": "From the sources",
    "local_terms": "Local terms",
    "item_sources": "Sources",
    "image_search": "Image search",
}


def warn(message: str) -> None:
    print(f"warning: {message}", file=sys.stderr)


def md_url(url: str) -> str:
    return url.replace(" ", "%20").replace("(", "%28").replace(")", "%29")


def abv_bounds(abv: object) -> tuple[float, float] | None:
    if isinstance(abv, (int, float)):
        return float(abv), float(abv)
    if isinstance(abv, list) and len(abv) == 2 and all(isinstance(x, (int, float)) for x in abv):
        low, high = sorted(float(x) for x in abv)
        return low, high
    return None


def fmt_number(value: float) -> str:
    return f"{value:.1f}".rstrip("0").rstrip(".")


def fmt_abv(abv: object, labels: dict) -> str:
    bounds = abv_bounds(abv)
    if bounds is None:
        return ""
    low, high = bounds
    if low == high:
        return f"{fmt_number(low)}%"
    return f"{labels['typically']} {fmt_number(low)}-{fmt_number(high)}%"


def alcohol_grams(ml: object, abv: object) -> tuple[float, float] | None:
    bounds = abv_bounds(abv)
    if bounds is None or not isinstance(ml, (int, float)):
        return None
    return tuple(ml * pct / 100 * ETHANOL_DENSITY for pct in bounds)  # type: ignore[return-value]


def fmt_grams(grams: tuple[float, float] | None, with_drinks: bool, labels: dict) -> str:
    if grams is None:
        return ""
    low, high = (round(g) for g in grams)
    text = f"≈{low} g" if low == high else f"≈{low}-{high} g"
    if with_drinks:
        d_low, d_high = (fmt_number(g / GRAMS_PER_DRINK) for g in grams)
        drinks = d_low if d_low == d_high else f"{d_low}-{d_high}"
        text += f", {drinks} {labels['drinks_unit']}"
    return text


def size_label(size: dict) -> str:
    parts = []
    if isinstance(size.get("ml"), (int, float)):
        parts.append(f"{fmt_number(size['ml'])} ml")
    if size.get("label"):
        parts.append(str(size["label"]))
    if size.get("container"):
        parts.append(str(size["container"]))
    return " ".join(parts)


def check_image(url: str, timeout: float) -> str:
    """Return "ok", "bad" (the server answered, but not with an image) or "unreachable"."""
    request = urllib.request.Request(
        url, headers={"User-Agent": USER_AGENT, "Range": "bytes=0-2047", "Accept": "image/*"}
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            content_type = response.headers.get("Content-Type", "")
            if response.status not in (200, 206) or not content_type.startswith("image/"):
                return "bad"
            return "ok" if response.read(64) else "bad"
    except (urllib.error.HTTPError, ValueError):
        return "bad"
    except (urllib.error.URLError, TimeoutError, OSError):
        return "unreachable"


def choose_images(items: list[dict], check: bool, timeout: float) -> dict[str, str | None]:
    chosen: dict[str, str | None] = {}
    if not check:
        for item in items:
            images = item.get("images") or []
            chosen[item["id"]] = images[0] if images else None
        return chosen

    def first_working(item: dict) -> tuple[str | None, list[str]]:
        results = []
        for url in item.get("images") or []:
            result = check_image(url, timeout)
            results.append(result)
            if result == "ok":
                return url, results
            warn(f"{item['id']}: image {'could not be reached' if result == 'unreachable' else 'did not load as an image'}: {url}")
        return None, results

    all_results: list[str] = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
        for item, (url, results) in zip(items, pool.map(first_working, items)):
            chosen[item["id"]] = url
            all_results += results
    if all_results and all(r == "unreachable" for r in all_results):
        warn(
            "no image could be reached; this environment may have no network access. "
            "Check the image URLs with your own browsing tool, keep only working ones, "
            "and rerun with --no-check-images."
        )
    return chosen


def image_search_url(item: dict, place: dict) -> str:
    query = item.get("image_search_query") or f"{item.get('local_name') or item['name']} {place.get('query', '')}"
    return "https://www.google.com/search?tbm=isch&q=" + urllib.parse.quote_plus(query.strip())


def terms_text(terms: list[dict]) -> str:
    out = []
    for term in terms:
        text = f"*{term.get('term', '')}* = {term.get('meaning', '')}"
        if term.get("pronunciation"):
            text += f" ({term['pronunciation']})"
        out.append(text)
    return "; ".join(out)


def render_overview(items: list[dict], is_drink: bool, labels: dict) -> list[str]:
    lines = []
    for number, item in enumerate(items, start=1):
        parts = [item.get("type", "")]
        if is_drink:
            parts.append(fmt_abv(item.get("abv"), labels))
        sizes = item.get("sizes") or []
        if sizes:
            first = sizes[0]
            size_text = " ".join(x for x in (size_label(first), str(first.get("price", ""))) if x)
            if is_drink:
                grams = fmt_grams(alcohol_grams(first.get("ml"), item.get("abv")), False, labels)
                if grams:
                    size_text += f" ({grams})"
            parts.append(size_text)
        elif item.get("pack_size") or item.get("price"):
            parts.append(" ".join(x for x in (item.get("pack_size"), item.get("price")) if x))
        summary = " · ".join(x for x in parts if x)
        lines.append(f"{number}. **{item['name']}**" + (f": {summary}" if summary else ""))
    if is_drink:
        lines += ["", "*" + labels["alcohol_note"].format(grams=GRAMS_PER_DRINK) + "*"]
    return lines


def render_card(
    item: dict,
    is_drink: bool,
    image: str | None,
    names_by_id: dict[str, str],
    source_numbers: dict[str, int],
    place: dict,
    labels: dict,
) -> list[str]:
    lines = [f"### {item['name']}", ""]
    alt = item.get("local_name") or item["name"]
    if image:
        lines += [f"![{alt}]({md_url(image)})", ""]
    else:
        lines += [f"[{labels['image_search']}: {alt}]({image_search_url(item, place)})", ""]

    summary = [item.get("type", "")]
    if is_drink:
        summary.append(fmt_abv(item.get("abv"), labels))
    maker = item.get("producer") or item.get("maker")
    origin = item.get("origin")
    summary.append(", ".join(x for x in (maker, origin) if x))
    summary_text = " · ".join(x for x in summary if x)
    if summary_text:
        lines += [f"*{summary_text}*", ""]

    bullets: list[tuple[str, str]] = []
    sizes = item.get("sizes") or []
    if sizes:
        parts = []
        for size in sizes:
            text = size_label(size)
            if size.get("price"):
                text += f" {size['price']}"
            if is_drink:
                grams = fmt_grams(alcohol_grams(size.get("ml"), item.get("abv")), True, labels)
                if grams:
                    text += f" ({grams})"
            parts.append(text.strip())
        bullets.append((labels["sizes"], "; ".join(parts)))
    elif item.get("pack_size") or item.get("price"):
        bullets.append((labels["sizes"], " ".join(x for x in (item.get("pack_size"), item.get("price")) if x)))

    for key, label in (("where_to_buy", "where_to_buy"), ("opening", "opening"), ("made_from", "made_from"),
                       ("how_made", "how_made"), ("taste", "taste")):
        if item.get(key):
            bullets.append((labels[label], str(item[key])))

    pairs = []
    for other in item.get("pairs_with") or []:
        if other in names_by_id:
            pairs.append(names_by_id[other])
        else:
            warn(f"{item['id']}: pairs_with refers to unknown id '{other}'")
    if pairs:
        bullets.append((labels["goes_with"], ", ".join(pairs)))

    if item.get("label_hints"):
        bullets.append((labels["look_for"], terms_text(item["label_hints"])))
    if item.get("examples"):
        bullets.append((labels["examples"], ", ".join(item["examples"])))
    if item.get("tips"):
        bullets.append((labels["tips"], str(item["tips"])))
    if item.get("local_terms"):
        bullets.append((labels["local_terms"], terms_text(item["local_terms"])))

    refs = [f"[{source_numbers[url]}]({md_url(url)})" for url in item.get("sources") or [] if url in source_numbers]
    if refs:
        bullets.append((labels["item_sources"], " ".join(refs)))

    lines += [f"- **{label}:** {text}" for label, text in bullets]
    lines.append("")
    return lines


def keep_items(items: list[dict], used_urls: set[str], kind: str) -> list[dict]:
    kept = []
    seen_ids = set()
    for index, item in enumerate(items):
        if not item.get("id") or not item.get("name"):
            warn(f"{kind}[{index}]: missing id or name, left out")
            continue
        if item["id"] in seen_ids:
            warn(f"{item['id']}: duplicate id, left out")
            continue
        if not any(url in used_urls for url in item.get("sources") or []):
            warn(f"{item['id']}: no used source, left out")
            continue
        if kind == "drinks" and abv_bounds(item.get("abv")) is None:
            warn(f"{item['id']}: abv missing or not a number/[low, high]; alcohol not computed")
        seen_ids.add(item["id"])
        kept.append(item)
    return kept


def render(data: dict, check_images: bool, timeout: float) -> str:
    labels = {**DEFAULT_LABELS, **(data.get("labels") or {})}
    place = data.get("place") or {}
    sources = data.get("sources") or []
    used = [s for s in sources if s.get("status") == "used" and s.get("url")]
    rejected = [s for s in sources if s.get("status") == "rejected"]
    source_numbers = {s["url"]: i for i, s in enumerate(used, start=1)}

    drinks = keep_items(data.get("drinks") or [], set(source_numbers), "drinks")
    snacks = keep_items(data.get("snacks") or [], set(source_numbers), "snacks")
    names_by_id = {item["id"]: item["name"] for item in drinks + snacks}
    images = choose_images(drinks + snacks, check_images, timeout)

    out: list[str] = []

    if data.get("buying_rules"):
        out += [f"## {labels['buying_rules']}", ""]
        out += [f"- {rule}" for rule in data["buying_rules"]]
        out.append("")

    for key, is_drink, items in (("drinks", True, drinks), ("snacks", False, snacks)):
        if not items:
            continue
        out += [f"## {labels[key]}", ""]
        out += render_overview(items, is_drink, labels)
        out.append("")
        for item in items:
            out += render_card(item, is_drink, images.get(item["id"]), names_by_id, source_numbers, place, labels)

    if data.get("shop_phrases"):
        out += [f"## {labels['shop_phrases']}", ""]
        for phrase in data["shop_phrases"]:
            text = f"- **{phrase.get('phrase', '')}**"
            if phrase.get("pronunciation"):
                text += f" ({phrase['pronunciation']})"
            if phrase.get("meaning"):
                text += f": {phrase['meaning']}"
            out.append(text)
        out.append("")

    if used:
        out += [f"## {labels['sources']}", ""]
        for number, source in enumerate(used, start=1):
            details = ", ".join(str(source[k]) for k in ("author", "date", "kind") if source.get(k))
            text = f"{number}. [{source.get('title') or source['url']}]({md_url(source['url'])})"
            if details:
                text += f": {details}"
            out.append(text)
        out.append("")

    if rejected:
        out += [f"### {labels['rejected_sources']}", ""]
        for source in rejected:
            title = source.get("title") or source.get("url", "")
            link = f"[{title}]({md_url(source['url'])})" if source.get("url") else title
            out.append(f"- {link}: {source.get('reason', '')}")
        out.append("")

    return "\n".join(out).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("input", help="nightcap list JSON")
    parser.add_argument("-o", "--output", help="write Markdown here instead of stdout")
    parser.add_argument("--no-check-images", action="store_true", help="use the first image candidate unchecked")
    parser.add_argument("--timeout", type=float, default=8.0, help="seconds per image request (default 8)")
    args = parser.parse_args()

    with open(args.input, encoding="utf-8") as f:
        data = json.load(f)

    markdown = render(data, not args.no_check_images, args.timeout)
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(markdown)
    else:
        sys.stdout.write(markdown)
    return 0


if __name__ == "__main__":
    sys.exit(main())
