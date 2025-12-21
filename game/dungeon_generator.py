# cogs/dungeon_generator.py

from __future__ import annotations
import time
import asyncio
import functools
import json
import logging
import random
from collections import deque
from typing import Any, Dict, List, Optional, Tuple, Set

import discord
from discord.ext import commands

from models.database import Database

logger = logging.getLogger("DungeonGenerator")
logger.setLevel(logging.DEBUG)


class DungeonGenerator(commands.Cog):
    """
    Procedural dungeon generator with multi-floor mazes, loops, staircases,
    locked/item/boss/shop rooms, treasure chest instancing and
    per-session vendor instances for shop rooms.
    """

    MIN_LOCK_DISTANCE = 5    # minimum tiles from (0,0) before a room can be locked
    MIN_STAIR_DISTANCE = 6   # minimum tiles from entry before staircase appears
    MIN_SPECIAL_DISTANCE = 2  # minimum spacing between special/unique rooms
    SPECIAL_ROOM_TYPES = {"shop", "cloister", "illusion", "item", "locked"}

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.db = Database()
        logger.debug("DungeonGenerator cog initialised.")

    def db_connect(self):
        return self.db.get_connection()

    # ─────────────────────────────────────────────── Weighted utilities
    @staticmethod
    def weighted_choice(defs: List[Dict[str, Any]], key: str = "spawn_weight") -> Optional[Dict[str, Any]]:
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
    def _carve_perfect_maze(self, w: int, h: int) -> Dict[Tuple[int, int], Set[Tuple[int, int]]]:
        """
        Carve a perfect maze over the full w×h grid using recursive backtracker.
        Returns an adjacency map.
        """
        adj: Dict[Tuple[int, int], Set[Tuple[int, int]]] = {
            (x, y): set() for x in range(w) for y in range(h)
        }
        stack: List[Tuple[int,int]] = []
        visited: Set[Tuple[int,int]] = set()
        start = (0, 0)
        visited.add(start)
        stack.append(start)

        while stack:
            x, y = stack[-1]
            neighbors = [
                (nx, ny)
                for dx, dy in ((1,0),(-1,0),(0,1),(0,-1))
                if 0 <= (nx := x + dx) < w
                and 0 <= (ny := y + dy) < h
                and (nx, ny) not in visited
            ]
            if neighbors:
                nxt = random.choice(neighbors)
                visited.add(nxt)
                adj[(x, y)].add(nxt)
                adj[nxt].add((x, y))
                stack.append(nxt)
            else:
                stack.pop()
        return adj

    def _add_random_loops(self,
                          adj: Dict[Tuple[int, int], Set[Tuple[int, int]]],
                          loop_chance: float = 0.08) -> None:
        """
        Add extra connections (“loops”) between adjacent cells with given probability.
        """
        cells = list(adj.keys())
        for x, y in cells:
            for dx, dy in ((1,0),(0,1)):
                nx, ny = x + dx, y + dy
                if (nx, ny) in adj and (nx, ny) not in adj[(x, y)]:
                    if random.random() < loop_chance:
                        adj[(x, y)].add((nx, ny))
                        adj[(nx, ny)].add((x, y))

    def _bfs_path(
        self,
        adj: Dict[Tuple[int, int], Set[Tuple[int, int]]],
        start: Tuple[int,int],
        end: Tuple[int,int]
    ) -> List[Tuple[int,int]]:
        """
        BFS shortest path over the adjacency map.
        """
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

    # ─────────────────────────────────────────────── Fetch template helpers
    def fetch_random_template(
        self,
        rtype: str,
        exclude_eidolon_ids: Optional[Set[int]] = None,
    ) -> Optional[Dict[str, Any]]:
        conn = self.db_connect()
        try:
            with conn.cursor(dictionary=True) as cur:
                if rtype == "cloister" and exclude_eidolon_ids:
                    placeholders = ", ".join(["%s"] * len(exclude_eidolon_ids))
                    cur.execute(
                        f"""
                        SELECT template_id, description, image_url, default_enemy_id, eidolon_id, attune_level
                          FROM room_templates
                         WHERE room_type=%s
                           AND eidolon_id NOT IN ({placeholders})
                         ORDER BY RAND()
                         LIMIT 1
                        """,
                        (rtype, *exclude_eidolon_ids),
                    )
                    row = cur.fetchone()
                    if row:
                        return row
                cur.execute(
                    """
                    SELECT template_id, description, image_url, default_enemy_id, eidolon_id, attune_level
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
                     WHERE room_type NOT IN ('locked','safe','entrance','chest_unlocked','boss','exit','illusion','cloister')
                     ORDER BY RAND()
                     LIMIT 1
                    """
                )
                row = cur.fetchone()
                return row[0] if row else None
        finally:
            conn.close()

    # ─────────────────────────────────────────────── Legacy path helpers
    @staticmethod
    def _choose_far_coordinate(width: int, height: int, min_dist: int) -> Tuple[int, int]:
        """Choose a (x, y) coordinate ≥ min_dist manhattan distance from (0,0)."""
        while True:
            x, y = random.randint(0, width-1), random.randint(0, height-1)
            if abs(x) + abs(y) >= min_dist:
                return x, y

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
        Legacy self-avoiding walk from (sx, sy) → (ex, ey), used for basement linking
        if needed. Falls back to BFS shortest path.
        """
        for _ in range(max_attempts):
            path: List[Tuple[int, int]] = [(sx, sy)]
            visited: Set[Tuple[int, int]] = {(sx, sy)}
            while len(path) < minimum or path[-1] != (ex, ey):
                x, y = path[-1]
                moves: List[Tuple[int, int]] = []
                for dx, dy in ((1,0),(-1,0),(0,1),(0,-1)):
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
        return self._bfs_path({(sx,sy):{(ex,ey)}}, (sx,sy), (ex,ey))  # fallback

    # ─────────────────────────────────────────────── Room exits using adjacency
    @staticmethod
    def get_room_exits(x: int,
                       y: int,
                       adj_map: Dict[Tuple[int,int], Set[Tuple[int,int]]]
                       ) -> Dict[str, Tuple[int, int]]:
        exits: Dict[str, Tuple[int, int]] = {}
        for dir, (dx, dy) in {
            "north": (0, -1),
            "south": (0, 1),
            "east":  (1, 0),
            "west":  (-1,0),
        }.items():
            if (x+dx, y+dy) in adj_map.get((x, y), ()):
                exits[dir] = (x+dx, y+dy)
        return exits

    # ─────────────────────────────────────────────── Treasure chest helpers
    def fetch_random_treasure_chest(self, reward_type: Optional[str] = None) -> List[Dict[str, Any]]:
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

    def fetch_treasure_chest_rewards(self, chest_id: int) -> List[Dict[str, Any]]:
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

    def create_treasure_chest_instance(self, session_id: int, room_id: int, chest_id: int) -> Optional[int]:
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
    def fetch_random_vendor(self) -> Optional[int]:
        conn = self.db_connect()
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT vendor_id FROM npc_vendors ORDER BY RAND() LIMIT 1")
                row = cur.fetchone()
                return row[0] if row else None
        finally:
            conn.close()

    def fetch_vendor_by_id(self, vendor_id: int) -> Optional[Dict[str, Any]]:
        conn = self.db_connect()
        try:
            with conn.cursor(dictionary=True) as cur:
                cur.execute("SELECT * FROM npc_vendors WHERE vendor_id=%s", (vendor_id,))
                return cur.fetchone()
        finally:
            conn.close()

    def create_session_vendor_instance(self, session_id: int, global_vendor_id: int) -> Optional[int]:
        vendor = self.fetch_vendor_by_id(global_vendor_id)
        if not vendor:
            return None

        conn = self.db_connect()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO session_vendor_instances
                        (session_id, vendor_id, vendor_name, description, image_url, created_at)
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
                    "SELECT item_id, price, stock, instance_stock FROM npc_vendor_items WHERE vendor_id=%s",
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
                        (session_vendor_id, item_id, price, stock, instance_stock, session_id),
                    )
            conn.commit()
            return session_vendor_id
        finally:
            conn.close()

    # ─────────────────────────────────────────────── Room generation helpers
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
    ) -> List[Tuple[int, int, int, str, Dict[str, Tuple[int, int]]]]:
        # 1) carve a full perfect maze + loops
        adj = self._carve_perfect_maze(width, height)
        self._add_random_loops(adj)

        # 2) compute distance-from-entry for lock/item rules
        dist: Dict[Tuple[int,int], int] = {(start_x, start_y): 0}
        dq = deque([(start_x, start_y)])
        while dq:
            cx, cy = dq.popleft()
            for nb in adj[(cx, cy)]:
                if nb not in dist:
                    dist[nb] = dist[(cx, cy)] + 1
                    dq.append(nb)

        # 3) shortest path along maze from start to exit
        path = self._bfs_path(adj, (start_x, start_y), (end_x, end_y))
        interior = path[1:-1]

        # 4) determine boss/exit coords
        boss_coord = path[-2] if is_last_floor and len(path) >= 2 else None
        exit_coord = path[-1] if is_last_floor else None

        # 5) select shop positions by distance-percentile, with jitter & dedupe
        shops_needed = min(shop_limit, len(interior))
        shop_positions: List[Tuple[int,int]] = []
        if shops_needed:
            sorted_by_dist = sorted(interior, key=lambda coord: dist.get(coord, 0))
            n = len(sorted_by_dist)
            used: Set[Tuple[int,int]] = set()
            # width of one “segment” for jitter calculation
            segment = n / (shops_needed + 1)
            half_seg = segment / 2

            for i in range(shops_needed):
                # base floating index at the (i+1)/(shops_needed+1) percentile
                base = (i + 1) * segment

                # optional jitter in ±half‑segment
                jitter = random.uniform(-half_seg, half_seg)
                raw_idx = base + jitter

                # clamp and cast to int
                idx = int(min(max(raw_idx, 0), n - 1))

                coord = sorted_by_dist[idx]

                # if duplicate, scan forward for the nearest unused
                if coord in used:
                    for offset in range(1, n):
                        cand = sorted_by_dist[(idx + offset) % n]
                        if cand not in used:
                            coord = cand
                            break

                shop_positions.append(coord)
                used.add(coord)

        # 6) floor rules
        rules     = self.fetch_floor_rules(difficulty, floor_number)
        remaining = {r["room_type"]: r["max_per_floor"] for r in rules}
        weights   = {r["room_type"]: r["chance"]      for r in rules}

        def choose_type(
            exclude_locked: bool = False,
            exclude_item: bool = False,
            exclude_special: bool = False,
        ) -> str:
            avail = [
                rt for rt, cap in remaining.items()
                if cap > 0
                and rt not in ("staircase_up","staircase_down")
                and rt != "trap"
                and not (exclude_locked and rt == "locked")
                and not (exclude_item and rt == "item")
                and not (exclude_special and rt in self.SPECIAL_ROOM_TYPES)
            ]
            if not avail:
                return "monster" if random.random() < enemy_chance else "safe"
            choice_ = random.choices(avail, weights=[weights[a] for a in avail])[0]
            remaining[choice_] -= 1
            if choice_ == "illusion" and not self.fetch_random_template(choice_):
                return "monster" if random.random() < enemy_chance else "safe"
            return choice_

        # 7) build rooms
        out: List[Tuple[int,int,int,str,Dict[str,Tuple[int,int]]]] = []
        special_coords: List[Tuple[int, int]] = []

        def is_special_too_close(coord: Tuple[int, int]) -> bool:
            for sx, sy in special_coords:
                if max(abs(coord[0] - sx), abs(coord[1] - sy)) <= self.MIN_SPECIAL_DISTANCE:
                    return True
            return False

        for y in range(height):
            for x in range(width):
                coord = (x, y)
                chosen_from_rules = False
                if coord == boss_coord:
                    rtype = "boss"
                elif coord == exit_coord:
                    rtype = "exit"
                elif coord == (start_x, start_y):
                    rtype = "entrance" if floor_number == 1 else "staircase_down"
                elif coord in shop_positions:
                    rtype = "shop"
                else:
                    rtype = choose_type()
                    chosen_from_rules = True

                # lock/item safety
                if rtype == "locked" and dist.get(coord,0) < self.MIN_LOCK_DISTANCE:
                    remaining["locked"] += 1
                    rtype = choose_type(exclude_locked=True)
                    chosen_from_rules = True
                if rtype in ("locked","item") and coord not in path:
                    remaining[rtype] += 1
                    rtype = "monster" if random.random() < enemy_chance else "safe"

                # spacing for special/unique rooms
                if rtype in self.SPECIAL_ROOM_TYPES and is_special_too_close(coord):
                    if chosen_from_rules:
                        remaining[rtype] += 1
                    rtype = choose_type(exclude_special=True)

                exits = self.get_room_exits(x, y, adj)
                out.append((floor_id, x, y, rtype, exits))
                if rtype in self.SPECIAL_ROOM_TYPES:
                    special_coords.append(coord)

        return out

    # ─────────────────────────────────────────────── Save dungeon state
    def save_dungeon_to_session(self, session_id: int, data: Dict[str, Any]) -> None:
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

    # ─────────────────────────────────────────────── first floor generator
    async def generate_dungeon_for_session(
        self, ctx: commands.Context, session_id: int, difficulty_name: str
    ) -> Optional[Dict[str, Any]]:
        settings = self.fetch_difficulty_settings(difficulty_name)
        if not settings:
            await ctx.send("❌ Difficulty settings not found.", delete_after=10)
            return None

        width        = settings["width"]
        height       = settings["height"]
        min_rooms    = settings["min_rooms"]
        min_floors   = settings["min_floors"]
        max_floors   = settings["max_floors"]
        enemy_chance = settings["enemy_chance"]
        npc_count    = settings["npc_count"]
        shop_limit   = settings.get("shops_per_floor", npc_count)

        basement_chance    = settings.get("basement_chance", 0.0)
        basement_min_rooms = settings.get("basement_min_rooms", 0)
        basement_max_rooms = settings.get("basement_max_rooms", 0)
        include_basement   = random.random() < basement_chance

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
            exit_x, exit_y = self._choose_far_coordinate(width, height, self.MIN_STAIR_DISTANCE)
            is_goal        = False

        basement_floor_id: Optional[int] = None
        used_eidolon_ids: Set[int] = set()
        loop = asyncio.get_running_loop()

        # Optional basement
        if include_basement:
            main_path = self.generate_path(entry_x, entry_y, exit_x, exit_y, width, height, min_rooms)
            link_x, link_y = random.choice(main_path[1:])

            with conn.cursor() as cur:
                total_b_rooms = random.randint(basement_min_rooms, basement_max_rooms)
                cur.execute(
                    "INSERT INTO floors "
                    "(session_id, difficulty, total_rooms, floor_number, is_goal_floor) "
                    "VALUES (%s,%s,%s,0,false)",
                    (session_id, difficulty_name, total_b_rooms),
                )
                conn.commit()
                basement_floor_id = cur.lastrowid

            basement_defs = await loop.run_in_executor(
                None,
                functools.partial(
                    self.generate_rooms_for_floor,
                    basement_floor_id, width, height, total_b_rooms,
                    enemy_chance, npc_count, shop_limit, False,
                    link_x, link_y, width - 1, height - 1,
                    difficulty_name, 0
                )
            )
            for _, x, y, rtype, exits in basement_defs:
                if (x, y) == (link_x, link_y):
                    rtype = "staircase_up"
                vendor_id = None
                if rtype == "shop":
                    gvid = self.fetch_random_vendor()
                    if gvid:
                        vendor_id = self.create_session_vendor_instance(session_id, gvid)
                tmpl = self.fetch_random_template(rtype, used_eidolon_ids) or {}
                desc = tmpl.get("description", "A mysterious room…")
                img  = tmpl.get("image_url")
                def_en = tmpl.get("default_enemy_id")
                eidolon_id = tmpl.get("eidolon_id")
                attune_level = tmpl.get("attune_level")
                if rtype == "cloister" and eidolon_id:
                    used_eidolon_ids.add(eidolon_id)

                with conn.cursor() as cur:
                    cur.execute(
                        "INSERT INTO rooms "
                        "(session_id,floor_id,coord_x,coord_y,description,room_type,"
                        " image_url,default_enemy_id,exits,vendor_id,inner_template_id,"
                        " eidolon_id,attune_level) "
                        "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,NULL,%s,%s)",
                        (
                            session_id,
                            basement_floor_id,
                            x, y,
                            desc,
                            rtype,
                            img,
                            def_en,
                            json.dumps(exits),
                            vendor_id,
                            eidolon_id,
                            attune_level,
                        ),
                    )
            conn.commit()

        # First floor record
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO floors "
                "(session_id, difficulty, total_rooms, floor_number, is_goal_floor) "
                "VALUES (%s,%s,%s,1,%s)",
                (session_id, difficulty_name, min_rooms, is_goal),
            )
            conn.commit()
            first_floor_id = cur.lastrowid

        # build miniboss queue
        with conn.cursor(dictionary=True) as cur:
            cur.execute(
                "SELECT template_id, default_enemy_id FROM room_templates WHERE room_type='miniboss'"
            )
            miniboss_pool = cur.fetchall()
        random.shuffle(miniboss_pool)
        mb_index = 0

        # generate first-floor rooms
        first_defs = await loop.run_in_executor(
            None,
            functools.partial(
                self.generate_rooms_for_floor,
                first_floor_id, width, height, min_rooms,
                enemy_chance, npc_count, shop_limit, is_goal,
                entry_x, entry_y, exit_x, exit_y,
                difficulty_name, 1
            )
        )

        locked_coord = (link_x, link_y) if include_basement else None
        staircase_down_tpl: Optional[int] = None
        if locked_coord:
            with conn.cursor(dictionary=True) as cur:
                cur.execute(
                    "SELECT template_id FROM room_templates WHERE room_type='staircase_down' LIMIT 1"
                )
                row = cur.fetchone()
                staircase_down_tpl = row["template_id"] if row else None

        item_rooms: List[int] = []
        locked_count = 0
        for _, x, y, rtype, exits in first_defs:
            inner_id = None
            stair_down_floor_id = None
            stair_down_x = None
            stair_down_y = None

            if locked_coord and (x, y) == locked_coord:
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
                    def_en = None
                locked_count += 1
            else:
                def_en = None

            vendor_id = None
            if rtype == "shop":
                gvid = self.fetch_random_vendor()
                if gvid:
                    vendor_id = self.create_session_vendor_instance(session_id, gvid)

            tmpl = self.fetch_random_template(rtype, used_eidolon_ids) or {}
            desc = tmpl.get("description", "A mysterious room…")
            img  = tmpl.get("image_url")
            eidolon_id = tmpl.get("eidolon_id")
            attune_level = tmpl.get("attune_level")
            if rtype == "cloister" and eidolon_id:
                used_eidolon_ids.add(eidolon_id)

            if rtype == "boss":
                with conn.cursor(dictionary=True) as cur2:
                    cur2.execute("SELECT enemy_id FROM enemies WHERE role='boss' ORDER BY RAND() LIMIT 1")
                    row2 = cur2.fetchone()
                def_en = row2["enemy_id"] if row2 else None
            elif rtype == "monster":
                with conn.cursor(dictionary=True) as cur2:
                    cur2.execute("SELECT enemy_id FROM enemies WHERE role='normal' ORDER BY RAND() LIMIT 1")
                    row2 = cur2.fetchone()
                def_en = row2["enemy_id"] if row2 else None

            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO rooms "
                    "(session_id,floor_id,coord_x,coord_y,description,room_type,"
                    " image_url,default_enemy_id,exits,vendor_id,inner_template_id,"
                    " stair_down_floor_id,stair_down_x,stair_down_y,eidolon_id,attune_level) "
                    "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
                    (
                        session_id, first_floor_id, x, y,
                        desc, rtype, img, def_en,
                        json.dumps(exits), vendor_id, inner_id,
                        stair_down_floor_id, stair_down_x, stair_down_y,
                        eidolon_id, attune_level,
                    ),
                )
                rid = cur.lastrowid
                if rtype == "item":
                    item_rooms.append(rid)
        conn.commit()

        # link staircases
        if include_basement:
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
                       AND coord_x=%s AND coord_y=%s
                    """,
                    (
                        first_floor_id, link_x, link_y,
                        session_id, basement_floor_id, link_x, link_y,
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
                       AND coord_x=%s AND coord_y=%s
                    """,
                    (
                        basement_floor_id, link_x, link_y,
                        session_id, first_floor_id, link_x, link_y,
                    ),
                )
                # update images & descriptions from templates
                cur.execute(
                    """
                    UPDATE rooms AS r
                    JOIN room_templates AS t
                    ON t.room_type = 'staircase_up'
                    SET
                    r.image_url        = t.image_url,
                    r.description      = t.description,
                    r.inner_template_id= t.template_id
                    WHERE
                    r.session_id = %s
                    AND r.floor_id = %s
                    AND r.coord_x  = %s
                    AND r.coord_y  = %s
                    """,
                    (session_id, basement_floor_id, link_x, link_y),
                )
                cur.execute(
                    """
                    UPDATE rooms AS r
                    JOIN room_templates AS t
                    ON t.room_type = 'staircase_down'
                    SET
                    r.image_url        = t.image_url,
                    r.description      = t.description,
                    r.inner_template_id= t.template_id
                    WHERE
                    r.session_id = %s
                    AND r.floor_id = %s
                    AND r.coord_x  = %s
                    AND r.coord_y  = %s
                    """,
                    (session_id, first_floor_id, link_x, link_y),
                )
            conn.commit()

        # create chests in item rooms
        key_defs = self.fetch_random_treasure_chest("key")
        all_defs = self.fetch_random_treasure_chest()
        for rid in item_rooms[:locked_count]:
            chest = self.weighted_choice(key_defs)
            if chest:
                self.create_treasure_chest_instance(session_id, rid, chest["chest_id"])
        for rid in item_rooms[locked_count:]:
            chest = self.weighted_choice(all_defs)
            if chest:
                self.create_treasure_chest_instance(session_id, rid, chest["chest_id"])
        conn.commit()
        conn.close()

        # build blob and save
        blob: Dict[str, Any] = {
            "difficulty": difficulty_name,
            "total_floors": total_floors + (1 if include_basement else 0),
            "rooms": [],
            "width": width,
            "height": height,
        }
        if include_basement:
            for _, x, y, rtype, exits in basement_defs:
                blob["rooms"].append({"floor_id": basement_floor_id, "x": x, "y": y, "type": rtype, "exits": exits})
        for _, x, y, rtype, exits in first_defs:
            blob["rooms"].append({"floor_id": first_floor_id, "x": x, "y": y, "type": rtype, "exits": exits})
        self.save_dungeon_to_session(session_id, blob)

        # remaining floors
        if total_floors > 1:
            await self._generate_remaining_floors(
                session_id, difficulty_name,
                width, height, min_rooms,
                enemy_chance, npc_count, shop_limit,
                total_floors, exit_x, exit_y, first_floor_id,
                used_eidolon_ids,
            )

        return blob

    # ─────────────────────────────────────────────── async remainder floors
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
        used_eidolon_ids: Set[int],
    ):
        conn = self.db_connect()
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT game_state FROM sessions WHERE session_id=%s", (session_id,))
        row = cur.fetchone()
        blob = json.loads(row["game_state"] or "{}")
        cur.close()

        loop = asyncio.get_running_loop()
        current_entry = (prev_x, prev_y)

        for floor_number in range(2, total_floors + 1):
            is_goal = floor_number == total_floors

            exit_x, exit_y = self._choose_far_coordinate(width, height, self.MIN_STAIR_DISTANCE)
            while abs(exit_x - current_entry[0]) + abs(exit_y - current_entry[1]) < self.MIN_STAIR_DISTANCE:
                exit_x, exit_y = self._choose_far_coordinate(width, height, self.MIN_STAIR_DISTANCE)

            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO floors (session_id, difficulty, total_rooms, floor_number, is_goal_floor) VALUES (%s,%s,%s,%s,%s)",
                    (session_id, difficulty_name, min_rooms, floor_number, is_goal),
                )
                conn.commit()
                floor_id = cur.lastrowid

            defs = await loop.run_in_executor(
                None,
                functools.partial(
                    self.generate_rooms_for_floor,
                    floor_id, width, height, min_rooms,
                    enemy_chance, npc_count, shop_limit, is_goal,
                    current_entry[0], current_entry[1], exit_x, exit_y,
                    difficulty_name, floor_number, prev_floor_id
                )
            )

            item_rooms: List[int] = []
            locked_count = 0

            for _, x, y, rtype, exits in defs:
                inner_id = None
                if rtype == "locked":
                    inner_id = self.fetch_random_inner_template()
                    locked_count += 1

                vendor_id = None
                if rtype == "shop":
                    gvid = self.fetch_random_vendor()
                    if gvid:
                        vendor_id = self.create_session_vendor_instance(session_id, gvid)

                tmpl = self.fetch_random_template(rtype, used_eidolon_ids) or {}
                desc = tmpl.get("description") or "A mysterious room..."
                img  = tmpl.get("image_url")
                eidolon_id = tmpl.get("eidolon_id")
                attune_level = tmpl.get("attune_level")
                if rtype == "cloister" and eidolon_id:
                    used_eidolon_ids.add(eidolon_id)

                if rtype in ("miniboss","boss","monster"):
                    role = "miniboss" if rtype=="miniboss" else ("boss" if rtype=="boss" else "normal")
                    with conn.cursor(dictionary=True) as cur2:
                        cur2.execute(
                            f"SELECT enemy_id FROM enemies WHERE role=%s ORDER BY RAND() LIMIT 1",
                            (role,)
                        )
                        row2 = cur2.fetchone()
                    def_en = row2["enemy_id"] if row2 else None
                else:
                    def_en = None

                with conn.cursor() as cur:
                    cur.execute(
                        "INSERT INTO rooms (session_id, floor_id, coord_x, coord_y, description, room_type, image_url, default_enemy_id, exits, vendor_id, inner_template_id, eidolon_id, attune_level) "
                        "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
                        (session_id, floor_id, x, y, desc, rtype, img, def_en, json.dumps(exits), vendor_id, inner_id, eidolon_id, attune_level),
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
                    self.create_treasure_chest_instance(session_id, rid, chest["chest_id"])
            for rid in item_rooms[locked_count:]:
                chest = self.weighted_choice(all_defs)
                if chest:
                    self.create_treasure_chest_instance(session_id, rid, chest["chest_id"])
            conn.commit()

            for _, x, y, rtype, exits in defs:
                blob.setdefault("rooms", []).append({
                    "floor_id": floor_id, "x": x, "y": y, "type": rtype, "exits": exits
                })

            with conn.cursor() as cur:
                # link stairs
                cur.execute(
                    "UPDATE rooms SET room_type='staircase_up', stair_up_floor_id=%s, stair_up_x=%s, stair_up_y=%s "
                    "WHERE session_id=%s AND floor_id=%s AND coord_x=%s AND coord_y=%s",
                    (floor_id, current_entry[0], current_entry[1], session_id, prev_floor_id, current_entry[0], current_entry[1])
                )
                cur.execute(
                    "UPDATE rooms SET stair_down_floor_id=%s, stair_down_x=%s, stair_down_y=%s "
                    "WHERE session_id=%s AND floor_id=%s AND coord_x=%s AND coord_y=%s",
                    (prev_floor_id, current_entry[0], current_entry[1], session_id, floor_id, current_entry[0], current_entry[1])
                )
            conn.commit()

            current_entry = (exit_x, exit_y)
            prev_floor_id = floor_id

        self.save_dungeon_to_session(session_id, blob)
        conn.close()

    @commands.command(name="gendungeon")
    @commands.has_permissions(administrator=True)
    async def cmd_generate_dungeon(self, ctx: commands.Context, difficulty_name: str):
        """Admin command to manually start dungeon generation."""
        conn = self.db.get_connection()
        try:
            with conn.cursor(dictionary=True) as cur:
                cur.execute(
                    "SELECT session_id FROM sessions WHERE guild_id=%s ORDER BY created_at DESC LIMIT 1",
                    (ctx.guild.id,),
                )
                row = cur.fetchone()
                if not row:
                    return await ctx.send("❌ No active session found.", delete_after=10)
                session_id = row["session_id"]
        finally:
            conn.close()

        result = await self.generate_dungeon_for_session(ctx, session_id, difficulty_name)
        if result:
            await ctx.send(
                f"🧱 Dungeon generation started for session **{session_id}** at difficulty **{difficulty_name}**! 🎯 First floor ready!"
            )
        else:
            await ctx.send("❌ Failed to generate dungeon.", delete_after=10)


async def setup(bot: commands.Bot):
    await bot.add_cog(DungeonGenerator(bot))
    logger.info("DungeonGenerator cog loaded ✔")
