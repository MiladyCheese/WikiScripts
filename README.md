# Wiki Scripts

A set of python scripts to automate RS wiki editing using Pywikibot (PWB) and AutoWikiBrowser (AWB). Currently built around [Dragonwilds](https://dragonwilds.runescape.wiki).

Featuring **proper noun awareness** to preserve & fix cases (like "Umbral Sands" vs "sand") -- see [util_nouns.py](util_nouns.py) for 900+ known proper nouns in the game.

Tools include:
- `pwb_redirect`: Automatically create redirects to all case variations, such as "ash logs" -> "Ash Logs".
- `py_articles_to_xml`: Export 500,000 lines of regex settings to load into AWB for find/replacing cases in prose.

<img width="1024" height="691" alt="Screenshot of AWB" src="https://github.com/user-attachments/assets/34a0e137-a67b-4705-aa8b-635b5972f37f" />

## Setup

Install [PWB](https://www.mediawiki.org/wiki/Manual:Pywikibot/Installation):
1. Clone this repo wherever you want, then navigate into it
1. `pip install pywikibot inflect`
1. Change the username in `user-config.py`
1. Change the password in `user-password.cfg`
1. `pwb login` # This will use the `rsdw` family which is already committed to the repo

(Or, if you have PWB installed already):
1. Clone this repo into the same folder as your PWB installation

Install [AWB](https://en.wikipedia.org/wiki/Wikipedia:AutoWikiBrowser):
1. Extract the latest zip file from [SourceForge](https://sourceforge.net/projects/autowikibrowser/)
1. Launch AutoWikiBrowser.exe

Ignore the changes you made to the example files:
1. `git update-index --assume-unchanged user-password.cfg user-config.py .python-version wiki-scripts-data/*.config.xml`

## Usage

1. See individual files for usage documentation.
