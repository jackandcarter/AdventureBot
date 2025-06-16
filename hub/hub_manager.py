import discord
from discord.ext import commands
from discord import app_commands, InteractionType
import logging
from typing import Any, Dict, List
from models.session_models import SessionModel, SessionPlayerModel, ClassModel
# Import hub_embed here (helper module for constructing hub embeds)
from hub import hub_embed
# Import queue‐embed helpers from GameMaster
from game.game_master import build_queue_embed, _build_queue_view

logger = logging.getLogger("HubManager")
logger.setLevel(logging.DEBUG)

def is_admin_or_mod():
    async def predicate(interaction: discord.Interaction) -> bool:
        perms = interaction.user.guild_permissions
        logger.debug(
            "HubManager: Checking if user %s (ID %s) has admin/manage_messages. perms=%s",
            interaction.user.display_name,
            interaction.user.id,
            perms
        )
        return perms.administrator or perms.manage_messages
    return app_commands.check(predicate)

class HubManager(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.hub_channel_id = None  # Stores hub channel ID.
        self.hub_message_id = None  # Stores main hub message ID.
        logger.debug("HubManager cog initialized: bot=%s", bot)

    @app_commands.command(
        name="adventuresetup",
        description="Run the AdventureBot setup wizard to create or update the game hub."
    )
    @is_admin_or_mod()
    async def adventuresetup(self, interaction: discord.Interaction) -> None:
        """
        Sets up (or updates) the hub channel and its main embed for AdventureBot.
        The hub channel will be named "adventurebot" (all lower-case).
        """
        logger.debug(
            "HubManager: adventuresetup command invoked by user=%s (ID %s) in guild=%s (ID %s)",
            interaction.user.display_name,
            interaction.user.id,
            interaction.guild.name if interaction.guild else None,
            interaction.guild.id if interaction.guild else None
        )

        guild = interaction.guild
        if not guild:
            return await interaction.response.send_message(
                "This command must be used in a server.", ephemeral=True
            )

        # Look for an existing hub channel named "adventurebot".
        hub_channel = discord.utils.get(guild.text_channels, name="adventurebot")
        if not hub_channel:
            overwrites = {
                guild.default_role: discord.PermissionOverwrite(
                    send_messages=False,
                    add_reactions=False,
                    embed_links=True,
                    view_channel=True
                ),
                guild.me: discord.PermissionOverwrite(
                    send_messages=True,
                    manage_channels=True,
                    view_channel=True
                )
            }
            hub_channel = await guild.create_text_channel(
                name="adventurebot",
                overwrites=overwrites,
                reason="Setting up AdventureBot hub for Dungeon Adventure."
            )
            logger.info(f"★ Created hub channel: {hub_channel.name} (ID: {hub_channel.id})")
        else:
            logger.info(f"★ Using existing hub channel: {hub_channel.name} (ID: {hub_channel.id})")

        self.hub_channel_id = hub_channel.id

        # Prepare the main hub embed and view.
        embed = hub_embed.get_main_hub_embed()
        view = HubView()

        # Look for an existing hub embed message.
        hub_message = None
        async for message in hub_channel.history(limit=50):
            if message.author == guild.me and message.embeds:
                possible_title = (message.embeds[0].title or "").lower()
                if "welcome to adventurebot" in possible_title:
                    hub_message = message
                    break

        if hub_message:
            await hub_message.edit(embed=embed, view=view)
            logger.info(f"★ Updated existing hub message (ID: {hub_message.id})")
        else:
            hub_message = await hub_channel.send(embed=embed, view=view)
            logger.info(f"★ Posted new hub message (ID: {hub_message.id})")

        self.hub_message_id = hub_message.id
        await interaction.response.send_message(
            f"Adventure hub setup complete in {hub_channel.mention}.",
            ephemeral=True
        )

    async def post_lfg_post(self, interaction: discord.Interaction, thread: discord.Thread, session_id: int):
        """
        Posts an LFG (Join Game) message into the hub channel.
        """
        if not self.hub_channel_id:
            return
        hub_channel = self.bot.get_channel(self.hub_channel_id)
        if not hub_channel:
            return

        starter_name = interaction.user.display_name
        lfg_embed = discord.Embed(
            title=f"{starter_name} started a new adventure!",
            description=(
                "Click **Join Game** to join this session.\n\n"
                "Once everyone has joined, this join message will be removed."
            ),
            color=discord.Color.green()
        )
        lfg_embed.set_footer(text=(
            f"Session Thread: {thread.name} | "
            f"Session Thread ID: {thread.id} | Starter: {starter_name}"
        ))
        # pass hub_channel_id into view and capture the sent message
        lfg_view = LFGView(
            session_id=session_id,
            thread_id=thread.id,
            hub_channel_id=self.hub_channel_id
        )
        lfg_msg = await hub_channel.send(embed=lfg_embed, view=lfg_view)
        lfg_view.lfg_message_id = lfg_msg.id

        logger.info(f"★ Posted LFG post (ID: {lfg_msg.id}) in hub for session {session_id} by {starter_name}")

    async def cleanup_lfg_posts(self, starter_name: str, thread_id: int):
        """
        Cleans up any LFG posts in the hub channel for a given session starter and thread.
        """
        if not self.hub_channel_id:
            return
        hub_channel = self.bot.get_channel(self.hub_channel_id)
        if not hub_channel:
            return

        thread_id_str = str(thread_id)
        async for message in hub_channel.history(limit=100):
            if message.author.id != self.bot.user.id or not message.embeds:
                continue
            for embed in message.embeds:
                footer = embed.footer.text or ""
                if f"Starter: {starter_name}" in footer and f"Session Thread ID: {thread_id_str}" in footer:
                    await message.delete()
                    logger.info(f"★ Deleted LFG post (message ID: {message.id})")

    @commands.Cog.listener()
    async def on_interaction(self, interaction: discord.Interaction) -> None:
        # only button/link component clicks
        if interaction.type is not InteractionType.component:
            return

        # if hub isn’t set up yet, or this isn’t in the hub channel, ignore
        if self.hub_channel_id is None or interaction.channel.id != self.hub_channel_id:
            return

        cid = (interaction.data or {}).get("custom_id", "").strip()
        logger.debug(
            "[Hub] on_interaction id=%s done=%s cid=%r",
            interaction.id,
            interaction.response.is_done(),
            cid
        )
        if not cid:
            return


        # ——— EPHEMERAL MENU: LOAD GAME ———
        if cid == "hub_load_game":
            saved = SessionModel.get_saved_sessions_for_user(interaction.user.id)
            if not saved:
                return await interaction.response.send_message(
                    "❌ You have no saved adventures to load.",
                    ephemeral=True
                )

            # build the embed
            embed = discord.Embed(
                title="🔄 Load Your Adventure",
                description="Select which saved session you’d like to reopen:",
                color=discord.Color.blue()
            )
            for idx, s in enumerate(saved, start=1):
                players = SessionPlayerModel.get_player_states(s["session_id"])
                lines = [
                    f"<@{p['player_id']}> **{ClassModel.get_class_name(p['class_id'])} Lv {p['level']}**"
                    for p in players
                ]
                embed.add_field(
                    name=f"Slot {idx}: Session #{s['session_id']} ({s['difficulty']})",
                    value="\n".join(lines) or "No players?",
                    inline=False
                )
            view = LoadSessionView(saved)

            # single ACK: defer then followup
            await interaction.response.defer(ephemeral=True)
            return await interaction.followup.send(embed=embed, view=view, ephemeral=True)

        # ——— EPHEMERAL MENU: CANCEL LOAD ———
        if cid == "hub_load_cancel":
            return await interaction.edit_original_response(
                content="Load cancelled.",
                embed=None,
                view=None
            )

        # ——— EPHEMERAL MENU: SLOT SELECTED ———
        if cid.startswith("hub_load_slot_"):
            session_id = int(cid.rsplit("_", 1)[-1])

            # 1) Defer so load_session can follow up
            await interaction.response.defer(ephemeral=True)

            # 2) Actually reload the session
            await self.bot.get_cog("SessionManager").load_session(interaction, session_id)

            # 3) Clear the original slot picker
            return await interaction.edit_original_response(
                content=None,
                embed=None,
                view=None
            )

        # ——— MAIN HUB EMBED (non‑ephemeral) BUTTONS ———
        if cid == "hub_tutorial":
            tutorial_embed = hub_embed.get_tutorial_embed(page=1)
            return await interaction.response.edit_message(
                embed=tutorial_embed,
                view=TutorialView(current_page=1)
            )

        if cid == "hub_high_scores":
            sm = interaction.client.get_cog("SessionManager")
            high_scores = await sm.get_high_scores() if sm else []
            new_embed = hub_embed.get_high_scores_embed(high_scores)
            return await interaction.response.edit_message(
                embed=new_embed,
                view=None
            )

        if cid == "hub_back":
            main_embed = hub_embed.get_main_hub_embed()
            return await interaction.response.edit_message(
                embed=main_embed,
                view=HubView()
            )
        if cid == "setup_new_game":
            # handled in GameMaster.on_interaction
            return

        logger.debug(f"HubManager: unhandled custom_id='{cid}'")



class HubView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(discord.ui.Button(
            label="New Game", style=discord.ButtonStyle.green,
            custom_id="setup_new_game"
        ))
        self.add_item(discord.ui.Button(
            label="Load Game", style=discord.ButtonStyle.secondary,
            custom_id="hub_load_game"
        ))
        self.add_item(discord.ui.Button(
            label="Tutorial", style=discord.ButtonStyle.secondary,
            custom_id="hub_tutorial"
        ))
        self.add_item(discord.ui.Button(
            label="High Scores", style=discord.ButtonStyle.secondary,
            custom_id="hub_high_scores"
        ))


class LoadSessionView(discord.ui.View):
    def __init__(self, sessions: List[Dict[str, Any]]):
        super().__init__(timeout=None)
        row = 0
        count = 0

        for s in sessions:
            sid = s["session_id"]
            # If we’ve already added 5 buttons in this row, move to next
            if count >= 5:
                row += 1
                count = 0

            self.add_item(discord.ui.Button(
                label=f"Session #{sid}",
                style=discord.ButtonStyle.primary,
                custom_id=f"hub_load_slot_{sid}",
                row=row
            ))
            count += 1

        # Put “Cancel” on the row after the last batch of session buttons
        self.add_item(discord.ui.Button(
            label="Cancel",
            style=discord.ButtonStyle.secondary,
            custom_id="hub_load_cancel",
            row=row + 1
        ))


class TutorialView(discord.ui.View):
    def __init__(self, current_page: int):
        super().__init__(timeout=None)
        self.current_page = current_page

    @discord.ui.button(label="Back", style=discord.ButtonStyle.secondary, custom_id="hub_back", row=0)
    async def back(self, interaction: discord.Interaction, button: discord.ui.Button):
        main_embed = hub_embed.get_main_hub_embed()
        await interaction.response.edit_message(embed=main_embed, view=HubView())

    @discord.ui.button(label="Previous", style=discord.ButtonStyle.primary, custom_id="tutorial_prev", row=1)
    async def previous(self, interaction: discord.Interaction, button: discord.ui.Button):
        total = hub_embed.get_tutorial_page_count()
        # wrap or cycle back to the last page
        self.current_page = self.current_page - 1 if self.current_page > 1 else total
        new_embed = hub_embed.get_tutorial_embed(page=self.current_page)
        await interaction.response.edit_message(embed=new_embed, view=self)

    @discord.ui.button(label="Next", style=discord.ButtonStyle.primary, custom_id="tutorial_next", row=1)
    async def next(self, interaction: discord.Interaction, button: discord.ui.Button):
        total = hub_embed.get_tutorial_page_count()
        # wrap or cycle back to the first page
        self.current_page = self.current_page + 1 if self.current_page < total else 1
        new_embed = hub_embed.get_tutorial_embed(page=self.current_page)
        await interaction.response.edit_message(embed=new_embed, view=self)



class LFGView(discord.ui.View):
    def __init__(self, session_id: int, thread_id: int, hub_channel_id: int):
        super().__init__(timeout=None)
        self.session_id = session_id
        self.thread_id = thread_id
        self.hub_channel_id = hub_channel_id
        self.lfg_message_id = None

    @discord.ui.button(label="Join Game", style=discord.ButtonStyle.primary, custom_id="lfg_join_game")
    async def join_game(self, interaction: discord.Interaction, button: discord.ui.Button):
        session_manager = interaction.client.get_cog("SessionManager")
        if not session_manager:
            return await interaction.response.send_message(
                "❌ SessionManager not available.", ephemeral=True
            )

        session = session_manager.sessions.get(self.session_id)
        if session and interaction.user.id == session.owner_id:
            return await interaction.response.send_message(
                "⚠️ You’re the game creator—no need to join yourself. Open your thread directly!",
                ephemeral=True
            )
        if session and interaction.user.id in session.players:
            return await interaction.response.send_message(
                "⚠️ You’ve already joined this session!", ephemeral=True
            )

        joined = await session_manager.join_session(
            interaction,
            self.session_id,
            self.thread_id,
            interaction.user
        )
        if joined:
            game_master = interaction.client.get_cog("GameMaster")
            if game_master:
                # only update the **thread**'s queue embed
                await game_master.update_queue_embed(self.thread_id, self.session_id)

            url = f"https://discord.com/channels/{interaction.guild.id}/{self.thread_id}/{self.thread_id}"
            view = discord.ui.View()
            view.add_item(discord.ui.Button(label="Open Session", style=discord.ButtonStyle.link, url=url))
            return await interaction.response.send_message(
                embed=discord.Embed(
                    title="You joined the game!",
                    description="Click below to open the session thread.",
                    color=discord.Color.green()
                ),
                view=view,
                ephemeral=True
            )

        return await interaction.response.send_message(
            "Failed to join the game. Please try again.",
            ephemeral=True
        )


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(HubManager(bot))
    logger.info("HubManager cog loaded with extensive debug logging.")
