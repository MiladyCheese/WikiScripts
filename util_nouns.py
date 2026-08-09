import re

# Capitalisation philosophy:
# https://discord.com/channels/1356178382106132570/1356180539522023498/1535338364667043840

# Note when creating a list of articles:
    # Add the following (or create real redirects):
        # Critical Swing
        # Critical Chance
        # Critical Hit
        # Critical
        # Progress
        # Landmarks
        # Body Type
        # Male
        # Female
        # One-Handed
        # Two-Handed
        # Crystal Helix
        # Crystal Helix Remains
        # Ingredients

    # Remove the following for faster speed:
        # All 365 calendar dates ("1 January" etc)

    # Remove the following for fewer false-positives:
        # God
        # Infusion (part of both recipe names and perks)
        # Infusions
        # N/A
        # Kara
        # Swamp
        # Sand
        # Sands
        # Saga
        # Temple
        #   "The..." location words on their own:
        # Bastion
        # Cathedral
        # Courtyard
        # Crypt
        # Demon Gate
        # Garrison
        # Grand Hall
        # Lake
        # Library
        # Menagerie
        # Nexus
        # Pastures

    # Sort by descending line length (so e.g. Willow Tree comes before Tree)

# Always preserve these capitalisations.
# Each item should be either a string "noun" or array of [regex match, "noun"].
PROPER_NOUNS = [
    # Skills
    "Agility",
    "Artisan",
    "Attack",
    "Construction",
    "Cooking",
    "Farming",
    "Fishing",
    "Magic",
    "Mining",
    [r"(?<!de)Ranged", "Ranged"],
    "Runecraft", # "ing" left out for wider match
    "Woodcutting",
    "Cape of Accomplishment",
    "Capes of Accomplishment",

    # Locations from recursive Category:Ashenfall
    "Adventurer's Guild",
    "Ashenfall",
    "Ashien",
    "Ashien's Watch",
    "Bleakfields Valley",
    "Bloodblight Castle",
    "Bloodblight Swamp",
    "Bramblemead Valley",
    "Bramblemead Village",
    "Brynmoor",
    "Chaktan Kara",
    "Coalridge Pass",
    "Colossal Wyrm Camp",
    "Crasorak Kara",
    "Crystalline Mesa",
    "Dowdun Reach",
    "Dragon's Run",
    "Druid's Cave",
    "Emberwood",
    "Fellhollow",
    "Fight Cave",
    "Forgotten Temple",
    "Fractured Plains",
    "Fractured Ruins",
    "Ghornfell",
    "Highlands Castle",
    "Hope's Fall",
    "Imaru's Tower",
    "Kalistrakthen Kara",
    "Keep of Blue Flames",
    "Kletterbuja Kara",
    "Lake of Lost Souls", # Overridden by "Lost Soul" :(
    "Lougrim's Shrine",
    "Nightmare Crucible",
    "Nightmare",
    "Crucible",
    "Outlook Ruins",
    "Purification Pool",
    "Runecrafting Guild",
    "Scorned Wilderness",
    "Silverthorn Keep",
    "Skeklac Kara",
    "Skekven Kara",
    "Stormtouched Highlands",
    "Takla Kara",
    "Temple Woods",
    "Thishepen Kara",
    "Umbral Sands",
    "Vekchenven Kara",
    "Velgar",
    "Velgar's Rise",
    "Vertentis Kara",
    "Whispering Swamp",
    "Witchwillow Range",
    # Plus some shortenings:
    "Bramblemead",
    "Bloodblight",
    "Dowdun",
    "Umbral",
    [r"Sands\b", "Sands"], # Don't match "Sandstone"
    # And agility courses:
    "Chasm Dash",
    "Fractured Ruins",
    "Thunder Assault",
    "Grave Run",
    "Tower Climb",
    "Lava Fields",
    # Sub-regions, many of which aren't listed in the category page:
    "Bleakfields Valley",
    "Coalridge Pass",
    "Dragon's Run",
    "Emberwood",
    "Forgotten Temple",
    "Hope's Fall",
    "Lake of Lost Souls",
    "Silverthorn Keep",
    "Witchwillow Range",
    "The Approach",
    "The Bastion",
    "The Cathedral",
    "The Courtyard",
    "The Crypt",
    "The Demon Gate",
    "The Garrison",
    "The Grand Hall",
    "The Lake",
    "The Library",
    "The Menagerie",
    "The Nexus",
    "The Pastures",
    "Alcarrid Oasis",
    "Dunes of Uzzer",
    "Manafem Plains",
    "The Burning Spire",

    # Other places
    "Gielinor",
    "Blue Flame Keep",
    "Blueflame Keep",
    "Brynmoor Castle",
    "Menaphos",
    "Temple of", # e.g. Saradomin
    "Shrine to", # e.g. Saradomin
    "Uzzer",
    "Antumnos",
    "Magrawn",
    "Brakka's Folly",
    "Grand Hall",
    "Kharid", # ...ian

    # Shops
    "Death's Exchange",
    "Evil Emporium",

    # Quests: https://dragonwilds.runescape.wiki/w/Template:Quests?action=edit
    "First Steps",
    "Getting Started",
    "Ratcatcher",
    "Rune Mysteries",
    "Dragon Slayer",
    "Withering Heights",
    "Black Knight's Fortress",
    "Icthlarin's Little Helper",
    "Growing Pains",
    "Shrimp Catcher",
    "Restless Ghosts",
    "Goblin Diplomacy",
    "Highlighting the Problem",
    "Granite Mauled",
    "Heartstrings",
    "Dog Days",
    "Cook's Assistant",
    "A Room With A Garou",
    "Animal Magnetism",
    "A Melody Remembered",
    "Even More Restless Ghosts",
    "The Wild Hunt",
    "Seeking Salvation",
    "Things That Go Boom In The Night",
    "Doric's Quest",
    "Letters for the Dead",
    "What Remains is Written",
    "Mirror, Mirror",
    "Biohazard",
    "Wanted!",
    "What's Theirs is Mine!",
    "Contact!",
    "Mapping The Sands I",
    "Mapping The Sands II",
    "Brink of Extinction",
    # More:
    "X Marks the Spot",
    "The Great Body Robbery",
    "Warding Off Danger",
    "Rogue Trader",
    "Kuldra's Saga",

    # Dates
    "First Age",
    "Second Age",
    "Third Age",
    "Fourth Age",
    "Fifth Age",
    "Sixth Age",
    "January",
    "February",
    "March",
    "April",
    "May",
    "June",
    "July",
    "August",
    "September",
    "October",
    "November",
    "December",

    # Gods
    "Armadyl",
    "Bandos",
    "Guthix",
    "Saradomin",
    "Zamorak",
    "Icthlarin",
    "Icthlarian",

    # Other names (often first names from below)
    "Elidinis",
    "Fuzan",
    "Noggin",
    "Oculus",
    "Ravanna",
    "Velgar",
    "General Velgar",
    "Victoria",
    "Grim Reaper",
    "Caratacus",
    "Caratacus the Elder",
    "Karibdos",
    [r"\bAva\b", "Ava"], # Careful, it's short
    "Anima Twist",
    "Wild Knight",
    "Fire-Touched",
    "Children of Shadows",
    "Valerius",
    "Delrom",
    "Manktongue",
    "Pulpknuckle",
    "Slopfinger",
    "Xikotal",
    "Postie Pete",
    [r"\bPete\b", "Pete"],
    "Iasadair - The Merchant",
    "Beartach - The Merchant",
    "Iasadair",
    "Muncher",
    "Wise Old Man",
    "Archmage Alric",
    "Alric",
    "Lord Rasmodel",
    "Dreaming Stone",
    "Stone of Jas",
    "Titan", # of Black Knight Titan
    "Garou King",
    "Kalphite Queen",
    "Rat Master Skrexis",
    "Edna",
    "KotHaar-Hok-Zi",
    "Doctor Fenkenstrain",
    "Eleanor Scathe",
    "Blightscale",
    "Ulgo",
    "Reforged Zi",
    [r"\bZi\b", "Zi"],
    "Brassica Prime",
    "Captain Rainer",
    "Commander Zilyana",
    "Zilyana",
    "Avisk Crystal",

    # List of NPCs: https://dragonwilds.runescape.wiki/w/Non-player_character?action=edit
    "Abraxus",
    "Abraxus The Eternal",
    "Avisk",
    "Bilegut",
    "Cathan",
    "Doric",
    "Finn",
    "Houndmaster Rexiton",
    "Imaru",
    [r"\bKay\b", "Kay"], # Careful, it's short
    "Lazina",
    "Putrilius",
    "Sergeant Blister",
    "Spitfoot",
    "Spittletoe",
    "Snotpit",
    "Offalfoot",
    "Summoner Flament",
    "Vannaka",
    "Warren",
    "Wormelbow",
    "Zanik",

    # NPCs that do not appear in-game
    "Aidan",
    "Ansel",
    "Artorius Flamhanger",
    "Ashien",
    "Auburn Ocelot",
    "Avisk",
    "Bilar Amaris",
    "Brakka",
    "Callius Waithe",
    "Claus",
    "Count Valingard",
    "Cynthia Valtis",
    "Dahnu",
    "Derien",
    "Drorkar",
    "Elias Oculus",
    "Eric",
    [r"\bEva\b", "Eva"], # Careful, it's short
    "Falistrius",
    "Finn",
    "Frode",
    "Gahl",
    "Glass Knife",
    "Gothren Actillian",
    "Gregor Volrath",
    "Haager",
    "Henrietta",
    "Hokistix",
    "Holtz",
    "Ignatius Wormwood",
    [r"\bIsla\b", "Isla"], # Careful, it's short
    "Jenniva Milgrim",
    "Jillian Varden",
    "Kessel",
    "Karia",
    "Kethren",
    "King Raluh",
    "King Rolthar",
    "Kuldra",
    "Lacrussa",
    "Lavernius",
    "Leander",
    "Lina Hesperian",
    "Lionel",
    "Lord Gawurin",
    "Lougrim",
    "Malgo",
    "Mallory",
    "Mayev",
    "Mia Larsdottir",
    "Mittens",
    "Moragrin",
    "Mouldfinger",
    "Mrs Hyacinth",
    "Nightingale",
    "Noggin",
    "Olga Skulltaker",
    "Olis",
    "Orik the Bear",
    "Otho",
    "Ramus Lumen",
    "Rasthin",
    "Ravanna",
    "Sadia Vulketra",
    "Shana",
    "Shatterfang",
    "Sir Lear",
    "Sir Percival Lateef",
    "Skrexis",
    "The Cairn",
    [r"\bUlv\b", "Ulv"], # Careful, it's short
    "Vemmeck",
    "Vesk",
    "Victoria Thistlethwaite",
    "Viika",

    # Jagex: https://dragonwilds.runescape.wiki/w/Category:Jagex
    "Ally Banayoti",
    "Community Campfire",
    "Jagex Audio Team",
    "Karlotta Skagfield",
    "Mod Aaart",
    "Mod Arclaw",
    "Mod Ark",
    "Mod Bakes",
    "Mod bitf0x",
    "Mod Blaze",
    "Mod Cerberus",
    "Mod Colibri",
    "Mod Corvin",
    "Mod Cyphus",
    "Mod Debris",
    "Mod Deluxe",
    "Mod Dodds",
    "Mod Dolan",
    "Mod Doom",
    "Mod Dutch",
    "Mod ExOh",
    "Mod Ice Cream",
    "Mod Joker",
    "Mod JT",
    "Mod Kodo",
    "Mod Labbo",
    "Mod Mossdog",
    "Mod Nomad",
    "Mod Nosfer",
    "Mod Oliveira",
    "Mod Orion",
    "Mod Osborne",
    "Mod Pointy",
    "Mod PugZ",
    "Mod Raven",
    "Mod Rook",
    "Mod Sharky",
    "Mod Sylvan",
    "Mod Zephyer",
    "Mod Zombie",
    "Peter Michael Davison",
    # Plus others not in category:
    "Jagex",
    "RuneScape",
    "Dragonwilds",
    "Ashton Mills",
    "Andrew Dodds",
    "RuneFest",
    "Alpha Test",

    # Group/tribe names
    # (not races: dragonkin, garou, goblin, kalphite all lowercase)
    "Amalgamated",
    "Dorgeshuun",
    "Black Knight",
    "White Knight",
    "Lunar Garou",
    "Moon Garou",
    "Elder God",
    "Cabal",
    "Bronze Advisors",
    "Glass Knives",

    # TzHaar creatures, for some reason: https://dragonwilds.runescape.wiki/w/KotHaar
    "TzHaar",
    "KotHaar",
    "KotHaar-Xil",
    "KotHaar-Kal",
    "KotHaar-Ket",
    "KotHaar-Hur",
    "Tok-Xil",

    # Weapon eponyms
    "Swingslash",
    "Skullsplitter",
    "Titan's Wrath",

    # Special attacks: TODO
    "Abyssal Snare",

    # Spells: https://dragonwilds.runescape.wiki/w/Special:Bucket?bucket=infobox_spell&select=*&where=&limit=500&offset=0
    "Windstep",
    "Tempest Shield",
    "Enchant Weapon: Fire",
    "Enchant Weapon: Air",
    "Rocksplosion",
    "Summon Stone Spirits",
    "Axtral Projection",
    "Splinter",
    "Bark To Bones",
    "Superheat",
    "Magical Mending",
    "Eye of Oculus",
    "Summon Shelter",
    "Personal Chest", # Removed unnecessary trailing "(spell)"
    "Internal Alchemy",
    "Bones to Peaches",
    "Fire Spirit",
    "Surge",
    "Confuse",
    "Snare",
    "Spectral Arrows",
    "Venomous Trapper",
    "Humidify",
    "Uproot",
    "Runes to Rune Essence",
    "Summon Elemental Spirits",
    "Fishing Frenzy",
    "Infernal Rod",
    "Fishnado",
    "Divine Rock",
    "Trunk Totem",
    "Recall",
    "Phase Dash",
    "Rapid Growth",
    "Mucksplosion",

    # Perks: https://dragonwilds.runescape.wiki/w/Template:Perks?action=edit
    "Arcane Aligned",
    "Evasion",
    "Ferocious Fighter",
    "Fleet Footed",
    "Quenched",
    "Relentless Ranger",
    "Soul Food",
    "Stalwart Shield",
    "Frosted Flavours",
    "Coagulated",
    "Foreman's Feast",
    "Fungal Fortitude",
    "Grounded",
    "Meaty Meal",
    "Knowledgable Nourishment",
    "Knowledgeable Nourishment", # Wrong but common
    "Steadfast Stomach",
    "Soul Food",
    "Ravenous",
    "Sea Legs",
    "Warding Fish",
    "Sea Life",
    "Sugar Rush",
    "Frosted Flavours",
    # Not "Antipoison" which is more common as an item
    # Not "Antifire" which is more common as an item
    "Focused Strikes",
    "Focused Casting",
    "Focused Artisan",
    "Focused Attack",
    "Focused Construction",
    "Focused Cooking",
    "Focused Mining",
    "Focused Runecrafting",
    "Focused Woodcutting",
    "Focused Farming",
    "Focused Fishing",
    "Focused Agility",
    "Lumberjack",
    "Quarrymaster",
    # Not "Stamina Potion" which is more common as an item
    "Antipoison II",
    "Antifire II",
    "Focused Artisan II",
    "Focused Attack II",
    "Focused Construction II",
    "Focused Cooking II",
    "Focused Mining II",
    "Focused Runecrafting II",
    "Focused Woodcutting II",
    "Focused Farming II",
    "Focused Fishing II",
    "Focused Agility II",
    "Lumberjack II",
    "Quarrymaster II",
    # More uncategorized:
    "Teamonger",
    "Creature Comforts",
    "Adept Culinaromancer",
    "Double Jump",
    "Air Dash",
    # RC passives: https://dragonwilds.runescape.wiki/w/Template:Runecrafting?action=edit
    "Summon Elemental Spirits",
    "Runes to Rune Essence",
    "Fire Spirit",
    "Greater Elemental Spirits",
    "Runes to Rune Essence",
    "Pure Essence",
    "Lesser Anima Siphoning",
    "Essential Strength",
    "Greater Anima Siphoning",
    "Attunement Phase Duration",
    "Lesser Infusion Duration",
    "Better Infusion Duration",
    "Greater Infusion Duration",
    "Air Efficiency",
    "Astral Efficiency",
    "Water Efficiency",
    "Earth Efficiency",
    "Fire Efficiency",
    "Nature Efficiency",
    "Law Efficiency",
    # Magic passives: TODO
    "Arcane Expertise",
    "Afterimage",
    "Greater Confuse",
    # Mining: TODO
    "Ultimate Burst",
    "Ingot Weight Reduction",
    # Fishing: TODO
    "Troubled Waters",
    # Farming: TODO
    "Overgrowth Aura",
    # Artisan: TODO
    "Bark to Bones",
    # Cooking: TODO
    "Amateur Culinaromancer",
    "Culinary Confidence",
    # Construction: TODO
    "Middle Ground",
    "Fine Details",
    "Sacred Geometry",

    # Status effects: https://dragonwilds.runescape.wiki/w/Template:Statuses?action=edit
    "Fresh Start",
    # "Shelter",
    "Cosiness",
    "Bleed",
    "Burning",
    "Encumbered",
    "Fatigue",
    "Poison",
    "Shocked",
    "Soulscourge",
    "Water Wading",
    "Wither",
    "Scorch",
    "Over Eating",

    # Book titles: https://dragonwilds.runescape.wiki/w/Template:Tomes and https://dragonwilds.runescape.wiki/w/Category:Quest_Items
    "The Pride of the Avernic",
    "The Importance of Chaos",
    "Aetheric Fundamentals, a Primordial Primer",
    "The Wrath of Baba Potterington",
    "Leonard the Bound",
    "Eventide - A New Spawn",
    "Coclear Malificarum",
    "The Binding of Ib",
    "Tome of Attack - Vol 1",
    "Tome of Attack - Vol 2",
    "Tome of Construction - Vol 1",
    "Tome of Construction - Vol 2",
    "Tome of Cooking - Vol 1",
    "Tome of Cooking - Vol 2",
    "Tome of Farming - Vol 1",
    "Tome of Farming - Vol 2",
    "Tome of Fishing - Vol 1",
    "Tome of Fishing - Vol 2",
    "Tome of Magic - Vol 1",
    "Tome of Magic - Vol 2",
    "Tome of Mining - Vol 1",
    "Tome of Mining - Vol 2",
    "Tome of Ranged - Vol 1",
    "Tome of Ranged - Vol 2",
    "Tome of Runecrafting - Vol 1",
    "Tome of Runecrafting - Vol 2",
    "Tome of Volcano",
    "Tome of Woodcutting - Vol 1",
    "Tome of Woodcutting - Vol 2",
    "Tome of the Artisan - Vol 1",
    "Tome of the Artisan - Vol 2",
    "Tome of the Dragon Slayer",
    "Tome of the Titan",
    "Tome of the Undying",

    # Music tracks: https://dragonwilds.runescape.wiki/w/Category:Music_tracks
    "A Wild World To Tame",
    "Ashenfall Nocturne 1",
    "Ashenfall Nocturne 2",
    "Beyond Nightfall",
    "Busy Getting To Work",
    "Cairn Toul",
    "Ceridwen",
    # Not "Combat (music)", too generic
    "Death's Domain",
    "Dragon Terror",
    "Dungeon Explore",
    "Echoes on the Wind",
    "Explore Chill",
    "Explore Ghornfell",
    "Explore Highlands",
    "Explore YesterYear",
    "Garou Camp (Combat)",
    "Garou Camp (Explore)",
    "Goblin Camp (Combat)",
    "Goblin Camp (Explore)",
    # Not "Harmony", too generic
    "Heroic Anticipation",
    "Into The Wilds (Main Theme)",
    "Magical Busy",
    # Not "Medieval", too generic
    "Melodi Fresci",
    "Menu Chill",
    "Morytania",
    "Mystery Curiosity",
    "Mystery Magic",
    "Primitive Martial",
    "Primitive Ritual",
    "Restless Ghosts (music track)",
    # Not "Sacred", too generic
    "Sea Shanty ii",
    "Starlit Voyage",
    "Swamp Explore",
    "Tinkering Smithing",
    # Not "Village", too generic
    "Withering Wastes",

    # Achievements: https://dragonwilds.runescape.wiki/w/Steam_Achievements?action=edit
    "Steam achievement",
    "Swift Pick",
    "One Misthalin Star",
    "Chop Chop",
    "Stab, Slash, Crush!",
    "Crafting to Your Own Rune",
    "Sheltered",
    "Not today!",
    "Singed!",
    "Strike True",
    "Fred would be proud",
    "Catch of the Day",
    "Winner Winner Fish Dinner",
    "Medal Winner",
    "Honed Edge",
    "I'll Just Watch",
    "Master Huntsman",
    "It's all Mine!",
    "You Axed for It",
    "Mend it like...",
    "Eye can see my house from here!",
    "Two Misthalin Stars",
    "No Runefunds!",
    "Gotta Patch 'Em All",
    "Frenzied",
    "Medal Collector",
    "Sharp and Shiny",
    "All Buffed Up",
    "Helping around the farm",
    "Bark at the Moon",
    "Dragon Slayer",
    "Don't fear the Reaper",
    "Withering Heights",
    "Mages & Knights & Demons, oh my!",
    "Black Knight's Fortress",
    "Icthlarin's Bigger Helper",
    "Scorching Sands",
    "Melee Master",
    "Dionysius' Disciple",
    "Thrill of the Hunt",
    "Everything is Oresome",
    "Everything is Treemendous",
    "The School of Jewels",
    "Absolute Planker",
    "Three Misthalin Stars",
    "Altar Native",
    "Granny's Favourite Farmer",
    "Maximum Effishiency",
    "Amazingly Acrobatic",

    # Acronyms
    "NPC",
    "PvP",
    [r"\bUI\b", "UI"], # Careful, it's short
    [r"\bXP\b", "XP"], # Careful, it's short

    # Other
    "Dragon Rebellion",
    "God War",
    "Soulscourge",
    "Creative Mode",
    "XBOX",
    "Series X",
    [r"\bX and S\b", "X and S"],
    "PlayStation",
    [r"(\w)/Level up table", "\\1/Level up table"],
    "MOUNT:",
    "PATTERN:",
    "PLAN:",
]

# But then undo these false-positive capitalisations.
# Each item should be either a string "noun" or array of [regex match, "noun"].
IMPROPER_NOUNS = [
    "cooking range",
    [r"cooking pot\b", "cooking pot"], # Not "Cooking potion"
    "farming plot",
    "farming tool",
    "net fishing",
    "rod fishing",
    "magical",
    "Magical Mending",
    "special attack",
    "PvP", # Restore lowercase v and/or last capital P in some cases
]

# Precompile regexes for speed.
PROPER_NOUN_PATTERNS = [
    (
        re.compile(noun[0], re.IGNORECASE),
        noun[1],
    ) if isinstance(noun, list) else (
        re.compile(re.escape(noun), re.IGNORECASE),
        noun,
    )
    for noun in PROPER_NOUNS
]

IMPROPER_NOUN_PATTERNS = [
    (
        re.compile(noun[0], re.IGNORECASE),
        noun[1],
    ) if isinstance(noun, list) else (
        re.compile(re.escape(noun), re.IGNORECASE),
        noun,
    )
    for noun in IMPROPER_NOUNS
]

def restore_proper_nouns(text):
    for pattern, replacement in PROPER_NOUN_PATTERNS:
        text = pattern.sub(replacement, text)
    for pattern, replacement in IMPROPER_NOUN_PATTERNS:
        text = pattern.sub(replacement, text)
    return text
