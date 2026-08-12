# Wiki Scripts

A set of python scripts to automate RS wiki editing using Pywikibot (PWB) and AutoWikiBrowser (AWB). Currently built around [Dragonwilds](https://dragonwilds.runescape.wiki).

Featuring **proper noun awareness** to preserve & fix cases (like "Umbral Sands" vs "sand") -- see [util_nouns.py](util_nouns.py) for 900+ known proper nouns in the game.

Tools include:
- `pwb_redirect`: Automatically create redirects to all case variations, such as "ash logs" -> "Ash Logs".
- `py_articles_to_xml`: Export 500,000 lines of regex settings to load into AWB for find/replacing cases in prose.

<img width="1024" height="691" alt="Screenshot of AWB" src="https://github.com/user-attachments/assets/34a0e137-a67b-4705-aa8b-635b5972f37f" />

## Usage

1. Clone this repo into the same folder as your PWB installation.
1. See individual files for usage documentation.
