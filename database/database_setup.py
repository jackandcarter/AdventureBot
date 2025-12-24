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

def table_exists(cur, table_name: str) -> bool:
    cur.execute(
        """
        SELECT COUNT(*)
          FROM information_schema.tables
         WHERE table_schema = %s
           AND table_name = %s
        """,
        (DB_CONFIG["database"], table_name),
    )
    return cur.fetchone()[0] > 0

def column_exists(cur, table_name: str, column_name: str) -> bool:
    cur.execute(
        """
        SELECT COUNT(*)
          FROM information_schema.columns
         WHERE table_schema = %s
           AND table_name = %s
           AND column_name = %s
        """,
        (DB_CONFIG["database"], table_name, column_name),
    )
    return cur.fetchone()[0] > 0

def ensure_column(cur, table_name: str, column_name: str, definition: str) -> bool:
    if column_exists(cur, table_name, column_name):
        return False
    logger.info("Adding column %s.%s", table_name, column_name)
    cur.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {definition}")
    return True

def ensure_enum_values(cur, table_name: str, column_name: str, values: List[str], default: str) -> None:
    cur.execute(
        """
        SELECT column_type
          FROM information_schema.columns
         WHERE table_schema = %s
           AND table_name = %s
           AND column_name = %s
        """,
        (DB_CONFIG["database"], table_name, column_name),
    )
    row = cur.fetchone()
    if not row:
        return
    col_type = row[0] or ""
    if not col_type.lower().startswith("enum("):
        return
    current = [v.strip("'") for v in col_type[5:-1].split(",")]
    if all(v in current for v in values):
        return
    merged = sorted(set(current + values), key=lambda v: current.index(v) if v in current else len(current))
    enum_list = ",".join(f"'{v}'" for v in merged)
    logger.info("Updating enum %s.%s to include %s", table_name, column_name, values)
    cur.execute(
        f"ALTER TABLE {table_name} MODIFY COLUMN {column_name} ENUM({enum_list}) NOT NULL DEFAULT '{default}'"
    )

# ═══════════════════════════════════════════════════════════════════════════
#  SEED DATA
# ═══════════════════════════════════════════════════════════════════════════

# --- abilities ----------------------------------------------------------------
MERGED_ABILITIES: List[Tuple] = [
    (1, 'Cure', 'Heals a small amount of HP.', '{"heal_current_pct": 0.35}', 1, 10, '❤️', 'self', None, None, None, None, '2025-03-31 12:40:47', 'magic_power'),
    (2, 'Fire', 'Deals fire damage to an enemy.', '{"base_damage": 50}', 1, 10, '🔥', 'enemy', None, 1, None, None, '2025-03-31 12:40:47', 'magic_power'),
    (3, 'Blizzard', 'Deals ice damage to an enemy.', '{"base_damage": 50}', 1, 10, '❄️', 'enemy', None, 2, None, None, '2025-03-31 12:40:47', 'magic_power'),
    (4, 'Holy', 'Deals holy damage to one enemy.', '{"base_damage": 100}', 1, 30, '✨', 'enemy', None, 3, None, None, '2025-03-31 12:40:47', 'magic_power'),
    (5, 'Meteor', 'Massive non‑elemental damage to enemies.', '{"base_damage": 120}', 2, 60, '💫', 'enemy', None, 4, None, None, '2025-03-31 12:40:47', 'magic_power'),
    (6, 'Jump', 'Leap high and strike down a foe.', '{"base_damage": 50}', 5, 0, '🏃\u200d♂️', 'enemy', None, None, None, None, '2025-03-31 12:40:47', 'attack_power'),
    (7, 'Kick', 'Deals physical damage to all enemies.', '{"base_damage": 50}', 3, 0, '🥾', 'enemy', None, None, None, None, '2025-03-31 12:40:47', 'attack_power'),
    (8, 'Steal', 'Attempt to steal an item from an enemy.', '{"steal_chance": 50}', 0, 0, '🦹', 'enemy', None, None, None, None, '2025-03-31 12:40:47', 'attack_power'),
    (9, 'Scan', 'Reveal an enemy’s HP and weaknesses.', '{"scan": true}', 1, 0, '🔍', 'enemy', None, None, None, None, '2025-03-31 12:40:47', 'attack_power'),
    (10, 'Berserk', 'Boost attack but reduce defense.', '{"attack_power": 50, "defense_down": 20}', 3, 0, '💪🔼🛡️', 'self', None, None, 15, 5, '2025-03-31 12:40:47', 'attack_power'),
    (11, 'Revive', 'Revives a fainted ally with a surge of healing.', '{"heal": 50, "revive": true}', 1, 10, '♻️', 'ally', None, None, None, None, '2025-03-31 12:40:47', 'magic_power'),
    (12, 'Thunder', 'Deals lightning damage to an enemy.', '{"base_damage": 50}', 1, 10, '⚡', 'enemy', None, 5, None, None, '2025-03-31 12:40:47', 'magic_power'),
    (13, 'Barrier', 'Raises your defense for a short time.', '{"barrier": {"duration": 3}}', 3, 10, '🛡️🔼', 'self', None, None, 12, 3, '2025-03-31 12:40:47', 'defense'),
    (14, 'Power Break', 'Lower Enemy Attack Power.', '{"attack_power_down": 10}', 1, 10, '💪🔽', 'enemy', None, None, 1, 3, '2025-04-03 17:43:43', 'attack_power'),
    (15, 'Armor Break', 'Lower Enemy Defense', '{"defense_down": 30}', 1, 10, '🛡️🔽', 'enemy', None, None, 2, 3, '2025-04-03 17:43:43', 'attack_power'),
    (16, 'Mental Break', 'Lowers Enemy Magic Power and Magic Defense', '{"magic_power_down": 30, "magic_defense_down": 30}', 1, 10, '🔮🛡️🔽', 'enemy', None, None, 14, 3, '2025-04-03 17:43:43', 'magic_power'),
    (17, 'Fira', 'Deals greater fire damage to one enemy.', '{"base_damage": 70}', 1, 20, '🔥', 'enemy', None, 1, None, None, '2025-04-03 17:43:43', 'magic_power'),
    (18, 'FIraga', 'Deals devastating fire damage to one enemy.', '{"base_damage": 90}', 1, 30, '🔥', 'enemy', None, 1, None, None, '2025-04-03 17:43:43', 'magic_power'),
    (19, 'Bizzara', 'Deals greater ice damage to one enemy.', '{"base_damage": 70}', 1, 20, '❄️', 'enemy', None, 2, None, None, '2025-04-03 17:43:43', 'magic_power'),
    (20, 'Bizzaga', 'Deals devastating ice damage to one enemy.', '{"base_damage": 90}', 1, 30, '❄️', 'enemy', None, 2, None, None, '2025-04-03 17:43:43', 'magic_power'),
    (21, 'Thundara', 'Deals greater lightning damage to a single enemy.', '{"base_damage": 70}', 1, 20, '⚡', 'enemy', None, 5, None, None, '2025-04-03 17:43:43', 'magic_power'),
    (22, 'Thundaga', 'Deals devastating lightning damage to a single enemy.', '{"base_damage": 90}', 1, 30, '⚡', 'enemy', None, 5, None, None, '2025-04-03 17:43:43', 'magic_power'),
    (23, 'Flare', 'A massive non‑elemental magic attack dealing significant damage.', '{"base_damage": 100}', 2, 50, '💥', 'enemy', None, 4, None, None, '2025-04-03 17:43:43', 'magic_power'),
    (24, 'Ultima', 'A massive non‑elemental magic attack dealing very high damage.', '{"base_damage": 150}', 3, 80, '🌀', 'enemy', None, 4, None, None, '2025-04-03 17:43:43', 'magic_power'),
    (25, 'Comet', 'A massive non‑elemental magic attack dealing very high damage.', '{"base_damage": 125}', 2, 60, '☄️', 'enemy', None, 4, None, None, '2025-04-03 17:43:43', 'magic_power'),
    (26, 'Cura', 'Heals a greater amount of HP.', '{"heal_current_pct": 0.75}', 1, 15, '❤️', 'self', None, None, None, None, '2025-04-03 17:43:43', 'magic_power'),
    (27, 'Curaga', 'Heals a high amount of HP.', '{"heal_current_pct": 1.0}', 1, 20, '❤️', 'self', None, None, None, None, '2025-04-03 17:43:43', 'magic_power'),
    (28, 'Regen', 'Heals a small amount of HP over time.', '{"healing_over_time": {"percent": 0.2, "duration": 10}}', 1, 15, '❤️🔄', 'self', None, None, 4, 10, '2025-04-03 17:43:43', 'magic_power'),
    (29, 'Shell', 'Raises your magic defense.', '{"magic_defense_up": 30}', 1, 10, '🔮🛡️🔼', 'self', None, None, 13, 5, '2025-04-03 17:43:43', 'magic_power'),
    (30, 'Blink', 'Raises your evasion.', '{"evasion_up": 30}', 2, 10, '🎯🔼', 'self', None, None, 10, 5, '2025-04-03 17:43:43', 'magic_power'),
    (31, 'Demi', 'Deals damaged based on enemy health.', '{"percent_damage": 0.25}', 1, 20, '🌀', 'enemy', None, 4, None, None, '2025-04-03 17:43:43', 'attack_power'),
    (32, 'Gravity', 'Deals Air based damage while grounding flying enemies.', '{"base_damage": 80}', 1, 10, '🪐', 'enemy', None, None, None, None, '2025-04-03 17:43:43', 'magic_power'),
    (33, 'Haste', 'Grants higher speed with chance of increasing turns.', None, 3, 10, '⏱️🔼', 'self', None, None, None, None, '2025-04-03 17:43:43', 'magic_power'),
    (34, 'Slow', 'Lowers enemy speed with chance of reducing turns.', None, 2, 10, '⏳🔽', 'enemy', None, None, None, None, '2025-04-03 17:43:43', 'magic_power'),
    (35, 'Poison', 'Deals a small amount of damage over time.', '{"damage_over_time": {"duration": 3, "damage_per_turn": 10}}', 3, 10, '☠️', 'enemy', None, None, 3, 5, '2025-04-03 17:43:43', 'attack_power'),
    (36, 'Bio', 'Deals a greater amount of damage over time.', '{"damage_over_time": {"duration": 5, "damage_per_turn": 12}}', 5, 20, '☣️', 'enemy', None, None, 8, 5, '2025-04-03 17:43:43', 'attack_power'),
    (37, 'Focus', 'Raises your magic power.', '{"magic_power_up": 30}', 1, 5, '🔮🔼', 'self', None, None, 16, 5, '2025-04-03 17:43:43', 'attack_power'),
    (38, 'Fireblade', 'A Spellblade ability that fuses fire to your attacks.', '{"base_damage": 50}', 1, 10, '🔥⚔️', 'enemy', None, 1, None, None, '2025-04-03 17:51:14', 'attack_power'),
    (39, 'Iceblade', 'A Spellblade ability that fuses ice to your attacks.', '{"base_damage": 50}', 1, 10, '❄️⚔️', 'enemy', None, 2, None, None, '2025-04-03 17:51:14', 'attack_power'),
    (40, 'Thunderblade', 'A Spellblade ability that fuses thunder to your attacks.', '{"base_damage": 50}', 1, 10, '⚡⚔️', 'enemy', None, 6, None, None, '2025-04-03 17:51:14', 'attack_power'),
    (41, 'Heavy Swing', 'A heavy attack dealing medium damage.', '{"base_damage": 50}', 2, 0, '⚔️', 'enemy', None, None, None, None, '2025-04-15 06:35:52', 'attack_power'),
    (42, 'Climhazzard', 'A deadly physical attack dealing high damage.', '{"base_damage": 110}', 5, 0, '⚔️', 'enemy', None, None, None, None, '2025-04-15 06:59:30', 'attack_power'),
    (43, 'Break', 'Reduce enemy HP to 1.', '{"set_enemy_hp_to": 1}', 5, 0, '⚔️', 'enemy', None, None, None, None, '2025-04-15 07:47:21', 'attack_power'),
    (44, 'Demiblade', 'A Spellblade ability that reduces enemy hp by a percentage.', '{"percent_damage": 0.25}', 1, 30, '⚔️', 'enemy', None, 4, None, None, '2025-04-28 00:16:00', 'attack_power'),
    (45, 'Gravityblade', 'A Spellblade ability that fuses gravity magic to your attacks.', '{"base_damage": 80}', 1, 20, '⚔️', 'enemy', None, 5, None, None, '2025-04-28 00:16:00', 'attack_power'),
    (46, 'Silence', 'Stops enemies from using magic for a short time.', None, 1, 10, None, 'enemy', None, None, 9, 3, '2025-04-28 00:16:00', 'attack_power'),
    (47, 'BioBlade', 'Deals initial base damage and greater amount of damage over time.', '{"damage_over_time": {"duration": 5, "damage_per_turn": 12}, "non_elemental_damage": 20}', 1, 20, '☣️⚔', 'any', None, None, 8, 3, '2025-05-01 17:17:43', 'attack_power'),
    (48, 'Lucky 7', 'Deals 7, 77, 777, or 7777 damage if the player HP has a 7 in it. Otherwise deal 1 damage.', '{"lucky_7": true}', 1, 0, '7️⃣', 'enemy', None, None, None, None, '2025-05-10 19:38:35', 'attack_power'),
    (49, 'Excalibur', 'Summons the legendary sword to deal massive non-elemental damage.', '{"base_damage": 200}', 5, 0, '⚔️', 'enemy', None, 4, None, None, '2025-05-10 20:12:34', 'attack_power'),
    (50, 'Pilfer Gil', 'Steals Gil from an enemy.', '{"pilfer_gil": true}', 2, 0, '💰', 'enemy', None, None, None, None, '2025-05-10 20:12:34', 'attack_power'),
    (51, 'Mug', 'Deals damage while stealing Gil from the enemy.', '{"mug": {"damage": 50}}', 1, 0, '⚔️💰', 'enemy', None, None, None, None, '2025-05-10 20:12:34', 'attack_power'),
    (52, 'Light Shot', 'Light attack on an enemy', '{"base_damage": 50}', 1, 0, '⚔️', 'enemy', None, None, None, None, '2025-05-10 23:26:42', 'attack_power'),
    (53, 'Heavy Shot', 'Heavy attack on an enemy', '{"base_damage": 150}', 1, 0, '⚔️', 'enemy', None, None, None, None, '2025-05-10 23:26:42', 'attack_power'),
    (54, 'Cross-Slash', None, '{"base_damage": 200}', 1, 0, '⚔️', 'enemy', None, None, None, None, '2025-05-11 08:48:29', 'attack_power'),
    (55, 'Meteorain', None, '{"base_damage": 300}', 1, 0, '⚔️', 'enemy', None, None, None, None, '2025-05-11 08:48:29', 'attack_power'),
    (56, 'Finishing Touch', None, '{"base_damage": 400}', 1, 0, '⚔️', 'enemy', None, None, None, None, '2025-05-11 08:48:29', 'attack_power'),
    (57, 'Omnislash', None, '{"base_damage": 999}', 1, 0, '⚔️', 'enemy', None, None, None, None, '2025-05-11 08:48:29', 'attack_power'),
    (58, 'Stagger', None, '{"base_damage": 150}', 1, 0, '⚔️', 'enemy', None, None, None, None, '2025-05-11 08:48:29', 'attack_power'),
    (59, 'Bull Charge', None, '{"base_damage": 200}', 1, 0, '⚔️', 'enemy', None, None, None, None, '2025-05-11 08:48:29', 'attack_power'),
    (60, 'Wallop', None, '{"base_damage": 300}', 1, 0, '⚔️', 'enemy', None, None, None, None, '2025-05-11 08:48:29', 'attack_power'),
    (61, 'Poisontouch', None, '{"damage_over_time": {"duration": 5, "damage_per_turn": 45}}', 1, 0, '⚔️', 'enemy', None, None, None, None, '2025-05-11 08:48:29', 'attack_power'),
    (62, 'Grand Lethal', None, '{"base_damage": 300}', 1, 0, '⚔️', 'enemy', None, None, None, None, '2025-05-11 08:48:29', 'attack_power'),
    (63, 'Bandit', None, '{"mug": {"damage": 100}}', 1, 0, '⚔️', 'enemy', None, None, None, None, '2025-05-11 08:48:29', 'attack_power'),
    (64, 'Master Thief', None, '{"base_damage": 200}', 1, 0, '⚔️', 'enemy', None, None, None, None, '2025-05-11 08:48:29', 'attack_power'),
    (65, 'Confuse', None, '{"base_damage": 200}', 1, 0, '⚔️', 'enemy', None, None, None, None, '2025-05-11 08:48:29', 'attack_power'),
    (66, 'Lancet', None, '{"base_damage": 200}', 1, 0, '⚔️', 'enemy', None, None, None, None, '2025-05-11 08:48:29', 'attack_power'),
    (67, 'High Jump', None, '{"base_damage": 200}', 1, 0, '⚔️', 'enemy', None, None, None, None, '2025-05-11 08:48:29', 'attack_power'),
    (68, 'Eye 4 Eye', None, '{"base_damage": 300}', 1, 0, '⚔️', 'enemy', None, None, None, None, '2025-05-11 08:48:29', 'attack_power'),
    (69, 'Beast Killer', None, '{"base_damage": 400}', 1, 0, '⚔️', 'enemy', None, None, None, None, '2025-05-11 08:48:29', 'attack_power'),
    (70, 'Avalanche', None, '{"base_damage": 300}', 1, 0, '⚔️', 'enemy', None, 2, None, None, '2025-05-11 08:48:29', 'magic_power'),
    (71, 'Tornado', None, '{"base_damage": 300}', 1, 0, '⚔️', 'enemy', None, 5, None, None, '2025-05-11 08:48:29', 'magic_power'),
    (72, 'Earthquake', None, '{"base_damage": 300}', 1, 0, '⚔️', 'enemy', None, 8, None, None, '2025-05-11 08:48:29', 'magic_power'),
    (73, 'Meteor', None, '{"base_damage": 400}', 1, 60, '⚔️', 'enemy', None, 4, None, None, '2025-05-11 08:48:29', 'magic_power'),
    (74, 'UltimaBlade', None, '{"base_damage": 400}', 1, 90, '⚔️', 'enemy', None, 4, None, None, '2025-05-11 08:48:29', 'magic_power'),
    (75, 'MeteorBlade', None, '{"base_damage": 400}', 1, 80, '⚔️', 'enemy', None, 4, None, None, '2025-05-11 08:48:29', 'magic_power'),
    (76, 'HolyBlade', None, '{"base_damage": 400}', 1, 40, '⚔️', 'enemy', None, 3, None, None, '2025-05-11 08:48:29', 'magic_power'),
    (77, 'GravijaBlade', None, '{"base_damage": 400}', 1, 50, '⚔️', 'enemy', None, 5, None, None, '2025-05-11 08:48:29', 'magic_power'),
    (78, 'Bio II', None, '{"damage_over_time": {"duration": 7, "damage_per_turn": 72}}', 1, 25, '⚔️', 'enemy', None, None, 8, 7, '2025-05-11 08:48:29', 'attack_power'),
    (79, 'Frog', None, '{"base_damage": 0}', 1, 25, '⚔️', 'enemy', None, None, None, None, '2025-05-11 08:48:29', 'attack_power'),
    (80, 'Full-Cure', None, '{"heal": 9999}', 1, 50, None, 'self', None, None, None, None, '2025-05-11 08:48:29', 'attack_power'),
    (81, 'Reflect', None, '{"base_damage": 150}', 1, 15, None, 'self', None, None, None, None, '2025-05-11 08:48:29', 'attack_power'),
    (82, 'Dbl Holy', None, '{"base_damage": 400}', 1, 50, '⚔️', 'enemy', None, 3, None, None, '2025-05-11 08:48:29', 'magic_power'),
    (83, 'Dbl Ultima', None, '{"base_damage": 400}', 1, 80, '⚔️', 'enemy', None, 4, None, None, '2025-05-11 08:48:29', 'magic_power'),
    (84, 'Dbl Focus', None, '{"base_damage": 150}', 1, 0, None, 'self', None, None, None, None, '2025-05-11 08:48:29', 'magic_power'),
    (85, 'Dbl Cure', None, '{"heal": 500}', 1, 10, None, 'self', None, None, None, None, '2025-05-11 08:48:29', 'magic_power'),
    (86, 'Dbl Flare', None, '{"base_damage": 200}', 1, 50, '⚔️', 'enemy', None, 4, None, None, '2025-05-11 08:48:29', 'magic_power'),
    (87, 'Dbl Dia', None, '{"base_damage": 200}', 1, 35, '⚔️', 'enemy', None, 3, None, None, '2025-05-11 08:48:29', 'magic_power'),
    (88, 'White Wind', None, '{"healing_over_time": {"percent": 0.05, "duration": 10}}', 0, 25, '❤️', 'self', None, None, 4, 10, '2025-05-14 06:44:27', 'magic_power'),
    (89, 'Mighty Guard', None, '{"barrier": {"duration": 3}}', 0, 25, '🛡️🔼', 'self', None, None, 12, 3, '2025-05-14 06:44:27', 'attack_power'),
    (90, 'Blue Bullet', None, '{"base_damage": 100}', 0, 25, '⚔️', 'enemy', None, None, None, None, '2025-05-14 06:45:27', 'attack_power'),
    (91, 'Karma', 'Deals Damage based on turn amount', '{"karma": true}', 3, 0, None, 'any', None, None, None, None, '2025-05-16 21:13:30', 'attack_power'),
    (92, '50 Needles', 'Deals 50 damage with 100% hit rate and ignores defense.', '{"flat_damage": 50}', 0, 0, None, 'any', None, None, None, None, '2025-05-22 20:21:04', 'attack_power'),
    (93, '1,000 Needles', 'Deals 1,000 damage with 100% hit rate and ignores defense.', '{"flat_damage": 1000}', 0, 0, None, 'any', None, None, None, None, '2025-05-22 20:21:04', 'attack_power'),
    (94, 'Absorb MP', 'Drain MP from an enemy and restore it to yourself.', '{"absorb_mp": {"amount": 25}}', 2, '💧', 'enemy', None, None, None, None, '2025-05-22 15:21:04', 'magic_power'),
    (95, 'Quake', 'Shake the earth to damage enemies.', '{"base_damage": 90}', 1, '🌎', 'enemy', None, 8, None, None, '2025-09-13 00:00:00', 'magic_power'),
    (96, 'Flood', 'Summon a surge of water that crashes into foes.', '{"base_damage": 90}', 1, '🌊', 'enemy', None, 7, None, None, '2025-09-13 00:00:00', 'magic_power'),
    (97, 'Aero', 'Slice enemies with razor-sharp wind.', '{"base_damage": 70}', 1, '🌪️', 'enemy', None, 5, None, None, '2025-09-13 00:00:00', 'magic_power'),
    (98, 'Wind Slash', 'Unleash a cutting gust that tears through foes.', '{"base_damage": 85}', 1, '🍃', 'enemy', None, 5, None, None, '2025-09-13 00:00:00', 'magic_power'),
    (99, "Gaia's Wrath", 'Call on the land itself to crush enemies.', '{"base_damage": 120}', 2, '🪨', 'enemy', None, 8, None, None, '2025-09-13 00:00:00', 'magic_power'),
    (100, 'Ballad of Might', 'A stirring song that raises attack power.', '{"status_effects": [{"name": "Attack Up", "duration": 5}], "status_only": true}', 2, '🎵⚔️', 'self', None, None, None, None, '2025-09-20 00:00:00', 'magic_power'),
    (101, 'Ballad of Guarding', 'A protective melody that raises defense.', '{"status_effects": [{"name": "Defense Up", "duration": 5}], "status_only": true}', 2, '🎵🛡️', 'self', None, None, None, None, '2025-09-20 00:00:00', 'magic_power'),
    (102, 'Ballad of Warding', 'A warding hymn that raises magic defense.', '{"status_effects": [{"name": "Mag.Def Up", "duration": 5}], "status_only": true}', 2, '🎵🔮🛡️', 'self', None, None, None, None, '2025-09-20 00:00:00', 'magic_power'),
    (103, 'Ballad of Clarity', 'A song that heightens magical focus.', '{"status_effects": [{"name": "Magic Up", "duration": 5}], "status_only": true}', 2, '🎵🔮', 'self', None, None, None, None, '2025-09-20 00:00:00', 'magic_power'),
    (104, 'Swift Etude', 'A quick tempo that raises evasion.', '{"status_effects": [{"name": "Evasion Up", "duration": 4}], "status_only": true}', 2, '🎵🎯', 'self', None, None, None, None, '2025-09-20 00:00:00', 'magic_power'),
    (105, 'Healing Carol', 'A gentle carol that restores health over time.', '{"healing_over_time": {"percent": 0.1, "duration": 5}, "hot_name": "Regen"}', 3, '🎵❤️', 'self', None, None, None, None, '2025-09-20 00:00:00', 'magic_power'),
    (106, 'Dissonant Requiem', 'A discordant refrain that weakens defenses.', '{"status_effects": [{"name": "Defense Down", "duration": 3, "chance": 0.75}, {"name": "Mag.Def Down", "duration": 3, "chance": 0.75}], "status_only": true}', 3, '🎵🔽', 'enemy', None, None, None, None, '2025-09-20 00:00:00', 'magic_power'),
    (107, 'Soothing Lullaby', 'A lullaby that can briefly stun a foe.', '{"status_effects": [{"name": "Stun", "duration": 1, "chance": 0.6}], "status_only": true}', 3, '🎵💤', 'enemy', None, None, None, None, '2025-09-20 00:00:00', 'magic_power'),
    (108, 'Silencing Coda', 'A sharp coda that can silence a foe.', '{"status_effects": [{"name": "Silence", "duration": 2, "chance": 0.6}], "status_only": true}', 3, '🎵🤐', 'enemy', None, None, None, None, '2025-09-20 00:00:00', 'magic_power'),
    (109, 'Defend', 'Brace to reduce incoming damage for a short time.', '{"status_effects": [{"name": "Defense Up", "duration": 2}], "status_only": true}', 1, '🛡️', 'self', None, None, None, None, '2025-09-20 00:00:00', 'defense'),
    (110, 'Cover', 'Protect an ally by taking hits meant for them.', '{"status_effects": [{"name": "Defense Up", "duration": 3}], "status_only": true}', 2, '🛡️❤️', 'ally', None, None, None, None, '2025-09-20 00:00:00', 'defense'),
    (111, 'Provoke', 'Draw enemy attention, leaving them exposed.', '{"status_effects": [{"name": "Defense Down", "duration": 2, "chance": 0.6}], "status_only": true}', 1, '📢', 'enemy', None, None, None, None, '2025-09-20 00:00:00', 'attack_power'),
    (112, 'Shield Bash', 'Bash with a shield to damage and possibly stun.', '{"base_damage": 80, "status_effects": [{"name": "Stun", "duration": 1, "chance": 0.3}]}', 1, '🛡️', 'enemy', None, None, None, None, '2025-09-20 00:00:00', 'attack_power'),
    (113, 'Shield Break', 'Crush the foe’s guard, lowering defense.', '{"base_damage": 100, "status_effects": [{"name": "Defense Down", "duration": 3, "chance": 0.5}]}', 1, '🛡️🔽', 'enemy', None, None, None, None, '2025-09-20 00:00:00', 'attack_power'),
    (114, 'Magic Break', 'Shatter magical strength to lower magic power.', '{"magic_power_down": 25}', 1, '🔮🔽', 'enemy', None, None, None, None, '2025-09-20 00:00:00', 'attack_power'),
    (115, 'Speed Break', 'Hinder the target’s speed and reaction time.', '{"status_effects": [{"name": "Slow", "duration": 2, "chance": 0.6}], "status_only": true}', 1, '⏳🔽', 'enemy', None, None, None, None, '2025-09-20 00:00:00', 'attack_power'),
    (116, 'Full Break', 'Cripple the target’s offensive and defensive power.', '{"attack_power_down": 15, "defense_down": 15, "magic_power_down": 15, "magic_defense_down": 15}', 3, '💥🔽', 'enemy', None, None, None, None, '2025-09-20 00:00:00', 'attack_power'),
    (117, 'Cleave', 'A wide, heavy swing that cuts through the foe.', '{"base_damage": 120}', 1, '⚔️', 'enemy', None, None, None, None, '2025-09-20 00:00:00', 'attack_power'),
    (118, 'Double Cut', 'Strike twice in rapid succession.', '{"multi_hit": {"hits": 2, "base_damage": 80, "scaling_stat": "attack_power", "scaling_factor": 1.0}}', 1, '⚔️', 'enemy', None, None, None, None, '2025-09-20 00:00:00', 'attack_power'),
    (119, 'Tame', 'Attempt to tame a weakened beast to fight alongside you.', '{"tame": {"base_chance": 0.35, "hp_bonus": 0.3, "level_penalty": 0.05}}', 2, '🐾', 'enemy', None, None, None, None, '2025-09-25 00:00:00', 'attack_power'),
    (120, 'Train', 'Train a companion beast, boosting its combat prowess.', '{"status_effects": [{"name": "Attack Up", "duration": 3}, {"name": "Defense Up", "duration": 3}], "status_only": true}', 3, '🎯', 'self', None, None, None, None, '2025-09-25 00:00:00', 'attack_power'),
    (121, 'Beast Command', 'Issue a commanding order that disrupts a foe.', '{"base_damage": 70, "status_effects": [{"name": "Evasion Down", "duration": 2, "chance": 0.6}]}', 2, '🪢', 'enemy', None, None, None, None, '2025-09-25 00:00:00', 'attack_power'),
    (122, 'Angelo Search', 'Angelo sniffs out supplies, increasing your chance to find loot.', '{"status_effects": [{"name": "Haste", "duration": 3}, {"name": "Evasion Up", "duration": 3}], "status_only": true}', 0, '🐕', 'self', None, None, None, None, '2025-09-25 00:00:00', 'attack_power'),
    (123, 'Angelo Strike', 'Angelo darts forward with a piercing strike.', '{"base_damage": 160}', 1, '🐕⚔️', 'enemy', None, None, None, None, '2025-09-25 00:00:00', 'attack_power'),
    (124, 'Angelo Recover', 'Angelo restores HP to the party leader.', '{"heal": 120}', 1, '🐕❤️', 'self', None, None, None, None, '2025-09-25 00:00:00', 'magic_power'),
    (125, 'Angelo Shield', 'Angelo protects you with a defensive barrier.', '{"status_effects": [{"name": "Defense Up", "duration": 3}], "status_only": true}', 2, '🐕🛡️', 'self', None, None, None, None, '2025-09-25 00:00:00', 'defense'),
    (201, 'Hellfire', 'Engulf the enemy in infernal flames.', '{"base_damage": 160}', 2, 35, '🔥', 'enemy', None, 1, None, None, '2025-07-01 05:00:00', 'magic_power'),
    (202, 'Diamond Dust', 'Unleash a frozen tempest.', '{"base_damage": 160}', 2, 35, '❄️', 'enemy', None, 2, None, None, '2025-07-01 05:00:00', 'magic_power'),
    (203, 'Judgment Bolt', 'Call down a thunderous strike.', '{"base_damage": 175}', 3, 40, '⚡', 'enemy', None, 6, None, None, '2025-07-01 05:00:00', 'magic_power'),
    (204, 'Inferno', 'Engulf the enemy in infernal flames.', '{"base_damage": 275}', 0, 50, None, 'enemy', None, 1, 6, 10, '2025-12-20 23:44:43', 'magic_power'),
    (205, 'Cold Snap', 'Freeze Enemies while causing damage.', '{"base_damage": 275}', 0, 50, None, 'enemy', None, 2, 7, 10, '2025-12-20 23:44:43', 'magic_power'),
    (206, 'Storm Tempest', 'Stun your foe with a devistating storm.', '{"base_damage": 275}', 0, 50, None, 'enemy', None, 6, 5, 10, '2025-12-20 23:44:43', 'magic_power'),
]

# --- eidolon abilities (with mp_cost) -----------------------------------------
MERGED_EIDOLON_ABILITY_DEFS: List[Tuple] = [
    (201, 'Hellfire', 'Engulf the enemy in infernal flames.', '{"base_damage": 160}', 2, '🔥', 'enemy', None, 1, None, None, '2025-07-01 00:00:00', 'magic_power', 35),
    (202, 'Diamond Dust', 'Unleash a frozen tempest.', '{"base_damage": 160}', 2, '❄️', 'enemy', None, 2, None, None, '2025-07-01 00:00:00', 'magic_power', 35),
    (203, 'Judgment Bolt', 'Call down a thunderous strike.', '{"base_damage": 175}', 3, '⚡', 'enemy', None, 6, None, None, '2025-07-01 00:00:00', 'magic_power', 40),
]

# --- ability ↔ status‑effects -------------------------------------------------
MERGED_ABILITY_STATUS_EFFECTS: List[Tuple[int, int]] = [
    (10, 2),
    (10, 2),
    (33, 17),
    (34, 18),
    (35, 3),
    (36, 8),
    (46, 9),
    (13, 13),
    (14, 19),
    (15, 2),
    (16, 14),
    (37, 16),
    (43, 19),
]

# --- class ↔ ability links ----------------------------------------------------
MERGED_CLASS_ABILITIES: List[Tuple[int, int, int]] = [
    (1, 7, 1),
    (1, 109, 1),
    (1, 111, 1),
    (1, 14, 1),
    (2, 7, 1),
    (2, 10, 1),
    (3, 38, 1),
    (3, 39, 1),
    (3, 40, 1),
    (4, 9, 1),
    (4, 50, 1),
    (5, 33, 1),
    (5, 34, 1),
    (5, 35, 1),
    (6, 6, 1),
    (6, 7, 1),
    (8, 1, 1),
    (9, 2, 1),
    (9, 3, 1),
    (9, 12, 1),
    (10, 13, 1),
    (10, 37, 1),
    (10, 97, 3),
    (11, 88, 1),
    (1, 15, 2),
    (1, 110, 2),
    (1, 112, 2),
    (1, 41, 2),
    (7, 52, 2),
    (9, 17, 2),
    (9, 28, 2),
    (9, 37, 2),
    (4, 48, 3),
    (7, 9, 3),
    (8, 11, 3),
    (9, 19, 3),
    (11, 89, 3),
    (7, 100, 3),
    (1, 117, 3),
    (7, 53, 4),
    (9, 21, 4),
    (1, 113, 4),
    (1, 118, 4),
    (7, 101, 5),
    (1, 16, 5),
    (1, 114, 5),
    (3, 47, 5),
    (4, 51, 5),
    (5, 32, 5),
    (6, 9, 5),
    (8, 4, 5),
    (9, 5, 5),
    (9, 36, 5),
    (10, 31, 5),
    (10, 95, 5),
    (11, 90, 5),
    (13, 119, 1),
    (13, 120, 2),
    (13, 121, 4),
    (7, 102, 7),
    (1, 42, 6),
    (1, 115, 6),
    (7, 103, 9),
    (10, 96, 7),
    (3, 45, 10),
    (5, 17, 10),
    (7, 33, 10),
    (8, 26, 10),
    (8, 28, 10),
    (9, 23, 10),
    (10, 23, 10),
    (10, 98, 10),
    (1, 116, 10),
    (7, 104, 11),
    (7, 105, 12),
    (1, 43, 15),
    (3, 44, 15),
    (5, 25, 15),
    (7, 106, 14),
    (8, 27, 15),
    (9, 18, 15),
    (9, 20, 15),
    (9, 22, 15),
    (10, 99, 15),
    (7, 107, 16),
    (3, 43, 20),
    (3, 49, 20),
    (7, 108, 18),
    (9, 24, 20)
]

# --- classes ------------------------------------------------------------------
MERGED_CLASSES: List[Tuple] = [
    (1, 'Warrior', 'A sturdy fighter with strong physical attacks.', 600, 40, 10, 0, 5, 5, 99, 1, 10, 'https://cdn.discordapp.com/attachments/1362832151485354065/1364778448379318442/war.gif?ex=680c39fa&is=680ae87a&hm=80c89e0290ea5ad2432f2d9b265df190741f94309c2bca981ad1885af90671c4&', None, '2025-03-31 07:40:47', 5),
    (2, 'Berserker', 'A savage fighter who channels uncontrollable fury.', 600, 45, 10, 0, 5, 5, 99, 1, 10, 'https://cdn.discordapp.com/attachments/1362832151485354065/1365296689379938355/Berserker.gif?ex=680ccb20&is=680b79a0&hm=aa06cfa2c7fb2fb30ffe9e4991d2dda0d4f9420587656a0ddc61b192372ad067&', None, '2025-04-03 12:05:45', 5),
    (3, 'Mystic Knight', 'A hybrid fighter that fuses magic to their blade.', 500, 40, 15, 0, 5, 5, 99, 1, 10, 'https://cdn.discordapp.com/attachments/1362832151485354065/1365296718815432724/mystic.gif?ex=680ccb27&is=680b79a7&hm=3f8ad9a2b215496adbc6c0dfd328a9e30621c73e292c40f0fd5ebfb0025bd910&', None, '2025-04-03 12:05:45', 5),
    (4, 'Thief', 'A quick fighter who excels at stealing items.', 500, 45, 10, 0, 5, 5, 99, 1, 10, 'https://cdn.discordapp.com/attachments/1362832151485354065/1365296784301363303/thief.gif?ex=680ccb37&is=680b79b7&hm=34ee2d981b968e6de51e52e85c51b3c16ed4ac71974df3ada3f305603d95b59a&', None, '2025-03-31 07:40:47', 5),
    (5, 'Green Mage', 'A powerful mage that manipulates time and space magics.', 500, 20, 20, 80, 5, 5, 99, 1, 10, None, None, '2025-03-31 07:40:47', 5),
    (6, 'Dragoon', 'A lancer who can jump high and strike down foes.', 500, 40, 10, 0, 5, 5, 99, 1, 10, None, None, '2025-03-31 07:40:47', 5),
    (7, 'Bard', 'A ranged attacker wielding a bow and musical influence.', 500, 45, 20, 40, 5, 5, 99, 1, 10, None, None, '2025-04-03 12:05:45', 5),
    (8, 'White Mage', 'A healer who uses holy magic to restore and protect.', 500, 15, 20, 120, 5, 5, 99, 1, 10, 'https://cdn.discordapp.com/attachments/1362832151485354065/1365296761723158538/whitemage.gif?ex=680ccb31&is=680b79b1&hm=cd94aeb45272086aac0e5c40507390e5738ef9ee419634a7eded75bf67ea91be&', None, '2025-04-03 12:05:45', 5),
    (9, 'Black Mage', 'A mage who uses destructive elemental spells.', 500, 15, 25, 120, 5, 5, 99, 1, 10, 'https://cdn.discordapp.com/attachments/1362832151485354065/1364772285873127434/blm.gif?ex=680c343d&is=680ae2bd&hm=c3ce479bfd4cd9152348f3bf1d114ce29a63c7c04ac42c7d3ad845ab6bf51eda&', None, '2025-04-03 12:05:45', 5),
    (10, 'Geomancer', 'A sorcerer using environmental/elemental attacks.', 500, 15, 20, 80, 5, 5, 99, 1, 10, 'https://cdn.discordapp.com/attachments/1362832151485354065/1372019632139145237/out.gif?ex=6825405b&is=6823eedb&hm=b0c22f7902cc76c50ce038d3c74dc16559a02e5e3d4262b5173592491bce32e6&', None, '2025-04-03 12:05:45', 5),
    (11, 'Gun Mage', 'A mage clad in blue armor who holds a magic-infused pistol.', 600, 30, 15, 60, 5, 5, 99, 1, 10, 'https://cdn.discordapp.com/attachments/1362832151485354065/1372162446311165983/out.gif?ex=6825c55c&is=682473dc&hm=1e03aac8f24a02d80ee1f48c84a204d43207a75b55259d5bb8c461bb7af6f35e&', None, '2025-04-03 12:05:45', 5),
    (12, 'Summoner', 'A mage who bonds with Eidolons and calls them to battle.', 650, 30, 25, 180, 10, 15, 99, 1, 10, None, None, '2025-07-01 05:00:00', 5),
    (13, 'Beast Master', 'A handler who tames and commands beasts in battle.', 540, 35, 15, 60, 5, 1, 99, 1, 10, None, None, '2025-09-25 00:00:00', 5),
]

# --- temporary abilities ------------------------------------------------------
MERGED_TEMPORARY_ABILITIES: List[Tuple] = [
    (1, 1, 'Pray', 'Heals you for 50% of your current HP.', '{"heal_current_pct": 0.5}', 3, 5, 'self', None, None, '2025-06-21 23:00:00'),
    (2, 2, 'Pray', 'Heals you for 50% of your current HP.', '{"heal_current_pct": 0.5}', 3, 5, 'self', None, None, '2025-06-21 23:00:00'),
    (3, 3, 'Pray', 'Heals you for 50% of your current HP.', '{"heal_current_pct": 0.5}', 3, 5, 'self', None, None, '2025-06-21 23:00:00'),
    (4, 4, 'Pray', 'Heals you for 50% of your current HP.', '{"heal_current_pct": 0.5}', 3, 5, 'self', None, None, '2025-06-21 23:00:00'),
    (5, 5, 'Pray', 'Heals you for 50% of your current HP.', '{"heal_current_pct": 0.5}', 3, 5, 'self', None, None, '2025-06-21 23:00:00'),
    (6, 6, 'Pray', 'Heals you for 50% of your current HP.', '{"heal_current_pct": 0.5}', 3, 5, 'self', None, None, '2025-06-21 23:00:00'),
    (7, 7, 'Pray', 'Heals you for 50% of your current HP.', '{"heal_current_pct": 0.5}', 3, 5, 'self', None, None, '2025-06-21 23:00:00'),
    (8, 8, 'Pray', 'Heals you for 50% of your current HP.', '{"heal_current_pct": 0.5}', 3, 5, 'self', None, None, '2025-06-21 23:00:00'),
    (9, 9, 'Pray', 'Heals you for 50% of your current HP.', '{"heal_current_pct": 0.5}', 3, 5, 'self', None, None, '2025-06-21 23:00:00'),
    (10, 10, 'Pray', 'Heals you for 50% of your current HP.', '{"heal_current_pct": 0.5}', 3, 5, 'self', None, None, '2025-06-21 23:00:00'),
    (11, 11, 'Pray', 'Heals you for 50% of your current HP.', '{"heal_current_pct": 0.5}', 3, 5, 'self', None, None, '2025-06-21 23:00:00'),
    (12, 12, 'Pray', 'Heals you for 50% of your current HP.', '{"heal_current_pct": 0.5}', 0, 1, 'self', None, None, '2025-12-21 03:38:25'),
]

# --- elements -----------------------------------------------------------------
MERGED_ELEMENTS: List[Tuple] = [
    (1, 'Fire', '2025-03-31 07:40:47'),
    (2, 'Ice', '2025-03-31 07:40:47'),
    (3, 'Holy', '2025-03-31 07:40:47'),
    (4, 'Death', '2025-03-31 07:40:47'),
    (5, 'Air', '2025-03-31 07:40:47'),
    (6, 'Lightning', '2025-06-18 02:39:35'),
    (7, 'Water', '2025-06-18 02:39:35'),
    (8, 'Earth', '2025-06-18 06:38:26'),
]

# --- element oppositions ------------------------------------------------------
MERGED_ELEMENT_OPPOSITIONS: List[Tuple[str, str]] = [
    ('Fire', 'Ice'),
    ('Ice', 'Fire'),
    ('Holy', 'Death'),
    ('Death', 'Holy'),
    ('Air', 'Earth'),
    ('Lightning', 'Water'),
    ('Water', 'Lightning'),
    ('Earth', 'Air'),
    (1, 1, 2, '2025-12-20 16:34:38'),
    (2, 2, 1, '2025-12-20 16:34:38'),
    (3, 3, 4, '2025-12-20 16:34:38'),
    (4, 4, 3, '2025-12-20 16:34:38'),
    (5, 5, 8, '2025-12-20 16:34:38'),
    (6, 6, 7, '2025-12-20 16:34:38'),
    (7, 7, 6, '2025-12-20 16:34:38'),
    (8, 8, 5, '2025-12-20 16:34:38'),
]

# --- difficulties -------------------------------------------------------------
MERGED_DIFFICULTIES: List[Tuple] = [
    (1, 'Easy', 10, 10, 2, 2, 80, 0.2, 2, 0.1, 20, 40, '2025-03-31 07:40:47', 2),
    (2, 'Medium', 10, 10, 2, 3, 80, 0.25, 3, 0.15, 20, 40, '2025-03-31 07:40:47', 2),
    (3, 'Hard', 12, 12, 2, 3, 100, 0.3, 3, 0.2, 30, 50, '2025-03-31 07:40:47', 1),
    (4, 'Crazy Catto', 12, 12, 3, 4, 125, 0.4, 3, 0.25, 40, 60, '2025-03-31 07:40:47', 1),
]

# --- intro steps --------------------------------------------------------------
MERGED_INTRO_STEPS: List[Tuple] = [
    (1, 1, 'An Unexpected Discovery', 'During what began as an ordinary raid, Sophia paused. The usual golden glow marking the entrance to familiar realms was absent, replaced instead by a strange portal shimmering with dark, translucent crystals. Curious murmurs rippled through the raid group…\n\nSophia:\n"This... isn\'t the gate we\'re used to. Has anyone seen anything like this before?"', 'https://cdn.discordapp.com/attachments/1362832151485354065/1383471362823290930/step1.png?ex=6948151c&is=6946c39c&hm=8abef3910589a84fbf6d129b79b95568a4b9b0e69a273f6807c46d02fa64f9ac&', '2025-03-31 12:40:47'),
    (2, 2, "Mog's Bold Venture", 'As the group hesitated, Mog, the courageous Moogle companion, hovered near the mysterious entrance, eyes wide with intrigue.\n\nMog:\n"Let me scout it out, Kupo! Moogles portal hop all the time! If there\'s trouble, I\'ll zip right back!"\n\nSophia:\n"Wait! Mog, we don\'t know whats on the other..."\n\nWithout another word, Mog vanished through the darkened portal.', 'https://cdn.discordapp.com/attachments/1362832151485354065/1384701702602489856/Step_2.png?ex=6947f1b4&is=6946a034&hm=635a04d626ae4c6654714c73268619948e4f91fb2902147afd9cecc445023532&', '2025-03-31 12:40:47'),
    (3, 3, 'The Moogle Returns', 'Moments felt like hours as the group waited anxiously. Suddenly, Mog burst back through, visibly shaken.\n\nMog:\n"It\'s... a labyrinth inside! Dark and scary, I almost got lost and I felt like something was watching me, kupo. We should not enter unprepared."', 'https://cdn.discordapp.com/attachments/1362832151485354065/1451086838453239898/step3.png?ex=6948312e&is=6946dfae&hm=28afe46a432dd1f782873b96a4cc8ebe7645a1b5cd86d56d17026b30e616442a&', '2025-03-31 12:40:47'),
    (4, 4, "Sophia's Decision", 'Sophia nodded solemnly, her gaze steady yet filled with resolve.\n\nSophia:\n"This discovery can\'t be ignored. Whatever lies beyond this portal demands our attention—but Mog\'s right. This will require strength, courage, and careful preparation."', 'https://cdn.discordapp.com/attachments/1362832151485354065/1451090272997085271/step4.png?ex=69483461&is=6946e2e1&hm=ee6220476fd1fe1f0effe67940daee77644f5bbf44b8cf512d1a4d03f812cd2c&', '2025-04-09 19:37:27'),
    (5, 5, 'The Call to Adventure', 'Returning to the Free Company house, Sophia gathered everyone, her voice clear and inspiring.\n\nSophia:\n"Friends, we\'ve faced many challenges, but now an unknown labyrinth awaits us. The dangers are uncertain, but the potential rewards—and truths—are greater still. Will you join me in unraveling this mystery? Our next journey begins now."\n\nYour adventure starts here...', 'https://cdn.discordapp.com/attachments/1362832151485354065/1451095742214049895/step5.png?ex=69483978&is=6946e7f8&hm=3020d69fb2e9280ba2255faa2384dabcbd86b25e9cb9956ee5a441e8f34c6ed4&', '2025-04-09 19:37:27'),
]

# --- room templates -----------------------------------------------------------
MERGED_ROOM_TEMPLATES: List[Tuple] = [
    (1, 'safe', 'Moss Room', 'You do not notice anything of importance, the area appears to be safe.', 'https://cdn.discordapp.com/attachments/1362832151485354065/1362833775637303336/roomtypemoss.png?ex=680c671c&is=680b159c&hm=3dc79f7a87ce268e9d54deae12bee18fa98b37a69caa1644257023135acfee8e&', None, '2025-03-31 12:40:47', None, None, None, None),
    (2, 'safe', 'Mystic Room', 'You do not notice anything of importance, the area appears to be safe.', 'https://cdn.discordapp.com/attachments/1362832151485354065/1362833776446673227/roomtypemystic.png?ex=680c671c&is=680b159c&hm=bc397f1f43a2317102e1f4216333b331c31dcbac9ffd8078f61c0c43171841a1&', None, '2025-03-31 12:40:47', None, None, None, None),
    (3, 'safe', 'Crystal Tunnel', 'You do not notice anything of importance, the area appears to be safe.', 'https://cdn.discordapp.com/attachments/1362832151485354065/1362833695169576981/crystals.png?ex=680c6709&is=680b1589&hm=2c0977deb61f6e286646aeddab3a54cf048c6043dbd398c15f5ebbe7a1d5e8f6&', None, '2025-03-31 12:40:47', None, None, None, None),
    (4, 'safe', 'Bridge', 'You do not notice anything of importance, the area appears to be safe.', 'https://cdn.discordapp.com/attachments/1362832151485354065/1362833699648966726/roomtypebridge.png?ex=680c670a&is=680b158a&hm=88011ac41a9c277ce6ecc855a7cb3099d9c35a0d648caa944397718741c2d5c0&', None, '2025-04-10 06:22:14', None, None, None, None),
    (5, 'safe', 'Magicite', 'You do not notice anything of importance, the area appears to be safe.', 'https://cdn.discordapp.com/attachments/1362832151485354065/1362833774844313750/roomtypemagicite.png?ex=680c671c&is=680b159c&hm=07b6f7a5c5f95e556e7adb11a013cb9d546489d7a64954d15f5c99d11acf9847&', None, '2025-04-10 06:22:19', None, None, None, None),
    (6, 'safe', 'Rainbow Crystal', 'You do not notice anything of importance, the area appears to be safe.', 'https://cdn.discordapp.com/attachments/1362832151485354065/1362833696519885081/rainbowcrystal.png?ex=680c6709&is=680b1589&hm=efecc1cf0d3a6e9f30364b1e4731697a65ab5745807ba1cb30574569cf10be16&', None, '2025-04-10 06:22:27', None, None, None, None),
    (7, 'safe', 'Aetheryte', 'You do not notice any hostile presence;\ninstead you see a naturally growing Aetheryte cluster.\n\nPerhaps this will be useful in the future...', 'https://cdn.discordapp.com/attachments/1362832151485354065/1362833698168508496/roomtypeaetheryte.png?ex=680c6709&is=680b159c&hm=29873e0d2dea2ecbd63a66c0d18825c5954f80965e19309827e18a8f77459052&', None, '2025-04-10 06:22:27', None, None, None, None),
    (8, 'monster', 'You Sense A Hostile Presence...', 'An enemy appears upon entering the area...', '', None, '2025-03-31 12:40:47', None, None, None, None),
    (9, 'staircase_up', 'Staircase Up', 'You notice a staircase leading up to the next level.', 'https://cdn.discordapp.com/attachments/1362832151485354065/1362832388677308516/stairs.png?ex=680c65d1&is=680b1451&hm=8b5d73c9b00898e7913c5d661d2f107731817084c19a8f938f7ce9ec3637340d&', None, '2025-04-19 23:55:00', None, None, None, None),
    (10, 'staircase_down', 'Staircase Down', 'You notice a staircase leading down to the next level.', 'https://cdn.discordapp.com/attachments/1362832151485354065/1365404303161950388/stairs_down_2.png?ex=680d2f59&is=680bddd9&hm=94fbe622374098bfcb2d17d0ffaaadeca5cfafa526db4273c28c02faf&', None, '2025-04-19 23:55:00', None, None, None, None),
    (11, 'exit', 'Dungeon Exit', '(Implemented in next patch)', 'https://the-demiurge.com/DemiDevUnit/images/backintro.png', None, '2025-03-31 07:40:47', None, None, None, None),
    (12, 'item', 'Treasure Room', 'You do not notice any hostile presence,\ninstead you see a treasure chest waiting to be unlocked.', 'https://cdn.discordapp.com/attachments/1362832151485354065/1362832389629284544/treasurechest.png?ex=680c65d1&is=680b1451&hm=e1971818f32f4e0b0f43cfcbf5283fc1c3f36f80b1af2bcfacbfd7ba8ecf3ace&', None, '2025-03-31 07:40:47', None, None, None, None),
    (13, 'boss', 'Boss Lair', 'A grand chamber with ominous decorations.', None, 17, '2025-03-31 07:40:47', None, None, None, None),
    (15, 'shop', 'Shop Room', 'You do not notice any hostile presence.\n\nInstead you find a Moogle hiding in the corner...', 'https://cdn.discordapp.com/attachments/1362832151485354065/1376308720144748554/Shop_Entrance.gif?ex=6834dae1&is=68338961&hm=5370f37045df11803229a217bc984ce52b910b64c59a6ede123468567b6d1991&', None, '2025-03-31 07:40:47', None, None, None, None),
    (16, 'illusion', 'Illusion Chamber', 'The room shimmers mysteriously...', 'https://cdn.discordapp.com/attachments/1362832151485354065/1362832385040711930/Illusion.png?ex=680c65d0&is=680b1450&hm=17f9b558f22f2738b576bb373eec18b161c8df67c8f2bcfff86a1ddc6d604eed&', None, '2025-03-31 07:40:47', None, None, None, None),
    (17, 'locked', 'Locked Door', 'A heavy door with a glowing symbol and what appears to be a lock. It seems you need a key.', 'https://cdn.discordapp.com/attachments/1362832151485354065/1362832387742109886/lockedroom.png?ex=680d0e91&is=680bbd11&hm=d3b19049954366cd7d625e5592a6cffbf7242aa3462ea107525c4919c371bee3&', None, '2025-04-19 23:55:00', None, None, None, None),
    (18, 'chest_unlocked', 'Unlocked Chest', 'You notice an empty chest and nothing else of importance.', 'https://cdn.discordapp.com/attachments/1362832151485354065/1365404301488291880/chestopen.png?ex=680d2f59&is=680bddd9&hm=df9e2742340f802058c078a816d17d0ffaaadeca5cfafa526db4273c28c02faf&', None, '2025-04-24 04:00:00', None, None, None, None),
    (19, 'safe', 'Lake Room', 'You do not notice anything of importance, the area appears to be safe.', 'https://cdn.discordapp.com/attachments/1362832151485354065/1362832385829244948/Lake2.png?ex=680c65d0&is=680b1450&hm=bbf00040b5390f13ae4c8eedd2ea32dc08a0510e150879ae30cfc4b6e0a13ff0&', None, '2025-04-25 17:29:10', None, None, None, None),
    (20, 'safe', 'Lake Room 2', 'You do not notice anything of importance, the area appears to be safe.', 'https://cdn.discordapp.com/attachments/1362832151485354065/1362832386416443683/Lake3.png?ex=680c65d1&is=680b1451&hm=1dc65d458458bb0e73e417850bc66973c79921757193b7d85d5849923cb3624a&', None, '2025-04-25 17:29:10', None, None, None, None),
    (21, 'miniboss', 'Mimic', "As you approach the locked chest it springs to life and bares it's fangs!", 'https://cdn.discordapp.com/attachments/1362832151485354065/1365786181417177148/2.png?ex=68113600&is=680fe480&hm=a35ce81d097c19b34c06338bb678627ec9b16061ba867cb0d72be0d84075a927&', 16, '2025-04-29 05:24:47', None, None, None, None),
    (22, 'death', 'Death', 'Your health as fallen to 0 and have fainted.', 'https://cdn.discordapp.com/attachments/1362832151485354065/1370837025665712178/output.gif?ex=6820f2f7&is=681fa177&hm=5c0ff142cc94ff7dd4050fb0be0cb1821580e251f6c5e8cb2f31384170afbd52&', None, '2025-05-09 21:59:31', None, None, None, None),
    (23, 'entrance', 'Dungeon Entrance', 'You arrive at the dungeon entrance. The air is calm, and the path ahead beckons you forward.', 'https://cdn.discordapp.com/attachments/1362832151485354065/1451193431446655107/entrance.png?ex=6947ebb3&is=69469a33&hm=83309aec93d17392e9025d9e1927254b7bddb594fe3a7d24168e4dc0963638a3&', None, '2025-06-23 17:00:00', None, None, None, None),
    (24, 'cloister', 'Cloister of Flames', 'You sense a great power in this cloister. A crimson Aetheryte crystal hums softly at its center.', 'https://cdn.discordapp.com/attachments/1362832151485354065/1451958079330713773/5ff3c362-8b62-4b7c-9202-ceb4bf75ade3.png?ex=694810d6&is=6946bf56&hm=96ccb56188e13de07f19215e22fc2e79168cbe67cbd28350b13476498587102e&', None, '2025-07-01 05:00:00', None, None, 1, 5),
    (25, 'cloister', 'Cloister of Frost', 'You sense a great power in this cloister. A pale Aetheryte crystal floats, cold mist curling from it.', 'https://cdn.discordapp.com/attachments/1362832151485354065/1451958423640998113/c49919eb-242f-44d3-a266-225a6e5c679c.png?ex=69481128&is=6946bfa8&hm=7dc2e3d176f318651b25292cf9a74fad0aca9f957de9a794876fe746cac999ee&', None, '2025-07-01 05:00:00', None, None, 2, 8),
    (26, 'cloister', 'Cloister of Storms', 'You sense a great power in this cloister. A crackling Aetheryte crystal pulses with thunder.', 'https://cdn.discordapp.com/attachments/1362832151485354065/1451958653082009771/14d77bc2-a1ab-49e7-bdf8-f02a5d9a3d7e.png?ex=6948115e&is=6946bfde&hm=c125b318a8b92f9dfc4faf6331c67f609b1a6c231e4044c73421dcfe3a9573c7&', None, '2025-07-01 05:00:00', None, None, 3, 12),
    (27, 'cloister', 'Cloister of Extremes', 'You Sense a great power in this cloister. A purple glow and feline prints are visible in the Aetheryte.', 'https://cdn.discordapp.com/attachments/1362832151485354065/1452150771188498556/cc7461ba-af40-4edd-8af6-461a3e4daaa0.png?ex=6948c44b&is=694772cb&hm=8b0c5aa48528be057452285ee044e36ddce76a44bbda75e5b8439da9e117a979&', None, '2025-12-21 04:44:10', None, None, 4, 15),
]

# --- items --------------------------------------------------------------------
MERGED_ITEMS: List[Tuple] = [
    (1, 'Potion', 'Heals 50 HP.', '{"heal": 50}', 'consumable', 1, 100, 10, 'self', 'https://example.com/icons/potion.png', None, '2025-03-31 07:40:47'),
    (2, 'Ether', 'Restores 30 MP.', '{"restore_mp": 30}', 'consumable', 1, 150, 5, 'self', 'https://example.com/icons/ether.png', None, '2025-03-31 07:40:47'),
    (3, 'Phoenix Down', 'Revives a fainted ally with 100 HP.', '{"heal": 100, "revive": true}', 'consumable', 1, 500, 2, 'ally', 'https://example.com/icons/phoenix_down.png', None, '2025-03-31 07:40:47'),
    (4, 'Tent', 'Restores all HP and enables Trance for a short time.', '{"heal": 999, "trance": true}', 'consumable', 1, 1200, 1, 'self', None, None, '2025-04-17 08:38:51'),
    (5, 'Hi-Potion', 'Heals 150 HP.', '{"heal": 150}', 'consumable', 1, 250, 3, 'self', None, None, '2025-04-17 08:38:51'),
    (6, 'Grenade', 'Deals explosive damage.', '{"attack": 120}', 'consumable', 1, 250, 2, 'enemy', None, None, '2025-04-17 08:40:23'),
    (7, 'Old Key', 'An old looking key.', None, 'quest', 1, 0, None, 'self', None, None, '2025-04-26 05:09:35'),
    (8, 'Auto-Life Magicite', 'A Glowing Sphere containing Life magics.', '{"revive": true}', 'quest', 1, 0, None, 'self', None, None, '2025-05-09 23:59:15'),
    (9, 'Antidote', 'Removes Poisoned Status', None, 'consumable', 1, 0, None, 'any', '🧪', None, '2025-05-23 06:45:00'),
]

# --- enemies ------------------------------------------------------------------
MERGED_ENEMIES: List[Tuple] = [
    (1, 'Behemoth', 'normal', 'large, purple, canine-esque creature...', 100, 100, 15, 10, 10, 5, 99, 1, 'Easy', None, 'https://cdn.discordapp.com/attachments/1362832151485354065/1362833225860382731/behemoth.png?ex=680db819&is=680c6699&hm=f09b8b78e76629b607f0aec017f5aef75c003a1965508701c7b7de48b5279dd7&', 0.3, 100, 75, 1, 1, None, '2025-03-31 12:40:47', 5, 11, 100, 100),
    (2, 'Ghost', 'normal', 'pale, translucent, or wispy being...', 50, 50, 10, 10, 10, 5, 99, 1, 'Easy', None, 'https://cdn.discordapp.com/attachments/1362832151485354065/1362833226606973221/ghost.png?ex=680db819&is=680c6699&hm=6e400e0649442964e4ac24e7dc2b0a6fd351f4557c611e85cce5ecf4d6a1e658&', 0.3, 50, 50, 3, 1, None, '2025-03-31 12:40:47', 5, 11, 100, 100),
    (3, 'Drake', 'normal', 'An ancient creature with scales and fangs, said to be extinct for over 1,000 years.', 200, 200, 15, 10, 10, 10, 99, 1, 'Easy', None, 'https://cdn.discordapp.com/attachments/1362832151485354065/1375114639914045480/drake.png?ex=683082ce&is=682f314e&hm=92fdeabf72b3026f912674b0faa2f98bf993aea384119831b63492d607c84d3e&', 0.1, 150, 150, 1, 1, None, '2025-03-31 12:40:47', 5, 11, 100, 100),
    (4, 'Larva', 'normal', 'A glowing entity capable of casting higher magics.', 300, 300, 12, 10, 15, 12, 99, 1, 'Hard', None, 'https://cdn.discordapp.com/attachments/1362832151485354065/1375114662240325712/larva.png?ex=683082d3&is=682f3153&hm=9d8c16343ea85757895cbd6578e0f67d8e9aa474a7ee0ca0e812ca13b820f719&', 0.2, 200, 200, 5, 1, None, '2025-03-31 12:40:47', 5, 11, 100, 100),
    (5, 'Black Flan', 'normal', 'A Gelatinous creature resistant to physical attacks.', 200, 200, 11, 15, 11, 5, 99, 1, 'Medium', None, 'https://cdn.discordapp.com/attachments/1362832151485354065/1362835170721534023/blackflan.png?ex=6803d6a8&is=68028528&hm=ee330fb7a2269de429cf44562580eb3646beff4a8de4cc2a6bc73ae4cdd930ba&', 0.2, 200, 250, 1, 1, None, '2025-03-31 12:40:47', 5, 11, 100, 100),
    (6, 'Nightmare', 'normal', 'You feel a sudden wave of fear as the dark shrouded creature approaches...', 125, 125, 20, 10, 10, 5, 99, 1, 'Easy', None, 'https://cdn.discordapp.com/attachments/1362832151485354065/1362835169949646998/nightmare_elemental.png?ex=680db9e8&is=680c6868&hm=66d12f806890019bad61635b0f304bc9c7acbb56128c279c515543e9066e8811&', 0.1, 125, 150, 3, 1, None, '2025-04-10 06:20:32', 5, 11, 100, 100),
    (7, 'Tonberry Chef', 'normal', "A creature said to be only in legend. It seems to like cooking, but where did it get that knife and chef's hat? Also VERY big.", 250, 250, 20, 10, 10, 6, 99, 1, 'Easy', None, 'https://cdn.discordapp.com/attachments/1362832151485354065/1362833225033977996/tonberry_chef.png?ex=680db819&is=680c6699&hm=f8769254ee0417a70fb677d9e885764572d3673c194953cb7acc617d54c66df9&', 0.1, 150, 110, 1, 1, None, '2025-04-10 06:20:32', 5, 11, 100, 100),
    (8, 'Overgrown Tonberry', 'normal', 'A creature said to be only in legend. Also VERY big.', 200, 200, 10, 10, 10, 5, 99, 1, 'Easy', None, 'https://cdn.discordapp.com/attachments/1362832151485354065/1362833224136524030/overgrown_tonberry.png?ex=680db818&is=680c6698&hm=0304508b1d30e458dc4b931d10a0808d57570119961a142934061f226bcc0d1c&', 0.3, 75, 90, 1, 1, None, '2025-03-31 12:40:47', 5, 11, 100, 100),
    (9, 'Black Flan', 'normal', 'A Gelatinous creature resistant to physical attacks.', 160, 160, 15, 15, 12, 2, 99, 1, 'Easy', None, 'https://cdn.discordapp.com/attachments/1362832151485354065/1362835170721534023/blackflan.png?ex=6803d6a8&is=68028528&hm=ee330fb7a2269de429cf44562580eb3646beff4a8de4cc2a6bc73ae4cdd930ba&', 0.5, 80, 80, 1, 1, None, '2025-04-17 08:03:02', 5, 11, 100, 100),
    (10, 'Bomb', 'normal', "A ball of everlasting embers growing hotter as the enemy enrages. Watch out for it's self-destruct.", 125, 125, 12, 10, 12, 5, 99, 1, 'Easy', None, 'https://cdn.discordapp.com/attachments/1362832151485354065/1362835171476377720/bombenemy.png?ex=6803d6a9&is=68028529&hm=0b67669b87b609a9e767920525d23dc9d224d1fedcb245154ada75b961905d6e&', 0.5, 80, 80, 1, 1, None, '2025-04-17 08:03:02', 5, 11, 100, 100),
    (11, 'Chimera', 'normal', "A beast taking on three forms, each having it's own abilities.", 200, 200, 20, 11, 13, 10, 99, 1, 'Hard', None, 'https://cdn.discordapp.com/attachments/1362832151485354065/1362835172298592508/chimera.png?ex=6803d6a9&is=68028529&hm=c207c28cc8df7b77ee82552ce183d27c2161576dcaff80cf08cdae7a98e95df6&', 0.5, 120, 150, 3, 1, None, '2025-04-17 08:03:02', 5, 11, 100, 100),
    (12, 'Clay Golem', 'normal', "A large being said to exist as the result of a sorcerer's curse. Legend states they are the last remnants of a large mining caravan.", 125, 125, 15, 10, 11, 5, 99, 1, 'Easy', None, 'https://cdn.discordapp.com/attachments/1362832151485354065/1362835173539840062/claygolem.png?ex=6803d6a9&is=68028529&hm=258bf6843e232975707bbc8f1a65581f217007fb6154954cc3774454ee06018e&', 0.5, 100, 120, 1, 1, None, '2025-04-17 08:03:02', 5, 11, 100, 100),
    (13, 'Ghast', 'normal', 'A large fiend with deformed limbs and humanoid features, it seems to be branded with a symbol of sorts.', 150, 150, 18, 12, 11, 6, 99, 1, 'Easy', None, 'https://cdn.discordapp.com/attachments/1362832151485354065/1362835175716683907/ghast.png?ex=6803d6aa&is=6802852a&hm=711d53e92c6df922e46e0f090427db41faad6cd07aecd22e5604dfc1ab53af5f&', 0.5, 175, 150, 3, 1, None, '2025-04-17 08:03:02', 5, 11, 100, 100),
    (14, 'Iron Giant', 'normal', 'A giant knight clad in Iron armor. It is known for having high defense.', 275, 275, 25, 20, 12, 5, 99, 1, 'Medium', None, 'https://cdn.discordapp.com/attachments/1362832151485354065/1362835176635240458/irongiant.png?ex=6803d6aa&is=6802852a&hm=66b16d26c72317c93fcaf313b1f8dc3cdbf127853d77dec2ce3e60160eaebaac&', 0.5, 200, 300, 1, 1, None, '2025-04-17 08:03:02', 5, 11, 100, 100),
    (15, 'Marlboro', 'normal', 'A smelly creature with large sharp teeth, long vine-like tentacles, and multiple eyes.', 175, 175, 17, 12, 12, 5, 99, 1, 'Easy', None, 'https://cdn.discordapp.com/attachments/1362832151485354065/1362835177486680437/marlboro.png?ex=6803d6aa&is=6802852a&hm=1c750b1405bda87627ad13f8d16b3f717c1f0298afdac7a3d2387bac69724363&', 0.5, 150, 150, 1, 1, None, '2025-04-17 08:03:02', 5, 11, 100, 100),
    (16, 'Mimic', 'miniboss', 'A small chest bearing fangs and teeth.', 500, 500, 20, 20, 15, 10, 99, 1, 'Easy', None, 'https://cdn.discordapp.com/attachments/1362832151485354065/1365786181417177148/2.png?ex=680f3bc0&is=680dea40&hm=cfad9ebbb97d24ec72185a1f248403001fcb9fbc6e8f3f8d463fc971d5c20bb8&', 0.2, 500, 2000, 6, 1, None, '2025-04-26 20:26:50', 5, 11, 100, 100),
    (17, 'Lightning Elemental', 'boss', 'You hear static crackle in the air...', 500, 500, 20, 20, 20, 20, 99, 1, 'Easy', None, 'https://cdn.discordapp.com/attachments/1362832151485354065/1366755651786637312/lightning_elemental.png?ex=681219e4&is=6810c864&hm=8c9364bff4b0760c66ac1b1d516666b830d550c9bc75a82b85d829d1c0aa7aa1&', 0.2, 500, 3000, 8, 1, None, '2025-04-26 20:26:50', 5, 11, 100, 100),
    (18, 'Agares', 'normal', 'A goblin creature that appears to use magic and is dressed in unfamiliar garb.', 200, 200, 10, 10, 12, 6, 99, 1, 'Easy', None, 'https://cdn.discordapp.com/attachments/1362832151485354065/1375114561799192766/Agares.png?ex=683082bb&is=682f313b&hm=bcec9bdaf61b08d27897db07918df65d15cd8d25ead882e0cd4d792b9376a99d&', 0.1, 200, 175, 5, 1, None, '2025-05-22 19:42:26', 5, 11, 100, 100),
    (19, 'Cactuar', 'normal', "An evasive cactus species that is known to attack and run, watch our for it's Needles!", 200, 200, 15, 12, 10, 7, 99, 2, 'Easy', None, 'https://cdn.discordapp.com/attachments/1362832151485354065/1375114595626389514/Cactuar.png?ex=683082c3&is=682f3143&hm=6dc61cc626160c8ed9d1619142eb319365330b98641bd2e9db5359c4fef1c373&', 0.1, 150, 150, 1, 1, None, '2025-05-22 19:42:26', 5, 11, 100, 100),
    (20, 'Demon Eye', 'normal', 'A floating creature with one eye and bat like wings.', 220, 220, 13, 10, 13, 6, 99, 1, 'Easy', None, 'https://cdn.discordapp.com/attachments/1362832151485354065/1375114610457313414/demoneyeball.png?ex=683082c7&is=682f3147&hm=e2512d5ab06077b428c84552b2d9ce68c3c2c58d010a4744c3ea9819b2b1174a&', 0.1, 110, 150, 1, 1, None, '2025-05-22 19:42:26', 5, 11, 100, 100),
    (21, 'Demon Eye', 'normal', 'A floating creature with one eye and bat like wings.', 220, 220, 13, 10, 13, 6, 99, 1, 'Medium', None, 'https://cdn.discordapp.com/attachments/1362832151485354065/1375114610457313414/demoneyeball.png?ex=683082c7&is=682f3147&hm=e2512d5ab06077b428c84552b2d9ce68c3c2c58d010a4744c3ea9819b2b1174a&', 0.1, 110, 150, 1, 1, None, '2025-05-22 19:42:26', 5, 11, 100, 100),
    (22, 'Larva', 'normal', 'A glowing entity capable of casting higher magics.', 250, 250, 10, 10, 12, 6, 99, 1, 'Easy', None, 'https://cdn.discordapp.com/attachments/1362832151485354065/1375114662240325712/larva.png?ex=683082d3&is=682f3153&hm=9d8c16343ea85757895cbd6578e0f67d8e9aa474a7ee0ca0e812ca13b820f719&', 0.1, 200, 180, 5, 1, None, '2025-05-22 19:42:26', 5, 11, 100, 100),
    (23, 'Black Waltz', 'miniboss', 'A mage resembling those from stories of the Dark Era of Alexandria. Where did it come from? What or who could it be searching for?', 600, 600, 10, 10, 13, 12, 99, 1, 'Easy', None, 'https://cdn.discordapp.com/attachments/1362832151485354065/1375114690589364266/blackwaltz.png?ex=683082da&is=682f315a&hm=dd33c631faee48b90bedb3c64c62b15b1b5dc339324507287cf396b0eb08f724&', 0.1, 500, 2200, 4, 1, None, '2025-05-22 19:42:26', 5, 11, 100, 100),
    (24, 'Black Waltz', 'miniboss', 'A mage resembling those from stories of the Dark Era of Alexandria. Where did it come from? What or who could it be searching for?', 800, 800, 11, 11, 14, 13, 99, 1, 'Medium', None, 'https://cdn.discordapp.com/attachments/1362832151485354065/1375114690589364266/blackwaltz.png?ex=683082da&is=682f315a&hm=dd33c631faee48b90bedb3c64c62b15b1b5dc339324507287cf396b0eb08f724&', 0.1, 500, 2200, 4, 1, None, '2025-05-22 19:42:26', 5, 11, 100, 100),
    (25, 'Drake', 'normal', 'An ancient creature with scales and fangs, said to be extinct for over 1,000 years.', 300, 300, 15, 10, 10, 10, 99, 1, 'Medium', None, 'https://cdn.discordapp.com/attachments/1362832151485354065/1375114639914045480/drake.png?ex=683082ce&is=682f314e&hm=92fdeabf72b3026f912674b0faa2f98bf993aea384119831b63492d607c84d3e&', 0.1, 150, 150, 5, 1, None, '2025-03-31 12:40:47', 5, 11, 100, 100),
    (26, 'Cactuar', 'normal', "An evasive cactus species that is known to attack and run, watch our for it's Needles!", 300, 300, 15, 13, 11, 8, 99, 1, 'Medium', None, 'https://cdn.discordapp.com/attachments/1362832151485354065/1375114595626389514/Cactuar.png?ex=683082c3&is=682f3143&hm=6dc61cc626160c8ed9d1619142eb319365330b98641bd2e9db5359c4fef1c373&', 0.1, 220, 200, 5, 1, None, '2025-05-22 19:44:44', 5, 11, 100, 100),
    (101, 'Ifrit', 'eidolon', 'A blazing Eidolon wreathed in infernal flames.', 750, 750, 25, 18, 20, 20, 99, 5, 'Summoner', None, 'https://cdn.discordapp.com/attachments/1362832151485354065/1451937077259272273/730fb195-cea1-4183-8ef4-f2677b1eb88e.png?ex=6947fd46&is=6946abc6&hm=bd42838fc0ee3081d00e2ec5567833f34716270c3c9e332c54c1ad00e237b190&', 0, 500, 800, None, 1, None, '2025-07-01 05:00:00', 6, 11, 100, 100),
    (102, 'Shiva', 'eidolon', 'A frigid Eidolon whose breath freezes the air.', 750, 750, 22, 18, 20, 22, 99, 6, 'Summoner', None, 'https://cdn.discordapp.com/attachments/1362832151485354065/1451938841089802391/e0b5b388-de0f-4a0e-a34d-adbae339711d.png?ex=6947feeb&is=6946ad6b&hm=4be5a3a201950ce527ebbdbbed9f6745cbc45ef515b2ca59a0252d693124921c&', 0, 600, 900, None, 1, None, '2025-07-01 05:00:00', 6, 11, 100, 100),
    (103, 'Ramuh', 'eidolon', 'A stormbound Eidolon crackling with lightning.', 800, 800, 24, 20, 20, 24, 99, 6, 'Summoner', None, 'https://cdn.discordapp.com/attachments/1362832151485354065/1451943284728664064/d9544aeb-1d50-4766-b2fa-7dc21a8b4aaf.png?ex=6948030e&is=6946b18e&hm=551008eb7439d8ea3a128d0e42394029bdadd82f4c90b3ea514286185ea67bbd&', 0, 700, 1000, None, 1, None, '2025-07-01 05:00:00', 6, 11, 100, 100),
    (104, 'Fat Cat', 'eidolon', 'A Large Feline Entity', 1000, 1000, 24, 10, 20, 10, 99, 5, 'Summoner', None, 'https://cdn.discordapp.com/attachments/1362832151485354065/1452150793049473065/710428d4-9cd5-462a-95db-8f3ebe0a9009.png?ex=6948c450&is=694772d0&hm=13a515e6e679f0f8cdef72a23bb1fbc3b03c9e57f7f2c6f4acf6de37687a8964&', 0, 1000, 1000, 8, 1, None, '2025-12-21 04:38:51', 5, 11, 100, 100),
]

# --- beast templates ----------------------------------------------------------
MERGED_BEAST_TEMPLATES: List[Tuple] = [
    (1, 1, 'Behemoth', 'large, purple, canine-esque creature...', 100, 0, 15, 10, 10, 5, 99, 1, 10, 'https://cdn.discordapp.com/attachments/1362832151485354065/1362833225860382731/behemoth.png?ex=680db819&is=680c6699&hm=f09b8b78e76629b607f0aec017f5aef75c003a1965508701c7b7de48b5279dd7&', '2025-09-25 00:00:00'),
    (2, 3, 'Drake', 'An ancient creature with scales and fangs, said to be extinct for over 1,000 years.', 200, 0, 15, 10, 10, 10, 99, 1, 10, 'https://cdn.discordapp.com/attachments/1362832151485354065/1375114639914045480/drake.png?ex=683082ce&is=682f314e&hm=92fdeabf72b3026f912674b0faa2f98bf993aea384119831b63492d607c84d3e&', '2025-09-25 00:00:00'),
    (3, 11, 'Chimera', "A beast taking on three forms, each having it's own abilities.", 200, 0, 20, 13, 11, 10, 99, 1, 10, 'https://cdn.discordapp.com/attachments/1362832151485354065/1362835172298592508/chimera.png?ex=6803d6a9&is=68028529&hm=c207c28cc8df7b77ee82552ce183d27c2161576dcaff80cf08cdae7a98e95df6&', '2025-09-25 00:00:00'),
    (4, 15, 'Marlboro', 'A smelly creature with large sharp teeth, long vine-like tentacles, and multiple eyes.', 175, 0, 17, 12, 12, 5, 99, 1, 10, 'https://cdn.discordapp.com/attachments/1362832151485354065/1362835177486680437/marlboro.png?ex=6803d6aa&is=6802852a&hm=1c750b1405bda87627ad13f8d16b3f717c1f0298afdac7a3d2387bac69724363&', '2025-09-25 00:00:00'),
    (5, 19, 'Cactuar', "An evasive cactus species that is known to attack and run, watch our for it's Needles!", 200, 0, 15, 10, 12, 7, 99, 2, 10, 'https://cdn.discordapp.com/attachments/1362832151485354065/1375114595626389514/Cactuar.png?ex=683082c3&is=682f3143&hm=6dc61cc626160c8ed9d1619142eb319365330b98641bd2e9db5359c4fef1c373&', '2025-09-25 00:00:00')
]

# --- enemy ↔ ability links ----------------------------------------------------
MERGED_ENEMY_ABILITIES: List[Tuple] = [
    (1, 2, 1, 0, None, None, 'attack_power', 1, 100),
    (1, 7, 1, 0, None, None, 'attack_power', 1, 100),
    (2, 2, 1, 0, None, None, 'attack_power', 1, 100),
    (2, 7, 1, 0, None, None, 'attack_power', 1, 100),
    (2, 9, 1, 0, None, None, 'attack_power', 1, 100),
    (3, 15, 0, 0, None, None, 'attack_power', 1, 100),
    (3, 35, 0, 0, None, None, 'attack_power', 1, 100),
    (4, 17, 0, 0, None, None, 'magic_power', 1, 100),
    (4, 19, 0, 0, None, None, 'magic_power', 1, 100),
    (4, 21, 0, 0, None, None, 'magic_power', 1, 100),
    (5, 10, 1, 0, None, None, 'attack_power', 1, 100),
    (5, 12, 1, 0, None, None, 'attack_power', 1, 100),
    (6, 12, 3, 0, None, None, 'magic_power', 1, 100),
    (6, 21, 1, 0, None, None, 'magic_power', 1, 100),
    (7, 17, 3, 0, None, None, 'magic_power', 1, 100),
    (7, 91, 1, 0, None, None, 'attack_power', 1, 100),
    (8, 2, 3, 0, None, None, 'magic_power', 1, 100),
    (8, 91, 1, 0, None, None, 'attack_power', 1, 100),
    (9, 17, 1, 0, None, None, 'magic_power', 1, 100),
    (9, 19, 1, 0, None, None, 'magic_power', 1, 100),
    (10, 2, 1, 0, None, None, 'magic_power', 1, 100),
    (11, 17, 2, 0, None, None, 'magic_power', 1, 100),
    (11, 19, 2, 0, None, None, 'magic_power', 1, 100),
    (11, 21, 2, 0, None, None, 'magic_power', 1, 100),
    (11, 23, 1, 0, None, None, 'magic_power', 1, 100),
    (12, 1, 1, 1, 0.15, 0.15, 'magic_power', 1, 100),
    (13, 16, 1, 0, None, None, 'attack_power', 1, 100),
    (13, 31, 1, 0, None, None, 'magic_power', 1, 100),
    (14, 1, 1, 1, 0.25, 0.15, 'magic_power', 1, 100),
    (14, 14, 1, 0, None, None, 'attack_power', 1, 100),
    (15, 36, 1, 0, None, None, 'attack_power', 1, 100),
    (16, 2, 1, 0, None, None, 'magic_power', 1, 100),
    (16, 3, 1, 0, None, None, 'magic_power', 1, 100),
    (16, 12, 1, 0, None, None, 'magic_power', 1, 100),
    (17, 21, 3, 0, None, None, 'magic_power', 1, 100),
    (17, 22, 1, 0, None, None, 'magic_power', 1, 100),
    (18, 2, 0, 0, None, None, 'magic_power', 1, 100),
    (18, 3, 0, 0, None, None, 'magic_power', 1, 100),
    (18, 12, 0, 0, None, None, 'magic_power', 1, 100),
    (19, 92, 0, 0, None, None, 'attack_power', 0, 100),
    (20, 2, 0, 0, None, None, 'magic_power', 1, 100),
    (20, 35, 0, 0, None, None, 'magic_power', 1, 100),
    (21, 17, 0, 0, None, None, 'magic_power', 1, 100),
    (21, 30, 0, 0, None, None, 'magic_power', 1, 100),
    (21, 36, 0, 0, None, None, 'magic_power', 1, 100),
    (22, 1, 0, 1, 0.2, 0.15, 'magic_power', 1, 100),
    (22, 2, 0, 0, None, None, 'magic_power', 1, 100),
    (22, 3, 0, 0, None, None, 'magic_power', 1, 100),
    (22, 12, 0, 0, None, None, 'magic_power', 1, 100),
    (23, 4, 0, 0, None, None, 'magic_power', 1, 100),
    (23, 17, 0, 0, None, None, 'magic_power', 1, 100),
    (23, 19, 0, 0, None, None, 'magic_power', 1, 100),
    (23, 21, 0, 0, None, None, 'magic_power', 1, 100),
    (23, 26, 0, 1, 0.2, 0.5, 'magic_power', 1, 100),
    (24, 17, 0, 0, None, None, 'magic_power', 1, 100),
    (24, 19, 0, 0, None, None, 'magic_power', 1, 100),
    (24, 21, 0, 0, None, None, 'magic_power', 1, 100),
    (24, 24, 0, 0, None, None, 'magic_power', 1, 100),
    (24, 26, 0, 1, 0.3, 0.5, 'magic_power', 1, 100),
    (25, 15, 0, 0, None, None, 'attack_power', 1, 100),
    (25, 36, 0, 0, None, None, 'attack_power', 1, 100),
    (26, 7, 0, 0, None, None, 'attack_power', 1, 100),
    (26, 30, 0, 0, None, None, 'magic_power', 1, 100),
    (26, 93, 0, 0, None, None, 'attack_power', 1, 100)
]

# --- eidolons -----------------------------------------------------------------
MERGED_EIDOLONS: List[Tuple] = [
    (1, 'Ifrit', 'A fiery Eidolon bound to the Cloister of Flames.', 101, 5, 1500, 80, 100, 50, 20, 99, 99, 5, 50, '2025-07-01 05:00:00'),
    (2, 'Shiva', 'A crystalline Eidolon bound to the Cloister of Frost.', 102, 8, 1500, 80, 100, 50, 22, 99, 99, 6, 50, '2025-07-01 05:00:00'),
    (3, 'Ramuh', 'A stormy Eidolon bound to the Cloister of Storms.', 103, 12, 1500, 80, 100, 50, 24, 99, 99, 6, 50, '2025-07-01 05:00:00'),
    (4, 'Fat Cat', 'A feline Eidolon bound to the Cloister of the Extreme.', 104, 15, 1500, 100, 100, 50, 24, 99, 99, 10, 75, '2025-12-21 04:40:13'),
]

# --- eidolon ↔ ability links --------------------------------------------------
MERGED_EIDOLON_ABILITIES: List[Tuple] = [
    (1, 201, 1),
    (2, 202, 1),
    (3, 203, 1),
]

# --- enemy drops --------------------------------------------------------------
MERGED_ENEMY_DROPS: List[Tuple] = [
    (1, 1, 0.5, 1, 1),
    (2, 3, 0.25, 1, 1),
    (4, 1, 0.25, 1, 1),
    (3, 1, 0.25, 1, 1),
    (5, 2, 0.25, 1, 1),
    (6, 1, 0.25, 1, 1),
    (7, 2, 0.25, 1, 1),
    (9, 2, 0.25, 1, 1),
    (11, 2, 0.25, 1, 1),
    (14, 5, 0.25, 1, 1),
    (16, 5, 0.25, 1, 1),
    (18, 1, 0.25, 1, 1),
    (22, 2, 0.25, 1, 1),
    (23, 5, 0.25, 1, 1),
    (101, 9, 0.25, 1, 1),
    (102, 9, 0.25, 1, 1),
    (103, 9, 0.25, 1, 1),
]

# --- enemy resistances --------------------------------------------------------
MERGED_ENEMY_RESISTANCES: List[Tuple] = [
    (4, 1, 0, 'weak', 1.5),
    (5, 3, 0, 'weak', 1.5),
    (10, 2, 0, 'weak', 1.5),
    (10, 2, 0, 'weak', 1.5),
    (12, 1, 0, 'weak', 1.5),
    (13, 6, 0, 'weak', 1.5),
    (15, 1, 0, 'weak', 1.5),
    (19, 7, 0, 'weak', 1.5),
    (19, 7, 0, 'weak', 1.5),
    (101, 2, 0, 'weak', 1.5),
    (102, 2, 100, 'absorb', -1),
    (103, 8, 0, 'weak', 1.5),
]

# --- levels -------------------------------------------------------------------
MERGED_LEVELS: List[Tuple] = [
    (1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, None, '2025-04-08 20:00:00'),
    (2, 150, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, None, '2025-04-08 20:00:00'),
    (3, 200, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, None, '2025-04-08 20:00:00'),
    (4, 250, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, None, '2025-04-09 20:15:49'),
    (5, 300, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, None, '2025-04-09 20:15:49'),
    (6, 350, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, None, '2025-04-09 20:15:49'),
    (7, 500, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, None, '2025-04-17 08:25:24'),
    (8, 600, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, None, '2025-04-17 08:25:24'),
    (9, 700, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, None, '2025-04-17 08:25:24'),
    (10, 900, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, None, '2025-04-17 08:25:24'),
    (11, 1000, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, None, '2025-04-17 08:25:24'),
    (12, 1100, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, None, '2025-04-17 08:25:24'),
    (13, 1200, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, None, '2025-04-17 08:25:24'),
    (14, 1300, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, None, '2025-04-17 08:25:24'),
    (15, 1400, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, None, '2025-04-17 08:25:24'),
    (16, 1500, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, None, '2025-04-17 08:25:24'),
    (17, 1600, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, None, '2025-04-17 08:25:24'),
    (18, 1700, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, None, '2025-04-17 08:25:24'),
    (19, 1800, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, None, '2025-04-17 08:25:24'),
    (20, 2000, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, None, '2025-04-17 08:25:24'),
]

# --- vendors + items ----------------------------------------------------------
MERGED_NPC_VENDORS: List[Tuple] = [
    (1, 'Stiltzkin', '__**Stiltzkin:**__\n\n**"Oh hello, I’m glad to see you are not a monster, kupo! I’m a traveling merchant, see.. I was portal hopping and suddenly came across a black portal I’d never seen before..."**\n\nStiltzkin looks at you as if he’s trying to recall something. **"Have we met before, kupo? You seem familiar."**\n\n**"At any rate, if you’d like to buy or sell something the shop is still open."**', None, 'https://cdn.discordapp.com/attachments/1362832151485354065/1362946279587713074/stiltzkin.gif?ex=68345ce3&is=68330b63&hm=b99988391998062f540188581a94327b15919d6d620bf7fe8dae6a953e29ba24&', '2025-03-24 22:37:28'),
    (2, 'Artemecion', '__**Artemecion:**__\n\n"Hey you aren\'t a monster, Kupo! Do you need a **Letter** delivered by chance? \n\nNo? Hmph, well I also sell a few wares I find along my journey, kupo."\n\n*Artemecion pauses for a moment, it looks as though he\'s trying to recall something...*\n\n"Sorry... your face reminds me of **someone I haven\'t seen in a long time**, kupo. I was lost in a good memory for a moment. \n\nFeel free to browse, but my dyes are off limits, kupo!"', None, 'https://cdn.discordapp.com/attachments/1362832151485354065/1376308818199445604/Artemecion.gif?ex=6834daf8&is=68338978&hm=16ecf8b4fff715e695e67f6c647a7dc918bf8cfb0486ac383cb337e22f380efd&', '2025-05-26 02:31:53'),
]

MERGED_NPC_VENDOR_ITEMS: List[Tuple] = [
    (1, 1, 50, 3, 2),
    (1, 3, 100, 3, 1),
    (1, 4, 500, 3, 3),
    (2, 4, 500, 3, 3),
    (2, 5, 500, 10, 10),
    (2, 9, 150, 3, 3),
]

# --- hub embeds/buttons -------------------------------------------------------
MERGED_HUB_EMBEDS: List[Tuple] = [
    (1, 'main', None, "***Step into an unexplored reality and find meaning and hidden truth behind it's existence.\n\nAssemble your party and compete with other players, or enter alone. \n\nChoose your class + difficulty level, and experience turn-based combat that challenges your strategy at every turn.***", 'https://cdn.discordapp.com/attachments/1362832151485354065/1451415058839113828/Hub.png?ex=6948115c&is=6946bfdc&hm=c48e9474e8deca66081e667a39ac8a9b1d53b2c953bf79b3c36ba0f991137684&', '**AdventureBot v3.0.9 is now Live!**\n\nJoin the Demi Dev Unity discord server for the latest patch notes.\n\n———————————————————————————\n:purple_square:**Beta Testers**:purple_square:\n\nPatch 3.1 features have been partially implemented for testing.\n\nPlease report any bugs and issues to the Demi Dev Unit discord.', None, '2025-03-31 13:43:19'),
    (2, 'tutorial', 'Starting A Game', 'Simply click the **New Game** button to create a new game thread.\n\nThis will add you to the **Queue** system inside the thread, along with anyone else who wants to join.\n\n- Only the players who join the game session will see the private thread and be added to it automatically.\n\n- Up to 6 players can join via the LFG post in the Game Channel by clicking the Join button. \n\n- Additional players will be shown in the **Queue List** in the thread.\n\nWhen the creator is ready they may click **Start Game** to lock in the emount of players playing.', 'https://cdn.discordapp.com/attachments/1362832151485354065/1373622234865733652/Screenshot_2025-05-18_at_6.14.47_AM.png?ex=682b14e5&is=6829c365&hm=b91a3c24ed88f1f493db9a8f61473923e316e284782ab15bd565f6a82ac25966&', 'Coming Soon...', 1, '2025-04-15 07:50:10'),
    (3, 'tutorial', 'Choose Class and Difficulty', "Once the Session Creator clicks the Start Game button they can choose their class and difficulty level.\n\n- Selecting **Easy** will generate up to 2 floors with a rare chance to spawn a basement floor. In this mode most harder enemeis are removed from generation.\n\n- Choosing **Medium** difficulty will generate up to 4 floors with at least 2 and a rare chance to spawn a basement. In this mode harder enemies spawn along side easy ones during generation.\n\n- Selecting **Hard** is exactly what you think it is. With up to 4 floors and higher spawn chances on more difficult enemies and less vendor shops and item drops.\n\n- **Crazy Catto** is the most difficult of challenges and well... you'd be a crazy catto to try it.", 'https://cdn.discordapp.com/attachments/1362832151485354065/1373622403455778848/Screenshot_2025-05-18_at_6.19.11_AM.png?ex=682b150d&is=6829c38d&hm=045419693ca1ecd758f7ecf5c7208ca4da321622636b908da9e15c99f97dde61&', 'Coming Soon...', 2, '2025-04-17 08:45:05'),
]
MERGED_HUB_BUTTONS: List[Tuple] = []

# --- status effects -----------------------------------------------------------
MERGED_STATUS_EFFECTS: List[Tuple] = [
    (1, 'Attack Up', 'buff', '⚔️🔼', '2025-03-31 07:40:47', 0, 5),
    (2, 'Defense Down', 'debuff', '🛡️🔽', '2025-03-31 07:40:47', 0, 5),
    (3, 'Poisoned', 'debuff', '☣️', '2025-03-31 07:40:47', 0, 10),
    (4, 'Regen', 'buff', '❤️🔄', '2025-03-31 07:40:47', 0, 5),
    (5, 'Stun', 'debuff', '🌀', '2025-03-31 07:40:47', 0, 5),
    (6, 'Burn', 'debuff', '🔥', '2025-03-31 07:40:47', 0, 5),
    (7, 'Freeze', 'debuff', '❄️', '2025-03-31 07:40:47', 0, 5),
    (8, 'Bio', 'debuff', '☣️', '2025-05-23 05:10:16', 0, 5),
    (9, 'Silence', 'debuff', None, '2025-05-25 02:24:50', 0, 5),
    (10, 'Evasion Up', 'buff', None, '2025-05-25 02:25:42', 0, 5),
    (11, 'Blind', 'debuff', None, '2025-05-25 02:25:42', 0, 5),
    (12, 'Defense Up', 'buff', '🛡️🔼', '2025-05-25 02:28:44', 0, 5),
    (13, 'Mag.Def Up', 'buff', '🔮🛡️🔼', '2025-05-25 02:28:44', 0, 5),
    (14, 'Mag.Def Down', 'debuff', '🔮🛡️🔽', '2025-05-25 02:33:23', 0, 5),
    (15, 'Berserk', 'neutral', None, '2025-05-25 02:34:39', 0, 99),
    (16, 'Magic Up', 'buff', '🔮🔼', '2025-05-25 02:36:05', 0, 5),
    (17, 'Haste', 'buff', '⏱️🔼', '2025-05-25 07:36:06', 0, 5),
    (18, 'Slow', 'debuff', '⏳🔽', '2025-05-25 07:36:07', 0, 5),
    (19, 'Attack Down', 'debuff', '⚔️🔽', '2025-12-23 01:18:19', 0, 5),
    (20, 'Frog', 'debuff', '🐸', '2025-07-05 00:00:00', 0, 0),
    (21, 'Reflect', 'buff', '🔁🛡️', '2025-07-05 00:00:00', 0, 0),
    (22, 'Evasion Down', 'debuff', '🎯🔽', '2025-09-25 00:00:00', 0, 0),
    (23, 'Tamed', 'debuff', '🐾', '2025-09-25 00:00:00', 0, 0),
]


# --- floor → room placement rules seed data -------------------------------------------------
# (difficulty_name, floor_number, room_type, chance, max_per_floor)
MERGED_FLOOR_ROOM_RULES: List[Tuple] = [
    (1, 'Easy', 1, 'safe', 0.5, 80, '2025-04-25 02:03:18'),
    (2, 'Easy', 2, 'monster', 0.3, 10, '2025-04-25 02:03:18'),
    (3, 'Easy', 2, 'item', 0.1, 4, '2025-04-25 02:03:18'),
    (4, 'Easy', 1, 'staircase_down', 0.05, 1, '2025-04-25 02:03:18'),
    (5, 'Easy', 2, 'illusion', 0.05, 1, '2025-04-25 02:03:18'),
    (6, 'Easy', 2, 'safe', 0.5, 50, '2025-04-25 02:03:18'),
    (7, 'Easy', 2, 'shop', 0.1, 2, '2025-04-22 00:07:34'),
    (8, 'Easy', 1, 'illusion', 0.1, 3, '2025-04-22 00:33:59'),
    (9, 'Easy', 1, 'monster', 0.5, 60, '2025-04-22 00:07:34'),
    (10, 'Easy', 1, 'item', 0.3, 6, '2025-04-22 00:07:34'),
    (11, 'Easy', 1, 'shop', 0.1, 2, '2025-04-22 00:07:34'),
    (12, 'Easy', 1, 'exit', 0, 0, '2025-04-22 00:33:59'),
    (13, 'Easy', 2, 'staircase_up', 0, 0, '2025-04-22 00:33:59'),
    (14, 'Easy', 1, 'boss', 0, 0, '2025-04-22 00:33:59'),
    (15, 'Easy', 2, 'boss', 0.1, 1, '2025-04-22 00:33:59'),
    (16, 'Easy', 1, 'locked', 0.1, 3, '2025-05-25 06:57:39'),
    (17, 'Easy', 2, 'locked', 0.1, 3, '2025-05-25 06:57:39'),
    (35, 'Medium', 1, 'locked', 0.1, 3, '2025-05-25 06:57:39'),
    (36, 'Medium', 2, 'locked', 0.1, 3, '2025-05-25 06:57:39'),
    (18, 'Easy', 1, 'cloister', 100, 4, '2025-07-01 05:00:00'),
    (19, 'Easy', 2, 'cloister', 0.02, 1, '2025-07-01 05:00:00'),
    (20, 'Medium', 1, 'safe', 0.5, 50, '2025-04-25 02:03:18'),
    (21, 'Medium', 2, 'safe', 0.5, 50, '2025-04-25 02:03:18'),
    (22, 'Medium', 1, 'monster', 0.5, 70, '2025-04-22 00:07:34'),
    (23, 'Medium', 2, 'monster', 0.3, 10, '2025-04-25 02:03:18'),
    (24, 'Medium', 1, 'item', 0.3, 80, '2025-04-22 00:07:34'),
    (25, 'Medium', 2, 'item', 0.1, 4, '2025-04-25 02:03:18'),
    (26, 'Medium', 1, 'shop', 0.1, 5, '2025-04-22 00:07:34'),
    (27, 'Medium', 2, 'shop', 0.1, 2, '2025-04-22 00:07:34'),
    (28, 'Medium', 1, 'boss', 0, 0, '2025-04-22 00:33:59'),
    (29, 'Medium', 2, 'boss', 0.1, 1, '2025-04-22 00:33:59'),
    (30, 'Medium', 1, 'illusion', 0.1, 3, '2025-04-22 00:33:59'),
    (31, 'Medium', 2, 'illusion', 0.05, 1, '2025-04-25 02:03:18'),
    (32, 'Medium', 1, 'exit', 0, 0, '2025-04-22 00:33:59'),
    (33, 'Medium', 2, 'staircase_up', 0, 0, '2025-04-22 00:33:59'),
    (34, 'Medium', 1, 'staircase_down', 0.05, 1, '2025-04-25 02:03:18'),
    (37, 'Medium', 1, 'cloister', 100, 4, '2025-07-01 05:00:00'),
    (38, 'Medium', 2, 'cloister', 0.02, 1, '2025-07-01 05:00:00'),
    (39, 'Hard', 1, 'safe', 0.5, 80, '2025-04-25 02:03:18'),
    (40, 'Hard', 2, 'monster', 0.3, 10, '2025-04-25 02:03:18'),
    (41, 'Hard', 2, 'item', 0.1, 4, '2025-04-25 02:03:18'),
    (42, 'Hard', 1, 'staircase_down', 0.05, 1, '2025-04-25 02:03:18'),
    (43, 'Hard', 2, 'illusion', 0.05, 1, '2025-04-25 02:03:18'),
    (44, 'Hard', 2, 'safe', 0.5, 50, '2025-04-25 02:03:18'),
    (45, 'Hard', 2, 'shop', 0.1, 2, '2025-04-22 00:07:34'),
    (46, 'Hard', 1, 'illusion', 0.1, 3, '2025-04-22 00:33:59'),
    (47, 'Hard', 1, 'monster', 0.5, 60, '2025-04-22 00:07:34'),
    (48, 'Hard', 1, 'item', 0.3, 6, '2025-04-22 00:07:34'),
    (49, 'Hard', 1, 'shop', 0.1, 2, '2025-04-22 00:07:34'),
    (50, 'Hard', 1, 'exit', 0, 0, '2025-04-22 00:33:59'),
    (51, 'Hard', 2, 'staircase_up', 0, 0, '2025-04-22 00:33:59'),
    (52, 'Hard', 1, 'boss', 0, 0, '2025-04-22 00:33:59'),
    (53, 'Hard', 2, 'boss', 0.1, 1, '2025-04-22 00:33:59'),
    (54, 'Hard', 1, 'locked', 0.1, 3, '2025-05-25 06:57:39'),
    (55, 'Hard', 2, 'locked', 0.1, 3, '2025-05-25 06:57:39'),
    (56, 'Hard', 1, 'cloister', 100, 4, '2025-07-01 05:00:00'),
    (57, 'Hard', 2, 'cloister', 0.02, 1, '2025-07-01 05:00:00'),
    (58, 'Crazy Catto', 1, 'safe', 0.5, 50, '2025-04-25 02:03:18'),
    (59, 'Crazy Catto', 2, 'safe', 0.5, 50, '2025-04-25 02:03:18'),
    (60, 'Crazy Catto', 1, 'monster', 0.5, 70, '2025-04-22 00:07:34'),
    (61, 'Crazy Catto', 2, 'monster', 0.3, 10, '2025-04-25 02:03:18'),
    (62, 'Crazy Catto', 1, 'item', 0.3, 80, '2025-04-22 00:07:34'),
    (63, 'Crazy Catto', 2, 'item', 0.1, 4, '2025-04-25 02:03:18'),
    (64, 'Crazy Catto', 1, 'shop', 0.1, 5, '2025-04-22 00:07:34'),
    (65, 'Crazy Catto', 2, 'shop', 0.1, 2, '2025-04-22 00:07:34'),
    (66, 'Crazy Catto', 1, 'boss', 0, 0, '2025-04-22 00:33:59'),
    (67, 'Crazy Catto', 2, 'boss', 0.1, 1, '2025-04-22 00:33:59'),
    (68, 'Crazy Catto', 1, 'illusion', 0.1, 3, '2025-04-22 00:33:59'),
    (69, 'Crazy Catto', 2, 'illusion', 0.05, 1, '2025-04-25 02:03:18'),
    (70, 'Crazy Catto', 1, 'exit', 0, 0, '2025-04-22 00:33:59'),
    (71, 'Crazy Catto', 2, 'staircase_up', 0, 0, '2025-04-22 00:33:59'),
    (72, 'Crazy Catto', 1, 'staircase_down', 0.05, 1, '2025-04-25 02:03:18'),
    (73, 'Crazy Catto', 1, 'locked', 0.1, 3, '2025-05-25 06:57:39'),
    (74, 'Crazy Catto', 2, 'locked', 0.1, 3, '2025-05-25 06:57:39'),
    (75, 'Crazy Catto', 1, 'cloister', 100, 4, '2025-07-01 05:00:00'),
    (76, 'Crazy Catto', 2, 'cloister', 0.02, 1, '2025-07-01 05:00:00'),
]

# --- class trances ------------------------------------------------------------
MERGED_CLASS_TRANCES: List[Tuple] = [
    (1, 1, 'Braver', 15),
    (2, 2, 'Berserk', 15),
    (3, 3, 'SpellBlade', 15),
    (4, 4, 'Mug', 15),
    (5, 5, 'Mace', 15),
    (6, 6, 'Jump', 15),
    (7, 7, 'Ensemble', 15),
    (8, 8, 'Dbl White', 15),
    (9, 9, 'Dbl Black', 15),
    (10, 10, 'Enviro', 15),
    (11, 11, 'Eat', 15),
    (12, 12, 'Esper', 15),
]

# --- trance abilities ---------------------------------------------------------
MERGED_TRANCE_ABILITIES: List[Tuple[int, int]] = [
    (1, 54),
    (1, 55),
    (1, 56),
    (1, 57),
    (2, 58),
    (2, 59),
    (2, 60),
    (2, 61),
    (3, 74),
    (3, 75),
    (3, 76),
    (3, 77),
    (4, 62),
    (4, 63),
    (4, 64),
    (4, 65),
    (5, 78),
    (5, 79),
    (5, 80),
    (5, 81),
    (6, 66),
    (6, 67),
    (6, 68),
    (6, 69),
    (7, 56),
    (7, 61),
    (7, 69),
    (7, 53),
    (8, 82),
    (8, 85),
    (8, 87),
    (9, 83),
    (9, 84),
    (9, 86),
    (10, 70),
    (10, 71),
    (10, 72),
    (10, 73),
    (11, 79),
    (12, 204),
    (12, 205),
    (12, 206),
    (12, 122),
    (12, 123),
    (12, 124),
    (12, 125),
]

# --- crystal templates --------------------------------------------------------
MERGED_CRYSTAL_TEMPLATES: List[Tuple] = [
    (1, 1, 'Red Crystal Shard', "The room's illusion shifts...\n\nA glowing red crystal shard appears, what should you do?", 'https://cdn.discordapp.com/attachments/1362832151485354065/1384704817330393269/firecrystal.png?ex=6853665b&is=685214db&hm=0b49ddc1370d2b2f91a408bbbbe76fb0d5d5723c202e53db14e52322d77fbe98&', '2025-06-18 06:33:11'),
    (2, 2, 'Light-Blue Crystal Shard', "The room's illusion shifts...\n\nA glowing light-blue crystal shard appears, what should you do?", 'https://cdn.discordapp.com/attachments/1362832151485354065/1384703341178654820/icecrystal.png?ex=685364fb&is=6852137b&hm=5f7940f58527f53be967d56a159f00916417199bc314f6eb12bb81bd4b0cf59e&', '2025-06-18 06:34:12'),
    (3, 3, 'Light-Pink Crystal Shard', "The room's illusion shifts...\n\nA glowing light-pink crystal shard appears, what should you do?", 'https://cdn.discordapp.com/attachments/1362832151485354065/1384707943659995256/holycrystal.png?ex=68536944&is=685217c4&hm=041a02f83ce5b5103e2ce97b6c2e2028473ccdbe2276980fcdb53f119fdd77f0&', '2025-06-18 06:35:39'),
    (4, 4, 'Black Crystal Shard', "The room's illusion shifts...\n\nA glowing light-pink crystal shard appears, what should you do?", 'https://cdn.discordapp.com/attachments/1362832151485354065/1384709533502279690/deathcrystal.png?ex=68536abf&is=6852193f&hm=c07c4db1ffa345b5c7817741d9294fbdc4540c88f21b5f628b6b09705c0610fd&', '2025-06-18 06:41:56'),
    (5, 5, 'Grey Crystal Shard', "The room's illusion shifts...\n\nA glowing grey crystal shard appears, what should you do?", 'https://cdn.discordapp.com/attachments/1362832151485354065/1384703288770826380/aircrystal.png?ex=685364ee&is=6852136e&hm=12e5cc4fbe5b756c046c7d8ccaf0c82acfe55d7f99a22cdb4d14404471ba4cfa&', '2025-06-18 06:41:56'),
    (6, 6, 'Purple Crystal Shard', "The room's illusion shifts...\n\nA glowing purple crystal shard appears, what should you do?", 'https://cdn.discordapp.com/attachments/1362832151485354065/1384704317050589307/lightningcrystal.png?ex=685365e3&is=68521463&hm=d9668f3b00e6fdcb3d5251fef5e16940985a9741240efee914ebf599fc5befd6&', '2025-06-18 06:41:56'),
    (7, 7, 'Blue Crystal Shard', "The room's illusion shifts...\n\nA glowing blue crystal shard appears, what should you do?", 'https://cdn.discordapp.com/attachments/1362832151485354065/1384701852913897633/watercrystal.png?ex=68536398&is=68521218&hm=004d052a414f1caef751389b09a99a8eff5a1eec84863f97208584836b31e0e0&', '2025-06-18 06:41:56'),
    (8, 8, 'Green Crystal Shard', "The room's illusion shifts...\n\nA glowing green crystal shard appears, what should you do?", 'https://cdn.discordapp.com/attachments/1362832151485354065/1384701828759031838/earthcrystal.png?ex=68536392&is=68521212&hm=345ac8cdf68e2057c36b8ed4d1a6290f51fe6e227d986320fe19ff0caac20dce&', '2025-06-18 06:41:56'),
]

# --- key items ----------------------------------------------------------------
MERGED_KEY_ITEMS: List[Tuple] = [
    (1, 'Gold Key', 'A small Golden Key', None, '2025-04-25 08:23:30'),
]

# --- treasure chests ----------------------------------------------------------
MERGED_TREASURE_CHESTS: List[Tuple] = [
    (1, 'Gold Chest', 1, 12, '2025-04-25 08:22:25'),
    (2, 'Bronze Chest', 1, 12, '2025-04-25 18:47:46'),
    (3, 'Silver Chest', 2, 12, '2025-05-10 00:03:00'),
]

# --- chest default rewards ----------------------------------------------------
MERGED_CHEST_DEF_REWARDS: List[Tuple] = [
    (1, 1, 'key', 7, None, 1, 0.6),
    (2, 2, 'item', 5, None, 1, 1),
    (3, 1, 'key', 8, None, 1, 0.3),
    (4, 3, 'gil', None, None, 500, 0.8),
    (5, 1, 'key', 7, None, 1, 0.6),
    (6, 1, 'key', 8, None, 1, 0.3),
    (7, 3, 'gil', None, None, 500, 0.8),
]

# --- item_effects -------------------------------------------------------------
MERGED_ITEM_EFFECTS: List[Tuple] = []

# ═══════════════════════════════════════════════════════════════════════════
#  TABLE DEFINITIONS (players added + new floor_room_rules)
# ═══════════════════════════════════════════════════════════════════════════
TABLES = {
    'seed_meta': '''
        CREATE TABLE IF NOT EXISTS seed_meta (
            seed_name   VARCHAR(100) PRIMARY KEY,
            applied_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''',
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
            created_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            shops_per_floor     INT NOT NULL DEFAULT 0
        )
    ''',

    # ---------- floor_room_rules ----------
    'floor_room_rules': '''
        CREATE TABLE IF NOT EXISTS floor_room_rules (
            rule_id           INT AUTO_INCREMENT PRIMARY KEY,
            difficulty_name   VARCHAR(50) NOT NULL,
            floor_number      INT,
            room_type ENUM(
                'safe','entrance','monster','item','shop','boss','trap','illusion',
                'staircase_up','staircase_down','exit','locked','cloister'
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
    # ---------- element_oppositions ----------
    'element_oppositions': '''
        CREATE TABLE IF NOT EXISTS element_oppositions (
            opposition_id INT AUTO_INCREMENT PRIMARY KEY,
            element_id INT NOT NULL,
            opposing_element_id INT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE KEY unique_element_opposition (element_id),
            FOREIGN KEY (element_id) REFERENCES elements(element_id) ON DELETE CASCADE,
            FOREIGN KEY (opposing_element_id) REFERENCES elements(element_id) ON DELETE CASCADE
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
            mp_cost        INT DEFAULT 0,
            icon_url       VARCHAR(255),
            target_type    ENUM('self','enemy','ally','any') DEFAULT 'any',
            special_effect VARCHAR(50),
            element_id     INT,
            status_effect_id INT,
            status_duration INT,
            created_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            scaling_stat   ENUM('attack_power','magic_power','defense') NOT NULL,
            FOREIGN KEY (element_id) REFERENCES elements(element_id) ON DELETE SET NULL,
            FOREIGN KEY (status_effect_id) REFERENCES status_effects(effect_id) ON DELETE SET NULL
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
            base_mp             INT DEFAULT 0,
            base_defense        INT DEFAULT 5,
            base_magic_defense  INT DEFAULT 5,
            base_accuracy       INT DEFAULT 95,
            base_evasion        INT DEFAULT 5,
            base_speed          INT DEFAULT 10,
            image_url           VARCHAR(255),
            creator_id          BIGINT,
            created_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            atb_max             INT DEFAULT 5
        )
    ''',
    # ---------- temporary_abilities ----------
    'temporary_abilities': '''
        CREATE TABLE IF NOT EXISTS temporary_abilities (
            temp_ability_id INT AUTO_INCREMENT PRIMARY KEY,
            class_id INT NOT NULL,
            ability_name VARCHAR(100) NOT NULL,
            description TEXT,
            effect JSON,
            cooldown_turns INT DEFAULT 0,
            duration_turns INT DEFAULT 1,
            target_type ENUM('self','enemy','ally','any') DEFAULT 'self',
            icon_url VARCHAR(255),
            element_id INT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (class_id) REFERENCES classes(class_id) ON DELETE CASCADE,
            FOREIGN KEY (element_id) REFERENCES elements(element_id) ON DELETE SET NULL
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
            mp_increase                FLOAT NOT NULL DEFAULT 0,
            unlocked_abilities         JSON,
            created_at                 TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''',
    # ---------- class_abilities ----------
    'class_abilities': '''
        CREATE TABLE IF NOT EXISTS class_abilities (
            class_id   INT NOT NULL,
            ability_id INT NOT NULL,
            unlock_level INT DEFAULT 1,
            PRIMARY KEY (class_id, ability_id),
            FOREIGN KEY (class_id)   REFERENCES classes(class_id)   ON DELETE CASCADE,
            FOREIGN KEY (ability_id) REFERENCES abilities(ability_id) ON DELETE CASCADE,
            FOREIGN KEY (unlock_level) REFERENCES levels(level) ON UPDATE CASCADE
        )
    ''',
    'class_trances': '''
        CREATE TABLE IF NOT EXISTS class_trances (
            trance_id INT AUTO_INCREMENT PRIMARY KEY,
            class_id  INT NOT NULL,
            trance_name VARCHAR(32) NOT NULL,
            duration_turns INT NOT NULL,
            FOREIGN KEY (class_id) REFERENCES classes(class_id)
        )
    ''',
    'trance_abilities': '''
        CREATE TABLE IF NOT EXISTS trance_abilities (
            trance_id  INT NOT NULL,
            ability_id INT NOT NULL,
            FOREIGN KEY (trance_id) REFERENCES class_trances(trance_id),
            FOREIGN KEY (ability_id) REFERENCES abilities(ability_id)
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
            saved         BOOLEAN NOT NULL DEFAULT FALSE,
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
            mp               INT DEFAULT 0,
            max_mp           INT DEFAULT 0,
            attack_power     INT DEFAULT 10,
            defense          INT DEFAULT 5,
            magic_power      INT DEFAULT 10,
            magic_defense    INT DEFAULT 5,
            accuracy         INT DEFAULT 95,
            evasion          INT DEFAULT 5,
            speed            INT DEFAULT 10,
            coord_x          INT DEFAULT 0,
            coord_y          INT DEFAULT 0,
            current_floor_id INT DEFAULT NULL,
            inventory        JSON,
            discovered_rooms JSON,
            gil              INT DEFAULT 0,
            status_effects   JSON,
            is_dead          BOOLEAN NOT NULL DEFAULT FALSE,
            created_at       TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at       TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            kill_count       INT NOT NULL DEFAULT 0,
            enemies_defeated INT DEFAULT 0,
            rooms_visited    INT DEFAULT 0,
            gil_earned       INT DEFAULT 0,
            bosses_defeated  INT DEFAULT 0,
            current_floor    INT DEFAULT 1,
            PRIMARY KEY (player_id, session_id),
            FOREIGN KEY (session_id) REFERENCES sessions(session_id) ON DELETE CASCADE,
            FOREIGN KEY (class_id)   REFERENCES classes(class_id)   ON DELETE SET NULL
        )
    ''',
    # ---------- player_temporary_abilities ----------
    'player_temporary_abilities': '''
        CREATE TABLE IF NOT EXISTS player_temporary_abilities (
            session_id INT NOT NULL,
            player_id BIGINT NOT NULL,
            temp_ability_id INT NOT NULL,
            remaining_turns INT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (session_id, player_id, temp_ability_id),
            FOREIGN KEY (session_id) REFERENCES sessions(session_id) ON DELETE CASCADE,
            FOREIGN KEY (temp_ability_id) REFERENCES temporary_abilities(temp_ability_id) ON DELETE CASCADE,
            FOREIGN KEY (player_id, session_id) REFERENCES players(player_id, session_id) ON DELETE CASCADE
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
                'safe','entrance','monster','item','shop','boss','trap','illusion',
                'staircase_up','staircase_down','exit','locked','chest_unlocked',
                'miniboss','death','cloister'
            ) NOT NULL DEFAULT 'safe',
            template_name VARCHAR(100) NOT NULL,
            description   TEXT,
            image_url     VARCHAR(255),
            default_enemy_id INT,
            created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            trap_type     ENUM('spike','gil_snatcher','mimic'),
            trap_payload  JSON,
            eidolon_id   INT NULL,
            attune_level INT NULL,
            FOREIGN KEY (default_enemy_id) REFERENCES enemies(enemy_id) ON DELETE SET NULL,
            FOREIGN KEY (eidolon_id) REFERENCES eidolons(eidolon_id) ON DELETE SET NULL
        )
    ''',
    'crystal_templates': '''
        CREATE TABLE IF NOT EXISTS crystal_templates (
            template_id INT AUTO_INCREMENT PRIMARY KEY,
            element_id  INT NOT NULL,
            name        VARCHAR(100) NOT NULL,
            description TEXT,
            image_url   VARCHAR(255),
            created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (element_id) REFERENCES elements(element_id) ON DELETE CASCADE
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
            room_type VARCHAR(64) NOT NULL,
            image_url VARCHAR(255),
            default_enemy_id INT,
            exits JSON,
            has_encounter BOOLEAN DEFAULT FALSE,
            vendor_id INT,
            stair_up_floor_id INT,
            stair_up_x       INT,
            stair_up_y       INT,
            stair_down_floor_id INT,
            stair_down_x     INT,
            stair_down_y     INT,
            inner_template_id INT NULL,
            eidolon_id INT NULL,
            attune_level INT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            stair_up_floor   INT,
            stair_down_floor INT,
            FOREIGN KEY (session_id) REFERENCES sessions(session_id) ON DELETE CASCADE,
            FOREIGN KEY (floor_id)   REFERENCES floors(floor_id)     ON DELETE CASCADE,
            FOREIGN KEY (vendor_id)  REFERENCES session_vendor_instances(session_vendor_id) ON DELETE SET NULL,
            FOREIGN KEY (inner_template_id) REFERENCES room_templates(template_id) ON DELETE SET NULL,
            FOREIGN KEY (eidolon_id) REFERENCES eidolons(eidolon_id) ON DELETE SET NULL
        )
    ''',
    # ---------- eidolons ----------
    'eidolons': '''
        CREATE TABLE IF NOT EXISTS eidolons (
            eidolon_id      INT AUTO_INCREMENT PRIMARY KEY,
            name            VARCHAR(100) NOT NULL,
            description     TEXT,
            enemy_id        INT NOT NULL,
            required_level  INT NOT NULL DEFAULT 1,
            base_hp         INT DEFAULT 100,
            base_attack     INT DEFAULT 10,
            base_magic      INT DEFAULT 10,
            base_defense    INT DEFAULT 5,
            base_magic_defense INT DEFAULT 5,
            base_accuracy   INT DEFAULT 95,
            base_evasion    INT DEFAULT 5,
            base_speed      INT DEFAULT 10,
            summon_mp_cost  INT DEFAULT 0,
            created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (enemy_id) REFERENCES enemies(enemy_id) ON DELETE CASCADE
        )
    ''',
    # ---------- eidolon_abilities ----------
    'eidolon_abilities': '''
        CREATE TABLE IF NOT EXISTS eidolon_abilities (
            eidolon_id   INT NOT NULL,
            ability_id   INT NOT NULL,
            unlock_level INT DEFAULT 1,
            PRIMARY KEY (eidolon_id, ability_id),
            FOREIGN KEY (eidolon_id) REFERENCES eidolons(eidolon_id) ON DELETE CASCADE,
            FOREIGN KEY (ability_id) REFERENCES abilities(ability_id) ON DELETE CASCADE,
            FOREIGN KEY (unlock_level) REFERENCES levels(level) ON UPDATE CASCADE
        )
    ''',
    # ---------- player_eidolons ----------
    'player_eidolons': '''
        CREATE TABLE IF NOT EXISTS player_eidolons (
            session_id   INT NOT NULL,
            player_id    BIGINT NOT NULL,
            eidolon_id   INT NOT NULL,
            level        INT DEFAULT 1,
            experience   INT DEFAULT 0,
            unlocked_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (session_id, player_id, eidolon_id),
            FOREIGN KEY (session_id) REFERENCES sessions(session_id) ON DELETE CASCADE,
            FOREIGN KEY (player_id, session_id) REFERENCES players(player_id, session_id) ON DELETE CASCADE,
            FOREIGN KEY (eidolon_id) REFERENCES eidolons(eidolon_id) ON DELETE CASCADE
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
            spawn_weight        FLOAT NOT NULL DEFAULT 1,
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
            is_broken         BOOLEAN           NOT NULL DEFAULT FALSE,
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
            role ENUM('normal','miniboss','boss','eidolon') NOT NULL DEFAULT 'normal',
            description TEXT,
            hp INT NOT NULL,
            max_hp INT NOT NULL,
            mp INT DEFAULT 0,
            max_mp INT DEFAULT 0,
            attack_power INT DEFAULT 10,
            defense INT DEFAULT 5,
            magic_power INT DEFAULT 10,
            magic_defense INT DEFAULT 5,
            accuracy INT DEFAULT 95,
            evasion INT DEFAULT 5,
            speed INT DEFAULT 10,
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
            atb_max INT DEFAULT 5,
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
    # ---------- session_saves ----------
    'session_saves': '''
        CREATE TABLE IF NOT EXISTS session_saves (
            session_id INT NOT NULL,
            slot INT NOT NULL,
            save_title VARCHAR(100) NOT NULL,
            is_auto_save BOOLEAN NOT NULL DEFAULT FALSE,
            saved_state JSON NOT NULL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (session_id, slot),
            FOREIGN KEY (session_id) REFERENCES sessions(session_id) ON DELETE CASCADE
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
            weight INT NOT NULL DEFAULT 1,
            can_heal BOOLEAN NOT NULL DEFAULT FALSE,
            heal_threshold_pct FLOAT,
            heal_amount_pct FLOAT,
            scaling_stat ENUM('attack_power','magic_power','defense') NOT NULL,
            scaling_factor FLOAT NOT NULL DEFAULT 0,
            accuracy INT NOT NULL DEFAULT 100,
            PRIMARY KEY (enemy_id, ability_id),
            FOREIGN KEY (enemy_id) REFERENCES enemies(enemy_id)   ON DELETE CASCADE,
            FOREIGN KEY (ability_id) REFERENCES abilities(ability_id) ON DELETE CASCADE
        )
    ''',
    # ---------- beast_templates ----------
    'beast_templates': '''
        CREATE TABLE IF NOT EXISTS beast_templates (
            beast_id INT AUTO_INCREMENT PRIMARY KEY,
            enemy_id INT NOT NULL,
            name VARCHAR(80) NOT NULL,
            description TEXT,
            base_hp INT NOT NULL,
            base_mp INT NOT NULL DEFAULT 0,
            base_attack INT NOT NULL,
            base_magic INT NOT NULL,
            base_defense INT NOT NULL,
            base_magic_defense INT NOT NULL,
            base_accuracy INT NOT NULL,
            base_evasion INT NOT NULL,
            base_speed INT NOT NULL DEFAULT 10,
            image_url VARCHAR(255),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE KEY uniq_beast_enemy (enemy_id),
            FOREIGN KEY (enemy_id) REFERENCES enemies(enemy_id) ON DELETE CASCADE
        )
    ''',
    # ---------- player_beasts ----------
    'player_beasts': '''
        CREATE TABLE IF NOT EXISTS player_beasts (
            session_id INT NOT NULL,
            player_id BIGINT NOT NULL,
            beast_id INT NOT NULL,
            level INT NOT NULL DEFAULT 1,
            experience INT NOT NULL DEFAULT 0,
            current_hp INT NOT NULL,
            current_mp INT NOT NULL DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (session_id, player_id, beast_id),
            FOREIGN KEY (session_id) REFERENCES sessions(session_id) ON DELETE CASCADE,
            FOREIGN KEY (beast_id) REFERENCES beast_templates(beast_id) ON DELETE CASCADE
        )
    ''',
    # ---------- status_effects ----------
    'status_effects': '''
        CREATE TABLE IF NOT EXISTS status_effects (
            effect_id INT AUTO_INCREMENT PRIMARY KEY,
            effect_name VARCHAR(100) NOT NULL,
            effect_type ENUM('buff','debuff','neutral') NOT NULL,
            icon_url VARCHAR(255),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            value INT NOT NULL,
            duration INT NOT NULL
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
            relation ENUM('weak','resist','absorb','immune','normal') NOT NULL DEFAULT 'normal',
            multiplier FLOAT NOT NULL DEFAULT 1,
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
            FOREIGN KEY (effect_id) REFERENCES status_effects(effect_id) ON DELETE CASCADE
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
            difficulty       VARCHAR(50),
            gil              INT DEFAULT 0,
            enemies_defeated INT DEFAULT 0,
            rooms_visited    INT DEFAULT 0,
            items_found      INT DEFAULT 0,
            play_time        INT DEFAULT 0,
            completed_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    '''
}

# ═══════════════════════════════════════════════════════════════════════════
#  CREATION ORDER (players added, floor_room_rules after difficulties)
# ═══════════════════════════════════════════════════════════════════════════
TABLE_ORDER = [
    'seed_meta',
    'difficulties',
    'floor_room_rules',
    'elements',
    'element_oppositions',
    'status_effects',
    'abilities',
    'classes',
    'temporary_abilities',
    'levels',
    'class_abilities',
    'class_trances',
    'trance_abilities',
    'sessions',
    'session_players',
    'players',
    'player_temporary_abilities',
    'floors',
    'items',
    'npc_vendors',
    'npc_vendor_items',
    'session_vendor_instances',
    'session_vendor_items',
    'enemies',
    'beast_templates',
    'eidolons',
    'eidolon_abilities',
    'player_eidolons',
    'player_beasts',
    'room_templates',
    'crystal_templates',
    'rooms',
    'key_items',
    'treasure_chests',
    'chest_def_rewards',
    'treasure_chest_instances',
    'chest_instance_rewards',
    'enemy_drops',
    'enemy_abilities',
    'enemy_resistances',
    'game_events',
    'game_saves',
    'session_saves',
    'intro_steps',
    'ability_status_effects',
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
    values = [
        (
            name,
            width,
            height,
            min_floors,
            max_floors,
            min_rooms,
            enemy_chance,
            npc_count,
            basement_chance,
            basement_min_rooms,
            basement_max_rooms,
            created_at,
            shops_per_floor,
            name,
        )
        for (
            _,
            name,
            width,
            height,
            min_floors,
            max_floors,
            min_rooms,
            enemy_chance,
            npc_count,
            basement_chance,
            basement_min_rooms,
            basement_max_rooms,
            created_at,
            shops_per_floor,
        ) in MERGED_DIFFICULTIES
    ]
    cur.executemany(
        """
        INSERT INTO difficulties
          (name, width, height, min_floors, max_floors, min_rooms,
           enemy_chance, npc_count, basement_chance,
           basement_min_rooms, basement_max_rooms, created_at, shops_per_floor)
        SELECT %s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s
        WHERE NOT EXISTS (
            SELECT 1 FROM difficulties WHERE name = %s
        )
        """,
        values,
    )
    logger.info("Ensured difficulties.")

def insert_floor_room_rules(cur):
    logger.info("Checking floor_room_rules seed data…")
    if MERGED_FLOOR_ROOM_RULES:
        cur.executemany(
            """
            INSERT IGNORE INTO floor_room_rules
              (difficulty_name, floor_number, room_type, chance, max_per_floor, created_at)
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            [row[1:] for row in MERGED_FLOOR_ROOM_RULES]
        )
        logger.info("Ensured floor_room_rules.")

def insert_elements(cur):
    logger.info("Checking elements seed data…")
    values = [
        (element_name, created_at, element_name)
        for (_, element_name, created_at) in MERGED_ELEMENTS
    ]
    cur.executemany(
        """
        INSERT INTO elements (element_name, created_at)
        SELECT %s, %s
        WHERE NOT EXISTS (
            SELECT 1 FROM elements WHERE element_name = %s
        )
        """,
        values,
    )
    logger.info("Ensured elements.")

def insert_element_oppositions(cur):
    logger.info("Checking element_oppositions seed data…")
    cur.executemany(
        """
        INSERT IGNORE INTO element_oppositions
          (element_id, opposing_element_id)
        SELECT e.element_id, o.element_id
        FROM elements e
        JOIN elements o
          ON e.element_name = %s
         AND o.element_name = %s
        """,
        MERGED_ELEMENT_OPPOSITIONS
    )
    logger.info("Ensured element_oppositions.")

def insert_abilities(cur):
    logger.info("Checking abilities seed data…")
    cur.executemany(
        """
        INSERT IGNORE INTO abilities
          (ability_id, ability_name, description, effect, cooldown, icon_url,
           target_type, special_effect, element_id, status_effect_id,
           status_duration, created_at, scaling_stat)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """,
        MERGED_ABILITIES
    )
    cur.executemany(
        """
        INSERT IGNORE INTO abilities
          (ability_id, ability_name, description, effect, cooldown, icon_url,
           target_type, special_effect, element_id, status_effect_id,
           status_duration, created_at, scaling_stat, mp_cost)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """,
        MERGED_EIDOLON_ABILITY_DEFS
    )
    logger.info("Ensured abilities.")

def insert_classes(cur):
    logger.info("Checking classes seed data…")
    cur.executemany(
        """
        INSERT IGNORE INTO classes
          (class_id, class_name, description, base_hp, base_attack, base_magic, base_mp,
           base_defense, base_magic_defense, base_accuracy,
           base_evasion, base_speed, image_url, creator_id, created_at, atb_max)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """,
        MERGED_CLASSES
    )
    logger.info("Ensured classes.")

def insert_class_abilities(cur):
    logger.info("Checking class_abilities links…")
    cur.executemany(
        "INSERT IGNORE INTO class_abilities (class_id, ability_id, unlock_level) VALUES (%s, %s, %s)",
        MERGED_CLASS_ABILITIES
    )
    logger.info("Ensured class_abilities links.")

def insert_temporary_abilities(cur):
    logger.info("Checking temporary_abilities seed data…")
    values = [
        (
            class_id,
            ability_name,
            description,
            effect,
            cooldown_turns,
            duration_turns,
            target_type,
            icon_url,
            element_id,
            created_at,
            class_id,
            ability_name,
        )
        for (
            _,
            class_id,
            ability_name,
            description,
            effect,
            cooldown_turns,
            duration_turns,
            target_type,
            icon_url,
            element_id,
            created_at,
        ) in MERGED_TEMPORARY_ABILITIES
    ]
    cur.executemany(
        """
        INSERT INTO temporary_abilities
          (class_id, ability_name, description, effect, cooldown_turns,
           duration_turns, target_type, icon_url, element_id, created_at)
        SELECT %s,%s,%s,%s,%s,%s,%s,%s,%s,%s
        WHERE NOT EXISTS (
            SELECT 1
            FROM temporary_abilities
            WHERE class_id = %s AND ability_name = %s
        )
        """,
        values,
    )
    logger.info("Ensured temporary_abilities.")

def insert_levels(cur):
    logger.info("Checking levels seed data…")
    cur.executemany(
        """
        INSERT IGNORE INTO levels
          (level, required_exp, hp_increase, attack_increase, magic_increase,
           defense_increase, magic_defense_increase, accuracy_increase,
           evasion_increase, speed_increase, mp_increase, unlocked_abilities, created_at)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """,
        MERGED_LEVELS
    )
    logger.info("Ensured levels seed data.")

def insert_intro_steps(cur):
    logger.info("Checking intro_steps seed data…")
    cur.execute("SELECT step_order FROM intro_steps")
    existing_steps = {row[0] for row in cur.fetchall() if row and row[0] is not None}
    if existing_steps:
        logger.info("intro_steps already has %d entries; seeding missing steps only", len(existing_steps))
    rows_to_insert = [row[1:] for row in MERGED_INTRO_STEPS if row[1] not in existing_steps]
    if not rows_to_insert:
        logger.info("intro_steps already contains all seeded steps – skipping")
        return
    cur.executemany(
        """
        INSERT INTO intro_steps
          (step_order, title, description, image_url, created_at)
        VALUES (%s,%s,%s,%s,%s)
        """,
        rows_to_insert
    )
    logger.info("Inserted intro_steps.")

def insert_room_templates(cur):
    logger.info("Checking room_templates seed data…")
    cur.executemany(
        """
        INSERT IGNORE INTO room_templates
          (template_id, room_type, template_name, description, image_url,
           default_enemy_id, created_at, trap_type, trap_payload, eidolon_id, attune_level)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """,
        MERGED_ROOM_TEMPLATES
    )
    logger.info("Ensured room_templates.")

def insert_crystal_templates(cur):
    logger.info("Checking crystal_templates seed data…")
    values = [
        (element_id, name, description, image_url, created_at, element_id, name)
        for (
            _,
            element_id,
            name,
            description,
            image_url,
            created_at,
        ) in MERGED_CRYSTAL_TEMPLATES
    ]
    cur.executemany(
        """
        INSERT INTO crystal_templates
          (element_id, name, description, image_url, created_at)
        SELECT %s,%s,%s,%s,%s
        WHERE NOT EXISTS (
            SELECT 1
            FROM crystal_templates
            WHERE element_id = %s AND name = %s
        )
        """,
        values,
    )
    logger.info("Ensured crystal_templates.")

def insert_npc_vendors(cur):
    logger.info("Checking npc_vendors seed data…")
    values = [
        (vendor_name, description, inventory, image_url, created_at, vendor_name)
        for (
            _,
            vendor_name,
            description,
            inventory,
            image_url,
            created_at,
        ) in MERGED_NPC_VENDORS
    ]
    cur.executemany(
        """
        INSERT INTO npc_vendors
          (vendor_name, description, inventory, image_url, created_at)
        SELECT %s,%s,%s,%s,%s
        WHERE NOT EXISTS (
            SELECT 1 FROM npc_vendors WHERE vendor_name = %s
        )
        """,
        values,
    )
    logger.info("Ensured npc_vendors.")

def insert_items(cur):
    logger.info("Checking items seed data…")
    values = [
        (
            item_name,
            description,
            effect,
            item_type,
            usage_limit,
            price,
            store_stock,
            target_type,
            image_url,
            creator_id,
            created_at,
            item_name,
        )
        for (
            _,
            item_name,
            description,
            effect,
            item_type,
            usage_limit,
            price,
            store_stock,
            target_type,
            image_url,
            creator_id,
            created_at,
        ) in MERGED_ITEMS
    ]
    cur.executemany(
        """
        INSERT INTO items
          (item_name, description, effect, type, usage_limit, price,
           store_stock, target_type, image_url, creator_id, created_at)
        SELECT %s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s
        WHERE NOT EXISTS (
            SELECT 1 FROM items WHERE item_name = %s
        )
        """,
        values,
    )
    logger.info("Ensured items.")

def insert_key_items(cur):
    logger.info("Checking key_items seed data…")
    values = [
        (name, description, image_url, created_at, name)
        for (
            _,
            name,
            description,
            image_url,
            created_at,
        ) in MERGED_KEY_ITEMS
    ]
    cur.executemany(
        """
        INSERT INTO key_items (name, description, image_url, created_at)
        SELECT %s,%s,%s,%s
        WHERE NOT EXISTS (
            SELECT 1 FROM key_items WHERE name = %s
        )
        """,
        values,
    )
    logger.info("Ensured key_items.")

def insert_treasure_chests(cur):
    logger.info("Checking treasure_chests seed data…")
    values = [
        (chest_name, spawn_weight, template_id, created_at, chest_name, template_id)
        for (_, chest_name, spawn_weight, template_id, created_at) in MERGED_TREASURE_CHESTS
    ]
    cur.executemany(
        """
        INSERT INTO treasure_chests (chest_name, spawn_weight, template_id, created_at)
        SELECT %s, %s, %s, %s
        WHERE NOT EXISTS (
            SELECT 1
            FROM treasure_chests
            WHERE chest_name = %s AND template_id = %s
        )
        """,
        values
    )
    logger.info("Ensured treasure_chests.")

def insert_chest_def_rewards(cur):
    logger.info("Checking chest_def_rewards seed data…")
    values = [
        (
            chest_id,
            reward_type,
            reward_item_id,
            reward_key_item_id,
            amount,
            spawn_weight,
            chest_id,
            reward_type,
            reward_item_id,
            reward_key_item_id,
            amount,
            spawn_weight,
        )
        for (
            _,
            chest_id,
            reward_type,
            reward_item_id,
            reward_key_item_id,
            amount,
            spawn_weight,
        ) in MERGED_CHEST_DEF_REWARDS
    ]
    cur.executemany(
        """
        INSERT INTO chest_def_rewards
          (chest_id, reward_type, reward_item_id, reward_key_item_id, amount, spawn_weight)
        SELECT %s,%s,%s,%s,%s,%s
        WHERE NOT EXISTS (
            SELECT 1
            FROM chest_def_rewards
            WHERE chest_id = %s
              AND reward_type = %s
              AND reward_item_id <=> %s
              AND reward_key_item_id <=> %s
              AND amount = %s
              AND spawn_weight = %s
        )
        """,
        values,
    )
    logger.info("Ensured chest_def_rewards.")

def insert_class_trances(cur):
    logger.info("Checking class_trances seed data…")
    values = [
        (class_id, trance_name, duration_turns, class_id, trance_name)
        for (_, class_id, trance_name, duration_turns) in MERGED_CLASS_TRANCES
    ]
    cur.executemany(
        """
        INSERT INTO class_trances (class_id, trance_name, duration_turns)
        SELECT %s, %s, %s
        WHERE NOT EXISTS (
            SELECT 1
            FROM class_trances
            WHERE class_id = %s AND trance_name = %s
        )
        """,
        values
    )
    logger.info("Ensured class_trances.")

def insert_trance_abilities(cur):
    logger.info("Checking trance_abilities seed data…")
    values = [
        (trance_id, ability_id, trance_id, ability_id)
        for (trance_id, ability_id) in MERGED_TRANCE_ABILITIES
    ]
    cur.executemany(
        """
        INSERT INTO trance_abilities (trance_id, ability_id)
        SELECT %s, %s
        WHERE NOT EXISTS (
            SELECT 1
            FROM trance_abilities
            WHERE trance_id = %s AND ability_id = %s
        )
        """,
        values
    )
    logger.info("Ensured trance_abilities.")

def insert_enemies(cur):
    logger.info("Checking enemies seed data…")
    cur.executemany(
        """
        INSERT IGNORE INTO enemies
          (enemy_id, enemy_name, role, description, hp, max_hp, attack_power, defense,
           magic_power, magic_defense, accuracy, evasion, difficulty,
           abilities, image_url, spawn_chance, gil_drop, xp_reward,
           loot_item_id, loot_quantity, creator_id, created_at, atb_max)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """,
        MERGED_ENEMIES
    )
    logger.info("Ensured enemies.")

def insert_beast_templates(cur):
    logger.info("Checking beast_templates seed data…")
    cur.executemany(
        """
        INSERT IGNORE INTO beast_templates
          (beast_id, enemy_id, name, description, base_hp, base_mp, base_attack,
           base_magic, base_defense, base_magic_defense, base_accuracy, base_evasion,
           base_speed, image_url, created_at)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """,
        MERGED_BEAST_TEMPLATES
    )
    logger.info("Ensured beast_templates.")

def insert_enemy_abilities(cur):
    logger.info("Checking enemy_abilities links…")
    cur.executemany(
        """
        INSERT IGNORE INTO enemy_abilities
          (enemy_id, ability_id, weight, can_heal, heal_threshold_pct,
           heal_amount_pct, scaling_stat, scaling_factor, accuracy)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """,
        MERGED_ENEMY_ABILITIES
    )
    logger.info("Ensured enemy_abilities links.")

def insert_eidolons(cur):
    logger.info("Checking eidolons seed data…")
    cur.executemany(
        """
        INSERT IGNORE INTO eidolons
          (eidolon_id, name, description, enemy_id, required_level,
           base_hp, base_attack, base_magic, base_defense, base_magic_defense,
           base_accuracy, base_evasion, base_speed, summon_mp_cost, created_at)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """,
        MERGED_EIDOLONS
    )
    logger.info("Ensured eidolons.")

def insert_eidolon_abilities(cur):
    logger.info("Checking eidolon_abilities links…")
    cur.executemany(
        """
        INSERT IGNORE INTO eidolon_abilities
          (eidolon_id, ability_id, unlock_level)
        VALUES (%s,%s,%s)
        """,
        MERGED_EIDOLON_ABILITIES
    )
    logger.info("Ensured eidolon_abilities.")

def insert_enemy_drops(cur):
    logger.info("Checking enemy_drops seed data…")
    cur.executemany(
        """
        INSERT IGNORE INTO enemy_drops (enemy_id,item_id,drop_chance,min_qty,max_qty)
        VALUES (%s,%s,%s,%s,%s)
        """,
        MERGED_ENEMY_DROPS
    )
    logger.info("Ensured enemy_drops.")

def insert_enemy_resistances(cur):
    logger.info("Checking enemy_resistances seed data…")
    cur.executemany(
        "INSERT IGNORE INTO enemy_resistances (enemy_id,element_id,resistance,relation,multiplier) VALUES (%s,%s,%s,%s,%s)",
        MERGED_ENEMY_RESISTANCES
    )
    logger.info("Ensured enemy_resistances.")

def insert_npc_vendor_items(cur):
    logger.info("Checking npc_vendor_items seed data…")
    cur.executemany(
        """
        INSERT IGNORE INTO npc_vendor_items (vendor_id,item_id,price,stock,instance_stock)
        VALUES (%s,%s,%s,%s,%s)
        """,
        MERGED_NPC_VENDOR_ITEMS
    )
    logger.info("Ensured npc_vendor_items.")

def insert_status_effects(cur):
    logger.info("Checking status_effects seed data…")
    values = [
        (
            effect_name,
            effect_type,
            icon_url,
            created_at,
            value,
            duration,
            effect_name,
        )
        for (
            _,
            effect_name,
            effect_type,
            icon_url,
            created_at,
            value,
            duration,
        ) in MERGED_STATUS_EFFECTS
    ]
    cur.executemany(
        """
        INSERT INTO status_effects
          (effect_name,effect_type,icon_url,created_at,value,duration)
        SELECT %s,%s,%s,%s,%s,%s
        WHERE NOT EXISTS (
            SELECT 1 FROM status_effects WHERE effect_name = %s
        )
        """,
        values,
    )
    logger.info("Ensured status_effects.")

def insert_ability_status_effects(cur):
    logger.info("Checking ability_status_effects links…")
    cur.executemany(
        "INSERT IGNORE INTO ability_status_effects (ability_id,effect_id) VALUES (%s,%s)",
        MERGED_ABILITY_STATUS_EFFECTS
    )
    logger.info("Ensured ability_status_effects links.")

def insert_hub_embeds(cur):
    logger.info("Checking hub_embeds seed data…")
    values = [
        (
            embed_type,
            title,
            description,
            image_url,
            text_field,
            step_order,
            created_at,
            embed_type,
            step_order,
            title,
        )
        for (
            _,
            embed_type,
            title,
            description,
            image_url,
            text_field,
            step_order,
            created_at,
        ) in MERGED_HUB_EMBEDS
    ]
    cur.executemany(
        """
        INSERT INTO hub_embeds
          (embed_type,title,description,image_url,text_field,step_order,created_at)
        SELECT %s,%s,%s,%s,%s,%s,%s
        WHERE NOT EXISTS (
            SELECT 1
            FROM hub_embeds
            WHERE embed_type = %s
              AND step_order <=> %s
              AND title <=> %s
        )
        """,
        values,
    )
    logger.info("Ensured hub_embeds.")

def seed_already_applied(cur, seed_name: str = "initial_seed") -> bool:
    cur.execute("SELECT 1 FROM seed_meta WHERE seed_name = %s LIMIT 1", (seed_name,))
    return cur.fetchone() is not None

def mark_seed_applied(cur, seed_name: str = "initial_seed") -> None:
    cur.execute("INSERT INTO seed_meta (seed_name) VALUES (%s)", (seed_name,))

# ═══════════════════════════════════════════════════════════════════════════
#  MAIN
# ═══════════════════════════════════════════════════════════════════════════
def main() -> None:
    logger.info("Connecting to MySQL…")
    try:
        with mysql.connector.connect(**DB_CONFIG) as cnx:
            with cnx.cursor() as cur:
                logger.info("Creating / verifying tables…")
                tables_to_seed = set()
                for tbl in TABLE_ORDER:
                    existed = table_exists(cur, tbl)
                    cur.execute(TABLES[tbl])
                    if not existed:
                        tables_to_seed.add(tbl)
                    logger.debug("Table `%s` ready.", tbl)

                # ── schema migrations (add missing columns/enums) ──────────────
                ensure_enum_values(cur, "enemies", "role", ["eidolon"], "normal")
                ensure_enum_values(cur, "floor_room_rules", "room_type", ["cloister"], "safe")
                ensure_enum_values(cur, "room_templates", "room_type", ["cloister"], "safe")

                if ensure_column(cur, "abilities", "mp_cost", "INT DEFAULT 0"):
                    tables_to_seed.add("abilities")
                if ensure_column(cur, "classes", "base_mp", "INT DEFAULT 0"):
                    tables_to_seed.add("classes")
                if ensure_column(cur, "levels", "mp_increase", "FLOAT NOT NULL DEFAULT 0"):
                    tables_to_seed.add("levels")
                if ensure_column(cur, "players", "mp", "INT DEFAULT 0"):
                    tables_to_seed.add("players")
                if ensure_column(cur, "players", "max_mp", "INT DEFAULT 0"):
                    tables_to_seed.add("players")
                if ensure_column(cur, "enemies", "mp", "INT DEFAULT 0"):
                    tables_to_seed.add("enemies")
                if ensure_column(cur, "enemies", "max_mp", "INT DEFAULT 0"):
                    tables_to_seed.add("enemies")
                if ensure_column(cur, "room_templates", "eidolon_id", "INT NULL"):
                    tables_to_seed.add("room_templates")
                if ensure_column(cur, "room_templates", "attune_level", "INT NULL"):
                    tables_to_seed.add("room_templates")
                if ensure_column(cur, "rooms", "eidolon_id", "INT NULL"):
                    tables_to_seed.add("rooms")
                if ensure_column(cur, "rooms", "attune_level", "INT NULL"):
                    tables_to_seed.add("rooms")
                if ensure_column(cur, "enemies", "speed", "INT DEFAULT 10"):
                    tables_to_seed.add("enemies")

                # ── seed data (order matters) ──────────────────────────────────
                if "difficulties" in tables_to_seed:
                    insert_difficulties(cur)
                if "floor_room_rules" in tables_to_seed:
                    insert_floor_room_rules(cur)
                if "elements" in tables_to_seed:
                    insert_elements(cur)
                if "element_oppositions" in tables_to_seed:
                    insert_element_oppositions(cur)
                if "status_effects" in tables_to_seed:
                    insert_status_effects(cur)
                if "levels" in tables_to_seed:
                    insert_levels(cur)
                if "abilities" in tables_to_seed:
                    insert_abilities(cur)
                if "classes" in tables_to_seed:
                    insert_classes(cur)
                if "class_abilities" in tables_to_seed:
                    insert_class_abilities(cur)
                if "temporary_abilities" in tables_to_seed:
                    insert_temporary_abilities(cur)
                if "class_trances" in tables_to_seed:
                    insert_class_trances(cur)
                if "trance_abilities" in tables_to_seed:
                    insert_trance_abilities(cur)
                if "intro_steps" in tables_to_seed:
                    insert_intro_steps(cur)
                if "npc_vendors" in tables_to_seed:
                    insert_npc_vendors(cur)
                if "items" in tables_to_seed:
                    insert_items(cur)
                if "key_items" in tables_to_seed:
                    insert_key_items(cur)
                if "enemies" in tables_to_seed:
                    insert_enemies(cur)
                if "beast_templates" in tables_to_seed:
                    insert_beast_templates(cur)
                if "enemy_abilities" in tables_to_seed:
                    insert_enemy_abilities(cur)
                if "eidolons" in tables_to_seed:
                    insert_eidolons(cur)
                if "eidolon_abilities" in tables_to_seed:
                    insert_eidolon_abilities(cur)
                if "room_templates" in tables_to_seed:
                    insert_room_templates(cur)
                if "treasure_chests" in tables_to_seed:
                    insert_treasure_chests(cur)
                if "chest_def_rewards" in tables_to_seed:
                    insert_chest_def_rewards(cur)
                if "crystal_templates" in tables_to_seed:
                    insert_crystal_templates(cur)
                if "enemy_drops" in tables_to_seed:
                    insert_enemy_drops(cur)
                if "enemy_resistances" in tables_to_seed:
                    insert_enemy_resistances(cur)
                if "npc_vendor_items" in tables_to_seed:
                    insert_npc_vendor_items(cur)
                if "ability_status_effects" in tables_to_seed:
                    insert_ability_status_effects(cur)
                if "hub_embeds" in tables_to_seed:
                    insert_hub_embeds(cur)
                cnx.commit()
                logger.info("Database setup complete ✔")
    except Error as err:
        logger.error("Database error: %s", err)
        raise SystemExit(1)


if __name__ == "__main__":
    main()
