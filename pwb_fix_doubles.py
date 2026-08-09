#!/usr/bin/env python3

import logging
import time
import re

import pywikibot

site = pywikibot.Site()

# Usage:
    # - Configure settings below
    # - Run this script to fix all double-redirects on the wiki

INPUT_FILE = "pwb_fix_doubles_list.txt"
LOG_FILE = "pwb_fix_doubles.log"

DRY_RUN = True # True = don't actually save anything, just log.
LIMIT = 0 # If greater than 0: save only N changes then exit.

HALT_PAGE = pywikibot.Page(site, "User talk:ChxPotatoCurry-Bot")
HALT_STRING = "AWB shutdown"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler()
    ]
)

def main():
    redirects = []

    with open(INPUT_FILE, encoding="utf-8") as f:
        for line in f:
            redirects.append(line)

    created = 0
    skipped = 0
    errors = 0

    logging.info(f"Processing {len(redirects)} redirects...")
    logging.info(f"\tDry run:\t{DRY_RUN}")
    logging.info(f"\tLimit:\t\t{LIMIT}")

    for original_title in redirects:
        original_title = original_title.strip()
        original_page = pywikibot.Page(site, original_title)
        page = original_page

        while page.isRedirectPage():
            page = page.getRedirectTarget()

        new_title = page.title()

        prefix = "[DRY RUN] " if DRY_RUN else ""
        logging.info(f"{prefix}REDIRECT: {original_title} -> {new_title}")

        if DRY_RUN:
            continue

        # Occasionally check for manual override
        if created % 10 == 0:
            HALT_PAGE.clear_cache()

            if HALT_STRING.lower() in HALT_PAGE.text.lower():
                logging.warning("Bot halt detected!")
                break

        try:
            original_page.text = (f"#REDIRECT [[{new_title}]]")
            original_page.save(f"Resolve double redirect to [[{new_title}]]")

            created += 1

            if LIMIT > 0 and created >= LIMIT:
                logging.info("LIMIT enabled; stopping here")
                break

        except Exception as e:
            errors += 1
            logging.exception(f"ERROR saving {original_title} -> {new_title}: {e}")

    logging.info("Done.")
    logging.info(f"\tCreated:\t{created}")
    logging.info(f"\tErrors:\t\t{errors}")

if __name__ == "__main__":
    main()
