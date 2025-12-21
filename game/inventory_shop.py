# cogs/inventory_shop.py

import json
import logging
import re
from typing import Optional, List, Dict, Any

import discord
from discord import Interaction, InteractionType
from discord.ext import commands

from models.database import Database
from models.session_models import SessionPlayerModel, ClassModel
from utils.helpers import load_config

logger = logging.getLogger("InventoryShop")
logger.setLevel(logging.DEBUG)

# --------------------------------------------------------------------------- #
# Helper utils
# --------------------------------------------------------------------------- #
def is_key_item(item_row: Dict[str, Any]) -> bool:
    """True if the DB row represents a quest / key item."""
    return item_row and item_row.get("type") == "quest"

def calculate_sell_price(buy_price: int, reduction_pct: float = 0.25) -> int:
    """
    Reduce the vendor’s buy_price by reduction_pct (default 25%).
    Always returns at least 1 gil.
    """
    sell = int(buy_price * (1 - reduction_pct))
    return max(1, sell)

def get_item_info(db: Database, item_id: int) -> Optional[Dict[str, Any]]:
    with db.get_connection() as conn, conn.cursor(dictionary=True) as cur:
        cur.execute("SELECT * FROM items WHERE item_id=%s", (item_id,))
        return cur.fetchone()

def filter_inventory(full_inv: List[Dict[str, Any]], *, exclude_keys: bool = True) -> List[Dict[str, Any]]:
    """Return the inventory list minus key items (unless exclude_keys=False)."""
    if not exclude_keys:
        return full_inv
    return [row for row in full_inv if not is_key_item(row)]

def is_revive_key(item_row: Dict[str, Any]) -> bool:
    """True if this item’s effect JSON has a revive field."""
    try:
        eff = json.loads(item_row.get("effect") or "{}")
        return "revive" in eff
    except Exception:
        return False

# --------------------------------------------------------------------------- #
# Inventory / Shop Cog
# --------------------------------------------------------------------------- #
class InventoryShop(commands.Cog):
    """Handles **use item** flow and **NPC vendor** buy / sell menus."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.db: Database = Database()
        self.config = load_config()

    # --------------------------------------------------------------------- #
    # Vendor helpers
    # --------------------------------------------------------------------- #
    def get_session_vendor(self, session_id: int, session_vendor_id: int) -> Optional[Dict[str, Any]]:
        with self.db.get_connection() as conn, conn.cursor(dictionary=True) as cur:
            cur.execute(
                "SELECT * FROM session_vendor_instances "
                "WHERE session_id=%s AND session_vendor_id=%s",
                (session_id, session_vendor_id)
            )
            return cur.fetchone()

    def get_vendor(self, vendor_id: int, session_id: Optional[int] = None) -> Optional[Dict[str, Any]]:
        # prefer per-session instance if supplied
        if session_id is not None:
            inst = self.get_session_vendor(session_id, vendor_id)
            if inst:
                return inst
        with self.db.get_connection() as conn, conn.cursor(dictionary=True) as cur:
            cur.execute("SELECT * FROM npc_vendors WHERE vendor_id=%s", (vendor_id,))
            return cur.fetchone()

    def get_vendor_items(self, session_vendor_id: int, session_id: int) -> List[Dict[str, Any]]:
        with self.db.get_connection() as conn, conn.cursor(dictionary=True) as cur:
            cur.execute(
                """
                SELECT i.item_id, i.item_name, i.type, svi.price, svi.stock
                FROM session_vendor_items svi
                JOIN items i ON i.item_id = svi.item_id
                WHERE svi.session_vendor_id = %s AND svi.session_id = %s
                """,
                (session_vendor_id, session_id)
            )
            # Vendors never sell key items
            return [row for row in cur.fetchall() if not is_key_item(row)]

    # --------------------------------------------------------------------- #
    # Player inventory helpers
    # --------------------------------------------------------------------- #
    def get_full_inventory(self, player_id: int, session_id: int) -> List[Dict[str, Any]]:
        """Return full inventory list with item info + quantity."""
        with self.db.get_connection() as conn, conn.cursor(dictionary=True) as cur:
            cur.execute(
                "SELECT inventory FROM players WHERE player_id=%s AND session_id=%s",
                (player_id, session_id)
            )
            row = cur.fetchone()
            raw_inv = json.loads(row["inventory"]) if row and row.get("inventory") else {}

            inventory: List[Dict[str, Any]] = []
            for item_id_str, qty in raw_inv.items():
                if qty <= 0:
                    continue
                try:
                    iid = int(item_id_str)
                except ValueError:
                    continue
                cur.execute(
                    "SELECT item_name, description, target_type, effect, type, price "
                    "FROM items WHERE item_id=%s", (iid,)
                )
                item_row = cur.fetchone()
                if item_row:
                    item_row.update(item_id=iid, quantity=qty)
                    inventory.append(item_row)
        return inventory

    # --------------------------------------------------------------------- #
    # Interaction router
    # --------------------------------------------------------------------- #
    @commands.Cog.listener()
    async def on_interaction(self, interaction: Interaction) -> None:
        if interaction.type != InteractionType.component:
            return
        
        # ── IGNORE HUB CHANNEL (let HubManager handle all hub buttons) ──
        hub_mgr = self.bot.get_cog("HubManager")
        if hub_mgr and interaction.channel.id == hub_mgr.hub_channel_id:
            return

        cid = interaction.data.get("custom_id", "")

        handled_prefixes = (
            "shop_main_",
            "shop_buy_",
            "shop_sell_",
            "action_shop_",
            "buy_",
            "sell_",
            "use_item_",
        )
        handled_exacts = {"back_from_use", "shop_back_room"}
        if not (cid.startswith(handled_prefixes) or cid in handled_exacts):
            return

        # Always defer so edits/followups are possible; ignore if already acknowledged
        try:
            if not interaction.response.is_done():
                await interaction.response.defer()
        except discord.errors.HTTPException as e:
            logger.debug("Deferred interaction failed (already acknowledged): %s", e)

        try:
            # ---------------- Shop main ----------------
            if cid.startswith(("shop_main_", "action_shop_")):
                m = re.match(r"(?:shop_main_|action_shop_)(\d+)", cid)
                if m:
                    await self.display_shop_menu(interaction, int(m.group(1)))
            elif cid.startswith("shop_buy_"):
                await self.display_buy_menu(interaction, int(cid.split("_")[2]))
            elif cid.startswith("shop_sell_"):
                await self.display_sell_menu(interaction, int(cid.split("_")[2]))
            elif cid.startswith("buy_"):
                _, vid, iid = cid.split("_")
                try:
                    if not interaction.response.is_done():
                        await interaction.response.defer(thinking=True)
                except discord.errors.HTTPException:
                    pass
                await self.process_purchase(interaction, int(vid), int(iid))
            elif cid.startswith("sell_"):
                _, vid, iid = cid.split("_")
                try:
                    if not interaction.response.is_done():
                        await interaction.response.defer(thinking=True)
                except discord.errors.HTTPException:
                    pass
                await self.process_sale(interaction, int(vid), int(iid))
            # --------------- Use-item flow --------------
            elif cid.startswith("use_item_"):
                parts = cid.split("_")
                if len(parts) >= 3:
                    iid = int(parts[2])
                    try:
                        if not interaction.response.is_done():
                            await interaction.response.defer(thinking=True)
                    except discord.errors.HTTPException:
                        pass
                    await self.process_use_item(interaction, iid)
                else:
                    await self.display_use_item_menu(interaction)
            elif cid == "back_from_use":
                mgr = self.bot.get_cog("SessionManager")
                if mgr:
                    await mgr.refresh_current_state(interaction)
            # --------------- Back to room ---------------
            elif cid == "shop_back_room":
                mgr = self.bot.get_cog("SessionManager")
                if mgr:
                    await mgr.refresh_current_state(interaction)
        except Exception as e:
            logger.error("Interaction handling error: %s", e, exc_info=True)

    # --------------------------------------------------------------------- #
    # SHOP UI
    # --------------------------------------------------------------------- #
    async def display_shop_menu(self, interaction: Interaction, vendor_id: int) -> None:
        mgr = self.bot.get_cog("SessionManager")
        session = mgr.get_session(interaction.channel.id) if mgr else None
        if not session:
            await interaction.followup.send("❌ No active session.", ephemeral=True)
            return

        vendor = self.get_vendor(vendor_id, session.session_id)
        if not vendor:
            await interaction.followup.send("❌ Vendor not found.", ephemeral=True)
            return

        embed = discord.Embed(
            title=f"🛒 {vendor['vendor_name']}'s Shop",
            description=vendor.get("description", ""),
            color=discord.Color.gold()
        )
        if vendor.get("image_url"):
            embed.set_image(url=vendor["image_url"])

        view = discord.ui.View(timeout=None)
        view.add_item(discord.ui.Button(
            label="Buy", style=discord.ButtonStyle.primary,
            custom_id=f"shop_buy_{vendor_id}"
        ))
        view.add_item(discord.ui.Button(
            label="Sell", style=discord.ButtonStyle.primary,
            custom_id=f"shop_sell_{vendor_id}"
        ))
        view.add_item(discord.ui.Button(
            label="Back to Room", style=discord.ButtonStyle.secondary,
            custom_id="shop_back_room"
        ))

        emb_mgr = self.bot.get_cog("EmbedManager")
        if emb_mgr:
            await emb_mgr.send_or_update_embed(interaction, "", "",
                                               embed_override=embed, view_override=view)
        else:
            await interaction.followup.send(embed=embed, view=view, ephemeral=True)

    async def display_buy_menu(self, interaction: Interaction, vendor_id: int) -> None:
        mgr = self.bot.get_cog("SessionManager")
        session = mgr.get_session(interaction.channel.id) if mgr else None
        if not session:
            await interaction.followup.send("❌ No active session.", ephemeral=True)
            return

        items = self.get_vendor_items(vendor_id, session.session_id)
        vendor = self.get_vendor(vendor_id, session.session_id)
        if not vendor:
            await interaction.followup.send("❌ Vendor not found.", ephemeral=True)
            return

        embed = discord.Embed(
            title=f"🛒 {vendor['vendor_name']}: Buy Items",
            color=discord.Color.gold()
        )
        if vendor.get("image_url"):
            embed.set_image(url=vendor["image_url"])
            
        with self.db.get_connection() as conn, conn.cursor(dictionary=True) as cur:
            cur.execute(
                "SELECT gil FROM players WHERE player_id=%s AND session_id=%s",
                (interaction.user.id, session.session_id)
            )
            player = cur.fetchone()
            gil = player["gil"] if player else 0

        embed.add_field(
            name="Your Gil",
            value=f"{gil} gil",
            inline=False
        )
        for it in items:
            embed.add_field(
                name=f"{it['item_name']} (x{it['stock']})",
                value=f"Price: {it['price']} gil",
                inline=False
            )

        view = discord.ui.View(timeout=None)
        for it in items:
            view.add_item(discord.ui.Button(
                label=f"Buy {it['item_name']}",
                style=discord.ButtonStyle.primary,
                custom_id=f"buy_{vendor_id}_{it['item_id']}"
            ))
        view.add_item(discord.ui.Button(
            label="Back", style=discord.ButtonStyle.secondary,
            custom_id=f"shop_main_{vendor_id}"
        ))
        view.add_item(discord.ui.Button(
            label="Back to Room", style=discord.ButtonStyle.secondary,
            custom_id="shop_back_room"
        ))

        emb_mgr = self.bot.get_cog("EmbedManager")
        if emb_mgr:
            await emb_mgr.send_or_update_embed(interaction, "", "",
                                               embed_override=embed, view_override=view)
        else:
            await interaction.followup.send(embed=embed, view=view, ephemeral=True)

    async def display_sell_menu(self, interaction: Interaction, vendor_id: int) -> None:
        mgr = self.bot.get_cog("SessionManager")
        session = mgr.get_session(interaction.channel.id) if mgr else None
        if not session:
            await interaction.followup.send("❌ No active session.", ephemeral=True)
            return

        vendor = self.get_vendor(vendor_id, session.session_id)
        if not vendor:
            await interaction.followup.send("❌ Vendor not found.", ephemeral=True)
            return

        full_inv = self.get_full_inventory(interaction.user.id, session.session_id)
        sellable_inv = filter_inventory(full_inv)  # remove key items

        if not sellable_inv:
            await interaction.followup.send("You have no items to sell.", ephemeral=True)
            return

        embed = discord.Embed(
            title=f"🛒 {vendor['vendor_name']}: Sell Items",
            color=discord.Color.gold()
        )
        if vendor.get("image_url"):
            embed.set_image(url=vendor["image_url"])

        # --- Add Gil Field AFTER embed is created ---
        with self.db.get_connection() as conn, conn.cursor(dictionary=True) as cur:
            cur.execute(
                "SELECT gil FROM players WHERE player_id=%s AND session_id=%s",
                (interaction.user.id, session.session_id)
            )
            player = cur.fetchone()
            gil = player["gil"] if player else 0

        embed.add_field(
            name="Your Gil",
            value=f"{gil} gil",
            inline=False
        )

        # --- Add Items and Buttons ---
        vendor_items = self.get_vendor_items(vendor_id, session.session_id)
        vendor_prices = {itm['item_id']: itm['price'] for itm in vendor_items}

        view = discord.ui.View(timeout=None)
        for it in sellable_inv:
            iid = it["item_id"]
            buy_price = vendor_prices.get(iid, get_item_info(self.db, iid).get("price", 0))
            sell_price = calculate_sell_price(buy_price)
            embed.add_field(
                name=f"{it['item_name']} (x{it['quantity']})",
                value=f"Vendor’s price: {buy_price} gil\nYour sell-back: {sell_price} gil",
                inline=False
            )
            view.add_item(discord.ui.Button(
                label=f"Sell {it['item_name']}",
                style=discord.ButtonStyle.primary,
                custom_id=f"sell_{vendor_id}_{iid}"
            ))

        view.add_item(discord.ui.Button(
            label="Back", style=discord.ButtonStyle.secondary,
            custom_id=f"shop_main_{vendor_id}"
        ))
        view.add_item(discord.ui.Button(
            label="Back to Room", style=discord.ButtonStyle.secondary,
            custom_id="shop_back_room"
        ))

        emb_mgr = self.bot.get_cog("EmbedManager")
        if emb_mgr:
            await emb_mgr.send_or_update_embed(interaction, "", "",
                                            embed_override=embed, view_override=view)
        else:
            await interaction.followup.send(embed=embed, view=view, ephemeral=True)


    # --------------------------------------------------------------------- #
    # USE-ITEM FLOW
    # --------------------------------------------------------------------- #
    async def display_use_item_menu(self, interaction: Interaction) -> None:
        mgr = self.bot.get_cog("SessionManager")
        session = mgr.get_session(interaction.channel.id) if mgr else None
        if not session:
            await interaction.followup.send("❌ No active session.", ephemeral=True)
            return
        if session.current_enemy and session.current_turn != interaction.user.id:
            return  # not your turn during battle

        full_inv = self.get_full_inventory(interaction.user.id, session.session_id)
        usable_inv = [
            it for it in filter_inventory(full_inv)
            if not is_revive_key(it)
        ]

        with self.db.get_connection() as conn, conn.cursor(dictionary=True) as cur:
            cur.execute(
                "SELECT hp, max_hp, gil FROM players "
                "WHERE player_id=%s AND session_id=%s",
                (interaction.user.id, session.session_id)
            )
            status = cur.fetchone()

        emb_mgr = self.bot.get_cog("EmbedManager")
        if emb_mgr:
            await emb_mgr.send_use_item_embed(
                interaction, usable_inv, status, "",
                "battle" if session.current_enemy else "room",
                "back_from_use"
            )
        else:
            await interaction.followup.send("❌ EmbedManager unavailable.", ephemeral=True)

    async def process_use_item(self, interaction: Interaction, item_id: int) -> None:
        mgr = self.bot.get_cog("SessionManager")
        session = mgr.get_session(interaction.channel.id) if mgr else None
        if not session:
            await interaction.followup.send("❌ No active session.", ephemeral=True)
            return

        item_row = get_item_info(self.db, item_id)
        if not item_row:
            await interaction.followup.send("❌ Item not found.", ephemeral=True)
            return
        if is_key_item(item_row):
            await interaction.followup.send("❌ You can't use that item here.", ephemeral=True)
            return

        with self.db.get_connection() as conn, conn.cursor(dictionary=True) as cur:
            cur.execute(
                "SELECT inventory, hp, max_hp, mp, max_mp, class_id FROM players "
                "WHERE player_id=%s AND session_id=%s",
                (interaction.user.id, session.session_id)
            )
            player = cur.fetchone()
            if not player:
                await interaction.followup.send("❌ Player data missing.", ephemeral=True)
                return

            inv_dict = json.loads(player["inventory"]) if player.get("inventory") else {}
            if str(item_id) not in inv_dict or inv_dict[str(item_id)] <= 0:
                await interaction.followup.send("❌ You don't have that item.", ephemeral=True)
                return

            effect = json.loads(item_row["effect"]) if item_row.get("effect") else {}
            heal = effect.get("heal", 0)
            restore_mp = effect.get("restore_mp", 0)
            is_trance = effect.get("trance", False)
            txt = f"You used **{item_row['item_name']}**."
            if heal:
                new_hp = min(player["hp"] + heal, player["max_hp"])
                cur.execute(
                    "UPDATE players SET hp=%s WHERE player_id=%s AND session_id=%s",
                    (new_hp, interaction.user.id, session.session_id)
                )
                txt += f" Healed **{heal}** HP! (HP: {new_hp}/{player['max_hp']})"
            if restore_mp and player.get("max_mp"):
                new_mp = min((player.get("mp") or 0) + restore_mp, player.get("max_mp") or 0)
                cur.execute(
                    "UPDATE players SET mp=%s WHERE player_id=%s AND session_id=%s",
                    (new_mp, interaction.user.id, session.session_id)
                )
                txt += f" Restored **{restore_mp}** MP! (MP: {new_mp}/{player['max_mp']})"

            inv_dict[str(item_id)] -= 1
            if inv_dict[str(item_id)] <= 0:
                del inv_dict[str(item_id)]
            cur.execute(
                "UPDATE players SET inventory=%s WHERE player_id=%s AND session_id=%s",
                (json.dumps(inv_dict), interaction.user.id, session.session_id)
            )
            conn.commit()
            if is_trance:
                bs = self.bot.get_cog("BattleSystem")
                if bs:
                    allow_trance = True
                    if ClassModel.get_class_name(player["class_id"]) == "Summoner":
                        unlocked = SessionPlayerModel.get_unlocked_eidolons(
                            session.session_id,
                            interaction.user.id,
                        )
                        allow_trance = bool(unlocked)
                    if allow_trance:
                        await bs.activate_trance(session, interaction.user.id)
                        txt += "\n*You feel a power welling up…*"

        await interaction.followup.send(txt, ephemeral=True)
        if mgr:
            await mgr.refresh_current_state(interaction)

    # --------------------------------------------------------------------- #
    # BUY / SELL BACK-END
    # --------------------------------------------------------------------- #
    async def process_purchase(self, interaction: Interaction, vendor_id: int, item_id: int) -> None:
        mgr = self.bot.get_cog("SessionManager")
        session = mgr.get_session(interaction.channel.id) if mgr else None
        if not session:
            await interaction.followup.send("❌ No active session.", ephemeral=True)
            return

        item_row = get_item_info(self.db, item_id)
        if is_key_item(item_row):
            await interaction.followup.send("❌ That item is not for sale.", ephemeral=True)
            return

        with self.db.get_connection() as conn, conn.cursor(dictionary=True) as cur:
            cur.execute(
                "SELECT gil, inventory FROM players "
                "WHERE player_id=%s AND session_id=%s",
                (interaction.user.id, session.session_id)
            )
            player = cur.fetchone()
            cur.execute(
                "SELECT price, stock FROM session_vendor_items "
                "WHERE session_vendor_id=%s AND item_id=%s AND session_id=%s",
                (vendor_id, item_id, session.session_id)
            )
            stock_row = cur.fetchone()

            if not player or not stock_row:
                await interaction.followup.send("❌ Invalid purchase.", ephemeral=True)
                return
            if player["gil"] < stock_row["price"]:
                await interaction.followup.send("❌ Not enough gil.", ephemeral=True)
                return
            if stock_row["stock"] <= 0:
                await interaction.followup.send("❌ Item out of stock.", ephemeral=True)
                return

            inv_dict = json.loads(player["inventory"]) if player.get("inventory") else {}
            inv_dict[str(item_id)] = inv_dict.get(str(item_id), 0) + 1
            cur.execute(
                "UPDATE players SET gil=%s, inventory=%s "
                "WHERE player_id=%s AND session_id=%s",
                (player["gil"] - stock_row["price"], json.dumps(inv_dict),
                 interaction.user.id, session.session_id)
            )
            cur.execute(
                "UPDATE session_vendor_items SET stock=stock-1 "
                "WHERE session_vendor_id=%s AND item_id=%s AND session_id=%s",
                (vendor_id, item_id, session.session_id)
            )
            conn.commit()

        await interaction.followup.send("✅ Purchase successful!", ephemeral=True)

        # Stay in the buy menu after purchase instead of bouncing back to the room
        await self.display_buy_menu(interaction, vendor_id)

    async def process_sale(self, interaction: Interaction, vendor_id: int, item_id: int) -> None:
        mgr = self.bot.get_cog("SessionManager")
        session = mgr.get_session(interaction.channel.id) if mgr else None
        if not session:
            await interaction.followup.send("❌ No active session.", ephemeral=True)
            return

        item_row = get_item_info(self.db, item_id)
        if is_key_item(item_row):
            await interaction.followup.send("❌ You can't sell that item.", ephemeral=True)
            return

        with self.db.get_connection() as conn, conn.cursor(dictionary=True) as cur:
            cur.execute(
                "SELECT gil, inventory FROM players "
                "WHERE player_id=%s AND session_id=%s",
                (interaction.user.id, session.session_id)
            )
            player = cur.fetchone()
            if not player:
                await interaction.followup.send("❌ Sale failed.", ephemeral=True)
                return

            inv_dict = json.loads(player["inventory"]) if player.get("inventory") else {}
            if str(item_id) not in inv_dict or inv_dict[str(item_id)] <= 0:
                await interaction.followup.send("❌ You don't have that item.", ephemeral=True)
                return

            cur.execute(
                "SELECT price FROM session_vendor_items "
                "WHERE session_vendor_id=%s AND item_id=%s AND session_id=%s",
                (vendor_id, item_id, session.session_id)
            )
            row = cur.fetchone()
            buy_price = row["price"] if row and row.get("price") is not None else item_row.get("price", 0)
            sell_price = calculate_sell_price(buy_price)

            inv_dict[str(item_id)] -= 1
            if inv_dict[str(item_id)] <= 0:
                del inv_dict[str(item_id)]

            cur.execute(
                "UPDATE players SET gil=%s, inventory=%s "
                "WHERE player_id=%s AND session_id=%s",
                (player["gil"] + sell_price, json.dumps(inv_dict),
                 interaction.user.id, session.session_id)
            )
            cur.execute(
                """
                INSERT INTO session_vendor_items (session_vendor_id, item_id, price, stock, session_id)
                VALUES (%s, %s, %s, 1, %s)
                ON DUPLICATE KEY UPDATE stock = stock + 1
                """,
                (vendor_id, item_id, buy_price, session.session_id)
            )
            conn.commit()

        await interaction.followup.send(f"✅ Sold for {sell_price} gil!", ephemeral=True)
        await self.display_sell_menu(interaction, vendor_id)

# --------------------------------------------------------------------------- #
# Setup
# --------------------------------------------------------------------------- #
async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(InventoryShop(bot))
    logger.info("InventoryShop cog loaded ✔")
