# cogs/embed_manager.py
from __future__ import annotations

import asyncio
import logging
import time
from typing import Any, Dict, List, Optional, Set, Tuple

import discord
from discord.ext import commands
from discord.ui import View, Button

from models.database import Database
from utils.ui_helpers import (
    create_cooldown_bar,
    create_progress_bar,
    get_emoji_for_room_type,
    format_status_effects,
)

logger = logging.getLogger("EmbedManager")
logger.setLevel(logging.DEBUG)

# Discord refuses completely blank title / description fields.
_ZWSP: str = "\u200b"  # zero-width space


class EmbedManager(commands.Cog):
    """Centralised embed + view builder used by every other cog."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.db = Database()

        # channel_id ➜ message_id
        self.active_messages: Dict[int, int] = {}
        self.status_messages: Dict[int, int] = {}

        # channel_id ➜ asyncio.Lock to serialize rapid updates
        self._update_locks: Dict[int, asyncio.Lock] = {}

        logger.debug("EmbedManager initialised.")

    # ──────────────────────────────────────────────────────────────────
    # Database connection helper
    # ──────────────────────────────────────────────────────────────────
    def db_connect(self):
        try:
            conn = self.db.get_connection()
            logger.debug("EmbedManager DB connection opened.")
            return conn
        except Exception as e:
            logger.error("EmbedManager DB error: %s", e)
            raise

    # ──────────────────────────────────────────────────────────────────
    # Ability icon helper
    # ──────────────────────────────────────────────────────────────────
    def get_ability_icon(self, ability: Dict[str, Any]) -> str:
        if ability.get("icon_url"):
            return ability["icon_url"]
        return {
            "Fire": "🔥",
            "Ice": "❄️",
            "Holy": "✨",
            "Non-Elemental": "🌟",
            "Air": "💨",
        }.get(ability.get("element_name"), "")

    # ──────────────────────────────────────────────────────────────────
    # Core embed / view sender/updater (serialized per-channel)
    # ──────────────────────────────────────────────────────────────────
    async def send_or_update_embed(
        self,
        interaction: discord.Interaction,
        title: str,
        description: str,
        *,
        image_url: Optional[str] = None,
        fields: Optional[List[Tuple[str, str, bool]]] = None,
        buttons: Optional[List[Tuple[str, discord.ButtonStyle, str, int]]] = None,
        embed_override: Optional[discord.Embed] = None,
        view_override: Optional[View] = None,
        channel: Optional[discord.abc.Messageable] = None,
    ) -> Optional[discord.Message]:
        """
        Send a new embed or update the existing one for this channel,
        guarding with a lock so rapid clicks won't duplicate.
        """
        target = channel or interaction.channel
        cid = target.id

        # Obtain or create the per-channel lock
        lock = self._update_locks.setdefault(cid, asyncio.Lock())

        async with lock:
            # Build or reuse embed
            if embed_override:
                embed = embed_override
            else:
                embed = discord.Embed(
                    title=title.strip() or _ZWSP,
                    description=description.strip() or _ZWSP,
                    color=discord.Color.blue(),
                )
                if image_url:
                    embed.set_image(url=image_url)
                if fields:
                    for name, value, inline in fields:
                        embed.add_field(name=name or _ZWSP, value=value or _ZWSP, inline=inline)

            # Build or reuse view
            if view_override:
                view = view_override
            else:
                view = View(timeout=None)
                if buttons:
                    for btn in buttons:
                        # now support 5‑tuples (label, style, custom_id, row, disabled)
                        if len(btn) == 5:
                            label, style, cid_btn, row, disabled = btn
                            view.add_item(
                                Button(
                                    label=label,
                                    style=style,
                                    custom_id=cid_btn,
                                    row=row,
                                    disabled=disabled,
                                )
                            )
                        elif len(btn) == 4:
                            label, style, cid_btn, row = btn
                            view.add_item(
                                Button(label=label, style=style, custom_id=cid_btn, row=row)
                            )
                        else:
                            label, style, cid_btn = btn
                            view.add_item(
                                Button(label=label, style=style, custom_id=cid_btn)
                            )

            # Send or edit
            try:
                if cid in self.active_messages:
                    msg = await target.fetch_message(self.active_messages[cid])
                    await msg.edit(embed=embed, view=view)
                else:
                    msg = await target.send(embed=embed, view=view)
                    self.active_messages[cid] = msg.id
                return msg
            except Exception as e:
                logger.error("send_or_update_embed failed: %s", e)
                # Fallback to followup
                try:
                    return await interaction.followup.send(embed=embed, view=view)
                except Exception as fb:
                    logger.error("Fallback send failed: %s", fb)
                    return None

    # ──────────────────────────────────────────────────────────────────
    # Submenu for Save / Quit / Back
    # ──────────────────────────────────────────────────────────────────
    def _get_game_menu_view(self) -> View:
        view = View(timeout=None)
        view.add_item(Button(label="💾 Save Game", style=discord.ButtonStyle.primary, custom_id="game_save"))
        view.add_item(Button(label="❌ Quit Game", style=discord.ButtonStyle.danger, custom_id="game_quit"))
        view.add_item(Button(label="↩️ Back", style=discord.ButtonStyle.secondary, custom_id="game_menu_back"))
        return view

    async def show_game_menu(self, interaction: discord.Interaction) -> None:
        cid = interaction.channel.id
        msg_id = self.active_messages.get(cid)
        if not msg_id:
            await interaction.response.send_message("⚙️ Game Menu", view=self._get_game_menu_view(), ephemeral=True)
            return

        msg = await interaction.channel.fetch_message(msg_id)
        await msg.edit(view=self._get_game_menu_view())
        if not interaction.response.is_done():
            await interaction.response.defer()

    # ──────────────────────────────────────────────────────────────────
    # Death embed (player fallen)
    # ──────────────────────────────────────────────────────────────────
    async def send_death_embed(
        self,
        interaction: discord.Interaction,
        description: str,
        image_url: Optional[str],
        view: View,
    ) -> None:
        embed = discord.Embed(
            title="💀 You have fallen",
            description=description,
            color=discord.Color.dark_red(),
        )
        if image_url:
            embed.set_image(url=image_url)
        await self.send_or_update_embed(
            interaction,
            title="",
            description="",
            embed_override=embed,
            view_override=view,
        )

    # ──────────────────────────────────────────────────────────────────
    # Persistent status embed
    # ──────────────────────────────────────────────────────────────────
    async def send_or_update_status_embed(
        self, interaction: discord.Interaction, embed: discord.Embed
    ) -> Optional[discord.Message]:
        cid = interaction.channel.id
        try:
            if cid in self.status_messages:
                m = await interaction.channel.fetch_message(self.status_messages[cid])
                await m.edit(embed=embed)
            else:
                m = await interaction.channel.send(embed=embed)
                self.status_messages[cid] = m.id
            return m
        except Exception as e:
            logger.error("Status embed update failed: %s", e)
            return None

    async def update_status_display(self, interaction: discord.Interaction, players: List[Dict[str, Any]]):
        cid = interaction.channel.id

        # If no players are left, remove any existing status message entirely.
        if not players:
            msg_id = self.status_messages.pop(cid, None)
            if msg_id:
                try:
                    msg = await interaction.channel.fetch_message(msg_id)
                    await msg.delete()
                except Exception as e:
                    logger.warning(
                        "Failed to delete status message in channel %s: %s",
                        cid,
                        e,
                    )
            return

        lines = []
        for p in players:
            turn = "👉 " if p.get("is_current_turn") else ""
            sts = format_status_effects(p.get("status_effects", []))
            lines.append(
                f"{turn}{p['username']}: ❤️ {p['hp']}/{p['max_hp']} ⚔️ {p['attack_power']} 🛡️ {p['defense']}"
                + (f" {sts}" if sts else "")
            )
        embed = discord.Embed(
            title="🛡️ Player Status", description="\n".join(lines), color=discord.Color.green()
        )
        await self.send_or_update_status_embed(interaction, embed)

    # ──────────────────────────────────────────────────────────────────
    # Class selection embed
    # ──────────────────────────────────────────────────────────────────
    async def send_class_selection_embed(self, interaction: discord.Interaction, num_players: int):
        title = "⚔️ Select Your Class..."
        desc = f"{num_players} players are joining—pick a class:"
        conn = self.db_connect()
        with conn.cursor(dictionary=True) as cur:
            cur.execute("SELECT class_id, class_name FROM classes")
            classes = cur.fetchall()
        embed = discord.Embed(title=title, description=desc, color=discord.Color.blue())
        embed.set_footer(text="Select your class to begin your adventure!")
        view = View(timeout=None)
        for idx, cls in enumerate(classes):
            view.add_item(
                Button(
                    label=cls["class_name"],
                    style=discord.ButtonStyle.primary,
                    custom_id=f"class_{cls['class_id']}",
                    row=idx // 5,
                )
            )
        await self.send_or_update_embed(interaction, _ZWSP, _ZWSP, embed_override=embed, view_override=view)

    # ──────────────────────────────────────────────────────────────────
    # Difficulty selection embed
    # ──────────────────────────────────────────────────────────────────
    async def send_difficulty_selection(self, interaction: discord.Interaction):
        conn = self.db_connect()
        with conn.cursor(dictionary=True) as cur:
            cur.execute("SELECT name FROM difficulties ORDER BY difficulty_id ASC")
            diffs = cur.fetchall()
        if not diffs:
            await interaction.followup.send("❌ No difficulties found!", ephemeral=True)
            return
        buttons = [(d["name"], discord.ButtonStyle.primary, f"difficulty_{d['name']}", 0) for d in diffs]
        await self.send_or_update_embed(interaction, "⚖️ Select Difficulty", "Choose the dungeon difficulty.", buttons=buttons)

    # ──────────────────────────────────────────────────────────────────
    # Intro slideshow embed
    # ──────────────────────────────────────────────────────────────────
    async def send_intro_embed(
        self, interaction: discord.Interaction, title: str, description: str, image_url: Optional[str] = None
    ):
        embed = discord.Embed(title=title or _ZWSP, description=description or _ZWSP, color=discord.Color.blue())
        if image_url:
            embed.set_image(url=image_url)
        view = View(timeout=None)
        view.add_item(Button(label="Continue", style=discord.ButtonStyle.primary, custom_id="intro_continue"))
        view.add_item(Button(label="Skip Intro", style=discord.ButtonStyle.secondary, custom_id="intro_skip"))
        await self.send_or_update_embed(interaction, _ZWSP, _ZWSP, embed_override=embed, view_override=view)

    # ──────────────────────────────────────────────────────────────────
    # Mini-map embed (with dead players shown)
    # ──────────────────────────────────────────────────────────────────
    async def send_minimap_embed(
        self,
        interaction: discord.Interaction,
        all_rooms: List[Dict[str, Any]],
        current_pos: Tuple[int, int],
        reveal_set: Set[Tuple[int, int]],
        discovered_set: Set[Tuple[int, int]],
        current_floor: int,
        dead_positions: Optional[Set[Tuple[int, int]]] = None,
    ):
        if dead_positions is None:
            dead_positions = set()

        rooms = [r for r in all_rooms if r["floor_id"] == current_floor]
        xs = [r["coord_x"] for r in rooms]
        ys = [r["coord_y"] for r in rooms]
        room_map = {(r["coord_x"], r["coord_y"]): r["room_type"] for r in rooms}

        VISITED = "🟨"
        gap = "    "
        lines: List[str] = []

        for y in range(min(ys), max(ys) + 1):
            row: List[str] = []
            for x in range(min(xs), max(xs) + 1):
                coord = (x, y)
                if coord in dead_positions:
                    char = "⚰️"
                elif coord == current_pos:
                    char = "🤺"
                elif coord in discovered_set and room_map.get(coord) in ("safe", "monster"):
                    char = VISITED
                elif coord in discovered_set or coord in reveal_set:
                    char = get_emoji_for_room_type(room_map.get(coord, "unknown"))
                else:
                    char = "⬛"
                row.append(char)
            lines.append(gap.join(row))
            lines.append("")

        grid = "\n".join(lines)
        embed = discord.Embed(
            title="🗺️ Mini-Map",
            description=f"```\n{grid}\n```",
            color=discord.Color.blue(),
        )
        embed.add_field(
            name="__**Legend**__",
            value=(
                "**🤺 You**  **🟨 Visited**  **🟩 Safe**  **🟥 Monster**  **⬛ Unknown**\n"
                "**🟦 Item**  **👤 Quest**  **🔼 Up**  **🔽 Down**\n"
                "**🟧 Trap**  **🔒 Locked**  **🟪 Shop**  **🔮 Illusion**\n"
                "**💀 Boss**  **🚪 Exit**  **⚰️ Fallen Player**"
            ),
            inline=False,
        )
        view = View(timeout=None)
        view.add_item(Button(label="Back to Room", style=discord.ButtonStyle.secondary, custom_id="minimap_back"))
        await self.send_or_update_embed(interaction, _ZWSP, _ZWSP, embed_override=embed, view_override=view)

    # ──────────────────────────────────────────────────────────────────
    # Battle menu embed
    # ──────────────────────────────────────────────────────────────────
    async def send_battle_menu(
        self,
        interaction: discord.Interaction,
        enemy_name: Optional[str] = None,
        enemy_hp: Optional[int] = None,
        enemy_max_hp: Optional[int] = None,
    ):
        title = "⚔️ You are in battle..."
        desc = f"A {enemy_name} appears!\nHP: {enemy_hp}/{enemy_max_hp}" if enemy_name else "Choose your action!"
        buttons = [
            ("Attack", discord.ButtonStyle.danger,    "combat_attack",      0),
            ("Skill",  discord.ButtonStyle.primary,   "combat_skill_menu",  0),
            ("Use",    discord.ButtonStyle.success,   "combat_item",        0),
            ("Flee",   discord.ButtonStyle.secondary, "combat_flee",        0),
            ("Menu",   discord.ButtonStyle.secondary, "action_menu",        0),
        ]
        await self.send_or_update_embed(interaction, title, desc, buttons=buttons)

    # ──────────────────────────────────────────────────────────────────
    # Inventory menu embed
    # ──────────────────────────────────────────────────────────────────
    async def send_inventory_menu(self, interaction: discord.Interaction):
        conn = self.db_connect()
        with conn.cursor(dictionary=True) as cur:
            cur.execute("SELECT item_name, item_id FROM items")
            items = cur.fetchall()
        buttons = [(i["item_name"], discord.ButtonStyle.primary, f"item_{i['item_id']}", 0) for i in items]
        await self.send_or_update_embed(interaction, "🎒 Your Inventory", "Choose an item:", buttons=buttons)

    # ──────────────────────────────────────────────────────────────────
    # NPC shop embed
    # ──────────────────────────────────────────────────────────────────
    async def send_npc_shop_embed(
        self,
        interaction: discord.Interaction,
        vendor_name: str,
        dialogue: str,
        image_url: str,
        player_currency: int,
    ):
        desc = f"{dialogue}\n\n**Your Gil:** {player_currency}"
        buttons = [
            ("Buy",  discord.ButtonStyle.primary,   "shop_buy_menu",  0),
            ("Sell", discord.ButtonStyle.primary,   "shop_sell_menu", 0),
            ("Back", discord.ButtonStyle.secondary, "shop_back_main", 0),
        ]
        await self.send_or_update_embed(interaction, f"Shop: {vendor_name}", desc, image_url=image_url, buttons=buttons)

    # ──────────────────────────────────────────────────────────────────
    # Use-item embed
    # ──────────────────────────────────────────────────────────────────
    async def send_use_item_embed(
        self,
        interaction: discord.Interaction,
        inventory_items: List[Dict[str, Any]],
        player_status: Dict[str, Any],
        game_log: str,
        allowed_context: str,
        back_custom_id: str,
    ):
        embed = discord.Embed(title="🎒 Use an Item", color=discord.Color.green())
        embed.add_field(
            name="Player Status",
            value=f"HP: {player_status.get('hp','?')}/{player_status.get('max_hp','?')} | Gil: {player_status.get('gil','?')}",
            inline=False,
        )
        embed.add_field(name="Game Log", value=game_log or _ZWSP, inline=False)
        inv_text = "Your inventory is empty." if not inventory_items else ""
        view = View(timeout=None)
        for item in inventory_items:
            tgt = item.get("target_type", "any")
            usable = (tgt in ["self", "enemy", "any"]) if allowed_context == "battle" else (tgt in ["self", "ally", "any"])
            note = "" if usable else " (Not usable here)"
            inv_text += f"**{item['item_name']}**: {item.get('description','')} {note}\nQuantity: {item.get('quantity',0)}\n\n"
            btn = Button(
                label=f"Use {item['item_name']} (x{item.get('quantity',0)})",
                style=discord.ButtonStyle.primary,
                custom_id=f"use_item_{item['item_id']}",
                disabled=not usable,
            )
            view.add_item(btn)
        embed.add_field(name="Inventory", value=inv_text or _ZWSP, inline=False)
        view.add_item(Button(label="Back", style=discord.ButtonStyle.secondary, custom_id=back_custom_id))
        await self.send_or_update_embed(interaction, _ZWSP, _ZWSP, embed_override=embed, view_override=view)

    # ──────────────────────────────────────────────────────────────────
    # Skill menu embed
    # ──────────────────────────────────────────────────────────────────
    async def send_skill_menu_embed(self, interaction: discord.Interaction, abilities: List[Dict[str, Any]]):
        if not abilities:
            buttons = [("Back", discord.ButtonStyle.secondary, "combat_skill_back", 0)]
            await self.send_or_update_embed(interaction, "No abilities found", "Please check your unlocks.", buttons=buttons)
            return
        abilities = sorted(abilities, key=lambda a: a.get("ability_name", "").lower())
        embed = discord.Embed(title="Select a Skill", description="Choose one of your abilities:", color=discord.Color.blue())
        view = View(timeout=None)
        rows = min(5, len(abilities))
        cols = -(-len(abilities) // rows)
        for r in range(rows):
            for c in range(cols):
                idx = r + c * rows
                if idx >= len(abilities):
                    continue
                ab = abilities[idx]
                icon = self.get_ability_icon(ab)
                cd = ab.get("cooldown", 0)
                cur_cd = ab.get("current_cooldown", 0)
                cd_bar = create_cooldown_bar(cur_cd, cd) if cd and cur_cd else ("[Ready]" if cd else "")
                label = f"{icon} {ab['ability_name']} {cd_bar}".strip()
                if len(label) > 80:
                    label = label[:77] + "..."
                view.add_item(Button(label=label, style=discord.ButtonStyle.primary, custom_id=f"combat_skill_{ab['ability_id']}", row=r))
        view.add_item(Button(label="Back", style=discord.ButtonStyle.secondary, custom_id="combat_skill_back", row=4))
        await self.send_or_update_embed(interaction, _ZWSP, _ZWSP, embed_override=embed, view_override=view)

    # ──────────────────────────────────────────────────────────────────
    # Build main menu buttons (static 4‑slot movement row + action row)
    # ──────────────────────────────────────────────────────────────────
    def get_main_menu_buttons(
        self,
        *,
        directions: Optional[List[str]] = None,
        include_shop: bool = False,
        vendor_id: Optional[int] = None,
        is_item: bool = False,
        is_locked: bool = False,
        has_key: bool = False,
        is_stair_up: bool = False,
        is_stair_down: bool = False,
    ) -> List[Tuple[str, discord.ButtonStyle, str, int, bool]]:
        """
        Always returns 4 move‑buttons in the exact order: North, South, West, East.
        Missing exits become a grey, disabled “⛔” placeholder.
        After that comes the standard action row.
        """
        btns: List[Tuple[str, discord.ButtonStyle, str, int, bool]] = []
        available = set(directions or [])
        order = [
            ("north", "⬆️"),
            ("south", "⬇️"),
            ("west",  "⬅️"),
            ("east",  "➡️"),
        ]

        # ── Row 0: movement slots ────────────────────────────────
        for dir_key, emoji in order:
            if dir_key in available:
                btns.append((
                    f"{emoji} {dir_key.capitalize()}",
                    discord.ButtonStyle.primary,
                    f"move_{dir_key}",
                    0,
                    False,  # enabled
                ))
            else:
                btns.append((
                    "⛔",
                    discord.ButtonStyle.secondary,
                    f"move_{dir_key}_disabled",
                    0,
                    True,   # disabled
                ))

        # ── Row 1: standard actions ─────────────────────────────
        action_row = [
            ("Look Around", discord.ButtonStyle.secondary, "action_look_around", 1, False),
            ("Skill",       discord.ButtonStyle.primary,   "action_skill",        1, False),
            ("Use",         discord.ButtonStyle.success,   "action_use",          1, False),
            ("Character",   discord.ButtonStyle.danger,    "action_character",    1, False),
            ("Menu",        discord.ButtonStyle.secondary, "action_menu",         1, False),
        ]
        btns.extend(action_row)

        # ── Row 2: shop / unlock / stairs (optional) ────────────
        if include_shop and vendor_id is not None:
            btns.append(("Shop", discord.ButtonStyle.secondary, f"action_shop_{vendor_id}", 2, False))
        if is_locked and has_key:
            btns.append(("🔒 Unlock Door", discord.ButtonStyle.success, "action_unlock_door", 2, False))
        if is_stair_up:
            btns.append(("⬆️ Use Stairs", discord.ButtonStyle.success, "action_use_stairs", 2, False))
        if is_stair_down:
            btns.append(("⬇️ Use Stairs", discord.ButtonStyle.success, "action_use_stairs", 2, False))

        return btns

    # ──────────────────────────────────────────────────────────────────
    # State router for external calls
    # ──────────────────────────────────────────────────────────────────
    STATE_BUILDERS = {
        "main":     lambda self, i, d: self.send_or_update_embed(i, d.get("title","Room"), d.get("description",_ZWSP), image_url=d.get("image_url"), buttons=d.get("buttons")),
        "battle":   lambda self, i, d: self.send_battle_menu(i, d.get("enemy_name"), d.get("enemy_hp"), d.get("enemy_max_hp")),
        "death":    lambda self, i, d: self.send_death_embed(i, d["description"], d.get("image_url"), d["view"]),
        "boss":     lambda self, i, d: self.send_boss_embed(i, d.get("boss_info"), d.get("battle_log",_ZWSP)),
        "illusion": lambda self, i, d: (
            self.send_illusion_crystal_embed(i, d.get("crystals", []), d.get("index", 0))
            if d.get("illusion_type") == "elemental_crystal"
            else self.send_illusion_embed(i, d.get("room_info"))
        ),
    }

    async def send_or_update_embed_for_state(self, interaction: discord.Interaction, state: str, data: Dict[str, Any]):
        builder = self.STATE_BUILDERS.get(state)
        if not builder:
            logger.error("Unknown state for embed update: %s", state)
            return None
        return await builder(self, interaction, data)

    # ──────────────────────────────────────────────────────────────────
    # Boss battle embed
    # ──────────────────────────────────────────────────────────────────
    async def send_boss_embed(self, interaction: discord.Interaction, boss_info: Dict[str, Any], battle_log: str):
        def bar(cur: int, max_: int, length: int = 10) -> str:
            filled = int(round(length * cur / float(max_))) if max_ else 0
            return f"[{'█'*filled}{'░'*(length-filled)}] {cur}/{max_}"
        desc = (
            f"{boss_info.get('description','A fearsome boss stands before you.')}\n\n"
            f"**Boss HP:** {bar(boss_info['hp'], boss_info['max_hp'])}\n\n{battle_log}"
        )
        embed = discord.Embed(title=f"🔥 Boss Battle: {boss_info['enemy_name']}", description=desc, color=discord.Color.dark_orange())
        if boss_info.get("image_url"):
            embed.set_image(url=f"{boss_info['image_url']}?t={int(time.time())}")
        buttons = [
            ("Attack", discord.ButtonStyle.danger,    "combat_attack",      0),
            ("Skill",  discord.ButtonStyle.primary,   "combat_skill_menu",  0),
            ("Use",    discord.ButtonStyle.success,   "combat_item",        0),
            ("Flee",   discord.ButtonStyle.secondary, "combat_flee",        0),
            ("Menu",   discord.ButtonStyle.secondary, "action_menu",        0),
        ]
        await self.send_or_update_embed(interaction, _ZWSP, _ZWSP, embed_override=embed, buttons=buttons)

    # ──────────────────────────────────────────────────────────────────
    # Illusion room embed
    # ──────────────────────────────────────────────────────────────────
    async def send_illusion_embed(self, interaction: discord.Interaction, room_info: Dict[str, Any]):
        embed = discord.Embed(
            title="🔮 Illusion Challenge",
            description=(
                f"{room_info.get('description','The room appears dark and mysterious.')}\n\n"
                "What do you think is hidden here?\n"
                "Choose wisely: Enemy, Treasure, Vendor, or an Empty room."
            ),
            color=discord.Color.purple(),
        )
        if room_info.get("image_url"):
            embed.set_image(url=f"{room_info['image_url']}?t={int(time.time())}")
        buttons = [
            ("Enemy",    discord.ButtonStyle.primary,   "illusion_enemy",    0),
            ("Treasure", discord.ButtonStyle.success,   "illusion_treasure", 0),
            ("Vendor",   discord.ButtonStyle.primary,   "illusion_vendor",   0),
            ("Empty",    discord.ButtonStyle.secondary, "illusion_empty",    0),
        ]
        await self.send_or_update_embed(interaction, _ZWSP, _ZWSP, embed_override=embed, buttons=buttons)

    async def send_illusion_crystal_embed(
        self,
        interaction: discord.Interaction,
        crystals: List[Dict[str, Any]],
        index: int = 0,
    ) -> None:
        """Display the elemental crystals for the illusion challenge."""
        lines = []
        for i, c in enumerate(crystals):
            icon = {
                "Fire": "🔥",
                "Ice": "❄️",
                "Holy": "✨",
                "Non-Elemental": "🌟",
                "Air": "💨",
            }.get(c.get("element_name"), "")
            prefix = "➡️" if i == index else "▫️"
            lines.append(f"{prefix} Crystal {i + 1}: {icon} {c.get('element_name')}")
        desc = "Use elemental skills to shatter each crystal in order."
        embed = discord.Embed(
            title="🔮 Elemental Crystals",
            description=desc,
            color=discord.Color.purple(),
        )
        if lines:
            embed.add_field(name="Crystals", value="\n".join(lines), inline=False)
        buttons = [("Skill", discord.ButtonStyle.primary, "combat_skill_menu", 0)]
        await self.send_or_update_embed(
            interaction,
            _ZWSP,
            _ZWSP,
            embed_override=embed,
            buttons=buttons,
        )


async def setup(bot: commands.Bot):
    await bot.add_cog(EmbedManager(bot))
    logger.info("EmbedManager cog loaded ✔")
