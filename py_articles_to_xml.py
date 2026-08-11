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
    # - Run this script on the cleaned list to generate XML
    # - Paste XML into an AWB settings file at the appropriate location
    # - Load settings file in AWB
    # - Run "find and replace" mode on whatever AWB list you want

def escape_xml(text):
    return text \
        .replace("&", "&amp;")

def escape_regex(text):
    return re.escape(text)

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
      <Replacement>
        <Find>\\[\\[{escaped}\\]\\]</Find>
        <Replace>[[{sentence_case}]]</Replace>
        <Comment />
        <IsRegex>true</IsRegex>
        <Enabled>true</Enabled>
        <Minor>true</Minor>
        <BeforeOrAfter>false</BeforeOrAfter>
        <RegularExpressionOptions>IgnoreCase</RegularExpressionOptions>
      </Replacement>
      <Replacement>
        <Find>\\[\\[{escaped}\\|({escaped})\\]\\]</Find>
        <Replace>[[$1]]</Replace>
        <Comment />
        <IsRegex>true</IsRegex>
        <Enabled>true</Enabled>
        <Minor>true</Minor>
        <BeforeOrAfter>false</BeforeOrAfter>
        <RegularExpressionOptions>IgnoreCase</RegularExpressionOptions>
      </Replacement>
      <Replacement>
        <Find>(?&lt;=[a-zA-Z0-9,)⌋&amp;'"`])( |-)(\\()?\\[\\[{escaped}\\]\\]</Find>
        <Replace>$1$2[[{lower_case}]]</Replace>
        <Comment />
        <IsRegex>true</IsRegex>
        <Enabled>true</Enabled>
        <Minor>true</Minor>
        <BeforeOrAfter>false</BeforeOrAfter>
        <RegularExpressionOptions>IgnoreCase</RegularExpressionOptions>
      </Replacement>
      <Replacement>
        <Find>(?&lt;=[a-zA-Z0-9,)⌋&amp;'"`])( |-)(\\()?\\[\\[{escaped}\\|({escaped_2})\\]\\]</Find>
        <Replace>$1$2[[{lower_case}|{lower_case_2}]]</Replace>
        <Comment />
        <IsRegex>true</IsRegex>
        <Enabled>true</Enabled>
        <Minor>true</Minor>
        <BeforeOrAfter>false</BeforeOrAfter>
        <RegularExpressionOptions>IgnoreCase</RegularExpressionOptions>
      </Replacement>
      <Replacement>
        <Find>(?&lt;=[a-zA-Z0-9,)⌋&amp;'"`])( |-)(\\()?\\[\\[({escaped})\\|({escaped_1})\\]\\]</Find>
        <Replace>$1$2[[$3|{lower_case_1}]]</Replace>
        <Comment />
        <IsRegex>true</IsRegex>
        <Enabled>true</Enabled>
        <Minor>true</Minor>
        <BeforeOrAfter>false</BeforeOrAfter>
        <RegularExpressionOptions>IgnoreCase</RegularExpressionOptions>
      </Replacement>
"""

ADDITIONAL_NARROW = """\
      <Replacement>
        <Find>(?&lt;=[a-zA-Z0-9,)⌋&amp;'"`])( |-)\\[\\[Power Level\\|Power Level( \\d)?\\]\\]</Find>
        <Replace>$1[[power level]]$2</Replace>
        <Comment />
        <IsRegex>true</IsRegex>
        <Enabled>true</Enabled>
        <Minor>true</Minor>
        <BeforeOrAfter>false</BeforeOrAfter>
        <RegularExpressionOptions>IgnoreCase</RegularExpressionOptions>
      </Replacement>
      <Replacement>
        <Find>\\[\\[Power Level\\|Power Level( \\d)?\\]\\]</Find>
        <Replace>[[Power level]]$1</Replace>
        <Comment />
        <IsRegex>true</IsRegex>
        <Enabled>true</Enabled>
        <Minor>true</Minor>
        <BeforeOrAfter>false</BeforeOrAfter>
        <RegularExpressionOptions>IgnoreCase</RegularExpressionOptions>
      </Replacement>
      <Replacement>
        <Find>for \\[\\[Compost\\|Composting\\]\\]</Find>
        <Replace>for [[compost]]ing</Replace>
        <Comment />
        <IsRegex>true</IsRegex>
        <Enabled>true</Enabled>
        <Minor>true</Minor>
        <BeforeOrAfter>false</BeforeOrAfter>
        <RegularExpressionOptions>IgnoreCase</RegularExpressionOptions>
      </Replacement>
      <Replacement>
        <Find>the \\[\\[Player Character\\|Player\\]\\]</Find>
        <Replace>the [[player]]</Replace>
        <Comment />
        <IsRegex>true</IsRegex>
        <Enabled>true</Enabled>
        <Minor>true</Minor>
        <BeforeOrAfter>false</BeforeOrAfter>
        <RegularExpressionOptions>IgnoreCase</RegularExpressionOptions>
      </Replacement>
      [[Player Character|Player]]
      <Replacement>
        <Find>\\{\\{(Disambig)\\}\\}</Find>
        <!-- Fake replacement to make this more obvious. Disambiguation list caps should not be lowered. -->
        <Replace>{{$1}} ⚠⚠⚠</Replace>
        <Comment />
        <IsRegex>true</IsRegex>
        <Enabled>true</Enabled>
        <Minor>true</Minor>
        <BeforeOrAfter>false</BeforeOrAfter>
        <RegularExpressionOptions>IgnoreCase</RegularExpressionOptions>
      </Replacement>
"""

# Broad replacements should have AWB "ignore links etc." turned ON or they'll break things.
# Note that link hiding replaces [[link]] with ⌊⌊⌊⌊link⌋⌋⌋⌋ which is still usable as a negative match.
TEMPLATE_BROAD = """\
      <Replacement>
        <Find>\\b{escaped_1}\\b</Find>
        <Replace>{sentence_case_1}</Replace>
        <Comment />
        <IsRegex>true</IsRegex>
        <Enabled>true</Enabled>
        <Minor>true</Minor>
        <BeforeOrAfter>false</BeforeOrAfter>
        <RegularExpressionOptions>IgnoreCase</RegularExpressionOptions>
      </Replacement>
      <Replacement>
        <Find>\\b{escaped_2}\\b</Find>
        <Replace>{sentence_case_2}</Replace>
        <Comment />
        <IsRegex>true</IsRegex>
        <Enabled>true</Enabled>
        <Minor>true</Minor>
        <BeforeOrAfter>false</BeforeOrAfter>
        <RegularExpressionOptions>IgnoreCase</RegularExpressionOptions>
      </Replacement>
      <Replacement>
        <Find>(?&lt;=[a-zA-Z0-9,)⌋&amp;'"`])( |-)('+|\\()?{escaped_1}\\b</Find>
        <Replace>$1${{2}}{lower_case_1}</Replace>
        <Comment />
        <IsRegex>true</IsRegex>
        <Enabled>true</Enabled>
        <Minor>true</Minor>
        <BeforeOrAfter>false</BeforeOrAfter>
        <RegularExpressionOptions>IgnoreCase</RegularExpressionOptions>
      </Replacement>
      <Replacement>
        <Find>(?&lt;=[a-zA-Z0-9,)⌋&amp;'"`])( |-)('+|\\()?{escaped_2}\\b</Find>
        <Replace>$1${{2}}{lower_case_2}</Replace>
        <Comment />
        <IsRegex>true</IsRegex>
        <Enabled>true</Enabled>
        <Minor>true</Minor>
        <BeforeOrAfter>false</BeforeOrAfter>
        <RegularExpressionOptions>IgnoreCase</RegularExpressionOptions>
      </Replacement>
"""

# Plural version of Attack skill is impossible to regex away in nouns list
ADDITIONAL_BROAD = """\
      <Replacement>
        <Find>(?&lt;=[a-zA-Z0-9,)⌋&amp;'"`])( |-)Attacks</Find>
        <Replace>$1attacks</Replace>
        <Comment />
        <IsRegex>true</IsRegex>
        <Enabled>true</Enabled>
        <Minor>true</Minor>
        <BeforeOrAfter>false</BeforeOrAfter>
        <RegularExpressionOptions>IgnoreCase</RegularExpressionOptions>
      </Replacement>
      <Replacement>
        <Find>(?&lt;=[a-zA-Z0-9,)⌋&amp;'"`])( |-)Attack (it|them|her|him|the|with|from)</Find>
        <Replace>$1attack $2</Replace>
        <Comment />
        <IsRegex>true</IsRegex>
        <Enabled>true</Enabled>
        <Minor>true</Minor>
        <BeforeOrAfter>false</BeforeOrAfter>
        <RegularExpressionOptions>IgnoreCase</RegularExpressionOptions>
      </Replacement>
      <Replacement>
        <Find>(breath[ -]|an |parrying )Attack\\b</Find>
        <Replace>$1attack</Replace>
        <Comment />
        <IsRegex>true</IsRegex>
        <Enabled>true</Enabled>
        <Minor>true</Minor>
        <BeforeOrAfter>false</BeforeOrAfter>
        <RegularExpressionOptions>IgnoreCase</RegularExpressionOptions>
      </Replacement>
      <Replacement>
        <Find>(a) Ranged\\b</Find>
        <Replace>$1 ranged</Replace>
        <Comment />
        <IsRegex>true</IsRegex>
        <Enabled>true</Enabled>
        <Minor>true</Minor>
        <BeforeOrAfter>false</BeforeOrAfter>
        <RegularExpressionOptions>IgnoreCase</RegularExpressionOptions>
      </Replacement>
      <Replacement>
        <Find>(a) Magic\\b</Find>
        <Replace>$1 magic</Replace>
        <Comment />
        <IsRegex>true</IsRegex>
        <Enabled>true</Enabled>
        <Minor>true</Minor>
        <BeforeOrAfter>false</BeforeOrAfter>
        <RegularExpressionOptions>IgnoreCase</RegularExpressionOptions>
      </Replacement>
      <Replacement>
        <Find>(?&lt;=[a-zA-Z0-9,)⌋&amp;'"`]) Ranged(,)? (and|or) Magic</Find>
        <Replace> ranged$1 $2 magic</Replace>
        <Comment />
        <IsRegex>true</IsRegex>
        <Enabled>true</Enabled>
        <Minor>true</Minor>
        <BeforeOrAfter>false</BeforeOrAfter>
        <RegularExpressionOptions>IgnoreCase</RegularExpressionOptions>
      </Replacement>
      <Replacement>
        <Find>(?&lt;=[a-zA-Z0-9,)⌋&amp;'"`]) Magic(,)? (and|or) Ranged</Find>
        <Replace> magic$1 $2 ranged</Replace>
        <Comment />
        <IsRegex>true</IsRegex>
        <Enabled>true</Enabled>
        <Minor>true</Minor>
        <BeforeOrAfter>false</BeforeOrAfter>
        <RegularExpressionOptions>IgnoreCase</RegularExpressionOptions>
      </Replacement>
      <Replacement>
        <Find>(from|while|by) Mining</Find>
        <Replace>$1 mining</Replace>
        <Comment />
        <IsRegex>true</IsRegex>
        <Enabled>true</Enabled>
        <Minor>true</Minor>
        <BeforeOrAfter>false</BeforeOrAfter>
        <RegularExpressionOptions>IgnoreCase</RegularExpressionOptions>
      </Replacement>
      <Replacement>
        <Find>(?&lt;=[a-zA-Z0-9,)⌋&amp;'"`]) getting started with</Find>
        <Replace> getting started with</Replace>
        <Comment />
        <IsRegex>true</IsRegex>
        <Enabled>true</Enabled>
        <Minor>true</Minor>
        <BeforeOrAfter>false</BeforeOrAfter>
        <RegularExpressionOptions>IgnoreCase</RegularExpressionOptions>
      </Replacement>
      <Replacement>
        <Find>(a|little) shelter</Find>
        <Replace>$1 shelter</Replace>
        <Comment />
        <IsRegex>true</IsRegex>
        <Enabled>true</Enabled>
        <Minor>true</Minor>
        <BeforeOrAfter>false</BeforeOrAfter>
        <RegularExpressionOptions>IgnoreCase</RegularExpressionOptions>
      </Replacement>
      <Replacement>
        <Find>(?&lt;=[a-zA-Z0-9,)⌋&amp;'"`]) shelter (from)</Find>
        <Replace> shelter $1</Replace>
        <Comment />
        <IsRegex>true</IsRegex>
        <Enabled>true</Enabled>
        <Minor>true</Minor>
        <BeforeOrAfter>false</BeforeOrAfter>
        <RegularExpressionOptions>IgnoreCase</RegularExpressionOptions>
      </Replacement>
"""

def main():
    if len(sys.argv) != 2:
        print(f"Usage: `{sys.argv[0]} list.txt` # Will output list-broad.xml and list-narrow.xml")
        sys.exit(1)

    input_file = sys.argv[1]
    input_path = Path(input_file)
    output_narrow = input_path.with_name(f"{input_path.stem}-narrow{input_path.suffix}")
    output_broad = input_path.with_name(f"{input_path.stem}-broad{input_path.suffix}")

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
            sentence = escape_xml(sentence)
            lower = escape_xml(lower)

            sentence_1 = escape_xml(sentence_1)
            lower_1 = escape_xml(lower_1)

            sentence_2 = escape_xml(sentence_2)
            lower_2 = escape_xml(lower_2)

            # Then ALSO escape regex for the "Find" (but not "Replace") fields.
            x_lower = escape_regex(lower)
            x_lower_1 = escape_regex(lower_1)
            x_lower_2 = escape_regex(lower_2)

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
            ))

        fout_narrow.write(ADDITIONAL_NARROW)
        fout_broad.write(ADDITIONAL_BROAD)

    print("Done.")

if __name__ == "__main__":
    main()
