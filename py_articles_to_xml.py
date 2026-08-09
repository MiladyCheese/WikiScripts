#!/usr/bin/env python3

import re
import sys
from pathlib import Path

import inflect
p = inflect.engine()

from util_nouns import restore_proper_nouns

# Usage:
    # - Run this script on your list of Special:AllPages to generate XML
    # - Paste XML into an AWB settings file at the appropriate location
    # - Load settings file in AWB
    # - Run "find and replace" on whatever AWB list you want

def escape_xml(text):
    return text \
        .replace("&", "&amp;")

def escape_regex(text):
    return text \
        .replace("\\", "\\\\") \
        .replace("/", "\\/") \
        .replace("(", "\\(") \
        .replace(")", "\\)") \
        .replace("[", "\\[") \
        .replace("]", "\\]") \
        .replace(".", "\\.") \
        .replace("*", "\\*") \
        .replace("+", "\\+") \
        .replace("?", "\\?") \
        .replace("^", "\\^") \
        .replace("$", "\\$")

def original_case(text):
    return text

def sentence_case(text):
    text = restore_proper_nouns(text.lower())
    text = text[0].upper() + text[1:]
    return text

def lower_case(text):
    text = restore_proper_nouns(text.lower())
    return text

# This method fixes the weird behavior of inflect, e.g.
#    >>> p.singular_noun("cows")
#    'cow'
#    >>> p.singular_noun("cow")
#    False # wrong
def _singular(word):
    return p.singular_noun(word) or word

def singular(text):
    tokens = text.split()
    last_word = tokens.pop()
    tokens.append(_singular(last_word))
    return " ".join(tokens)

# This method fixes the weird behavior of inflect, e.g.
#    >>> p.plural_noun("cow")
#    'cows'
#    >>> p.plural_noun("cows")
#    'cowss' # wrong
def _plural(word):
    if p.singular_noun(word): # returns False if already singular
        return word # already plural
    return p.plural_noun(word)

def plural(text):
    tokens = text.split()
    last_word = tokens.pop()
    tokens.append(_plural(last_word))
    return " ".join(tokens)

# Narrow replacements should have AWB "ignore links etc." turned OFF or they won't accomplish much.
TEMPLATE_NARROW = """\
      <Replacement>
        <Find>(?&lt;=[a-zA-Z0-9,)\\]&amp;'"`]) (\\()?\\[\\[{x_original_case}\\]\\]</Find>
        <Replace> $1[[{lower_case}]]</Replace>
        <Comment />
        <IsRegex>true</IsRegex>
        <Enabled>true</Enabled>
        <Minor>true</Minor>
        <BeforeOrAfter>false</BeforeOrAfter>
        <RegularExpressionOptions>None</RegularExpressionOptions>
      </Replacement>
      <Replacement>
        <Find>(?&lt;=[a-zA-Z0-9,)\\]&amp;'"`]) (\\()?\\[\\[{x_original_case}\\|({x_sentence_case_2}|{x_original_case_2})\\]\\]</Find>
        <!-- Redirect from singular to plural. Purposely refer to same-case version so that AWB then pluralizes like `[[original]]s` automatically -->
        <Replace> $1[[{lower_case}|{lower_case_2}]]</Replace>
        <Comment />
        <IsRegex>true</IsRegex>
        <Enabled>true</Enabled>
        <Minor>true</Minor>
        <BeforeOrAfter>false</BeforeOrAfter>
        <RegularExpressionOptions>None</RegularExpressionOptions>
      </Replacement>
      <Replacement>
        <Find>(?&lt;=[a-zA-Z0-9,)\\]&amp;'"`]) (\\()?\\[\\[{x_original_case}\\|({x_sentence_case_1}|{x_original_case_1})\\]\\]</Find>
        <!-- Otherwise redirect from plural to singular. -->
        <Replace> $1[[{original_case}|{lower_case_1}]]</Replace>
        <Comment />
        <IsRegex>true</IsRegex>
        <Enabled>true</Enabled>
        <Minor>true</Minor>
        <BeforeOrAfter>false</BeforeOrAfter>
        <RegularExpressionOptions>None</RegularExpressionOptions>
      </Replacement>
      <Replacement>
        <Find>\\[\\[{x_original_case}\\|({x_lower_case}|{x_sentence_case}|{x_original_case})\\]\\]</Find>
        <Replace>[[$1]]</Replace>
        <Comment />
        <IsRegex>true</IsRegex>
        <Enabled>true</Enabled>
        <Minor>true</Minor>
        <BeforeOrAfter>false</BeforeOrAfter>
        <RegularExpressionOptions>None</RegularExpressionOptions>
      </Replacement>
      <Replacement>
        <Find>\\[\\[{x_original_case}\\]\\]</Find>
        <Replace>[[{sentence_case}]]</Replace>
        <Comment />
        <IsRegex>true</IsRegex>
        <Enabled>true</Enabled>
        <Minor>true</Minor>
        <BeforeOrAfter>false</BeforeOrAfter>
        <RegularExpressionOptions>None</RegularExpressionOptions>
      </Replacement>
"""

ADDITIONAL_NARROW = """\
      <Replacement>
        <Find>(?&lt;=[a-zA-Z0-9,)\\]&amp;'"`]) \\[\\[[Pp]ower [Ll]evel\\|[Pp]ower [Ll]evel( \\d)?\\]\\]</Find>
        <Replace> [[power level]]$1</Replace>
        <Comment />
        <IsRegex>true</IsRegex>
        <Enabled>true</Enabled>
        <Minor>true</Minor>
        <BeforeOrAfter>false</BeforeOrAfter>
        <RegularExpressionOptions>None</RegularExpressionOptions>
      </Replacement>
      <Replacement>
        <Find>\\[\\[[Pp]ower [Ll]evel\\|[Pp]ower [Ll]evel( \\d)?\\]\\]</Find>
        <Replace>[[Power level]]$1</Replace>
        <Comment />
        <IsRegex>true</IsRegex>
        <Enabled>true</Enabled>
        <Minor>true</Minor>
        <BeforeOrAfter>false</BeforeOrAfter>
        <RegularExpressionOptions>None</RegularExpressionOptions>
      </Replacement>
      <Replacement>
        <Find>\\|[Pp]ower [Ll]evel</Find>
        <Replace>|power level</Replace>
        <Comment />
        <IsRegex>true</IsRegex>
        <Enabled>true</Enabled>
        <Minor>true</Minor>
        <BeforeOrAfter>false</BeforeOrAfter>
        <RegularExpressionOptions>None</RegularExpressionOptions>
      </Replacement>
      <Replacement>
        <Find>for \\[\\[Compost\\|Composting\\]\\]</Find>
        <Replace>for [[compost]]ing</Replace>
        <Comment />
        <IsRegex>true</IsRegex>
        <Enabled>true</Enabled>
        <Minor>true</Minor>
        <BeforeOrAfter>false</BeforeOrAfter>
        <RegularExpressionOptions>None</RegularExpressionOptions>
      </Replacement>
"""

# Broad replacements should have AWB "ignore links etc." turned ON or they'll break things.
TEMPLATE_BROAD = """\
      <Replacement>
        <Find>(?&lt;=[a-zA-Z0-9,)\\]&amp;'"`]) ('+|\\()?{x_original_case_1}\\b</Find>
        <Replace> ${{1}}{lower_case_1}</Replace>
        <Comment />
        <IsRegex>true</IsRegex>
        <Enabled>true</Enabled>
        <Minor>true</Minor>
        <BeforeOrAfter>false</BeforeOrAfter>
        <RegularExpressionOptions>None</RegularExpressionOptions>
      </Replacement>
      <Replacement>
        <Find>(?&lt;=[a-zA-Z0-9,)\\]&amp;'"`]) ('+|\\()?{x_original_case_2}\\b</Find>
        <Replace> ${{1}}{lower_case_2}</Replace>
        <Comment />
        <IsRegex>true</IsRegex>
        <Enabled>true</Enabled>
        <Minor>true</Minor>
        <BeforeOrAfter>false</BeforeOrAfter>
        <RegularExpressionOptions>None</RegularExpressionOptions>
      </Replacement>
      <Replacement>
        <Find>\\b{x_original_case_1}\\b</Find>
        <Replace>{sentence_case_1}</Replace>
        <Comment />
        <IsRegex>true</IsRegex>
        <Enabled>true</Enabled>
        <Minor>true</Minor>
        <BeforeOrAfter>false</BeforeOrAfter>
        <RegularExpressionOptions>None</RegularExpressionOptions>
      </Replacement>
      <Replacement>
        <Find>\\b{x_original_case_2}\\b</Find>
        <Replace>{sentence_case_2}</Replace>
        <Comment />
        <IsRegex>true</IsRegex>
        <Enabled>true</Enabled>
        <Minor>true</Minor>
        <BeforeOrAfter>false</BeforeOrAfter>
        <RegularExpressionOptions>None</RegularExpressionOptions>
      </Replacement>
"""

# Fix a few things that are hard to do right (e.g. stone should be lowercase and matches later after Dreaming Stone).
ADDITIONAL_BROAD = """\
      <Replacement>
        <Find>\\b[Dd]reaming [Ss]tone\\b</Find>
        <Replace>Dreaming Stone</Replace>
        <Comment />
        <IsRegex>true</IsRegex>
        <Enabled>true</Enabled>
        <Minor>true</Minor>
        <BeforeOrAfter>false</BeforeOrAfter>
        <RegularExpressionOptions>None</RegularExpressionOptions>
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
            original = line.strip()
            if not original:
                continue

            # First create the cases...
            original = original_case(original)
            sentence = sentence_case(original)
            lower = lower_case(original)

            original_1 = singular(original)
            sentence_1 = singular(sentence)
            lower_1 = singular(lower)

            original_2 = plural(original)
            sentence_2 = plural(sentence)
            lower_2 = plural(lower)

            # Then escape each one as a final pass (to avoid repeat-escaping above)...
            original = escape_xml(original)
            sentence = escape_xml(sentence)
            lower = escape_xml(lower)

            original_1 = escape_xml(original_1)
            sentence_1 = escape_xml(sentence_1)
            lower_1 = escape_xml(lower_1)

            original_2 = escape_xml(original_2)
            sentence_2 = escape_xml(sentence_2)
            lower_2 = escape_xml(lower_2)

            # Then ALSO escape regex for the "Find" (but not "Replace") fields.
            x_original = escape_regex(original)
            x_sentence = escape_regex(sentence)
            x_lower = escape_regex(lower)

            x_original_1 = escape_regex(original_1)
            x_sentence_1 = escape_regex(sentence_1)
            x_lower_1 = escape_regex(lower_1)

            x_original_2 = escape_regex(original_2)
            x_sentence_2 = escape_regex(sentence_2)
            x_lower_2 = escape_regex(lower_2)

            if count % 200 == 0:
                print(".", end="", flush=True)

            # Debug plurality:
            #print(f"{original} (1 {original_1}; 2 {original_2})...")

            fout_narrow.write(TEMPLATE_NARROW.format(
                original_case=original,
                sentence_case=sentence,
                lower_case=lower,
                original_case_1=original_1,
                sentence_case_1=sentence_1,
                lower_case_1=lower_1,
                original_case_2=original_2,
                sentence_case_2=sentence_2,
                lower_case_2=lower_2,

                x_original_case=x_original,
                x_sentence_case=x_sentence,
                x_lower_case=x_lower,
                x_original_case_1=x_original_1,
                x_sentence_case_1=x_sentence_1,
                x_lower_case_1=x_lower_1,
                x_original_case_2=x_original_2,
                x_sentence_case_2=x_sentence_2,
                x_lower_case_2=x_lower_2,
            ))

            fout_broad.write(TEMPLATE_BROAD.format(
                original_case=original,
                sentence_case=sentence,
                lower_case=lower,
                original_case_1=original_1,
                sentence_case_1=sentence_1,
                lower_case_1=lower_1,
                original_case_2=original_2,
                sentence_case_2=sentence_2,
                lower_case_2=lower_2,

                x_original_case=x_original,
                x_sentence_case=x_sentence,
                x_lower_case=x_lower,
                x_original_case_1=x_original_1,
                x_sentence_case_1=x_sentence_1,
                x_lower_case_1=x_lower_1,
                x_original_case_2=x_original_2,
                x_sentence_case_2=x_sentence_2,
                x_lower_case_2=x_lower_2,
            ))

            count += 1

        fout_narrow.write(ADDITIONAL_NARROW)
        fout_broad.write(ADDITIONAL_BROAD)

    print("Done.")

if __name__ == "__main__":
    main()
