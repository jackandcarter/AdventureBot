# cogs/dungeon_generator.py
from __future__ import annotations

import asyncio
import functools
import json
import logging
import random
import time
from collections import deque
from typing import Any, Dict, List, Optional, Set, Tuple

import discord
from discord.ext import commands

from models.database import Database

logger = logging.getLogger("DungeonGenerator")
logger.setLevel(logging.DEBUG)


class DungeonGenerator(commands.Cog):
    """
    Procedural dungeon generator with multi-floor mazes, loops, staircases,
    locked/item/boss/shop rooms, treasure-chest instancing and
    per-session vendor instances for shop rooms.
    """

    MIN_LOCK_DISTANCE = 5       # minimum tiles from (0, 0) before a room can be locked
    MIN_STAIR_DISTANCE = 6      # minimum tiles from entry before staircase appears
    DEFAULT_LOOP_CHANCE = 0.15
    DEFAULT_STRAIGHT_BIAS = 0.6
    DEFAULT_STAIR_BIAS = 0.7
    MINIBOSS_PER_FLOOR = 2

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.db = Database()
        logger.debug("DungeonGenerator cog initialised.")

    # ─────────────────────────────────────────────── DB
    def db_connect(self):
        return self.db.get_connection()

    # ─────────────────────────────────────────────── Weighted utilities
    @staticmethod
    def weighted_choice(
        defs: List[Dict[str, Any]], key: str = "spawn_weight"
    ) -> Optional[Dict[str, Any]]:
        total = sum(d.get(key, 0) for d in defs)
        if total <= 0:
            return None
        r, acc = random.uniform(0, total), 0
        for d in defs:
            acc += d.get(key, 0)
            if acc >= r:
                return d
        return defs[-1]

    # ─────────────────────────────────────────────── Fetch helpers
    def fetch_difficulty_settings(self, name: str) -> Optional[Dict[str, Any]]:
        conn = self.db_connect()
        try:
            with conn.cursor(dictionary=True) as cur:
                cur.execute("SELECT * FROM difficulties WHERE name=%s", (name,))
                return cur.fetchone()
        finally:
            conn.close()

    def fetch_floor_rules(self, difficulty: str, floor_num: int) -> List[Dict[str, Any]]:
        conn = self.db_connect()
        try:
            with conn.cursor(dictionary=True) as cur:
                cur.execute(
                    """
                    SELECT room_type, chance, max_per_floor
                      FROM floor_room_rules
                     WHERE difficulty_name=%s
                       AND (floor_number=%s OR floor_number IS NULL)
                    """,
                    (difficulty, floor_num),
                )
                return cur.fetchall()
        finally:
            conn.close()

    # ─────────────────────────────────────────────── Maze helpers
    def _carve_perfect_maze(
        self, w: int, h: int, straight_bias: float = 0.0
    ) -> Dict[Tuple[int, int], Set[Tuple[int, int]]]:
        """Recursive-backtracker maze (optionally biased toward straight runs)."""
        adj: Dict[Tuple[int, int], Set[Tuple[int, int]]] = {
            (x, y): set() for x in range(w) for y in range(h)
        }
        stack: List[Tuple[int, int]] = []
        visited: Set[Tuple[int, int]] = set()
        start = (0, 0)
        visited.add(start)
        stack.append(start)

        while stack:
            x, y = stack[-1]
            neighbors = [
                (nx, ny)
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))
                if 0 <= (nx := x + dx) < w
                and 0 <= (ny := y + dy) < h
                and (nx, ny) not in visited
            ]
            if neighbors:
                nxt = None
                if len(stack) > 1 and random.random() < straight_bias:
                    px, py = stack[-2]
                    dxp, dyp = x - px, y - py
                    straight = [
                        n for n in neighbors if (n[0] - x, n[1] - y) == (dxp, dyp)
                    ]
                    if straight:
                        nxt = random.choice(straight)
                if not nxt:
                    nxt = random.choice(neighbors)
                visited.add(nxt)
                adj[(x, y)].add(nxt)
                adj[nxt].add((x, y))
                stack.append(nxt)
            else:
                stack.pop()
        return adj

    def _add_random_loops(
        self,
        adj: Dict[Tuple[int, int], Set[Tuple[int, int]]],
        loop_chance: float = DEFAULT_LOOP_CHANCE,
    ) -> None:
        """Add extra connections (“loops”) between adjacent cells."""
        cells = list(adj.keys())
        for x, y in cells:
            for dx, dy in ((1, 0), (0, 1)):
                nx, ny = x + dx, y + dy
                if (nx, ny) in adj and (nx, ny) not in adj[(x, y)]:
                    if random.random() < loop_chance:
                        adj[(x, y)].add((nx, ny))
                        adj[(nx, ny)].add((x, y))

    def _bfs_path(
        self,
        adj: Dict[Tuple[int, int], Set[Tuple[int, int]]],
        start: Tuple[int, int],
        end: Tuple[int, int],
    ) -> List[Tuple[int, int]]:
        """Shortest path over adjacency map (BFS)."""
        dq = deque([[start]])
        seen = {start}
        while dq:
            p = dq.popleft()
            node = p[-1]
            if node == end:
                return p
            for nb in adj[node]:
                if nb not in seen:
                    seen.add(nb)
                    dq.append(p + [nb])
        return [start, end]

    # ─────────────────────────────────────────────── Template helpers
    def fetch_random_template(self, rtype: str) -> Optional[Dict[str, Any]]:
        conn = self.db_connect()
        try:
            with conn.cursor(dictionary=True) as cur:
                cur.execute(
                    """
                    SELECT template_id, description, image_url, default_enemy_id
                      FROM room_templates
                     WHERE room_type=%s
                     ORDER BY RAND()
                     LIMIT 1
                    """,
                    (rtype,),
                )
                return cur.fetchone()
        finally:
            conn.close()

    def fetch_random_inner_template(self) -> Optional[int]:
        conn = self.db_connect()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT template_id
                      FROM room_templates
                     WHERE room_type NOT IN ('locked','safe','chest_unlocked','boss','exit','illusion')
                     ORDER BY RAND()
                     LIMIT 1
                    """
                )
                row = cur.fetchone()
                return row[0] if row else None
        finally:
            conn.close()

    # ─────────────────────────────────────────────── Misc helpers
    @staticmethod
    def _choose_far_coordinate(
        width: int,
        height: int,
        min_dist: int,
        edge_bias: float = 0.0,
    ) -> Tuple[int, int]:
        """Choose a coordinate at least `min_dist` Manhattan steps from (0, 0)."""
        all_coords = [
            (x, y)
            for x in range(width)
            for y in range(height)
            if abs(x) + abs(y) >= min_dist
        ]
        if not all_coords:
            return width - 1, height - 1

        outer_coords = [
            (x, y)
            for x, y in all_coords
            if x < width // 3
            or x >= width - width // 3
            or y < height // 3
            or y >= height - height // 3
        ]

        if outer_coords and random.random() < edge_bias:
            return random.choice(outer_coords)
        return random.choice(all_coords)

    # ─────────────────────────────────────────────── Legacy path helper
    def generate_path(
        self,
        sx: int,
        sy: int,
        ex: int,
        ey: int,
        w: int,
        h: int,
        minimum: int,
        max_attempts: int = 2000,
    ) -> List[Tuple[int, int]]:
        """
        Legacy self-avoiding walk from (sx, sy) → (ex, ey). Falls back to BFS.
        """
        for _ in range(max_attempts):
            path: List[Tuple[int, int]] = [(sx, sy)]
            visited: Set[Tuple[int, int]] = {(sx, sy)}
            while len(path) < minimum or path[-1] != (ex, ey):
                x, y = path[-1]
                moves: List[Tuple[int, int]] = []
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < w and 0 <= ny < h and (nx, ny) not in visited:
                        moves.append((nx, ny))
                if not moves:
                    break
                nxt = random.choice(moves)
                visited.add(nxt)
                path.append(nxt)
            else:
                return path
        return self._bfs_path({(sx, sy): {(ex, ey)}}, (sx, sy), (ex, ey))

    # ─────────────────────────────────────────────── Room exits
    @staticmethod
    def get_room_exits(
        x: int,
        y: int,
        adj_map: Dict[Tuple[int, int], Set[Tuple[int, int]]],
    ) -> Dict[str, Tuple[int, int]]:
        exits: Dict[str, Tuple[int, int]] = {}
        for dir_, (dx, dy) in {
            "north": (0, -1),
            "south": (0, 1),
            "east": (1, 0),
            "west": (-1, 0),
        }.items():
            if (x + dx, y + dy) in adj_map.get((x, y), ()):
                exits[dir_] = (x + dx, y + dy)
        return exits

    # ─────────────────────────────────────────────── Treasure helpers
    def fetch_random_treasure_chest(
        self, reward_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        conn = self.db_connect()
        try:
            with conn.cursor(dictionary=True) as cur:
                sql = """
                    SELECT DISTINCT tc.chest_id, tc.spawn_weight
                      FROM treasure_chests tc
                      JOIN chest_def_rewards cd USING (chest_id)
                """
                params: List[Any] = []
                if reward_type:
                    sql += " WHERE cd.reward_type=%s"
                    params.append(reward_type)
                cur.execute(sql, params)
                return cur.fetchall()
        finally:
            conn.close()

    def fetch_treasure_chest_rewards(
        self, chest_id: int
    ) -> List[Dict[str, Any]]:
        conn = self.db_connect()
        try:
            with conn.cursor(dictionary=True) as cur:
                cur.execute(
                    """
                    SELECT reward_type,
                           reward_item_id,
                           reward_key_item_id,
                           amount,
                           spawn_weight
                      FROM chest_def_rewards
                     WHERE chest_id=%s
                    """,
                    (chest_id,),
                )
                return cur.fetchall()
        finally:
            conn.close()

    def create_treasure_chest_instance(
        self, session_id: int, room_id: int, chest_id: int
    ) -> Optional[int]:
        conn = self.db_connect()
        try:
            with conn.cursor(dictionary=True) as cur:
                cur.execute(
                    "SELECT floor_id, coord_x, coord_y FROM rooms WHERE room_id=%s",
                    (room_id,),
                )
                room = cur.fetchone()
                if not room:
                    return None

                target = random.randint(1, 20)
                hint = random.choice([n for n in range(1, 21) if n != target])

                cur.execute(
                    """
                    INSERT INTO treasure_chest_instances
                        (session_id, room_id, chest_id, floor_id,
                         coord_x, coord_y, step, correct_count,
                         wrong_count, target_number, hint_value,
                         is_unlocked, created_at)
                    VALUES (%s,%s,%s,%s,%s,%s,1,0,0,%s,%s,0,NOW())
                    """,
                    (
                        session_id,
                        room_id,
                        chest_id,
                        room["floor_id"],
                        room["coord_x"],
                        room["coord_y"],
                        target,
                        hint,
                    ),
                )
                inst_id = cur.lastrowid

                rewards = self.fetch_treasure_chest_rewards(chest_id)
                choice = self.weighted_choice(rewards, key="spawn_weight")
                if choice:
                    cur.execute(
                        """
                        INSERT INTO chest_instance_rewards
                            (instance_id, reward_type, reward_item_id,
                             reward_key_item_id, reward_amount)
                        VALUES (%s,%s,%s,%s,%s)
                        """,
                        (
                            inst_id,
                            choice["reward_type"],
                            choice.get("reward_item_id", 0),
                            choice.get("reward_key_item_id", 0),
                            choice["amount"],
                        ),
                    )
                conn.commit()
                return inst_id
        finally:
            conn.close()

    # ─────────────────────────────────────────────── Vendor helpers
    def fetch_random_vendor(
        self, used_vendors: Optional[Set[int]] = None
    ) -> Optional[int]:
        conn = self.db_connect()
        try:
            with conn.cursor() as cur:
                if used_vendors:
                    placeholders = ",".join(["%s"] * len(used_vendors))
                    cur.execute(
                        f"""
                        SELECT vendor_id
                          FROM npc_vendors
                         WHERE vendor_id NOT IN ({placeholders})
                         ORDER BY RAND()
                         LIMIT 1
                        """,
                        tuple(used_vendors),
                    )
                    row = cur.fetchone()
                    if row:
                        return row[0]

                cur.execute(
                    "SELECT vendor_id FROM npc_vendors ORDER BY RAND() LIMIT 1"
                )
                row = cur.fetchone()
                return row[0] if row else None
        finally:
            conn.close()

    def fetch_vendor_by_id(self, vendor_id: int) -> Optional[Dict[str, Any]]:
        conn = self.db_connect()
        try:
            with conn.cursor(dictionary=True) as cur:
                cur.execute(
                    "SELECT * FROM npc_vendors WHERE vendor_id=%s",
                    (vendor_id,),
                )
                return cur.fetchone()
        finally:
            conn.close()

    def create_session_vendor_instance(
        self, session_id: int, global_vendor_id: int
    ) -> Optional[int]:
        vendor = self.fetch_vendor_by_id(global_vendor_id)
        if not vendor:
            return None

        conn = self.db_connect()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO session_vendor_instances
                        (session_id, vendor_id, vendor_name, description,
                         image_url, created_at)
                    VALUES (%s,%s,%s,%s,%s,NOW())
                    """,
                    (
                        session_id,
                        global_vendor_id,
                        vendor["vendor_name"],
                        vendor["description"],
                        vendor["image_url"],
                    ),
                )
                session_vendor_id = cur.lastrowid

                cur.execute(
                    """
                    SELECT item_id, price, stock, instance_stock
                      FROM npc_vendor_items
                     WHERE vendor_id=%s
                    """,
                    (global_vendor_id,),
                )
                for item_id, price, stock, instance_stock in cur.fetchall():
                    cur.execute(
                        """
                        INSERT INTO session_vendor_items
                            (session_vendor_id, item_id, price,
                             stock, instance_stock, session_id)
                        VALUES (%s,%s,%s,%s,%s,%s)
                        """,
                        (
                            session_vendor_id,
                            item_id,
                            price,
                            stock,
                            instance_stock,
                            session_id,
                        ),
                    )
            conn.commit()
            return session_vendor_id
        finally:
            conn.close()

    # ─────────────────────────────────────────────── Floor room builder
    def generate_rooms_for_floor(
        self,
        floor_id: int,
        width: int,
        height: int,
        min_rooms: int,
        enemy_chance: float,
        npc_count: int,
        shop_limit: int,
        is_last_floor: bool,
        start_x: int,
        start_y: int,
        end_x: int,
        end_y: int,
        difficulty: str,
        floor_number: int,
        prev_floor_id: Optional[int] = None,
        loop_chance: float = DEFAULT_LOOP_CHANCE,
        straight_bias: float = DEFAULT_STRAIGHT_BIAS,
    ) -> List[Tuple[int, int, int, str, Dict[str, Tuple[int, int]]]]:
        """Return a list of (floor_id,x,y,room_type,exits) tuples."""
        # 1) maze + loops
        adj = self._carve_perfect_maze(width, height, straight_bias)
        self._add_random_loops(adj, loop_chance)

        # 2) BFS distance map
        dist: Dict[Tuple[int, int], int] = {(start_x, start_y): 0}
        dq = deque([(start_x, start_y)])
        while dq:
            cx, cy = dq.popleft()
            for nb in adj[(cx, cy)]:
                if nb not in dist:
                    dist[nb] = dist[(cx, cy)] + 1
                    dq.append(nb)

        # 3) guaranteed path start→exit
        path = self._bfs_path(adj, (start_x, start_y), (end_x, end_y))
        interior = path[1:-1]

        # 4) boss/exit coordinates
        boss_coord = path[-2] if is_last_floor and len(path) >= 2 else None
        exit_coord = path[-1] if is_last_floor else None

        # 5) shops
        shops_needed = min(shop_limit, len(interior))
        shop_positions: List[Tuple[int, int]] = []
        if shops_needed:
            sorted_by_dist = sorted(interior, key=lambda c: dist.get(c, 0))
            n = len(sorted_by_dist)
            segment = n / (shops_needed + 1)
            half_seg = segment / 2
            used: Set[Tuple[int, int]] = set()
            for i in range(shops_needed):
                base = (i + 1) * segment
                idx = int(
                    min(max(base + random.uniform(-half_seg, half_seg), 0), n - 1)
                )
                coord = sorted_by_dist[idx]
                if coord in used:
                    for offset in range(1, n):
                        cand = sorted_by_dist[(idx + offset) % n]
                        if cand not in used:
                            coord = cand
                            break
                shop_positions.append(coord)
                used.add(coord)

        # 6) floor rules table
        rules = self.fetch_floor_rules(difficulty, floor_number)
        remaining = {r["room_type"]: r["max_per_floor"] for r in rules}
        weights = {r["room_type"]: r["chance"] for r in rules}

        def choose_type(
            exclude_locked=False, exclude_item=False, exclude_shop=False
        ) -> str:
            avail = [
                rt
                for rt, cap in remaining.items()
                if cap > 0
                and rt not in ("staircase_up", "staircase_down")
                and not (exclude_locked and rt == "locked")
                and not (exclude_item and rt == "item")
                and not (exclude_shop and rt == "shop")
            ]
            if not avail:
                return "monster" if random.random() < enemy_chance else "safe"
            choice_rt = random.choices(avail, weights=[weights[a] for a in avail])[0]
            remaining[choice_rt] -= 1
            if choice_rt in ("trap", "illusion") and not self.fetch_random_template(
                choice_rt
            ):
                return "monster" if random.random() < enemy_chance else "safe"
            return choice_rt

        # 7) build room list
        out: List[Tuple[int, int, int, str, Dict[str, Tuple[int, int]]]] = []
        room_types: Dict[Tuple[int, int], str] = {}
        for y in range(height):
            for x in range(width):
                coord = (x, y)
                if coord == boss_coord:
                    rtype = "boss"
                elif coord == exit_coord:
                    rtype = "exit"
                elif coord == (start_x, start_y):
                    rtype = "safe" if floor_number == 1 else "staircase_down"
                elif coord in shop_positions:
                    rtype = "shop"
                else:
                    rtype = choose_type()

                # distance & adjacency safety
                if rtype == "locked" and dist.get(coord, 0) < self.MIN_LOCK_DISTANCE:
                    remaining["locked"] += 1
                    rtype = choose_type(exclude_locked=True)
                if rtype in ("locked", "item") and coord not in path:
                    remaining[rtype] += 1
                    rtype = "monster" if random.random() < enemy_chance else "safe"

                if rtype in ("shop", "item"):
                    neighbors = [
                        (x + dx, y + dy)
                        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))
                        if 0 <= x + dx < width and 0 <= y + dy < height
                    ]
                    if any(room_types.get(nb) == rtype for nb in neighbors):
                        remaining[rtype] += 1
                        if rtype == "shop":
                            rtype = choose_type(exclude_shop=True)
                        else:
                            rtype = choose_type(exclude_item=True)

                exits = self.get_room_exits(x, y, adj)
                room_types[coord] = rtype
                out.append((floor_id, x, y, rtype, exits))

        return out

    # ─────────────────────────────────────────────── Persist state
    def save_dungeon_to_session(
        self, session_id: int, data: Dict[str, Any]
    ) -> None:
        conn = self.db_connect()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE sessions SET game_state=%s WHERE session_id=%s",
                    (json.dumps(data), session_id),
                )
                conn.commit()
        finally:
            conn.close()

    # ─────────────────────────────────────────────── First-floor generator
    async def generate_dungeon_for_session(
        self, ctx: commands.Context, session_id: int, difficulty_name: str
    ) -> Optional[Dict[str, Any]]:
        settings = self.fetch_difficulty_settings(difficulty_name)
        if not settings:
            await ctx.send("❌ Difficulty settings not found.", delete_after=10)
            return None

        width = settings["width"]
        height = settings["height"]
        min_rooms = settings["min_rooms"]
        min_floors = settings["min_floors"]
        max_floors = settings["max_floors"]
        enemy_chance = settings["enemy_chance"]
        npc_count = settings["npc_count"]
        shop_limit = settings.get("shops_per_floor", npc_count)

        loop_chance = settings.get("loop_chance", self.DEFAULT_LOOP_CHANCE)
        straight_bias = settings.get("straight_bias", self.DEFAULT_STRAIGHT_BIAS)
        stair_bias = settings.get("stair_edge_bias", self.DEFAULT_STAIR_BIAS)

        basement_chance = settings.get("basement_chance", 0.0)
        basement_min_rooms = settings.get("basement_min_rooms", 0)
        basement_max_rooms = settings.get("basement_max_rooms", 0)
        include_basement = random.random() < basement_chance

        total_floors = random.randint(min_floors, max_floors)

        conn = self.db_connect()
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE sessions SET total_floors=%s WHERE session_id=%s",
                (total_floors + (1 if include_basement else 0), session_id),
            )
            conn.commit()

        entry_x, entry_y = 0, 0
        if total_floors == 1:
            exit_x, exit_y, is_goal = width - 1, height - 1, True
        else:
            exit_x, exit_y = self._choose_far_coordinate(
                width, height, self.MIN_STAIR_DISTANCE, stair_bias
            )
            is_goal = False

        loop = asyncio.get_running_loop()
        used_vendors: Set[int] = set()

        # ── Basement (optional) ─────────────────────
        basement_floor_id: Optional[int] = None
        basement_defs: List[Tuple[int, int, int, str, Dict[str, Tuple[int, int]]]] = []
        if include_basement:
            main_path = self.generate_path(
                entry_x, entry_y, exit_x, exit_y, width, height, min_rooms
            )
            link_x, link_y = random.choice(main_path[1:])

            with conn.cursor() as cur:
                total_b_rooms = random.randint(basement_min_rooms, basement_max_rooms)
                cur.execute(
                    """
                    INSERT INTO floors
                        (session_id, difficulty, total_rooms, floor_number, is_goal_floor)
                    VALUES (%s,%s,%s,0,false)
                    """,
                    (session_id, difficulty_name, total_b_rooms),
                )
                conn.commit()
                basement_floor_id = cur.lastrowid

            basement_defs = await loop.run_in_executor(
                None,
                functools.partial(
                    self.generate_rooms_for_floor,
                    basement_floor_id,
                    width,
                    height,
                    total_b_rooms,
                    enemy_chance,
                    npc_count,
                    shop_limit,
                    False,
                    link_x,
                    link_y,
                    width - 1,
                    height - 1,
                    difficulty_name,
                    0,
                    None,
                    loop_chance,
                    straight_bias,
                ),
            )

            # insert basement rooms
            item_rooms: List[int] = []
            locked_count = 0
            for _, x, y, rtype, exits in basement_defs:
                inner_id = None
                vendor_id = None
                def_en = None

                if rtype == "locked":
                    inner_id = self.fetch_random_inner_template()
                    locked_count += 1

                if rtype == "shop":
                    gvid = self.fetch_random_vendor(used_vendors)
                    if gvid:
                        vendor_id = self.create_session_vendor_instance(
                            session_id, gvid
                        )
                        used_vendors.add(gvid)

                tmpl = self.fetch_random_template(rtype) or {}
                desc = tmpl.get("description", "A mysterious room…")
                img = tmpl.get("image_url")
                if def_en is None:
                    def_en = tmpl.get("default_enemy_id")

                with conn.cursor() as cur:
                    cur.execute(
                        """
                        INSERT INTO rooms
                            (session_id,floor_id,coord_x,coord_y,description,
                             room_type,image_url,default_enemy_id,exits,
                             vendor_id,inner_template_id)
                        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                        """,
                        (
                            session_id,
                            basement_floor_id,
                            x,
                            y,
                            desc,
                            rtype,
                            img,
                            def_en,
                            json.dumps(exits),
                            vendor_id,
                            inner_id,
                        ),
                    )
                    if rtype == "item":
                        item_rooms.append(cur.lastrowid)
            conn.commit()

            # chests in basement
            key_defs = self.fetch_random_treasure_chest("key")
            all_defs = self.fetch_random_treasure_chest()
            for rid in item_rooms[:locked_count]:
                chest = self.weighted_choice(key_defs)
                if chest:
                    self.create_treasure_chest_instance(
                        session_id, rid, chest["chest_id"]
                    )
            for rid in item_rooms[locked_count:]:
                chest = self.weighted_choice(all_defs)
                if chest:
                    self.create_treasure_chest_instance(
                        session_id, rid, chest["chest_id"]
                    )
            conn.commit()

        # ── First floor ─────────────────────────────
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO floors
                    (session_id, difficulty, total_rooms, floor_number, is_goal_floor)
                VALUES (%s,%s,%s,1,%s)
                """,
                (session_id, difficulty_name, min_rooms, is_goal),
            )
            conn.commit()
            first_floor_id = cur.lastrowid

        # miniboss pool (for first & later floors)
        with conn.cursor(dictionary=True) as cur:
            cur.execute(
                """
                SELECT template_id, default_enemy_id
                  FROM room_templates
                 WHERE room_type='miniboss'
                """
            )
            miniboss_pool: List[Dict[str, Any]] = cur.fetchall()
        random.shuffle(miniboss_pool)
        mb_index = 0

        first_defs = await loop.run_in_executor(
            None,
            functools.partial(
                self.generate_rooms_for_floor,
                first_floor_id,
                width,
                height,
                min_rooms,
                enemy_chance,
                npc_count,
                shop_limit,
                is_goal,
                entry_x,
                entry_y,
                exit_x,
                exit_y,
                difficulty_name,
                1,
                None,
                loop_chance,
                straight_bias,
            ),
        )

        # link from surface to basement (locked staircase)
        locked_coord = (link_x, link_y) if include_basement else None
        staircase_down_tpl: Optional[int] = None
        if locked_coord:
            with conn.cursor(dictionary=True) as cur:
                cur.execute(
                    """
                    SELECT template_id
                      FROM room_templates
                     WHERE room_type='staircase_down'
                     LIMIT 1
                    """
                )
                row = cur.fetchone()
                staircase_down_tpl = row["template_id"] if row else None

        # insert first-floor rooms
        item_rooms: List[int] = []
        locked_count = 0
        for _, x, y, rtype, exits in first_defs:
            inner_id = None
            stair_down_floor_id = None
            stair_down_x = None
            stair_down_y = None
            vendor_id = None
            def_en = None

            if locked_coord and (x, y) == locked_coord:
                # this is the locked entrance to basement
                rtype = "locked"
                inner_id = staircase_down_tpl
                stair_down_floor_id = basement_floor_id
                stair_down_x, stair_down_y = x, y
            elif rtype == "locked":
                if mb_index < len(miniboss_pool):
                    inner_id = miniboss_pool[mb_index]["template_id"]
                    def_en = miniboss_pool[mb_index]["default_enemy_id"]
                    mb_index += 1
                else:
                    inner_id = self.fetch_random_inner_template()
                locked_count += 1

            if rtype == "shop":
                gvid = self.fetch_random_vendor(used_vendors)
                if gvid:
                    vendor_id = self.create_session_vendor_instance(
                        session_id, gvid
                    )
                    used_vendors.add(gvid)

            tmpl = self.fetch_random_template(rtype) or {}
            desc = tmpl.get("description", "A mysterious room…")
            img = tmpl.get("image_url")

            if rtype == "boss":
                role = "boss"
            elif rtype == "monster":
                role = "normal"
            else:
                role = None

            if role:
                with conn.cursor(dictionary=True) as cur2:
                    cur2.execute(
                        """
                        SELECT enemy_id
                          FROM enemies
                         WHERE role=%s
                         ORDER BY RAND()
                         LIMIT 1
                        """,
                        (role,),
                    )
                    row2 = cur2.fetchone()
                def_en = row2["enemy_id"] if row2 else def_en

            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO rooms
                        (session_id,floor_id,coord_x,coord_y,description,
                         room_type,image_url,default_enemy_id,exits,
                         vendor_id,inner_template_id,
                         stair_down_floor_id,stair_down_x,stair_down_y)
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                    """,
                    (
                        session_id,
                        first_floor_id,
                        x,
                        y,
                        desc,
                        rtype,
                        img,
                        def_en,
                        json.dumps(exits),
                        vendor_id,
                        inner_id,
                        stair_down_floor_id,
                        stair_down_x,
                        stair_down_y,
                    ),
                )
                rid = cur.lastrowid
                if rtype == "item":
                    item_rooms.append(rid)
        conn.commit()

        # staircase-up (inside basement) & staircase-down (surface) link
        if include_basement:
            with conn.cursor() as cur:
                # basement → up
                cur.execute(
                    """
                    UPDATE rooms
                       SET room_type='staircase_up',
                           stair_up_floor_id=%s,
                           stair_up_x=%s,
                           stair_up_y=%s
                     WHERE session_id=%s
                       AND floor_id=%s
                       AND coord_x=%s
                       AND coord_y=%s
                    """,
                    (
                        first_floor_id,
                        link_x,
                        link_y,
                        session_id,
                        basement_floor_id,
                        link_x,
                        link_y,
                    ),
                )
                # surface → down
                cur.execute(
                    """
                    UPDATE rooms
                       SET stair_down_floor_id=%s,
                           stair_down_x=%s,
                           stair_down_y=%s
                     WHERE session_id=%s
                       AND floor_id=%s
                       AND coord_x=%s
                       AND coord_y=%s
                    """,
                    (
                        basement_floor_id,
                        link_x,
                        link_y,
                        session_id,
                        first_floor_id,
                        link_x,
                        link_y,
                    ),
                )
                # decorate staircase_up image/description
                cur.execute(
                    """
                    UPDATE rooms AS r
                    JOIN room_templates AS t
                      ON t.room_type = 'staircase_up'
                       SET r.image_url        = t.image_url,
                           r.description      = t.description,
                           r.inner_template_id= t.template_id
                     WHERE r.session_id=%s
                       AND r.floor_id=%s
                       AND r.coord_x =%s
                       AND r.coord_y =%s
                    """,
                    (session_id, basement_floor_id, link_x, link_y),
                )
            conn.commit()

        # chests on first floor
        key_defs = self.fetch_random_treasure_chest("key")
        all_defs = self.fetch_random_treasure_chest()
        for rid in item_rooms[:locked_count]:
            chest = self.weighted_choice(key_defs)
            if chest:
                self.create_treasure_chest_instance(
                    session_id, rid, chest["chest_id"]
                )
        for rid in item_rooms[locked_count:]:
            chest = self.weighted_choice(all_defs)
            if chest:
                self.create_treasure_chest_instance(
                    session_id, rid, chest["chest_id"]
                )
        conn.commit()

        # ── Build save-blob & persist ───────────────
        blob: Dict[str, Any] = {
            "difficulty": difficulty_name,
            "total_floors": total_floors + (1 if include_basement else 0),
            "rooms": [],
            "width": width,
            "height": height,
        }
        for defs in (basement_defs if include_basement else []):
            _, x, y, rtype, exits = defs
            blob["rooms"].append(
                {
                    "floor_id": basement_floor_id,
                    "x": x,
                    "y": y,
                    "type": rtype,
                    "exits": exits,
                }
            )
        for _, x, y, rtype, exits in first_defs:
            blob["rooms"].append(
                {
                    "floor_id": first_floor_id,
                    "x": x,
                    "y": y,
                    "type": rtype,
                    "exits": exits,
                }
            )
        self.save_dungeon_to_session(session_id, blob)

        # ── Remaining floors (async) ────────────────
        if total_floors > 1:
            await self._generate_remaining_floors(
                session_id,
                difficulty_name,
                width,
                height,
                min_rooms,
                enemy_chance,
                npc_count,
                shop_limit,
                total_floors,
                exit_x,
                exit_y,
                first_floor_id,
                loop_chance,
                straight_bias,
                stair_bias,
                used_vendors,
            )

        return blob

    # ─────────────────────────────────────────────── Later floors
    async def _generate_remaining_floors(
        self,
        session_id: int,
        difficulty_name: str,
        width: int,
        height: int,
        min_rooms: int,
        enemy_chance: float,
        npc_count: int,
        shop_limit: int,
        total_floors: int,
        prev_x: int,
        prev_y: int,
        prev_floor_id: int,
        loop_chance: float,
        straight_bias: float,
        stair_bias: float,
        used_vendors: Set[int],
    ) -> None:
        conn = self.db_connect()
        try:
            with conn.cursor(dictionary=True) as cur:
                cur.execute(
                    "SELECT game_state FROM sessions WHERE session_id=%s",
                    (session_id,),
                )
                row = cur.fetchone()
            blob = json.loads(row["game_state"] or "{}")

            loop = asyncio.get_running_loop()
            current_entry = (prev_x, prev_y)

            for floor_number in range(2, total_floors + 1):
                is_goal = floor_number == total_floors
                exit_x, exit_y = self._choose_far_coordinate(
                    width, height, self.MIN_STAIR_DISTANCE, stair_bias
                )
                while (
                    abs(exit_x - current_entry[0]) + abs(exit_y - current_entry[1])
                    < self.MIN_STAIR_DISTANCE
                ):
                    exit_x, exit_y = self._choose_far_coordinate(
                        width, height, self.MIN_STAIR_DISTANCE, stair_bias
                    )

                with conn.cursor() as cur:
                    cur.execute(
                        """
                        INSERT INTO floors
                            (session_id,difficulty,total_rooms,floor_number,is_goal_floor)
                        VALUES (%s,%s,%s,%s,%s)
                        """,
                        (
                            session_id,
                            difficulty_name,
                            min_rooms,
                            floor_number,
                            is_goal,
                        ),
                    )
                    conn.commit()
                    floor_id = cur.lastrowid

                defs = await loop.run_in_executor(
                    None,
                    functools.partial(
                        self.generate_rooms_for_floor,
                        floor_id,
                        width,
                        height,
                        min_rooms,
                        enemy_chance,
                        npc_count,
                        shop_limit,
                        is_goal,
                        current_entry[0],
                        current_entry[1],
                        exit_x,
                        exit_y,
                        difficulty_name,
                        floor_number,
                        prev_floor_id,
                        loop_chance * (1 + 0.05 * (floor_number - 1)),
                        straight_bias,
                    ),
                )

                item_rooms: List[int] = []
                locked_count = 0

                for _, x, y, rtype, exits in defs:
                    inner_id = None
                    vendor_id = None
                    def_en = None

                    if rtype == "locked":
                        inner_id = self.fetch_random_inner_template()
                        locked_count += 1

                    if rtype == "shop":
                        gvid = self.fetch_random_vendor(used_vendors)
                        if gvid:
                            vendor_id = self.create_session_vendor_instance(
                                session_id, gvid
                            )
                            used_vendors.add(gvid)

                    tmpl = self.fetch_random_template(rtype) or {}
                    desc = tmpl.get("description") or "A mysterious room..."
                    img = tmpl.get("image_url")

                    if rtype in ("miniboss", "boss", "monster"):
                        role = (
                            "miniboss"
                            if rtype == "miniboss"
                            else ("boss" if rtype == "boss" else "normal")
                        )
                        with conn.cursor(dictionary=True) as cur2:
                            cur2.execute(
                                """
                                SELECT enemy_id
                                  FROM enemies
                                 WHERE role=%s
                                 ORDER BY RAND()
                                 LIMIT 1
                                """,
                                (role,),
                            )
                            row2 = cur2.fetchone()
                        def_en = row2["enemy_id"] if row2 else None

                    with conn.cursor() as cur:
                        cur.execute(
                            """
                            INSERT INTO rooms
                                (session_id,floor_id,coord_x,coord_y,description,
                                 room_type,image_url,default_enemy_id,exits,
                                 vendor_id,inner_template_id)
                            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                            """,
                            (
                                session_id,
                                floor_id,
                                x,
                                y,
                                desc,
                                rtype,
                                img,
                                def_en,
                                json.dumps(exits),
                                vendor_id,
                                inner_id,
                            ),
                        )
                        room_id = cur.lastrowid
                        if rtype == "item":
                            item_rooms.append(room_id)
                conn.commit()

                # chests
                key_defs = self.fetch_random_treasure_chest("key")
                all_defs = self.fetch_random_treasure_chest()
                for rid in item_rooms[:locked_count]:
                    chest = self.weighted_choice(key_defs)
                    if chest:
                        self.create_treasure_chest_instance(
                            session_id, rid, chest["chest_id"]
                        )
                for rid in item_rooms[locked_count:]:
                    chest = self.weighted_choice(all_defs)
                    if chest:
                        self.create_treasure_chest_instance(
                            session_id, rid, chest["chest_id"]
                        )
                conn.commit()

                for _, x, y, rtype, exits in defs:
                    blob.setdefault("rooms", []).append(
                        {
                            "floor_id": floor_id,
                            "x": x,
                            "y": y,
                            "type": rtype,
                            "exits": exits,
                        }
                    )

                # link stairs between this and previous floor
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        UPDATE rooms
                           SET room_type='staircase_up',
                               stair_up_floor_id=%s,
                               stair_up_x=%s,
                               stair_up_y=%s
                         WHERE session_id=%s
                           AND floor_id=%s
                           AND coord_x=%s
                           AND coord_y=%s
                        """,
                        (
                            floor_id,
                            current_entry[0],
                            current_entry[1],
                            session_id,
                            prev_floor_id,
                            current_entry[0],
                            current_entry[1],
                        ),
                    )
                    cur.execute(
                        """
                        UPDATE rooms
                           SET stair_down_floor_id=%s,
                               stair_down_x=%s,
                               stair_down_y=%s
                         WHERE session_id=%s
                           AND floor_id=%s
                           AND coord_x=%s
                           AND coord_y=%s
                        """,
                        (
                            prev_floor_id,
                            current_entry[0],
                            current_entry[1],
                            session_id,
                            floor_id,
                            current_entry[0],
                            current_entry[1],
                        ),
                    )
                conn.commit()

                current_entry = (exit_x, exit_y)
                prev_floor_id = floor_id

            self.save_dungeon_to_session(session_id, blob)
        finally:
            conn.close()

    # ─────────────────────────────────────────────── Admin command
    @commands.command(name="gendungeon")
    @commands.has_permissions(administrator=True)
    async def cmd_generate_dungeon(
        self, ctx: commands.Context, difficulty_name: str
    ):
        """Admin command to generate a dungeon for the current session."""
        conn = self.db.get_connection()
        try:
            with conn.cursor(dictionary=True) as cur:
                cur.execute(
                    """
                    SELECT session_id
                      FROM sessions
                     WHERE guild_id=%s
                     ORDER BY created_at DESC
                     LIMIT 1
                    """,
                    (ctx.guild.id,),
                )
                row = cur.fetchone()
                if not row:
                    return await ctx.send(
                        "❌ No active session found.", delete_after=10
                    )
                session_id = row["session_id"]
        finally:
            conn.close()

        result = await self.generate_dungeon_for_session(
            ctx, session_id, difficulty_name
        )
        if result:
            await ctx.send(
                f"🧱 Dungeon generation started for session **{session_id}** "
                f"at difficulty **{difficulty_name}**! 🎯 First floor ready!"
            )
        else:
            await ctx.send(
                "❌ Failed to generate dungeon.", delete_after=10
            )


async def setup(bot: commands.Bot):
    await bot.add_cog(DungeonGenerator(bot))
    logger.info("DungeonGenerator cog loaded ✔")
