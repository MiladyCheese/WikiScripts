# Wiki Scripts

A set of python scripts to automate RS wiki editing. Currently built around [Dragonwilds](https://dragonwilds.runescape.wiki).

Tools include:
- Automatically create redirects to all case variations, such as "ash logs" -> "Ash Logs".
- Export 500,000 lines of regex settings to load into AWB for case find/replace in prose.

All scripts have **proper noun awareness** to keep cases (like "Umbral Sands" vs "sand") -- see [util_nouns.py](util_nouns.py) for ~800 known proper nouns in the game.

See individual files for usage documentation.
