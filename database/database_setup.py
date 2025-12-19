# db/setup_database.py
# ───────────────────────────────────────────────────────────────────────────
#  AdventureBot  –  schema builder + seed‑loader
# ───────────────────────────────────────────────────────────────────────────

import json
import logging
import os
from typing import List, Tuple

import mysql.connector
from mysql.connector import Error

# ═══════════════════════════════════════════════════════════════════════════
#  LOGGING
# ═══════════════════════════════════════════════════════════════════════════
logging.basicConfig(
    level=logging.DEBUG,
    format="[%(asctime)s] %(message)s",
)
logger = logging.getLogger("DatabaseSetup")

# ═══════════════════════════════════════════════════════════════════════════
#  CONFIG
# ═══════════════════════════════════════════════════════════════════════════
def load_config() -> dict:
    here       = os.path.dirname(os.path.abspath(__file__))
    root       = os.path.dirname(here)
    cfg_path   = os.path.join(root, "config.json")
    if not os.path.exists(cfg_path):
        logger.error("❌ Config file missing at %s", cfg_path)
        raise SystemExit(1)
    with open(cfg_path, "r") as fh:
        cfg = json.load(fh)
    logger.debug("Configuration loaded ✓")
    return cfg

CONFIG    = load_config()
DB_CONFIG = CONFIG["mysql"]

# ═══════════════════════════════════════════════════════════════════════════
#  HELPER – is table empty?
# ═══════════════════════════════════════════════════════════════════════════
def table_is_empty(cur, table_name: str) -> bool:
    cur.execute(f"SELECT COUNT(*) FROM {table_name}")
    return cur.fetchone()[0] == 0

# ═══════════════════════════════════════════════════════════════════════════
#  SEED DATA
# ═══════════════════════════════════════════════════════════════════════════

# --- abilities ----------------------------------------------------------------
MERGED_ABILITIES: List[Tuple] = [
    (1,  'Cure',        'Heals a small amount of HP.',                                      '{"heal": 50}', 0, '❤️',     'self',  None, None, '2025-03-31 02:40:47'),
    (2,  'Fire',        'Deals fire damage to one enemy.',                                  '{"fire_damage": 30}', 0, '🔥',     'enemy', None, 1, '2025-03-31 02:40:47'),
    (3,  'Blizzard',    'Deals ice damage to one enemy.',                                   '{"ice_damage": 30}', 0, '❄️',     'enemy', None, 2, '2025-03-31 02:40:47'),
    (4,  'Holy',        'Deals holy damage to one enemy.',                                  '{"holy_damage": 100}', 1, '✨',     'enemy', None, 3, '2025-03-31 02:40:47'),
    (5,  'Meteor',      'Massive non‑elemental damage to enemies.',                         '{"non_elemental_damage": 120}', 2, '💫', 'enemy', None, 4, '2025-03-31 02:40:47'),
    (6,  'Jump',        'Leap high and strike down a foe.',                                 '{"jump_attack": 1}', 5, '🏃‍♂️',   'enemy', None, None, '2025-03-31 02:40:47'),
    (7,  'Kick',        'Deals physical damage to all enemies.',                            '{"aoe_physical": 15}', 3, '🥾',     'enemy', None, None, '2025-03-31 02:40:47'),
    (8,  'Steal',       'Attempt to steal an item from an enemy.',                          '{"steal_chance": 50}', 0, '🦹',     'enemy', None, None, '2025-03-31 02:40:47'),
    (9,  'Scan',        'Reveal an enemy’s HP and weaknesses.',                             '{"scan": true}', 0, '🔍',       'enemy', None, None, '2025-03-31 02:40:47'),
    (10, 'Berserk',     'Boost attack but reduce defense.',                                 '{"attack_power": 50, "defense_down": 20}', 3, '💪🔼🛡️','self', None, None,'2025-03-31 02:40:47'),
    (11, 'Revive',      'Revives a fainted ally with a surge of healing.',                  '{"heal": 50, "revive": true}', 0, '♻️', 'ally', None, None, '2025-03-31 02:40:47'),
    (12, 'Thunder',     'Deals lightning damage to a single enemy.',                       '{"lightning_damage": 30}', 1, '⚡', 'enemy', None, 5, '2025-03-31 02:40:47'),
    (13, 'Barrier',     'Raises your defense for a short time.',                            '{"defense_up": 30}', 2, '🛡️🔼',  'self', None, None, '2025-03-31 02:40:47'),
    (14, 'Power Break', 'Lower Enemy Attack Power.',                                        '{"attack_power_down": 10}', 0, '💪🔽', 'enemy', None, None,'2025-04-03 07:43:43'),
    (15, 'Armor Break', 'Lower Enemy Defense',                                              '{"defense_down": 30}', 0, '🛡️🔽',  'enemy', None, None,'2025-04-03 07:43:43'),
    (16, 'Mental Break','Lowers Enemy Magic Power and Magic Defense',                       '{"magic_power_down": 30, "magic_defense_down": 30}',0,'🔮🛡️🔽','enemy',None,None,'2025-04-03 07:43:43'),
    (17, 'Fira',        'Deals greater fire damage to one enemy.',                          '{"fire_damage": 50}', 0, '🔥',     'enemy', None, 1, '2025-04-03 07:43:43'),
    (18, 'FIraga',      'Deals devastating fire damage to one enemy.',                      '{"fire_damage": 90}', 1, '🔥',     'enemy', None, 1, '2025-04-03 07:43:43'),
    (19, 'Bizzara',     'Deals greater ice damage to one enemy.',                           '{"ice_damage": 50}', 0, '❄️',     'enemy', None, 2, '2025-04-03 07:43:43'),
    (20, 'Bizzaga',     'Deals devastating ice damage to one enemy.',                       '{"ice_damage": 80}', 1, '❄️',     'enemy', None, 2, '2025-04-03 07:43:43'),
    (21, 'Thundara',    'Deals greater lightning damage to a single enemy.',                '{"lightning_damage": 50}', 0, '⚡', 'enemy', None, 5, '2025-04-03 07:43:43'),
    (22, 'Thundaga',    'Deals devastating lightning damage to a single enemy.',            '{"lightning_damage": 80}', 1, '⚡', 'enemy', None, 5, '2025-04-03 07:43:43'),
    (23, 'Flare',       'A massive non‑elemental magic attack dealing significant damage.', '{"non_elemental_damage": 90}', 2,'💥','enemy',None,4,'2025-04-03 07:43:43'),
    (24, 'Ultima',      'A massive non‑elemental magic attack dealing very high damage.',   '{"non_elemental_damage": 200}',3,'🌀','enemy',None,4,'2025-04-03 07:43:43'),
    (25, 'Comet',       'A massive non‑elemental magic attack dealing very high damage.',   '{"non_elemental_damage": 150}',2,'☄️','enemy',None,4,'2025-04-03 07:43:43'),
    (26, 'Cura',        'Heals a greater amount of HP.',                                    '{"heal": 100}', 0, '❤️',    'self', None, None,'2025-04-03 07:43:43'),
    (27, 'Curaga',      'Heals a high amount of HP.',                                       '{"heal": 200}', 0, '❤️',    'self', None, None,'2025-04-03 07:43:43'),
    (28, 'Regen',       'Heals a small amount of HP over time.',                            None, 0, '❤️🔄',   'self',  None, None,'2025-04-03 07:43:43'),
    (29, 'Shell',       'Raises your magic defense.',                                       '{"magic_defense_up": 30}', 0,'🔮🛡️🔼','self',None,None,'2025-04-03 07:43:43'),
    (30, 'Blink',       'Raises your evasion.',                                             '{"evasion_up": 30}', 2, '🎯🔼','self', None, None,'2025-04-03 07:43:43'),
    (31, 'Demi',        'Deals damaged based on enemy health.',                             None, 0, '🌀',      'enemy', None, None,'2025-04-03 07:43:43'),
    (32, 'Gravity',     'Deals Air based damage while grounding flying enemies.',           '{"non_elemental_damage": 80}', 0,'🪐','enemy',None,None,'2025-04-03 07:43:43'),
    (33, 'Haste',       'Grants higher speed with chance of increasing turns.',             None, 3, '⏱️🔼',   'self',  None, None,'2025-04-03 07:43:43'),
    (34, 'Slow',        'Lowers enemy speed with chance of reducing turns.',                None, 2, '⏳🔽',   'enemy', None, None,'2025-04-03 07:43:43'),
    (35, 'Poison',      'Deals a small amount of damage over time.',                        None, 0, '☠️',     'enemy', None, None,'2025-04-03 07:43:43'),
    (36, 'Bio',         'Deals a greater amount of damage over time.',                      None, 1, '☣️',     'enemy', None, None,'2025-04-03 07:43:43'),
    (37, 'Focus',       'Raises your magic power.',                                         '{"magic_power_up": 30}', 0,'🔮🔼','self',None,None,'2025-04-03 07:43:43'),
    (38, 'Fireblade',   'A Spellblade ability that fuses fire to your attacks.',            '{"fire_damage": 30}', 0,'🔥⚔️','enemy',None,1,'2025-04-03 07:51:14'),
    (39, 'Iceblade',    'A Spellblade ability that fuses ice to your attacks.',             '{"ice_damage": 30}', 0,'❄️⚔️','enemy',None,2,'2025-04-03 07:51:14'),
    (40, 'Thunderblade','A Spellblade ability that fuses thunder to your attacks.',         '{"lightning_damage": 30}', 0,'⚡⚔️','enemy',None,5,'2025-04-03 07:51:14')
]

# --- ability ↔ status‑effects -------------------------------------------------
MERGED_ABILITY_STATUS_EFFECTS: List[Tuple[int, int]] = [
    (10, 1),
    (10, 2)
]

# --- class ↔ ability links ----------------------------------------------------
MERGED_CLASS_ABILITIES: List[Tuple[int, int]] = [
    (8,  1),  (9,  2), (9,  3), (8,  4), (9,  5), (6,  6),
    (1,  7),  (2,  7), (6,  7), (4,  9), (6,  9), (7,  9),
    (2, 10),  (8, 11), (9, 12), (10,13), (1, 14), (1, 15),
    (1, 16),  (5, 17), (9, 17), (9, 18), (9, 19), (9, 20),
    (9, 21),  (9, 22), (9, 23), (10,23), (9, 24), (5, 25),
    (8, 26),  (8, 27), (8, 28), (10,31), (5, 32), (5, 33),
    (7, 33),  (5, 34), (5, 35), (9, 36), (9, 37), (10,37),
    (3, 38),  (3, 39), (3, 40)
]

# --- classes ------------------------------------------------------------------
MERGED_CLASSES: List[Tuple] = [
    (1, 'Warrior',       'A sturdy fighter with strong physical attacks.',                       300, 15,  5, 10,  5, 95,  5, 10, '', None,'2025-03-30 21:40:47'),
    (2, 'Berserker',     'A savage fighter who channels uncontrollable fury.',                   250, 25,  0,  8,  5, 90,  5, 10, '', None,'2025-04-03 02:05:45'),
    (3, 'Mystic Knight', 'A hybrid fighter that fuses magic to their blade.',                    250, 25, 10,  8,  5, 95,  5, 10, '', None,'2025-04-03 02:05:45'),
    (4, 'Thief',         'A quick fighter who excels at stealing items.',                       200, 20,  5,  8,  5, 95, 10, 10, '', None,'2025-03-30 21:40:47'),
    (5, 'Green Mage',    'A powerful mage that manipulates time and space magics.',             200,  5, 20,  8, 10, 90,  8, 10, '', None,'2025-03-30 21:40:47'),
    (6, 'Dragoon',       'A lancer who can jump high and strike down foes.',                    200, 20,  8, 10,  8, 95,  5, 10, '', None,'2025-03-30 21:40:47'),
    (7, 'Bard',          'A ranged attacker wielding a bow and musical influence.',             200, 20, 10,  5,  5, 95,  5, 10, '', None,'2025-04-03 02:05:45'),
    (8, 'White Mage',    'A healer who uses holy magic to restore and protect.',                100,  5, 15,  7, 10, 95,  5, 10, '', None,'2025-04-03 02:05:45'),
    (9, 'Black Mage',    'A mage who uses destructive elemental spells.',                       200,  5, 20,  5,  5, 95,  5, 10, '', None,'2025-04-03 02:05:45'),
    (10,'Geomancer',     'A sorcerer using environmental/elemental attacks.',                   200, 10, 15,  5, 10, 95,  6, 10, '', None,'2025-04-03 02:05:45')
]

# --- elements -----------------------------------------------------------------
MERGED_ELEMENTS: List[Tuple] = [
    (1, 'Fire',           '2025-03-30 21:40:47'),
    (2, 'Ice',            '2025-03-30 21:40:47'),
    (3, 'Holy',           '2025-03-30 21:40:47'),
    (4, 'Non-Elemental',  '2025-03-30 21:40:47'),
    (5, 'Air',            '2025-03-30 21:40:47')
]

# --- difficulties -------------------------------------------------------------
MERGED_DIFFICULTIES: List[Tuple] = [
    (1, 'Easy',        10, 10, 1, 1, 50, 0.20, 2, 0.10, 3,  5,'2025-03-30 21:40:47'),
    (2, 'Medium',      10, 10, 1, 2, 75, 0.25, 3, 0.15, 4,  6,'2025-03-30 21:40:47'),
    (3, 'Hard',        12, 12, 2, 3,100, 0.30, 3, 0.20, 5,  8,'2025-03-30 21:40:47'),
    (4, 'Crazy Catto', 12, 12, 3, 4,125, 0.40, 3, 0.25, 6, 10,'2025-03-30 21:40:47'),
]

# --- intro steps --------------------------------------------------------------
MERGED_INTRO_STEPS: List[Tuple] = [
    (
        1,
        1,
        "An Unexpected Discovery",
        "During what began as an ordinary raid, Sophia paused. The usual golden glow marking "
        "the entrance to familiar realms was absent, replaced instead by a strange portal shimmering "
        "with dark, translucent crystals. Curious murmurs rippled through the raid group…\n\n"
        "Sophia:\u2028\"This... isn't the gate we're used to. Has anyone seen anything like this before?\"",
        "https://cdn.discordapp.com/attachments/1362832151485354065/1364793339538440232/step1.png?"
        "ex=680f9398&is=680e4218&hm=7832e0e8397c563e8c86ab6846989f63af51cd786cf8c2c8427d3c5d5f8b3466&",
        "2025-03-31 07:40:47",
    ),
    (
        2,
        2,
        "Mog's Bold Venture",
        "As the group hesitated, Mog, the courageous Moogle companion, hovered near the mysterious "
        "entrance, eyes wide with intrigue.\n\nMog:\u2028\"Let me scout it out, Kupo! Moogles portal hop "
        "all the time! If there's trouble, I'll zip right back!\"\n\nWithout another word, Mog vanished "
        "through the darkened portal.",
        "https://cdn.discordapp.com/attachments/1362832151485354065/1364793340331298897/step2.png?"
        "ex=680f9398&is=680e4218&hm=50cb0c034376bb47248d7e4c495cd482280dae41d394938288aa6ad1774b6c3f&",
        "2025-03-31 07:40:47",
    ),
    (
        3,
        3,
        "The Moogle Returns",
        "Moments felt like hours as the group waited anxiously. With a burst of light, Mog reappeared, "
        "fur ruffled and eyes gleaming.\n\nMog:\u2028\"Kupo! That portal leads somewhere strange..."
        "somewhere new! I didn't see anyone, but I heard whispers and saw shadows.\"\n\nHe looked both "
        "nervous and excited.",
        "https://cdn.discordapp.com/attachments/1362832151485354065/1364793340956444712/step3.png?"
        "ex=680f9398&is=680e4218&hm=8840246c658b6c4635befbaf6ce72ea4583d75b1f778068d57c0f090f83259d9&",
        "2025-03-31 07:40:47",
    ),
    (
        4,
        4,
        "Sophia's Decision",
        "Sophia nodded solemnly, weighing the risk and opportunity. The team exchanged glances, "
        "some anxious, others eager.\n\nSophia:\u2028\"Alright, team. This is uncharted territory, but "
        "it might be exactly the challenge we've been waiting for. Gear up. We're going in.\"",
        "https://cdn.discordapp.com/attachments/1362832151485354065/1364793340792877003/step4.png?"
        "ex=680f9398&is=680e4218&hm=46792e348b39a7064b44c54c9ee118d71f212711fe6cb3c2e4c873e3adfc3d5d&",
        "2025-04-09 16:37:27",
    ),
    (
        5,
        5,
        "The Call to Adventure",
        "Returning to their Free Company house, Sophia gathered everyone to plan the expedition. "
        "Maps were spread out; gear was prepared. Excitement buzzed through the air as word spread "
        "of the unknown portal.\n\nSophia:\u2028\"This isn't just another raid. It's a chance to "
        "discover something new, maybe even change everything we know. Let's make history, everyone.\"",
        "https://cdn.discordapp.com/attachments/1362832151485354065/1364793342256752711/step5.png?"
        "ex=680f9398&is=680e4218&hm=2c8bba266e80e4b78598307b1e9e890030c078df6e03c09486de1d6306c3ada7&",
        "2025-04-09 16:37:27",
    ),
]

# --- room templates -----------------------------------------------------------
MERGED_ROOM_TEMPLATES: List[Tuple] = [
    (
        1,
        "safe",
        "Moss Room",
        "You do not notice anything of importance, the area appears to be safe.",
        "https://cdn.discordapp.com/attachments/1362832151485354065/1362833775637303336/roomtypemoss.png?"
        "ex=680c671c&is=680b159c&hm=3dc79f7a87ce268e9d54deae12bee18fa98b37a69caa1644257023135acfee8e&",
        None,
        "2025-03-31 07:40:47",
        None,
        None,
    ),
    (
        2,
        "safe",
        "Mystic Room",
        "You do not notice anything of importance, the area appears to be safe.",
        "https://cdn.discordapp.com/attachments/1362832151485354065/1362833776446673227/roomtypemystic.png?"
        "ex=680c671c&is=680b159c&hm=bc397f1f43a2317102e1f4216333b331c31dcbac9ffd8078f61c0c43171841a1&",
        None,
        "2025-03-31 07:40:47",
        None,
        None,
    ),
    (
        3,
        "safe",
        "Crystal Tunnel",
        "You do not notice anything of importance, the area appears to be safe.",
        "https://cdn.discordapp.com/attachments/1362832151485354065/1362833695169576981/crystals.png?"
        "ex=680c6709&is=680b1589&hm=2c0977deb61f6e286646aeddab3a54cf048c6043dbd398c15f5ebbe7a1d5e8f6&",
        None,
        "2025-03-31 07:40:47",
        None,
        None,
    ),
    (
        4,
        "safe",
        "Bridge",
        "You do not notice anything of importance, the area appears to be safe.",
        "https://cdn.discordapp.com/attachments/1362832151485354065/1362833699648966726/roomtypebridge.png?"
        "ex=680c670a&is=680b158a&hm=88011ac41a9c277ce6ecc855a7cb3099d9c35a0d648caa944397718741c2d5c0&",
        None,
        "2025-04-10 01:22:14",
        None,
        None,
    ),
    (
        5,
        "safe",
        "Magicite",
        "You do not notice anything of importance, the area appears to be safe.",
        "https://cdn.discordapp.com/attachments/1362832151485354065/1362833774844313750/roomtypemagicite.png?"
        "ex=680c671c&is=680b159c&hm=07b6f7a5c5f95e556e7adb11a013cb9d546489d7a64954d15f5c99d11acf9847&",
        None,
        "2025-04-10 01:22:19",
        None,
        None,
    ),
    (
        6,
        "safe",
        "Rainbow Crystal",
        "You do not notice anything of importance, the area appears to be safe.",
        "https://cdn.discordapp.com/attachments/1362832151485354065/1362833696519885081/rainbowcrystal.png?"
        "ex=680c6709&is=680b1589&hm=efecc1cf0d3a6e9f30364b1e4731697a65ab5745807ba1cb30574569cf10be16&",
        None,
        "2025-04-10 01:22:27",
        None,
        None,
    ),
    (
        7,
        "safe",
        "Aetheryte",
        "You do not notice any hostile presence; instead you see a naturally growing Aetheryte cluster.",
        "Perhaps this will be useful in the future...",
        "https://cdn.discordapp.com/attachments/1362832151485354065/1362833698168508496/roomtypeaetheryte.png?"
        "ex=680c6709&is=680b1589&hm=29873e0d2dea2ecbd63a66c0d18825c5954f80965e19309827e18a8f77459052&",
        None,
        "2025-04-10 01:22:27",
        None,
        None,
    ),
    (
        8,
        "monster",
        "You Sense A Hostile Presence...",
        "An enemy appears upon entering the area...",
        "",
        None,
        "2025-03-31 07:40:47",
        None,
        None,
    ),
    (
        9,
        "staircase_up",
        "Staircase Up",
        "You notice a staircase leading up to the next level.",
        "https://cdn.discordapp.com/attachments/1362832151485354065/1362832388677308516/stairs.png?"
        "ex=680c65d1&is=680b1451&hm=8b5d73c9b00898e7913c5d661d2f107731817084c19a8f938f7ce9ec3637340d&",
        None,
        "2025-04-19 18:55:00",
        None,
        None,
    ),
    (
        10,
        "staircase_down",
        "Staircase Down",
        "You notice a staircase leading down to the next level.",
        "https://cdn.discordapp.com/attachments/1362832151485354065/1365404303161950388/stairs_down_2.png?"
        "ex=680d2f59&is=680bddd9&hm=94fbe622374098bfcb2d17b5c79a63542853d7ee574c5c93ef98dfea92e6780b&",
        None,
        "2025-04-19 18:55:00",
        None,
        None,
    ),
    (
        11,
        "exit",
        "Dungeon Exit",
        "(Implemented in next patch)",
        "https://the-demiurge.com/DemiDevUnit/images/backintro.png",
        None,
        "2025-03-31 02:40:47",
        None,
        None,
    ),
    (
        12,
        "item",
        "Treasure Room",
        "You do not notice any hostile presence, instead you see a treasure chest waiting to be unlocked.",
        "https://cdn.discordapp.com/attachments/1362832151485354065/1362832389629284544/treasurechest.png?"
        "ex=680c65d1&is=680b1451&hm=e1971818f32f4e0b0f43cfcbf5283fc1c3f36f80b1af2bcfacbfd7ba8ecf3ace&",
        None,
        "2025-03-31 02:40:47",
        None,
        None,
    ),
    (
        13,
        "boss",
        "Boss Lair",
        "A grand chamber with ominous decorations.",
        None,
        None,
        "2025-03-31 02:40:47",
        None,
        None,
    ),
    (
        15,
        "shop",
        "Shop Room",
        "You do not notice any hostile presence. Instead you find a Moogle hiding in the corner...",
        "https://cdn.discordapp.com/attachments/1362832151485354065/1376308720144748554/Shop_Entrance.gif?"
        "ex=6834dae1&is=68338961&hm=5370f37045df11803229a217bc984ce52b910b64c59a6ede123468567b6d1991&",
        None,
        "2025-03-31 02:40:47",
        None,
        None,
    ),
    (
        16,
        "illusion",
        "Illusion Chamber",
        "The room shimmers mysteriously...",
        "https://cdn.discordapp.com/attachments/1362832151485354065/1362832385040711930/Illusion.png?"
        "ex=680c65d0&is=680b1450&hm=17f9b558f22f2738b576bb373eec18b161c8df67c8f2bcfff86a1ddc6d604eed&",
        None,
        "2025-03-31 02:40:47",
        None,
        None,
    ),
    (
        17,
        "locked",
        "Locked Door",
        "A heavy door with a glowing symbol and what appears to be a lock. It seems you need a key.",
        "https://cdn.discordapp.com/attachments/1362832151485354065/1362832387742109886/lockedroom.png?"
        "ex=680d0e91&is=680bbd11&hm=d3b19049954366cd7d625e5592a6cffbf7242aa3462ea107525c4919c371bee3&",
        None,
        "2025-04-19 18:55:00",
        None,
        None,
    ),
    (
        18,
        "chest_unlocked",
        "Unlocked Chest",
        "You notice an empty chest and nothing else of importance.",
        "https://cdn.discordapp.com/attachments/1362832151485354065/1365404301488291880/chestopen.png?"
        "ex=680d2f59&is=680bddd9&hm=df9e2742340f802058c078a816d17d0ffaaadeca5cfafa526db4273c28c02faf&",
        None,
        "2025-04-23 23:00:00",
        None,
        None,
    ),
    (
        19,
        "safe",
        "Lake Room",
        "You do not notice anything of importance, the area appears to be safe.",
        "https://cdn.discordapp.com/attachments/1362832151485354065/1362832385829244948/Lake2.png?"
        "ex=680c65d0&is=680b1450&hm=bbf00040b5390f13ae4c8eedd2ea32dc08a0510e150879ae30cfc4b6e0a13ff0&",
        None,
        "2025-04-25 12:29:10",
        None,
        None,
    ),
    (
        20,
        "safe",
        "Lake Room 2",
        "You do not notice anything of importance, the area appears to be safe.",
        "https://cdn.discordapp.com/attachments/1362832151485354065/1362832386416443683/Lake3.png?"
        "ex=680c65d1&is=680b1451&hm=1dc65d458458bb0e73e417850bc66973c79921757193b7d85d5849923cb3624a&",
        None,
        "2025-04-25 12:29:10",
        None,
        None,
    ),
    (
        21,
        "miniboss",
        "Mimic",
        "As you approach the locked chest it springs to life and bares it's fangs!",
        "https://cdn.discordapp.com/attachments/1362832151485354065/1365786181417177148/2.png?"
        "ex=68113600&is=680fe480&hm=a35ce81d097c19b34c06338bb678627ec9b16061ba867cb0d72be0d84075a927&",
        None,
        "2025-04-29 00:24:47",
        None,
        None,
    ),
    (
        22,
        "death",
        "Death",
        "Your health as fallen to 0 and have fainted.",
        "https://cdn.discordapp.com/attachments/1362832151485354065/1370837025665712178/output.gif?"
        "ex=6820f2f7&is=681fa177&hm=5c0ff142cc94ff7dd4050fb0be0cb1821580e251f6c5e8cb2f31384170afbd52&",
        None,
        "2025-05-09 16:59:31",
        None,
        None,
    ),
]
# --- items --------------------------------------------------------------------
MERGED_ITEMS: List[Tuple] = [
    (1, 'Potion',       'Heals 50 HP.',                                                 '{"heal": 50}',                 'consumable', 1, 100, 10, 'self', 'https://example.com/icons/potion.png',        None,'2025-03-30 21:40:47'),
    (2, 'Ether',        'Restores 30 MP.',                                              '{"restore_mp": 30}',           'consumable', 1, 150,  5, 'self', 'https://example.com/icons/ether.png',         None,'2025-03-30 21:40:47'),
    (3, 'Phoenix Down', 'Revives a fainted ally with 100 HP.',                          '{"heal": 100, "revive": true}', 'consumable', 1, 500,  2, 'ally','https://example.com/icons/phoenix_down.png',  None,'2025-03-30 21:40:47')
]

# --- enemies ------------------------------------------------------------------
MERGED_ENEMIES: List[Tuple] = [
    (1, 'Behemoth',            'large, purple, canine-esque creature...', 100, 100, 15,  5,  5,  5,  90, 5, 'Easy',   None,'http://the-demiurge.com/DemiDevUnit/images/monsters/behemoth.png',             0.3, 100,  75, None, 1, None,'2025-03-31 02:40:47'),
    (2, 'Ghost',               'pale, translucent, or wispy being...',    50,  50, 10,  5,  5,  3,  85, 5, 'Easy',   None,'http://the-demiurge.com/DemiDevUnit/images/monsters/ghost.png',                0.3,  50,  50, None, 2, None,'2025-03-31 02:40:47'),
    (3, 'Dragon Whelp',        'A young dragon spitting small flames.',   100, 100, 15,  8, 10,  5,  80,10, 'Hard',   None,'https://example.com/images/dragon_whelp.png',                                  0.1, 150, 150, None, 1, None,'2025-03-31 02:40:47'),
    (4, 'Lich',                'An undead sorcerer with devastating magic.',80, 80, 12,  4, 20, 10,  90, 5, 'Hard',   None,'https://example.com/images/lich.png',                                          0.2, 200, 200, None, 1, None,'2025-03-31 02:40:47'),
    (5, 'Dark Knight',         'A mysterious warrior clad in obsidian armor.',120,120,20,10,  5,  8,  85, 5, 'Medium', None,'https://example.com/images/dark_knight.png',                                   0.4, 150, 250, None, 1, None,'2025-03-31 02:40:47'),
    (6, 'Nightmare',           'You feel a sudden wave of fear as the dark shrouded creature approaches...',125,125,20,6,6,6,90,5,'Easy',None,'http://the-demiurge.com/DemiDevUnit/images/monsters/elementals/nightmare_elemental.png',0.1,125,150,None,1,None,'2025-04-09 20:20:32'),
    (7, 'Tonberry Chef',       'A creature said to be only in legend. It seems to like cooking, but where did it get that knife and chef\'s hat? Also VERY big.',250,250,20,6,10,6,90,5,'Easy',None,'http://the-demiurge.com/DemiDevUnit/images/monsters/tonberry/tonberry_chef.png',0.1,150,110,None,1,None,'2025-04-09 20:20:32'),
    (8, 'Overgrown Tonberry',  'A creature said to be only in legend. Also VERY big.',200,200,10,5,2,3,85,5,'Easy',None,'http://the-demiurge.com/DemiDevUnit/images/monsters/tonberry/overgrown_tonberry.png', 0.3, 75,  90, None, 1, None,'2025-03-31 02:40:47')
]

# --- enemy ↔ ability links ----------------------------------------------------
MERGED_ENEMY_ABILITIES: List[Tuple[int, int]] = [
    (1, 2), (2, 2), (3, 2), (4, 2), (4, 3),
    (1, 7), (2, 7), (3, 7), (6, 7),
    (2, 9), (4, 9),
    (5, 10), (6, 10),
    (5, 12)
]

# --- enemy drops --------------------------------------------------------------
MERGED_ENEMY_DROPS: List[Tuple] = [
    (1, 1, 0.5, 1, 1),
    (2, 3, 0.25, 1, 1),
    (4, 1, 0.25, 1, 1)
]

# --- enemy resistances --------------------------------------------------------
MERGED_ENEMY_RESISTANCES: List[Tuple] = [
    (1, 1, 0)
]

# --- levels -------------------------------------------------------------------
MERGED_LEVELS: List[Tuple] = [
    (1,  0,    0,   0,   0,   0,   0,   0,   0,   0,   None,'2025-04-08 10:00:00'),
    (2,  500,  0.1, 0.1, 0.05,0.05,0.05, 0,   0,   0.01,None,'2025-04-08 10:00:00'),
    (3,  1000, 0.2, 0.15,0.1, 0.05,0.07, 0,   0,   0.01,None,'2025-04-08 10:00:00'),
    (4,  2000, 0.2, 0.1, 0.1, 0.01,0.02, 0,   0,   0.01,None,'2025-04-09 10:15:49'),
    (5,  3000, 0.2, 0.1, 0.1, 0.01,0.02, 0,   0,   0.01,None,'2025-04-09 10:15:49'),
    (6,  4500, 0.2, 0.1, 0.1, 0.01,0.02, 0, 0.01, 0.01,None,'2025-04-09 10:15:49')
]

# --- vendors + items ----------------------------------------------------------
MERGED_NPC_VENDORS: List[Tuple] = [
    (1, 'Stiltzkin',
     'Stiltzkin: "Oh hello, I’m glad to see you are not a monster, kupo! '
     'I seem to have fallen asleep after getting lost for quite some time, kupo. '
     'I’m a traveling merchant, see.. I was portal hopping and suddenly came across '
     'a black portal I’d never seen before..."\n'
     'Stiltzkin looks at you as if he’s trying to recall something. '
     '"Have we met before, kupo? You seem familiar."\n'
     '"At any rate, if you’d like to buy or sell something the shop is still open."',
     None,
     'https://the-demiurge.com/DemiDevUnit/images/shop/stiltzkin.gif',
     '2025-03-24 12:37:28')
]

MERGED_NPC_VENDOR_ITEMS: List[Tuple] = [
    (1, 1,  50, 1, 2),
    (1, 3, 100, 1, 1)
]

# --- hub embeds/buttons -------------------------------------------------------


MERGED_HUB_EMBEDS: List[Tuple] = [
    (
        1,
        "main",
        "",
        (
            "***Step into an unexplored reality and find meaning and hidden truth behind its existence. "
            "Assemble your party and compete with other players, or enter alone. "
            "Choose your class + difficulty level, and experience turn-based combat that challenges your strategy at every turn.***"
        ),
        "https://cdn.discordapp.com/attachments/1362832151485354065/1367115629408292974/12346.png?"
        "ex=68136925&is=681217a5&hm=dd0bfd5013c7add42b3a4033f1bad6367b99b54ecb70b43a0e1d0071678091a0&",
        (
            "**AdventureBot v3.0.9 is now Live!**\n\n"
            "You can see the current https://discord.com/channels/1337786582996095036/1376040430445133895 here.\n\n"
            "__——————————————————__\n"
            "**Beta Testers:**\n\n"
            "Patch 3.1 features have been partially implemented for testing.\n\n"
            "Please see the https://discord.com/channels/1337786582996095036/1360683660365529300 channel if you come across any issues."
        ),
        None,
        "2025-03-31 08:43:19",
    ),
    (
        2,
        "tutorial",
        "Starting A Game",
        (
            "Simply click the **New Game** button to create a new game thread.\n\n"
            "This will add you to the **Queue** system inside the thread, along with anyone else who wants to join.\n\n"
            "- Only the players who join the game session will see the private thread and be added to it automatically.\n\n"
            "- Up to 6 players can join via the LFG post in the Game Channel by clicking the Join button.\n\n"
            "- Additional players will be shown in the **Queue List** in the thread.\n\n"
            "When the creator is ready they may click **Start Game** to lock in the amount of players playing."
        ),
        "https://cdn.discordapp.com/attachments/1362832151485354065/1373622234865733652/Screenshot_2025-05-18_at_6.14.47_AM.png?"
        "ex=682b14e5&is=6829c365&hm=b91a3c24ed88f1f493db9a8f61473923e316e284782ab15bd565f6a82ac25966&",
        "Coming Soon...",
        1,
        "2025-04-15 02:50:10",
    ),
    (
        3,
        "tutorial",
        "Choose Class and Difficulty",
        (
            "Once the Session Creator clicks the Start Game button they can choose their class and difficulty level.\n\n"
            "- Selecting **Easy** will generate up to 2 floors with a rare chance to spawn a basement floor. In this mode most harder enemies are removed from generation.\n\n"
            "- Choosing **Medium** difficulty will generate up to 4 floors with at least 2 and a rare chance to spawn a basement. In this mode harder enemies spawn alongside easy ones during generation.\n\n"
            "- Selecting **Hard** is exactly what you think it is. With up to 4 floors and higher spawn chances on more difficult enemies and fewer vendor shops and item drops.\n\n"
            "- **Crazy Catto** is the most difficult of challenges and well... you'd be a crazy catto to try it."
        ),
        "https://cdn.discordapp.com/attachments/1362832151485354065/1373622403455778848/Screenshot_2025-05-18_at_6.19.11_AM.png?"
        "ex=682b150d&is=6829c38d&hm=045419693ca1ecd758f7ecf5c7208ca4da321622636b908da9e15c99f97dde61&",
        "Coming Soon...",
        2,
        "2025-04-17 03:45:05",
    ),
]
MERGED_HUB_BUTTONS: List[Tuple] = []

# --- status effects -----------------------------------------------------------
MERGED_STATUS_EFFECTS: List[Tuple] = [
    (1, 'Attack Boost', 'buff',    50, 3, 'https://example.com/icons/attack_boost.png','2025-03-30 21:40:47'),
    (2, 'Defense Down', 'debuff',  20, 3, 'https://example.com/icons/defense_down.png','2025-03-30 21:40:47'),
    (3, 'Poison',       'debuff',  10, 5, 'https://example.com/icons/poison.png',      '2025-03-30 21:40:47'),
    (4, 'Heal Over Time','buff',   15, 4, 'https://example.com/icons/heal_over_time.png','2025-03-30 21:40:47'),
    (5, 'Stun',         'debuff',   0, 1, 'https://example.com/icons/stun.png',        '2025-03-30 21:40:47'),
    (6, 'Burn',         'debuff',  10, 3, 'https://example.com/icons/burn.png',        '2025-03-30 21:40:47'),
    (7, 'Freeze',       'debuff',   0, 2, 'https://example.com/icons/freeze.png',      '2025-03-30 21:40:47'),
]


# --- floor → room placement rules seed data -------------------------------------------------
# (difficulty_name, floor_number, room_type, chance, max_per_floor)
MERGED_FLOOR_ROOM_RULES: List[Tuple[str, int, str, float, int]] = [
    # Example entries; replace these with your real tuning values:
    ("Easy",  1, "entrance",       1.00, 1),
    ("Easy",  1, "safe",           0.50, 20),
    ("Easy",  1, "monster",        0.30, 10),
    ("Easy",  1, "item",           0.10,  5),
    ("Easy",  1, "locked",         0.05,  2),
    ("Easy",  1, "staircase_up",   0.05,  1),
    # …etc for each floor / difficulty…
]

# --- item_effects -------------------------------------------------------------
MERGED_ITEM_EFFECTS: List[Tuple] = []

# ═══════════════════════════════════════════════════════════════════════════
#  TABLE DEFINITIONS (players added + new floor_room_rules)
# ═══════════════════════════════════════════════════════════════════════════
TABLES = {
    'difficulties': '''
        CREATE TABLE IF NOT EXISTS difficulties (
            difficulty_id       INT AUTO_INCREMENT PRIMARY KEY,
            name                VARCHAR(50) NOT NULL UNIQUE,
            width               INT NOT NULL,
            height              INT NOT NULL,
            min_floors          INT NOT NULL,
            max_floors          INT NOT NULL,
            min_rooms           INT NOT NULL,
            enemy_chance        FLOAT NOT NULL,
            npc_count           INT NOT NULL,
            basement_chance     FLOAT NOT NULL DEFAULT 0.0,
            basement_min_rooms  INT NOT NULL DEFAULT 0,
            basement_max_rooms  INT NOT NULL DEFAULT 0,
            created_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''',

    # ---------- floor_room_rules ----------
    'floor_room_rules': '''
        CREATE TABLE IF NOT EXISTS floor_room_rules (
            rule_id           INT AUTO_INCREMENT PRIMARY KEY,
            difficulty_name   VARCHAR(50) NOT NULL,
            floor_number      INT,
            room_type ENUM(
                'safe','monster','item','shop','boss','trap','illusion',
                'staircase_up','staircase_down','exit','locked','entrance',
                'chest_unlocked','miniboss','death'
            ) NOT NULL,
            chance            FLOAT   NOT NULL,
            max_per_floor     INT     NOT NULL,
            created_at        TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (difficulty_name)
              REFERENCES difficulties(name) ON DELETE CASCADE
        )
    ''',

    # ---------- elements ----------
    'elements': '''
        CREATE TABLE IF NOT EXISTS elements (
            element_id   INT AUTO_INCREMENT PRIMARY KEY,
            element_name VARCHAR(50) NOT NULL UNIQUE,
            created_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''',
    # ---------- element_relationships ----------
    'element_relationships': '''
        CREATE TABLE IF NOT EXISTS element_relationships (
            element_id          INT NOT NULL,
            counter_element_id  INT NOT NULL,
            relation_type ENUM('opposes','weakens','empowers') DEFAULT 'opposes',
            created_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (element_id, counter_element_id, relation_type),
            FOREIGN KEY (element_id)         REFERENCES elements(element_id) ON DELETE CASCADE,
            FOREIGN KEY (counter_element_id) REFERENCES elements(element_id) ON DELETE CASCADE
        )
    ''',
    # ---------- abilities ----------
    'abilities': '''
        CREATE TABLE IF NOT EXISTS abilities (
            ability_id     INT AUTO_INCREMENT PRIMARY KEY,
            ability_name   VARCHAR(100) NOT NULL,
            description    TEXT,
            effect         JSON,
            cooldown       INT DEFAULT 0,
            icon_url       VARCHAR(255),
            target_type    ENUM('self','enemy','ally','any') DEFAULT 'any',
            special_effect VARCHAR(50),
            element_id     INT,
            created_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (element_id) REFERENCES elements(element_id) ON DELETE SET NULL
        )
    ''',
    # ---------- classes ----------
    'classes': '''
        CREATE TABLE IF NOT EXISTS classes (
            class_id            INT AUTO_INCREMENT PRIMARY KEY,
            class_name          VARCHAR(50) NOT NULL,
            description         TEXT,
            base_hp             INT DEFAULT 100,
            base_attack         INT DEFAULT 10,
            base_magic          INT DEFAULT 10,
            base_defense        INT DEFAULT 5,
            base_magic_defense  INT DEFAULT 5,
            base_accuracy       INT DEFAULT 95,
            base_evasion        INT DEFAULT 5,
            base_speed          INT DEFAULT 10,
            image_url           VARCHAR(255),
            creator_id          BIGINT,
            created_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''',
    # ---------- temp_abilities ----------
    'temp_abilities': '''
        CREATE TABLE IF NOT EXISTS temp_abilities (
            temp_ability_id  INT AUTO_INCREMENT PRIMARY KEY,
            ability_id       INT NOT NULL,
            allowed_class_id INT NOT NULL,
            duration_turns   INT DEFAULT 1,
            reward_image_url VARCHAR(255),
            created_at       TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (ability_id) REFERENCES abilities(ability_id) ON DELETE CASCADE,
            FOREIGN KEY (allowed_class_id) REFERENCES classes(class_id) ON DELETE CASCADE
        )
    ''',
    # ---------- illusion_reward_options ----------
    'illusion_reward_options': '''
        CREATE TABLE IF NOT EXISTS illusion_reward_options (
            reward_option_id   INT AUTO_INCREMENT PRIMARY KEY,
            template_id        INT NOT NULL,
            reward_label       VARCHAR(150),
            reward_type        ENUM('temp_ability','item','gil','chest','none') DEFAULT 'none',
            drop_chance        FLOAT NOT NULL DEFAULT 1.0,
            temp_ability_id    INT DEFAULT NULL,
            item_id            INT DEFAULT NULL,
            item_quantity      INT DEFAULT 1,
            gil_amount         INT DEFAULT 0,
            chest_id           INT DEFAULT NULL,
            reward_image_url   VARCHAR(255),
            created_at         TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (template_id)     REFERENCES room_templates(template_id)    ON DELETE CASCADE,
            FOREIGN KEY (temp_ability_id) REFERENCES temp_abilities(temp_ability_id) ON DELETE SET NULL,
            FOREIGN KEY (item_id)         REFERENCES items(item_id)                ON DELETE SET NULL,
            FOREIGN KEY (chest_id)        REFERENCES treasure_chests(chest_id)     ON DELETE SET NULL
        )
    ''',
    # ---------- illusion_crystal_templates ----------
    'illusion_crystal_templates': '''
        CREATE TABLE IF NOT EXISTS illusion_crystal_templates (
            template_id           INT AUTO_INCREMENT PRIMARY KEY,
            template_name         VARCHAR(100) NOT NULL,
            element_id            INT NOT NULL,
            counter_element_id    INT,
            image_url             VARCHAR(255),
            reward_image_url      VARCHAR(255),
            prompt_text           VARCHAR(255),
            created_at            TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (element_id)         REFERENCES elements(element_id) ON DELETE CASCADE,
            FOREIGN KEY (counter_element_id) REFERENCES elements(element_id) ON DELETE SET NULL
        )
    ''',
    # ---------- levels ----------
    'levels': '''
        CREATE TABLE IF NOT EXISTS levels (
            level                      INT PRIMARY KEY,
            required_exp               INT  NOT NULL,
            hp_increase                FLOAT NOT NULL,
            attack_increase            FLOAT NOT NULL,
            magic_increase             FLOAT NOT NULL,
            defense_increase           FLOAT NOT NULL,
            magic_defense_increase     FLOAT NOT NULL,
            accuracy_increase          FLOAT NOT NULL,
            evasion_increase           FLOAT NOT NULL,
            speed_increase             FLOAT NOT NULL,
            unlocked_abilities         JSON,
            created_at                 TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''',
    # ---------- class_abilities ----------
    'class_abilities': '''
        CREATE TABLE IF NOT EXISTS class_abilities (
            class_id   INT NOT NULL,
            ability_id INT NOT NULL,
            PRIMARY KEY (class_id, ability_id),
            FOREIGN KEY (class_id)   REFERENCES classes(class_id)   ON DELETE CASCADE,
            FOREIGN KEY (ability_id) REFERENCES abilities(ability_id) ON DELETE CASCADE
        )
    ''',
    # ---------- sessions ----------
    'sessions': '''
        CREATE TABLE IF NOT EXISTS sessions (
            session_id    INT AUTO_INCREMENT PRIMARY KEY,
            guild_id      BIGINT NOT NULL,
            thread_id     VARCHAR(64) NOT NULL,
            owner_id      BIGINT NOT NULL,
            num_players   INT NOT NULL,
            current_turn  BIGINT,
            player_turn   BIGINT,
            status        ENUM('active','paused','ended') DEFAULT 'active',
            current_floor INT  DEFAULT 1,
            total_floors  INT  DEFAULT 1,
            difficulty    VARCHAR(50),
            message_id    BIGINT,
            game_log      JSON,
            game_state    JSON,
            created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
        )
    ''',
    # ---------- session_players ----------
    'session_players': '''
        CREATE TABLE IF NOT EXISTS session_players (
            id          INT AUTO_INCREMENT PRIMARY KEY,
            session_id  INT NOT NULL,
            player_id   BIGINT NOT NULL,
            joined_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (session_id) REFERENCES sessions(session_id) ON DELETE CASCADE
        )
    ''',
    # ---------- players (NEW) ----------
    'players': '''
        CREATE TABLE IF NOT EXISTS players (
            player_id        BIGINT       NOT NULL,
            session_id       INT          NOT NULL,
            username         VARCHAR(100) NOT NULL,
            class_id         INT,
            level            INT DEFAULT 1,
            experience       INT DEFAULT 0,
            hp               INT DEFAULT 100,
            max_hp           INT DEFAULT 100,
            attack_power     INT DEFAULT 10,
            defense          INT DEFAULT 5,
            magic_power      INT DEFAULT 10,
            magic_defense    INT DEFAULT 5,
            accuracy         INT DEFAULT 95,
            evasion          INT DEFAULT 5,
            speed            INT DEFAULT 10,
            coord_x          INT DEFAULT 0,
            coord_y          INT DEFAULT 0,
            current_floor    INT DEFAULT 1,
            inventory        JSON,
            discovered_rooms JSON,
            gil              INT DEFAULT 0,
            status_effects   JSON,
            created_at       TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at       TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            PRIMARY KEY (player_id, session_id),
            FOREIGN KEY (session_id) REFERENCES sessions(session_id) ON DELETE CASCADE,
            FOREIGN KEY (class_id)   REFERENCES classes(class_id)   ON DELETE SET NULL
        )
    ''',
    # ---------- floors ----------
    'floors': '''
        CREATE TABLE IF NOT EXISTS floors (
            floor_id     INT AUTO_INCREMENT PRIMARY KEY,
            session_id   INT NOT NULL,
            difficulty   VARCHAR(50),
            total_rooms  INT NOT NULL,
            floor_number INT NOT NULL,
            is_goal_floor BOOLEAN DEFAULT FALSE,
            created_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (session_id) REFERENCES sessions(session_id) ON DELETE CASCADE
        )
    ''',
    # ---------- room_templates ----------
    'room_templates': '''
        CREATE TABLE IF NOT EXISTS room_templates (
            template_id   INT AUTO_INCREMENT PRIMARY KEY,
            room_type ENUM(
                'safe','monster','item','shop','boss','trap','illusion',
                'staircase_up','staircase_down','exit','locked','chest_unlocked','entrance',
                'miniboss','death'
            ) NOT NULL,
            template_name VARCHAR(100) NOT NULL,
            description   TEXT,
            image_url     VARCHAR(255),
            default_enemy_id INT,
            created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            trap_type ENUM('spike','gil_snatcher','mimic') DEFAULT NULL,
            trap_payload JSON,
            FOREIGN KEY (default_enemy_id) REFERENCES enemies(enemy_id)
                ON DELETE SET NULL
        )
    ''',
    # ---------- npc_vendors ----------
    'npc_vendors': '''
        CREATE TABLE IF NOT EXISTS npc_vendors (
            vendor_id   INT AUTO_INCREMENT PRIMARY KEY,
            vendor_name VARCHAR(100) NOT NULL,
            description TEXT,
            inventory   JSON,
            image_url   VARCHAR(255),
            created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''',
    # ---------- items ----------
    'items': '''
        CREATE TABLE IF NOT EXISTS items (
            item_id      INT AUTO_INCREMENT PRIMARY KEY,
            item_name    VARCHAR(100) NOT NULL,
            description  TEXT,
            effect       JSON,
            type ENUM('consumable','equipment','quest') NOT NULL,
            usage_limit  INT DEFAULT 1,
            price        INT DEFAULT 0,
            store_stock  INT,
            target_type  ENUM('self','enemy','ally','any') DEFAULT 'any',
            image_url    VARCHAR(255),
            creator_id   BIGINT,
            created_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''',
    # ---------- npc_vendor_items ----------
    'npc_vendor_items': '''
        CREATE TABLE IF NOT EXISTS npc_vendor_items (
            vendor_id INT NOT NULL,
            item_id   INT NOT NULL,
            price           INT DEFAULT 0,
            stock           INT,
            instance_stock  INT,
            PRIMARY KEY (vendor_id, item_id),
            FOREIGN KEY (vendor_id) REFERENCES npc_vendors(vendor_id) ON DELETE CASCADE,
            FOREIGN KEY (item_id)   REFERENCES items(item_id)        ON DELETE CASCADE
        )
    ''',
    # ---------- session_vendor_instances ----------
    'session_vendor_instances': '''
        CREATE TABLE IF NOT EXISTS session_vendor_instances (
            session_vendor_id INT AUTO_INCREMENT PRIMARY KEY,
            session_id INT NOT NULL,
            vendor_id  INT NOT NULL,
            vendor_name VARCHAR(100) NOT NULL,
            description TEXT,
            image_url   VARCHAR(255),
            created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (session_id) REFERENCES sessions(session_id) ON DELETE CASCADE
        )
    ''',
    # ---------- session_vendor_items ----------
    'session_vendor_items': '''
        CREATE TABLE IF NOT EXISTS session_vendor_items (
            session_vendor_id INT NOT NULL,
            item_id           INT NOT NULL,
            price             INT DEFAULT 0,
            stock             INT,
            instance_stock    INT,
            session_id        INT NOT NULL,
            PRIMARY KEY (session_vendor_id, item_id),
            FOREIGN KEY (session_vendor_id) REFERENCES session_vendor_instances(session_vendor_id) ON DELETE CASCADE,
            FOREIGN KEY (item_id)           REFERENCES items(item_id)              ON DELETE CASCADE,
            FOREIGN KEY (session_id)        REFERENCES sessions(session_id)        ON DELETE CASCADE
        )
    ''',
    # ---------- rooms ----------
    'rooms': '''
        CREATE TABLE IF NOT EXISTS rooms (
            room_id INT AUTO_INCREMENT PRIMARY KEY,
            session_id INT NOT NULL,
            floor_id   INT NOT NULL,
            coord_x    INT NOT NULL,
            coord_y    INT NOT NULL,
            description TEXT,
            room_type ENUM(
                'safe','monster','item','shop','boss','trap','illusion',
                'staircase_up','staircase_down','exit','locked','chest_unlocked','entrance'
            ) NOT NULL,
            image_url VARCHAR(255),
            default_enemy_id INT,
            exits JSON,
            has_encounter BOOLEAN DEFAULT FALSE,
            vendor_id INT,
            stair_up_floor   INT,
            stair_up_x       INT,
            stair_up_y       INT,
            stair_down_floor INT,
            stair_down_x     INT,
            stair_down_y     INT,
            inner_template_id INT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (session_id) REFERENCES sessions(session_id) ON DELETE CASCADE,
            FOREIGN KEY (floor_id)   REFERENCES floors(floor_id)     ON DELETE CASCADE,
            FOREIGN KEY (vendor_id)  REFERENCES session_vendor_instances(session_vendor_id) ON DELETE SET NULL,
            FOREIGN KEY (inner_template_id) REFERENCES room_templates(template_id) ON DELETE SET NULL
        )
    ''',
    # ---------- illusion_room_states ----------
    'illusion_room_states': '''
        CREATE TABLE IF NOT EXISTS illusion_room_states (
            room_state_id        INT AUTO_INCREMENT PRIMARY KEY,
            room_id              INT NOT NULL UNIQUE,
            session_id           INT NOT NULL,
            active_crystal_index INT DEFAULT 0,
            empowered            BOOLEAN DEFAULT FALSE,
            pending_teleport     BOOLEAN DEFAULT FALSE,
            updated_at           TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            FOREIGN KEY (room_id)    REFERENCES rooms(room_id)    ON DELETE CASCADE,
            FOREIGN KEY (session_id) REFERENCES sessions(session_id) ON DELETE CASCADE
        )
    ''',
    # ---------- illusion_crystal_instances ----------
    'illusion_crystal_instances': '''
        CREATE TABLE IF NOT EXISTS illusion_crystal_instances (
            instance_id     INT AUTO_INCREMENT PRIMARY KEY,
            room_id         INT NOT NULL,
            session_id      INT NOT NULL,
            template_id     INT NOT NULL,
            sequence_order  INT NOT NULL DEFAULT 0,
            status ENUM('intact','shattered','empowered') DEFAULT 'intact',
            updated_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (room_id)    REFERENCES rooms(room_id) ON DELETE CASCADE,
            FOREIGN KEY (session_id) REFERENCES sessions(session_id) ON DELETE CASCADE,
            FOREIGN KEY (template_id) REFERENCES illusion_crystal_templates(template_id) ON DELETE CASCADE
        )
    ''',
    # ---------- illusion_reward_instances ----------
    'illusion_reward_instances': '''
        CREATE TABLE IF NOT EXISTS illusion_reward_instances (
            instance_id           INT AUTO_INCREMENT PRIMARY KEY,
            room_id               INT NOT NULL,
            session_id            INT NOT NULL,
            reward_option_id      INT DEFAULT NULL,
            granted_to_player_id  BIGINT,
            reward_label          VARCHAR(150),
            reward_type           ENUM('temp_ability','item','gil','chest','none') DEFAULT 'none',
            reward_image_url      VARCHAR(255),
            resolved_temp_ability_id INT DEFAULT NULL,
            resolved_item_id      INT DEFAULT NULL,
            resolved_item_qty     INT DEFAULT 0,
            resolved_gil_amount   INT DEFAULT 0,
            resolved_chest_id     INT DEFAULT NULL,
            created_at            TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (room_id)          REFERENCES rooms(room_id)               ON DELETE CASCADE,
            FOREIGN KEY (session_id)       REFERENCES sessions(session_id)         ON DELETE CASCADE,
            FOREIGN KEY (reward_option_id) REFERENCES illusion_reward_options(reward_option_id) ON DELETE SET NULL,
            FOREIGN KEY (resolved_temp_ability_id) REFERENCES temp_abilities(temp_ability_id) ON DELETE SET NULL,
            FOREIGN KEY (resolved_item_id) REFERENCES items(item_id) ON DELETE SET NULL,
            FOREIGN KEY (resolved_chest_id) REFERENCES treasure_chests(chest_id) ON DELETE SET NULL
        )
    ''',
    # ---------- key_items ----------
    'key_items': '''
        CREATE TABLE IF NOT EXISTS key_items (
            key_item_id     INT AUTO_INCREMENT PRIMARY KEY,
            name            VARCHAR(100) NOT NULL,
            description     TEXT,
            image_url       VARCHAR(255),
            created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''',
    'treasure_chests': '''
        CREATE TABLE IF NOT EXISTS treasure_chests (
            chest_id       INT AUTO_INCREMENT PRIMARY KEY,
            chest_name     VARCHAR(100) NOT NULL,
            spawn_weight   FLOAT NOT NULL,
            template_id    INT NOT NULL,
            created_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (template_id)
                REFERENCES room_templates(template_id) ON DELETE CASCADE
        )
    ''',

    'chest_def_rewards': '''
        CREATE TABLE IF NOT EXISTS chest_def_rewards (
            def_id              INT AUTO_INCREMENT PRIMARY KEY,
            chest_id            INT NOT NULL,
            reward_type         ENUM('gil','item','key') NOT NULL,
            reward_item_id      INT DEFAULT NULL,
            reward_key_item_id  INT DEFAULT NULL,
            amount              INT NOT NULL,
            FOREIGN KEY (chest_id)
                REFERENCES treasure_chests(chest_id)      ON DELETE CASCADE,
            FOREIGN KEY (reward_item_id)
                REFERENCES items(item_id)                 ON DELETE SET NULL,
            FOREIGN KEY (reward_key_item_id)
                REFERENCES key_items(key_item_id)         ON DELETE SET NULL
        )
    ''',


    'treasure_chest_instances': '''
        CREATE TABLE IF NOT EXISTS treasure_chest_instances (
            instance_id       INT AUTO_INCREMENT PRIMARY KEY,
            session_id        INT                                 NOT NULL,
            room_id           INT                                 NOT NULL,
            chest_id          INT                                 NOT NULL,
            floor_id          INT                                 NOT NULL,
            coord_x           INT                                 NOT NULL,
            coord_y           INT                                 NOT NULL,
            step              INT               NOT NULL DEFAULT 1,
            correct_count     INT               NOT NULL DEFAULT 0,
            wrong_count       INT               NOT NULL DEFAULT 0,
            target_number     INT               NOT NULL,
            hint_value        INT               NOT NULL,
            is_unlocked       BOOLEAN           NOT NULL DEFAULT FALSE,
            created_at        TIMESTAMP         DEFAULT CURRENT_TIMESTAMP,
            updated_at        TIMESTAMP         DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            FOREIGN KEY (session_id)
                REFERENCES sessions(session_id)         ON DELETE CASCADE,
            FOREIGN KEY (room_id)
                REFERENCES rooms(room_id)               ON DELETE CASCADE,
            FOREIGN KEY (chest_id)
                REFERENCES treasure_chests(chest_id)    ON DELETE CASCADE,
            FOREIGN KEY (floor_id)
                REFERENCES floors(floor_id)             ON DELETE CASCADE
        )
    ''',
    'chest_instance_rewards': '''
        CREATE TABLE IF NOT EXISTS chest_instance_rewards (
            instance_id         INT        NOT NULL,
            reward_type         ENUM('gil','item','key') NOT NULL,
            reward_item_id      INT        NULL,
            reward_key_item_id  INT        NULL,
            reward_amount       INT        NOT NULL DEFAULT 1,
            PRIMARY KEY (
                instance_id,
                reward_type
            ),
            FOREIGN KEY (instance_id)
                REFERENCES treasure_chest_instances(instance_id) ON DELETE CASCADE,
            FOREIGN KEY (reward_item_id)
                REFERENCES items(item_id) ON DELETE SET NULL,
            FOREIGN KEY (reward_key_item_id)
                REFERENCES key_items(key_item_id) ON DELETE SET NULL
        )
    ''',


    # ---------- enemies ----------
    'enemies': '''
        CREATE TABLE IF NOT EXISTS enemies (
            enemy_id INT AUTO_INCREMENT PRIMARY KEY,
            enemy_name VARCHAR(50) NOT NULL,
            description TEXT,
            hp INT NOT NULL,
            max_hp INT NOT NULL,
            attack_power INT DEFAULT 10,
            defense INT DEFAULT 5,
            magic_power INT DEFAULT 10,
            magic_defense INT DEFAULT 5,
            accuracy INT DEFAULT 95,
            evasion INT DEFAULT 5,
            difficulty VARCHAR(50),
            abilities JSON,
            image_url VARCHAR(255),
            spawn_chance FLOAT DEFAULT 0.5,
            gil_drop INT,
            xp_reward INT,
            loot_item_id INT,
            loot_quantity INT DEFAULT 1,
            creator_id BIGINT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (loot_item_id) REFERENCES items(item_id) ON DELETE SET NULL
        )
    ''',
    # ---------- enemy_drops ----------
    'enemy_drops': '''
        CREATE TABLE IF NOT EXISTS enemy_drops (
            enemy_id INT NOT NULL,
            item_id  INT NOT NULL,
            drop_chance FLOAT NOT NULL,
            min_qty INT DEFAULT 1,
            max_qty INT DEFAULT 1,
            PRIMARY KEY (enemy_id, item_id),
            FOREIGN KEY (enemy_id) REFERENCES enemies(enemy_id) ON DELETE CASCADE,
            FOREIGN KEY (item_id)  REFERENCES items(item_id)  ON DELETE CASCADE
        )
    ''',
    # ---------- game_events ----------
    'game_events': '''
        CREATE TABLE IF NOT EXISTS game_events (
            event_id INT AUTO_INCREMENT PRIMARY KEY,
            event_name VARCHAR(100) NOT NULL,
            event_type ENUM('story','battle','item','trap','special') NOT NULL,
            effect JSON,
            floor_id INT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (floor_id) REFERENCES floors(floor_id) ON DELETE CASCADE
        )
    ''',
    # ---------- game_saves ----------
    'game_saves': '''
        CREATE TABLE IF NOT EXISTS game_saves (
            save_id INT AUTO_INCREMENT PRIMARY KEY,
            guild_id BIGINT NOT NULL,
            save_title VARCHAR(100) NOT NULL,
            save_data JSON NOT NULL,
            timestamp INT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''',
    # ---------- intro_steps ----------
    'intro_steps': '''
        CREATE TABLE IF NOT EXISTS intro_steps (
            intro_step_id INT AUTO_INCREMENT PRIMARY KEY,
            step_order INT NOT NULL,
            title VARCHAR(255) NOT NULL,
            description TEXT,
            image_url VARCHAR(255),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''',
    # ---------- enemy_abilities ----------
    'enemy_abilities': '''
        CREATE TABLE IF NOT EXISTS enemy_abilities (
            enemy_id  INT NOT NULL,
            ability_id INT NOT NULL,
            PRIMARY KEY (enemy_id, ability_id),
            FOREIGN KEY (enemy_id) REFERENCES enemies(enemy_id)   ON DELETE CASCADE,
            FOREIGN KEY (ability_id) REFERENCES abilities(ability_id) ON DELETE CASCADE
        )
    ''',
    # ---------- status_effects ----------
    'status_effects': '''
        CREATE TABLE IF NOT EXISTS status_effects (
            effect_id INT AUTO_INCREMENT PRIMARY KEY,
            effect_name VARCHAR(100) NOT NULL,
            effect_type ENUM('buff','debuff','neutral') NOT NULL,
            value INT NOT NULL,
            duration INT NOT NULL,
            icon_url VARCHAR(255),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''',
    # ---------- ability_status_effects ----------
    'ability_status_effects': '''
        CREATE TABLE IF NOT EXISTS ability_status_effects (
            ability_id INT NOT NULL,
            effect_id  INT NOT NULL,
            PRIMARY KEY (ability_id, effect_id),
            FOREIGN KEY (ability_id) REFERENCES abilities(ability_id) ON DELETE CASCADE,
            FOREIGN KEY (effect_id)  REFERENCES status_effects(effect_id) ON DELETE CASCADE
        )
    ''',
    # ---------- enemy_resistances ----------
    'enemy_resistances': '''
        CREATE TABLE IF NOT EXISTS enemy_resistances (
            enemy_id  INT NOT NULL,
            element_id INT NOT NULL,
            resistance INT NOT NULL,
            PRIMARY KEY (enemy_id, element_id),
            FOREIGN KEY (enemy_id) REFERENCES enemies(enemy_id)   ON DELETE CASCADE,
            FOREIGN KEY (element_id) REFERENCES elements(element_id) ON DELETE CASCADE
        )
    ''',
    # ---------- item_effects ----------
    'item_effects': '''
        CREATE TABLE IF NOT EXISTS item_effects (
            item_id  INT NOT NULL,
            effect_id INT NOT NULL,
            PRIMARY KEY (item_id, effect_id),
            FOREIGN KEY (item_id)  REFERENCES items(item_id)  ON DELETE CASCADE,
            FOREIGN KEY (effect_id)REFERENCES status_effects(effect_id)ON DELETE CASCADE
        )
    ''',
    # ---------- hub_embeds ----------
    'hub_embeds': '''
        CREATE TABLE IF NOT EXISTS hub_embeds (
            embed_id   INT AUTO_INCREMENT PRIMARY KEY,
            embed_type ENUM('main','tutorial','news') NOT NULL,
            title       VARCHAR(255),
            description TEXT,
            image_url   VARCHAR(255),
            text_field  TEXT,
            step_order  INT,
            created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''',
    # ---------- hub_buttons ----------
    'hub_buttons': '''
        CREATE TABLE IF NOT EXISTS hub_buttons (
            button_id      INT AUTO_INCREMENT PRIMARY KEY,
            embed_type     ENUM('main','tutorial','news') NOT NULL,
            button_label   VARCHAR(50),
            button_custom_id VARCHAR(50),
            created_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''',
    # ---------- high_scores ----------
    'high_scores': '''
        CREATE TABLE IF NOT EXISTS high_scores (
            score_id         INT AUTO_INCREMENT PRIMARY KEY,
            player_name      VARCHAR(100) NOT NULL,
            guild_id         BIGINT NOT NULL,
            player_level     INT DEFAULT 1,
            player_class     VARCHAR(50),
            gil              INT DEFAULT 0,
            enemies_defeated INT DEFAULT 0,
            play_time        INT DEFAULT 0,
            completed_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    '''
}

# ═══════════════════════════════════════════════════════════════════════════
#  CREATION ORDER (players added, floor_room_rules after difficulties)
# ═══════════════════════════════════════════════════════════════════════════
TABLE_ORDER = [
    'difficulties',
    'floor_room_rules',
    'elements',
    'element_relationships',
    'abilities',
    'classes',
    'levels',
    'class_abilities',
    'temp_abilities',
    'sessions',
    'session_players',
    'players',
    'floors',
    'items',
    'enemies',
    'room_templates',
    'npc_vendors',
    'npc_vendor_items',
    'session_vendor_instances',
    'session_vendor_items',
    'rooms',
    'illusion_room_states',
    'illusion_crystal_templates',
    'illusion_crystal_instances',
    'treasure_chests',
    'illusion_reward_options',
    'illusion_reward_instances',
    'key_items',
    'chest_def_rewards',
    'treasure_chest_instances',
    'chest_instance_rewards',
    'enemy_drops',
    'game_events',
    'game_saves',
    'intro_steps',
    'enemy_abilities',
    'status_effects',
    'ability_status_effects',
    'enemy_resistances',
    'item_effects',
    'hub_embeds',
    'hub_buttons',
    'high_scores'
]

# ═══════════════════════════════════════════════════════════════════════════
#  INSERT HELPERS
# ═══════════════════════════════════════════════════════════════════════════

def insert_difficulties(cur):
    logger.info("Checking difficulties seed data…")
    if not table_is_empty(cur, "difficulties"):
        logger.info("difficulties already populated – skipping")
        return
    cur.executemany(
        """
        INSERT INTO difficulties
          (name, width, height, min_floors, max_floors, min_rooms,
           enemy_chance, npc_count, basement_chance,
           basement_min_rooms, basement_max_rooms, created_at)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """,
        [row[1:] for row in MERGED_DIFFICULTIES]
    )
    logger.info("Inserted difficulties.")

def insert_floor_room_rules(cur):
    logger.info("Checking floor_room_rules seed data…")
    if table_is_empty(cur, "floor_room_rules") and MERGED_FLOOR_ROOM_RULES:
        cur.executemany(
            """
            INSERT INTO floor_room_rules
              (difficulty_name, floor_number, room_type, chance, max_per_floor, created_at)
            VALUES (%s, %s, %s, %s, %s, NOW())
            """,
            MERGED_FLOOR_ROOM_RULES
        )
        logger.info("Inserted floor_room_rules.")
    else:
        logger.info("floor_room_rules already populated or no seed data provided – skipping")

def insert_elements(cur):
    logger.info("Checking elements seed data…")
    cur.execute("SELECT element_id FROM elements")
    existing_ids = {row[0] for row in cur.fetchall()}
    rows_to_insert = [row for row in MERGED_ELEMENTS if row[0] not in existing_ids]
    if not rows_to_insert:
        logger.info("elements already populated – skipping")
        return
    cur.executemany(
        "INSERT INTO elements (element_id, element_name, created_at) VALUES (%s, %s, %s)",
        rows_to_insert
    )
    logger.info("Inserted elements.")

def insert_abilities_and_classes(cur):
    logger.info("Checking abilities seed data…")
    if table_is_empty(cur, "abilities"):
        cur.executemany(
            """
            INSERT INTO abilities
              (ability_name, description, effect, cooldown, icon_url,
               target_type, special_effect, element_id, created_at)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """,
            [row[1:] for row in MERGED_ABILITIES]
        )
        logger.info("Inserted abilities.")
    else:
        logger.info("abilities already populated – skipping")

    logger.info("Checking classes seed data…")
    if table_is_empty(cur, "classes"):
        cur.executemany(
            """
            INSERT INTO classes
              (class_name, description, base_hp, base_attack, base_magic,
               base_defense, base_magic_defense, base_accuracy,
               base_evasion, base_speed, image_url, creator_id, created_at)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """,
            [row[1:] for row in MERGED_CLASSES]
        )
        logger.info("Inserted classes.")
    else:
        logger.info("classes already populated – skipping")

    logger.info("Checking class_abilities links…")
    if table_is_empty(cur, "class_abilities"):
        cur.executemany(
            "INSERT INTO class_abilities (class_id, ability_id) VALUES (%s, %s)",
            MERGED_CLASS_ABILITIES
        )
        logger.info("Inserted class_abilities links.")
    else:
        logger.info("class_abilities already populated – skipping")

def insert_levels(cur):
    logger.info("Checking levels seed data…")
    if not table_is_empty(cur, "levels"):
        logger.info("levels already populated – skipping")
        return
    cur.executemany(
        """
        INSERT INTO levels
          (level, required_exp, hp_increase, attack_increase, magic_increase,
           defense_increase, magic_defense_increase, accuracy_increase,
           evasion_increase, speed_increase, unlocked_abilities, created_at)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """,
        MERGED_LEVELS
    )
    logger.info("Inserted levels.")

def insert_intro_steps(cur):
    logger.info("Checking intro_steps seed data…")
    if not table_is_empty(cur, "intro_steps"):
        logger.info("intro_steps already populated – skipping")
        return
    cur.executemany(
        """
        INSERT INTO intro_steps
          (step_order, title, description, image_url, created_at)
        VALUES (%s,%s,%s,%s,%s)
        """,
        [row[1:] for row in MERGED_INTRO_STEPS]
    )
    logger.info("Inserted intro_steps.")

def insert_room_templates(cur):
    logger.info("Checking room_templates seed data…")
    if not table_is_empty(cur, "room_templates"):
        logger.info("room_templates already populated – skipping")
        return
    cur.executemany(
        """
        INSERT INTO room_templates
          (room_type, template_name, description, image_url,
           default_enemy_id, created_at, trap_type, trap_payload)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
        """,
        [row[1:] for row in MERGED_ROOM_TEMPLATES]
    )
    logger.info("Inserted room_templates.")

def insert_npc_vendors(cur):
    logger.info("Checking npc_vendors seed data…")
    if not table_is_empty(cur, "npc_vendors"):
        logger.info("npc_vendors already populated – skipping")
        return
    cur.executemany(
        """
        INSERT INTO npc_vendors
          (vendor_name, description, inventory, image_url, created_at)
        VALUES (%s,%s,%s,%s,%s)
        """,
        [row[1:] for row in MERGED_NPC_VENDORS]
    )
    logger.info("Inserted npc_vendors.")

def insert_items(cur):
    logger.info("Checking items seed data…")
    if not table_is_empty(cur, "items"):
        logger.info("items already populated – skipping")
        return
    cur.executemany(
        """
        INSERT INTO items
          (item_name, description, effect, type, usage_limit, price,
           store_stock, target_type, image_url, creator_id, created_at)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """,
        [row[1:] for row in MERGED_ITEMS]
    )
    logger.info("Inserted items.")

def insert_enemies_and_abilities(cur):
    logger.info("Checking enemies seed data…")
    if table_is_empty(cur, "enemies"):
        cur.executemany(
            """
            INSERT INTO enemies
              (enemy_name, description, hp, max_hp, attack_power, defense,
               magic_power, magic_defense, accuracy, evasion, difficulty,
               abilities, image_url, spawn_chance, gil_drop, xp_reward,
               loot_item_id, loot_quantity, creator_id, created_at)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """,
            [row[1:] for row in MERGED_ENEMIES]
        )
        logger.info("Inserted enemies.")
    else:
        logger.info("enemies already populated – skipping")

    logger.info("Checking enemy_abilities links…")
    if table_is_empty(cur, "enemy_abilities"):
        cur.execute("SELECT enemy_id, enemy_name FROM enemies")
        id_map = {row[1]: row[0] for row in cur.fetchall()}
        enemy_names = [
            'Behemoth','Ghost','Dragon Whelp','Lich','Dark Knight',
            'Nightmare','Tonberry Chef','Overgrown Tonberry'
        ]
        rows = []
        for idx, ability in MERGED_ENEMY_ABILITIES:
            name = enemy_names[idx-1]
            if name in id_map:
                rows.append((id_map[name], ability))
        if rows:
            cur.executemany(
                "INSERT INTO enemy_abilities (enemy_id, ability_id) VALUES (%s,%s)",
                rows
            )
            logger.info("Inserted enemy_abilities links.")
    else:
        logger.info("enemy_abilities already populated – skipping")

def insert_enemy_drops(cur):
    logger.info("Checking enemy_drops seed data…")
    if not table_is_empty(cur, "enemy_drops"):
        logger.info("enemy_drops already populated – skipping")
        return
    cur.executemany(
        """
        INSERT INTO enemy_drops (enemy_id,item_id,drop_chance,min_qty,max_qty)
        VALUES (%s,%s,%s,%s,%s)
        """,
        MERGED_ENEMY_DROPS
    )
    logger.info("Inserted enemy_drops.")

def insert_enemy_resistances(cur):
    logger.info("Checking enemy_resistances seed data…")
    if not table_is_empty(cur, "enemy_resistances"):
        logger.info("enemy_resistances already populated – skipping")
        return
    cur.executemany(
        "INSERT INTO enemy_resistances (enemy_id,element_id,resistance) VALUES (%s,%s,%s)",
        MERGED_ENEMY_RESISTANCES
    )
    logger.info("Inserted enemy_resistances.")

def insert_npc_vendor_items(cur):
    logger.info("Checking npc_vendor_items seed data…")
    if not table_is_empty(cur, "npc_vendor_items"):
        logger.info("npc_vendor_items already populated – skipping")
        return
    cur.executemany(
        """
        INSERT INTO npc_vendor_items (vendor_id,item_id,price,stock,instance_stock)
        VALUES (%s,%s,%s,%s,%s)
        """,
        MERGED_NPC_VENDOR_ITEMS
    )
    logger.info("Inserted npc_vendor_items.")

def insert_new_relational_tables(cur):
    logger.info("Checking status_effects seed data…")
    if table_is_empty(cur, "status_effects"):
        cur.executemany(
            """
            INSERT INTO status_effects
              (effect_name,effect_type,value,duration,icon_url,created_at)
            VALUES (%s,%s,%s,%s,%s,%s)
            """,
            [row[1:] for row in MERGED_STATUS_EFFECTS]
        )
        logger.info("Inserted status_effects.")
    else:
        logger.info("status_effects already populated – skipping")

    logger.info("Checking ability_status_effects links…")
    if table_is_empty(cur, "ability_status_effects"):
        cur.executemany(
            "INSERT INTO ability_status_effects (ability_id,effect_id) VALUES (%s,%s)",
            MERGED_ABILITY_STATUS_EFFECTS
        )
        logger.info("Inserted ability_status_effects links.")
    else:
        logger.info("ability_status_effects already populated – skipping")

def insert_hub_embeds(cur):
    logger.info("Checking hub_embeds seed data…")
    if not table_is_empty(cur, "hub_embeds"):
        logger.info("hub_embeds already populated – skipping")
        return
    cur.executemany(
        """
        INSERT INTO hub_embeds
          (embed_type,title,description,image_url,text_field,step_order,created_at)
        VALUES (%s,%s,%s,%s,%s,%s,%s)
        """,
        [row[1:] for row in MERGED_HUB_EMBEDS]
    )
    logger.info("Inserted hub_embeds.")

# ═══════════════════════════════════════════════════════════════════════════
#  MAIN
# ═══════════════════════════════════════════════════════════════════════════
def main() -> None:
    logger.info("Connecting to MySQL…")
    try:
        with mysql.connector.connect(**DB_CONFIG) as cnx:
            with cnx.cursor() as cur:
                logger.info("Creating / verifying tables…")
                for tbl in TABLE_ORDER:
                    cur.execute(TABLES[tbl])
                    logger.debug("Table `%s` ready.", tbl)

                # ── seed data (order matters) ──────────────────────────────────
                insert_difficulties(cur)
                insert_floor_room_rules(cur)
                insert_elements(cur)
                insert_abilities_and_classes(cur)
                insert_levels(cur)
                insert_intro_steps(cur)
                insert_npc_vendors(cur)
                insert_items(cur)
                insert_enemies_and_abilities(cur)
                insert_room_templates(cur)
                insert_enemy_drops(cur)
                insert_enemy_resistances(cur)
                insert_npc_vendor_items(cur)
                insert_new_relational_tables(cur)
                insert_hub_embeds(cur)
                cnx.commit()
                logger.info("Database setup complete ✔")
    except Error as err:
        logger.error("Database error: %s", err)
        raise SystemExit(1)


if __name__ == "__main__":
    main()
