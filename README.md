# Wiki Scripts

A set of python scripts to automate RS wiki editing using Pywikibot (PWB) and AutoWikiBrowser (AWB). Currently built around [Dragonwilds](https://dragonwilds.runescape.wiki).

Tools include:
- `pwb_redirect`: Automatically create redirects to all case variations, such as "ash logs" -> "Ash Logs".
- `py_articles_to_xml`: Export 500,000 lines of regex settings to load into AWB for find/replacing cases in prose.

All scripts have **proper noun awareness** to keep cases (like "Umbral Sands" vs "sand") -- see [util_nouns.py](util_nouns.py) for ~800 known proper nouns in the game.

## Usage

1. Clone this repo into the same folder as your PWB installation.
1. See individual files for usage documentation.
