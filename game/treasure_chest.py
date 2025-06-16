from __future__ import annotations

import json
import logging
import random
import time
from typing import Any, Dict, List, Optional

import discord
from discord.ext import commands

from models.database import Database  # project DB wrapper
from models.session_models import SessionPlayerModel

logger = logging.getLogger("TreasureChest")
logger.setLevel(logging.DEBUG)

# ──────────────────────────────────────────────────────────────
#  Helper functions
# ──────────────────────────────────────────────────────────────


def db_connect() -> Any:
    """Return a fresh MySQL connection via the project’s Database helper."""
    return Database().get_connection()


def get_room_image(instance_id: int) -> str:
    """Return the current room image for a chest instance (or “”)."""
    conn = db_connect()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT r.image_url
                  FROM treasure_chest_instances t
                  JOIN rooms r ON r.session_id = t.session_id
                              AND r.floor_id   = t.floor_id
                              AND r.coord_x    = t.coord_x
                              AND r.coord_y    = t.coord_y
                 WHERE t.instance_id = %s
                """,
                (instance_id,),
            )
            row = cur.fetchone()
            return row[0] if row and row[0] else ""
    finally:
        conn.close()


def fetch_item_name(item_id: int | None) -> Optional[str]:
    """Human‑readable name for an item (None‑safe)."""
    if item_id is None:
        return None
    conn = db_connect()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT item_name FROM items WHERE item_id=%s", (item_id,))
            row = cur.fetchone()
            return row[0] if row else None
    finally:
        conn.close()


def _apply_chest_rewards(
    player_id: int,
    session_id: int,
    rewards: list[dict[str, Any]],
) -> None:
    """Apply gil & inventory gains from a chest."""
    conn = db_connect()
    try:
        with conn.cursor(dictionary=True) as cur:
            cur.execute(
                "SELECT gil, inventory FROM players WHERE player_id=%s AND session_id=%s",
                (player_id, session_id),
            )
            row = cur.fetchone() or {}
            gil = row.get("gil", 0)
            inv = json.loads(row.get("inventory") or "{}")

            for rw in rewards:
                if rw["reward_type"] == "gil":
                    gil += rw["reward_amount"]
                    continue
                if rw["reward_item_id"] is None:
                    logger.warning("Skipped chest reward with NULL item_id: %s", rw)
                    continue
                iid = str(rw["reward_item_id"])
                inv[iid] = inv.get(iid, 0) + rw["reward_amount"]

            cur.execute(
                "UPDATE players SET gil=%s, inventory=%s WHERE player_id=%s AND session_id=%s",
                (gil, json.dumps(inv), player_id, session_id),
            )
            if gil:
                SessionPlayerModel.add_gil_earned(session_id, player_id, gil)
        conn.commit()
    finally:
        conn.close()


# ──────────────────────────────────────────────────────────────
#  Interaction‑safety helper
# ──────────────────────────────────────────────────────────────


async def _ensure_deferred(
    interaction: discord.Interaction, *, ephemeral: bool = True
) -> None:
    """Guarantee the interaction has been ACK’d exactly once."""
    if not interaction.response.is_done():
        await interaction.response.defer(ephemeral=ephemeral)


# ──────────────────────────────────────────────────────────────
#  VIEW 1 – after “Unlock Chest”
# ──────────────────────────────────────────────────────────────


class StartChestUnlockView(discord.ui.View):
    """Initialises (or resumes) the lock code, then swaps to UnlockChestView."""

    def __init__(self, instance_id: int):
        super().__init__(timeout=None)
        self.instance_id = instance_id

    async def start_unlock_challenge(self, interaction: discord.Interaction) -> None:
        await _ensure_deferred(interaction)

        conn = db_connect()
        try:
            with conn.cursor(dictionary=True) as cur:
                cur.execute(
                    """
                    SELECT step, hint_value, is_broken
                      FROM treasure_chest_instances
                     WHERE instance_id=%s
                    """,
                    (self.instance_id,),
                )
                inst = cur.fetchone()
                if not inst:
                    return await interaction.followup.send(
                        "Chest data missing.", ephemeral=True
                    )
                if inst["is_broken"]:
                    return await interaction.followup.send(
                        "💥 The lock is jammed and won’t budge.", ephemeral=True
                    )

                if inst["step"] == 1:  # first visit
                    target = random.randint(2, 99)
                    hint = random.choice([n for n in range(2, 100) if n != target])
                    cur.execute(
                        """
                        UPDATE treasure_chest_instances
                           SET target_number=%s, hint_value=%s
                         WHERE instance_id=%s
                        """,
                        (target, hint, self.instance_id),
                    )
                    conn.commit()
                else:
                    hint = inst["hint_value"]
        finally:
            conn.close()

        img = get_room_image(self.instance_id)
        embed = discord.Embed(
            title="🔒 Chest Lock Challenge",
            description=(
                "**Step 1 / 3 — ✅ 0 | ❌ 0**\n\n"
                f"Is the secret number **higher** or **lower** than **{hint}**?"
            ),
            color=discord.Color.gold(),
        )
        if img:
            embed.set_image(url=f"{img}?t={int(time.time())}")

        await interaction.message.edit(
            embed=embed, view=UnlockChestView(self.instance_id)
        )


# ──────────────────────────────────────────────────────────────
#  VIEW 2 – High / Low mini‑game
# ──────────────────────────────────────────────────────────────


class UnlockChestView(discord.ui.View):
    """Up to 3 guesses; get 2 right (before 2 wrong) to unlock."""

    MAX_STEPS = 3

    def __init__(self, instance_id: int):
        super().__init__(timeout=None)
        self.instance_id = instance_id

    @discord.ui.button(
        label="⬆️ High", style=discord.ButtonStyle.primary, custom_id="guess_high"
    )
    async def guess_high(self, interaction: discord.Interaction, _: discord.ui.Button):
        await self._handle_guess(interaction, guess_higher=True)

    @discord.ui.button(
        label="⬇️ Low", style=discord.ButtonStyle.primary, custom_id="guess_low"
    )
    async def guess_low(self, interaction: discord.Interaction, _: discord.ui.Button):
        await self._handle_guess(interaction, guess_higher=False)

    @discord.ui.button(
        label="🔙 Back", style=discord.ButtonStyle.secondary, custom_id="guess_back"
    )
    async def go_back(self, interaction: discord.Interaction, _: discord.ui.Button):
        """Return to the standard room view."""
        self.stop()
        sm = interaction.client.get_cog("SessionManager")
        if sm:
            await sm.refresh_current_state(interaction)

    async def _handle_guess(
        self, interaction: discord.Interaction, *, guess_higher: bool
    ) -> None:
        await _ensure_deferred(interaction)

        conn = db_connect()
        try:
            with conn.cursor(dictionary=True) as cur:
                cur.execute(
                    """
                    SELECT step, correct_count, wrong_count,
                           target_number, hint_value,
                           session_id, floor_id, coord_x, coord_y,
                           is_unlocked, is_broken
                      FROM treasure_chest_instances
                     WHERE instance_id=%s
                    """,
                    (self.instance_id,),
                )
                inst = cur.fetchone()
                if not inst:
                    return await interaction.followup.send(
                        "Chest error.", ephemeral=True
                    )
                if inst["is_unlocked"]:
                    return await interaction.followup.send(
                        "Chest already unlocked!", ephemeral=True
                    )
                if inst["is_broken"]:
                    return await interaction.followup.send(
                        "💥 The lock is jammed.", ephemeral=True
                    )

                correct = (inst["target_number"] > inst["hint_value"]) == guess_higher
                next_step = inst["step"] + 1
                next_correct = inst["correct_count"] + (1 if correct else 0)
                next_wrong = inst["wrong_count"] + (0 if correct else 1)
                feedback = (
                    "✅ You hear a satisfying click!"
                    if correct
                    else "❌ The lock grinds ominously!"
                )

                gm = interaction.client.get_cog("GameMaster")

                # ── SUCCESS ────────────────────────────────────────
                if next_correct >= 2:
                    cur.execute(
                        "UPDATE treasure_chest_instances SET is_unlocked=1 WHERE instance_id=%s",
                        (self.instance_id,),
                    )
                    conn.commit()

                    if gm:
                        gm._unlock_chest_room(
                            inst["session_id"],
                            inst["floor_id"],
                            inst["coord_x"],
                            inst["coord_y"],
                        )
                        discovered_3d = await gm.update_permanent_discovered_room(
                            interaction.user.id,
                            inst["session_id"],
                            (inst["floor_id"], inst["coord_x"], inst["coord_y"]),
                        )

                    # rewards
                    cur.execute(
                        """
                        SELECT reward_type, reward_item_id, reward_amount
                          FROM chest_instance_rewards
                         WHERE instance_id=%s
                        """,
                        (self.instance_id,),
                    )
                    rewards_raw = cur.fetchall()
                    _apply_chest_rewards(
                        interaction.user.id,
                        inst["session_id"],
                        rewards_raw,
                    )

                    rewards: List[str] = []
                    for r in rewards_raw:
                        if r["reward_type"] == "gil":
                            rewards.append(f"💰 **{r['reward_amount']}** gil")
                        elif r["reward_item_id"] is None:
                            continue
                        elif r["reward_type"] == "item":
                            name = fetch_item_name(r["reward_item_id"]) or f"Item #{r['reward_item_id']}"
                            rewards.append(f"🧪 ×{r['reward_amount']} {name}")
                        elif r["reward_type"] == "key":
                            name = fetch_item_name(r["reward_item_id"]) or f"Key #{r['reward_item_id']}"
                            rewards.append(f"🗝️ ×{r['reward_amount']} {name}")

                    # rebuild room buttons
                    cur.execute(
                        """
                        SELECT exits, vendor_id, room_type
                          FROM rooms
                         WHERE session_id=%s AND floor_id=%s
                           AND coord_x=%s AND coord_y=%s
                        """,
                        (
                            inst["session_id"],
                            inst["floor_id"],
                            inst["coord_x"],
                            inst["coord_y"],
                        ),
                    )
                    room_row = cur.fetchone() or {}
                    directions = list(json.loads(room_row.get("exits") or "{}").keys())
                    include_shop = room_row.get("vendor_id") is not None
                    vendor_id = room_row.get("vendor_id")

                    emb_mgr = interaction.client.get_cog("EmbedManager")
                    view: Optional[discord.ui.View] = None
                    if emb_mgr:
                        btn_defs = emb_mgr.get_main_menu_buttons(
                            directions=directions,
                            include_shop=include_shop,
                            vendor_id=vendor_id,
                            is_item=False,
                            is_locked=False,
                            has_key=False,
                            is_stair_up=(room_row.get("room_type") == "staircase_up"),
                            is_stair_down=(room_row.get("room_type") == "staircase_down"),
                        )
                        view = discord.ui.View(timeout=None)
                        for label, style, cid, row, *rest in btn_defs:
                            view.add_item(
                                discord.ui.Button(label=label, style=style, custom_id=cid, row=row)
                            )

                    # fetch floor rooms for mini-map
                    floor_rooms = []
                    if gm:
                        conn2 = gm.db_connect()
                        with conn2.cursor(dictionary=True) as cur2:
                            cur2.execute(
                                "SELECT coord_x, coord_y, room_type "
                                "FROM rooms "
                                "WHERE session_id=%s AND floor_id=%s",
                                (inst["session_id"], inst["floor_id"]),
                            )
                            floor_rooms = cur2.fetchall()
                        conn2.close()

                        discovered_here = {
                            (x, y) for (f, x, y) in discovered_3d if f == inst["floor_id"]
                        }
                        neighbours = {
                            (inst["coord_x"] + 1, inst["coord_y"]),
                            (inst["coord_x"] - 1, inst["coord_y"]),
                            (inst["coord_x"], inst["coord_y"] + 1),
                            (inst["coord_x"], inst["coord_y"] - 1),
                        }
                        visible = discovered_here | neighbours
                        local_map = gm._render_local_map(
                            all_rooms=floor_rooms,
                            center=(inst["coord_x"], inst["coord_y"]),
                            discovered=discovered_here,
                            reveal=visible,
                        )
                    else:
                        local_map = ""

                    img = get_room_image(self.instance_id)
                    embed = discord.Embed(
                        title="🎉 Chest Unlocked!",
                        description=(
                            f"```{local_map}```\n"
                            f"{feedback}\nYou found:\n" + "\n".join(rewards)
                        ),
                        color=discord.Color.green(),
                    )
                    if img:
                        embed.set_image(url=f"{img}?t={int(time.time())}")

                    await interaction.message.edit(embed=embed, view=view)
                    return

                # ── FAILURE ────────────────────────────────────────
                if next_wrong >= 2 or next_step > self.MAX_STEPS:
                    cur.execute(
                        """
                        UPDATE treasure_chest_instances
                           SET step=%s, wrong_count=%s, is_broken=1
                         WHERE instance_id=%s
                        """,
                        (next_step, next_wrong, self.instance_id),
                    )
                    conn.commit()

                    # rebuild room buttons
                    cur.execute(
                        """
                        SELECT exits, vendor_id, room_type
                          FROM rooms
                         WHERE session_id=%s AND floor_id=%s
                           AND coord_x=%s AND coord_y=%s
                        """,
                        (
                            inst["session_id"],
                            inst["floor_id"],
                            inst["coord_x"],
                            inst["coord_y"],
                        ),
                    )
                    room_row = cur.fetchone() or {}
                    directions = list(json.loads(room_row.get("exits") or "{}").keys())
                    include_shop = room_row.get("vendor_id") is not None
                    vendor_id = room_row.get("vendor_id")

                    emb_mgr = interaction.client.get_cog("EmbedManager")
                    view: Optional[discord.ui.View] = None
                    if emb_mgr:
                        btn_defs = emb_mgr.get_main_menu_buttons(
                            directions=directions,
                            include_shop=include_shop,
                            vendor_id=vendor_id,
                            is_item=False,
                            is_locked=False,
                            has_key=False,
                            is_stair_up=(room_row.get("room_type") == "staircase_up"),
                            is_stair_down=(room_row.get("room_type") == "staircase_down"),
                        )
                        view = discord.ui.View(timeout=None)
                        for label, style, cid, row, *rest in btn_defs:
                            view.add_item(
                                discord.ui.Button(label=label, style=style, custom_id=cid, row=row)
                            )

                    # fetch floor rooms for mini-map
                    floor_rooms = []
                    if gm:
                        conn3 = gm.db_connect()
                        with conn3.cursor(dictionary=True) as cur3:
                            cur3.execute(
                                "SELECT coord_x, coord_y, room_type "
                                "FROM rooms "
                                "WHERE session_id=%s AND floor_id=%s",
                                (inst["session_id"], inst["floor_id"]),
                            )
                            floor_rooms = cur3.fetchall()
                        conn3.close()

                        discovered_3d = await gm.update_permanent_discovered_room(
                            interaction.user.id,
                            inst["session_id"],
                            (inst["floor_id"], inst["coord_x"], inst["coord_y"])
                        )
                        discovered_here = {
                            (x, y) for (f, x, y) in discovered_3d if f == inst["floor_id"]
                        }
                        neighbours = {
                            (inst["coord_x"] + 1, inst["coord_y"]),
                            (inst["coord_x"] - 1, inst["coord_y"]),
                            (inst["coord_x"], inst["coord_y"] + 1),
                            (inst["coord_x"], inst["coord_y"] - 1),
                        }
                        visible = discovered_here | neighbours
                        local_map = gm._render_local_map(
                            all_rooms=floor_rooms,
                            center=(inst["coord_x"], inst["coord_y"]),
                            discovered=discovered_here,
                            reveal=visible,
                        )
                    else:
                        local_map = ""

                    img = get_room_image(self.instance_id)
                    embed = discord.Embed(
                        title="💥 The lock breaks!",
                        description=(
                            f"```{local_map}```\n"
                            f"{feedback}\nThe mechanism snaps — the chest can’t be opened."
                        ),
                        color=discord.Color.red(),
                    )
                    if img:
                        embed.set_image(url=f"{img}?t={int(time.time())}")

                    await interaction.message.edit(embed=embed, view=view)
                    return

                # ── CONTINUE ───────────────────────────────────────
                new_hint = random.choice(
                    [n for n in range(2, 100) if n != inst["target_number"]]
                )
                cur.execute(
                    """
                    UPDATE treasure_chest_instances
                       SET step=%s,
                           correct_count=%s,
                           wrong_count=%s,
                           hint_value=%s
                     WHERE instance_id=%s
                    """,
                    (
                        next_step,
                        next_correct,
                        next_wrong,
                        new_hint,
                        self.instance_id,
                    ),
                )
                conn.commit()
        finally:
            conn.close()

        img = get_room_image(self.instance_id)
        embed = discord.Embed(
            title="🔒 Chest Lock Challenge",
            description=(
                f"**Step {next_step} / {self.MAX_STEPS} — "
                f"✅ {next_correct} | ❌ {next_wrong}**\n\n"
                f"{feedback}\n"
                f"Is the secret number **higher** or **lower** than **{new_hint}**?"
            ),
            color=discord.Color.gold(),
        )
        if img:
            embed.set_image(url=f"{img}?t={int(time.time())}")

        await interaction.message.edit(embed=embed, view=self)


# ──────────────────────────────────────────────────────────────
#  Back‑compat alias
# ──────────────────────────────────────────────────────────────


class OpenChestView(StartChestUnlockView):
    """Alias kept for Game‑Master’s call‑site."""
    pass


# ──────────────────────────────────────────────────────────────
#  Cog container
# ──────────────────────────────────────────────────────────────


class TreasureChestCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        # expose for other cogs
        self.OpenChestView = OpenChestView
        self.StartChestUnlockView = StartChestUnlockView
        logger.debug("TreasureChest cog initialised.")


async def setup(bot: commands.Bot):
    await bot.add_cog(TreasureChestCog(bot))
    logger.info("TreasureChest cog loaded ✔")
