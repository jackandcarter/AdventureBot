# cogs/game_master.py

from __future__ import annotations
import re
import asyncio
import json
import logging
import time
from typing import Any, Dict, List, Optional, Set, Tuple

import discord
from discord import Interaction, InteractionType
from discord.ext import commands
import mysql.connector
import aiomysql
from utils.status_engine  import StatusEffectEngine
from utils.ui_helpers     import get_emoji_for_room_type  # For minimap icons, if needed
from models.database import Database
from core.game_session    import GameSession
from models.session_models import (
    SessionModel,
    SessionPlayerModel,
    ClassModel,
)
from hub import hub_embed

from .treasure_chest import TreasureChestCog

logger = logging.getLogger("GameMaster")
logger.setLevel(logging.DEBUG)


def build_queue_embed_field(player_ids: List[int],
                            guild: discord.Guild,
                            max_slots: int = 6) -> str:
    """Build a list of mentions (or placeholders) up to max_slots."""
    mentions = []
    for pid in player_ids:
        member = guild.get_member(pid)
        if member:
            mentions.append(f"<@{member.id}> ({member.display_name})")
        else:
            mentions.append(f"<@{pid}>")
    while len(mentions) < max_slots:
        mentions.append("Empty Slot")
    return "\n\n".join(mentions)


def _build_queue_view() -> discord.ui.View:
    """Return a view with the Start Game button."""
    v = discord.ui.View(timeout=None)
    v.add_item(discord.ui.Button(
        label="Start Game",
        style=discord.ButtonStyle.blurple,
        custom_id="start_game"
    ))
    return v


def build_queue_embed(owner: discord.Member, session_id: int) -> discord.Embed:
    """Build the waiting-for-players embed."""
    players = SessionPlayerModel.get_players(session_id)
    embed   = discord.Embed(
        title="Game Session: Waiting for Players",
        description=(
            "This session is in the queue.\n\n"
            "Players joining via the hub will appear below.\n\n"
            "When ready, the session creator may click **Start Game**."
        ),
        color=discord.Color.green()
    )
    embed.add_field(
        name="Players",
        value=build_queue_embed_field(players, owner.guild),
        inline=False
    )
    embed.set_footer(text=f"Session ID: {session_id}")
    return embed


def _player_has_key(session_id: int, player_id: int) -> bool:
    """True if the player has at least one quest/key item."""
    return SessionPlayerModel.get_key_count(session_id, player_id) > 0


def _consume_key(session_id: int, player_id: int) -> bool:
    """Consume one key from the player's key‐item inventory."""
    return SessionPlayerModel.consume_key(session_id, player_id)






class GameMaster(commands.Cog):
    """Primary gameplay director – dungeon flow, player actions, etc."""
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.db = Database()
        # intro_data[ thread_id ] = {"steps": [...], "current_index": int}
        self.intro_data: Dict[int, Dict[str, Any]] = {}
        logger.debug("★ GameMaster initialised.")

    def db_connect(self) -> mysql.connector.MySQLConnection:
        conn = self.db.get_connection()
        conn.autocommit = True
        return conn

    async def adb_connect(self):
        from models.database import AsyncDatabase
        return await AsyncDatabase().get_connection()

    def _player_has_auto_revive(self, session_id: int, player_id: int) -> bool:
        """
        Return True if the player’s inventory contains an item whose JSON `effect`
        blob has a `revive` field.
        """
        inv = SessionPlayerModel.get_inventory(session_id, player_id)
        if not inv:
            return False

        placeholders = ",".join("%s" for _ in inv)
        try:
            conn = self.db_connect()
            cur  = conn.cursor()
            cur.execute(
                f"SELECT 1 FROM items WHERE item_id IN ({placeholders}) "
                "AND JSON_EXTRACT(effect,'$.revive') IS NOT NULL LIMIT 1",
                tuple(int(i) for i in inv.keys())
            )
            return cur.fetchone() is not None
        except Exception:
            logger.exception("Error checking auto‑revive item")
            return False
        finally:
            cur.close()
            conn.close()

    def _render_local_map(
        self,
        all_rooms: List[Dict[str, Any]],
        center: Tuple[int, int],
        discovered: Set[Tuple[int,int]],
        reveal: Set[Tuple[int,int]],
    ) -> str:
        """
        Return a 5×5 map centered on `center` using the same emojis
        as your full minimap (via get_emoji_for_room_type).
        Unknown / out‑of‑bounds = ⬛.
        """
        x0, y0 = center
        # build lookup: (x,y) → room_type
        room_map = { (r["coord_x"], r["coord_y"]): r["room_type"] for r in all_rooms }

        def ch(x: int, y: int) -> str:
            if (x, y) == (x0, y0):
                return "🤺"
            # only reveal if discovered or peeking
            if (x,y) in discovered or (x,y) in reveal:
                rtype = room_map.get((x, y), None)
                return get_emoji_for_room_type(rtype)
            return "⬛"

        lines = []
        for dy in range(-2, 3):  # -2, -1, 0, 1, 2
            row = "".join(ch(x0 + dx, y0 + dy) for dx in range(-2, 3))
            lines.append(row)
        return "\n".join(lines)


    def fetch_intro_steps(self) -> List[Dict[str, Any]]:
        """Load all intro steps from the DB."""
        try:
            conn = self.db_connect()
            with conn.cursor(dictionary=True) as cur:
                cur.execute("SELECT * FROM intro_steps ORDER BY step_order")
                steps = cur.fetchall()
            conn.close()
            return steps
        except Exception as e:
            logger.error("fetch_intro_steps: %s", e)
            return []

    def append_game_log(self, session_id: int, line: str, keep: int = 10) -> None:
        """Append a line to the session's game_log JSON array."""
        try:
            conn = self.db_connect()
            with conn.cursor(dictionary=True) as cur:
                cur.execute("SELECT game_log FROM sessions WHERE session_id=%s", (session_id,))
                row = cur.fetchone()
                log = json.loads(row["game_log"]) if row and row["game_log"] else []
                log.append(line)
                log = log[-keep:]
                cur.execute("UPDATE sessions SET game_log=%s WHERE session_id=%s",
                            (json.dumps(log), session_id))
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error("append_game_log: %s", e)

    def get_game_log(self, session_id: int, last: int = 5) -> str:
        """Retrieve the last `last` lines from the game_log."""
        try:
            conn = self.db_connect()
            with conn.cursor(dictionary=True) as cur:
                cur.execute("SELECT game_log FROM sessions WHERE session_id=%s", (session_id,))
                row = cur.fetchone()
            conn.close()
            if row and row.get("game_log"):
                return "\n".join(json.loads(row["game_log"])[-last:])
            return "*No recent actions.*"
        except Exception as e:
            logger.error("get_game_log: %s", e)
            return "*No recent actions.*"

    async def update_permanent_discovered_room(
        self,
        player_id: int,
        session_id: int,
        pos: Tuple[int, int, int],
    ) -> set[Tuple[int, int, int]]:
        """Mark the given (floor, x, y) as permanently discovered for the player."""
        try:
            conn = self.db_connect()
            with conn.cursor(dictionary=True) as cur:
                cur.execute(
                    "SELECT discovered_rooms FROM players WHERE player_id=%s AND session_id=%s",
                    (player_id, session_id)
                )
                row = cur.fetchone()
                raw = json.loads(row["discovered_rooms"]) if row and row.get("discovered_rooms") else []
                # build a set of (floor, x, y) tuples
                discovered: set[Tuple[int,int,int]] = {tuple(entry) for entry in raw if len(entry) == 3}
                # (if you have any legacy 2-element entries, you can ignore or migrate them here)
                discovered.add(pos)
                cur.execute(
                    "UPDATE players SET discovered_rooms=%s WHERE player_id=%s AND session_id=%s",
                    (json.dumps([list(p) for p in discovered]), player_id, session_id)
                )
            conn.commit()
            conn.close()
            return discovered
        except Exception as e:
            logger.error("update_permanent_discovered_room: %s", e)
            return set()

    def _unlock_chest_room(self,
                           session_id: int,
                           floor_id:   int,
                           x: int,
                           y: int) -> None:
        """Flip the room to 'chest_unlocked' template."""
        conn = self.db_connect()
        cur = conn.cursor(dictionary=True)
        try:
            # 1) grab the unlocked‑chest template
            cur.execute(
                "SELECT description, image_url "
                "FROM room_templates "
                "WHERE room_type=%s "
                "LIMIT 1",
                ("chest_unlocked",),
            )
            tpl = cur.fetchone()
            if not tpl:
                return

            # 2) apply it in the same cursor
            cur.execute(
                "UPDATE rooms "
                "   SET room_type   = %s, "
                "       description = %s, "
                "       image_url   = %s "
                " WHERE session_id = %s "
                "   AND floor_id    = %s "
                "   AND coord_x     = %s "
                "   AND coord_y     = %s",
                (
                    "chest_unlocked",
                    tpl["description"],
                    tpl["image_url"],
                    session_id,
                    floor_id,
                    x,
                    y,
                ),
            )
            conn.commit()
        finally:
            cur.close()
            conn.close()

    # ────────────────────────────────────────────────────────────────────────────
    #  1. Create session → queue
    # ────────────────────────────────────────────────────────────────────────────
    async def create_session(self,
                             interaction: discord.Interaction,
                             max_slots: int = 6) -> None:
        sm = self.bot.get_cog("SessionManager")
        if not sm:
            return await interaction.response.send_message(
                "❌ SessionManager unavailable.", ephemeral=True
            )

        result = await sm.create_new_session(interaction)
        if not result:
            return
        thread, session_id = result

        # Send the queue embed into the private thread
        em = self.bot.get_cog("EmbedManager")
        embed = build_queue_embed(interaction.user, session_id)
        view  = _build_queue_view()
        if em:
            await em.send_or_update_embed(
                interaction,
                "", "",
                embed_override=embed,
                view_override=view,
                channel=thread
            )
        else:
            await thread.send(embed=embed, view=view)

        # Post LFG in the hub
        hub = self.bot.get_cog("HubManager")
        if hub and hasattr(hub, "post_lfg_post"):
            await hub.post_lfg_post(interaction, thread, session_id)

    # ────────────────────────────────────────────────────────────────────────────
    #  2. Class selection → difficulty
    # ────────────────────────────────────────────────────────────────────────────
    async def handle_class_selection(self,
                                     interaction: discord.Interaction,
                                     class_id: int) -> None:
        sm = self.bot.get_cog("SessionManager")
        session = sm.get_session(interaction.channel.id) if sm else None
        if not session:
            return await interaction.followup.send(
                "❌ No active session.", ephemeral=True
            )

        if not interaction.response.is_done():
            try:
                await interaction.response.defer()
            except discord.errors.HTTPException as e:
                logger.debug("Deferred interaction failed (already acknowledged): %s", e)

        SessionPlayerModel.update_player_class(
            session.session_id, interaction.user.id, class_id
        )
        cname = ClassModel.get_class_name(class_id)
        self.append_game_log(
            session.session_id,
            f"<@{interaction.user.id}> chose **{cname}**."
        )

        em = self.bot.get_cog("EmbedManager")
        total_players = len(
            SessionPlayerModel.get_player_states(session.session_id)
        )
        if em:
            await em.send_class_selection_embed(interaction, total_players)

        # If everyone has chosen, go to difficulty
        if all(p["class_id"]
               for p in SessionPlayerModel.get_player_states(session.session_id)):
            await self.send_difficulty_selection(interaction)

    async def send_difficulty_selection(self,
                                        interaction: discord.Interaction) -> None:
        em = self.bot.get_cog("EmbedManager")
        if em:
            await em.send_difficulty_selection(interaction)
        else:
            await interaction.followup.send(
                "❌ EmbedManager unavailable.", ephemeral=True
            )

    # ────────────────────────────────────────────────────────────────────────────
    #  3. Difficulty chosen → intro
    # ────────────────────────────────────────────────────────────────────────────
    async def start_session(self,
                            interaction: discord.Interaction,
                            difficulty: str) -> None:
        if not interaction.response.is_done():
            defer_fn = getattr(interaction.response, "defer_update", None)
            if callable(defer_fn):
                await defer_fn()
            else:
                await interaction.response.defer()
        sm = self.bot.get_cog("SessionManager")
        session = sm.get_session(interaction.channel.id) if sm else None
        if not session:
            return await interaction.followup.send(
                "❌ No session.", ephemeral=True
            )

        conn = self.db_connect()
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE sessions SET difficulty=%s WHERE session_id=%s",
                (difficulty, session.session_id)
            )
        conn.commit()
        conn.close()

        self.intro_data[interaction.channel.id] = {
            "steps": self.fetch_intro_steps(),
            "current_index": 0
        }
        self.append_game_log(
            session.session_id,
            f"Difficulty set to **{difficulty}**."
        )
        await self.begin_intro_sequence(interaction, interaction.channel.id)

    # ────────────────────────────────────────────────────────────────────────────
    #  4. Intro slideshow
    # ────────────────────────────────────────────────────────────────────────────
    async def begin_intro_sequence(self,
                                   interaction: discord.Interaction,
                                   chan_id: int) -> None:
        if not interaction.response.is_done():
            await interaction.response.defer()
        data = self.intro_data.get(chan_id)
        if not data:
            return

        idx, steps = data["current_index"], data["steps"]
        if idx >= len(steps):
            return await self.finish_intro_and_generate(interaction, chan_id)

        step = steps[idx]
        em = self.bot.get_cog("EmbedManager")
        if em:
            await em.send_intro_embed(
                interaction,
                title=step.get("title", "Intro"),
                description=step.get("description", "..."),
                image_url=step.get("image_url")
            )

        data["current_index"] += 1

    # ────────────────────────────────────────────────────────────────────────────
    #  5. Finish intro → dungeon gen & first room
    # ────────────────────────────────────────────────────────────────────────────
    async def finish_intro_and_generate(self, interaction: discord.Interaction, chan_id: int) -> None:
        if not interaction.response.is_done():
            await interaction.response.defer()

        # ←── SHOW “Generating Dungeon Layout…” FEEDBACK ────
        em = self.bot.get_cog("EmbedManager")
        if em:
            await em.send_or_update_embed(
                interaction,
                title="🧱 Generating Dungeon Layout…",
                description="Please hang tight while your dungeon is being created!",
            )
        else:
            # fallback if EmbedManager is missing
            await interaction.followup.send(
                embed=discord.Embed(
                    title="🧱 Generating Dungeon Layout…",
                    description="Please hang tight while your dungeon is being created!",
                    color=discord.Color.dark_gray()
                )
            )
        sm = self.bot.get_cog("SessionManager")
        session = sm.get_session(chan_id) if sm else None
        if not session:
            return await interaction.followup.send(
                "❌ Session missing.", ephemeral=True
            )

        conn = self.db_connect()
        with conn.cursor(dictionary=True) as cur:
            cur.execute(
                "SELECT difficulty FROM sessions WHERE session_id=%s",
                (session.session_id,)
            )
            diff_row = cur.fetchone()
        conn.close()

        difficulty = diff_row["difficulty"] if diff_row else "Easy"

        dg = self.bot.get_cog("DungeonGenerator")
        if not dg:
            return await interaction.followup.send(
                "❌ DungeonGenerator unavailable.", ephemeral=True
            )

        await dg.generate_dungeon_for_session(
            interaction, session.session_id, difficulty
        )
        self.append_game_log(session.session_id, "Dungeon generated.")

        # Step 1: Get first floor_id dynamically
        conn = self.db_connect()
        with conn.cursor(dictionary=True) as cur:
            cur.execute(
                "SELECT floor_id FROM floors WHERE session_id=%s ORDER BY floor_number ASC LIMIT 1",
                (session.session_id,)
            )
            floor_row = cur.fetchone()
        conn.close()

        if not floor_row:
            return await interaction.followup.send(
                "❌ No floors found after dungeon generation.", ephemeral=True
            )

        first_floor_id = floor_row["floor_id"]

        # Step 2: Reset player positions on correct floor
        conn = self.db_connect()
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE players SET coord_x=0, coord_y=0, current_floor_id=%s "
                "WHERE session_id=%s",
                (first_floor_id, session.session_id)
            )
        await self.update_permanent_discovered_room(
            session.owner_id,
            session.session_id,
            (first_floor_id, 0, 0)
        )

        conn.commit()
        conn.close()

        sm.set_initial_turn(chan_id)
        if session.current_turn is None:
            session.current_turn = session.owner_id

        self.append_game_log(
            session.session_id,
            f"<@{session.current_turn}> begins the journey!"
        )

        # Step 3: Fetch the starting room by floor_id
        conn = self.db_connect()
        with conn.cursor(dictionary=True) as cur:
            cur.execute("""
                SELECT r.*, f.floor_number
                FROM rooms r
                JOIN floors f ON f.floor_id = r.floor_id
                WHERE r.session_id=%s
                AND r.floor_id=%s
                AND r.coord_x=0
                AND r.coord_y=0
            """, (session.session_id, first_floor_id))
            room0 = cur.fetchone()
        conn.close()

        if not room0:
            return await interaction.followup.send(
                "❌ First room missing.", ephemeral=True
            )

        await self.update_room_view(interaction, room0, 0, 0)


    # ────────────────────────────────────────────────────────────────────────────
    #  Skip intro
    # ────────────────────────────────────────────────────────────────────────────
    async def skip_intro(self,
                         interaction: discord.Interaction,
                         chan_id: int) -> None:
        if not interaction.response.is_done():
            await interaction.response.defer()
        if chan_id in self.intro_data:
            self.intro_data[chan_id]["current_index"] = len(
                self.intro_data[chan_id]["steps"]
            )

        em = self.bot.get_cog("EmbedManager")
        if em:
            await em.send_or_update_embed(
                interaction, "", "", view_override=discord.ui.View()
            )
        await self.finish_intro_and_generate(interaction, chan_id)
    
    # ────────────────────────────────────────────────────────────────────────────
    #  **NEW**: Refresh the waiting‑for‑players embed when someone joins
    # ────────────────────────────────────────────────────────────────────────────
        # ────────────────────────────────────────────────────────────────────────────
    #  Refresh the waiting‑for‑players embed when someone joins
    # ────────────────────────────────────────────────────────────────────────────
    async def update_queue_embed(self, thread_id: int, session_id: int) -> None:
        # 1) grab the thread
        thread = self.bot.get_channel(thread_id)
        if not isinstance(thread, discord.Thread):
            logger.warning(f"update_queue_embed: channel {thread_id} is not a Thread")
            return

        # 2) make sure we still have a session
        sm = self.bot.get_cog("SessionManager")
        session = sm.get_session(thread_id) if sm else None
        if not session:
            return

        # 3) rebuild the embed & view
        owner = thread.guild.get_member(session.owner_id)
        if not owner:
            return
        new_embed = build_queue_embed(owner, session_id)
        new_view  = _build_queue_view()

        async for msg in thread.history(limit=20):
            if msg.author.id == self.bot.user.id and msg.embeds:
                emb = msg.embeds[0]
                footer = (emb.footer.text or "").strip()
                if footer.startswith(f"Session ID: {session_id}"):
                    await msg.edit(embed=new_embed, view=new_view)
                    return

        # 5) (fallback) if we didn’t find one, just send a new embed
        await thread.send(embed=new_embed, view=new_view)
        logger.warning(f"⚠️ Couldn’t find existing queue‑embed in thread {thread_id}, sent a new one")



    # ────────────────────────────────────────────────────────────────────────────
    #  Update room view (header, description, buttons)
    # ────────────────────────────────────────────────────────────────────────────
    async def update_room_view(self, interaction: discord.Interaction, room: Dict[str, Any], x: int, y: int, *, force_end_turn: bool = False) -> None:
        sm = self.bot.get_cog("SessionManager")
        session = sm.get_session(interaction.channel.id) if sm else None
        if not session:
            return await interaction.followup.send("❌ No active session.", ephemeral=True)
        # ─── if this player is dead, show the death‐embed under the main game embed ───────
        if SessionPlayerModel.is_player_dead(session.session_id, session.current_turn):
            # fetch “death” template
            conn = await self.adb_connect()
            async with conn.cursor(aiomysql.DictCursor) as cur:
                await cur.execute(
                    "SELECT description, image_url FROM room_templates WHERE room_type=%s LIMIT 1",
                    ("death",)
                )
                tpl = await cur.fetchone()
            conn.close()

            description = tpl["description"] if tpl else "You have fallen and can only be revived."
            image_url   = tpl["image_url"]    if tpl else None

            # build our button row
            view = discord.ui.View(timeout=None)
            # 1) Auto‑Raise if available
            if self._player_has_auto_revive(session.session_id, session.current_turn):
                view.add_item(discord.ui.Button(
                    label="Auto‑Raise",
                    style=discord.ButtonStyle.success,
                    custom_id="death_revive"
                ))
            # 2) “End My Turn” in multiplayer, else real Game Over
            all_pids   = SessionPlayerModel.get_players(session.session_id)
            alive_pids = [pid for pid in all_pids if not SessionPlayerModel.is_player_dead(session.session_id, pid)]
            if len(alive_pids) > 1:
                view.add_item(discord.ui.Button(
                    label="End My Turn",
                    style=discord.ButtonStyle.secondary,
                    custom_id="death_end_turn"
                ))
            else:
                view.add_item(discord.ui.Button(
                    label="Game Over",
                    style=discord.ButtonStyle.danger,
                    custom_id="death_game_over"
                ))

            # send as a normal thread message (so it appears under the room embed)
            death_embed = discord.Embed(
                title="💀 You have fallen",
                description=description,
                color=discord.Color.dark_gray()
            )
            if image_url:
                death_embed.set_image(url=image_url + f"?t={int(time.time())}")

            msg = await interaction.channel.send(embed=death_embed, view=view)
            # stash its ID so we can auto‐delete it later
            session.last_death_msg_id = msg.id

            return

        rtype = room["room_type"]

        # 1) IMMEDIATELY trigger ANY battle (monster, miniboss or boss)
        if rtype in ("monster","miniboss","boss") and room.get("default_enemy_id"):
            bs = self.bot.get_cog("BattleSystem")
            if bs:
                enemy = await bs.get_enemy_by_id(room["default_enemy_id"])
                if enemy:
                    self.append_game_log(session.session_id, f"Encountered **{enemy['enemy_name']}**!")
                    await bs.start_battle(
                        interaction,
                        session.current_turn,
                        enemy,
                        previous_coords=None
                    )
                    return

        # 2) Only *after* you've ruled out “we’re about to fight” do you do
        #    your staircase template reloads.
        if rtype in ("staircase_up", "staircase_down"):
            conn = await self.adb_connect()
            try:
                async with conn.cursor(aiomysql.DictCursor) as cur:
                    await cur.execute(
                        "SELECT description, image_url FROM room_templates WHERE room_type=%s LIMIT 1",
                        (rtype,)
                    )
                    tpl = await cur.fetchone()
                if tpl:
                    room["description"] = tpl["description"]
                    room["image_url"] = tpl["image_url"]
            finally:
                conn.close()

        # 3) All of your existing “pull player stats, build buttons,
        #    redraw embed” comes *after* both of the above.


        # Pull player stats for header
        p = None
        conn = await self.adb_connect()
        try:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                await cur.execute(
                    "SELECT hp, max_hp, gil FROM players "
                    "WHERE player_id=%s AND session_id=%s",
                    (session.current_turn, session.session_id)
                )
                p = await cur.fetchone()
        except Exception as e:
            logger.error("update_room_view db fetch error: %s", e)
        finally:
            conn.close()

        # ─────── Build local 3×3 map ────────────────────────────────
        # 1) get full discovered set and floor neighbors
        full_discovered = await self.update_permanent_discovered_room(
            session.current_turn,
            session.session_id,
            (room["floor_id"], x, y)
        )
        discovered_here = { (ff, xx, yy) for (ff, xx, yy) in full_discovered if ff == room["floor_id"] }
        neighbours = { (x+1,y), (x-1,y), (x, y+1), (x, y-1) }
        visible = { (xx,yy) for (_,xx,yy) in discovered_here } | neighbours

        # 2) fetch all rooms on this floor
        conn = await self.adb_connect()
        async with conn.cursor(aiomysql.DictCursor) as cur:
            await cur.execute(
                "SELECT coord_x, coord_y, room_type FROM rooms "
                "WHERE session_id=%s AND floor_id=%s",
                (session.session_id, room["floor_id"])
            )
            floor_rooms = await cur.fetchall()
        conn.close()

        # 3) render our 3×3 patch
        local_coords = { (xx, yy) for (_, xx, yy) in discovered_here }
        local_map = self._render_local_map(
            floor_rooms,
            (x, y),
            local_coords,
            visible
        )

        def _bar(curr, mx, ln=10):
            if not mx:
                return "[-]"
            filled = int(round(ln * curr / mx))
            return f"[{'█'*filled}{'░'*(ln-filled)}] {curr}/{mx}"

        header = ""
        if p:
            # 1) HP bar
            header += f"**HP:** {_bar(p['hp'], p['max_hp'])}\n"

            # 2) Status‐effects line (one per effect)
            from utils.ui_helpers import format_status_effects
            raw_buffs = SessionPlayerModel.get_status_effects(
                session.session_id, session.current_turn
            )
            if raw_buffs:
                normalized = []
                for se in raw_buffs:
                    icon = se.get("icon") or se.get("icon_url", "")
                    name = se.get("effect_name", "").strip()
                    rem  = se.get("remaining")
                    if rem is None:
                        rem = se.get("remaining_turns", 0)
                    if not icon or not name:
                        continue
                    normalized.append({"icon": icon, "effect_name": name, "remaining": rem})

                status_line = format_status_effects(normalized)
                if status_line:
                    header += f"**Status:** {status_line}\n"

            # 3) Gil always goes underneath
            header += f"\n**Gil:** {p['gil']}\n"


        desc = room.get("description") or ""
        recent = self.get_game_log(session.session_id)
        body = f"{header}{desc}\n\n**Recent Actions:**\n{recent}"

        em = self.bot.get_cog("EmbedManager")
        if not em:
            return await interaction.followup.send("❌ EmbedManager unavailable.", ephemeral=True)

        exits = None
        if room.get("exits"):
            try:
                exits = json.loads(room["exits"])
            except Exception:
                exits = None



        has_key = _player_has_key(session.session_id, session.current_turn)

        buttons = em.get_main_menu_buttons(
            directions=exits,
            include_shop=(room.get("vendor_id") is not None),
            vendor_id=room.get("vendor_id"),
            is_item=(room.get("room_type") == "item"),
            is_locked=(room.get("room_type") == "locked"),
            has_key=has_key,
            is_stair_up=(room.get("room_type") == "staircase_up"),
            is_stair_down=(room.get("room_type") == "staircase_down"),
        )

        # Chest logic: check if chest is still locked
        if room.get("room_type") == "item":
            conn = await self.adb_connect()
            try:
                async with conn.cursor(aiomysql.DictCursor) as cur:
                    await cur.execute(
                        """
                        SELECT tci.instance_id, tci.is_unlocked
                        FROM treasure_chest_instances tci
                        JOIN rooms r ON r.room_id = tci.room_id
                        WHERE tci.session_id = %s
                        AND r.floor_id = %s
                        AND r.coord_x = %s
                        AND r.coord_y = %s
                        LIMIT 1
                        """,
                        (
                            session.session_id,
                            room.get("floor_id"),
                            x, y
                        )
                    )
                    instance = await cur.fetchone()

                if instance and not instance["is_unlocked"]:
                    buttons.append(
                        (
                            "🗝️ Unlock Chest",
                            discord.ButtonStyle.primary,
                            f"open_chest_{instance['instance_id']}",
                            2,
                        )
                    )
            except Exception as e:
                logger.error("Chest button fetch failed: %s", e)
            finally:
                conn.close()

        img_url = room.get("image_url")
        if img_url:
            img_url += f"?t={int(time.time())}"


        # build a code‑block version of the map and stick it at the top
        map_block      = f"```{local_map}```\n\n"
        new_description = map_block + body

        # send the embed without a separate map-field—
        # the map now lives at the top of the description
        await em.send_or_update_embed(
            interaction,
            title=f"Room ({x}, {y}) F{room.get('floor_number', 1)}",
            description=new_description,
            image_url=img_url,
            buttons=buttons
        )


    # ────────────────────────────────────────────────────────────────────────────
    #  Handle Unlock Door action
    # ────────────────────────────────────────────────────────────────────────────
    async def handle_unlock_door(self, interaction: discord.Interaction) -> None:
        sm = self.bot.get_cog("SessionManager")
        session = sm.get_session(interaction.channel.id) if sm else None
        if not session:
            return await interaction.response.send_message("❌ No active session.", ephemeral=True)

        if not interaction.response.is_done():
            # Acknowledge the interaction without editing immediately
            # `defer_update` is unavailable in some discord.py versions
            defer_fn = getattr(interaction.response, "defer_update", None)
            if callable(defer_fn):
                await defer_fn()
            else:
                # Fall back to regular defer which behaves similarly
                await interaction.response.defer()

        # 1) player’s current position
        conn = self.db_connect()
        with conn.cursor(dictionary=True) as cur:
            cur.execute(
                "SELECT coord_x, coord_y, current_floor_id FROM players "
                "WHERE player_id=%s AND session_id=%s",
                (interaction.user.id, session.session_id),
            )
            pos = cur.fetchone()
        conn.close()
        if not pos:
            return await interaction.followup.send("❌ Position error.", ephemeral=True)
        x, y, floor = pos["coord_x"], pos["coord_y"], pos["current_floor_id"]

        # 2) fetch locked-room + inner_template info
        conn = self.db_connect()
        with conn.cursor(dictionary=True) as cur:
            cur.execute(
                """
                SELECT
                    r.room_id,
                    r.room_type,
                    r.inner_template_id,
                    tpl.room_type        AS new_room_type,
                    tpl.description      AS new_desc,
                    tpl.image_url        AS new_img,
                    tpl.default_enemy_id AS new_enemy
                FROM rooms r
                LEFT JOIN room_templates tpl
                  ON tpl.template_id = r.inner_template_id
                WHERE r.session_id = %s
                  AND r.floor_id   = %s
                  AND r.coord_x    = %s
                  AND r.coord_y    = %s
                """,
                (session.session_id, floor, x, y),
            )
            room = cur.fetchone()
        conn.close()

        if not room or room["room_type"] != "locked":
            return await interaction.followup.send("❌ Nothing to unlock here.", ephemeral=True)
        if not room["inner_template_id"] or not room["new_room_type"]:
            return await interaction.followup.send("❌ There’s nothing behind this door.", ephemeral=True)
        if not _player_has_key(session.session_id, interaction.user.id):
            return await interaction.followup.send("🚪 You have no key.", ephemeral=True)

        # 3) spend a key and log it
        _consume_key(session.session_id, interaction.user.id)
        self.append_game_log(session.session_id, f"<@{interaction.user.id}> unlocked the door.")

        # 4) capture stair linkage before overwrite
        conn = self.db_connect()
        with conn.cursor(dictionary=True) as cur:
            cur.execute(
                """
                SELECT stair_down_floor_id, stair_down_x, stair_down_y,
                       stair_up_floor_id,   stair_up_x,   stair_up_y
                FROM rooms
                WHERE room_id = %s
                """,
                (room["room_id"],),
            )
            stair_info = cur.fetchone()
        conn.close()

        # 5) reveal the inner room
        conn = self.db_connect()
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE rooms r
                JOIN room_templates tpl
                  ON tpl.template_id = r.inner_template_id
                SET
                  r.room_type           = tpl.room_type,
                  r.description         = tpl.description,
                  r.image_url           = tpl.image_url,
                  r.default_enemy_id    = tpl.default_enemy_id,
                  r.inner_template_id   = NULL,
                  r.stair_down_floor_id = %s,
                  r.stair_down_x        = %s,
                  r.stair_down_y        = %s,
                  r.stair_up_floor_id   = %s,
                  r.stair_up_x          = %s,
                  r.stair_up_y          = %s
                WHERE r.room_id = %s
                """,
                (
                    stair_info["stair_down_floor_id"],
                    stair_info["stair_down_x"],
                    stair_info["stair_down_y"],
                    stair_info["stair_up_floor_id"],
                    stair_info["stair_up_x"],
                    stair_info["stair_up_y"],
                    room["room_id"],
                ),
            )
        conn.commit()
        conn.close()

        # 6) sanity‑check for staircase templates
        if room["new_room_type"] in ("staircase_up", "staircase_down"):
            conn2 = self.db_connect()
            with conn2.cursor(dictionary=True) as cur2:
                cur2.execute(
                    """
                    SELECT stair_up_floor_id, stair_up_x, stair_up_y,
                           stair_down_floor_id, stair_down_x, stair_down_y
                    FROM rooms
                    WHERE room_id = %s
                    """,
                    (room["room_id"],),
                )
                stair_info = cur2.fetchone()
            conn2.close()
            if room["new_room_type"] == "staircase_up" and stair_info["stair_up_floor_id"] is None:
                logger.warning(f"⚠️ Unlocked staircase_up at ({x},{y}) has no destination!")
            if room["new_room_type"] == "staircase_down" and stair_info["stair_down_floor_id"] is None:
                logger.warning(f"⚠️ Unlocked staircase_down at ({x},{y}) has no destination!")

        # 7) re‑load the revealed room
        conn = self.db_connect()
        with conn.cursor(dictionary=True) as cur:
            cur.execute(
                """
                SELECT r.*, f.floor_number
                FROM rooms r
                JOIN floors f ON f.floor_id = r.floor_id
                WHERE r.room_id = %s
                """,
                (room["room_id"],),
            )
            new_room = cur.fetchone()
        conn.close()

        # patch missing floor_number
        if new_room and "floor_number" not in new_room:
            conn = self.db_connect()
            with conn.cursor(dictionary=True) as cur:
                cur.execute("SELECT floor_number FROM floors WHERE floor_id = %s", (new_room["floor_id"],))
                fr = cur.fetchone()
            conn.close()
            new_room["floor_number"] = fr["floor_number"] if fr else 1

        # 8) mark discovered
        await self.update_permanent_discovered_room(
            interaction.user.id,
            session.session_id,
            (new_room["floor_id"], new_room["coord_x"], new_room["coord_y"]),
        )

        # 9) if this is any battle‐room, start combat immediately
        rtype = new_room["room_type"]
        if rtype in ("boss","miniboss","monster"):
            bs = self.bot.get_cog("BattleSystem")
            if bs:
                if rtype == "boss" and new_room.get("default_enemy_id"):
                    # boss rooms use their fixed enemy
                    enemy = await bs.get_enemy_by_id(new_room["default_enemy_id"])
                else:
                    # miniboss & normal monster pick one dynamically
                    enemy = await bs.get_enemy_for_room(
                        session,
                        new_room["floor_id"],
                        new_room["coord_x"],
                        new_room["coord_y"],
                    )

                if enemy:
                    self.append_game_log(
                        session.session_id,
                        f"Encountered **{enemy['enemy_name']}**!"
                    )
                    return await bs.start_battle(
                        interaction,
                        session.current_turn,
                        enemy,
                        previous_coords=(new_room["floor_id"], x, y)
                    )

        # 10) otherwise, if it’s a chest‐room, seed an instance
        if new_room["room_type"] == "item":
            dg = self.bot.get_cog("DungeonGenerator")
            if dg:
                key_defs = dg.fetch_random_treasure_chest("key")
                all_defs = dg.fetch_random_treasure_chest()
                choice   = key_defs or all_defs
                chest    = dg.weighted_choice(choice)
                if chest:
                    dg.create_treasure_chest_instance(
                        session.session_id,
                        new_room["room_id"],
                        chest["chest_id"],
                    )

        # 11) finally, re‑draw the room (with unlock/chest buttons as appropriate)
        await sm.refresh_current_state(interaction)
        await self.end_player_turn(interaction)


    # ─────────────────────────────────────────────────────────────────
    #  Movement: locks, stairs, battles, turn advance
    # ─────────────────────────────────────────────────────────────────
    async def handle_move(self, interaction: discord.Interaction, direction: str) -> None:
        sm = self.bot.get_cog("SessionManager")
        session = sm.get_session(interaction.channel.id) if sm else None
        if not session:
            return await interaction.followup.send("❌ No active session.", ephemeral=True)

        if not interaction.response.is_done():
            defer_fn = getattr(interaction.response, "defer_update", None)
            if callable(defer_fn):
                await defer_fn()
            else:
                await interaction.response.defer()

        try:
            conn = await self.adb_connect()
            async with conn.cursor(aiomysql.DictCursor) as cur:
                await cur.execute(
                    "SELECT coord_x, coord_y, current_floor_id FROM players "
                    "WHERE player_id=%s AND session_id=%s",
                    (interaction.user.id, session.session_id)
                )
                pos = await cur.fetchone()
            conn.close()

            if not pos:
                return await interaction.followup.send("❌ Position error.", ephemeral=True)

            x, y, floor = pos["coord_x"], pos["coord_y"], pos["current_floor_id"]
            dx, dy = {"north": (0, -1), "south": (0, 1), "east": (1, 0), "west": (-1, 0)}.get(direction, (0, 0))
            nx, ny = x + dx, y + dy
        except Exception as e:
            logger.error("handle_move: %s", e)
            return await interaction.followup.send("❌ Position error.", ephemeral=True)

        

        # ── 2. look up the target tile on the *current* floor ────────
        conn = await self.adb_connect()
        async with conn.cursor(aiomysql.DictCursor) as cur:
            await cur.execute(
                """
                SELECT r.*, f.floor_number
                FROM rooms  r
                JOIN floors f ON f.floor_id = r.floor_id
                WHERE r.session_id = %s
                AND r.floor_id = %s

                AND r.coord_x = %s
                AND r.coord_y = %s
                """,
                (session.session_id, floor, nx, ny)
            )
            target = await cur.fetchone()
        conn.close()

        if not target:
            return await interaction.followup.send("🚫 You can’t go that way.", ephemeral=True)

        # ── 3. handle locked doors ──────────────────────────────────
        if target["room_type"] == "locked":
            self.append_game_log(
                session.session_id,
                "A locked door blocks the way."
            )

        # ── 4. default floor (no change yet even if stairs) ──────────
        new_floor = floor

        logger.debug("Room lookup → sess=%s floor=%s x=%s y=%s", session.session_id, new_floor, nx, ny)

        # ── 5. write the movement to the DB ──────────────────────────
        conn = await self.adb_connect()
        async with conn.cursor() as cur:
            await cur.execute(
                "UPDATE players SET coord_x=%s, coord_y=%s, current_floor_id=%s "
                "WHERE player_id=%s AND session_id=%s",
                (nx, ny, new_floor, interaction.user.id, session.session_id)
            )
        await conn.commit()
        conn.close()
        # mark this tile permanently discovered now that the move succeeded
        await self.update_permanent_discovered_room(
            interaction.user.id,
            session.session_id,
            (new_floor, nx, ny)
        )
        SessionPlayerModel.increment_rooms_visited(session.session_id, interaction.user.id)
        self.append_game_log(session.session_id, f"<@{interaction.user.id}> moved {direction}.")

        # ── 6. fetch the room we actually landed in ──────────────────
        conn = await self.adb_connect()
        async with conn.cursor(aiomysql.DictCursor) as cur:
            await cur.execute(
                """
                SELECT r.*, f.floor_number
                FROM rooms  r
                JOIN floors f ON f.floor_id = r.floor_id
                WHERE r.session_id = %s
                AND r.floor_id = %s

                AND r.coord_x = %s
                AND r.coord_y = %s
                """,
                (session.session_id, new_floor, nx, ny)
            )
            landed = await cur.fetchone()
        conn.close()

        if not landed:
            return await interaction.followup.send("❌ Room data missing.", ephemeral=True)

        # ── 7. special cases: trap / monster ─────────────────────────
        if landed["room_type"] == "trap":
            await self.trigger_trap(interaction, landed)
            return

        if landed["room_type"] in ("boss", "miniboss", "monster"):
            bs = self.bot.get_cog("BattleSystem")
            if bs:
                default_id = landed.get("default_enemy_id")
                if landed["room_type"] == "boss" and default_id:
                    enemy = await bs.get_enemy_by_id(default_id)
                else:
                    enemy = await bs.get_enemy_for_room(session, new_floor, nx, ny)

                if enemy:
                    self.append_game_log(
                        session.session_id,
                        f"Encountered **{enemy['enemy_name']}**!"
                    )
                    await bs.start_battle(
                        interaction,
                        interaction.user.id,
                        enemy,
                        previous_coords=(floor, x, y)
                    )
                    return

        # ── 8. normal room (safe, item, staircase, etc) ───────────────
        await self.update_room_view(interaction, landed, nx, ny)
        await self.end_player_turn(interaction)
        

    # ──────────────────────────────────────────────────────────
    #  Trap dispatcher
    # ──────────────────────────────────────────────────────────
    async def trigger_trap(self,
                           interaction: discord.Interaction,
                           room: dict[str, Any]) -> None:
        """
        For now, trap rooms behave exactly like safe rooms:
        just redraw the current room.  Future trap effects (e.g.,
        periodic HP loss over several turns) go here.
        """
        # TODO: apply trap effects (e.g. debuff, %HP drain per turn)
        await self.update_room_view(
            interaction,
            room,
            room["coord_x"],
            room["coord_y"],
        )
        await self.end_player_turn(interaction)

    async def handle_quit_game(self, interaction: Interaction) -> None:
        sm: SessionManager = self.bot.get_cog("SessionManager")
        session = sm.get_session(interaction.channel.id) if sm else None
        if not session:
            return await interaction.response.send_message("❌ No active session found.", ephemeral=True)

        # Defer only if the interaction hasn't already been acknowledged
        if not interaction.response.is_done():
            try:
                await interaction.response.defer()
            except discord.errors.HTTPException as e:
                logger.debug(
                    "Deferred interaction failed (already acknowledged): %s", e
                )

        # Look up the saved flag
        from models.session_models import SessionModel
        saved = SessionModel.is_saved(session.session_id)

        if not saved:
            # Unsaved sessions: mark ended in DB and remove from memory
            await sm.terminate_session(session.session_id, "Quit by user")
            scores = await sm.get_high_scores()
            embed = hub_embed.get_high_scores_embed(scores)
            await interaction.channel.send(embed=embed)
        else:
            # Saved sessions: only remove from memory, leave DB intact
            sm.delete_session_state(session.session_id)

        # Finally, delete the Discord thread itself
        try:
            await interaction.channel.delete()
        except discord.errors.HTTPException as e:
            logger.debug("Thread deletion failed: %s", e)
        except Exception as e:
            logger.error(f"Error deleting thread on quit: {e}", exc_info=True)

    
    # ────────────────────────────────────────────────────────────────────────────
    #  Handle "Use Stairs" button
    # ────────────────────────────────────────────────────────────────────────────
    async def handle_use_stairs(self, interaction: discord.Interaction) -> None:
        sm = self.bot.get_cog("SessionManager")
        session = sm.get_session(interaction.channel.id) if sm else None
        if not session:
            return await interaction.followup.send("❌ No session.", ephemeral=True)

        if not interaction.response.is_done():
            defer_fn = getattr(interaction.response, "defer_update", None)
            if callable(defer_fn):
                await defer_fn()
            else:
                await interaction.response.defer()

        # Current position
        conn = self.db_connect()
        with conn.cursor(dictionary=True) as cur:
            cur.execute(
                "SELECT coord_x, coord_y, current_floor_id FROM players "
                "WHERE player_id=%s AND session_id=%s",
                (interaction.user.id, session.session_id)
            )
            pos = cur.fetchone()
        conn.close()
        if not pos:
            return await interaction.followup.send("❌ Position error.", ephemeral=True)

        x, y, floor = pos["coord_x"], pos["coord_y"], pos["current_floor_id"]

        # Info about the tile
        conn = self.db_connect()
        with conn.cursor(dictionary=True) as cur:
            cur.execute("""
                SELECT r.*, f.floor_number
                FROM rooms  r
                JOIN floors f ON f.floor_id = r.floor_id
                WHERE r.session_id=%s
                AND r.floor_id=%s
                AND r.coord_x=%s AND r.coord_y=%s
            """, (session.session_id, floor, x, y))
            room = cur.fetchone()
        conn.close()
        if not room:
            return await interaction.followup.send("❌ Room error.", ephemeral=True)

        # Decide destination
        dest_floor_id = None
        dest_x, dest_y = x, y

        if room["room_type"] == "staircase_up" and room["stair_up_floor_id"] is not None:
            dest_floor_id = room["stair_up_floor_id"]
            dest_x = room["stair_up_x"]
            dest_y = room["stair_up_y"]
        elif room["room_type"] == "staircase_down" and room["stair_down_floor_id"] is not None:
            dest_floor_id = room["stair_down_floor_id"]
            dest_x = room["stair_down_x"]
            dest_y = room["stair_down_y"]
        else:
            return await interaction.followup.send("🚫 These stairs don’t lead anywhere yet.", ephemeral=True)

        # Move player
        conn = self.db_connect()
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE players SET coord_x=%s, coord_y=%s, current_floor_id=%s "
                "WHERE player_id=%s AND session_id=%s",
                (dest_x, dest_y, dest_floor_id, interaction.user.id, session.session_id)
            )
        conn.commit()
        conn.close()

        self.append_game_log(
            session.session_id,
            f"<@{interaction.user.id}> used the stairs to floor {dest_floor_id}."
        )
        await self.update_permanent_discovered_room(
            interaction.user.id,
            session.session_id,
            ( dest_floor_id, dest_x, dest_y )
        )
        SessionPlayerModel.increment_rooms_visited(session.session_id, interaction.user.id)
        # Fetch the destination room
        conn = self.db_connect()
        with conn.cursor(dictionary=True) as cur:
            cur.execute("""
                SELECT r.*, f.floor_number
                FROM rooms r
                JOIN floors f ON f.floor_id = r.floor_id
                WHERE r.session_id=%s
                AND r.floor_id=%s
                AND r.coord_x=%s AND r.coord_y=%s
            """, (session.session_id, dest_floor_id, dest_x, dest_y))
            dest_room = cur.fetchone()
        conn.close()

        if not dest_room:
            return await interaction.followup.send(
                "❌ Destination room missing after stairs!", ephemeral=True
            )

        await self.update_room_view(interaction, dest_room, dest_x, dest_y)
            # stairs always land you in a safe room → end this player's turn
        await self.end_player_turn(interaction)    

    # ────────────────────────────────────────────────────────────────────────────
    #  LOOK AROUND → minimap
    # ────────────────────────────────────────────────────────────────────────────
    async def handle_look_around(self, interaction: discord.Interaction) -> None:
        sm      = self.bot.get_cog("SessionManager")
        session = sm.get_session(interaction.channel.id) if sm else None
        if not session:
            return await interaction.followup.send("❌ No session.", ephemeral=True)
        if session.battle_state:
            return await interaction.followup.send("⚔️ You can’t look around during battle!", ephemeral=True)

        if not interaction.response.is_done():
            defer_fn = getattr(interaction.response, "defer_update", None)
            if callable(defer_fn):
                await defer_fn()
            else:
                await interaction.response.defer()

        # 1) fetch current floor, x, y
        conn = self.db_connect()
        with conn.cursor(dictionary=True) as cur:
            cur.execute(
                "SELECT coord_x, coord_y, current_floor_id FROM players "
                "WHERE player_id=%s AND session_id=%s",
                (interaction.user.id, session.session_id),
            )
            pos = cur.fetchone()
        conn.close()
        if not pos:
            return await interaction.followup.send("❌ Position error.", ephemeral=True)

        x, y, floor = pos["coord_x"], pos["coord_y"], pos["current_floor_id"]
        current = (x, y)

        # 2) record (floor,x,y) in the DB, get back the full set
        full_discovered = await self.update_permanent_discovered_room(
            interaction.user.id,
            session.session_id,
            (floor, x, y),
        )
        # filter to only this floor
        discovered_here = {
            (xx, yy)
            for (ff, xx, yy) in full_discovered
            if ff == floor
        }

        # 3) allow peeking into adjacent tiles on this floor
        neighbours = {(x+1, y), (x-1, y), (x, y+1), (x, y-1)}
        visible    = discovered_here.union(neighbours)

        # 4) fetch all rooms and hand off to your minimap embed
        conn = self.db_connect()
        with conn.cursor(dictionary=True) as cur:
            cur.execute("""
                SELECT coord_x, coord_y, room_type, floor_id
                  FROM rooms
                 WHERE session_id=%s
                   AND floor_id=%s
            """, (session.session_id, floor))
            rooms = cur.fetchall()
        conn.close()
        # ——— NEW: fetch any dead players on this floor ———
        conn = self.db_connect()
        with conn.cursor(dictionary=True) as cur:
            cur.execute(
                "SELECT player_id, coord_x, coord_y "
                "FROM players "
                "WHERE session_id=%s AND current_floor_id=%s",
                (session.session_id, floor)
            )
            players_pos = cur.fetchall()
        conn.close()

        dead_positions = {
            (r["coord_x"], r["coord_y"])
            for r in players_pos
            if SessionPlayerModel.is_player_dead(session.session_id, r["player_id"])
        }
        em = self.bot.get_cog("EmbedManager")
        if em:
            await em.send_minimap_embed(
                interaction,
                all_rooms=rooms,
                current_pos=current,
                reveal_set=visible,
                discovered_set=discovered_here,
                current_floor=floor,
                dead_positions=dead_positions
            )
        else:
            await interaction.followup.send("❌ Map unavailable.", ephemeral=True)


    # ────────────────────────────────────────────────────────────────────────────
    #  BATTLE / XP / CHARACTER SHEET
    # ────────────────────────────────────────────────────────────────────────────
    async def award_experience(self,
                               player_id: int,
                               session_id: int,
                               xp_reward: int) -> None:
        try:
            conn = self.db_connect()
            with conn.cursor(dictionary=True) as cur:
                cur.execute(
                    "SELECT experience,level,class_id FROM players "
                    "WHERE player_id=%s AND session_id=%s",
                    (player_id, session_id)
                )
                p = cur.fetchone()
                if not p:
                    return

                total_xp  = p["experience"] + xp_reward
                cur_level = p["level"]
                cid       = p["class_id"]
                leveled   = False

                while True:
                    cur.execute(
                        "SELECT required_exp FROM levels WHERE level=%s",
                        (cur_level+1,)
                    )
                    nxt = cur.fetchone()
                    if not nxt or total_xp < nxt["required_exp"]:
                        break
                    total_xp  -= nxt["required_exp"]
                    cur_level += 1
                    leveled   = True
                    from utils.stat_levelup import update_player_stats
                    update_player_stats(player_id, session_id, cur_level, cid)
                    self.append_game_log(
                        session_id,
                        f"<@{player_id}> reached **Lv {cur_level}**!"
                    )

                cur.execute(
                    "UPDATE players SET experience=%s, level=%s "
                    "WHERE player_id=%s AND session_id=%s",
                    (total_xp, cur_level, player_id, session_id)
                )
            conn.commit()
            conn.close()

            if not leveled:
                self.append_game_log(
                    session_id,
                    f"<@{player_id}> gained {xp_reward} XP."
                )
        except Exception as e:
            logger.error("award_experience: %s", e)

    async def level_up_player(self,
                              player_id: int,
                              session_id: int,
                              new_level: int,
                              class_id: int) -> None:
        from utils.stat_levelup import update_player_stats
        update_player_stats(player_id, session_id, new_level, class_id)

    async def display_character_sheet(self,
                                      interaction: discord.Interaction) -> None:
        sm = self.bot.get_cog("SessionManager")
        session = sm.get_session(interaction.channel.id) if sm else None
        if not session:
            return await interaction.followup.send(
                "❌ No session.", ephemeral=True
            )

        if not interaction.response.is_done():
            try:
                await interaction.response.defer()
            except discord.errors.HTTPException as e:
                logger.debug("Deferred interaction failed: %s", e)

        pd = next((
            p for p in
            SessionPlayerModel.get_player_states(session.session_id)
            if p["player_id"] == session.current_turn
        ), None)
        if not pd:
            return await interaction.followup.send(
                "❌ Data error.", ephemeral=True
            )

        def _bar(v, m, ln=10):
            if not m:
                return "[-]"
            full = int(round(ln * v / m))
            return f"[{'█'*full}{'░'*(ln-full)}] {v}/{m}"

        conn = self.db_connect()
        with conn.cursor(dictionary=True) as cur:
            cur.execute(
                "SELECT required_exp FROM levels WHERE level=%s",
                (pd["level"]+1,)
            )
            nxt = cur.fetchone()
        conn.close()

        xp_bar = _bar(pd["experience"], nxt["required_exp"] if nxt else None)
        hp_bar = _bar(pd["hp"], pd["max_hp"])

        c_name  = ClassModel.get_class_name(pd["class_id"]) or "Unknown"
        c_thumb = ClassModel.get_class_image_url(pd["class_id"])

        # how many keys?
        key_count = SessionPlayerModel.get_key_count(session.session_id, session.current_turn)

                # how many Auto‑Raise items?  (quest items whose JSON effect has revive=true)
        inv_dict = SessionPlayerModel.get_inventory(
            session.session_id, session.current_turn
        ) or {}
        magicite_count = 0
        if inv_dict:
            # build a placeholder list for SQL IN(...)
            placeholders = ",".join("%s" for _ in inv_dict)
            conn = self.db_connect()
            with conn.cursor(dictionary=True) as cur:
                cur.execute(
                    f"""
                    SELECT item_id
                      FROM items
                     WHERE type = 'quest'
                       AND item_id IN ({placeholders})
                       AND JSON_EXTRACT(effect, '$.revive') = true
                    """,
                    tuple(int(i) for i in inv_dict.keys())
                )
                rows = cur.fetchall()
            conn.close()
            # sum up all quantities of those matching quest items
            for r in rows:
                magicite_count += inv_dict.get(str(r["item_id"]), 0)


        e = discord.Embed(title="Character Sheet",
                          color=discord.Color.gold())
        if c_thumb:
            e.set_thumbnail(url=c_thumb)

        # core stats + keys
        fields = [
            ("Name", pd["username"], True),
            ("Class", c_name, True),
            ("Level", str(pd["level"]), True),
            ("Experience", xp_bar, False),
            ("HP", hp_bar, False),
            ("Keys", str(key_count), True),
            ("Auto‑Raise", str(magicite_count), True),
        ]
        
        # other stats
        for n in ("gil", "attack_power", "defense",
                  "magic_power", "magic_defense",
                  "accuracy", "evasion", "speed"):
            fields.append((n.replace("_"," ").title(), str(pd[n]), True))

        for name, val, inline in fields:
            e.add_field(name=name, value=val, inline=inline)

        # ← HERE: initialize your View
        view = discord.ui.View(timeout=None)
        view.add_item(discord.ui.Button(
            label="Class Abilities",
            style=discord.ButtonStyle.primary,
            custom_id="character_class_abilities"
        ))
        view.add_item(discord.ui.Button(
            label="Back",
            style=discord.ButtonStyle.secondary,
            custom_id="character_back"
        ))
 
        em = self.bot.get_cog("EmbedManager")
        if em:
            await em.send_or_update_embed(
                interaction, "", "",
                embed_override=e,
                view_override=view
            )
        else:
            await interaction.followup.send(embed=e, view=view)

    async def display_class_abilities(self, interaction: discord.Interaction) -> None:
        """Show what abilities this player’s class has unlocked vs. locked."""
        sm = self.bot.get_cog("SessionManager")
        session = sm.get_session(interaction.channel.id) if sm else None
        if not session:
            return await interaction.response.send_message("❌ No session.", ephemeral=True)

        if not interaction.response.is_done():
            try:
                await interaction.response.defer()
            except discord.errors.HTTPException as e:
                logger.debug("Deferred interaction failed: %s", e)

        # pull current player data
        pd = next(p for p in SessionPlayerModel.get_player_states(session.session_id)
                  if p["player_id"] == session.current_turn)

        class_id = pd["class_id"]
        player_lvl = pd["level"]

        # fetch all abilities for this class
        conn = self.db_connect()
        with conn.cursor(dictionary=True) as cur:
            cur.execute(
                """
                SELECT ca.ability_id,
                       a.ability_name,
                       a.description,
                       ca.unlock_level
                  FROM class_abilities ca
                  JOIN abilities a
                    ON a.ability_id = ca.ability_id
                 WHERE ca.class_id = %s
                 ORDER BY ca.unlock_level
                """,
                (class_id,)
            )
            rows = cur.fetchall()
        conn.close()

        unlocked = []
        locked   = []
        for r in rows:
            name = r["ability_name"]
            lvl  = r["unlock_level"]
            desc = r["description"]
            if player_lvl >= lvl:
                unlocked.append(f"**{name}** (unlocked at Lv {lvl})\n{desc}")
            else:
                locked.append(f"~~{name}~~ (available at Lv {lvl})")

        e = discord.Embed(title="Class Abilities", color=discord.Color.blue())
        if unlocked:
            e.add_field(name="✅ Unlocked", value="\n\n".join(unlocked), inline=False)
        else:
            e.add_field(name="✅ Unlocked", value="*None yet*", inline=False)

        if locked:
            e.add_field(name="🔒 Locked", value="\n".join(locked), inline=False)

        # back button
        view = discord.ui.View(timeout=None)
        view.add_item(discord.ui.Button(
            label="Back to Character",
            style=discord.ButtonStyle.secondary,
            custom_id="class_abilities_back"
        ))

        em = self.bot.get_cog("EmbedManager")
        if em:
            await em.send_or_update_embed(interaction, "", "",
                                          embed_override=e,
                                          view_override=view)
        else:
            await interaction.followup.send(embed=e, view=view, ephemeral=True)

    # ────────────────────────────────────────────────────────────────────────────
    #  TURN HELPERS
    # ────────────────────────────────────────────────────────────────────────────
    async def advance_turn(self, interaction: discord.Interaction, sess_key: int) -> None:
        sm = self.bot.get_cog("SessionManager")
        session = sm.get_session(sess_key) if sm else None
        if not session:
            return

        # preserve the join order
        all_players = SessionPlayerModel.get_players(session.session_id)
        alive = [
            pid for pid in all_players
            if not SessionPlayerModel.is_player_dead(session.session_id, pid)
        ]
        if not alive:
            # everyone fainted → end session
            await sm.terminate_session(session.session_id, "All players fainted")
            return

        # if current is missing or dead, start at the first alive
        if session.current_turn not in alive:
            session.current_turn = alive[0]
        else:
            idx = alive.index(session.current_turn)
            session.current_turn = alive[(idx + 1) % len(alive)]

        session.append_log(f"Turn → <@{session.current_turn}>")
        logger.info("Turn advanced → %s", session.current_turn)

    async def end_player_turn(self,
                            interaction: discord.Interaction) -> None:
        """
        Ends the current player's turn: decrements their Trance duration (if active),
        advances to the next alive player, and refreshes the view.
        """
        sm = self.bot.get_cog("SessionManager")
        session = sm.get_session(interaction.channel.id) if sm else None
        if not session:
            return await interaction.followup.send(
                "❌ No session.", ephemeral=True
            )

        # 1️⃣ Tick all world HoT/DoT on the outgoing player
        prev_pid = session.current_turn
        engine   = StatusEffectEngine(session, self.append_game_log)
        await engine.tick_world(prev_pid)


        # ───────────────────────────────────────────────────────
        # 1️⃣ Decrement Trance duration for that player, if active
        if hasattr(session, "trance_states") and session.trance_states:
            ts = session.trance_states.get(prev_pid)
            if ts:
                ts["remaining"] = max(ts["remaining"] - 1, 0)
                if ts["remaining"] <= 0:
                    # Trance has ended
                    session.game_log.append(
                        f"✨ <@{prev_pid}>'s **{ts['name']}** has ended."
                    )
                    del session.trance_states[prev_pid]
                else:
                    # Log remaining turns
                    session.game_log.append(
                        f"✨ <@{prev_pid}>'s **{ts['name']}** has {ts['remaining']} turn(s) remaining."
                    )

        # 2️⃣ Advance to the next alive player
        await self.advance_turn(interaction, interaction.channel.id)

        # 3️⃣ Tick world HoT/DoT on the incoming player (only if the turn actually changed)
        new_pid = session.current_turn
        if new_pid != prev_pid:
            await engine.tick_world(new_pid)

        # 4️⃣ Finally redraw that player’s view
        await sm.refresh_current_state(interaction)


    # ────────────────────────────────────────────────────────────────────────────
    #  MINIMAP BACK
    # ────────────────────────────────────────────────────────────────────────────
    async def handle_minimap_back(self,
                                  interaction: discord.Interaction) -> None:
        sm = self.bot.get_cog("SessionManager")
        session = sm.get_session(interaction.channel.id) if sm else None
        if not session:
            return await interaction.followup.send(
                "❌ No session.", ephemeral=True
            )

        if not interaction.response.is_done():
            defer_fn = getattr(interaction.response, "defer_update", None)
            if callable(defer_fn):
                await defer_fn()
            else:
                await interaction.response.defer()

        conn = self.db_connect()
        with conn.cursor(dictionary=True) as cur:
            cur.execute(
                "SELECT coord_x,coord_y,current_floor_id FROM players "
                "WHERE player_id=%s AND session_id=%s",
                (interaction.user.id, session.session_id)
            )
            pos = cur.fetchone()
        conn.close()
        if not pos:
            return await interaction.followup.send(
                "❌ Position error.", ephemeral=True
            )

        x, y, floor = pos["coord_x"], pos["coord_y"], pos["current_floor_id"]
        conn = self.db_connect()
        with conn.cursor(dictionary=True) as cur:
            cur.execute("""
                SELECT r.*, f.floor_number
                  FROM rooms r
                  JOIN floors f ON f.floor_id = r.floor_id
                 WHERE r.session_id=%s
                   AND r.floor_id=%s
                   AND r.coord_x=%s AND r.coord_y=%s
            """, (session.session_id, floor, x, y))
            room = cur.fetchone()
        conn.close()
        if not room:
            return await interaction.followup.send(
                "❌ Room missing.", ephemeral=True
            )
        await self.update_room_view(interaction, room, x, y)

    async def handle_save_game(self, interaction: Interaction) -> None:
        """
        Handle the Save Game button:
        1) Push the full session.to_dict() into the `game_state` column.
        2) Mark it as saved so cleanup skips it.
        3) Confirm and restore the current view.
        """
        sm = self.bot.get_cog("SessionManager")
        if not sm:
            return await interaction.response.send_message(
                "❌ SessionManager unavailable.", ephemeral=True
            )

        session = sm.get_session(interaction.channel.id)
        if not session:
            return await interaction.response.send_message(
                "❌ No active session.", ephemeral=True
            )

        if not interaction.response.is_done():
            defer_fn = getattr(interaction.response, "defer_update", None)
            if callable(defer_fn):
                await defer_fn()
            else:
                await interaction.response.defer()

        # 1) Persist the full session state JSON
        from models.session_models import SessionModel
        SessionModel.update_game_state(session.session_id, session.to_dict())

        # 2) Mark it as “saved” so it won’t be auto‑cleaned up
        SessionModel.mark_saved(session.session_id, True)

        # 3) Acknowledge and pop back to wherever we were
        await interaction.followup.send(
            "✅ Game saved!", ephemeral=True
        )
        await sm.return_to_current_view(interaction)

    # ────────────────────────────────────────────────────────────────────────────
    #  INTERACTION ROUTER
    # ────────────────────────────────────────────────────────────────────────────
    @commands.Cog.listener()
    
    async def on_interaction(self, interaction: discord.Interaction) -> None:
        if interaction.type != InteractionType.component:
            return
        cid = (interaction.data.get("custom_id") or "").strip()
        logger.debug("[Game] on_interaction id=%s done=%s cid=%r",
                     interaction.id, interaction.response.is_done(), cid)
        # ──────────────────────────────────────────────────────────────────
        # ignore our greyed‑out “⛔” placeholders
        if cid.endswith("_disabled"):
            return
        
        # New Game button in hub → create session
        if cid == "setup_new_game":
            # ACK the button silently (no ephemeral, no new message)
            if not interaction.response.is_done():
                try:
                    await interaction.response.defer()
                except discord.errors.HTTPException as e:
                    logger.debug("Deferred interaction failed: %s", e)
            await self.create_session(interaction, max_slots=6)
            return
        # ─── “End My Turn” on death (multiplayer) ───────────────────
        if cid == "death_end_turn":
            sm      = self.bot.get_cog("SessionManager")
            session = sm.get_session(interaction.channel.id)
            # delete the death‐embed if we tracked it
            if hasattr(session, "last_death_msg_id"):
                try:
                    dm = await interaction.channel.fetch_message(session.last_death_msg_id)
                    await dm.delete()
                except:
                    pass
                del session.last_death_msg_id
            # advance turn without reviving
            return await self.end_player_turn(interaction)
        
        # ─── Death: Revive ──────────────────────────────────────────
        if cid == "death_revive":
            sm      = self.bot.get_cog("SessionManager")
            session = sm.get_session(interaction.channel.id)
            sid     = session.session_id
            pid     = interaction.user.id

            # remove the death‐embed
            if hasattr(session, "last_death_msg_id"):
                try:
                    dm = await interaction.channel.fetch_message(session.last_death_msg_id)
                    await dm.delete()
                except:
                    pass
                del session.last_death_msg_id

            # consume one revive item
            inv = SessionPlayerModel.get_inventory(sid, pid)
            for raw_id in inv.keys():
                iid = int(raw_id)
                conn = self.db_connect()
                with conn.cursor(dictionary=True) as cur:
                    cur.execute(
                        "SELECT JSON_EXTRACT(effect,'$.revive') AS revive_amount FROM items WHERE item_id=%s",
                        (iid,)
                    )
                    row = cur.fetchone()
                conn.close()
                if row and row.get("revive_amount") is not None:
                    SessionPlayerModel.remove_inventory_item(sid, pid, iid, 1)
                    break

            # clear dead flag & restore 1 HP
            SessionPlayerModel.revive_player(sid, pid)
            conn = self.db_connect()
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE players SET hp=1 WHERE session_id=%s AND player_id=%s",
                    (sid, pid)
                )
            conn.commit()
            conn.close()

            # re‑enter battle or refresh view
            bs = self.bot.get_cog("BattleSystem")
            if bs and session.battle_state:
                await bs.update_battle_embed(interaction, pid, session.battle_state["enemy"])
            else:
                await sm.refresh_current_state(interaction)
            return

        # ─── Death: Game Over ───────────────────────────────────────
        if cid == "death_game_over":
            sm      = self.bot.get_cog("SessionManager")
            session = sm.get_session(interaction.channel.id)
            sid     = session.session_id
            pid     = interaction.user.id

            # remove the death‐embed
            if hasattr(session, "last_death_msg_id"):
                try:
                    dm = await interaction.channel.fetch_message(session.last_death_msg_id)
                    await dm.delete()
                except:
                    pass
                del session.last_death_msg_id

            # drop them from the session
            if pid in session.players:
                session.players.remove(pid)
                sm.update_session_players(interaction.channel.id, session.players)

            qualified = sm.record_player_high_score(sid, pid) if sm else False
            if qualified:
                scores = await sm.get_high_scores() if sm else []
                embed = hub_embed.get_high_scores_embed(scores)
                await interaction.channel.send(embed=embed)

            # if nobody left → end session & delete thread
            if not session.players:
                await sm.terminate_session(sid, "All players have left or died")
                try:
                    await interaction.channel.delete()
                except:
                    pass
                return

            # otherwise next alive player's view
            await sm.refresh_current_state(interaction)
            return

        
        # ─── Open the ⚙️ submenu ───────────────────────────────────
        if cid == "action_menu":
            em = self.bot.get_cog("EmbedManager")
            return await em.show_game_menu(interaction)
        # Quit Game
        if cid == "game_quit":
            return await self.handle_quit_game(interaction)
        
        # Save Game
        if cid == "game_save":
            return await self.handle_save_game(interaction)
        
        # Character / inventory shortcuts
        if cid == "action_character":
            return await self.display_character_sheet(interaction)
        if cid in ("character_back", "minimap_back"):
            return await self.handle_minimap_back(interaction)
        
        # Back from ⚙️ submenu → restore whatever view we were in
        if cid == "game_menu_back":
            sm = self.bot.get_cog("SessionManager")
            return await sm.return_to_current_view(interaction)
        if cid == "action_use":
            inv = self.bot.get_cog("InventoryShop")
            if inv:
                return await inv.display_use_item_menu(interaction)
        # Use-stairs
        if cid == "action_use_stairs":
            return await self.handle_use_stairs(interaction)


        # ↳ custom_id="action_skill"
        if cid == "action_skill":
            bs = self.bot.get_cog("BattleSystem")
            if not bs:
                return await interaction.response.send_message("❌ BattleSystem offline.", ephemeral=True)
            return await bs.handle_skill_menu(interaction)

        if cid == "character_class_abilities":
            return await self.display_class_abilities(interaction)

        if cid == "class_abilities_back":
            # simply re‑show the character sheet
            return await self.display_character_sheet(interaction)
        


        try:
            if cid == "action_look_around":
                return await self.handle_look_around(interaction)

            if cid == "action_unlock_door":
                return await self.handle_unlock_door(interaction)

            if cid.startswith("move_"):
                return await self.handle_move(
                    interaction, cid.split("_",1)[1]
                )

            if cid == "action_end_turn":
                return await self.end_player_turn(interaction)

            if cid == "start_game":
                if not interaction.response.is_done():
                    defer_fn = getattr(interaction.response, "defer_update", None)
                    if callable(defer_fn):
                        await defer_fn()
                    else:
                        await interaction.response.defer()

                sm = self.bot.get_cog("SessionManager")
                session = sm.get_session(interaction.channel.id) if sm else None
                if not session:
                    return await interaction.response.send_message(
                        "❌ No active session found.", ephemeral=True
                    )

                if not SessionModel.is_owner(session.session_id, interaction.user.id):
                    return await interaction.response.send_message(
                        "❌ Only the session creator can start the game.", ephemeral=True
                    )

                players = SessionPlayerModel.get_players(session.session_id)
                SessionModel.update_num_players(session.session_id, len(players))

                embed_mgr = self.bot.get_cog("EmbedManager")
                if embed_mgr:
                    await embed_mgr.send_class_selection_embed(
                        interaction,
                        len(players)
                    )

                hub = self.bot.get_cog("HubManager")
                if hub:
                    await hub.cleanup_lfg_posts(
                        interaction.user.display_name,
                        session.thread_id
                    )

                # ←── **NEW**: initialize turn order now that everyone is in
                sm.set_initial_turn(interaction.channel.id)

                return

            if cid.startswith("setup_"):
                # e.g. “setup_4” → 4‑player session
                defer_fn = getattr(interaction.response, "defer_update", None)
                if callable(defer_fn):
                    await defer_fn()
                else:
                    await interaction.response.defer()
                parts = cid.split("_",1)
                try:
                    slots = int(parts[1])
                except ValueError:
                    return
                await self.create_session(interaction, max_slots=slots)
                return

            if cid.startswith("class_"):
                return await self.handle_class_selection(
                    interaction, int(cid.split("_")[1])
                )

            if cid.startswith("difficulty_"):
                return await self.start_session(
                    interaction, cid.split("_",1)[1]
                )

            if cid == "intro_continue":
                if not interaction.response.is_done():
                    defer_fn = getattr(interaction.response, "defer_update", None)
                    if callable(defer_fn):
                        await defer_fn()
                    else:
                        await interaction.response.defer()
                return await self.begin_intro_sequence(interaction, interaction.channel.id)
            if cid == "intro_skip":
                if not interaction.response.is_done():
                    defer_fn = getattr(interaction.response, "defer_update", None)
                    if callable(defer_fn):
                        await defer_fn()
                    else:
                        await interaction.response.defer()
                return await self.skip_intro(interaction, interaction.channel.id)

            if cid.startswith("action_shop_"):
                shop = self.bot.get_cog("InventoryShop")
                if shop:
                    vid = int(cid.split("_")[2])
                    return await shop.display_shop_menu(interaction, vid)

            if cid == "end_game":
                sm = self.bot.get_cog("SessionManager")
                if sm:
                    sess = sm.get_session(interaction.channel.id)
                    if sess:
                        await sm.terminate_session(
                            sess.session_id,
                            "Ended by user"
                        )
                        await interaction.channel.send("🛑 Session ended.")
            # Handle *only* the room’s “Open Chest” button (open_chest_<digits>)
            # Handle the room’s “Unlock Chest” button  (open_chest_<digits>)
            m = re.match(r"^open_chest_(\d+)$", cid)
            if m:
                instance_id = int(m.group(1))
                tc = self.bot.get_cog("TreasureChestCog")
                if not tc:
                    return await interaction.response.send_message("Chest system offline.", ephemeral=True)

                # one-shot view – seeds / resumes the puzzle and edits the message for us
                await tc.OpenChestView(instance_id).start_unlock_challenge(interaction)
                return
    
                        
        except Exception as e:
            logger.error(f"on_interaction({cid}): {e}", exc_info=True)
            if not interaction.response.is_done():
                await interaction.response.send_message(
                    "❌ An error occurred.", ephemeral=True
                )
            else:
                await interaction.followup.send(
                    "❌ An error occurred.", ephemeral=True
                )


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(GameMaster(bot))
    logger.info("GameMaster cog loaded ✔")
