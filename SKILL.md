---
name: travel-nightcap-from-local-shops
description: On a trip, list the local alcoholic drinks and snacks worth buying at a local supermarket, liquor shop or kiosk to enjoy in the hotel room in the evening, sourced from first-hand writing by locals and travellers. Each item has a photo, ABV, sizes, a rough local price, grams of alcohol per container, what it is made from and how. Use when the user wants an evening drink, nightcap, local beer, wine or snacks to buy at a shop during a trip. The place name may come later; if it is not given, ask for it in the chat.
---

# Nightcap from local shops on a trip

Turn a place name into a list, shown in the chat, of local alcoholic drinks and snacks
the user can buy at a local shop and enjoy in their hotel room that evening. Every item
comes from real posts by residents or people who travelled there.

These are everyday purchases for one evening, not souvenirs. Favour what a local would
pick up on the way home: everyday prices and sizes one person can finish in an evening.

The user is usually already on the trip, often reading on a phone, and wants the list
soon. Keep the research focused and the output narrow: no wide tables.

**A missing fact is better than a wrong fact. A missing link is better than a guessed
link.** Never invent ABV, sizes, prices, ingredients or URLs.

These instructions are agent-neutral. "Search the web", "open the page" and "run the
command" mean whatever tools your environment provides. If you cannot run scripts,
follow the manual path in Step 7.

## Step 1: Ask for the place in the chat and wait

- If the user's message already names a place, use it and go to Step 2.
- Otherwise, your whole reply is one short question in the chat, in the user's
  language. For example:

  > Where are you staying? A city, town or region is enough. Add the country if the
  > name could mean more than one place.

- Ask as ordinary chat text, then stop and wait. Do not search or guess first.
- If the name is ambiguous (Portland, Victoria, San José), ask which one.
- Ask nothing else: not drink preferences, number of people, budget or diet.
- Note the **user's language** (the language they write in) and the **local
  language(s)** of the place. Write the list in the user's language; local names and
  terms come from the local language.

## Step 2: Find first-hand sources

Search in the user's language and the local language. When neither is English, also
search in English, which usually has more first-hand posts. Use several phrasings, for
example (translate and adapt them; the local-language ones here are Finnish):

- `what to drink in <place>`, `<place> local beer supermarket`, `<place> craft beer shop`
- `<place> supermarket snacks to try`, `<place> local snacks to buy`
- `<place> wine shop local wine`, `<country> liquor store rules`
- local language: `paras kauppaolut`, `suomalaiset herkut kaupasta`, `asun <place>`
- forum and community threads (Reddit, local forums) when they contain detail

Open and read the posts, not just the search snippets. Aim for 3 to 5 distinct
first-hand sources; for small places accept however many genuinely exist.

**Keep** a source when it is first-person ("we bought", "I've lived here ten years"),
shows the author was there (own photos, specific details), and has an identifiable
author or publication.

**Reject** shop and review aggregators, AI-generated or SEO listicles, pages with no
author, and content that only rewrites other sites. Log every source you opened, kept
or rejected, with a one-line reason.

## Step 3: Extract drinks and snacks

Collect what the sources recommend buying in a shop. Skip what is only served in bars
or restaurants.

Decide each item's `kind`:

- `product`: one specific, widely sold brand, for example Sandels beer in Finnish
  shops. Use this when the sources name it and shoppers will find exactly that product.
- `style`: a category with many interchangeable products, for example local wine,
  cheese or rye crisps. Describe what is popular ("dry white wine is popular here"), what
  to look for on the label, and give 1 to 3 example products only if sources or
  retailer listings name them.

For each item record what the source authors said and the URL of every kept source
that mentions it. Merge duplicates across sources and keep all their URLs.

Drinks can be anything alcoholic sold locally: beer, cider, long drinks, wine, sake,
spirits, and so on. For strong alcohol prefer small sizes (for example 50 ml or 200 ml
bottles), but larger ones can be recommended too.

Snacks can be anything from a local shop, including chilled items such as cheese or
cured fish, as long as it is **ready to eat in a hotel room as bought**. There is no
kitchen: no pan, grill, oven or microwave. Leave out raw or cook-before-eating items
(fresh sausages, frozen food, instant noodles). If a dish is famous but needs cooking,
include its ready-to-eat form only when shops sell one (for example a cold-cut or
tinned version), and describe only that form.

## Step 4: Decide how many

There is no fixed number. Include what first-hand sources actually recommend, usually
about 5 to 12 drinks and 5 to 12 snacks; fewer for small places.

- Every item needs at least one kept source.
- Rank by how many independent sources mention it. Among similar items, prefer
  everyday prices and evening-sized containers over expensive or souvenir-type ones.
- List drinks and snacks in ranked order.

## Step 5: Fill in the details

Look up facts beyond the posts: the producer's site, Wikipedia (in both languages),
Wikidata, and local retailer or state liquor shop listings. Search retailer listings in
the local language; they give ABV, sizes and prices.

- `abv`: a number for a product; `[low, high]` for a style.
- `sizes`: the containers commonly sold, each with `ml`, `container` and a rough
  `price` in the local currency, such as `~2-3 EUR`. Rough is fine; no date or shop.
- `made_from`, `how_made`, `taste`: ingredients, how it is made, and what it tastes
  like, in 1 or 2 sentences each.
- `pairs_with`: ids of items in the other list that go well with it.
- `where_to_buy`: the kind of shop, for example "any supermarket" or "state liquor
  shop only".
- `opening` (drinks): can, screw cap, crown cap (needs an opener) or cork.
- `label_hints` (styles): local words to look for on the label or shelf.
- `local_terms`: useful local words from the name, with a pronunciation hint when
  useful.

Also collect, for the place:

- `buying_rules`: 2 to 5 facts that matter when buying: which shops sell which
  strength, sales hours, minimum age, can and bottle deposit. Only confirmed facts,
  from official or first-hand sources.
- `shop_phrases`: 2 to 5 local phrases or words that help in the shop.

### Photos

Every item needs a photo; the output never shows a link instead of one. List image
URLs in `images`, best first, and give each item several candidates from different
sites, because some will not embed in chat apps.

1. The official product image from the producer or a local retailer. Search in the
   local language.
2. Open Food Facts (`world.openfoodfacts.org`), which has photos of supermarket
   packs, including many drinks and condiments. Use the
   `https://images.openfoodfacts.org/images/products/...` URL of a front photo at 400 px.
3. Wikimedia Commons. Use the direct `https://upload.wikimedia.org/...` thumbnail URL
   (about 480 px wide), not the `commons.wikimedia.org/wiki/File:` page.
4. A photo from one of the source posts.

For a `style`, use a photo of a typical example, such as the pack of one of its
`examples`. If an item still has no image, keep searching in the local language
(product name plus words like "pack", "bottle", "can") before giving up.

Each URL must:

- start with `https://`;
- point directly at a JPEG, PNG, WebP or GIF file, not a web page, SVG or AVIF;
- be a thumbnail-sized file, under about 1.5 MB.

## Step 6: Write the JSON

If you can run scripts, write the list to any temporary file, for example
`/tmp/travel-nightcap-<place-slug>.json`. Nothing needs to be kept after the chat. If
you cannot write files, keep the same structure in mind and use the manual path in
Step 7.

```json
{
  "place": {"query": "Helsinki, Finland", "name": "Helsinki", "slug": "helsinki",
            "user_language": "en", "local_language": "fi", "currency": "EUR"},
  "labels": {},
  "buying_rules": ["Supermarkets sell drinks up to 5.5% ABV; stronger ones only at Alko."],
  "drinks": [
    {
      "id": "sandels", "kind": "product",
      "name": "Sandels", "local_name": "Sandels", "type": "Lager",
      "producer": "Olvi", "origin": "Iisalmi", "abv": 4.7,
      "sizes": [{"ml": 330, "container": "can", "price": "~1.5-2 EUR"}],
      "made_from": "Barley malt, hops, water",
      "how_made": "...", "taste": "...",
      "pairs_with": ["ruislastut"],
      "where_to_buy": "Any supermarket or kiosk", "opening": "Can",
      "tips": "What the source authors said.",
      "local_terms": [{"term": "olut", "meaning": "beer", "pronunciation": "OH-lut"}],
      "sources": ["https://..."],
      "images": ["https://...", "https://..."]
    }
  ],
  "snacks": [
    {
      "id": "ruislastut", "kind": "style",
      "name": "Rye crisps (ruislastut)", "local_name": "ruislastut", "type": "Savoury crisps",
      "origin": "Finland", "pack_size": "~150 g bag", "price": "~2-3 EUR",
      "made_from": "...", "how_made": "...", "taste": "...",
      "pairs_with": ["sandels"], "where_to_buy": "Any supermarket",
      "label_hints": [{"term": "ruis", "meaning": "rye"}],
      "examples": [],
      "sources": ["https://..."], "images": ["https://...", "https://..."]
    }
  ],
  "shop_phrases": [{"phrase": "Kiitos", "pronunciation": "KEE-tos", "meaning": "Thank you"}],
  "sources": [
    {"url": "https://...", "title": "...", "author": "...", "date": "2025-06-14",
     "language": "en", "kind": "traveller blog", "status": "used", "reason": "..."},
    {"url": "https://...", "title": "...", "status": "rejected", "reason": "SEO listicle"}
  ]
}
```

- `name`: the local name, with the user's-language name in brackets when it helps:
  `Finnish berry wine (marjaviini)`.
- Leave out any field you could not confirm. Do not fill it with a guess.
- `labels`: when the user's language is not English, translate the output headings.
  Keys and English defaults: `buying_rules` Buying rules, `drinks` Drinks, `snacks`
  Snacks, `shop_phrases` Shop phrases, `sources` Sources, `rejected_sources` Rejected
  sources, `typically` typically, `drinks_unit` drinks, `alcohol_note` "g = grams of
  pure alcohol per container; 1 drink = {grams} g.", `sizes` Sizes,
  `where_to_buy` Where to buy, `opening` Opening, `made_from` Made from, `how_made`
  How it's made, `taste` Taste, `goes_with` Goes with, `look_for` Look for on the
  label, `examples` Examples, `tips` From the sources, `local_terms` Local terms,
  `item_sources` Sources.

## Step 7: Render

### With the script (preferred)

The script uses only the Python 3 standard library. The path is relative to this
skill's folder.

```bash
python3 scripts/render_nightcap.py /tmp/travel-nightcap-<slug>.json
```

It prints Markdown to stdout and warnings to stderr. It:

- tries each `images` URL in order the way a chat app would embed it (from another
  site, following redirects), keeps the first that passes the rules above, and
  outputs its final direct URL;
- computes grams of pure alcohol per container (`ml × ABV / 100 × 0.789`) and drinks
  of 10 g;
- leaves out items with no used source, and warns about unknown `pairs_with` ids.

Read the warnings. Every "no working image" warning means an item would show without
a photo: add candidates from other sites in the Photos order and rerun until each
item has one. If the script says no image could be reached, the environment where you run
scripts probably has no internet access. Check the image URLs with your browsing
tool, remove the ones that do not show the item, and rerun with `--no-check-images`.

### Without the script (manual path)

1. Open each image URL; keep the first that shows the right item and follows the
   rules in Photos. Use the final URL after any redirect.
2. For each drink size, compute `ml × ABV / 100 × 0.789` grams, rounded, and divide by
   10 for drinks. For a style use the low and high ABV.
3. Write the Markdown in the layout of Step 8. Escape `(`, `)` and spaces in URLs as
   `%28`, `%29` and `%20` so links and images render.

## Step 8: Show the list in the chat

Post the rendered Markdown as your reply, in the user's language, with one short
sentence before it. Do not only point to a file. The layout is made for a phone
screen, with no tables:

1. **Buying rules**: bullets.
2. **Drinks**: a numbered overview, one line per drink with type, ABV, the first size,
   its price and grams of alcohol. Then one card per drink.
3. **Snacks**: a numbered overview, one line per snack with type, pack size and
   price. Then one card per snack.
4. **Shop phrases**.
5. **Sources**: used sources numbered, then rejected sources with reasons.

An overview line looks like this:

```markdown
1. **Sandels**: Lager · 4.7% · 330 ml can ~1.5-2 EUR (≈12 g)
```

A card looks like this:

```markdown
### Sandels

![Sandels](https://...)

*Lager · 4.7% · Olvi, Iisalmi*

- **Sizes:** 330 ml can ~1.5-2 EUR (≈12 g, 1.2 drinks)
- **Where to buy:** Any supermarket or kiosk
- **Opening:** Can
- **Made from:** Barley malt, hops, water
- **How it's made:** ...
- **Taste:** ...
- **Goes with:** Rye crisps (ruislastut)
- **From the sources:** ...
- **Local terms:** *olut* = beer (OH-lut)
- **Sources:** [1](https://...)
```

Style cards also have **Look for on the label** and, when known, **Examples**.
