import logging
import random
from typing import Any, Dict, Optional


logger = logging.getLogger("IllusionEngine")


class IllusionEngine:
    """Utility helpers for illusion room crystal interactions."""

    def __init__(self, db_connect):
        self.db_connect = db_connect

    # ------------------------------------------------------------------ #
    # Basic lookups
    # ------------------------------------------------------------------ #
    def _player_meta(self, session_id: int, player_id: int) -> Optional[Dict[str, Any]]:
        conn = self.db_connect()
        cur = conn.cursor(dictionary=True)
        cur.execute(
            """
            SELECT class_id, username
              FROM players
             WHERE session_id=%s AND player_id=%s
             LIMIT 1
            """,
            (session_id, player_id),
        )
        meta = cur.fetchone()
        cur.close(); conn.close()
        return meta

    # ------------------------------------------------------------------ #
    # Crystal helpers
    # ------------------------------------------------------------------ #
    def _fetch_room(self, session_id: int, floor_id: int, x: int, y: int) -> Optional[Dict[str, Any]]:
        conn = self.db_connect()
        cur = conn.cursor(dictionary=True)
        cur.execute(
            """
            SELECT room_id, room_type, image_url, inner_template_id
              FROM rooms
             WHERE session_id=%s AND floor_id=%s AND coord_x=%s AND coord_y=%s
             LIMIT 1
            """,
            (session_id, floor_id, x, y),
        )
        room = cur.fetchone()
        cur.close(); conn.close()
        return room

    def _active_crystal(self, room_id: int, session_id: int) -> Optional[Dict[str, Any]]:
        conn = self.db_connect()
        cur = conn.cursor(dictionary=True)
        cur.execute(
            """
            SELECT ic.instance_id, ic.status, ic.sequence_order,
                   ict.template_name, ict.element_id AS crystal_element_id,
                   ict.counter_element_id, ict.image_url, ict.prompt_text
              FROM illusion_crystal_instances ic
              JOIN illusion_crystal_templates ict ON ict.template_id = ic.template_id
             WHERE ic.room_id = %s AND ic.session_id = %s
               AND ic.status != 'shattered'
             ORDER BY ic.sequence_order ASC
             LIMIT 1
            """,
            (room_id, session_id),
        )
        row = cur.fetchone()
        cur.close(); conn.close()
        return row

    def _opposing_element_for(self, element_id: Optional[int]) -> Optional[int]:
        if not element_id:
            return None
        conn = self.db_connect()
        cur = conn.cursor()
        cur.execute(
            """
            SELECT counter_element_id
              FROM element_relationships
             WHERE element_id=%s AND relation_type='opposes'
             LIMIT 1
            """,
            (element_id,),
        )
        row = cur.fetchone()
        cur.close(); conn.close()
        if not row:
            return None
        return row[0]

    def _room_template_for_rewards(self, room_id: int) -> Optional[Dict[str, Any]]:
        conn = self.db_connect()
        cur = conn.cursor(dictionary=True)
        cur.execute(
            """
            SELECT r.inner_template_id,
                   r.description,
                   r.image_url,
                   COALESCE(
                       r.inner_template_id,
                       (
                           SELECT template_id
                             FROM room_templates
                            WHERE room_type = 'illusion'
                            LIMIT 1
                       )
                   ) AS template_id
              FROM rooms r
             WHERE r.room_id = %s
             LIMIT 1
            """,
            (room_id,),
        )
        tpl = cur.fetchone()
        cur.close(); conn.close()
        return tpl

    def _select_reward_option(self, template_id: Optional[int], player_class_id: Optional[int]) -> Optional[Dict[str, Any]]:
        if not template_id:
            return None
        conn = self.db_connect()
        cur = conn.cursor(dictionary=True)
        cur.execute(
            """
            SELECT iro.*, ta.allowed_class_id
              FROM illusion_reward_options iro
              LEFT JOIN temp_abilities ta ON ta.temp_ability_id = iro.temp_ability_id
             WHERE iro.template_id = %s
            """,
            (template_id,),
        )
        options = cur.fetchall()
        cur.close(); conn.close()

        filtered = []
        for opt in options:
            allowed = opt.get("allowed_class_id")
            if opt.get("reward_type") == "temp_ability" and allowed and player_class_id and allowed != player_class_id:
                continue
            filtered.append(opt)

        if not filtered:
            return None

        weights = [max(opt.get("drop_chance") or 0, 0) for opt in filtered]
        total = sum(weights)
        if total <= 0:
            return filtered[0]

        roll = random.random() * total
        cumulative = 0.0
        for opt, weight in zip(filtered, weights):
            cumulative += weight
            if roll <= cumulative:
                return opt
        return filtered[-1]

    def _record_reward_instance(
        self,
        room_id: int,
        session_id: int,
        player_id: int,
        option: Optional[Dict[str, Any]],
    ) -> Optional[int]:
        if not option:
            return None
        conn = self.db_connect()
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO illusion_reward_instances (
                room_id, session_id, reward_option_id, granted_to_player_id,
                reward_label, reward_type, reward_image_url,
                resolved_temp_ability_id, resolved_item_id, resolved_item_qty,
                resolved_gil_amount, resolved_chest_id
            ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """,
            (
                room_id,
                session_id,
                option.get("reward_option_id"),
                player_id,
                option.get("reward_label"),
                option.get("reward_type", "none"),
                option.get("reward_image_url"),
                option.get("temp_ability_id"),
                option.get("item_id"),
                option.get("item_quantity") or 0,
                option.get("gil_amount") or 0,
                option.get("chest_id"),
            ),
        )
        conn.commit()
        instance_id = cur.lastrowid
        cur.close(); conn.close()
        return instance_id

    def _dissipate_illusion(
        self,
        room_id: int,
        session_id: int,
        *,
        reward: Optional[Dict[str, Any]],
        base_description: Optional[str],
        fallback_image: Optional[str],
    ) -> None:
        reward_label = reward.get("reward_label") if reward else None
        reward_type = reward.get("reward_type") if reward else None
        reward_img = reward.get("reward_image_url") if reward else None

        reward_line = "The illusion dissipates, but nothing special is found."
        if reward_label:
            reward_line = f"The illusion dissipates, revealing **{reward_label}**."
        elif reward_type and reward_type != "none":
            reward_line = f"The illusion dissipates, revealing a {reward_type} reward."

        new_description = (base_description or "The illusion fades.")
        new_description = f"{new_description}\n\n{reward_line}"

        conn = self.db_connect()
        cur = conn.cursor()
        cur.execute(
            """
            UPDATE rooms
               SET room_type='safe',
                   description=%s,
                   image_url=%s
             WHERE room_id=%s AND session_id=%s
            """,
            (
                new_description,
                reward_img or fallback_image,
                room_id,
                session_id,
            ),
        )
        conn.commit()
        cur.close(); conn.close()

        self._update_room_state(
            room_id,
            session_id,
            active_idx=None,
            empowered=False,
            pending_teleport=False,
        )

    def _update_room_state(
        self,
        room_id: int,
        session_id: int,
        *,
        active_idx: Optional[int] = None,
        empowered: Optional[bool] = None,
        pending_teleport: Optional[bool] = None,
    ) -> None:
        conn = self.db_connect()
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO illusion_room_states (room_id, session_id, active_crystal_index, empowered, pending_teleport)
            VALUES (%s,%s,%s,%s,%s)
            ON DUPLICATE KEY UPDATE
                active_crystal_index=VALUES(active_crystal_index),
                empowered=COALESCE(%s, empowered),
                pending_teleport=COALESCE(%s, pending_teleport)
            """,
            (
                room_id,
                session_id,
                active_idx if active_idx is not None else 0,
                bool(empowered) if empowered is not None else False,
                bool(pending_teleport) if pending_teleport is not None else False,
                empowered,
                pending_teleport,
            ),
        )
        conn.commit()
        cur.close(); conn.close()

    # ------------------------------------------------------------------ #
    # Public API
    # ------------------------------------------------------------------ #
    def cast_on_active_crystal(
        self,
        *,
        session_id: int,
        room_id: int,
        ability_id: int,
        player_id: int,
    ) -> Dict[str, Any]:
        """
        Apply an ability to the first non-shattered crystal in the room.

        Returns a payload describing the result for the caller to decide
        on teleportation / messaging:
        {
            "status": "shattered"|"empowered"|"no_crystal",
            "log": str,
            "should_teleport": bool,
            "image_url": Optional[str],
        }
        """
        active = self._active_crystal(room_id, session_id)
        if not active:
            return {
                "status": "no_crystal",
                "log": "✨ The illusion has no crystals left to shatter.",
                "should_teleport": False,
                "image_url": None,
            }

        conn = self.db_connect()
        cur = conn.cursor(dictionary=True)
        cur.execute(
            "SELECT element_id, ability_name FROM abilities WHERE ability_id=%s", (ability_id,)
        )
        ability = cur.fetchone()
        cur.close(); conn.close()
        if not ability:
            return {
                "status": "no_crystal",
                "log": "❌ That ability could not be used here.",
                "should_teleport": False,
                "image_url": active.get("image_url"),
            }

        required_element = active.get("counter_element_id") or self._opposing_element_for(active.get("crystal_element_id"))
        ability_element = ability.get("element_id")

        # Track which crystal index the player just attempted
        self._update_room_state(
            room_id,
            session_id,
            active_idx=active.get("sequence_order", 0),
            empowered=False,
            pending_teleport=False,
        )

        if required_element and ability_element == required_element:
            conn = self.db_connect()
            cur = conn.cursor()
            cur.execute(
                "UPDATE illusion_crystal_instances SET status='shattered' WHERE instance_id=%s",
                (active["instance_id"],),
            )
            conn.commit(); cur.close(); conn.close()

            # If no intact crystals remain, ensure pending teleport flags are cleared
            conn = self.db_connect(); cur = conn.cursor()
            cur.execute(
                """
                SELECT COUNT(*) FROM illusion_crystal_instances
                 WHERE room_id=%s AND session_id=%s AND status!='shattered'
                """,
                (room_id, session_id),
            )
            remaining = cur.fetchone()[0]
            cur.close(); conn.close()
            self._update_room_state(room_id, session_id, active_idx=active.get("sequence_order", 0), empowered=False, pending_teleport=False)

            reward_info: Optional[Dict[str, Any]] = None
            reward_log = ""
            if remaining == 0:
                tpl = self._room_template_for_rewards(room_id) or {}
                player = self._player_meta(session_id, player_id)
                option = self._select_reward_option(tpl.get("template_id"), (player or {}).get("class_id"))
                self._record_reward_instance(room_id, session_id, player_id, option)
                reward_info = option or {}
                self._dissipate_illusion(
                    room_id,
                    session_id,
                    reward=option,
                    base_description=tpl.get("description"),
                    fallback_image=tpl.get("image_url"),
                )
                reward_label = (reward_info or {}).get("reward_label") or reward_info.get("reward_type")
                if reward_label:
                    reward_log = f" The illusion fades and reveals **{reward_label}**."
                else:
                    reward_log = " The illusion fades, revealing the chamber's reward."

            log_line = f"✅ {ability['ability_name']} shatters the crystal! ({remaining} remaining)" if remaining else f"✅ {ability['ability_name']} shatters the final crystal!{reward_log}"

            return {
                "status": "shattered",
                "log": log_line,
                "should_teleport": False,
                "image_url": active.get("image_url"),
                "reward": reward_info,
            }

        # Wrong element → empower + flag teleport
        conn = self.db_connect(); cur = conn.cursor()
        cur.execute(
            "UPDATE illusion_crystal_instances SET status='empowered' WHERE instance_id=%s",
            (active["instance_id"],),
        )
        conn.commit(); cur.close(); conn.close()
        self._update_room_state(room_id, session_id, active_idx=active.get("sequence_order", 0), empowered=True, pending_teleport=True)

        return {
            "status": "empowered",
            "log": "⚠️ The crystal surges with energy and the runes force you elsewhere!",
            "should_teleport": True,
            "image_url": active.get("image_url"),
        }
