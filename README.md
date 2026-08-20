# Wiki Scripts

A set of python scripts to automate RS wiki editing using Pywikibot (PWB) and AutoWikiBrowser (AWB). Currently built around [Dragonwilds](https://dragonwilds.runescape.wiki).

Featuring **proper noun awareness** to preserve & fix cases (like "Umbral Sands" vs "sand") -- see [util_nouns.py](util_nouns.py) for 900+ known proper nouns in the game.

Tools include:
- `pwb_redirect`: Automatically create redirects to all case variations, such as "ash logs" -> "Ash Logs".
- `py_articles_to_xml`: Export 500,000 lines of regex settings to load into AWB for find/replacing cases in prose.

<img width="1024" height="691" alt="Screenshot of AWB" src="https://github.com/user-attachments/assets/34a0e137-a67b-4705-aa8b-635b5972f37f" />

## Setup

If you have PWB installed already:

1. Clone this repo into the same folder as your PWB installation

If you don't have PWB installed yet (see also [official docs](https://www.mediawiki.org/wiki/Manual:Pywikibot/Installation)):

1. Clone this repo wherever you want, then navigate into it
1. `pip install pywikibot`
1. `pwb generate_user_files` # Accept and ignore defaults
1. `pwb login` # This will use the `rsdw` family which is already committed to the repo

## Usage

1. See individual files for usage documentation.
