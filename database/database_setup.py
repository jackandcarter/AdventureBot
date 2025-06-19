# db/setup_database.py
# ───────────────────────────────────────────────────────────────────────────
#  AdventureBot  –  schema builder + seed‑loader
# ───────────────────────────────────────────────────────────────────────────

import json
import logging
import os
from typing import List, Tuple
import re

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
    (1, 'Cure', 'Heals a small amount of HP.', '{"heal": 50}', 1, '❤️', 'self', None, None, None, None, '2025-03-31 07:40:47', 'magic_power'),
    (2, 'Fire', 'Deals fire damage to an enemy.', '{"base_damage": 50}', 1, '🔥', 'enemy', None, 1, None, None, '2025-03-31 07:40:47', 'magic_power'),
    (3, 'Blizzard', 'Deals ice damage to an enemy.', '{"base_damage": 50}', 1, '❄️', 'enemy', None, 2, None, None, '2025-03-31 07:40:47', 'magic_power'),
    (4, 'Holy', 'Deals holy damage to one enemy.', '{"base_damage": 100}', 1, '✨', 'enemy', None, 3, None, None, '2025-03-31 07:40:47', 'magic_power'),
    (5, 'Meteor', 'Massive non‑elemental damage to enemies.', '{"base_damage": 120}', 2, '💫', 'enemy', None, 4, None, None, '2025-03-31 07:40:47', 'magic_power'),
    (6, 'Jump', 'Leap high and strike down a foe.', '{"base_damage": 50}', 5, '🏃\u200d♂️', 'enemy', None, None, None, None, '2025-03-31 07:40:47', 'attack_power'),
    (7, 'Kick', 'Deals physical damage to all enemies.', '{"base_damage": 50}', 3, '🥾', 'enemy', None, None, None, None, '2025-03-31 07:40:47', 'attack_power'),
    (8, 'Steal', 'Attempt to steal an item from an enemy.', '{"steal_chance": 50}', 0, '🦹', 'enemy', None, None, None, None, '2025-03-31 07:40:47', 'attack_power'),
    (9, 'Scan', 'Reveal an enemy’s HP and weaknesses.', '{"scan": true}', 1, '🔍', 'enemy', None, None, None, None, '2025-03-31 07:40:47', 'attack_power'),
    (10, 'Berserk', 'Boost attack but reduce defense.', '{"attack_power": 50, "defense_down": 20}', 3, '💪🔼🛡️', 'self', None, None, 15, 5, '2025-03-31 07:40:47', 'attack_power'),
    (11, 'Revive', 'Revives a fainted ally with a surge of healing.', '{"heal": 50, "revive": true}', 1, '♻️', 'ally', None, None, None, None, '2025-03-31 07:40:47', 'magic_power'),
    (12, 'Thunder', 'Deals lightning damage to an enemy.', '{"base_damage": 50}', 1, '⚡', 'enemy', None, 5, None, None, '2025-03-31 07:40:47', 'magic_power'),
    (13, 'Barrier', 'Raises your defense for a short time.', '{"barrier": {"duration": 3}}', 3, '🛡️🔼', 'self', None, None, 12, 3, '2025-03-31 07:40:47', 'defense'),
    (14, 'Power Break', 'Lower Enemy Attack Power.', '{"attack_power_down": 10}', 1, '💪🔽', 'enemy', None, None, 1, 3, '2025-04-03 12:43:43', 'attack_power'),
    (15, 'Armor Break', 'Lower Enemy Defense', '{"defense_down": 30}', 1, '🛡️🔽', 'enemy', None, None, 2, 3, '2025-04-03 12:43:43', 'attack_power'),
    (16, 'Mental Break', 'Lowers Enemy Magic Power and Magic Defense', '{"magic_power_down": 30, "magic_defense_down": 30}', 1, '🔮🛡️🔽', 'enemy', None, None, 14, 3, '2025-04-03 12:43:43', 'magic_power'),
    (17, 'Fira', 'Deals greater fire damage to one enemy.', '{"base_damage": 70}', 1, '🔥', 'enemy', None, 1, None, None, '2025-04-03 12:43:43', 'magic_power'),
    (18, 'FIraga', 'Deals devastating fire damage to one enemy.', '{"base_damage": 90}', 1, '🔥', 'enemy', None, 1, None, None, '2025-04-03 12:43:43', 'magic_power'),
    (19, 'Bizzara', 'Deals greater ice damage to one enemy.', '{"base_damage": 70}', 1, '❄️', 'enemy', None, 2, None, None, '2025-04-03 12:43:43', 'magic_power'),
    (20, 'Bizzaga', 'Deals devastating ice damage to one enemy.', '{"base_damage": 90}', 1, '❄️', 'enemy', None, 2, None, None, '2025-04-03 12:43:43', 'magic_power'),
    (21, 'Thundara', 'Deals greater lightning damage to a single enemy.', '{"base_damage": 70}', 1, '⚡', 'enemy', None, 5, None, None, '2025-04-03 12:43:43', 'magic_power'),
    (22, 'Thundaga', 'Deals devastating lightning damage to a single enemy.', '{"base_damage": 90}', 1, '⚡', 'enemy', None, 5, None, None, '2025-04-03 12:43:43', 'magic_power'),
    (23, 'Flare', 'A massive non‑elemental magic attack dealing significant damage.', '{"base_damage": 100}', 2, '💥', 'enemy', None, 4, None, None, '2025-04-03 12:43:43', 'magic_power'),
    (24, 'Ultima', 'A massive non‑elemental magic attack dealing very high damage.', '{"base_damage": 150}', 3, '🌀', 'enemy', None, 4, None, None, '2025-04-03 12:43:43', 'magic_power'),
    (25, 'Comet', 'A massive non‑elemental magic attack dealing very high damage.', '{"base_damage": 125}', 2, '☄️', 'enemy', None, 4, None, None, '2025-04-03 12:43:43', 'magic_power'),
    (26, 'Cura', 'Heals a greater amount of HP.', '{"heal": 100}', 1, '❤️', 'self', None, None, None, None, '2025-04-03 12:43:43', 'magic_power'),
    (27, 'Curaga', 'Heals a high amount of HP.', '{"heal": 200}', 1, '❤️', 'self', None, None, None, None, '2025-04-03 12:43:43', 'magic_power'),
    (28, 'Regen', 'Heals a small amount of HP over time.', '{"healing_over_time": {"percent": 0.2, "duration": 10}}', 1, '❤️🔄', 'self', None, None, 4, 10, '2025-04-03 12:43:43', 'magic_power'),
    (29, 'Shell', 'Raises your magic defense.', '{"magic_defense_up": 30}', 1, '🔮🛡️🔼', 'self', None, None, 13, 5, '2025-04-03 12:43:43', 'magic_power'),
    (30, 'Blink', 'Raises your evasion.', '{"evasion_up": 30}', 2, '🎯🔼', 'self', None, None, 10, 5, '2025-04-03 12:43:43', 'magic_power'),
    (31, 'Demi', 'Deals damaged based on enemy health.', '{"percent_damage": 0.25}', 1, '🌀', 'enemy', None, 4, None, None, '2025-04-03 12:43:43', 'attack_power'),
    (32, 'Gravity', 'Deals Air based damage while grounding flying enemies.', '{"base_damage": 80}', 1, '🪐', 'enemy', None, None, None, None, '2025-04-03 12:43:43', 'magic_power'),
    (33, 'Haste', 'Grants higher speed with chance of increasing turns.', '{"speed_up": 30, "duration": 3}', 3, '⏱️🔼', 'self', None, None, None, None, '2025-04-03 12:43:43', 'magic_power'),
    (34, 'Slow', 'Lowers enemy speed with chance of reducing turns.', '{"speed_down": 30, "duration": 2}', 2, '⏳🔽', 'enemy', None, None, None, None, '2025-04-03 12:43:43', 'magic_power'),
    (35, 'Poison', 'Deals a small amount of damage over time.', '{"damage_over_time": {"duration": 3, "damage_per_turn": 10}}', 3, '☠️', 'enemy', None, None, 3, 5, '2025-04-03 12:43:43', 'attack_power'),
    (36, 'Bio', 'Deals a greater amount of damage over time.', '{"damage_over_time": {"duration": 5, "damage_per_turn": 12}}', 5, '☣️', 'enemy', None, None, 8, 5, '2025-04-03 12:43:43', 'attack_power'),
    (37, 'Focus', 'Raises your magic power.', '{"magic_power_up": 30}', 1, '🔮🔼', 'self', None, None, 16, 5, '2025-04-03 12:43:43', 'attack_power'),
    (38, 'Fireblade', 'A Spellblade ability that fuses fire to your attacks.', '{"base_damage": 50}', 1, '🔥⚔️', 'enemy', None, 1, None, None, '2025-04-03 12:51:14', 'attack_power'),
    (39, 'Iceblade', 'A Spellblade ability that fuses ice to your attacks.', '{"base_damage": 50}', 1, '❄️⚔️', 'enemy', None, 2, None, None, '2025-04-03 12:51:14', 'attack_power'),
    (40, 'Thunderblade', 'A Spellblade ability that fuses thunder to your attacks.', '{"base_damage": 50}', 1, '⚡⚔️', 'enemy', None, 6, None, None, '2025-04-03 12:51:14', 'attack_power'),
    (41, 'Heavy Swing', 'A heavy attack dealing medium damage.', '{"base_damage": 50}', 2, '⚔️', 'enemy', None, None, None, None, '2025-04-15 01:35:52', 'attack_power'),
    (42, 'Climhazzard', 'A deadly physical attack dealing high damage.', '{"base_damage": 110}', 5, '⚔️', 'enemy', None, None, None, None, '2025-04-15 01:59:30', 'attack_power'),
    (43, 'Break', 'Reduce enemy HP to 1.', '{"set_enemy_hp_to": 1}', 5, '⚔️', 'enemy', None, None, None, None, '2025-04-15 02:47:21', 'attack_power'),
    (44, 'Demiblade', 'A Spellblade ability that reduces enemy hp by a percentage.', '{"percent_damage": 0.25}', 1, '⚔️', 'enemy', None, 4, None, None, '2025-04-27 19:16:00', 'attack_power'),
    (45, 'Gravityblade', 'A Spellblade ability that fuses gravity magic to your attacks.', '{"base_damage": 80}', 1, '⚔️', 'enemy', None, 5, None, None, '2025-04-27 19:16:00', 'attack_power'),
    (46, 'Silence', 'Stops enemies from using magic for a short time.', None, 1, None, 'enemy', None, None, 9, 3, '2025-04-27 19:16:00', 'attack_power'),
    (47, 'BioBlade', 'Deals initial base damage and greater amount of damage over time.', '{"damage_over_time": {"duration": 5, "damage_per_turn": 12}, "non_elemental_damage": 20}', 1, '☣️⚔', 'any', None, None, 8, 3, '2025-05-01 12:17:43', 'attack_power'),
    (48, 'Lucky 7', 'Deals 7, 77, 777, or 7777 damage if the player HP has a 7 in it. Otherwise deal 1 damage.', '{"lucky_7": true}', 1, '7️⃣', 'enemy', None, None, None, None, '2025-05-10 14:38:35', 'attack_power'),
    (49, 'Excalibur', 'Summons the legendary sword to deal massive non-elemental damage.', '{"base_damage": 200}', 5, '⚔️', 'enemy', None, 4, None, None, '2025-05-10 15:12:34', 'attack_power'),
    (50, 'Pilfer Gil', 'Steals Gil from an enemy.', '{"pilfer_gil": true}', 2, '💰', 'enemy', None, None, None, None, '2025-05-10 15:12:34', 'attack_power'),
    (51, 'Mug', 'Deals damage while stealing Gil from the enemy.', '{"mug": {"damage": 50}}', 1, '⚔️💰', 'enemy', None, None, None, None, '2025-05-10 15:12:34', 'attack_power'),
    (52, 'Light Shot', 'Light attack on an enemy', '{"base_damage": 50}', 1, '⚔️', 'enemy', None, None, None, None, '2025-05-10 18:26:42', 'attack_power'),
    (53, 'Heavy Shot', 'Heavy attack on an enemy', '{"base_damage": 150}', 1, '⚔️', 'enemy', None, None, None, None, '2025-05-10 18:26:42', 'attack_power'),
    (54, 'Cross-Slash', None, '{"base_damage": 200}', 1, '⚔️', 'enemy', None, None, None, None, '2025-05-11 03:48:29', 'attack_power'),
    (55, 'Meteorain', None, '{"base_damage": 300}', 1, '⚔️', 'enemy', None, None, None, None, '2025-05-11 03:48:29', 'attack_power'),
    (56, 'Finishing Touch', None, '{"base_damage": 400}', 1, '⚔️', 'enemy', None, None, None, None, '2025-05-11 03:48:29', 'attack_power'),
    (57, 'Omnislash', None, '{"base_damage": 999}', 1, '⚔️', 'enemy', None, None, None, None, '2025-05-11 03:48:29', 'attack_power'),
    (58, 'Stagger', None, '{"base_damage": 150}', 1, '⚔️', 'enemy', None, None, None, None, '2025-05-11 03:48:29', 'attack_power'),
    (59, 'Bull Charge', None, '{"base_damage": 200}', 1, '⚔️', 'enemy', None, None, None, None, '2025-05-11 03:48:29', 'attack_power'),
    (60, 'Wallop', None, '{"base_damage": 300}', 1, '⚔️', 'enemy', None, None, None, None, '2025-05-11 03:48:29', 'attack_power'),
    (61, 'Poisontouch', None, '{"damage_over_time": {"duration": 5, "damage_per_turn": 45}}', 1, '⚔️', 'enemy', None, None, None, None, '2025-05-11 03:48:29', 'attack_power'),
    (62, 'Grand Lethal', None, '{"base_damage": 300}', 1, '⚔️', 'enemy', None, None, None, None, '2025-05-11 03:48:29', 'attack_power'),
    (63, 'Bandit', None, '{"mug": {"damage": 100}}', 1, '⚔️', 'enemy', None, None, None, None, '2025-05-11 03:48:29', 'attack_power'),
    (64, 'Master Thief', None, '{"base_damage": 200}', 1, '⚔️', 'enemy', None, None, None, None, '2025-05-11 03:48:29', 'attack_power'),
    (65, 'Confuse', None, '{"base_damage": 200}', 1, '⚔️', 'enemy', None, None, None, None, '2025-05-11 03:48:29', 'attack_power'),
    (66, 'Lancet', None, '{"base_damage": 200}', 1, '⚔️', 'enemy', None, None, None, None, '2025-05-11 03:48:29', 'attack_power'),
    (67, 'High Jump', None, '{"base_damage": 200}', 1, '⚔️', 'enemy', None, None, None, None, '2025-05-11 03:48:29', 'attack_power'),
    (68, 'Eye 4 Eye', None, '{"base_damage": 300}', 1, '⚔️', 'enemy', None, None, None, None, '2025-05-11 03:48:29', 'attack_power'),
    (69, 'Beast Killer', None, '{"base_damage": 400}', 1, '⚔️', 'enemy', None, None, None, None, '2025-05-11 03:48:29', 'attack_power'),
    (70, 'Avalanche', None, '{"base_damage": 300}', 1, '⚔️', 'enemy', None, 2, None, None, '2025-05-11 03:48:29', 'magic_power'),
    (71, 'Tornado', None, '{"base_damage": 300}', 1, '⚔️', 'enemy', None, 5, None, None, '2025-05-11 03:48:29', 'magic_power'),
    (72, 'Earthquake', None, '{"base_damage": 300}', 1, '⚔️', 'enemy', None, 8, None, None, '2025-05-11 03:48:29', 'magic_power'),
    (73, 'Meteor', None, '{"base_damage": 400}', 1, '⚔️', 'enemy', None, 4, None, None, '2025-05-11 03:48:29', 'magic_power'),
    (74, 'UltimaBlade', None, '{"base_damage": 400}', 1, '⚔️', 'enemy', None, 4, None, None, '2025-05-11 03:48:29', 'magic_power'),
    (75, 'MeteorBlade', None, '{"base_damage": 400}', 1, '⚔️', 'enemy', None, 4, None, None, '2025-05-11 03:48:29', 'magic_power'),
    (76, 'HolyBlade', None, '{"base_damage": 400}', 1, '⚔️', 'enemy', None, 3, None, None, '2025-05-11 03:48:29', 'magic_power'),
    (77, 'GravijaBlade', None, '{"base_damage": 400}', 1, '⚔️', 'enemy', None, 5, None, None, '2025-05-11 03:48:29', 'magic_power'),
    (78, 'Bio II', None, '{"damage_over_time": {"duration": 7, "damage_per_turn": 72}}', 1, '⚔️', 'enemy', None, None, 8, 7, '2025-05-11 03:48:29', 'attack_power'),
    (79, 'Frog', None, '{"base_damage": 0}', 1, '⚔️', 'enemy', None, None, None, None, '2025-05-11 03:48:29', 'attack_power'),
    (80, 'Full-Cure', None, '{"heal": 9999}', 1, None, 'self', None, None, None, None, '2025-05-11 03:48:29', 'attack_power'),
    (81, 'Reflect', None, '{"base_damage": 150}', 1, None, 'self', None, None, None, None, '2025-05-11 03:48:29', 'attack_power'),
    (82, 'Dbl Holy', None, '{"base_damage": 400}', 1, '⚔️', 'enemy', None, 3, None, None, '2025-05-11 03:48:29', 'magic_power'),
    (83, 'Dbl Ultima', None, '{"base_damage": 400}', 1, '⚔️', 'enemy', None, 4, None, None, '2025-05-11 03:48:29', 'magic_power'),
    (84, 'Dbl Focus', None, '{"base_damage": 150}', 1, None, 'self', None, None, None, None, '2025-05-11 03:48:29', 'magic_power'),
    (85, 'Dbl Cure', None, '{"heal": 500}', 1, None, 'self', None, None, None, None, '2025-05-11 03:48:29', 'magic_power'),
    (86, 'Dbl Flare', None, '{"base_damage": 200}', 1, '⚔️', 'enemy', None, 4, None, None, '2025-05-11 03:48:29', 'magic_power'),
    (87, 'Dbl Dia', None, '{"base_damage": 200}', 1, '⚔️', 'enemy', None, 3, None, None, '2025-05-11 03:48:29', 'magic_power'),
    (88, 'White Wind', None, '{"healing_over_time": {"percent": 0.05, "duration": 10}}', 0, '❤️', 'self', None, None, 4, 10, '2025-05-14 01:44:27', 'magic_power'),
    (89, 'Mighty Guard', None, '{"barrier": {"duration": 3}}', 0, '🛡️🔼', 'self', None, None, 12, 3, '2025-05-14 01:44:27', 'attack_power'),
    (90, 'Blue Bullet', None, '{"base_damage": 100}', 0, '⚔️', 'enemy', None, None, None, None, '2025-05-14 01:45:27', 'attack_power'),
    (91, 'Karma', 'Deals Damage based on turn amount', '{"karma": true}', 3, None, 'any', None, None, None, None, '2025-05-16 16:13:30', 'attack_power'),
    (92, '50 Needles', 'Deals 50 damage with 100% hit rate and ignores defense.', '{"base_damage": 47}', 0, None, 'any', None, None, None, None, '2025-05-22 15:21:04', 'attack_power'),
    (93, '1,000 Needles', 'Deals 1,000 damage with 100% hit rate and ignores defense.', '{"base_damage": 1000}', 0, None, 'any', None, None, None, None, '2025-05-22 15:21:04', 'attack_power'),
]
# --- ability ↔ status‑effects -------------------------------------------------
MERGED_ABILITY_STATUS_EFFECTS: List[Tuple[int, int]] = [
    (10, 1),
    (10, 2),
    # new links
    (35, 3),  # Poison -> Poisoned
    (36, 8),  # Bio -> Bio
    (33, 17), # Haste -> Haste
    (34, 18), # Slow -> Slow
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
    (1, 'Warrior', 'A sturdy fighter with strong physical attacks.', 600, 40, 10, 5, 1, 99, 1, 10, 'https://cdn.discordapp.com/attachments/1362832151485354065/1364778448379318442/war.gif?ex=680c39fa&is=680ae87a&hm=80c89e0290ea5ad2432f2d9b265df190741f94309c2bca981ad1885af90671c4&', None, '2025-03-31 02:40:47'),
    (2, 'Berserker', 'A savage fighter who channels uncontrollable fury.', 600, 45, 10, 5, 1, 99, 1, 10, 'https://cdn.discordapp.com/attachments/1362832151485354065/1365296689379938355/Berserker.gif?ex=680ccb20&is=680b79a0&hm=aa06cfa2c7fb2fb30ffe9e4991d2dda0d4f9420587656a0ddc61b192372ad067&', None, '2025-04-03 07:05:45'),
    (3, 'Mystic Knight', 'A hybrid fighter that fuses magic to their blade.', 500, 40, 15, 5, 1, 99, 1, 10, 'https://cdn.discordapp.com/attachments/1362832151485354065/1365296718815432724/mystic.gif?ex=680ccb27&is=680b79a7&hm=3f8ad9a2b215496adbc6c0dfd328a9e30621c73e292c40f0fd5ebfb0025bd910&', None, '2025-04-03 07:05:45'),
    (4, 'Thief', 'A quick fighter who excels at stealing items.', 500, 45, 10, 5, 1, 99, 1, 10, 'https://cdn.discordapp.com/attachments/1362832151485354065/1365296784301363303/thief.gif?ex=680ccb37&is=680b79b7&hm=34ee2d981b968e6de51e52e85c51b3c16ed4ac71974df3ada3f305603d95b59a&', None, '2025-03-31 02:40:47'),
    (5, 'Green Mage', 'A powerful mage that manipulates time and space magics.', 500, 20, 20, 5, 1, 99, 1, 10, '', None, '2025-03-31 02:40:47'),
    (6, 'Dragoon', 'A lancer who can jump high and strike down foes.', 500, 40, 10, 5, 1, 99, 1, 10, '', None, '2025-03-31 02:40:47'),
    (7, 'Bard', 'A ranged attacker wielding a bow and musical influence.', 500, 45, 20, 5, 1, 99, 1, 10, '', None, '2025-04-03 07:05:45'),
    (8, 'White Mage', 'A healer who uses holy magic to restore and protect.', 500, 15, 20, 5, 1, 99, 1, 10, 'https://cdn.discordapp.com/attachments/1362832151485354065/1365296761723158538/whitemage.gif?ex=680ccb31&is=680b79b1&hm=cd94aeb45272086aac0e5c40507390e5738ef9ee419634a7eded75bf67ea91be&', None, '2025-04-03 07:05:45'),
    (9, 'Black Mage', 'A mage who uses destructive elemental spells.', 500, 15, 25, 5, 1, 99, 1, 10, 'https://cdn.discordapp.com/attachments/1362832151485354065/1364772285873127434/blm.gif?ex=680c343d&is=680ae2bd&hm=c3ce479bfd4cd9152348f3bf1d114ce29a63c7c04ac42c7d3ad845ab6bf51eda&', None, '2025-04-03 07:05:45'),
    (10, 'Geomancer', 'A sorcerer using environmental/elemental attacks.', 500, 15, 20, 5, 1, 99, 1, 10, 'https://cdn.discordapp.com/attachments/1362832151485354065/1372019632139145237/out.gif?ex=6825405b&is=6823eedb&hm=b0c22f7902cc76c50ce038d3c74dc16559a02e5e3d4262b5173592491bce32e6&', None, '2025-04-03 07:05:45'),
    (11, 'Gun Mage', 'A mage clad in blue armor who holds a magic-infused pistol.', 600, 30, 15, 5, 1, 99, 1, 10, 'https://cdn.discordapp.com/attachments/1362832151485354065/1372162446311165983/out.gif?ex=6825c55c&is=682473dc&hm=1e03aac8f24a02d80ee1f48c84a204d43207a75b55259d5bb8c461bb7af6f35e&', None, '2025-04-03 07:05:45'),
]
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
    (1, 1, 'An Unexpected Discovery', 'During what began as an ordinary raid, Sophia paused...',                           'https://the-demiurge.com/DemiDevUnit/images/intro/step1.png', '2025-03-31 02:40:47'),
    (2, 2, "Mog's Bold Venture",     'As the group hesitated, a tiny figure fluttered forward...',                        'https://the-demiurge.com/DemiDevUnit/images/intro/step2.png', '2025-03-31 02:40:47'),
    (3, 3, 'The Moogle Returns',     'Moments felt like hours as the group waited anxiously...',                           'https://the-demiurge.com/DemiDevUnit/images/intro/step3.png', '2025-03-31 02:40:47'),
    (4, 4, "Sophia's Decision",      'Sophia nodded solemnly...',                                                          'https://the-demiurge.com/DemiDevUnit/images/intro/step4.png', '2025-04-09 09:37:27'),
    (5, 5, 'The Call to Adventure',  'Returning to their Free Company house, Sophia gathered everyone...',                'https://the-demiurge.com/DemiDevUnit/images/intro/step5.png', '2025-04-09 09:37:27')
]

# --- room templates -----------------------------------------------------------
MERGED_ROOM_TEMPLATES: List[Tuple] = [
    (1,  'safe',          'Moss Room',          'You do not notice anything of importance, the area appears to be safe.',                          'https://the-demiurge.com/DemiDevUnit/images/rooms/roomtypemoss.png',            None,'2025-03-31 02:40:47'),
    (2,  'safe',          'Mystic Room',        'You do not notice anything of importance, the area appears to be safe.',                          'https://the-demiurge.com/DemiDevUnit/images/rooms/roomtypemystic.png',          None,'2025-03-31 02:40:47'),
    (3,  'safe',          'Crystal Tunnel',     'You do not notice anything of importance, the area appears to be safe.',                          'https://the-demiurge.com/DemiDevUnit/images/rooms/crystals.png',                None,'2025-03-31 02:40:47'),
    (4,  'safe',          'Bridge',             'You do not notice anything of importance, the area appears to be safe.',                          'https://the-demiurge.com/DemiDevUnit/images/rooms/roomtypebridge.png',          None,'2025-04-09 20:22:14'),
    (5,  'safe',          'Magicite',           'You do not notice anything of importance, the area appears to be safe.',                          'https://the-demiurge.com/DemiDevUnit/images/rooms/roomtypemagicite.png',        None,'2025-04-09 20:22:19'),
    (6,  'safe',          'Rainbow Crystal',    'You do not notice anything of importance, the area appears to be safe.',                          'https://the-demiurge.com/DemiDevUnit/images/rooms/rainbowcrystal.png',          None,'2025-04-09 20:22:27'),
    (7,  'safe',          'Aetheryte',          'You do not notice any hostile presence; instead you see a naturally growing Aetheryte cluster.',   'https://the-demiurge.com/DemiDevUnit/images/rooms/roomtypeaetheryte.png',       None,'2025-04-09 20:22:27'),
    (8,  'monster',       'You Sense A Hostile Presence...', 'An enemy appears upon entering the area...',                                         '', None,'2025-03-31 02:40:47'),
    (9,  'staircase_up',  'Staircase Up',       'A staircase leading upward to the next level.',                                                   'https://the-demiurge.com/DemiDevUnit/images/rooms/stairs_up.png',               None,'2025-04-19 13:55:00'),
    (10, 'staircase_down','Staircase Down',     'A staircase leading downward to the lower level.',                                               'https://the-demiurge.com/DemiDevUnit/images/rooms/stairs_down.png',             None,'2025-04-19 13:55:00'),
    (11, 'exit',          'Dungeon Exit',       '(Implemented in next patch)',                                                                    'https://the-demiurge.com/DemiDevUnit/images/backintro.png',                     None,'2025-03-30 21:40:47'),
    (12, 'item',          'Treasure Room',      'A treasure chest sits in the corner.',                                                            'https://the-demiurge.com/DemiDevUnit/images/backintro.png',                     None,'2025-03-30 21:40:47'),
    (13, 'boss',          'Boss Lair',          'A grand chamber with ominous decorations.',                                                       'https://the-demiurge.com/DemiDevUnit/images/backintro.png',                     None,'2025-03-30 21:40:47'),
    (14, 'trap',          'Trap Room',          'The floor is riddled with hidden traps.',                                                         'https://the-demiurge.com/DemiDevUnit/images/backintro.png',                     None,'2025-03-30 21:40:47'),
    (15, 'shop',          'Shop Room',          'A traveling moogle is seen hiding...',                                                            'https://the-demiurge.com/DemiDevUnit/images/shop/stiltzkin.gif',                None,'2025-03-30 21:40:47'),
    (16, 'illusion',      'Illusion Chamber',   'The room shimmers mysteriously...',                                                               'https://the-demiurge.com/DemiDevUnit/images/rooms/roomtypeillusion.png',        None,'2025-03-30 21:40:47'),
    (17, 'locked',        'Locked Door',        'A heavy locked door. You need a key.',                                                            'https://the-demiurge.com/DemiDevUnit/images/rooms/locked.png',                  None,'2025-04-19 13:55:00'),
    (18, 'chest_unlocked','Unlocked Chest',     'The chest lies open, its contents revealed.', 'https://your.cdn/path/chest_unlocked.png', None, '2025-04-23 18:00:00'),
    (19, 'illusion', 'Illusion Chamber', 'Shifting shadows form the shapes of countless foes.',
        'https://the-demiurge.com/DemiDevUnit/images/rooms/roomtypeillusion.png',
        None, '2025-04-24 12:00:00'),
    (20, 'illusion',  'Illusion Chamber', 'Several doors materialise from thin air, each beckoning.',
        'https://the-demiurge.com/DemiDevUnit/images/rooms/roomtypeillusion.png',
        None, '2025-04-24 12:00:00'),
    (21, 'illusion',  'Illusion Chamber', 'Glowing elemental crystals illuminate the chamber.',
        'https://the-demiurge.com/DemiDevUnit/images/rooms/roomtypeillusion.png',
        None, '2025-04-24 12:00:00'),
    (22, 'illusion',  'Empty Illusion Chamber', 'The illusions fade away leaving only an empty space.',
        'https://the-demiurge.com/DemiDevUnit/images/rooms/illusion_empty.png',
        None, '2025-04-24 12:00:00')
]

# --- crystal templates --------------------------------------------------------
MERGED_CRYSTAL_TEMPLATES: List[Tuple] = []

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
    (1, 1, 'weak', 1.5),
    (2, 3, 'absorb', -1.0),
    (3, 2, 'resist', 0.5)
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
    (1, 'main', '', 'Welcome to AdventureBot, a classic turn based dungeon crawler...', 'https://the-demiurge.com/DemiDevUnit/images/embed.png', 'AdventureBot v3.0.2 is now Live!', None, '2025-03-31 03:43:19'),
    (
        2,
        'tutorial',
        'Starting A Game',
        '\nSimply click the **New Game** button to create a new game thread.\n\nThis will add you to the **Queue** system inside the thread, along with anyone else who wants to join.\n\n- Only the players who join the game session will see the private thread and be added to it automatically.\n\n- Up to 6 players can join via the LFG post in the Game Channel by clicking the Join button. \n\n- Additional players will be shown in the **Queue List** in the thread.\n\nWhen the creator is ready they may click **Start Game** to lock in the emount of players playing.\n\n\n',
        'https://cdn.discordapp.com/attachments/1362832151485354065/1373622234865733652/Screenshot_2025-05-18_at_6.14.47_AM.png?ex=682b14e5&is=6829c365&hm=b91a3c24ed88f1f493db9a8f61473923e316e284782ab15bd565f6a82ac25966&',
        'Coming Soon...',
        1,
        '2025-04-15 02:50:10',
    ),
    (
        3,
        'tutorial',
        'Choose Class and Difficulty',
        'Once the Session Creator clicks the Start Game button they can choose their class and difficulty level.\n\n- Selecting **Easy** will generate up to 2 floors with a rare chance to spawn a basement floor. In this mode most harder enemeis are removed from generation.\n\n- Choosing **Medium** difficulty will generate up to 4 floors with at least 2 and a rare chance to spawn a basement. In this mode harder enemies spawn along side easy ones during generation.\n\n- Selecting **Hard** is exactly what you think it is. With up to 4 floors and higher spawn chances on more difficult enemies and less vendor shops and item drops.\n\n- **Crazy Catto** is the most difficult of challenges and well... you\'d be a crazy catto to try it.',
        'https://cdn.discordapp.com/attachments/1362832151485354065/1373622403455778848/Screenshot_2025-05-18_at_6.19.11_AM.png?ex=682b150d&is=6829c38d&hm=045419693ca1ecd758f7ecf5c7208ca4da321622636b908da9e15c99f97dde61&',
        'Coming Soon...',
        2,
        '2025-04-17 03:45:05',
    ),
]
MERGED_HUB_BUTTONS: List[Tuple] = []

# --- status effects -----------------------------------------------------------
MERGED_STATUS_EFFECTS: List[Tuple] = [
    (1, 'Attack Up', 'buff', '⚔️🔼', '2025-03-31 02:40:47', 0, 0),
    (2, 'Defense Down', 'debuff', '🛡️🔽', '2025-03-31 02:40:47', 0, 0),
    (3, 'Poisoned', 'debuff', '☣️', '2025-03-31 02:40:47', 0, 0),
    (4, 'Regen', 'buff', '❤️🔄', '2025-03-31 02:40:47', 0, 0),
    (5, 'Stun', 'debuff', '🌀', '2025-03-31 02:40:47', 0, 0),
    (6, 'Burn', 'debuff', '🔥', '2025-03-31 02:40:47', 0, 0),
    (7, 'Freeze', 'debuff', '❄️', '2025-03-31 02:40:47', 0, 0),
    (8, 'Bio', 'debuff', '☣️', '2025-05-23 00:10:16', 0, 0),
    (9, 'Silence', 'debuff', None, '2025-05-24 21:24:50', 0, 0),
    (10, 'Evasion Up', 'buff', None, '2025-05-24 21:25:42', 0, 0),
    (11, 'Blind', 'debuff', None, '2025-05-24 21:25:42', 0, 0),
    (12, 'Defense Up', 'buff', '🛡️🔼', '2025-05-24 21:28:44', 0, 0),
    (13, 'Mag.Def Up', 'buff', '🔮🛡️🔼', '2025-05-24 21:28:44', 0, 0),
    (14, 'Mag.Def Down', 'debuff', '🔮🛡️🔽', '2025-05-24 21:33:23', 0, 0),
    (15, 'Berserk', 'neutral', None, '2025-05-24 21:34:39', 0, 0),
    (16, 'Magic Up', 'buff', '🔮🔼', '2025-05-24 21:36:05', 0, 0),
    (17, 'Haste', 'buff', '⏱️🔼', '2025-05-24 21:36:06', 0, 0),
    (18, 'Slow', 'debuff', '⏳🔽', '2025-05-24 21:36:07', 0, 0),
]
# --- floor → room placement rules seed data -------------------------------------------------
# (difficulty_name, floor_number, room_type, chance, max_per_floor)
MERGED_FLOOR_ROOM_RULES: List[Tuple[str, int, str, float, int]] = [
    # Example entries; replace these with your real tuning values:
    ("Easy",  1, "safe",           0.50, 20),
    ("Easy",  1, "monster",        0.30, 10),
    ("Easy",  1, "item",           0.10,  5),
    ("Easy",  1, "locked",         0.05,  2),
    ("Easy",  1, "staircase_up",   0.05,  1),
    ("Easy",  None, "boss",        0.0,   1),
    ("Medium", None, "boss",       0.0,   1),
    ("Hard",  None, "boss",        0.0,   1),
    ("Crazy Catto", None, "boss",  0.0,   1),
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
                'staircase_up','staircase_down','exit','locked'
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
            enemies_defeated INT DEFAULT 0,
            rooms_visited    INT DEFAULT 0,
            gil_earned       INT DEFAULT 0,
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
                'staircase_up','staircase_down','exit','locked','chest_unlocked'
            ) NOT NULL,
            template_name VARCHAR(100) NOT NULL,
            description   TEXT,
            image_url     VARCHAR(255),
            default_enemy_id INT,
            created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''',
    # ---------- crystal_templates ----------
    'crystal_templates': '''
        CREATE TABLE IF NOT EXISTS crystal_templates (
            template_id   INT AUTO_INCREMENT PRIMARY KEY,
            element_id    INT NOT NULL,
            name          VARCHAR(100) NOT NULL,
            description   TEXT,
            image_url     VARCHAR(255),
            created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
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
            room_type ENUM(
                'safe','monster','item','shop','boss','trap','illusion',
                'staircase_up','staircase_down','exit','locked','chest_unlocked'
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
            template_id    room_templates.template_id,
            created_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (template_id)
                REFERENCES room_templates(template_id) ON DELETE CASCADE
        )
    ''',
            # in TABLES:
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
            enemy_id   INT NOT NULL,
            element_id INT NOT NULL,
            relation   ENUM('weak','resist','absorb','immune','normal') NOT NULL DEFAULT 'normal',
            multiplier FLOAT NOT NULL DEFAULT 1.0,
            PRIMARY KEY (enemy_id, element_id),
            FOREIGN KEY (enemy_id)  REFERENCES enemies(enemy_id)   ON DELETE CASCADE,
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
            bosses_defeated INT DEFAULT 0,
            rooms_visited    INT DEFAULT 0,
            score_value      INT DEFAULT 0,
            difficulty       VARCHAR(50),
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
    'abilities',
    'classes',
    'levels',
    'class_abilities',
    'sessions',
    'session_players',
    'players',
    'floors',
    'room_templates',
    'crystal_templates',
    'npc_vendors',
    'items',
    'npc_vendor_items',
    'session_vendor_instances',
    'session_vendor_items',
    'rooms',
    'key_items',
    'treasure_chests',
    'chest_def_rewards',
    'treasure_chest_instances',
    'chest_instance_rewards',
    'enemies',
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
    if not table_is_empty(cur, "elements"):
        logger.info("elements already populated – skipping")
        return
    cur.executemany(
        "INSERT INTO elements (element_name, created_at) VALUES (%s, %s)",
        [row[1:] for row in MERGED_ELEMENTS]
    )
    logger.info("Inserted elements.")

def insert_abilities_and_classes(cur):
    logger.info("Checking abilities seed data…")
    if table_is_empty(cur, "abilities"):
        cur.executemany(
            """
            INSERT INTO abilities
              (ability_name, description, effect, cooldown, icon_url,
               target_type, special_effect, element_id,
               status_effect_id, status_duration, created_at, scaling_stat)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
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

    logger.info("Checking status_effects seed data…")
    if table_is_empty(cur, "status_effects"):
        cur.executemany(
            """
            INSERT INTO status_effects
              (effect_name,effect_type,icon_url,created_at,value,duration)
            VALUES (%s,%s,%s,%s,%s,%s)
            """,
            [row[1:] for row in MERGED_STATUS_EFFECTS]
        )
        logger.info("Inserted status_effects.")
    else:
        logger.info("status_effects already populated – skipping")

    logger.info("Checking ability_status_effects links…")
    cur.execute("SELECT ability_id, effect_id FROM ability_status_effects")
    existing = set(cur.fetchall())
    missing = [row for row in MERGED_ABILITY_STATUS_EFFECTS if tuple(row) not in existing]
    if missing:
        cur.executemany(
            "INSERT INTO ability_status_effects (ability_id,effect_id) VALUES (%s,%s)",
            missing,
        )
        logger.info("Inserted ability_status_effects links.")
    else:
        logger.info("ability_status_effects already populated – skipping")

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
           default_enemy_id, created_at)
        VALUES (%s,%s,%s,%s,%s,%s)
        """,
        [row[1:] for row in MERGED_ROOM_TEMPLATES]
    )
    logger.info("Inserted room_templates.")

def insert_crystal_templates(cur):
    logger.info("Checking crystal_templates seed data…")
    if not table_is_empty(cur, "crystal_templates"):
        logger.info("crystal_templates already populated – skipping")
        return
    # No default crystal templates yet
    logger.info("No crystal_templates seed data to insert.")

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
        "INSERT INTO enemy_resistances (enemy_id,element_id,relation,multiplier) VALUES (%s,%s,%s,%s)",
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
              (effect_name,effect_type,icon_url,created_at,value,duration)
            VALUES (%s,%s,%s,%s,%s,%s)
            """,
            [row[1:] for row in MERGED_STATUS_EFFECTS]
        )
        logger.info("Inserted status_effects.")
    else:
        logger.info("status_effects already populated – skipping")

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


def _parse_columns(create_sql: str) -> list[tuple[str, str]]:
    """Extract column definitions from a ``CREATE TABLE`` statement."""
    inside = create_sql.split("(", 1)[1].rsplit(")", 1)[0]
    columns = []
    for line in inside.splitlines():
        line = line.strip().rstrip(",")
        if not line or line.upper().startswith(("PRIMARY KEY", "FOREIGN KEY", "REFERENCES")):
            continue
        m = re.match(r"`?([A-Za-z_][A-Za-z0-9_]*)`?\s+(.*)", line)
        if m:
            columns.append((m.group(1), m.group(2)))
    return columns


def ensure_table_columns(cur, table_name: str, create_sql: str) -> None:
    """Add any missing columns for ``table_name`` using ``create_sql``."""
    for col_name, definition in _parse_columns(create_sql):
        cur.execute(f"SHOW COLUMNS FROM {table_name} LIKE %s", (col_name,))
        if not cur.fetchone():
            logger.info("Adding missing column: %s.%s", table_name, col_name)
            cur.execute(f"ALTER TABLE {table_name} ADD {col_name} {definition}")


def ensure_all_columns(cur) -> None:
    """Ensure every table has all expected columns."""
    for tbl in TABLE_ORDER:
        ensure_table_columns(cur, tbl, TABLES[tbl])

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

                # ensure all columns exist
                ensure_all_columns(cur)

                # ── seed data (order matters) ──────────────────────────────────
                insert_difficulties(cur)
                insert_floor_room_rules(cur)
                insert_elements(cur)
                insert_abilities_and_classes(cur)
                insert_levels(cur)
                insert_intro_steps(cur)
                insert_room_templates(cur)
                insert_crystal_templates(cur)
                insert_npc_vendors(cur)
                insert_items(cur)
                insert_enemies_and_abilities(cur)
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
