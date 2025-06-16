import discord
from discord.ext import commands
import logging
from typing import Optional, Tuple, Dict, List, Any
import mysql.connector
import json
import asyncio
from datetime import datetime

from game import high_score

from models.session_models import SessionModel, SessionPlayerModel
from core.game_session import GameSession  # New GameSession object

logger = logging.getLogger("SessionManager")
logger.setLevel(logging.DEBUG)

def build_main_menu_view(is_active_turn: bool, vendor_id: Optional[int] = None) -> discord.ui.View:
    """
    Builds a main menu view with two rows:

    - Row 0 (first row): Movement buttons with directional arrow emojis.
    - Row 1 (second row): Additional action buttons.

    The "Use" button is styled green, and the "Character" button is styled red.
    If a vendor_id is provided, a Shop button is also appended on the action row.
    All buttons are disabled if is_active_turn is False.
    """
    logger.debug(
        "SessionManager.build_main_menu_view called: is_active_turn=%s, vendor_id=%s",
        is_active_turn, vendor_id
    )
    view = discord.ui.View(timeout=None)

    # Row 0: Movement buttons.
    movement_buttons = [
        ("⬆️ Head North", discord.ButtonStyle.primary, "move_north", 0),
        ("⬇️ Head South", discord.ButtonStyle.primary, "move_south", 0),
        ("➡️ Head East",  discord.ButtonStyle.primary, "move_east",  0),
        ("⬅️ Head West",  discord.ButtonStyle.primary, "move_west",  0),
    ]

    for label, style, custom_id, row in movement_buttons:
        view.add_item(
            discord.ui.Button(
                label=label,
                style=style,
                custom_id=custom_id,
                row=row,
                disabled=not is_active_turn
            )
        )

    # Row 1: Additional action buttons.
    action_buttons = [
        ("Look Around", discord.ButtonStyle.secondary, "action_look_around", 1),
        ("Use", discord.ButtonStyle.success, "action_use", 1),   # Use is green.
        ("Character", discord.ButtonStyle.danger, "action_character", 1),  # Character is red.
        ("Menu", discord.ButtonStyle.secondary, "action_menu", 1),
    ]

    # Append the Shop button if vendor_id is provided.
    if vendor_id is not None:
        action_buttons.append(("Shop", discord.ButtonStyle.secondary, f"action_shop_{vendor_id}", 1))

    for label, style, custom_id, row in action_buttons:
        view.add_item(
            discord.ui.Button(
                label=label,
                style=style,
                custom_id=custom_id,
                row=row,
                disabled=not is_active_turn
            )
        )
    return view

class SessionManager(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        # In-memory sessions keyed by session_id and by thread_id for fast lookups
        self.sessions: Dict[int, GameSession] = {}
        self.sessions_by_thread: Dict[int, GameSession] = {}
        logger.info(
            "SessionManager cog initialized. In-memory session dictionaries created."
        )

    def db_connect(self) -> mysql.connector.connection.MySQLConnection:
        logger.debug("SessionManager.db_connect called.")
        from models.database import Database
        db = Database()
        try:
            conn = db.get_connection()
            logger.debug("SessionManager.db_connect: Connection to DB successful.")
            return conn
        except Exception as e:
            logger.error("SessionManager.db_connect: Database connection error: %s", e, exc_info=True)
            raise

    @staticmethod
    def player_has_key(session_id: int, player_id: int) -> bool:
        """
        True if the player's inventory JSON contains any item of type 'quest'.
        """
        inv = SessionPlayerModel.get_inventory(session_id, player_id) or {}
        if not inv:
            return False

        from models.database import Database
        db = Database()
        conn = db.get_connection()
        try:
            cur = conn.cursor(dictionary=True)
            for item_id, qty in inv.items():
                if qty <= 0:
                    continue
                cur.execute("SELECT type FROM items WHERE item_id=%s", (item_id,))
                row = cur.fetchone()
                if row and row.get("type") == "quest":
                    return True
            return False
        finally:
            cur.close()
            conn.close()

    async def create_new_session(self, interaction: discord.Interaction) -> Optional[Tuple[discord.Thread, int]]:
        logger.debug(
            "SessionManager.create_new_session called by user=%s (ID=%s) in channel=%s",
            interaction.user.display_name, interaction.user.id, interaction.channel.id
        )
        guild = interaction.guild
        owner = interaction.user
        channel = interaction.channel

        # If called from inside a thread, switch back to parent channel
        if isinstance(channel, discord.Thread) and channel.parent:
            channel = channel.parent

        try:
            # Create a private thread.
            thread = await channel.create_thread(
                name=f"Session - {owner.display_name}",
                type=discord.ChannelType.private_thread,
                auto_archive_duration=1440
            )
            logger.info("★ Created thread %s for new session in channel %s.", thread.id, channel.id)

            # Create a session record in the database.
            session_id = SessionModel.create_session(
                guild_id=guild.id,
                thread_id=str(thread.id),
                owner_id=owner.id,
                num_players=1,
                difficulty="Easy",
                game_state=None
            )
            logger.debug("SessionModel.create_session returned session_id=%s", session_id)

            if session_id is None:
                logger.error("SessionManager: Failed to create session record in DB.")
                if not interaction.response.is_done():
                    await interaction.response.send_message("❌ Failed to create session record.", ephemeral=True)
                else:
                    await interaction.followup.send("❌ Failed to create session record.", ephemeral=True)
                return None

            # Add the owner as a player.
            SessionPlayerModel.add_player(session_id, owner.id, owner.display_name)
            current_players = SessionPlayerModel.get_players(session_id)
            logger.debug(
                "Player %s added to session %s. Players now: %s",
                owner.id, session_id, current_players
            )

            # Create and store the GameSession in memory.
            new_session = GameSession(
                session_id=session_id,
                guild_id=guild.id,
                thread_id=str(thread.id),
                owner_id=owner.id,
                difficulty="Easy"
            )
            new_session.players = current_players
            new_session.current_turn = owner.id
            self.sessions[session_id] = new_session
            self.sessions_by_thread[int(thread.id)] = new_session
            logger.info("GameSession %s created and stored in memory.", session_id)

            await thread.add_user(owner)
            return thread, session_id

        except Exception as e:
            logger.error("Error creating new session: %s", e, exc_info=True)
            if not interaction.response.is_done():
                await interaction.response.send_message("❌ Failed to create game session.", ephemeral=True)
            else:
                await interaction.followup.send("❌ Failed to create game session.", ephemeral=True)
            return None

    async def join_session(self, interaction: discord.Interaction, session_id: int, thread_id: int, user: discord.Member) -> bool:
        logger.debug(
            "join_session called for user=%s to session %s (thread %s)",
            user.id, session_id, thread_id
        )
        session = self.sessions.get(session_id)
        if not session:
            logger.error("Session %s not found in memory.", session_id)
            if not interaction.response.is_done():
                await interaction.response.send_message("❌ Session not found.", ephemeral=True)
            else:
                await interaction.followup.send("❌ Session not found.", ephemeral=True)
            return False
        if user.id in session.players:
            return await interaction.response.send_message(
                "⚠️ You’ve already joined this session!", ephemeral=True
            )

        try:
                SessionPlayerModel.add_player(
                    session_id, user.id, user.display_name
                )
                SessionModel.increment_player_count(session_id)
                session.add_player(user.id)
                session.players = SessionPlayerModel.get_players(session_id)
                logger.info("User %s added to session %s.", user.id, session_id)

                th = interaction.guild.get_channel(thread_id) or await self.bot.fetch_channel(thread_id)
                await th.add_user(user)
                return True
        except Exception as e:
            logger.error("Error in join_session: %s", e, exc_info=True)
            await interaction.response.send_message("❌ Could not join session.", ephemeral=True)
            return False


    def update_session_players(self, thread_id: int, players: List[int]) -> None:
        session = self.get_session(thread_id)
        if session:
            session.players = players
            logger.info("Session %s players updated: %s", session.session_id, players)

    def set_initial_turn(self, session_id: int) -> None:
        session = self.sessions.get(session_id)
        if session:
            session.current_turn = session.owner_id
            logger.info("Initial turn for session %s set to owner %s", session_id, session.owner_id)

    def get_current_turn(self, session_id: int) -> Optional[int]:
        session = self.sessions.get(session_id)
        return session.current_turn if session else None

    def update_session_state(self, session_id: int, new_state: Dict[str, Any]) -> None:
        session = self.sessions.get(session_id)
        if session:
            for key, val in new_state.items():
                setattr(session, key, val)
            logger.info("Session %s state updated: %s", session_id, new_state)

    def delete_session_state(self, session_id: int) -> None:
        session = self.sessions.pop(session_id, None)
        if session:
            self.sessions_by_thread.pop(int(session.thread_id), None)
            logger.info("Session %s removed from memory.", session_id)

    def record_high_score(self, session_id: int) -> None:
        """Gather final stats for all players and record a high score entry."""
        try:
            conn = self.db_connect()
            cur = conn.cursor(dictionary=True)

            cur.execute(
                "SELECT guild_id, difficulty, created_at FROM sessions WHERE session_id=%s",
                (session_id,)
            )
            sess = cur.fetchone()
            if not sess:
                return

            cur.execute(
                """
                SELECT p.username, p.level, p.gil, p.discovered_rooms,
                       p.kill_count AS enemies_defeated, c.class_name
                  FROM players p
             LEFT JOIN classes c ON p.class_id = c.class_id
                 WHERE p.session_id = %s
                """,
                (session_id,),
            )
            players = cur.fetchall() or []

            play_time = 0
            if sess.get("created_at"):
                play_time = int((datetime.utcnow() - sess["created_at"]).total_seconds())

            for p in players:
                try:
                    rooms = len(json.loads(p.get("discovered_rooms") or "[]"))
                except Exception:
                    rooms = 0

                data = {
                    "player_name": p.get("username"),
                    "guild_id": sess.get("guild_id"),
                    "player_level": p.get("level"),
                    "player_class": p.get("class_name"),
                    "gil": p.get("gil", 0),
                    "enemies_defeated": p.get("enemies_defeated", 0),
                    "play_time": play_time,
                    "rooms_visited": rooms,
                    "difficulty": sess.get("difficulty"),
                }
                high_score.record_score(data)

        except Exception as e:  # pylint: disable=broad-except
            logger.error("record_high_score failed for session %s: %s", session_id, e, exc_info=True)
        finally:
            try:
                cur.close()
            except Exception:
                pass
            try:
                conn.close()
            except Exception:
                pass

    async def terminate_session(self, session_id: int, reason: str) -> None:
        logger.debug("terminate_session called for %s: %s", session_id, reason)
        try:
            conn = self.db_connect()
            cur = conn.cursor()
            cur.execute("UPDATE sessions SET status='ended' WHERE session_id=%s", (session_id,))
            conn.commit()
            cur.close()
            conn.close()
            logger.info("Session %s marked ended in DB.", session_id)
        except Exception as e:
            logger.error("Error ending session %s: %s", session_id, e, exc_info=True)
        finally:
            self.record_high_score(session_id)
            self.delete_session_state(session_id)

    def get_session(self, thread_id: int) -> Optional[GameSession]:
        return self.sessions_by_thread.get(int(thread_id))

    async def refresh_current_state(self, interaction: discord.Interaction) -> None:
        logger.debug("refresh_current_state called for channel %s", interaction.channel.id)
        session = self.get_session(interaction.channel.id)
        if not session:
            return await interaction.followup.send("❌ No active session found.", ephemeral=True)

        pid = session.current_turn
        # ── If this player is dead, jump into GM.update_room_view (which will
        #     send the “💀 You have fallen” embed and buttons) *without* touching battle_state.
        if SessionPlayerModel.is_player_dead(session.session_id, pid):
            # pull their current position (we’ve already fetched pos above, but you can re‑use it)
            conn = self.db_connect()
            with conn.cursor(dictionary=True) as cur:
                cur.execute(
                    "SELECT coord_x, coord_y, current_floor_id "
                    "FROM players WHERE player_id=%s AND session_id=%s",
                    (pid, session.session_id)
                )
                pos = cur.fetchone()
            conn.close()
            if not pos:
                return await interaction.followup.send("❌ Position missing.", ephemeral=True)

            # pull the room they’re in
            conn = self.db_connect()
            with conn.cursor(dictionary=True) as cur:
                cur.execute(
                    """
                    SELECT r.*, f.floor_number
                      FROM rooms r
                      JOIN floors f ON f.floor_id = r.floor_id
                     WHERE r.session_id=%s
                       AND r.floor_id=%s
                       AND r.coord_x=%s
                       AND r.coord_y=%s
                    """,
                    (session.session_id, pos["current_floor_id"], pos["coord_x"], pos["coord_y"])
                )
                room = cur.fetchone()
            conn.close()
            if not room:
                return await interaction.followup.send("❌ Room data missing.", ephemeral=True)

            # hands off to GameMaster.update_room_view, which will detect is_player_dead
            return await self.bot.get_cog("GameMaster").update_room_view(
                interaction, room, pos["coord_x"], pos["coord_y"]
            )
        if pid is None:
            return await interaction.followup.send("❌ No current player.", ephemeral=True)

        # ── Pull player position ──────────────────────────────
        conn = self.db_connect()
        with conn.cursor(dictionary=True) as cur:
            cur.execute(
                "SELECT coord_x, coord_y, current_floor_id FROM players WHERE player_id=%s AND session_id=%s",
                (pid, session.session_id)
            )
            pos = cur.fetchone()
        conn.close()
        if not pos:
            return await interaction.followup.send("❌ Position missing.", ephemeral=True)

        x, y, floor = pos["coord_x"], pos["coord_y"], pos["current_floor_id"]

        # ── Pull current room ──────────────────────────────────
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
            if not interaction.response.is_done():
                await interaction.response.send_message("❌ Room data missing.", ephemeral=True)
            else:
                await interaction.followup.send("❌ Room data missing.", ephemeral=True)
            return

        # ── Safety patch: if session thinks battle ongoing but room is now safe ───────
        if session.battle_state and room.get("room_type") not in ("monster", "miniboss", "boss"):
            logger.warning("⚠️ Battle state mismatch — clearing stale battle for session %s", session.session_id)
            session.clear_battle_state()

        # ── If still in battle, refresh battle view ───────────────────────────────────
        if session.battle_state:
            bs = self.bot.get_cog("BattleSystem")
            if bs:
                return await bs.update_battle_embed(
                    interaction, session.current_turn,
                    session.battle_state.get("enemy")
                )

        # ── Otherwise normal room ────────────────────────────────────────────────────
        # Attach key status
        if room.get("room_type") == "locked":
            room["player_has_key"] = self.player_has_key(session.session_id, pid)

        # Delegate to GameMaster
        gm = self.bot.get_cog("GameMaster")
        if gm:
            await gm.update_room_view(interaction, room, x, y)
        else:
            await interaction.followup.send("❌ GameMaster unavailable.", ephemeral=True)


    async def return_to_current_view(self, interaction: discord.Interaction) -> None:
        session = self.get_session(interaction.channel.id)
        if not session:
            if not interaction.response.is_done():
                await interaction.response.send_message("❌ No active session found.", ephemeral=True)
            else:
                await interaction.followup.send("❌ No active session found.", ephemeral=True)
            return

        if session.battle_state:
            from game.battle_system import BattleSystem
            bs = self.bot.get_cog("BattleSystem")
            if bs:
                await bs.update_battle_embed(
                    interaction,
                    session.current_turn,
                    session.battle_state.get("enemy")
                )
            else:
                if not interaction.response.is_done():
                    await interaction.response.send_message("❌ Battle system unavailable.", ephemeral=True)
                else:
                    await interaction.followup.send("❌ Battle system unavailable.", ephemeral=True)
        else:
            # when not in battle, fall back to the normal room refresh
            await self.refresh_current_state(interaction)

    @commands.command(
        name="cleanup_sessions",
        help="(Admin only) terminate and delete all unsaved game sessions."
    )
    @commands.has_guild_permissions(administrator=True)
    async def cleanup_sessions(self, ctx: commands.Context):
        """Find all sessions with saved=0, end them, delete threads, and remove from memory."""
        conn = self.db_connect()
        with conn.cursor(dictionary=True) as cur:
            cur.execute(
                "SELECT session_id, thread_id FROM sessions "
                "WHERE saved = 0 AND status = 'active'"
            )
            rows = cur.fetchall()
        conn.close()

        if not rows:
            return await ctx.send("✅ No unsaved sessions found to clean up.")

        cleaned = 0
        errors: List[str] = []
        for row in rows:
            sid = row["session_id"]
            tid = int(row["thread_id"])
            # 2) End it in the DB and in‑memory
            try:
                await self.terminate_session(sid, "Cleaned up unsaved session")
            except Exception as e:
                errors.append(f"• Failed to terminate session {sid}: {e}")
                continue

            # 3) Delete the Discord thread
            try:
                thread = ctx.guild.get_channel(tid) or await self.bot.fetch_channel(tid)
                await thread.delete()
            except Exception as e:
                errors.append(f"• Could not delete thread {tid}: {e}")

            cleaned += 1

        # 4) Report
        msg = f"🧹 Cleaned up **{cleaned}** unsaved session(s)."
        if errors:
            msg += "\n\n⚠️ Some issues:\n" + "\n".join(errors)
        await ctx.send(msg)

    async def load_session(self, interaction: discord.Interaction, session_id: int):
        """
        1) Create a new private thread
        2) Update DB + memory
        3) Add back all players
        4) Re-post the last room embed
        5) DM the opener a link
        """

        guild = interaction.guild
        hub_channel = self.bot.get_channel(
            self.bot.get_cog("HubManager").hub_channel_id
        )
        if not hub_channel:
            return await interaction.response.send_message(
                "❌ Hub channel not found. Cannot load.", ephemeral=True
            )

        # 1) spin up a fresh thread
        thread = await hub_channel.create_thread(
            name=f"Session – Reloaded #{session_id}",
            type=discord.ChannelType.private_thread,
            auto_archive_duration=1440
        )

        # 2) update the DB thread pointer
        SessionModel.update_thread_id(session_id, str(thread.id))

        # 3) Rehydrate full session state from saved JSON
        raw = SessionModel.get_game_state(session_id)

        # ——— Normalize whatever get_game_state returned ———

        # Case A: no state found
        if raw is None:
            return await interaction.response.send_message(
                "❌ Could not find saved session state.", ephemeral=True
            )

        # Case B: raw is a row‐dict with only a 'game_state' column
        if isinstance(raw, dict) and "session_id" not in raw:
            if "game_state" in raw and isinstance(raw["game_state"], str):
                try:
                    raw = json.loads(raw["game_state"])
                except Exception as e:
                    logger.error(
                        "Failed to parse game_state for session %s: %s",
                        session_id, e, exc_info=True
                    )
                    raw = {}
            else:
                # unexpected shape: start fresh
                raw = {}

        # Case C: raw is a JSON string
        elif isinstance(raw, str):
            try:
                raw = json.loads(raw)
            except Exception as e:
                logger.error(
                    "Failed to parse game_state string for session %s: %s",
                    session_id, e, exc_info=True
                )
                raw = {}

        # ─── **NEW**: ensure the dict actually has session_id for from_dict() ───────────
        raw.setdefault("session_id", session_id)
        raw["guild_id"]  = guild.id
        raw["thread_id"] = str(thread.id)
        # 4) now rebuild the in‐memory session exactly as before
        session = GameSession.from_dict(raw)
        self.sessions[session.session_id] = session
        self.sessions_by_thread[int(thread.id)] = session

        # 5) re‑invite all players
        for pid in session.players:
            member = guild.get_member(pid)
            if member:
                try:
                    await thread.add_user(member)
                except:
                    pass

        # 6) re‑draw the last room for the current turn
        class _FakeInteraction:
            def __init__(self, orig: discord.Interaction, new_channel: discord.abc.Messageable):
                # we only need these to make refresh_current_state() happy:
                self.client   = orig.client
                self.user     = orig.user
                self.guild    = orig.guild
                self.data     = orig.data
                self.response = orig.response
                self.followup = orig.followup
                # point at the newly created thread:
                self.channel  = new_channel

        fake_int = _FakeInteraction(interaction, thread)
        await self.refresh_current_state(fake_int)

        # 7) ping everyone inside the new thread
        mentions = " ".join(f"<@{pid}>" for pid in session.players)
        await thread.send(
            f"🔄 <@{interaction.user.id}> reloaded this adventure!\n"
            f"{mentions}"
        )

        # 8) finally acknowledge to the loader (ephemeral).
        if interaction.response.is_done():
            await interaction.followup.send(
                f"✅ Session #{session_id} reloaded — check your private thread!",
                ephemeral=True
            )
        else:
            await interaction.response.send_message(
                f"✅ Session #{session_id} reloaded — check your private thread!",
                ephemeral=True
            )



async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(SessionManager(bot))
    logger.info("SessionManager cog loaded ✔")
