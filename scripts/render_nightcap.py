#!/usr/bin/env python3
"""Render a nightcap list (local drinks and snacks) from JSON to Markdown.

Checks each item's image candidates in order and keeps the first one that loads
as an image, rewrites it to a GitHub image proxy URL so chat apps that only trust
a few image hosts show it, computes grams of pure alcohol per container, and prints Markdown
for the chat. Warnings go to stderr.

Usage:
    python3 scripts/render_nightcap.py list.json
    python3 scripts/render_nightcap.py list.json -o list.md --no-check-images
"""

from __future__ import annotations

import argparse
import concurrent.futures
import json
import os
import re
import sys
import urllib.error
import urllib.request

ETHANOL_DENSITY = 0.789
GRAMS_PER_DRINK = 10
USER_AGENT = (
    "Mozilla/5.0 (iPhone; CPU iPhone OS 18_0 like Mac OS X) AppleWebKit/605.1.15 "
    "(KHTML, like Gecko) Version/18.0 Mobile/15E148 Safari/604.1"
)
IMAGE_REQUEST_HEADERS = {
    "User-Agent": USER_AGENT,
    "Accept": "image/webp,image/png,image/jpeg,image/*;q=0.8",
    "Referer": "https://example.com/",
    "Sec-Fetch-Dest": "image",
    "Sec-Fetch-Mode": "no-cors",
    "Sec-Fetch-Site": "cross-site",
}
EMBEDDABLE_TYPES = {"image/jpeg", "image/png", "image/gif", "image/webp"}
MAX_IMAGE_BYTES = 1_500_000
GITHUB_MARKDOWN_API = "https://api.github.com/markdown"

DEFAULT_LABELS = {
    "buying_rules": "Buying rules",
    "drinks": "Drinks",
    "snacks": "Snacks",
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


def sniff_image(head: bytes) -> bool:
    return (
        head.startswith(b"\xff\xd8\xff")
        or head.startswith(b"\x89PNG\r\n\x1a\n")
        or head.startswith((b"GIF87a", b"GIF89a"))
        or (head[:4] == b"RIFF" and head[8:12] == b"WEBP")
    )


def check_image(url: str, timeout: float) -> tuple[str, str, str]:
    """Return (result, final_url, reason). result is "ok", "bad" or "unreachable".

    The request imitates a chat app embedding the image from another site, so images
    that only load on their own site (hotlink protection, Cross-Origin-Resource-Policy)
    are rejected. The final URL after redirects is returned, because some chat apps do
    not follow redirects for embedded images.
    """
    if not url.startswith("https://"):
        return "bad", url, "not https (many chat apps block http images)"
    request = urllib.request.Request(md_url(url), headers=IMAGE_REQUEST_HEADERS)
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            final_url = response.geturl()
            content_type = response.headers.get("Content-Type", "").split(";")[0].strip().lower()
            corp = response.headers.get("Cross-Origin-Resource-Policy", "").strip().lower()
            length = response.headers.get("Content-Length", "")
            if not final_url.startswith("https://"):
                return "bad", final_url, "redirects to http"
            if content_type not in EMBEDDABLE_TYPES:
                return "bad", final_url, f"content type {content_type or 'missing'}"
            if corp in ("same-origin", "same-site"):
                return "bad", final_url, f"Cross-Origin-Resource-Policy: {corp}"
            if length.isdigit() and int(length) > MAX_IMAGE_BYTES:
                return "bad", final_url, f"too large ({int(length) // 1024} KB); use a smaller thumbnail"
            if not sniff_image(response.read(16)):
                return "bad", final_url, "body is not an image"
            return "ok", final_url, ""
    except urllib.error.HTTPError as error:
        return "bad", url, f"HTTP {error.code}"
    except ValueError as error:
        return "bad", url, str(error)
    except (urllib.error.URLError, TimeoutError, OSError):
        return "unreachable", url, "could not be reached"


def github_proxy_url(url: str, timeout: float) -> str | None:
    """Return GitHub's camo proxy URL for an image, or None if GitHub can't be reached.

    Some chat apps, often on mobile and web, only load images from an allowlist of
    hosts, and camo.githubusercontent.com is commonly on it. GitHub's Markdown API
    rewrites image URLs to signed camo URLs without uploading anything.
    """
    headers = {"Accept": "application/vnd.github+json", "User-Agent": "travel-nightcap-from-local-shops"}
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    body = json.dumps({"text": f"![]({md_url(url)})", "mode": "gfm"}).encode()
    request = urllib.request.Request(GITHUB_MARKDOWN_API, data=body, headers=headers)
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            html = response.read().decode("utf-8", "replace")
    except (urllib.error.URLError, TimeoutError, OSError) as error:
        warn(f"GitHub Markdown API failed ({error}); photos may not show in apps that only trust a few image hosts")
        return None
    match = re.search(r'<img src="(https://camo\.githubusercontent\.com/[^"]+)"', html)
    return match.group(1) if match else None


def choose_images(items: list[dict], check: bool, proxy: bool, timeout: float) -> dict[str, str | None]:
    chosen: dict[str, str | None] = {}
    if not check:
        for item in items:
            images = item.get("images") or []
            chosen[item["id"]] = images[0] if images else None
        return chosen

    def first_working(item: dict) -> tuple[str | None, list[str]]:
        results = []
        for url in item.get("images") or []:
            result, final_url, reason = check_image(url, timeout)
            results.append(result)
            if result != "ok":
                warn(f"{item['id']}: image rejected ({reason}): {url}")
                continue
            if not proxy:
                return final_url, results
            camo_url = github_proxy_url(final_url, timeout)
            if camo_url is None:
                return final_url, results
            camo_result, _, camo_reason = check_image(camo_url, timeout)
            if camo_result == "ok":
                return camo_url, results
            warn(f"{item['id']}: GitHub's image proxy can't load it ({camo_reason}): {url}")
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
    labels: dict,
) -> list[str]:
    lines = [f"### {item['name']}", ""]
    alt = item.get("local_name") or item["name"]
    if image:
        lines += [f"![{alt}]({md_url(image)})", ""]
    else:
        warn(f"{item['id']}: no working image; find one (see Photos in SKILL.md) and rerun")

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


def render(data: dict, check_images: bool, proxy_images: bool, timeout: float) -> str:
    labels = {**DEFAULT_LABELS, **(data.get("labels") or {})}
    sources = data.get("sources") or []
    used = [s for s in sources if s.get("status") == "used" and s.get("url")]
    rejected = [s for s in sources if s.get("status") == "rejected"]
    source_numbers = {s["url"]: i for i, s in enumerate(used, start=1)}

    drinks = keep_items(data.get("drinks") or [], set(source_numbers), "drinks")
    snacks = keep_items(data.get("snacks") or [], set(source_numbers), "snacks")
    names_by_id = {item["id"]: item["name"] for item in drinks + snacks}
    images = choose_images(drinks + snacks, check_images, proxy_images, timeout)

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
            out += render_card(item, is_drink, images.get(item["id"]), names_by_id, source_numbers, labels)

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
    parser.add_argument(
        "--no-proxy", action="store_true",
        help="output original image URLs instead of GitHub proxy URLs (photos may then not show in apps that only trust a few image hosts)",
    )
    parser.add_argument("--timeout", type=float, default=8.0, help="seconds per image request (default 8)")
    args = parser.parse_args()

    with open(args.input, encoding="utf-8") as f:
        data = json.load(f)

    markdown = render(data, not args.no_check_images, not args.no_proxy, args.timeout)
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(markdown)
    else:
        sys.stdout.write(markdown)
    return 0


if __name__ == "__main__":
    sys.exit(main())
