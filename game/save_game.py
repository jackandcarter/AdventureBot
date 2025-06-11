import discord
from discord.ext import commands
import time
import json
import logging
from models.database import Database
# We now rely on GameMaster to store the active session state.

logger = logging.getLogger("SaveGame")
logger.setLevel(logging.INFO)

class SaveGame(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='savegame')
    async def save_current_session(self, ctx, slot: int):
        """
        Save the current game session into a specified slot.
        Uses the channel/thread ID in GameMaster.sessions, instead of guild_id.
        """
        gm = self.bot.get_cog("GameMaster")
        if not gm:
            await ctx.send("❌ GameMaster cog not available.")
            return

        thread_id = ctx.channel.id
        session = gm.sessions.get(thread_id)
        if not session:
            await ctx.send("❌ No active session found to save in this thread.")
            return

        session_id = session["session_id"]
        save_title = f"Save {time.strftime('%Y-%m-%d %H:%M:%S')}"
        is_auto_save = False  # Manual save

        db = Database()
        conn = db.get_connection()
        cursor = conn.cursor()
        try:
            sql = """
                REPLACE INTO session_saves (session_id, slot, save_title, is_auto_save, saved_state)
                VALUES (%s, %s, %s, %s, %s)
            """
            cursor.execute(sql, (session_id, slot, save_title, is_auto_save, json.dumps(session)))
            conn.commit()
            await ctx.send(f"✅ Game saved successfully in slot {slot} as '{save_title}'.")
        except Exception as e:
            logger.error("Error saving game session: %s", e, exc_info=True)
            await ctx.send("❌ Failed to save the game.")
        finally:
            cursor.close()
            conn.close()

    @commands.command(name='loadgame')
    async def load_session(self, ctx, slot: int):
        """
        Load a game session from a specified slot.
        Again, uses channel/thread ID for the active session.
        """
        gm = self.bot.get_cog("GameMaster")
        if not gm:
            await ctx.send("❌ GameMaster cog not available.")
            return

        thread_id = ctx.channel.id
        session = gm.sessions.get(thread_id)
        if not session:
            await ctx.send("❌ No active session found to load into in this thread.")
            return

        session_id = session["session_id"]
        db = Database()
        conn = db.get_connection()
        cursor = conn.cursor(dictionary=True)
        try:
            sql = "SELECT saved_state FROM session_saves WHERE session_id = %s AND slot = %s"
            cursor.execute(sql, (session_id, slot))
            result = cursor.fetchone()
            if result and result.get("saved_state"):
                loaded_state = json.loads(result["saved_state"])
                # Update the GameMaster's in-memory session state for this thread
                gm.sessions[thread_id] = loaded_state
                await ctx.send(f"✅ Game loaded successfully from slot {slot}.")
                # Optionally, trigger a refresh of the game embed (assuming the user is still in the correct thread).
                await gm.refresh_current_state(ctx)
            else:
                await ctx.send("❌ No saved game found in that slot.")
        except Exception as e:
            logger.error("Error loading game session: %s", e, exc_info=True)
            await ctx.send("❌ Failed to load the game.")
        finally:
            cursor.close()
            conn.close()

    @commands.command(name='listsaves')
    async def list_saved_sessions(self, ctx):
        """
        List all saved sessions for the current active session in this thread.
        """
        gm = self.bot.get_cog("GameMaster")
        if not gm:
            await ctx.send("❌ GameMaster cog not available.")
            return

        thread_id = ctx.channel.id
        session = gm.sessions.get(thread_id)
        if not session:
            await ctx.send("❌ No active session found.")
            return

        session_id = session["session_id"]
        db = Database()
        conn = db.get_connection()
        cursor = conn.cursor(dictionary=True)
        try:
            sql = "SELECT slot, timestamp FROM session_saves WHERE session_id = %s"
            cursor.execute(sql, (session_id,))
            rows = cursor.fetchall()
            if not rows:
                await ctx.send("❌ You have no saved games.")
                return
            embed = discord.Embed(title="🗃️ Your Save Slots", color=discord.Color.blue())
            for row in rows:
                # The table presumably uses an integer UNIX timestamp or a datetime. Adjust as needed.
                saved_ts = row.get('timestamp')
                if isinstance(saved_ts, int):
                    saved_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(saved_ts))
                else:
                    # If it's a datetime object, just convert to str
                    saved_time = str(saved_ts)
                embed.add_field(name=f"Slot {row['slot']}", value=f"Saved on {saved_time}", inline=False)
            await ctx.send(embed=embed)
        except Exception as e:
            logger.error("Error listing saved sessions: %s", e, exc_info=True)
            await ctx.send("❌ Failed to list saved games.")
        finally:
            cursor.close()
            conn.close()

async def setup(bot):
    await bot.add_cog(SaveGame(bot))
