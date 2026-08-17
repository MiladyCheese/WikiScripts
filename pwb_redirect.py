#!/usr/bin/env python3

import logging
import time
import sys
import re

# Docs:
#   https://www.mediawiki.org/wiki/Manual:Pywikibot/Installation
#   https://doc.wikimedia.org/pywikibot/master/api_ref/pywikibot.page.html
import pywikibot
# Credentials are stored in user-config.py
site = pywikibot.Site()

from util_nouns import restore_proper_nouns

# Usage:
    # - Configure settings below
    # - Run this script to create case-aware redirects

LOG_FILE = "pwb_redirect.log" # Relative to the current directory.

DRY_RUN = True # True = don't actually save anything, just log.
LIMIT = 0 # If greater than 0: save only N changes then exit.

# These will all be ignored if a filename is passed in as the first argument to the script.
CATEGORY = False # String to filter, or False to use recent/allpages.
RECENT = False # True to start from recently created, or False to start alphabetically.
RECENT_SIZE = 500 # This many pages will be pre-loaded before beginning.
START = "" # Alphabetical location to resume from, or leave blank for all.

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

def get_articles():
    if len(sys.argv) > 2:
        print(f"Usage: `{sys.argv[0]} <file.txt>`")
        sys.exit(1)

    if len(sys.argv) == 2:
        list = []
        with open(sys.argv[1], encoding="utf-8") as f:
            for line in f:
                list.append(pywikibot.Page(site, line))
        return list

    # `Main` namespace is `0`
    if CATEGORY:
        return pywikibot.Category(site, CATEGORY).articles(namespaces=0, recurse=True, startprefix=START)

    if RECENT:
        list = []
        for entry in site.recentchanges(changetype='new', namespaces=0):
            list.append(pywikibot.Page(site, entry['title']))
            if len(list) >= RECENT_SIZE:
                break
        return list

    return site.allpages(namespace=0, start=START)

# Regular expressions to skip some things:
MONTHS = ("January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December")
DATE_PAGE_RE = re.compile(rf"^(?:[1-9]|[12][0-9]|3[01]) (?:{'|'.join(MONTHS)})$", re.IGNORECASE)
DW_NAMESPACE_RE = re.compile(rf"^DW:", re.IGNORECASE)
RS_NAMESPACE_RE = re.compile(rf"^RS:", re.IGNORECASE)

def should_skip_regex(original_title):
    if DATE_PAGE_RE.match(original_title):
        logging.info(f"SKIP: DATE_PAGE_RE: {original_title}")
        return True
    if DW_NAMESPACE_RE.match(original_title):
        logging.info(f"SKIP: DW_NAMESPACE_RE: {original_title}")
        return True
    if RS_NAMESPACE_RE.match(original_title):
        logging.info(f"SKIP: RS_NAMESPACE_RE: {original_title}")
        return True

    return False

SKIP_CATEGORIES = {
    "Category:Dates in RuneScape: Dragonwilds",
}

def should_skip_category(page):
    for cat in page.categories():
        if cat.title() in SKIP_CATEGORIES:
            logging.info(f"SKIP: category {cat.title()} (page {page.title()})")
            return True
    return False

def should_skip_exists(redirect_page, original_title, lower_title):
    if redirect_page.exists():
        logging.info(f"SKIP: exists: {lower_title} -> {original_title}")
        return True
    return False

def should_skip_deleted(original_page):
    if RECENT and not original_page.exists():
        logging.info(f"SKIP: recent page already deleted: {original_page.title()}")
        return True
    return False

def should_skip_subpage(original_title):
    if "/" in original_title:
        logging.info(f"SKIP: subpage: {original_title}")
        return True
    return False

def should_skip_noop(original_title, lower_title):
    if original_title == lower_title:
        logging.info(f"SKIP: same title: {original_title}")
        return True
    return False

# Takes about 8 minutes to check 8000 pages when there's nothing to do (July 2026).
# Otherwise, takes ~1 second per page when creating pages, which would take 2-3 hours max.
def main():
    logging.info("Statistics:\n%s\n", site.siteinfo["statistics"])

    articles = get_articles()

    created = 0
    skipped = 0
    errors = 0

    logging.info("Starting...")
    logging.info(f"\tCategory:\t{CATEGORY if CATEGORY else "allpages"}")
    logging.info(f"\tDry run:\t{DRY_RUN}")
    logging.info(f"\tLimit:\t\t{LIMIT}")

    for original_page in articles:
        original_title = original_page.title()
        lower_title = restore_proper_nouns(original_title.capitalize()) # Sentence case

        # Quick heuristics to skip many pages before we even need to load them.
        if (
            should_skip_regex(original_title)
            or should_skip_subpage(original_title)
            or should_skip_noop(original_title, lower_title)
        ):
            skipped +=1
            continue

        redirect_page = pywikibot.Page(site, lower_title)

        # Slower heuristics.
        if (
            should_skip_exists(redirect_page, original_title, lower_title)
            or should_skip_deleted(original_page)
            or should_skip_category(original_page)
        ):
            skipped += 1
            continue

        # Follow redirects so we don't create a double redirect.
        redirected_from = False
        if original_page.isRedirectPage():
            try:
                new_title = original_page.getRedirectTarget().title()
            except pywikibot.exceptions.UnsupportedPageError:
                # We can't get a Page object to the Special namespace, and that's okay.
                logging.info(f"SKIP resolving redirect to unsupported namespace: {original_page.title()}")
                continue
            logging.info(f"RESOLVED: redirect {original_title} -> {new_title}")
            redirected_from = original_title
            original_title = new_title

        prefix = "[DRY RUN] " if DRY_RUN else ""
        logging.info(f"{prefix}CREATE: {lower_title} -> {original_title}")

        if DRY_RUN:
            continue

        # Occasionally check for manual override
        if created % HALT_FREQUENCY == 0:
            HALT_PAGE.clear_cache()

            if HALT_STRING.lower() in HALT_PAGE.text.lower():
                logging.warning("Bot halt detected!")
                break

        try:
            redirect_page.text = f"#REDIRECT [[{original_title}]]"
            redirect_page.save(f"Redirected page to [[{original_title}]]{f" (via [[{redirected_from}]])" if redirected_from else ""}")
            created += 1
        except Exception as e:
            errors += 1
            logging.exception(f"ERROR saving {lower_title} -> {original_title}: {e}")

        if LIMIT > 0 and created >= LIMIT:
            logging.info("LIMIT enabled; stopping here")
            break

    logging.info("Done.")
    logging.info(f"\tCreated:\t{created}")
    logging.info(f"\tSkipped:\t{skipped}")
    logging.info(f"\tErrors:\t\t{errors}")

if __name__ == "__main__":
    main()
