#!/usr/bin/env python3

import logging
import sys
import re

# Docs:
#   https://www.mediawiki.org/wiki/Manual:Pywikibot/Installation
#   https://doc.wikimedia.org/pywikibot/master/api_ref/pywikibot.page.html
import pywikibot
# Credentials are stored in user-config.py
site = pywikibot.Site()

# Usage:
    # - Configure settings below
    # - Run `pwb_detect_shortcuts.py <file.txt>`, with file containing one title per line

LOG_FILE = "pwb_detect_shortcuts.log" # Relative to the current directory.

DRY_RUN = True # True = don't actually save anything, just log.
LIMIT = 0 # If greater than 0: save only N changes then exit.

TEMPLATE_NAME = "shortcut" # Not case-sensitive.
ANCHOR_DISTANCE = 3 # Max lines between a {{shortcut}} and the {{anchor}} it links to.
# Example:
    # ==Grammar and spelling==
    # ==={{anchor|CASE}}Case===
    # {{shortcut|DW:CASE|DW:STYLE#CASE}}

SHORTCUT_RE = re.compile(rf"\{{\{{\s*(?:Template:)?{TEMPLATE_NAME}\s*\|([^}}]*)\}}\}}", re.IGNORECASE)
ANCHOR_RE = re.compile(r"\{\{\s*(?:Template:)?anchor\s*\|\s*([^|}]+)", re.IGNORECASE)

HALT_PAGE = pywikibot.Page(site, "User talk:ChxPotatoCurry-Bot")
HALT_STRING = "AWB shutdown" # If this text is seen on HALT_PAGE, bot will halt.
HALT_FREQUENCY = 10 # Number of changes before checking again for shutdowns.

# Note: flood protection happens automatically and is configured in user-config.py, for example:
# put_throttle = 1

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler()
    ]
)

# Clean up titles that live within sub-templates.
def substitute_titles(title):
    return title \
        .replace("Template:Sandboxheader", "Dragonwilds:Sandbox") \
        .replace("Dragonwilds:User help/Header", "Dragonwilds:User help")

def get_articles():
    if len(sys.argv) != 2:
        print(f"Usage: `{sys.argv[0]} <file.txt>`")
        sys.exit(1)

    list = []
    with open(sys.argv[1], encoding="utf-8") as f:
        for line in f:
            title = line.strip()
            if title:
                list.append(pywikibot.Page(site, title))
    return list

# Returns the first name of the closest {{anchor}} within ANCHOR_DISTANCE lines, or None.
# Ties go to the anchor above, since that's where headings normally are.
def nearest_anchor(anchors, line_no):
    # TODO: Gross loop
    nearby = [(abs(i - line_no), i > line_no, name) for i, name in anchors if abs(i - line_no) <= ANCHOR_DISTANCE]
    return min(nearby)[2] if nearby else None

# Returns (shortcut, anchor) for every shortcut on the page, e.g.
#   ==={{anchor|CASE}}Case===
#   {{shortcut|DW:CASE}}
#   ->
#   returns [("DW:CASE", "CASE")]
def get_shortcuts(page):
    lines = page.text.splitlines()
    # TODO: Gross loop
    anchors = [(i, m.group(1).strip()) for i, line in enumerate(lines) for m in ANCHOR_RE.finditer(line)]

    shortcuts = []
    for i, line in enumerate(lines):
        for m in SHORTCUT_RE.finditer(line):
            anchor = nearest_anchor(anchors, i)
            for shortcut in m.group(1).split("|"):
                shortcut = shortcut.strip()
                # Skip blanks and named params like `|align=right`.
                if not shortcut or "=" in shortcut:
                    continue
                # Skip section links like `DW:STYLE#CASE` because we assume the base link already exists from earlier.
                if "#" in shortcut:
                    logging.info(f"SKIP: section shortcut likely exists: {shortcut}")
                    continue
                shortcuts.append((shortcut, anchor))
    return shortcuts

# Avoid creating a double redirect.
# Returns the target title, or False if it can't be resolved.
def resolve_target(page):
    if not page.isRedirectPage():
        return page.title()
    try:
        target = page.getRedirectTarget().title()
    except pywikibot.exceptions.UnsupportedPageError:
        logging.info(f"SKIP: redirect to unsupported namespace: {page.title()}")
        return False
    logging.info(f"RESOLVED: redirect {page.title()} -> {target}")
    return target

# Returns [created_count, skip_count, error_count].
def try_to_redirect(shortcut_title, target_title, anchor_name):
    redirect_page = pywikibot.Page(site, shortcut_title)
    target_link = f"{target_title}#{anchor_name}" if anchor_name else target_title

    if shortcut_title == target_title:
        logging.info(f"SKIP: shortcut is the page itself: {shortcut_title}")
        return [0, 1, 0]

    if redirect_page.exists():
        if redirect_page.isRedirectPage() and redirect_page.getRedirectTarget().title() == target_link:
            logging.info(f"SKIP: exists: {shortcut_title} -> {target_link}")
        else:
            logging.warning(f"SKIP: exists but does not redirect to {target_link}: {shortcut_title}")
        return [0, 1, 0]

    prefix = "[DRY RUN] " if DRY_RUN else ""
    logging.info(f"{prefix}CREATE: {shortcut_title} -> {target_link}")

    if DRY_RUN:
        return [1, 0, 0]

    try:
        redirect_page.text = f"#REDIRECT [[{target_link}]]"
        redirect_page.save(f"Redirected {{{{shortcut}}}} to [[{target_link}]]")
        return [1, 0, 0]
    except Exception as e:
        logging.exception(f"ERROR saving {shortcut_title} -> {target_link}: {e}")
        return [0, 0, 1]

# Return True if bot halt detected, otherwise False.
def should_halt():
    HALT_PAGE.clear_cache()

    if HALT_STRING.lower() in HALT_PAGE.text.lower():
        logging.warning("Bot halt detected!")
        return True

    return False

def main():
    articles = get_articles()

    created = 0
    skipped = 0
    errors = 0

    logging.info("Starting...")
    logging.info(f"\tFile:\t\t{sys.argv[1]}")
    logging.info(f"\tDry run:\t{DRY_RUN}")
    logging.info(f"\tLimit:\t\t{LIMIT}")

    if should_halt():
        return

    for page in articles:
        target_title = substitute_titles(page.title())

        shortcuts = get_shortcuts(page)
        if not shortcuts:
            logging.info(f"SKIP: no {{{{{TEMPLATE_NAME}}}}} found: {page.title()}")
            skipped += 1
            continue

        stop = False
        for shortcut_title, anchor_name in shortcuts:
            new_c, new_s, new_e = try_to_redirect(shortcut_title, target_title, anchor_name)
            created += new_c
            skipped += new_s
            errors += new_e

            if LIMIT > 0 and created >= LIMIT:
                logging.info("LIMIT enabled; stopping here")
                stop = True
                break

            # Occasionally check for manual override,
            # but only if we recently did anything (this is a slow check).
            if new_c > 0 and created % HALT_FREQUENCY == 0 and should_halt():
                stop = True
                break

        if stop:
            break

    logging.info("Done.")
    logging.info(f"\tCreated:\t{created}")
    logging.info(f"\tSkipped:\t{skipped}")
    logging.info(f"\tErrors:\t\t{errors}")

if __name__ == "__main__":
    main()
