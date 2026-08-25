#!/usr/bin/env python3

import re
import sys
from pathlib import Path
import importlib

import inflect
p = inflect.engine()

from util_nouns import restore_proper_nouns, singular, plural, restart

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

# Add \b to the back only if appropriate ("Wanted!" is an example of a tricky word)
def escape_regex_boundBack(text):
    needs_back = re.search(r"\W$", text) is None
    return f"{escape_regex(text)}{"\\b" if needs_back else ""}"

# Add \b to the front + back only if appropriate ("Wanted!" is an example of a tricky word)
def escape_regex_boundBoth(text):
    needs_front = re.search(r"^\W", text) is None
    return f"{"\\b" if needs_front else ""}{escape_regex_boundBack(text)}"

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
        <Find>\\[\\[{escaped}\\|{escaped_2}\\]\\]</Find>
        <Replace>[[{sentence_case}|{sentence_case_2}]]</Replace>
        <Comment />
        <IsRegex>true</IsRegex>
        <Enabled>true</Enabled>
        <Minor>true</Minor>
        <BeforeOrAfter>false</BeforeOrAfter>
        <RegularExpressionOptions>IgnoreCase</RegularExpressionOptions>
      </Replacement>
      <Replacement>
        <Find>(?&lt;=[a-zA-Z0-9,%)>/\\]&amp;'"`])([ /-])(\\()?\\[\\[{escaped}\\]\\]</Find>
        <Replace>$1$2[[{lower_case}]]</Replace>
        <Comment />
        <IsRegex>true</IsRegex>
        <Enabled>true</Enabled>
        <Minor>true</Minor>
        <BeforeOrAfter>false</BeforeOrAfter>
        <RegularExpressionOptions>IgnoreCase</RegularExpressionOptions>
      </Replacement>
      <Replacement>
        <Find>(?&lt;=[a-zA-Z0-9,%)>/\\]&amp;'"`])([ /-])(\\()?\\[\\[{escaped}\\|({escaped_2})\\]\\]</Find>
        <Replace>$1$2[[{lower_case}|{lower_case_2}]]</Replace>
        <Comment />
        <IsRegex>true</IsRegex>
        <Enabled>true</Enabled>
        <Minor>true</Minor>
        <BeforeOrAfter>false</BeforeOrAfter>
        <RegularExpressionOptions>IgnoreCase</RegularExpressionOptions>
      </Replacement>
      <Replacement>
        <Find>(?&lt;=[a-zA-Z0-9,%)>/\\]&amp;'"`])([ /-])(\\()?\\[\\[({escaped})\\|({escaped_1})\\]\\]</Find>
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
        <Find>(?&lt;=[a-zA-Z0-9,%)>/\\]&amp;'"`])( |-)\\[\\[Power Level\\|Power Level( \\d)?\\]\\]</Find>
        <Replace>$1[[power level]]$2</Replace>
        <Comment />
        <IsRegex>true</IsRegex>
        <Enabled>true</Enabled>
        <Minor>true</Minor>
        <BeforeOrAfter>false</BeforeOrAfter>
        <RegularExpressionOptions>IgnoreCase</RegularExpressionOptions>
      </Replacement>
      <Replacement>
        <Find>(?&lt;=[a-zA-Z0-9,%)>/\\]&amp;'"`])( |-)\\[\\[Power Level\\|Tier( \\d)?\\]\\]</Find>
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
        <Find>he \\[\\[Garou \\(race\\)\\|Garou\\]\\] series</Find>
        <Replace>he Garou series</Replace>
        <Comment />
        <IsRegex>true</IsRegex>
        <Enabled>true</Enabled>
        <Minor>true</Minor>
        <BeforeOrAfter>false</BeforeOrAfter>
        <RegularExpressionOptions>IgnoreCase</RegularExpressionOptions>
      </Replacement>
      <Replacement>
        <Find>he \\[\\[Dragonkin \\(race\\)\\|Dragonkin\\]\\] series</Find>
        <Replace>he Dragonkin series</Replace>
        <Comment />
        <IsRegex>true</IsRegex>
        <Enabled>true</Enabled>
        <Minor>true</Minor>
        <BeforeOrAfter>false</BeforeOrAfter>
        <RegularExpressionOptions>IgnoreCase</RegularExpressionOptions>
      </Replacement>
      <Replacement>
        <Find>(?&lt;=[a-zA-Z0-9,%)>/\\]&amp;'"`]) \\[\\[Garou \\(race\\)\\|Garou\\]\\]</Find>
        <Replace> [[Garou (race)|garou]]</Replace>
        <Comment />
        <IsRegex>true</IsRegex>
        <Enabled>true</Enabled>
        <Minor>true</Minor>
        <BeforeOrAfter>false</BeforeOrAfter>
        <RegularExpressionOptions>IgnoreCase</RegularExpressionOptions>
      </Replacement>
      <Replacement>
        <Find>Moon \\[\\[(Garou \\(race\\)\\|)?Garou\\]\\]</Find>
        <Replace>Moon [[$1Garou]]</Replace>
        <Comment />
        <IsRegex>true</IsRegex>
        <Enabled>true</Enabled>
        <Minor>true</Minor>
        <BeforeOrAfter>false</BeforeOrAfter>
        <RegularExpressionOptions>IgnoreCase</RegularExpressionOptions>
      </Replacement>
      <Replacement>
        <Find>Lunar \\[\\[(Garou \\(race\\)\\|)?Garou\\]\\]</Find>
        <Replace>Lunar [[$1Garou]]</Replace>
        <Comment />
        <IsRegex>true</IsRegex>
        <Enabled>true</Enabled>
        <Minor>true</Minor>
        <BeforeOrAfter>false</BeforeOrAfter>
        <RegularExpressionOptions>IgnoreCase</RegularExpressionOptions>
      </Replacement>
      <Replacement>
        <Find>(?&lt;=[a-zA-Z0-9,%)>/\\]&amp;'"`]) \\[\\[Dragonkin \\(race\\)\\|Dragonkin\\]\\]</Find>
        <Replace> [[Dragonkin (race)|dragonkin]]</Replace>
        <Comment />
        <IsRegex>true</IsRegex>
        <Enabled>true</Enabled>
        <Minor>true</Minor>
        <BeforeOrAfter>false</BeforeOrAfter>
        <RegularExpressionOptions>IgnoreCase</RegularExpressionOptions>
      </Replacement>
      <Replacement>
        <Find>(?&lt;=[a-zA-Z0-9,%)>/\\]&amp;'"`]) \\[\\[Dragonkin Vault\\|Vault\\]\\]</Find>
        <Replace> [[dragonkin vault|vault]]</Replace>
        <Comment />
        <IsRegex>true</IsRegex>
        <Enabled>true</Enabled>
        <Minor>true</Minor>
        <BeforeOrAfter>false</BeforeOrAfter>
        <RegularExpressionOptions>IgnoreCase</RegularExpressionOptions>
      </Replacement>
      <Replacement>
        <Find>the \\[\\[Player Character(\\|Player)?\\]\\]</Find>
        <Replace>the [[player]]</Replace>
        <Comment />
        <IsRegex>true</IsRegex>
        <Enabled>true</Enabled>
        <Minor>true</Minor>
        <BeforeOrAfter>false</BeforeOrAfter>
        <RegularExpressionOptions>IgnoreCase</RegularExpressionOptions>
      </Replacement>
      <Replacement>
        <Find>(?&lt;=[a-zA-Z0-9,%)>/\\]&amp;'"`]) \\[\\[Wither\\]\\](ed|ing)</Find>
        <Replace> [[wither]]$1</Replace>
        <Comment />
        <IsRegex>true</IsRegex>
        <Enabled>true</Enabled>
        <Minor>true</Minor>
        <BeforeOrAfter>false</BeforeOrAfter>
        <RegularExpressionOptions>IgnoreCase</RegularExpressionOptions>
      </Replacement>
      <Replacement>
        <Find>(?&lt;=[a-zA-Z0-9,%)>/⌋&amp;'"`]) \\[\\[Ranged\\]\\](,)? (and|or) \\[\\[Magic\\]\\]</Find>
        <Replace> [[ranged]]$1 $2 [[magic]]</Replace>
        <Comment />
        <IsRegex>true</IsRegex>
        <Enabled>true</Enabled>
        <Minor>true</Minor>
        <BeforeOrAfter>false</BeforeOrAfter>
        <RegularExpressionOptions>IgnoreCase</RegularExpressionOptions>
      </Replacement>
      <Replacement>
        <Find>(?&lt;=[a-zA-Z0-9,%)>/⌋&amp;'"`]) \\[\\[Magic\\]\\](,)? (and|or) \\[\\[Ranged\\]\\]</Find>
        <Replace> [[magic]]$1 $2 [[ranged]]</Replace>
        <Comment />
        <IsRegex>true</IsRegex>
        <Enabled>true</Enabled>
        <Minor>true</Minor>
        <BeforeOrAfter>false</BeforeOrAfter>
        <RegularExpressionOptions>IgnoreCase</RegularExpressionOptions>
      </Replacement>
      <Replacement>
        <Find>(?&lt;=[a-zA-Z0-9,%)>/⌋&amp;'"`]) \\[\\[Melee((\\]\\])? (\\[\\[)?(armour|equipment|weapon|attack))</Find>
        <Replace> [[melee$1</Replace>
        <Comment />
        <IsRegex>true</IsRegex>
        <Enabled>true</Enabled>
        <Minor>true</Minor>
        <BeforeOrAfter>false</BeforeOrAfter>
        <RegularExpressionOptions>IgnoreCase</RegularExpressionOptions>
      </Replacement>
      <Replacement>
        <Find>(?&lt;=[a-zA-Z0-9,%)>/⌋&amp;'"`]) \\[\\[Ranged((\\]\\])? (\\[\\[)?(armour|equipment|weapon|attack))</Find>
        <Replace> [[ranged$1</Replace>
        <Comment />
        <IsRegex>true</IsRegex>
        <Enabled>true</Enabled>
        <Minor>true</Minor>
        <BeforeOrAfter>false</BeforeOrAfter>
        <RegularExpressionOptions>IgnoreCase</RegularExpressionOptions>
      </Replacement>
      <Replacement>
        <Find>(?&lt;=[a-zA-Z0-9,%)>/⌋&amp;'"`]) \\[\\[Magic(al)?((\\]\\])? (\\[\\[)?(armour|equipment|weapon|attack))</Find>
        <Replace> [[magic$1$2</Replace>
        <Comment />
        <IsRegex>true</IsRegex>
        <Enabled>true</Enabled>
        <Minor>true</Minor>
        <BeforeOrAfter>false</BeforeOrAfter>
        <RegularExpressionOptions>IgnoreCase</RegularExpressionOptions>
      </Replacement>
      <Replacement>
        <Find>(for|in) \\[\\[Construction\\]\\]</Find>
        <Replace>$1 [[construction]]</Replace>
        <Comment />
        <IsRegex>true</IsRegex>
        <Enabled>true</Enabled>
        <Minor>true</Minor>
        <BeforeOrAfter>false</BeforeOrAfter>
        <RegularExpressionOptions>IgnoreCase</RegularExpressionOptions>
      </Replacement>
      <Replacement>
        <Find>(after) \\[\\[Mining\\]\\]</Find>
        <Replace>$1 [[mining]]</Replace>
        <Comment />
        <IsRegex>true</IsRegex>
        <Enabled>true</Enabled>
        <Minor>true</Minor>
        <BeforeOrAfter>false</BeforeOrAfter>
        <RegularExpressionOptions>IgnoreCase</RegularExpressionOptions>
      </Replacement>
      <Replacement>
        <Find>\\{\\{(Disambig(uation)?)\\}\\}</Find>
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
        <Find>{b_escaped_1_b}</Find>
        <Replace>{sentence_case_1}</Replace>
        <Comment />
        <IsRegex>true</IsRegex>
        <Enabled>true</Enabled>
        <Minor>true</Minor>
        <BeforeOrAfter>false</BeforeOrAfter>
        <RegularExpressionOptions>IgnoreCase</RegularExpressionOptions>
      </Replacement>
      <Replacement>
        <Find>{b_escaped_2_b}</Find>
        <Replace>{sentence_case_2}</Replace>
        <Comment />
        <IsRegex>true</IsRegex>
        <Enabled>true</Enabled>
        <Minor>true</Minor>
        <BeforeOrAfter>false</BeforeOrAfter>
        <RegularExpressionOptions>IgnoreCase</RegularExpressionOptions>
      </Replacement>
      <Replacement>
        <Find>(?&lt;=[a-zA-Z0-9,%)>/⌋&amp;'"`])([ /-])('+|\\()?{escaped_1_b}</Find>
        <Replace>$1${{2}}{lower_case_1}</Replace>
        <Comment />
        <IsRegex>true</IsRegex>
        <Enabled>true</Enabled>
        <Minor>true</Minor>
        <BeforeOrAfter>false</BeforeOrAfter>
        <RegularExpressionOptions>IgnoreCase</RegularExpressionOptions>
      </Replacement>
      <Replacement>
        <Find>(?&lt;=[a-zA-Z0-9,%)>/⌋&amp;'"`])([ /-])('+|\\()?{escaped_2_b}</Find>
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
        <Find>(?&lt;=[a-zA-Z0-9,%)>/⌋&amp;'"`])( |-)Attacks</Find>
        <Replace>$1attacks</Replace>
        <Comment />
        <IsRegex>true</IsRegex>
        <Enabled>true</Enabled>
        <Minor>true</Minor>
        <BeforeOrAfter>false</BeforeOrAfter>
        <RegularExpressionOptions>IgnoreCase</RegularExpressionOptions>
      </Replacement>
      <Replacement>
        <Find>(?&lt;=[a-zA-Z0-9,%)>/⌋&amp;'"`])( |-)Attack (is|it|them|her|him|the|with|from|where|speed)</Find>
        <Replace>$1attack $2</Replace>
        <Comment />
        <IsRegex>true</IsRegex>
        <Enabled>true</Enabled>
        <Minor>true</Minor>
        <BeforeOrAfter>false</BeforeOrAfter>
        <RegularExpressionOptions>IgnoreCase</RegularExpressionOptions>
      </Replacement>
      <Replacement>
        <Find>(breath|based|an|to|will|parrying|magic|'s) Attack\\b</Find>
        <Replace>$1 attack</Replace>
        <Comment />
        <IsRegex>true</IsRegex>
        <Enabled>true</Enabled>
        <Minor>true</Minor>
        <BeforeOrAfter>false</BeforeOrAfter>
        <RegularExpressionOptions>IgnoreCase</RegularExpressionOptions>
      </Replacement>
      <Replacement>
        <Find>(a|to|for|use|using|wielding) Melee\\b</Find>
        <Replace>$1 melee</Replace>
        <Comment />
        <IsRegex>true</IsRegex>
        <Enabled>true</Enabled>
        <Minor>true</Minor>
        <BeforeOrAfter>false</BeforeOrAfter>
        <RegularExpressionOptions>IgnoreCase</RegularExpressionOptions>
      </Replacement>
      <Replacement>
        <Find>(a|to|for|use|using|wielding) Ranged\\b</Find>
        <Replace>$1 ranged</Replace>
        <Comment />
        <IsRegex>true</IsRegex>
        <Enabled>true</Enabled>
        <Minor>true</Minor>
        <BeforeOrAfter>false</BeforeOrAfter>
        <RegularExpressionOptions>IgnoreCase</RegularExpressionOptions>
      </Replacement>
      <Replacement>
        <Find>(a|to|for|use|using|wielding|air|water|earth|fire) Magic\\b</Find>
        <Replace>$1 magic</Replace>
        <Comment />
        <IsRegex>true</IsRegex>
        <Enabled>true</Enabled>
        <Minor>true</Minor>
        <BeforeOrAfter>false</BeforeOrAfter>
        <RegularExpressionOptions>IgnoreCase</RegularExpressionOptions>
      </Replacement>
      <Replacement>
        <Find>(?&lt;=[a-zA-Z0-9,%)>/⌋&amp;'"`]) Magic dart</Find>
        <Replace> magic dart</Replace>
        <Comment />
        <IsRegex>true</IsRegex>
        <Enabled>true</Enabled>
        <Minor>true</Minor>
        <BeforeOrAfter>false</BeforeOrAfter>
        <RegularExpressionOptions>IgnoreCase</RegularExpressionOptions>
      </Replacement>
      <Replacement>
        <Find>(?&lt;=[a-zA-Z0-9,%)>/⌋&amp;'"`]) Ranged(,)? (and|or) Magic</Find>
        <Replace> ranged$1 $2 magic</Replace>
        <Comment />
        <IsRegex>true</IsRegex>
        <Enabled>true</Enabled>
        <Minor>true</Minor>
        <BeforeOrAfter>false</BeforeOrAfter>
        <RegularExpressionOptions>IgnoreCase</RegularExpressionOptions>
      </Replacement>
      <Replacement>
        <Find>(?&lt;=[a-zA-Z0-9,%)>/⌋&amp;'"`]) Magic(,)? (and|or) Ranged</Find>
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
        <Find>(?&lt;=[a-zA-Z0-9,%)>/⌋&amp;'"`]) Mining (node)</Find>
        <Replace> mining $1</Replace>
        <Comment />
        <IsRegex>true</IsRegex>
        <Enabled>true</Enabled>
        <Minor>true</Minor>
        <BeforeOrAfter>false</BeforeOrAfter>
        <RegularExpressionOptions>IgnoreCase</RegularExpressionOptions>
      </Replacement>
      <Replacement>
        <Find>(for|in) Construction</Find>
        <Replace>$1 construction</Replace>
        <Comment />
        <IsRegex>true</IsRegex>
        <Enabled>true</Enabled>
        <Minor>true</Minor>
        <BeforeOrAfter>false</BeforeOrAfter>
        <RegularExpressionOptions>IgnoreCase</RegularExpressionOptions>
      </Replacement>
      <Replacement>
        <Find>(by|while|whilst) Cooking</Find>
        <Replace>$1 cooking</Replace>
        <Comment />
        <IsRegex>true</IsRegex>
        <Enabled>true</Enabled>
        <Minor>true</Minor>
        <BeforeOrAfter>false</BeforeOrAfter>
        <RegularExpressionOptions>IgnoreCase</RegularExpressionOptions>
      </Replacement>
      <Replacement>
        <Find>(?&lt;=[a-zA-Z0-9,%)>/⌋&amp;'"`]) Cooking (a)</Find>
        <Replace> cooking $1</Replace>
        <Comment />
        <IsRegex>true</IsRegex>
        <Enabled>true</Enabled>
        <Minor>true</Minor>
        <BeforeOrAfter>false</BeforeOrAfter>
        <RegularExpressionOptions>IgnoreCase</RegularExpressionOptions>
      </Replacement>
      <Replacement>
        <Find>(by|for) Farming</Find>
        <Replace>$1 farming</Replace>
        <Comment />
        <IsRegex>true</IsRegex>
        <Enabled>true</Enabled>
        <Minor>true</Minor>
        <BeforeOrAfter>false</BeforeOrAfter>
        <RegularExpressionOptions>IgnoreCase</RegularExpressionOptions>
      </Replacement>
      <Replacement>
        <Find>(?&lt;=[a-zA-Z0-9,%)>/⌋&amp;'"`]) getting started with</Find>
        <Replace> getting started with</Replace>
        <Comment />
        <IsRegex>true</IsRegex>
        <Enabled>true</Enabled>
        <Minor>true</Minor>
        <BeforeOrAfter>false</BeforeOrAfter>
        <RegularExpressionOptions>IgnoreCase</RegularExpressionOptions>
      </Replacement>
      <Replacement>
        <Find>the goblin series</Find>
        <Replace>the Goblin series</Replace>
        <Comment />
        <IsRegex>true</IsRegex>
        <Enabled>true</Enabled>
        <Minor>true</Minor>
        <BeforeOrAfter>false</BeforeOrAfter>
        <RegularExpressionOptions>IgnoreCase</RegularExpressionOptions>
      </Replacement>
      <Replacement>
        <Find>the garou series</Find>
        <Replace>the Garou series</Replace>
        <Comment />
        <IsRegex>true</IsRegex>
        <Enabled>true</Enabled>
        <Minor>true</Minor>
        <BeforeOrAfter>false</BeforeOrAfter>
        <RegularExpressionOptions>IgnoreCase</RegularExpressionOptions>
      </Replacement>
      <Replacement>
        <Find>the dragon attack series</Find>
        <Replace>the Dragon Attack series</Replace>
        <Comment />
        <IsRegex>true</IsRegex>
        <Enabled>true</Enabled>
        <Minor>true</Minor>
        <BeforeOrAfter>false</BeforeOrAfter>
        <RegularExpressionOptions>IgnoreCase</RegularExpressionOptions>
      </Replacement>
      <Replacement>
        <Find>spells tab</Find>
        <Replace>Spells tab</Replace>
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
        <Find>(?&lt;=[a-zA-Z0-9,%)>/⌋&amp;'"`]) shelter(ed)? (from)</Find>
        <Replace> shelter$1 $2</Replace>
        <Comment />
        <IsRegex>true</IsRegex>
        <Enabled>true</Enabled>
        <Minor>true</Minor>
        <BeforeOrAfter>false</BeforeOrAfter>
        <RegularExpressionOptions>IgnoreCase</RegularExpressionOptions>
      </Replacement>
      <Replacement>
        <Find>(?:(?&lt;!on |'s |of |at )(?&lt;!his |her |per |the )(?&lt;!each )(?&lt;!their ))Death(?! of)</Find>
        <Replace>Death</Replace>
        <Comment />
        <IsRegex>true</IsRegex>
        <Enabled>true</Enabled>
        <Minor>true</Minor>
        <BeforeOrAfter>false</BeforeOrAfter>
        <RegularExpressionOptions>IgnoreCase</RegularExpressionOptions>
      </Replacement>
"""

def generate(input_file, output_narrow, output_broad):
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

    print("Done generating XML.")

def main():
    if len(sys.argv) != 2:
        print(f"Usage: `{sys.argv[0]} list.txt` # Will output list-broad.xml and list-narrow.xml")
        sys.exit(1)

    input_file = sys.argv[1]
    input_path = Path(input_file)
    output_narrow = input_path.with_name(f"{input_path.stem}-narrow.xml")
    output_broad = input_path.with_name(f"{input_path.stem}-broad.xml")

    while True:
        # First time is automatic
        generate(input_file, output_narrow, output_broad)

        # Then daemonise (because loading the `inflect` library + compiling regexes on startup is slow)
        print("Press enter to regen if nouns have changed (or type 'r' to fully reload if templates have changed):")
        line = input()

        if line.lower() == "r":
            restart()

        # else continue
        importlib.reload(sys.modules["util_nouns"])
        from util_nouns import restore_proper_nouns, singular, plural, restart

if __name__ == "__main__":
    main()
