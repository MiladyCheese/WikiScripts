#!/usr/bin/env python3

import re
import sys
from pathlib import Path

import inflect
p = inflect.engine()

from util_nouns import restore_proper_nouns, singular, plural

# Usage:
    # - Run py_list_cleanup.py on your list first
    # - Make sure lowercase redirects already exist (run pwb_redirect.py)
    # - Run this script on the cleaned list to generate JSON
    # - Paste JSON into a JWB settings file at the appropriate location
    # - Load settings file in JWB
    # - Run "find and replace" mode on whatever article list you want

def escape_json(text):
    return text \
        .replace("\\", "\\\\") \
        .replace("\"", "\\\"")

def escape_xml(text):
    return text \
        .replace("&", "&amp;")

def escape_regex(text):
    return re.escape(text) \
        .replace("\\", "\\\\") \
        .replace("\"", "\\\"") \
        .replace("\\\\\\\\", "\\\\") # Undo double-applying escapes (hacky workaround for now)

# Add \b to the back only if appropriate ("Wanted!" is an example of a tricky word)
def escape_regex_boundBack(text):
    needs_back = re.search(r"\W$", text) is None
    return f"{escape_regex(text)}{"\\\\b" if needs_back else ""}"

# Add \b to the front + back only if appropriate ("Wanted!" is an example of a tricky word)
def escape_regex_boundBoth(text):
    needs_front = re.search(r"^\W", text) is None
    return f"{"\\\\b" if needs_front else ""}{escape_regex_boundBack(text)}"

# Unused except when undoing things like disambiguation pages
def title_case(text):
    text = restore_proper_nouns(text.title())
    return text

def sentence_case(text):
    text = restore_proper_nouns(text.lower())
    text = text[0].upper() + text[1:]
    return text

def lower_case(text):
    text = restore_proper_nouns(text.lower())
    return text

# Narrow replacements should have AWB "ignore links etc." turned OFF or they won't accomplish much.
TEMPLATE_NARROW = """\
            {{
                "replaceText": "\\[\\[{escaped}\\]\\]",
                "replaceWith": "[[{sentence_case}]]",
                "useRegex": true,
                "regexFlags": "gi",
                "ignoreNowiki": true
            }},
            {{
                "replaceText": "\\[\\[{escaped}\\|({escaped})\\]\\]",
                "replaceWith": "[[$1]]",
                "useRegex": true,
                "regexFlags": "gi",
                "ignoreNowiki": true
            }},
            {{
                "replaceText": "\\[\\[{escaped}\\|{escaped_2}\\]\\]",
                "replaceWith": "[[{sentence_case}|{sentence_case_2}]]",
                "useRegex": true,
                "regexFlags": "gi",
                "ignoreNowiki": true
            }},
            {{
                "replaceText": "(?<=[a-zA-Z0-9,%)>/\\]&'\\"`])([ /-])(\\()?\\[\\[{escaped}\\]\\]",
                "replaceWith": "$1$2[[{lower_case}]]",
                "useRegex": true,
                "regexFlags": "gi",
                "ignoreNowiki": true
            }},
            {{
                "replaceText": "(?<=[a-zA-Z0-9,%)>/\\]&'\\"`])([ /-])(\\()?\\[\\[{escaped}\\|({escaped_2})\\]\\]",
                "replaceWith": "$1$2[[{lower_case}|{lower_case_2}]]",
                "useRegex": true,
                "regexFlags": "gi",
                "ignoreNowiki": true
            }},
            {{
                "replaceText": "(?<=[a-zA-Z0-9,%)>/\\]&'\\"`])([ /-])(\\()?\\[\\[({escaped})\\|({escaped_1})\\]\\]",
                "replaceWith": "$1$2[[$3|{lower_case_1}]]",
                "useRegex": true,
                "regexFlags": "gi",
                "ignoreNowiki": true
            }},
"""

ADDITIONAL_NARROW = """\
            {
                "replaceText": "(?<=[a-zA-Z0-9,%)>/\\]&'\\"`])( |-)\\[\\[Power Level\\|Power Level( \\d)?\\]\\]",
                "replaceWith": "$1[[power level]]$2",
                "useRegex": true,
                "regexFlags": "gi",
                "ignoreNowiki": true
            },
            {
                "replaceText": "(?<=[a-zA-Z0-9,%)>/\\]&'\\"`])( |-)\\[\\[Power Level\\|Tier( \\d)?\\]\\]",
                "replaceWith": "$1[[power level]]$2",
                "useRegex": true,
                "regexFlags": "gi",
                "ignoreNowiki": true
            },
            {
                "replaceText": "\\[\\[Power Level\\|Power Level( \\d)?\\]\\]",
                "replaceWith": "[[Power level]]$1",
                "useRegex": true,
                "regexFlags": "gi",
                "ignoreNowiki": true
            },
            {
                "replaceText": "for \\[\\[Compost\\|Composting\\]\\]",
                "replaceWith": "for [[compost]]ing",
                "useRegex": true,
                "regexFlags": "gi",
                "ignoreNowiki": true
            },
            {
                "replaceText": "(?<=[a-zA-Z0-9,%)>/\\]&'\\"`]) \\[\\[Garou \\(race\\)\\|Garou\\]\\]",
                "replaceWith": " [[Garou (race)|garou]]",
                "useRegex": true,
                "regexFlags": "gi",
                "ignoreNowiki": true
            },
            {
                "replaceText": "Moon \\[\\[(Garou \\(race\\)\\|)?Garou\\]\\]",
                "replaceWith": "Moon [[$1Garou]]",
                "useRegex": true,
                "regexFlags": "gi",
                "ignoreNowiki": true
            },
            {
                "replaceText": "Lunar \\[\\[(Garou \\(race\\)\\|)?Garou\\]\\]",
                "replaceWith": "Lunar [[$1Garou]]",
                "useRegex": true,
                "regexFlags": "gi",
                "ignoreNowiki": true
            },
            {
                "replaceText": "(?<=[a-zA-Z0-9,%)>/\\]&'\\"`]) \\[\\[Dragonkin \\(race\\)\\|Dragonkin\\]\\]",
                "replaceWith": " [[Dragonkin (race)|dragonkin]]",
                "useRegex": true,
                "regexFlags": "gi",
                "ignoreNowiki": true
            },
            {
                "replaceText": "(?<=[a-zA-Z0-9,%)>/\\]&'\\"`]) \\[\\[Dragonkin Vault\\|Vault\\]\\]",
                "replaceWith": " [[dragonkin vault|vault]]",
                "useRegex": true,
                "regexFlags": "gi",
                "ignoreNowiki": true
            },
            {
                "replaceText": "the \\[\\[Player Character(\\|Player)?\\]\\]",
                "replaceWith": "the [[player]]",
                "useRegex": true,
                "regexFlags": "gi",
                "ignoreNowiki": true
            },
            {
                "replaceText": "(?<=[a-zA-Z0-9,%)>/\\]&'\\"`]) \\[\\[Wither\\]\\](ed|ing)",
                "replaceWith": " [[wither]]$1",
                "useRegex": true,
                "regexFlags": "gi",
                "ignoreNowiki": true
            },
            {
                "replaceText": "(?<=[a-zA-Z0-9,%)>/⌋&'\\"`]) \\[\\[Ranged\\]\\](,)? (and|or) \\[\\[Magic\\]\\]",
                "replaceWith": " [[ranged]]$1 $2 [[magic]]",
                "useRegex": true,
                "regexFlags": "gi",
                "ignoreNowiki": true
            },
            {
                "replaceText": "(?<=[a-zA-Z0-9,%)>/⌋&'\\"`]) \\[\\[Magic\\]\\](,)? (and|or) \\[\\[Ranged\\]\\]",
                "replaceWith": " [[magic]]$1 $2 [[ranged]]",
                "useRegex": true,
                "regexFlags": "gi",
                "ignoreNowiki": true
            },
            {
                "replaceText": "(?<=[a-zA-Z0-9,%)>/⌋&'\\"`]) \\[\\[Melee((\\]\\])? (\\[\\[)?(armour|attack))",
                "replaceWith": " [[melee$1",
                "useRegex": true,
                "regexFlags": "gi",
                "ignoreNowiki": true
            },
            {
                "replaceText": "(?<=[a-zA-Z0-9,%)>/⌋&'\\"`]) \\[\\[Ranged((\\]\\])? (\\[\\[)?(armour|attack))",
                "replaceWith": " [[ranged$1",
                "useRegex": true,
                "regexFlags": "gi",
                "ignoreNowiki": true
            },
            {
                "replaceText": "(?<=[a-zA-Z0-9,%)>/⌋&'\\"`]) \\[\\[Magic(al)?((\\]\\])? (\\[\\[)?(armour|attack))",
                "replaceWith": " [[magic$1$2",
                "useRegex": true,
                "regexFlags": "gi",
                "ignoreNowiki": true
            },
            {
                "replaceText": "(for|in) \\[\\[Construction\\]\\]",
                "replaceWith": "$1 [[construction]]",
                "useRegex": true,
                "regexFlags": "gi",
                "ignoreNowiki": true
            },
            {
                "replaceText": "(after) \\[\\[Mining\\]\\]",
                "replaceWith": "$1 [[mining]]",
                "useRegex": true,
                "regexFlags": "gi",
                "ignoreNowiki": true
            },
            {
                "README": "Fake replacement to make this more obvious. Disambiguation list caps should not be lowered."
                "replaceText": "\\{\\{(Disambig(uation)?)\\}\\}",
                "replaceWith": "{{$1}} ⚠⚠⚠",
                "useRegex": true,
                "regexFlags": "gi",
                "ignoreNowiki": true
            }
"""

# Broad replacements should have AWB "ignore links etc." turned ON or they'll break things.
# Note that link hiding replaces [[link]] with ⌊⌊⌊⌊link⌋⌋⌋⌋ which is still usable as a negative match.
TEMPLATE_BROAD = """\
            {{
                "replaceText": "{b_escaped_1_b}",
                "replaceWith": "{sentence_case_1}",
                "useRegex": true,
                "regexFlags": "gi",
                "ignoreNowiki": true
            }},
            {{
                "replaceText": "{b_escaped_2_b}",
                "replaceWith": "{sentence_case_2}",
                "useRegex": true,
                "regexFlags": "gi",
                "ignoreNowiki": true
            }},
            {{
                "replaceText": "(?<=[a-zA-Z0-9,%)>/⌋&'\\"`])([ /-])('+|\\\\()?{escaped_1_b}",
                "replaceWith": "$1${{2}}{lower_case_1}",
                "useRegex": true,
                "regexFlags": "gi",
                "ignoreNowiki": true
            }},
            {{
                "replaceText": "(?<=[a-zA-Z0-9,%)>/⌋&'\\"`])([ /-])('+|\\\\()?{escaped_2_b}",
                "replaceWith": "$1${{2}}{lower_case_2}",
                "useRegex": true,
                "regexFlags": "gi",
                "ignoreNowiki": true
            }},
"""

# Plural version of Attack skill is impossible to regex away in nouns list
ADDITIONAL_BROAD = """\
            {
                "replaceText": "(?<=[a-zA-Z0-9,%)>/⌋&'\\"`])( |-)Attacks",
                "replaceWith": "$1attacks",
                "useRegex": true,
                "regexFlags": "gi",
                "ignoreNowiki": true
            },
            {
                "replaceText": "(?<=[a-zA-Z0-9,%)>/⌋&'\\"`])( |-)Attack (is|it|them|her|him|the|with|from|where|speed)",
                "replaceWith": "$1attack $2",
                "useRegex": true,
                "regexFlags": "gi",
                "ignoreNowiki": true
            },
            {
                "replaceText": "(breath|based|an|to|will|parrying|magic|'s) Attack\\\\b",
                "replaceWith": "$1 attack",
                "useRegex": true,
                "regexFlags": "gi",
                "ignoreNowiki": true
            },
            {
                "replaceText": "(a|to|for|use|using|wielding) Melee\\\\b",
                "replaceWith": "$1 melee",
                "useRegex": true,
                "regexFlags": "gi",
                "ignoreNowiki": true
            },
            {
                "replaceText": "(a|to|for|use|using|wielding) Ranged\\\\b",
                "replaceWith": "$1 ranged",
                "useRegex": true,
                "regexFlags": "gi",
                "ignoreNowiki": true
            },
            {
                "replaceText": "(a|to|for|use|using|wielding|air|water|earth|fire) Magic\\\\b",
                "replaceWith": "$1 magic",
                "useRegex": true,
                "regexFlags": "gi",
                "ignoreNowiki": true
            },
            {
                "replaceText": "(?<=[a-zA-Z0-9,%)>/⌋&'\\"`]) Magic dart",
                "replaceWith": " magic dart",
                "useRegex": true,
                "regexFlags": "gi",
                "ignoreNowiki": true
            },
            {
                "replaceText": "(?<=[a-zA-Z0-9,%)>/⌋&'\\"`]) Ranged(,)? (and|or) Magic",
                "replaceWith": " ranged$1 $2 magic",
                "useRegex": true,
                "regexFlags": "gi",
                "ignoreNowiki": true
            },
            {
                "replaceText": "(?<=[a-zA-Z0-9,%)>/⌋&'\\"`]) Magic(,)? (and|or) Ranged",
                "replaceWith": " magic$1 $2 ranged",
                "useRegex": true,
                "regexFlags": "gi",
                "ignoreNowiki": true
            },
            {
                "replaceText": "(from|while|by) Mining",
                "replaceWith": "$1 mining",
                "useRegex": true,
                "regexFlags": "gi",
                "ignoreNowiki": true
            },
            {
                "replaceText": "(?<=[a-zA-Z0-9,%)>/⌋&'\\"`]) Mining (node)",
                "replaceWith": " mining $1",
                "useRegex": true,
                "regexFlags": "gi",
                "ignoreNowiki": true
            },
            {
                "replaceText": "(for|in) Construction",
                "replaceWith": "$1 construction",
                "useRegex": true,
                "regexFlags": "gi",
                "ignoreNowiki": true
            },
            {
                "replaceText": "(by|while|whilst) Cooking",
                "replaceWith": "$1 cooking",
                "useRegex": true,
                "regexFlags": "gi",
                "ignoreNowiki": true
            },
            {
                "replaceText": "(?<=[a-zA-Z0-9,%)>/⌋&'\\"`]) Cooking (a)",
                "replaceWith": " cooking $1",
                "useRegex": true,
                "regexFlags": "gi",
                "ignoreNowiki": true
            },
            {
                "replaceText": "(by|for) Farming",
                "replaceWith": "$1 farming",
                "useRegex": true,
                "regexFlags": "gi",
                "ignoreNowiki": true
            },
            {
                "replaceText": "(?<=[a-zA-Z0-9,%)>/⌋&'\\"`]) getting started with",
                "replaceWith": " getting started with",
                "useRegex": true,
                "regexFlags": "gi",
                "ignoreNowiki": true
            },
            {
                "replaceText": "the goblin series",
                "replaceWith": "the Goblin series",
                "useRegex": true,
                "regexFlags": "gi",
                "ignoreNowiki": true
            },
            {
                "replaceText": "the garou series",
                "replaceWith": "the Garou series",
                "useRegex": true,
                "regexFlags": "gi",
                "ignoreNowiki": true
            },
            {
                "replaceText": "the dragon attack series",
                "replaceWith": "the Dragon Attack series",
                "useRegex": true,
                "regexFlags": "gi",
                "ignoreNowiki": true
            },
            {
                "replaceText": "spells tab",
                "replaceWith": "Spells tab",
                "useRegex": true,
                "regexFlags": "gi",
                "ignoreNowiki": true
            },
            {
                "replaceText": "(a|little) shelter",
                "replaceWith": "$1 shelter",
                "useRegex": true,
                "regexFlags": "gi",
                "ignoreNowiki": true
            },
            {
                "replaceText": "(?<=[a-zA-Z0-9,%)>/⌋&'\\"`]) shelter(ed)? (from)",
                "replaceWith": " shelter$1 $2",
                "useRegex": true,
                "regexFlags": "gi",
                "ignoreNowiki": true
            },
            {
                "replaceText": "(?:(?<!on |'s |of |at )(?<!his |her |per |the )(?<!each )(?<!their ))Death(?! of)",
                "replaceWith": "Death",
                "useRegex": true,
                "regexFlags": "gi",
                "ignoreNowiki": true
            }
"""

def main():
    if len(sys.argv) != 2:
        print(f"Usage: `{sys.argv[0]} list.txt` # Will output list-broad.json and list-narrow.json")
        sys.exit(1)

    input_file = sys.argv[1]
    input_path = Path(input_file)
    output_narrow = input_path.with_name(f"{input_path.stem}-narrow.json")
    output_broad = input_path.with_name(f"{input_path.stem}-broad.json")

    with open(input_file, encoding="utf-8") as fin, \
         open(output_narrow, "w", encoding="utf-8", newline="\n") as fout_narrow, \
         open(output_broad, "w", encoding="utf-8", newline="\n") as fout_broad:

        count = 0
        for line in fin:
            if count % 200 == 0:
                print(".", end="", flush=True)
            count += 1

            raw = line.strip()
            if not raw:
                continue

            # First create the cases for each plurality...
            raw_1 = singular(raw)
            raw_2 = plural(raw)

            sentence = sentence_case(raw)
            lower = lower_case(raw)

            sentence_1 = sentence_case(raw_1)
            lower_1 = lower_case(raw_1)

            sentence_2 = sentence_case(raw_2)
            lower_2 = lower_case(raw_2)

            # Then escape each one as a final pass (to avoid repeat-escaping above)...
            sentence = escape_json(sentence)
            lower = escape_json(lower)

            sentence_1 = escape_json(sentence_1)
            lower_1 = escape_json(lower_1)

            sentence_2 = escape_json(sentence_2)
            lower_2 = escape_json(lower_2)

            # Then ALSO escape regex for the "Find" (but not "Replace") fields.
            x_lower = escape_regex(lower)
            x_lower_1 = escape_regex(lower_1)
            x_lower_2 = escape_regex(lower_2)

            # And include alternatives with punctuation-aware `\b` caps.
            x_lower_b = escape_regex_boundBack(lower)
            x_lower_1_b = escape_regex_boundBack(lower_1)
            x_lower_2_b = escape_regex_boundBack(lower_2)

            b_x_lower_b = escape_regex_boundBoth(lower)
            b_x_lower_1_b = escape_regex_boundBoth(lower_1)
            b_x_lower_2_b = escape_regex_boundBoth(lower_2)

            # Debug plurality:
            #print(f"{lower} (1 {lower_1}; 2 {lower_2})...")

            fout_narrow.write(TEMPLATE_NARROW.format(
                sentence_case=sentence,
                lower_case=lower,

                sentence_case_1=sentence_1,
                lower_case_1=lower_1,

                sentence_case_2=sentence_2,
                lower_case_2=lower_2,

                escaped=x_lower,
                escaped_1=x_lower_1,
                escaped_2=x_lower_2,

                escaped_b=x_lower_b,
                escaped_1_b=x_lower_1_b,
                escaped_2_b=x_lower_2_b,

                b_escaped_b=b_x_lower_b,
                b_escaped_1_b=b_x_lower_1_b,
                b_escaped_2_b=b_x_lower_2_b,
            ))

            fout_broad.write(TEMPLATE_BROAD.format(
                sentence_case=sentence,
                lower_case=lower,

                sentence_case_1=sentence_1,
                lower_case_1=lower_1,

                sentence_case_2=sentence_2,
                lower_case_2=lower_2,

                escaped=x_lower,
                escaped_1=x_lower_1,
                escaped_2=x_lower_2,

                escaped_b=x_lower_b,
                escaped_1_b=x_lower_1_b,
                escaped_2_b=x_lower_2_b,

                b_escaped_b=b_x_lower_b,
                b_escaped_1_b=b_x_lower_1_b,
                b_escaped_2_b=b_x_lower_2_b,
            ))

        fout_narrow.write(ADDITIONAL_NARROW)
        fout_broad.write(ADDITIONAL_BROAD)

    print("Done.")

if __name__ == "__main__":
    main()
