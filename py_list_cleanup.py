#!/usr/bin/env python3

import re
import sys
from pathlib import Path

from util_nouns import singular, plural

# Usage:
    # - Run this script on your cleaned-up list of Special:AllPages
    # (clean up based on instructions in util_nouns.py)

def generate(input_file, output_file):
    seen = set()

    with open(input_file, encoding="utf-8") as fin, \
         open(output_file, "w", encoding="utf-8", newline="\n") as fout:

        count = 0
        for line in fin:
            if count % 200 == 0:
                print(".", end="", flush=True)
            count += 1

            line = line.strip().lower()
            if line:
                seen.add(line)

        for line in sorted(sorted(seen), key=len):
            fout.write(line + "\n")

    print("Done cleaning list.")

def main():
    if len(sys.argv) != 2:
        print(f"Usage: `{sys.argv[0]} list.txt` # Will output list-clean.txt")
        sys.exit(1)

    input_file = sys.argv[1]
    input_path = Path(input_file)
    output_file = input_path.with_name(f"{input_path.stem}-clean{input_path.suffix}")

    while True:
        # First time is automatic
        generate(input_file, output_file)

        # Then daemonise (because loading the `inflect` library on startup can be slow)
        print("Press enter to regen if list has changed:")
        line = input()

if __name__ == "__main__":
    main()
