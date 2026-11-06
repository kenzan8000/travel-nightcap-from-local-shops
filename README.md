# Travel nightcap from local shops

An agent skill for trips. Tell it where you are staying, and it lists the local
alcoholic drinks and snacks worth buying at a local supermarket, liquor shop or kiosk
to enjoy in your hotel room that evening. The agent reads posts by residents and people
who travelled there, picks what they recommend, looks up the details, and shows the
list in the chat.

The output is laid out for reading on a phone, with no wide tables. It starts with the
local buying rules. Drinks come next, with a short numbered overview and then a card per
drink, and snacks follow in the same way. Each card has:

| Field | Content |
| --- | --- |
| Photo | Official product image, Open Food Facts, Wikimedia Commons, or a source post's photo, checked to embed from another site |
| Name | Local name, with your language's name when it helps |
| ABV, sizes, price | Typical containers and a rough local price |
| Alcohol | Grams of pure alcohol per container, and drinks of 10 g |
| Made from, how it's made, taste | Ingredients and production |
| Goes with | Drinks and snacks from the list that pair well |
| Look for on the label | Local words to find a style of item, such as *kuiva* = dry |
| Sources | The posts that recommended it |

Widely sold brands are listed as exact products. Categories with many similar products,
such as local wine or cheese, are listed as a style with label hints and examples.

## What's in here

```
travel-nightcap-from-local-shops/
  SKILL.md                     the skill: workflow and rules for the agent
  scripts/render_nightcap.py   checks photos, computes alcohol grams, prints Markdown
  examples/helsinki.json       sample input
```

The script needs only Python 3.9 or newer, with no extra packages. Agents that cannot
run scripts can follow the manual path in `SKILL.md`.

## Install

`SKILL.md` uses the open Agent Skills format (a folder with a `SKILL.md` file and
`name`/`description` frontmatter). Copy or symlink the whole folder:

| Agent | Where |
| --- | --- |
| Claude Code | `~/.claude/skills/travel-nightcap-from-local-shops/` |
| Claude apps (phone, web, desktop) | Zip the folder and upload it in the Skills section of Settings |
| Cursor | `~/.cursor/skills/travel-nightcap-from-local-shops/` |
| Cursor Cloud Agents (phone, web) | Keep the folder in a repo the agent opens, under `.cursor/skills/` |
| Codex CLI | `~/.codex/skills/travel-nightcap-from-local-shops/` |
| Anything else | Paste `SKILL.md` into the chat or the agent's custom instructions |

Then ask something like "What local drinks and snacks should I get for tonight in
Helsinki?" The agent needs web search and page reading.

Apps that cannot run scripts, or whose code sandbox has no internet access, still
work. The agent follows the manual path in `SKILL.md` and checks photos with its own
browsing tool.

## Running the script yourself

```bash
python3 scripts/render_nightcap.py examples/helsinki.json
```

Options:

- `-o list.md`: write the Markdown to a file instead of stdout
- `--no-check-images`: use the first image URL without checking it
- `--no-proxy`: keep the original image URLs instead of GitHub image proxy URLs.
  Some chat apps, often on mobile and web, only show images from a short list of
  trusted hosts such as `camo.githubusercontent.com`; without the proxy, photos may
  not show there.
  `GITHUB_TOKEN` or `GH_TOKEN` raises GitHub's limit of 60 requests an hour.
- `--timeout 8`: seconds per image request

The sample's source URLs are `example.com` placeholders and its prices are
illustrative; real runs use the actual posts and listings.
