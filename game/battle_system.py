import discord
from discord.ext import commands
import mysql.connector
import json
import time
import logging
import asyncio
import random
from utils.status_engine   import StatusEffectEngine
from utils.ability_engine import AbilityEngine
from utils.helpers import load_config
from typing import Any, Dict, List, Optional, Set, Tuple
from utils.ui_helpers import (
    create_cooldown_bar,
    create_health_bar,
    create_progress_bar,
    format_status_effects,
    get_emoji_for_room_type,
)
from models.session_models import SessionPlayerModel

logger = logging.getLogger("BattleSystem")
logger.setLevel(logging.DEBUG)


class BattleSystem(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.config = load_config()
        self.db_config = self.config["mysql"]
        self.embed_manager: Optional[commands.Cog] = self.bot.get_cog("EmbedManager")
        # AbilityEngine handles ALL ability logic & damage formulas
        self.ability = AbilityEngine(self.db_connect, self.config.get("damage_variance", 0.0))

    # --------------------------------------------------------------------- #
    #                               Helpers                                 #
    # --------------------------------------------------------------------- #
    def _append_battle_log(self, session_id: int, line: str):
        """Called by StatusEffectEngine to append a line to the battle log."""
        gm = self.bot.get_cog("GameMaster")
        gm.append_game_log(session_id, line)

    def db_connect(self):
        try:
            return mysql.connector.connect(**self.db_config)
        except Exception as e:
            logger.error("DB connection error in BattleSystem: %s", e)
            raise

    def _get_player_class_name(self, session_id: int, player_id: int) -> Optional[str]:
        conn = self.db_connect()
        try:
            cur = conn.cursor(dictionary=True)
            cur.execute(
                """
                SELECT c.class_name
                  FROM players p
                  JOIN classes c ON c.class_id = p.class_id
                 WHERE p.session_id = %s AND p.player_id = %s
                """,
                (session_id, player_id),
            )
            row = cur.fetchone()
            return row["class_name"] if row else None
        finally:
            cur.close()
            conn.close()

    def _get_player_level(self, session_id: int, player_id: int) -> Optional[int]:
        conn = self.db_connect()
        try:
            cur = conn.cursor()
            cur.execute(
                "SELECT level FROM players WHERE session_id=%s AND player_id=%s",
                (session_id, player_id),
            )
            row = cur.fetchone()
            return row[0] if row else None
        finally:
            cur.close()
            conn.close()

    def _get_player_mp(self, session_id: int, player_id: int) -> Optional[Dict[str, int]]:
        conn = self.db_connect()
        try:
            cur = conn.cursor(dictionary=True)
            cur.execute(
                "SELECT mp, max_mp FROM players WHERE session_id=%s AND player_id=%s",
                (session_id, player_id),
            )
            return cur.fetchone()
        finally:
            cur.close()
            conn.close()

    def _set_player_mp(self, session_id: int, player_id: int, mp: int) -> None:
        conn = self.db_connect()
        try:
            cur = conn.cursor()
            cur.execute(
                "UPDATE players SET mp=%s WHERE session_id=%s AND player_id=%s",
                (mp, session_id, player_id),
            )
            conn.commit()
        finally:
            cur.close()
            conn.close()

    def _get_eidolon_for_enemy(self, enemy_id: int) -> Optional[Dict[str, Any]]:
        conn = self.db_connect()
        try:
            cur = conn.cursor(dictionary=True)
            cur.execute(
                "SELECT * FROM eidolons WHERE enemy_id=%s",
                (enemy_id,),
            )
            return cur.fetchone()
        finally:
            cur.close()
            conn.close()

    def _get_eidolon(self, eidolon_id: int) -> Optional[Dict[str, Any]]:
        conn = self.db_connect()
        try:
            cur = conn.cursor(dictionary=True)
            cur.execute(
                "SELECT * FROM eidolons WHERE eidolon_id=%s",
                (eidolon_id,),
            )
            return cur.fetchone()
        finally:
            cur.close()
            conn.close()

    def _get_eidolon_level(self, session_id: int, player_id: int, eidolon_id: int) -> Optional[int]:
        conn = self.db_connect()
        try:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT level
                  FROM player_eidolons
                 WHERE session_id=%s AND player_id=%s AND eidolon_id=%s
                """,
                (session_id, player_id, eidolon_id),
            )
            row = cur.fetchone()
            return row[0] if row else None
        finally:
            cur.close()
            conn.close()

    def _get_level_growth(self, level: int) -> Dict[str, Any]:
        conn = self.db_connect()
        try:
            cur = conn.cursor(dictionary=True)
            cur.execute("SELECT * FROM levels WHERE level=%s", (level,))
            row = cur.fetchone()
            return row or {}
        finally:
            cur.close()
            conn.close()

    def _calculate_eidolon_stats(self, eidolon: Dict[str, Any], level: int) -> Dict[str, Any]:
        growth = self._get_level_growth(level)
        mapping = {
            "base_hp": "hp_increase",
            "base_attack": "attack_increase",
            "base_magic": "magic_increase",
            "base_defense": "defense_increase",
            "base_magic_defense": "magic_defense_increase",
            "base_accuracy": "accuracy_increase",
            "base_evasion": "evasion_increase",
            "base_speed": "speed_increase",
        }
        stats = {}
        for base_key, growth_key in mapping.items():
            base_value = eidolon.get(base_key, 0)
            growth_factor = growth.get(growth_key, 0) or 0
            stats[base_key.replace("base_", "")] = int(base_value * (1 + growth_factor * (level - 1)))
        stats["hp"] = stats.get("hp", eidolon.get("base_hp", 0))
        stats["max_hp"] = stats.get("hp", eidolon.get("base_hp", 0))
        return stats

    def _normalize_se(self, raw: Dict[str,Any]) -> Dict[str,Any]:
        """
        Turn raw engine output into exactly the 3 keys our UI helper wants:
          - icon (str)
          - effect_name (str)
          - remaining (int)
        plus anything else your engine attaches (damage_per_turn, etc.)
        """
        out = {
            "effect_id":   raw.get("effect_id"),
            "effect_name": raw.get("effect_name"),
            "remaining":   raw.get("remaining", raw.get("remaining_turns", 0)),
            "icon":        raw.get("icon") or raw.get("icon_url",""),
            # preserve any extra tick fields
            **{k: v for k,v in raw.items() if k in ("damage_per_turn","heal_per_turn")}
        }
        out["target"] = raw.get("target", "self")
        return out
    # --------------------------------------------------------------------- #
    #                     Room / Template utilities                         #
    # --------------------------------------------------------------------- #
    async def _get_random_safe_template(self) -> Optional[Dict[str, Any]]:
        try:
            conn = self.db_connect()
            cursor = conn.cursor(dictionary=True, buffered=True)
            cursor.execute(
                """
                SELECT image_url, description
                FROM room_templates
                WHERE room_type = 'safe'
                ORDER BY RAND()
                LIMIT 1
                """
            )
            template = cursor.fetchone()
            cursor.close()
            conn.close()
            logger.debug("Random safe template fetched: %s", template)
            return template
        except Exception as e:
            logger.error("Error fetching random safe template: %s", e)
            return None

    async def _replace_monster_room_with_safe(self, session: Any, floor_id: int, x: int, y: int) -> int:
        try:
            conn = self.db_connect()
            cursor = conn.cursor(dictionary=True, buffered=True)
            cursor.execute(
                """
                SELECT room_id, floor_id, exits
                FROM rooms
                WHERE session_id = %s
                  AND floor_id = %s
                  AND coord_x = %s
                  AND coord_y = %s
                  AND room_type IN ('monster','miniboss','boss')
                """,
                (session.session_id, floor_id, x, y),
            )
            old_room = cursor.fetchone()
            if not old_room:
                cursor.close(); conn.close(); return 0
            old_exits, old_room_id = old_room["exits"], old_room["room_id"]
            cursor.close(); conn.close()
        except Exception as e:
            logger.error("Error fetching old room: %s", e)
            return 0

        template = await self._get_random_safe_template()
        if not template:
            logger.error("No safe template found; cannot replace monster room.")
            return 0

        try:
            conn = self.db_connect()
            cursor = conn.cursor(buffered=True)
            cursor.execute("DELETE FROM rooms WHERE room_id = %s", (old_room_id,))
            cursor.execute(
                """
                INSERT INTO rooms (
                    session_id, floor_id, coord_x, coord_y,
                    room_type, image_url, description, exits
                ) VALUES (
                    %s, %s, %s, %s,
                    'safe', %s, %s, %s
                )
                """,
                (
                    session.session_id,
                    floor_id,
                    x,
                    y,
                    template["image_url"],
                    template["description"],
                    old_exits,
                ),
            )
            conn.commit()
            cursor.close()
            conn.close()
            logger.debug("Replaced monster room (id=%s) with safe room.", old_room_id)
            return 1
        except Exception as e:
            logger.error("Error replacing monster room with safe room: %s", e)
            return 0

    async def get_enemy_for_room(self, session: Any, floor_id: int, x: int, y: int) -> Optional[dict]:
        try:
            conn = self.db_connect()
            cursor = conn.cursor(dictionary=True)
            cursor.execute(
                "SELECT difficulty FROM sessions WHERE session_id = %s LIMIT 1",
                (session.session_id,),
            )
            row = cursor.fetchone()
            if not row: cursor.close(); conn.close(); return None
            difficulty = (row["difficulty"] or "").capitalize()

            cursor.execute(
                """
                SELECT room_type
                FROM rooms
                WHERE session_id = %s
                  AND floor_id = %s
                  AND coord_x = %s
                  AND coord_y = %s
                """,
                (session.session_id, floor_id, x, y),
            )
            room = cursor.fetchone()
            if not room: cursor.close(); conn.close(); return None

            expected_role = "miniboss" if room["room_type"] == "miniboss" else "normal"

            cursor.execute(
                """
                SELECT
                    enemy_id, enemy_name, hp, max_hp,
                    attack_power, magic_power, defense, magic_defense,
                    accuracy, evasion, xp_reward, gil_drop,
                    loot_item_id, loot_quantity, image_url, role
                FROM enemies
                WHERE difficulty = %s
                  AND role = %s
                ORDER BY RAND()
                LIMIT 1
                """,
                (difficulty, expected_role),
            )
            enemy = cursor.fetchone()
            cursor.close(); conn.close()
            logger.debug("Selected enemy for %s (%s): %s", room["room_type"], expected_role, enemy)
            return enemy
        except Exception as e:
            logger.error("Error in get_enemy_for_room: %s", e)
            return None

    async def get_enemy_by_id(self, enemy_id: int) -> Optional[dict]:
        try:
            conn = self.db_connect()
            cursor = conn.cursor(dictionary=True)
            cursor.execute(
                """
                SELECT enemy_id, enemy_name, hp, max_hp,
                       attack_power, magic_power, defense, magic_defense,
                       accuracy, evasion, xp_reward, gil_drop,
                       loot_item_id, loot_quantity, image_url, role
                FROM enemies
                WHERE enemy_id = %s
                LIMIT 1
                """,
                (enemy_id,),
            )
            enemy = cursor.fetchone()
            cursor.close(); conn.close()
            logger.debug("Fetched enemy by id %s: %s", enemy_id, enemy)
            return enemy
        except Exception as e:
            logger.error("Error in get_enemy_by_id: %s", e)
            return None

    async def activate_trance(self, session: Any, player_id: int) -> None:
        conn = self.db_connect()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT ct.trance_id, ct.trance_name, ct.duration_turns
            FROM class_trances ct
            JOIN players p ON p.class_id = ct.class_id
            WHERE p.session_id = %s
              AND p.player_id  = %s
            LIMIT 1
            """,
            (session.session_id, player_id),
        )
        trance = cursor.fetchone()
        cursor.close(); conn.close()
        if not trance:
            return

        if not hasattr(session, "trance_states") or session.trance_states is None:
            session.trance_states = {}

        session.trance_states[player_id] = {
            "trance_id": trance["trance_id"],
            "name":      trance["trance_name"],
            "remaining": trance["duration_turns"],
            "max":       trance["duration_turns"],
        }
        session.game_log.append(f"✨ <@{player_id}> has entered **{trance['trance_name']}**!")

    # --------------------------------------------------------------------- #
    #                     Cool‑down / session helpers                       #
    # --------------------------------------------------------------------- #
    def get_ability_icon(self, ability: Dict[str, Any]) -> Optional[str]:
        return ability.get("icon_url")

    def reduce_player_cooldowns(self, session: Any, player_id: int) -> None:
        if not hasattr(session, "ability_cooldowns") or session.ability_cooldowns is None:
            session.ability_cooldowns = {}
        cds = session.ability_cooldowns.get(player_id, {})

        conn = self.db_connect()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            "SELECT speed, class_id FROM players WHERE player_id = %s AND session_id = %s",
            (player_id, session.session_id),
        )
        player = cursor.fetchone()
        cursor.close(); conn.close()
        if not player:
            return

        player_speed = player["speed"]
        conn = self.db_connect()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            "SELECT base_speed FROM classes WHERE class_id = %s",
            (player["class_id"],),
        )
        class_data = cursor.fetchone()
        cursor.close(); conn.close()

        base = class_data["base_speed"] if class_data else 10
        multiplier = player_speed / base
        for aid in list(cds):
            cds[aid] = max(cds[aid] - multiplier, 0)

        session.ability_cooldowns[player_id] = cds

    def _append_elemental_log(self, session: Any, result: Any, target_name: str) -> None:
        relation = getattr(result, "element_relation", None)
        if not relation:
            return
        if relation == "weak":
            session.game_log.append("It's super effective!")
        elif relation == "resist":
            session.game_log.append("It's not very effective...")
        elif relation == "immune":
            session.game_log.append("It has no effect.")
        elif relation == "absorb":
            session.game_log.append(f"{target_name} absorbs the element!")

    def get_session(self, channel_id: int) -> Optional[Any]:
        mgr = self.bot.get_cog("SessionManager")
        if not mgr:
            logger.error("SessionManager cog not available.")
            return None
        return mgr.get_session(channel_id)

    def choose_enemy_ability(self, session: Any, enemy: Dict[str,Any]) -> Optional[Dict[str,Any]]:
        """
        Pick one of this enemy’s abilities, respecting:
          – Silence status on enemy_effects
          – Per‐turn cooldowns (–1 each turn, +cooldown on use)
          – Healing only when hp% ≤ heal_threshold_pct & can_heal=1
          – Weighted random choice by ea.weight
        Returns None to fall back to a plain Attack.
        """
        eid = enemy["enemy_id"]

        # 1) If silenced, no spells at all
        if any(eff.get("effect_name") == "Silence"
               for eff in session.battle_state.get("enemy_effects", [])):
            return None

        # 2) Decrement this enemy’s cooldowns by 1
        session.ability_cooldowns = getattr(session, "ability_cooldowns", {}) or {}
        cds = session.ability_cooldowns.get(eid, {})
        for aid in list(cds):
            cds[aid] = max(cds[aid] - 1, 0)
        session.ability_cooldowns[eid] = cds

        # 3) Load all enemy_abilities + ability metadata
        conn = self.db_connect()
        cur  = conn.cursor(dictionary=True)
        cur.execute("""
            SELECT ea.ability_id, ea.weight,
                   ea.can_heal, ea.heal_threshold_pct,
                   ea.heal_amount_pct,
                   a.ability_name, a.effect, a.cooldown,
                   a.special_effect, a.target_type, a.icon_url,
                   a.element_id
              FROM enemy_abilities ea
              JOIN abilities a USING (ability_id)
             WHERE ea.enemy_id = %s
        """, (eid,))
        rows = cur.fetchall()
        cur.close(); conn.close()

        # 4) Filter out on‐cooldown & out‐of‐threshold heals
        pool = []
        pct  = enemy["hp"] / enemy["max_hp"]
        for r in rows:
            aid = r["ability_id"]
            if cds.get(aid, 0) > 0:
                continue
            if r["can_heal"] and pct > (r["heal_threshold_pct"] or 0):
                continue
            pool.append(r)

        if not pool:
            return None

        # 5) Weighted random pick
        total = sum(r["weight"] for r in pool)
        pick  = random.uniform(0, total)
        upto  = 0.0
        for r in pool:
            upto += r["weight"]
            if pick <= upto:
                # apply its cooldown
                cd = r.get("cooldown") or 0
                if cd > 0:
                    cds[r["ability_id"]] = cd
                    session.ability_cooldowns[eid] = cds
                return r

        return None

    # --------------------------------------------------------------------- #
    #                           Battle sequence                             #
    # --------------------------------------------------------------------- #
    async def handle_enemy_defeat(self, interaction: discord.Interaction, session: Any, enemy: dict) -> None:
        session.victory_pending = True
        session.victory_embed_sent = False
        session.last_victory_enemy = dict(enemy)
        session.current_enemy = None
        gm = self.bot.get_cog("GameMaster")
        if gm:
            gm.append_game_log(session.session_id, f"{enemy['enemy_name']} was defeated!")
        xp = enemy.get("xp_reward", 0) or 0
        if xp and session:
            summoned = getattr(session, "summoned_eidolons", {}) or {}
            for eidolon_id in summoned.get(session.current_turn, set()):
                SessionPlayerModel.award_eidolon_experience(
                    session.session_id,
                    session.current_turn,
                    eidolon_id,
                    int(xp * 0.75),
                )
            summoned.pop(session.current_turn, None)
            session.summoned_eidolons = summoned
        if xp and gm:
            await gm.award_experience(session.current_turn, session.session_id, xp)
        if xp and session:
            session.game_log.append(f"<@{session.current_turn}> gained {xp} XP.")

        conn = self.db_connect()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            "SELECT coord_x, coord_y, current_floor_id FROM players WHERE player_id = %s AND session_id = %s",
            (session.current_turn, session.session_id),
        )
        pd = cursor.fetchone()
        cursor.close(); conn.close()

        if pd:
            await self._replace_monster_room_with_safe(
                session, pd["current_floor_id"], pd["coord_x"], pd["coord_y"]
            )
            conn = self.db_connect()
            cursor = conn.cursor(dictionary=True)
            cursor.execute(
                """
                SELECT r.*, f.floor_number
                FROM rooms r
                JOIN floors f ON f.floor_id = r.floor_id
                WHERE r.session_id = %s
                  AND r.floor_id = %s
                  AND r.coord_x = %s
                  AND r.coord_y = %s
                """,
                (session.session_id, pd["current_floor_id"], pd["coord_x"], pd["coord_y"]),
            )
            new_room = cursor.fetchone()
            cursor.close(); conn.close()
            if new_room:
                session.game_state = new_room

        # ─── Completely tear down combat state ─────────────────────────
        # 1) Clear out any lingering player‐side DoT/status effects
        if session.battle_state:
            session.battle_state.pop("player_effects", None)
            session.battle_state.pop("enemy_effects", None)

        # 2) Call your normal clear (in case it resets other bits)
        session.clear_battle_state()

        # ─── Now show the “Victory!” embed ─────────────────────────────
        await self.display_victory_embed(interaction, session, enemy)

    async def _check_eidolon_attunement(self, interaction: discord.Interaction, session: Any, enemy: dict) -> bool:
        if enemy.get("role") != "eidolon":
            return False
        threshold = max(1, int(enemy["max_hp"] * 0.1))
        if enemy["hp"] > threshold:
            return False
        eidolon = self._get_eidolon_for_enemy(enemy["enemy_id"])
        if not eidolon:
            return False
        session.eidolon_attuned = getattr(session, "eidolon_attuned", set())
        key = (session.session_id, session.current_turn, eidolon["eidolon_id"])
        if key in session.eidolon_attuned:
            return False

        SessionPlayerModel.unlock_eidolon(session.session_id, session.current_turn, eidolon["eidolon_id"])
        session.eidolon_attuned.add(key)
        session.game_log.append(f"{eidolon['name']} acknowledges your strength and joins your journey!")
        msg = (
            f"✨ **{eidolon['name']}**: *Your strength is proven. I shall fight at your side.*"
        )
        if interaction.response.is_done():
            await interaction.followup.send(msg, ephemeral=True)
        else:
            await interaction.response.send_message(msg, ephemeral=True)
        await self.handle_enemy_defeat(interaction, session, enemy)
        return True

    async def start_battle(self,
                            interaction: discord.Interaction,
                            player_id: int,
                            enemy: Dict[str, Any]) -> None:
        mgr = self.bot.get_cog("SessionManager")
        if not mgr:
            return await interaction.response.send_message("❌ SessionManager not available.", ephemeral=True)
        session = mgr.get_session(interaction.channel.id)
        if not session:
            return await interaction.response.send_message("❌ No session found.", ephemeral=True)

        session.battle_state     = {"enemy": enemy, "player_effects": [], "enemy_effects": []}
        session.victory_pending = False
        session.victory_embed_sent = False
        session.last_victory_enemy = None

        # 2) Load & normalize any buffs the player already had
        raw_buffs = SessionPlayerModel.get_status_effects(
            session.session_id,
            player_id
        )
        session.battle_state["player_effects"] = [
            self._normalize_se(raw_se)
            for raw_se in raw_buffs
        ]
    
        enemy["gil_pool"]        = enemy.get("gil_drop", 0)
        session.game_log         = ["Battle initiated!"]
        session.current_enemy    = enemy
        def battle_log(sid: int, line: str):
            # 1) persist to your normal battle_log table via GameMaster
            self._append_battle_log(sid, line)
            # 2) append it _in memory_ so update_battle_embed will render it
            session.game_log.append(line)

        session._status_engine = StatusEffectEngine(
            session,
            battle_log
        )

        conn = self.db_connect()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            "SELECT hp, max_hp, mp, max_mp, defense, attack_power FROM players WHERE player_id = %s AND session_id = %s",
            (player_id, session.session_id),
        )
        player = cursor.fetchone()
        cursor.close(); conn.close()

        self.embed_manager = self.embed_manager or self.bot.get_cog("EmbedManager")
        role = enemy.get("role", "normal")
        if role == "boss":
            title, color = "🔥 Boss Battle!", discord.Color.purple()
        elif role == "miniboss":
            title, color = "🐉 Miniboss Battle!", discord.Color.dark_gold()
        else:
            title, color = "⚔️ Battle Mode", discord.Color.dark_red()

        eb = discord.Embed(title=title, color=color)
        # show enemy HP + effects
        enemy_line = format_status_effects(session.battle_state["enemy_effects"])
        val = f"❤️ HP: {create_health_bar(enemy['hp'], enemy['max_hp'])}"
        if enemy_line:
            val += f" {enemy_line}"
        eb.add_field(name=f"Enemy: {enemy['enemy_name']}", value=val, inline=False)

        # show player HP + effects
        player_line = format_status_effects(session.battle_state["player_effects"])
        stats_text = f"❤️ HP: {create_health_bar(player['hp'], player['max_hp'])}"
        if player.get("max_mp"):
            stats_text += f"\n💠 MP: {create_health_bar(player.get('mp', 0), player['max_mp'])}"
        if player_line:
            stats_text += f" {player_line}"
        stats_text += f"\n⚔️ ATK: {player['attack_power']}\n🛡️ DEF: {player['defense']}"
        eb.add_field(name="Your Stats", value=stats_text, inline=False)

        eb.add_field(name="Battle Log",
                     value="\n".join(session.game_log[-5:]) or "No actions recorded.",
                     inline=False)
        if enemy.get("image_url"):
            eb.set_image(url=enemy["image_url"] + f"?t={int(time.time())}")

        pid    = session.current_turn
        trance = getattr(session, "trance_states", {}).get(pid)
        if trance:
            bar   = create_progress_bar(trance["remaining"], trance["max"], length=6)
            label = f"{trance['name']} {bar}"
            buttons = [
                (label, discord.ButtonStyle.danger,   "combat_trance_menu", 0),
                ("Skill", discord.ButtonStyle.primary, "combat_skill_menu",  0),
                ("Use",   discord.ButtonStyle.success, "combat_item",        0),
                ("Flee",  discord.ButtonStyle.secondary,"combat_flee",        0),
            ]
        else:
            buttons = [
                ("Attack", discord.ButtonStyle.danger,   "combat_attack",      0),
                ("Skill",  discord.ButtonStyle.primary,  "combat_skill_menu",  0),
                ("Use",    discord.ButtonStyle.success,  "combat_item",        0),
                ("Flee",   discord.ButtonStyle.secondary,"combat_flee",        0),
            ]

        class_name = self._get_player_class_name(session.session_id, pid)
        unlocked = SessionPlayerModel.get_unlocked_eidolons(session.session_id, pid)
        session.active_summons = getattr(session, "active_summons", {}) or {}
        if class_name == "Summoner" and unlocked:
            session.summon_used = getattr(session, "summon_used", {}) or {}
            if not session.summon_used.get(pid) and not session.active_summons.get(pid):
                buttons.append(("Summon", discord.ButtonStyle.primary, "combat_summon_menu", 1))
        if session.active_summons.get(pid):
            eidolon_name = session.active_summons[pid]["name"]
            buttons[0] = (eidolon_name, discord.ButtonStyle.danger, "combat_eidolon_menu", 0)

        await self.embed_manager.send_or_update_embed(
            interaction, title="", description="", embed_override=eb, buttons=buttons
        )
        logger.debug("Battle started: %s vs %s", player_id, enemy["enemy_name"])

    async def update_battle_embed(
            self,
            interaction: discord.Interaction,
            player_id: int,
            enemy: Dict[str, Any]
    ) -> None:
        mgr = self.bot.get_cog("SessionManager")
        if not mgr:
            return
        session = mgr.get_session(interaction.channel.id)
        if not session:
            return
        if getattr(session, "victory_pending", False):
            return
        if not session.battle_state or session.current_enemy is None:
            return

        conn = self.db_connect()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            "SELECT hp, max_hp, mp, max_mp, defense, attack_power FROM players WHERE player_id = %s AND session_id = %s",
            (player_id, session.session_id),
        )
        player = cursor.fetchone()
        cursor.close(); conn.close()

        role = enemy.get("role", "normal")
        if role == "boss":
            title, color = "🔥 Boss Battle!", discord.Color.purple()
        elif role == "miniboss":
            title, color = "🐉 Miniboss Battle!", discord.Color.dark_gold()
        else:
            title, color = "⚔️ Battle Mode", discord.Color.dark_red()

        eb = discord.Embed(title=title, color=color)
        enemy_line  = format_status_effects(session.battle_state.get("enemy_effects", []))
        val = f"❤️ HP: {create_health_bar(enemy['hp'], enemy['max_hp'])}"
        if enemy_line:
            val += f" {enemy_line}"
        eb.add_field(name=f"Enemy: {enemy['enemy_name']}", value=val, inline=False)

        player_line = format_status_effects(session.battle_state.get("player_effects", []))
        stats_text = f"❤️ HP: {create_health_bar(player['hp'], player['max_hp'])}"
        if player.get("max_mp"):
            stats_text += f"\n💠 MP: {create_health_bar(player.get('mp', 0), player['max_mp'])}"
        if player_line:
            stats_text += f" {player_line}"
        stats_text += (
            f"\n⚔️ ATK: {player['attack_power']}\n"
            f"🛡️ DEF: {player['defense']}"
        )
        eb.add_field(name="Your Stats", value=stats_text, inline=False)

        eb.add_field(name="Battle Log",
                     value="\n".join(session.game_log[-5:]) or "No actions recorded.",
                     inline=False)
        if enemy.get("image_url"):
            eb.set_image(url=enemy["image_url"] + f"?t={int(time.time())}")

        pid    = session.current_turn
        trance = getattr(session, "trance_states", {}).get(pid)
        if trance:
            bar   = create_progress_bar(trance["remaining"], trance["max"], length=6)
            label = f"{trance['name']} {bar}"
            buttons = [
                (label, discord.ButtonStyle.danger,   "combat_trance_menu", 0),
                ("Skill", discord.ButtonStyle.primary, "combat_skill_menu",  0),
                ("Use",   discord.ButtonStyle.success, "combat_item",        0),
                ("Flee",  discord.ButtonStyle.secondary,"combat_flee",        0),
            ]
        else:
            buttons = [
                ("Attack", discord.ButtonStyle.danger,   "combat_attack",      0),
                ("Skill",  discord.ButtonStyle.primary,  "combat_skill_menu",  0),
                ("Use",    discord.ButtonStyle.success,  "combat_item",        0),
                ("Flee",   discord.ButtonStyle.secondary,"combat_flee",        0),
            ]

        class_name = self._get_player_class_name(session.session_id, pid)
        unlocked = SessionPlayerModel.get_unlocked_eidolons(session.session_id, pid)
        session.active_summons = getattr(session, "active_summons", {}) or {}
        if class_name == "Summoner" and unlocked:
            session.summon_used = getattr(session, "summon_used", {}) or {}
            if not session.summon_used.get(pid) and not session.active_summons.get(pid):
                buttons.append(("Summon", discord.ButtonStyle.primary, "combat_summon_menu", 1))
        if session.active_summons.get(pid):
            eidolon_name = session.active_summons[pid]["name"]
            buttons[0] = (eidolon_name, discord.ButtonStyle.danger, "combat_eidolon_menu", 0)

        await self.embed_manager.send_or_update_embed(
            interaction, title="", description="", embed_override=eb, buttons=buttons
        )
    

    async def handle_skill_menu(self, interaction: discord.Interaction) -> None:
        """
        Pull the player’s unlocked abilities, filter by in/out-of-battle targets,
        show cooldown bars, and hand off to EmbedManager.send_skill_menu_embed.
        """
        mgr = self.bot.get_cog("SessionManager")
        embed_mgr = self.bot.get_cog("EmbedManager")
        if not mgr or not embed_mgr:
            return await interaction.response.send_message("❌ SessionManager or EmbedManager unavailable.", ephemeral=True)
        self.embed_manager = embed_mgr

        session = mgr.get_session(interaction.channel.id)
        if not session:
            return await interaction.response.send_message("❌ No active session.", ephemeral=True)

        # Ensure cooldown buckets exist
        if not hasattr(session, "ability_cooldowns") or session.ability_cooldowns is None:
            session.ability_cooldowns = {}

        pid = session.current_turn
        in_battle = bool(session.battle_state)
        gm = self.bot.get_cog("GameMaster")
        in_illusion = bool(gm and gm.is_player_in_illusion(session, pid))

        # fetch class & level
        from models.session_models import SessionPlayerModel
        players = SessionPlayerModel.get_player_states(session.session_id)
        me = next((p for p in players if p["player_id"] == pid), None)
        if not me:
            return await interaction.response.send_message("❌ Could not find your player data.", ephemeral=True)
        class_id, level = me["class_id"], me["level"]

        # load unlocked abilities
        conn = self.db_connect()
        cur = conn.cursor(dictionary=True)
        cur.execute(
            """
            SELECT a.ability_id,
                   a.ability_name,
                   a.effect,
                   a.cooldown,
                   a.icon_url,
                   a.target_type,
                   a.element_id
              FROM class_abilities ca
              JOIN abilities a USING (ability_id)
             WHERE ca.class_id    = %s
               AND ca.unlock_level <= %s
            """,
            (class_id, level),
        )
        abilities = cur.fetchall()
        cur.close()

        cur = conn.cursor(dictionary=True)
        cur.execute(
            """
            SELECT pta.temp_ability_id,
                   pta.remaining_turns,
                   ta.ability_name,
                   ta.description,
                   ta.effect,
                   ta.cooldown_turns,
                   ta.duration_turns,
                   ta.icon_url,
                   ta.target_type,
                   ta.element_id
              FROM player_temporary_abilities pta
              JOIN temporary_abilities ta
                ON ta.temp_ability_id = pta.temp_ability_id
             WHERE pta.session_id = %s
               AND pta.player_id = %s
               AND pta.remaining_turns > 0
            """,
            (session.session_id, pid),
        )
        temp_abilities = cur.fetchall()
        cur.close()
        conn.close()

        # filter by context
        allowed = {"self", "any"} | ({"enemy"} if (in_battle or in_illusion) else {"ally"})
        abilities = [a for a in abilities if a["target_type"] in allowed]
        temp_abilities = [a for a in temp_abilities if a["target_type"] in allowed]

        # annotate current cooldowns
        cds = session.ability_cooldowns.get(pid, {})
        for a in abilities:
            a["current_cooldown"] = cds.get(a["ability_id"], 0)

        session.temp_ability_cooldowns = getattr(session, "temp_ability_cooldowns", {}) or {}
        temp_cds = session.temp_ability_cooldowns.get(pid, {})
        for a in temp_abilities:
            a["ability_id"] = a.pop("temp_ability_id")
            a["cooldown"] = a.pop("cooldown_turns", 0)
            a["duration_turns"] = a.pop("duration_turns", 0)
            a["remaining_duration"] = a.pop("remaining_turns", 0)
            a["current_cooldown"] = temp_cds.get(a["ability_id"], 0)
            a["custom_id"] = f"combat_temp_{a['ability_id']}"

        abilities.extend(temp_abilities)

        if not interaction.response.is_done():
            await interaction.response.defer()
        await embed_mgr.send_skill_menu_embed(interaction, abilities)

    async def show_summon_menu(self, interaction: discord.Interaction) -> None:
        mgr = self.bot.get_cog("SessionManager")
        if not mgr or not self.embed_manager:
            return await interaction.response.send_message("❌ SessionManager or EmbedManager unavailable.", ephemeral=True)

        session = mgr.get_session(interaction.channel.id)
        if not session:
            return await interaction.response.send_message("❌ No active session.", ephemeral=True)

        pid = session.current_turn
        class_name = self._get_player_class_name(session.session_id, pid)
        if class_name != "Summoner":
            return await interaction.response.send_message("❌ Only Summoners can attune to Eidolons.", ephemeral=True)

        unlocked = SessionPlayerModel.get_unlocked_eidolons(session.session_id, pid)
        if not unlocked:
            return await interaction.response.send_message("❌ You have not unlocked any Eidolons yet.", ephemeral=True)

        session.summon_used = getattr(session, "summon_used", {}) or {}
        if session.summon_used.get(pid):
            return await interaction.response.send_message("❌ You can only summon once per turn.", ephemeral=True)

        buttons = []
        for eid in unlocked:
            buttons.append((
                f"{eid['name']} (Lv {eid['level']})",
                discord.ButtonStyle.primary,
                f"summon_select_{eid['eidolon_id']}",
                0,
            ))
        buttons.append(("Back", discord.ButtonStyle.secondary, "summon_back", 1))
        await self.embed_manager.send_or_update_embed(
            interaction,
            title="🔮 Eidolon Summon",
            description="Select an Eidolon to summon.",
            buttons=buttons,
        )

    async def show_eidolon_ability_menu(self, interaction: discord.Interaction, eidolon_id: int) -> None:
        mgr = self.bot.get_cog("SessionManager")
        if not mgr or not self.embed_manager:
            return await interaction.response.send_message("❌ SessionManager or EmbedManager unavailable.", ephemeral=True)

        session = mgr.get_session(interaction.channel.id)
        if not session:
            return await interaction.response.send_message("❌ No active session.", ephemeral=True)

        pid = session.current_turn
        level = self._get_eidolon_level(session.session_id, pid, eidolon_id)
        if not level:
            return await interaction.response.send_message("❌ Eidolon not unlocked.", ephemeral=True)

        conn = self.db_connect()
        cur = conn.cursor(dictionary=True)
        cur.execute(
            """
            SELECT a.*, ea.unlock_level
              FROM eidolon_abilities ea
              JOIN abilities a ON a.ability_id = ea.ability_id
             WHERE ea.eidolon_id = %s
               AND ea.unlock_level <= %s
            """,
            (eidolon_id, level),
        )
        abilities = cur.fetchall()
        cur.close()
        conn.close()

        session.eidolon_ability_cooldowns = getattr(session, "eidolon_ability_cooldowns", {}) or {}
        cds = session.eidolon_ability_cooldowns.get(pid, {})

        buttons = []
        for a in abilities:
            cd_now = int(cds.get(a["ability_id"], 0))
            bar = create_cooldown_bar(cd_now, a.get("cooldown", 0), length=6)
            style = discord.ButtonStyle.secondary if cd_now > 0 else discord.ButtonStyle.primary
            buttons.append((
                f"{a['ability_name']} {bar}",
                style,
                f"summon_ability_{eidolon_id}_{a['ability_id']}",
                0,
                cd_now > 0,
            ))

        buttons.append(("Back", discord.ButtonStyle.secondary, "summon_back", 1))
        await self.embed_manager.send_or_update_embed(
            interaction,
            title="✨ Eidolon Abilities",
            description="Choose an Eidolon ability to unleash.",
            buttons=buttons,
        )

    async def display_trance_menu(self, interaction: discord.Interaction) -> None:
        """
        Show the active Trance’s abilities in combat, with cooldown bars,
        and a Back button to the main battle embed.
        """
        session = self.get_session(interaction.channel.id)
        if not session:
            return await interaction.response.send_message("❌ No session found.", ephemeral=True)

        pid = session.current_turn
        ts = getattr(session, "trance_states", {}).get(pid)
        if not ts:
            return await interaction.response.send_message("❌ You have no active Trance.", ephemeral=True)

        session.ability_cooldowns = getattr(session, "ability_cooldowns", {}) or {}

        # Load the abilities for this trance_id
        conn = self.db_connect()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT ta.ability_id,
                   a.ability_name,
                   a.cooldown,
                   a.icon_url
              FROM trance_abilities ta
              JOIN abilities a USING (ability_id)
             WHERE ta.trance_id = %s
             ORDER BY ta.ability_id
        """, (ts["trance_id"],))
        abilities = cursor.fetchall()
        cursor.close(); conn.close()

        if not abilities:
            return await interaction.response.send_message("⚠️ This Trance has no abilities.", ephemeral=True)

        # Annotate cooldowns
        cds = session.ability_cooldowns.get(pid, {})
        buttons = []
        for a in abilities:
            cd_now = int(cds.get(a["ability_id"], 0))
            bar = create_cooldown_bar(cd_now, a["cooldown"], length=6)
            style = discord.ButtonStyle.secondary if cd_now > 0 else discord.ButtonStyle.primary
            buttons.append((f"{a['ability_name']} {bar}", style, f"combat_trance_{a['ability_id']}", 0, cd_now > 0))

        # ← Back
        buttons.append(("← Back", discord.ButtonStyle.secondary, "combat_trance_back", 0))

        await self.embed_manager.send_or_update_embed(
            interaction,
            title=f"✨ {ts['name']} Abilities ({ts['remaining']} turns left)",
            description="Choose your Trance ability:",
            buttons=buttons
        )

    async def handle_skill_use(self, interaction: discord.Interaction, ability_id: int) -> None:
        mgr = self.bot.get_cog("SessionManager")
        if not mgr or not self.embed_manager:
            return await interaction.response.send_message("❌ SessionManager or EmbedManager unavailable.", ephemeral=True)

        session = mgr.get_session(interaction.channel.id)
        if not session:
            return await interaction.response.send_message("❌ No active session.", ephemeral=True)

        session.ability_cooldowns = getattr(session, "ability_cooldowns", {}) or {}

        # 1) fetch ability metadata up‑front so we know its target_type
        conn = self.db_connect()
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT * FROM abilities WHERE ability_id = %s", (ability_id,))
        ability_meta = cur.fetchone()
        cur.close(); conn.close()
        if not ability_meta:
            return await interaction.response.send_message("❌ Ability not found.", ephemeral=True)

        # Block usage if this ability is still cooling down
        current_cd = session.ability_cooldowns.get(session.current_turn, {}).get(ability_id, 0)
        if current_cd > 0:
            msg = f"⏳ {ability_meta.get('ability_name', 'That ability')} is cooling down (remaining: {current_cd:.1f})."
            if interaction.response.is_done():
                return await interaction.followup.send(msg, ephemeral=True)
            return await interaction.response.send_message(msg, ephemeral=True)

        # 2) If it’s an enemy‑target skill but we’re not in a battle, block it
        in_battle = bool(session.current_enemy)
        gm = self.bot.get_cog("GameMaster")
        in_illusion = bool(gm and gm.is_player_in_illusion(session, session.current_turn))
        if ability_meta["target_type"] == "enemy" and not in_battle and not in_illusion:
            return await interaction.response.send_message(
                "❌ That ability can only be used in battle.", ephemeral=True
            )

        # 3) Ensure we always have buckets for status effects (so self‑buffs work outside battle)
        if not hasattr(session, "battle_state") or session.battle_state is None:
            session.battle_state = {"player_effects": [], "enemy_effects": []}
        else:
            session.battle_state.setdefault("player_effects", [])
            session.battle_state.setdefault("enemy_effects", [])

        pid = session.current_turn
        enemy = session.current_enemy if in_battle else None

        if not interaction.response.is_done():
            await interaction.response.defer()

        if in_illusion and gm:
            handled = await gm.handle_illusion_skill(
                interaction,
                ability_element_id=ability_meta.get("element_id"),
                ability_name=ability_meta.get("ability_name", "That ability"),
            )
            if handled:
                session.ability_cooldowns.setdefault(pid, {})[ability_id] = ability_meta.get("cooldown", 0)
                self.reduce_player_cooldowns(session, pid)
                return

        mp_cost = ability_meta.get("mp_cost", 0) or 0
        if mp_cost:
            mp_state = self._get_player_mp(session.session_id, session.current_turn)
            if not mp_state or mp_state.get("mp", 0) < mp_cost:
                return await interaction.response.send_message("❌ Not enough MP.", ephemeral=True)
            new_mp = max(mp_state.get("mp", 0) - mp_cost, 0)
            self._set_player_mp(session.session_id, session.current_turn, new_mp)


        # 2) fetch player stats
        conn = self.db_connect()
        cur = conn.cursor(dictionary=True)
        cur.execute(
            "SELECT hp, max_hp, attack_power, magic_power, defense, magic_defense, accuracy, evasion FROM players WHERE player_id=%s AND session_id=%s",
            (pid, session.session_id),
        )
        player = cur.fetchone()
        cur.close(); conn.close()
        if not player:
            return await interaction.response.send_message("❌ Could not retrieve your stats.", ephemeral=True)
        

        # 3) resolve via AbilityEngine
        # if we’re outside battle, treat the player as the “target” for self‑buffs/heals
        engine_target = enemy if enemy is not None else player
        result = self.ability.resolve(player, engine_target, ability_meta)
        target = ability_meta.get("target_type", "self")
        # ── out‑of‑battle self‑buff / HoT ──
        if not in_battle and target == "self":
            gm = self.bot.get_cog("GameMaster")
            pid = session.current_turn

            # 1) append each freshly generated log line
            for line in result.logs:
                gm.append_game_log(session.session_id, line)

            # 2) normalize, merge & persist each new buff exactly once
            # ─── load any existing buffs from the DB into memory ───────────
            if "player_effects" not in session.battle_state:
                raw_saved = SessionPlayerModel.get_status_effects(session.session_id, pid)
                session.battle_state["player_effects"] = [
                    self._normalize_se(raw) for raw in raw_saved
                ]
            buffs = session.battle_state["player_effects"]
        
            # ─── merge in any newly returned status effects ───────────────
            for raw_se in result.status_effects or []:
                se = self._normalize_se(raw_se)
                # only add if it isn’t already in our list (by effect_id)
                if not any(existing.get("effect_id") == se.get("effect_id") for existing in buffs):
                    buffs.append(se)
        
            # ─── write the full, deduped list back to the DB ─────────────
            SessionPlayerModel.update_status_effects(
                session.session_id,
                pid,
                buffs
            )


            # 3) if it healed you immediately, also log that
            if result.type in ("heal", "set_hp"):
                old_hp = self._get_player_hp(pid, session.session_id)
                new_hp = (result.amount
                        if result.type == "set_hp"
                        else min(old_hp + result.amount,
                                self._get_player_max_hp(pid, session.session_id)))
                self._update_player_hp(pid, session.session_id, new_hp)
                gm.append_game_log(session.session_id, f"You are healed to {new_hp} HP.")

            # 4) redraw the room embed (old lines stay intact, new ones are appended)
            sm = self.bot.get_cog("SessionManager")
            return await sm.refresh_current_state(interaction)

        

        # 4) Emit exactly one log line per result.type, or fall back on engine.logs for niche cases
        if result.type == "damage":
            session.game_log.append(
                f"You use {ability_meta['ability_name']} and deal {result.amount} damage!"
            )
            self._append_elemental_log(session, result, enemy["enemy_name"])
        elif result.type == "dot":
            session.game_log.append(
                f"{enemy['enemy_name']} has been afflicted by {result.dot['effect_name']}."
            )
            self._append_elemental_log(session, result, enemy["enemy_name"])
        elif result.type == "hot":
            if target in ("self", "ally"):
                session.game_log.append(
                    f"You are affected by {result.dot['effect_name']}."
                )
            else:
                session.game_log.append(
                    f"{enemy['enemy_name']} is affected by {result.dot['effect_name']}."
                )
                self._append_elemental_log(session, result, enemy["enemy_name"])
        else:
            # miss, heal, pilfer, mug, etc.
            session.game_log.extend(result.logs)
            self._append_elemental_log(session, result, enemy["enemy_name"])
            # ── If we’re *outside* battle and this was a self‐target skill ──
            if not in_battle and target == "self":
                # 1) Persist any status‐effects exactly as before
                if result.status_effects:
                    SessionPlayerModel.update_status_effects(
                        session.session_id,
                        pid,
                        session.battle_state.get("player_effects", []) + result.status_effects
                    )

                # 2) If this skill also heals immediately on use, write that to the DB now:
                if result.type in ("heal", "set_hp"):
                    # e.g. “heal” gives you result.amount HP
                    # or “set_hp” forces to exactly result.amount
                    old_hp = self._get_player_hp(pid, session.session_id)
                    new_hp = result.amount if result.type == "set_hp" else min(
                        old_hp + result.amount,
                        self._get_player_max_hp(pid, session.session_id),
                    )
                    self._update_player_hp(pid, session.session_id, new_hp)
                    session.game_log.append(f"You are healed to {new_hp} HP.")

                # 3) Finally—*after* writing to the DB— redraw the *room* (not the battle embed)
                #    so your room embed updates with your new HP and buttons.
                sm = self.bot.get_cog("SessionManager")
                return await sm.refresh_current_state(interaction)


        # 5) apply any returned status effects
        for raw_se in getattr(result, "status_effects", []) or []:
            raw_se.setdefault("target", ability_meta.get("target_type", "self"))
            se = self._normalize_se(raw_se)
            bucket = "player_effects" if se["target"] == "self" else "enemy_effects"
            session.battle_state[bucket].append(se)

            # initial application log
            if se["target"] == "self":
                session.game_log.append(
                    f"{se['effect_name']} has been applied to <@{pid}>."
                )
                # persist the player buff
                SessionPlayerModel.update_status_effects(
                    session.session_id, pid, session.battle_state[bucket]
                )
            else:
                name = session.current_enemy.get("enemy_name", "The enemy")
                session.game_log.append(
                    f"{name} has been afflicted by {se['effect_name']}."
                )

        # 6) burn cooldown on the player
        session.ability_cooldowns.setdefault(pid, {})[ability_id] = ability_meta.get("cooldown", 0)
        self.reduce_player_cooldowns(session, pid)

        # 7) handle the result types
        if result.type in ("damage","heal","set_hp","dot","hot"):
            # update enemy.hp or player.hp as needed
            if result.type == "damage":
                enemy["hp"] = max(enemy["hp"] - result.amount, 0)
            elif result.type == "heal":
                if target in ("self","ally"):
                    # heal the player
                    new_hp = min(player["hp"] + result.amount, player["max_hp"])
                    self._update_player_hp(pid, session.session_id, new_hp)
                    session.game_log.append(f"You restore {result.amount} HP to yourself!")
                else:
                    # heal the enemy (e.g. Vampire or enemy‑buff)
                    enemy["hp"] = min(enemy["hp"] + result.amount, enemy["max_hp"])
                    session.game_log.append(f"{enemy['enemy_name']} recovers {result.amount} HP!")
            elif result.type == "set_hp":
                enemy["hp"] = result.amount
            elif result.type == "dot":
                enemy.setdefault("dot_effects", []).append(result.dot)
                enemy["hp"] = max(enemy["hp"] - result.dot["damage_per_turn"], 0)
            elif result.type == "hot":
                heal_tick = result.dot.get("heal_per_turn", 0)
                if target in ("self", "ally"):
                    new_hp = min(player["hp"] + heal_tick, player["max_hp"])
                    self._update_player_hp(pid, session.session_id, new_hp)
                    session.game_log.append(f"You recover {heal_tick} HP!")
                else:
                    enemy.setdefault("dot_effects", []).append(result.dot)
                    enemy["hp"] = min(enemy["hp"] + heal_tick, enemy["max_hp"])
                    session.game_log.append(f"{enemy['enemy_name']} recovers {heal_tick} HP!")


        else:
            # for “miss”, “pilfer”, “mug”, etc.
            await self.update_battle_embed(interaction, pid, enemy)
            if result.type in ("pilfer","mug") and result.type=="pilfer":
                # apply gil steal on DB
                self._steal_gil(pid, session.session_id, result.amount)
                enemy["gil_pool"] -= result.amount
            if result.type=="mug":
                enemy["hp"] = max(enemy["hp"] - result.amount, 0)
                if enemy["hp"] <= 0:
                    return await self.handle_enemy_defeat(interaction, session, enemy)
        
        if await self._check_eidolon_attunement(interaction, session, enemy):
            return
        if await self._check_eidolon_attunement(interaction, session, enemy):
            return
        if enemy["hp"] <= 0:
            return await self.handle_enemy_defeat(interaction, session, enemy)

        await self.update_battle_embed(interaction, pid, enemy)

        # 8) now let the enemy take their turn, then advance back
        await asyncio.sleep(1)
        await self.enemy_turn(interaction, enemy)

    async def handle_summon_select(self, interaction: discord.Interaction, eidolon_id: int) -> None:
        mgr = self.bot.get_cog("SessionManager")
        if not mgr or not self.embed_manager:
            return await interaction.response.send_message("❌ SessionManager or EmbedManager unavailable.", ephemeral=True)

        session = mgr.get_session(interaction.channel.id)
        if not session:
            return await interaction.response.send_message("❌ No active session.", ephemeral=True)

        pid = session.current_turn
        session.summon_used = getattr(session, "summon_used", {}) or {}
        if session.summon_used.get(pid):
            return await interaction.response.send_message("❌ You can only summon once per turn.", ephemeral=True)

        eidolon = self._get_eidolon(eidolon_id)
        if not eidolon:
            return await interaction.response.send_message("❌ Eidolon not found.", ephemeral=True)

        level = self._get_eidolon_level(session.session_id, pid, eidolon_id)
        if not level:
            return await interaction.response.send_message("❌ Eidolon not unlocked.", ephemeral=True)

        player_level = self._get_player_level(session.session_id, pid) or 0
        if player_level < (eidolon.get("required_level") or 1):
            return await interaction.response.send_message("❌ You are not attuned enough to summon that Eidolon.", ephemeral=True)

        session.active_summons = getattr(session, "active_summons", {}) or {}
        if session.active_summons.get(pid):
            return await interaction.response.send_message("❌ You already have an Eidolon attuned this turn.", ephemeral=True)

        mp_state = self._get_player_mp(session.session_id, pid)
        summon_cost = eidolon.get("summon_mp_cost", 0) or 0
        if summon_cost and (not mp_state or mp_state.get("mp", 0) < summon_cost):
            return await interaction.response.send_message("❌ Not enough MP to summon.", ephemeral=True)

        if summon_cost:
            new_mp = max((mp_state.get("mp", 0) if mp_state else 0) - summon_cost, 0)
            self._set_player_mp(session.session_id, pid, new_mp)

        session.active_summons[pid] = {
            "eidolon_id": eidolon_id,
            "name": eidolon["name"],
            "level": level,
        }

        if session.current_enemy:
            session.summoned_eidolons = getattr(session, "summoned_eidolons", {}) or {}
            session.summoned_eidolons.setdefault(pid, set()).add(eidolon_id)
            return await self.update_battle_embed(interaction, pid, session.current_enemy)

        return await self.show_eidolon_ability_menu(interaction, eidolon_id)

    async def handle_eidolon_ability_use(
        self,
        interaction: discord.Interaction,
        eidolon_id: int,
        ability_id: int,
    ) -> None:
        mgr = self.bot.get_cog("SessionManager")
        if not mgr or not self.embed_manager:
            return await interaction.response.send_message("❌ SessionManager or EmbedManager unavailable.", ephemeral=True)

        session = mgr.get_session(interaction.channel.id)
        if not session:
            return await interaction.response.send_message("❌ No active session.", ephemeral=True)

        pid = session.current_turn
        active = getattr(session, "active_summons", {}) or {}
        if not active.get(pid) or active[pid]["eidolon_id"] != eidolon_id:
            return await interaction.response.send_message("❌ No active Eidolon to command.", ephemeral=True)

        conn = self.db_connect()
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT * FROM abilities WHERE ability_id = %s", (ability_id,))
        ability_meta = cur.fetchone()
        cur.close()
        conn.close()
        if not ability_meta:
            return await interaction.response.send_message("❌ Ability not found.", ephemeral=True)

        session.eidolon_ability_cooldowns = getattr(session, "eidolon_ability_cooldowns", {}) or {}
        current_cd = session.eidolon_ability_cooldowns.get(pid, {}).get(ability_id, 0)
        if current_cd > 0:
            return await interaction.response.send_message("❌ That Eidolon ability is cooling down.", ephemeral=True)

        mp_cost = ability_meta.get("mp_cost", 0) or 0
        if mp_cost:
            mp_state = self._get_player_mp(session.session_id, pid)
            if not mp_state or mp_state.get("mp", 0) < mp_cost:
                return await interaction.response.send_message("❌ Not enough MP.", ephemeral=True)
            new_mp = max(mp_state.get("mp", 0) - mp_cost, 0)
            self._set_player_mp(session.session_id, pid, new_mp)

        in_battle = bool(session.current_enemy)
        gm = self.bot.get_cog("GameMaster")
        in_illusion = bool(gm and gm.is_player_in_illusion(session, pid))
        if ability_meta["target_type"] == "enemy" and not in_battle and not in_illusion:
            return await interaction.response.send_message("❌ That Eidolon ability can only be used in battle.", ephemeral=True)

        eidolon = self._get_eidolon(eidolon_id)
        level = self._get_eidolon_level(session.session_id, pid, eidolon_id) or 1
        eidolon_stats = self._calculate_eidolon_stats(eidolon, level) if eidolon else {}

        conn = self.db_connect()
        cur = conn.cursor(dictionary=True)
        cur.execute(
            "SELECT hp, max_hp, attack_power, magic_power, defense, magic_defense, accuracy, evasion FROM players WHERE player_id=%s AND session_id=%s",
            (pid, session.session_id),
        )
        player = cur.fetchone()
        cur.close()
        conn.close()
        if not player:
            return await interaction.response.send_message("❌ Could not retrieve your stats.", ephemeral=True)

        enemy = session.current_enemy if in_battle else None
        engine_target = enemy if enemy is not None else player
        result = self.ability.resolve(eidolon_stats, engine_target, ability_meta)

        session.eidolon_ability_cooldowns.setdefault(pid, {})[ability_id] = ability_meta.get("cooldown", 0)
        session.summon_used = getattr(session, "summon_used", {}) or {}
        session.summon_used[pid] = True
        eidolon_name = active.get(pid, {}).get("name", "Eidolon")
        active.pop(pid, None)

        if not in_battle and ability_meta.get("target_type") == "self":
            if gm:
                for line in result.logs:
                    gm.append_game_log(session.session_id, line)
            if result.type in ("heal", "set_hp"):
                old_hp = self._get_player_hp(pid, session.session_id)
                new_hp = (result.amount if result.type == "set_hp" else min(
                    old_hp + result.amount,
                    self._get_player_max_hp(pid, session.session_id),
                ))
                self._update_player_hp(pid, session.session_id, new_hp)
                if gm:
                    gm.append_game_log(session.session_id, f"You are healed to {new_hp} HP.")
            sm = self.bot.get_cog("SessionManager")
            return await sm.refresh_current_state(interaction)

        if not session.battle_state:
            session.battle_state = {"player_effects": [], "enemy_effects": []}

        target = ability_meta.get("target_type", "self")
        if result.type in ("damage", "heal", "set_hp", "dot", "hot"):
            if result.type == "damage":
                enemy["hp"] = max(enemy["hp"] - result.amount, 0)
                session.game_log.append(
                    f"{eidolon_name} uses {ability_meta['ability_name']} for {result.amount} damage!"
                )
                self._append_elemental_log(session, result, enemy["enemy_name"])
            elif result.type == "heal":
                if target in ("self", "ally"):
                    new_hp = min(player["hp"] + result.amount, player["max_hp"])
                    self._update_player_hp(pid, session.session_id, new_hp)
                    session.game_log.append(f"Eidolon restores {result.amount} HP to you!")
                else:
                    enemy["hp"] = min(enemy["hp"] + result.amount, enemy["max_hp"])
                    session.game_log.append(f"{enemy['enemy_name']} recovers {result.amount} HP!")
                self._append_elemental_log(session, result, enemy["enemy_name"])
            elif result.type == "set_hp":
                enemy["hp"] = result.amount
            elif result.type == "dot":
                enemy.setdefault("dot_effects", []).append(result.dot)
                enemy["hp"] = max(enemy["hp"] - result.dot["damage_per_turn"], 0)
                self._append_elemental_log(session, result, enemy["enemy_name"])
            elif result.type == "hot":
                heal_tick = result.dot.get("heal_per_turn", 0)
                if target in ("self", "ally"):
                    new_hp = min(player["hp"] + heal_tick, player["max_hp"])
                    self._update_player_hp(pid, session.session_id, new_hp)
                    session.game_log.append(f"Eidolon restores {heal_tick} HP to you!")
                else:
                    enemy.setdefault("dot_effects", []).append(result.dot)
                    enemy["hp"] = min(enemy["hp"] + heal_tick, enemy["max_hp"])
                    session.game_log.append(f"{enemy['enemy_name']} recovers {heal_tick} HP!")
                self._append_elemental_log(session, result, enemy["enemy_name"])
        else:
            session.game_log.extend(result.logs)
            self._append_elemental_log(session, result, enemy["enemy_name"])

        for raw_se in getattr(result, "status_effects", []) or []:
            raw_se.setdefault("target", ability_meta.get("target_type", "self"))
            se = self._normalize_se(raw_se)
            bucket = "player_effects" if se["target"] == "self" else "enemy_effects"
            session.battle_state[bucket].append(se)
            if se["target"] == "self":
                session.game_log.append(
                    f"{se['effect_name']} has been applied to <@{pid}>."
                )
                SessionPlayerModel.update_status_effects(
                    session.session_id, pid, session.battle_state[bucket]
                )
            else:
                name = session.current_enemy.get("enemy_name", "The enemy")
                session.game_log.append(
                    f"{name} has been afflicted by {se['effect_name']}."
                )

        if enemy and await self._check_eidolon_attunement(interaction, session, enemy):
            return
        if enemy and enemy["hp"] <= 0:
            return await self.handle_enemy_defeat(interaction, session, enemy)

        await self.update_battle_embed(interaction, pid, enemy)
        await asyncio.sleep(1)
        await self.enemy_turn(interaction, enemy)

    async def handle_temp_skill_use(self, interaction: discord.Interaction, temp_ability_id: int) -> None:
        mgr = self.bot.get_cog("SessionManager")
        if not mgr or not self.embed_manager:
            return await interaction.response.send_message("❌ SessionManager or EmbedManager unavailable.", ephemeral=True)

        session = mgr.get_session(interaction.channel.id)
        if not session:
            return await interaction.response.send_message("❌ No active session.", ephemeral=True)

        session.temp_ability_cooldowns = getattr(session, "temp_ability_cooldowns", {}) or {}
        pid = session.current_turn

        current_cd = session.temp_ability_cooldowns.get(pid, {}).get(temp_ability_id, 0)
        if current_cd > 0:
            msg = f"⏳ That ability is cooling down (remaining: {current_cd})."
            if interaction.response.is_done():
                return await interaction.followup.send(msg, ephemeral=True)
            return await interaction.response.send_message(msg, ephemeral=True)

        conn = self.db_connect()
        cur = conn.cursor(dictionary=True)
        cur.execute(
            """
            SELECT pta.remaining_turns,
                   ta.temp_ability_id,
                   ta.ability_name,
                   ta.description,
                   ta.effect,
                   ta.cooldown_turns,
                   ta.duration_turns,
                   ta.icon_url,
                   ta.target_type,
                   ta.element_id
              FROM player_temporary_abilities pta
              JOIN temporary_abilities ta
                ON ta.temp_ability_id = pta.temp_ability_id
             WHERE pta.session_id = %s
               AND pta.player_id = %s
               AND pta.temp_ability_id = %s
               AND pta.remaining_turns > 0
            """,
            (session.session_id, pid, temp_ability_id),
        )
        ability_meta = cur.fetchone()
        cur.close()
        conn.close()
        if not ability_meta:
            return await interaction.response.send_message("❌ Temporary ability not found.", ephemeral=True)

        in_battle = bool(session.current_enemy)
        gm = self.bot.get_cog("GameMaster")
        in_illusion = bool(gm and gm.is_player_in_illusion(session, session.current_turn))
        if ability_meta["target_type"] == "enemy" and not in_battle and not in_illusion:
            return await interaction.response.send_message(
                "❌ That ability can only be used in battle.", ephemeral=True
            )

        if not hasattr(session, "battle_state") or session.battle_state is None:
            session.battle_state = {"player_effects": [], "enemy_effects": []}
        else:
            session.battle_state.setdefault("player_effects", [])
            session.battle_state.setdefault("enemy_effects", [])

        if not interaction.response.is_done():
            await interaction.response.defer()

        if in_illusion and gm:
            handled = await gm.handle_illusion_skill(
                interaction,
                ability_element_id=ability_meta.get("element_id"),
                ability_name=ability_meta.get("ability_name", "That ability"),
            )
            if handled:
                session.temp_ability_cooldowns.setdefault(pid, {})[temp_ability_id] = ability_meta.get("cooldown_turns", 0)
                return

        ability_meta["ability_id"] = ability_meta["temp_ability_id"]
        enemy = session.current_enemy if in_battle else None

        conn = self.db_connect()
        cur = conn.cursor(dictionary=True)
        cur.execute(
            "SELECT hp, max_hp, attack_power, magic_power, defense, magic_defense, accuracy, evasion "
            "FROM players WHERE player_id=%s AND session_id=%s",
            (pid, session.session_id),
        )
        player = cur.fetchone()
        cur.close()
        conn.close()
        if not player:
            return await interaction.response.send_message("❌ Could not retrieve your stats.", ephemeral=True)

        engine_target = enemy if enemy is not None else player
        result = self.ability.resolve(player, engine_target, ability_meta)
        target = ability_meta.get("target_type", "self")

        if not in_battle and target == "self":
            if gm:
                for line in result.logs:
                    gm.append_game_log(session.session_id, line)

                if "player_effects" not in session.battle_state:
                    raw_saved = SessionPlayerModel.get_status_effects(session.session_id, pid)
                    session.battle_state["player_effects"] = [
                        self._normalize_se(raw) for raw in raw_saved
                    ]
                buffs = session.battle_state["player_effects"]

                for raw_se in result.status_effects or []:
                    se = self._normalize_se(raw_se)
                    if not any(existing.get("effect_id") == se.get("effect_id") for existing in buffs):
                        buffs.append(se)

                SessionPlayerModel.update_status_effects(
                    session.session_id,
                    pid,
                    buffs
                )

                if result.type in ("heal", "set_hp"):
                    old_hp = self._get_player_hp(pid, session.session_id)
                    new_hp = (result.amount
                              if result.type == "set_hp"
                              else min(old_hp + result.amount,
                                       self._get_player_max_hp(pid, session.session_id)))
                    self._update_player_hp(pid, session.session_id, new_hp)
                    gm.append_game_log(session.session_id, f"You are healed to {new_hp} HP.")

            session.temp_ability_cooldowns.setdefault(pid, {})[temp_ability_id] = ability_meta.get("cooldown_turns", 0)
            sm = self.bot.get_cog("SessionManager")
            return await sm.refresh_current_state(interaction)

        if result.type == "damage":
            session.game_log.append(
                f"You use {ability_meta['ability_name']} and deal {result.amount} damage!"
            )
            self._append_elemental_log(session, result, enemy["enemy_name"])
        elif result.type == "dot":
            dot = result.dot
            enemy.setdefault("dot_effects", []).append(dot)
            enemy["hp"] = max(enemy["hp"] - dot["damage_per_turn"], 0)
            session.game_log.append(
                f"{enemy['enemy_name']} has been afflicted by {dot['effect_name']}."
            )
            self._append_elemental_log(session, result, enemy["enemy_name"])
            if enemy["hp"] <= 0:
                return await self.handle_enemy_defeat(interaction, session, enemy)
        elif result.type == "hot":
            dot = result.dot
            if target in ("self", "ally"):
                session.game_log.append(
                    f"You are affected by {dot['effect_name']}."
                )
            else:
                enemy.setdefault("dot_effects", []).append(dot)
                enemy["hp"] = min(
                    enemy["hp"] + dot.get("heal_per_turn", 0),
                    enemy["max_hp"]
                )
                session.game_log.append(
                    f"{enemy['enemy_name']} is affected by {dot['effect_name']}."
                )
                self._append_elemental_log(session, result, enemy["enemy_name"])
        else:
            session.game_log.extend(result.logs)
            self._append_elemental_log(session, result, enemy["enemy_name"])

        for raw_se in getattr(result, "status_effects", []) or []:
            raw_se.setdefault("target", ability_meta.get("target_type", "self"))
            se = self._normalize_se(raw_se)
            bucket = "player_effects" if se["target"] == "self" else "enemy_effects"
            session.battle_state[bucket].append(se)

            if se["target"] == "self":
                session.game_log.append(
                    f"{se['effect_name']} has been applied to <@{pid}>."
                )
                SessionPlayerModel.update_status_effects(
                    session.session_id, pid, session.battle_state[bucket]
                )
            else:
                name = session.current_enemy.get("enemy_name", "The enemy")
                session.game_log.append(
                    f"{name} has been afflicted by {se['effect_name']}."
                )

        session.temp_ability_cooldowns.setdefault(pid, {})[temp_ability_id] = ability_meta.get("cooldown_turns", 0)

        if result.type in ("damage", "heal", "set_hp", "dot", "hot"):
            if result.type == "damage":
                enemy["hp"] = max(enemy["hp"] - result.amount, 0)
            elif result.type == "heal":
                if target in ("self", "ally"):
                    new_hp = min(player["hp"] + result.amount, player["max_hp"])
                    self._update_player_hp(pid, session.session_id, new_hp)
                    session.game_log.append(f"You restore {result.amount} HP to yourself!")
                else:
                    enemy["hp"] = min(enemy["hp"] + result.amount, enemy["max_hp"])
                    session.game_log.append(f"{enemy['enemy_name']} recovers {result.amount} HP!")
            elif result.type == "set_hp":
                enemy["hp"] = result.amount
            elif result.type == "dot":
                enemy.setdefault("dot_effects", []).append(result.dot)
                enemy["hp"] = max(enemy["hp"] - result.dot["damage_per_turn"], 0)
            elif result.type == "hot":
                enemy.setdefault("dot_effects", []).append(result.dot)
                enemy["hp"] = min(
                    enemy["hp"] + result.dot.get("heal_per_turn", 0),
                    enemy["max_hp"]
                )

        if enemy["hp"] <= 0:
            return await self.handle_enemy_defeat(interaction, session, enemy)

        await self.update_battle_embed(interaction, pid, enemy)
        await asyncio.sleep(1)
        await self.enemy_turn(interaction, enemy)

    # --------------------------------------------------------------------- #
    #                          Enemy –> Player turn                         #
    # --------------------------------------------------------------------- #
    
    async def enemy_turn(self, interaction: discord.Interaction, enemy: Dict[str, Any]) -> None:
        mgr = self.bot.get_cog("SessionManager")
        if not mgr:
            return
        session = mgr.get_session(interaction.channel.id)
        if not session:
            return
        # if battle is over (enemy cleared out), don't keep looping
        if not session.battle_state or session.current_enemy is None or session.current_enemy.get("hp", 0) <= 0:
            return
        
        # 1) tick all enemy effects for this turn
        await session._status_engine.tick_combat("enemy")
        if enemy["hp"] <= 0:
            return await self.handle_enemy_defeat(interaction, session, enemy)
        # 2) then tick all player effects immediately before enemy acts
        await session._status_engine.tick_combat("player")

        # 2) fetch fresh player stats
        pid = session.current_turn
        conn = self.db_connect()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            "SELECT hp, max_hp, defense, magic_defense, accuracy, evasion "
            "FROM players WHERE player_id = %s AND session_id = %s",
            (pid, session.session_id),
        )
        player = cursor.fetchone()
        cursor.close(); conn.close()

        # 3) pick an ability (or None)
        ability = self.choose_enemy_ability(session, enemy)

        # 4) fallback to plain attack
        if not ability:
            dmg = self.ability.jrpg_damage(
                enemy, player,
                base_damage=0,
                scaling_stat="attack_power",
                scaling_factor=1.0
            )
            session.game_log.append(f"{enemy['enemy_name']} attacks for {dmg} damage!")
            new_hp = max(player["hp"] - dmg, 0)
            self._update_player_hp(pid, session.session_id, new_hp)
            if new_hp <= 0:
                return await self._kill_player(interaction, pid, session)
            await self.update_battle_embed(interaction, pid, enemy)
            return await self._end_enemy_action(interaction)

        # 5) otherwise resolve the chosen ability
        result = self.ability.resolve(enemy, player, ability)

        # 6) apply any status effects first (e.g. enemy‐inflicted DoT/HoT)
        for raw_se in getattr(result, "status_effects", []):
            se = self._normalize_se(raw_se)
            # these are coming from the enemy → must go on the player
            session.battle_state["player_effects"].append(se)
            session.game_log.append(
                f"{enemy['enemy_name']} inflicts **{se['effect_name']}** on you for {se['remaining']} turns."
            )

        # 7) unified logging for each result type
        if result.type == "miss":
            session.game_log.append(
                f"{enemy['enemy_name']} uses {ability['ability_name']} but misses!"
            )
            await self.update_battle_embed(interaction, pid, enemy)
            return await self._end_enemy_action(interaction)

        if result.type == "heal":
            enemy["hp"] = min(enemy["hp"] + result.amount, enemy["max_hp"])
            session.game_log.append(
                f"{enemy['enemy_name']} uses {ability['ability_name']} and heals for {result.amount} HP!"
            )
            await self.update_battle_embed(interaction, pid, enemy)
            return await self._end_enemy_action(interaction)

        if result.type == "set_hp":
            enemy["hp"] = result.amount
            session.game_log.append(
                f"{enemy['enemy_name']} is reduced to 1 HP by {ability['ability_name']}!"
            )
            if enemy["hp"] <= 0:
                return await self.handle_enemy_defeat(interaction, session, enemy)
            await self.update_battle_embed(interaction, pid, enemy)
            return await self._end_enemy_action(interaction)

        if result.type == "dot":
            dot = result.dot
            # apply the DoT on the **player** side
            session.battle_state["player_effects"].append(dot)
            # immediate first tick
            new_hp = max(player["hp"] - dot["damage_per_turn"], 0)
            self._update_player_hp(pid, session.session_id, new_hp)
            session.game_log.append(
                f"<@{pid}> has been hurt from {dot['effect_name']} for {dot['damage_per_turn']} HP."
            )
            await self.update_battle_embed(interaction, pid, enemy)
            return await self._end_enemy_action(interaction)

        if result.type == "hot":
            dot = result.dot
            session.battle_state["player_effects"].append(dot)
            heal = dot.get("heal_per_turn", 0)
            new_hp = min(player["hp"] + heal, player["max_hp"])
            self._update_player_hp(pid, session.session_id, new_hp)
            session.game_log.append(
                f"<@{pid}> is healed by {dot['effect_name']} for {heal} HP."
            )
            await self.update_battle_embed(interaction, pid, enemy)
            return await self._end_enemy_action(interaction)

        if result.type == "damage":
            dmg = result.amount
            # barrier check
            if any(b["effect_name"] == "Barrier" for b in session.battle_state["player_effects"]):
                dmg //= 2
                session.game_log.append("🛡️ Barrier halves the incoming damage!")
            new_hp = max(player["hp"] - dmg, 0)
            self._update_player_hp(pid, session.session_id, new_hp)
            session.game_log.append(
                f"{enemy['enemy_name']} uses {ability['ability_name']} and deals {dmg} damage!"
            )
            if new_hp <= 0:
                return await self._kill_player(interaction, pid, session)
            await self.update_battle_embed(interaction, pid, enemy)
            return await self._end_enemy_action(interaction)

        if result.type in ("pilfer", "mug"):
            if result.type == "pilfer":
                steal = result.amount
                self._steal_gil(pid, session.session_id, steal)
                enemy["gil_pool"] -= steal
                session.game_log.append(
                    f"{enemy['enemy_name']} uses {ability['ability_name']} and pilfers {steal} Gil!"
                )
            else:
                dmg = result.amount
                enemy["hp"] = max(enemy["hp"] - dmg, 0)
                session.game_log.append(
                    f"{enemy['enemy_name']} uses {ability['ability_name']} and deals {dmg} damage!"
                )
                if enemy["hp"] <= 0:
                    return await self.handle_enemy_defeat(interaction, session, enemy)

            await self.update_battle_embed(interaction, pid, enemy)
            return await self._end_enemy_action(interaction)

        # 8) final fallback (should rarely hit)
        await self.update_battle_embed(interaction, pid, enemy)
        return await self._end_enemy_action(interaction)



    async def handle_attack(self, interaction: discord.Interaction) -> None:
        mgr = self.bot.get_cog("SessionManager")
        if not mgr or not self.embed_manager:
            # safe‐exit without double‑respond
            if not interaction.response.is_done():
                await interaction.response.send_message(
                    "❌ SessionManager or EmbedManager not available.", ephemeral=True
                )
            else:
                await interaction.followup.send(
                    "❌ SessionManager or EmbedManager not available.", ephemeral=True
                )
            return

        session = mgr.get_session(interaction.channel.id)
        if not session or not session.battle_state or not session.battle_state.get("enemy"):
            if not interaction.response.is_done():
                await interaction.response.send_message("❌ No active battle found.", ephemeral=True)
            else:
                await interaction.followup.send("❌ No active battle found.", ephemeral=True)
            return

        enemy = session.current_enemy
        pid = session.current_turn
        conn = self.db_connect()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            "SELECT hp, max_hp, defense, attack_power FROM players WHERE player_id = %s AND session_id = %s",
            (pid, session.session_id),
        )
        player = cursor.fetchone()
        cursor.close(); conn.close()
        dmg = self.ability.jrpg_damage(player, enemy, base_damage=0, scaling_stat="attack_power", scaling_factor=1.0)
        enemy["hp"] = max(enemy["hp"] - dmg, 0)
        session.game_log.append(f"You strike the {enemy['enemy_name']} for {dmg} damage!")
        self.reduce_player_cooldowns(session, pid)

        if await self._check_eidolon_attunement(interaction, session, enemy):
            return
        if enemy["hp"] <= 0:
            return await self.handle_enemy_defeat(interaction, session, enemy)

        # 1) show your strike…
        await self.update_battle_embed(interaction, pid, enemy)
        # 2) brief pause so it’s visible
        await asyncio.sleep(1)
        # 3) now let the enemy take its turn (enemy_turn will refresh and then call end‐of‐turn)
        return await self.enemy_turn(interaction, enemy)

    # --------------------------------------------------------------------- #
    #                            Victory embed                              #
    # --------------------------------------------------------------------- #
    async def display_victory_embed(self, interaction: discord.Interaction, session: Any, enemy: dict) -> None:
        self.embed_manager = self.embed_manager or self.bot.get_cog("EmbedManager")
        if not self.embed_manager:
            logger.warning("EmbedManager missing; cannot render victory embed.")
            return
        reward_text = await self.award_loot(session, enemy)
        eb = discord.Embed(title="Victory!", color=discord.Color.gold())
        if enemy.get("image_url"):
            eb.set_image(url=enemy["image_url"] + f"?t={int(time.time())}")
        recent = session.game_log[-5:]
        eb.add_field(name="Battle Log", value="\n".join(recent) or "No actions recorded.", inline=False)
        eb.add_field(name="Rewards", value=reward_text, inline=False)
        btns = [("Continue", discord.ButtonStyle.primary, "battle_victory_continue", 0)]
        await self.embed_manager.send_or_update_embed(interaction, title="", description="", embed_override=eb, buttons=btns)
        session.victory_embed_sent = True

    # --------------------------------------------------------------------- #
    #                              Loot / XP                                #
    # --------------------------------------------------------------------- #
    async def award_loot(self, session: Any, enemy: dict) -> str:
        mgr = self.bot.get_cog("SessionManager")
        if not mgr:
            return ""
        sid, pid = session.session_id, session.current_turn
        xp = enemy.get("xp_reward", 0) or 0
        gil = enemy.get("gil_drop", 0)
        item_id, qty = enemy.get("loot_item_id"), enemy.get("loot_quantity", 0)
        lines: List[str] = []
        if xp:
            lines.append(f"You gained {xp} XP.")
        if gil:
            lines.append(f"You received {gil} Gil.")

        conn = self.db_connect()
        cursor = conn.cursor(dictionary=True)
        if enemy.get("enemy_id"):
            cursor.execute(
                "SELECT item_id, drop_chance, min_qty, max_qty FROM enemy_drops WHERE enemy_id = %s",
                (enemy["enemy_id"],),
            )
            drops = cursor.fetchall()
        else:
            drops = []
        if item_id:
            drops.append({"item_id": item_id, "drop_chance": 1.0, "min_qty": qty, "max_qty": qty})

        awards: Dict[int, int] = {}
        for d in drops:
            if random.random() <= d["drop_chance"]:
                n = random.randint(d["min_qty"], d["max_qty"])
                awards[d["item_id"]] = awards.get(d["item_id"], 0) + n

        cursor.execute("SELECT gil, inventory FROM players WHERE player_id = %s AND session_id = %s", (pid, sid))
        pd = cursor.fetchone()
        if pd:
            new_gil = pd["gil"] + gil
            inv = json.loads(pd["inventory"] or "{}")
            for iid, n in awards.items():
                cursor.execute("SELECT item_name FROM items WHERE item_id = %s", (iid,))
                row = cursor.fetchone()
                name = row["item_name"] if row else "Unknown Item"
                lines.append(f"You received {n} × {name}.")
                inv[str(iid)] = inv.get(str(iid), 0) + n
            cursor.execute(
                "UPDATE players SET gil = %s, inventory = %s WHERE player_id = %s AND session_id = %s",
                (new_gil, json.dumps(inv), pid, sid),
            )
            conn.commit()

        cursor.close(); conn.close()
        return "\n".join(lines) if lines else "No rewards."

    # --------------------------------------------------------------------- #
    #                          Inventory / flee                             #
    # --------------------------------------------------------------------- #
    async def handle_item_menu(self, interaction: discord.Interaction) -> None:
        inv = self.bot.get_cog("InventoryShop")
        if inv:
            return await inv.display_use_item_menu(interaction)
        else:
            await interaction.response.send_message("❌ Inventory system not available.", ephemeral=True)

    async def handle_flee(self, interaction: discord.Interaction) -> None:
        mgr = self.bot.get_cog("SessionManager")
        if not mgr or not self.embed_manager:
            return await interaction.response.send_message("❌ SessionManager or EmbedManager not available.", ephemeral=True)
        session = mgr.get_session(interaction.channel.id)
        if not session:
            return await interaction.response.send_message("❌ No active session found.", ephemeral=True)
        session.clear_battle_state()
        session.victory_pending = False
        session.game_log.append("You fled the battle!")
        await mgr.refresh_current_state(interaction)

    # --------------------------------------------------------------------- #
    #                       Component interaction router                    #
    # --------------------------------------------------------------------- #
    @commands.Cog.listener()
    async def on_interaction(self, interaction: discord.Interaction) -> None:
        if interaction.type != discord.InteractionType.component:
            return
        cid = interaction.data.get("custom_id", "")

        mgr = self.bot.get_cog("SessionManager")
        session = mgr.get_session(interaction.channel.id) if mgr else None

        if cid == "battle_victory_continue":
            if not interaction.response.is_done():
                await interaction.response.defer()
            if session:
                session.victory_pending = False
                conn = self.db_connect()
                with conn.cursor(dictionary=True) as cur:
                    cur.execute(
                        "SELECT coord_x, coord_y, current_floor_id FROM players WHERE player_id=%s AND session_id=%s",
                        (session.current_turn, session.session_id),
                    )
                    pos = cur.fetchone()
                conn.close()
                if pos:
                    x, y, floor = pos["coord_x"], pos["coord_y"], pos["current_floor_id"]
                    conn = self.db_connect()
                    with conn.cursor() as cur:
                        cur.execute(
                            """
                            UPDATE rooms
                            SET room_type = 'safe', default_enemy_id = NULL
                            WHERE session_id=%s AND floor_id=%s AND coord_x=%s AND coord_y=%s
                            """,
                            (session.session_id, floor, x, y),
                        )
                    conn.commit()
                    conn.close()
                session.clear_battle_state()
            gm = self.bot.get_cog("GameMaster")
            if gm:
                await gm.end_player_turn(interaction)
            else:
                sm = self.bot.get_cog("SessionManager")
                await sm.refresh_current_state(interaction)
            return

        if cid == "combat_skill_menu":
            return await self.handle_skill_menu(interaction)
        if cid == "combat_item":
            return await self.handle_item_menu(interaction)
        if cid == "combat_summon_menu":
            return await self.show_summon_menu(interaction)
        if cid == "combat_eidolon_menu":
            if session and getattr(session, "active_summons", None):
                active = session.active_summons.get(session.current_turn)
                if active:
                    return await self.show_eidolon_ability_menu(interaction, active["eidolon_id"])
            return await interaction.response.send_message("❌ No active Eidolon to command.", ephemeral=True)
        if cid.startswith("summon_select_"):
            eidolon_id = int(cid.split("_", 2)[2])
            return await self.handle_summon_select(interaction, eidolon_id)
        if cid.startswith("summon_ability_"):
            _, _, eidolon_id, ability_id = cid.split("_", 3)
            return await self.handle_eidolon_ability_use(interaction, int(eidolon_id), int(ability_id))
        if cid == "summon_back":
            if session and session.current_enemy:
                return await self.update_battle_embed(interaction, session.current_turn, session.current_enemy)
            sm = self.bot.get_cog("SessionManager")
            return await sm.refresh_current_state(interaction) if sm else None
        if not cid.startswith("combat_"):
            return

        # Anything from the combat_* namespace should acknowledge missing context early
        if not session:
            return await interaction.response.send_message("❌ No active session found.", ephemeral=True)

        if cid == "combat_trance_back":
            if session.current_enemy:
                return await self.update_battle_embed(interaction, session.current_turn, session.current_enemy)
            return await interaction.response.send_message("❌ No active battle to return to.", ephemeral=True)

        if session.current_enemy and session.current_turn != interaction.user.id:
            if interaction.response.is_done():
                await interaction.followup.send("❌ It isn't your turn.", ephemeral=True)
            else:
                await interaction.response.send_message("❌ It isn't your turn.", ephemeral=True)
            return
        if cid.startswith("combat_skill_") and cid != "combat_skill_back":
            aid = int(cid.split("_", 2)[2])
            # fetch its target_type
            conn = self.db_connect()
            cur = conn.cursor(dictionary=True)
            cur.execute("SELECT target_type FROM abilities WHERE ability_id=%s", (aid,))
            meta = cur.fetchone()
            cur.close(); conn.close()
            # allow “self” or “any” outside battle
            if meta and meta["target_type"] in ("self", "any") and not (session and session.current_enemy):
                return await self.handle_skill_use(interaction, aid)
            # otherwise fall back
            return await self.handle_skill_use(interaction, aid)

        if cid.startswith("combat_temp_"):
            tid = int(cid.split("_", 2)[2])
            return await self.handle_temp_skill_use(interaction, tid)
        

        try:
            if cid == "combat_trance_menu":
                return await self.display_trance_menu(interaction)
            if cid.startswith("combat_trance_"):
                aid = int(cid.split("_", 2)[2])
                return await self.handle_skill_use(interaction, aid)
            if cid == "combat_skill_back":
                if session and session.current_enemy:
                    return await self.update_battle_embed(interaction, session.current_turn, session.current_enemy)
                else:
                    return await mgr.refresh_current_state(interaction)
            if cid == "combat_attack":
                return await self.handle_attack(interaction)
            if cid == "combat_flee":
                return await self.handle_flee(interaction)
        except Exception as e:
            logger.error("Error handling combat interaction '%s': %s", cid, e, exc_info=True)
            await interaction.followup.send("❌ An error occurred processing battle action.", ephemeral=True)

    # --------------------------------------------------------------------- #
    #                   Embed helpers for other states                      #
    # --------------------------------------------------------------------- #
    async def send_battle_menu(
        self,
        interaction: discord.Interaction,
        enemy_name: Optional[str] = None,
        enemy_hp: Optional[int] = None,
        enemy_max_hp: Optional[int] = None,
    ) -> None:
        title = "⚔️ You are in battle..."
        desc = f"A {enemy_name} appears!\nHP: {enemy_hp}/{enemy_max_hp}" if enemy_name else "Choose your action!"
        buttons = [
            ("Attack", discord.ButtonStyle.danger, "combat_attack", 0),
            ("Skill",  discord.ButtonStyle.primary, "combat_skill_menu", 0),
            ("Use",    discord.ButtonStyle.success, "combat_item", 0),
            ("Flee",   discord.ButtonStyle.secondary, "combat_flee", 0),
            ("Menu",   discord.ButtonStyle.secondary, "action_menu", 0),
        ]
        mgr = self.bot.get_cog("SessionManager")
        if mgr:
            session = mgr.get_session(interaction.channel.id)
            if session:
                class_name = self._get_player_class_name(session.session_id, session.current_turn)
                unlocked = SessionPlayerModel.get_unlocked_eidolons(session.session_id, session.current_turn)
                session.summon_used = getattr(session, "summon_used", {}) or {}
                session.active_summons = getattr(session, "active_summons", {}) or {}
                if (
                    class_name == "Summoner"
                    and unlocked
                    and not session.summon_used.get(session.current_turn)
                    and not session.active_summons.get(session.current_turn)
                ):
                    buttons.append(("Summon", discord.ButtonStyle.primary, "combat_summon_menu", 1))
        await self.embed_manager.send_or_update_embed(interaction, title, desc, buttons=buttons)

    async def send_inventory_menu(self, interaction: discord.Interaction) -> None:
        title, desc = "🎒 Your Inventory", "Choose an item to use in battle."
        conn = self.db_connect()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT item_name, item_id FROM items")
        items = cursor.fetchall()
        cursor.close(); conn.close()
        buttons = [(it["item_name"], discord.ButtonStyle.primary, f"item_{it['item_id']}", 0) for it in items]
        await self.embed_manager.send_or_update_embed(interaction, title, desc, buttons=buttons)

    async def send_npc_shop_embed(
        self,
        interaction: discord.Interaction,
        vendor_name: str,
        dialogue: str,
        image_url: str,
        player_currency: int,
    ) -> None:
        title = f"Shop: {vendor_name}"
        desc = f"{dialogue}\n\n**Your Gil:** {player_currency}"
        buttons = [
            ("Buy",  discord.ButtonStyle.primary, "shop_buy_menu", 0),
            ("Sell", discord.ButtonStyle.primary, "shop_sell_menu", 0),
            ("Back", discord.ButtonStyle.secondary, "shop_back_main", 0),
        ]
        await self.embed_manager.send_or_update_embed(interaction, title, desc, image_url=image_url, buttons=buttons)

    async def send_or_update_embed(
        self,
        interaction: discord.Interaction,
        title: str,
        description: str,
        image_url: Optional[str] = None,
        fields: Optional[List[Tuple[str, str, bool]]] = None,
        buttons: Optional[List[Tuple[str, discord.ButtonStyle, str, int]]] = None,
        embed_override: Optional[discord.Embed] = None,
        view_override: Optional[discord.ui.View] = None,
        channel: Optional[discord.abc.Messageable] = None,
    ) -> Optional[discord.Message]:
        if not self.embed_manager:
            self.embed_manager = self.bot.get_cog("EmbedManager")
        if self.embed_manager:
            return await self.embed_manager.send_or_update_embed(
                interaction,
                title,
                description,
                image_url=image_url,
                fields=fields,
                buttons=buttons,
                embed_override=embed_override,
                view_override=view_override,
                channel=channel,
            )
        return None

    # --------------------------------------------------------------------- #
    #                            Internal helpers                           #
    # --------------------------------------------------------------------- #
    def _update_player_hp(self, player_id: int, session_id: int, new_hp: int):
        conn = self.db_connect()
        cur = conn.cursor()
        cur.execute(
            "UPDATE players SET hp=%s WHERE player_id=%s AND session_id=%s",
            (new_hp, player_id, session_id),
        )
        conn.commit()
        cur.close(); conn.close()

    def _steal_gil(self, player_id: int, session_id: int, amount: int):
        conn = self.db_connect()
        cur = conn.cursor()
        cur.execute(
            "UPDATE players SET gil = gil + %s WHERE player_id=%s AND session_id=%s",
            (amount, player_id, session_id),
        )
        conn.commit()
        cur.close(); conn.close()

    # ─── New: fetch current & max HP for DoT/HoT ─────────────────────────
    def _get_player_hp(self, player_id: int, session_id: int) -> int:
        conn = self.db_connect()
        cur = conn.cursor()
        cur.execute("SELECT hp FROM players WHERE player_id=%s AND session_id=%s",
                    (player_id, session_id))
        row = cur.fetchone()
        cur.close(); conn.close()
        return row[0] if row else 0

    def _get_player_max_hp(self, player_id: int, session_id: int) -> int:
        conn = self.db_connect()
        cur = conn.cursor()
        cur.execute("SELECT max_hp FROM players WHERE player_id=%s AND session_id=%s",
                    (player_id, session_id))
        row = cur.fetchone()
        cur.close(); conn.close()
        return row[0] if row else 0

    async def _kill_player(self, interaction, pid, session):
        # 1) force the DB → 0 HP so the next embed shows 0/max
        self._update_player_hp(pid, session.session_id, 0)

        # 2) mark them dead
        conn = self.db_connect()
        cur = conn.cursor()
        cur.execute(
            "UPDATE players SET is_dead=TRUE WHERE player_id=%s AND session_id=%s",
            (pid, session.session_id),
        )
        conn.commit()
        cur.close()
        conn.close()
        SessionPlayerModel.set_player_dead(session.session_id, pid)

        # 3) hand off to SessionManager/GameMaster to render the “💀 You have fallen” embed
        sm = self.bot.get_cog("SessionManager")
        return await sm.refresh_current_state(interaction)

    async def _end_enemy_action(self, interaction):
        sm = self.bot.get_cog("SessionManager")
        session = sm.get_session(interaction.channel.id) if sm else None
        if sm and session:
            sm.set_room_refresh_intent(session, False)
        gm = self.bot.get_cog("GameMaster")
        if gm:
            return await gm.end_player_turn(interaction)
        if sm and session and not sm.consume_room_refresh_intent(session):
            return None
        if sm:
            return await sm.refresh_current_state(interaction)
        return None


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(BattleSystem(bot))
    logger.info("BattleSystem cog loaded with AbilityEngine integration.")
