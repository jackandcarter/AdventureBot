import json
import logging
from typing import Union, Optional, Dict, Any, List

from models.database import Database

logger = logging.getLogger("SessionModels")
logger.setLevel(logging.DEBUG)

# ────────────────────────────────────────────────────────────────────────
#  SessionModel
# ────────────────────────────────────────────────────────────────────────
class SessionModel:
    @staticmethod
    def create_session(guild_id: int, thread_id: str, owner_id: int,
                       num_players: int, difficulty: str,
                       game_state: Optional[dict]) -> Union[int, None]:
        db = Database()
        conn = db.get_connection()
        cur  = conn.cursor()
        try:
            cur.execute(
                """
                INSERT INTO sessions
                       (guild_id, thread_id, owner_id,
                        num_players, difficulty,
                        game_state, status)
                VALUES (%s, %s, %s, %s, %s, %s, 'active')
                """,
                (
                    guild_id, thread_id, owner_id,
                    num_players, difficulty,
                    json.dumps(game_state) if game_state is not None else None,
                ),
            )
            conn.commit()
            sid = cur.lastrowid
            logger.debug("Created session %s for guild %s", sid, guild_id)
            return sid
        except Exception:
            logger.exception("Error creating session")
            return None
        finally:
            cur.close()
            conn.close()

    @staticmethod
    def increment_player_count(session_id: int) -> None:
        db = Database()
        conn = db.get_connection()
        cur  = conn.cursor()
        try:
            cur.execute(
                "UPDATE sessions SET num_players = num_players + 1 "
                "WHERE session_id = %s",
                (session_id,),
            )
            conn.commit()
        except Exception:
            logger.exception("Error incrementing player count")
        finally:
            cur.close()
            conn.close()

    @staticmethod
    def update_num_players(session_id: int, num_players: int) -> None:
        db = Database()
        conn = db.get_connection()
        cur  = conn.cursor()
        try:
            cur.execute(
                "UPDATE sessions SET num_players=%s WHERE session_id=%s",
                (num_players, session_id),
            )
            conn.commit()
        except Exception:
            logger.exception("Error updating number of players")
        finally:
            cur.close()
            conn.close()

    @staticmethod
    def activate_session(session_id: int) -> None:
        db = Database()
        conn = db.get_connection()
        cur  = conn.cursor()
        try:
            cur.execute(
                "UPDATE sessions SET status='active' WHERE session_id=%s",
                (session_id,),
            )
            conn.commit()
        except Exception:
            logger.exception("Error activating session")
        finally:
            cur.close()
            conn.close()

    @staticmethod
    def get_game_state(session_id: int) -> dict | None:
        """
        Fetch the JSON blob from sessions.game_state, parse it, and return
        the *exact* dict that was originally saved (so from_dict() works).
        """
        db = Database()
        conn = db.get_connection()
        try:
            cur = conn.cursor(dictionary=True)
            cur.execute(
                "SELECT game_state "
                "  FROM sessions "
                " WHERE session_id = %s",
                (session_id,)
            )
            row = cur.fetchone()
            if not row or not row.get("game_state"):
                return None

            raw = row["game_state"]
            # If the driver returns a string, parse it.  Otherwise assume it's already dict.
            if isinstance(raw, str):
                try:
                    return json.loads(raw)
                except json.JSONDecodeError:
                    return None
            return raw

        finally:
            cur.close()
            conn.close()

    @staticmethod
    def update_game_state(session_id: int, state: dict) -> None:
        """
        Persist the full GameSession.to_dict() output into the sessions.game_state JSON column,
        and mark saved=1 so we know it’s loadable.
        """
        db = Database()
        conn = db.get_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                "UPDATE sessions "
                "   SET game_state = %s, saved = 1 "
                " WHERE session_id = %s",
                (json.dumps(state, default=str), session_id)
            )
            conn.commit()
        finally:
            cur.close()
            conn.close()

    @staticmethod
    def is_owner(session_id: int, player_id: int) -> bool:
        db = Database()
        conn = db.get_connection()
        cur  = conn.cursor()
        try:
            cur.execute(
                "SELECT owner_id FROM sessions WHERE session_id=%s",
                (session_id,),
            )
            row = cur.fetchone()
            return row and row[0] == player_id
        except Exception:
            logger.exception("Error checking session owner")
            return False
        finally:
            cur.close()
            conn.close()

    @staticmethod
    def mark_saved(session_id: int, saved: bool) -> None:
        """
        Toggle the `saved` flag on a session so cleanup will skip it.
        """
        conn = Database().get_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                "UPDATE sessions SET saved=%s WHERE session_id=%s",
                (1 if saved else 0, session_id)
            )
            conn.commit()
        finally:
            cur.close()
            conn.close()

    @staticmethod
    def is_saved(session_id: int) -> bool:
        conn = Database().get_connection()
        cur = conn.cursor()
        try:
            cur.execute("SELECT saved FROM sessions WHERE session_id=%s", (session_id,))
            row = cur.fetchone()
            return bool(row and row[0])
        finally:
            cur.close()
            conn.close()

    @staticmethod
    def get_saved_sessions_for_user(player_id: int) -> list[dict]:
        """
        Return a list of saved sessions that this player has joined.
        We only need session_id & difficulty here (for the hub-load menu).
        """
        db = Database()
        conn = db.get_connection()
        try:
            cur = conn.cursor(dictionary=True)
            cur.execute(
                """
                SELECT s.session_id, s.difficulty
                  FROM sessions s
                  JOIN session_players sp ON sp.session_id = s.session_id
                 WHERE sp.player_id = %s
                   AND s.saved = 1
                """,
                (player_id,)
            )
            return cur.fetchall() or []
        finally:
            cur.close()
            conn.close()

    @staticmethod
    def update_thread_id(session_id: int, new_thread_id: str) -> None:
        """Point this session record at a freshly‑created thread."""
        db = Database()
        conn = db.get_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                "UPDATE sessions SET thread_id=%s, status='active' WHERE session_id=%s",
                (new_thread_id, session_id)
            )
            conn.commit()
        finally:
            cur.close()
            conn.close()


# ────────────────────────────────────────────────────────────────────────
#  SessionPlayerModel
# ────────────────────────────────────────────────────────────────────────
class SessionPlayerModel:

    # ── player-row bootstrap ────────────────────────────────────────────
    @staticmethod
    def add_player(session_id: int, player_id: int, username: str) -> None:
        db = Database()
        conn = db.get_connection()
        cur  = conn.cursor()
        try:
            cur.execute(
                "INSERT IGNORE INTO session_players (session_id, player_id) "
                "VALUES (%s, %s)",
                (session_id, player_id),
            )
            conn.commit()
            logger.debug("Added player %s → session %s", player_id, session_id)
        except Exception:
            logger.exception("Error adding player to session_players")
        finally:
            cur.close()
            conn.close()

        SessionPlayerModel.ensure_player_state(session_id, player_id, username)

    @staticmethod
    def ensure_player_state(session_id: int, player_id: int, username: str) -> None:
        db = Database()
        conn = db.get_connection()
        cur  = conn.cursor()
        try:
            cur.execute("""
            INSERT INTO players
                  (player_id, username, session_id,
                   gil, experience, level,
                   coord_x, coord_y, current_floor_id,
                   inventory, discovered_rooms, status_effects,
                   is_dead)
            VALUES (%s,%s,%s, 0,0,1, 0,0,1, %s,%s,%s, 0)
            ON DUPLICATE KEY UPDATE username = VALUES(username)
            """, (
                player_id, username, session_id,
                json.dumps({}), json.dumps([]), json.dumps([]),
            ))
            conn.commit()
        except Exception:
            logger.exception("Error ensuring player state")
        finally:
            cur.close()
            conn.close()

    @staticmethod
    def add_status_effect(session_id: int,
                          player_id:  int,
                          effect:     Dict[str, Any]) -> None:
        """
        Append one status‑effect dict into players.status_effects JSON.
        """
        conn = Database().get_connection()
        try:
            cur = conn.cursor(dictionary=True)
            cur.execute(
                "SELECT status_effects FROM players "
                " WHERE session_id=%s AND player_id=%s",
                (session_id, player_id)
            )
            row = cur.fetchone()
            arr = json.loads(row["status_effects"] or "[]")

            # append the full effect dict
            arr.append(effect)

            cur.execute(
                "UPDATE players SET status_effects=%s "
                " WHERE session_id=%s AND player_id=%s",
                (json.dumps(arr), session_id, player_id)
            )
            conn.commit()
        except Exception:
            logger.exception("Error appending status effect")
        finally:
            cur.close()
            conn.close()
            
    # ── inventory helpers ───────────────────────────────────────────────
    @staticmethod
    def get_inventory(session_id: int, player_id: int) -> Dict[str, int]:
        db = Database()
        conn = db.get_connection()
        cur  = conn.cursor(dictionary=True)
        try:
            cur.execute(
                "SELECT inventory FROM players "
                "WHERE session_id=%s AND player_id=%s",
                (session_id, player_id),
            )
            row = cur.fetchone()
            return json.loads(row["inventory"]) if row and row["inventory"] else {}
        except Exception:
            logger.exception("Error fetching inventory")
            return {}
        finally:
            cur.close()
            conn.close()

    @staticmethod
    def update_inventory(session_id: int, player_id: int,
                         inventory: Dict[str, int]) -> None:
        db = Database()
        conn = db.get_connection()
        cur  = conn.cursor()
        try:
            cur.execute(
                "UPDATE players SET inventory=%s "
                "WHERE session_id=%s AND player_id=%s",
                (json.dumps(inventory), session_id, player_id),
            )
            conn.commit()
        except Exception:
            logger.exception("Error updating inventory")
        finally:
            cur.close()
            conn.close()

    @staticmethod
    def add_inventory_item(session_id: int, player_id: int,
                           item_id: int, qty: int = 1) -> None:
        inv = SessionPlayerModel.get_inventory(session_id, player_id)
        key = str(item_id)
        inv[key] = inv.get(key, 0) + qty
        SessionPlayerModel.update_inventory(session_id, player_id, inv)

    @staticmethod
    def remove_inventory_item(session_id: int, player_id: int,
                              item_id: int, qty: int = 1) -> bool:
        inv = SessionPlayerModel.get_inventory(session_id, player_id)
        key = str(item_id)
        cur_qty = inv.get(key, 0)
        if cur_qty <= 0:
            return False
        new_qty = max(cur_qty - qty, 0)
        if new_qty:
            inv[key] = new_qty
        else:
            inv.pop(key)
        SessionPlayerModel.update_inventory(session_id, player_id, inv)
        return True

    # ── death / faint helpers ────────────────────────────────────────────
    def set_player_dead(session_id: int, player_id: int) -> None:
        """
        Mark a player as dead/fainted.
        """
        conn = Database().get_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                "UPDATE players SET is_dead = 1 WHERE session_id = %s AND player_id = %s",
                (session_id, player_id)
            )
            conn.commit()
        except Exception:
            logger.exception("Error marking player dead")
        finally:
            cur.close()
            conn.close()

    @staticmethod
    def revive_player(session_id: int, player_id: int) -> None:
        """
        Revive a dead/fainted player (clear the flag).
        Does *not* itself restore HP—do that at the GameMaster/battle layer.
        """
        conn = Database().get_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                "UPDATE players SET is_dead = 0 WHERE session_id = %s AND player_id = %s",
                (session_id, player_id)
            )
            conn.commit()
        except Exception:
            logger.exception("Error reviving player")
        finally:
            cur.close()
            conn.close()

    @staticmethod
    def is_player_dead(session_id: int, player_id: int) -> bool:
        """
        Return True if the player is currently marked as dead/fainted.
        """
        conn = Database().get_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                "SELECT is_dead FROM players WHERE session_id = %s AND player_id = %s",
                (session_id, player_id)
            )
            row = cur.fetchone()
            return bool(row and row[0] == 1)
        except Exception:
            logger.exception("Error checking player death status")
            return False
        finally:
            cur.close()
            conn.close()

    # ── key-item helpers ───────────────────────────────────────────────
    @staticmethod
    def _quest_item_ids_from_inventory(inv: Dict[str, int]) -> List[int]:
        ids: List[int] = []
        for raw in inv.keys():
            try:
                ids.append(int(raw))
            except (TypeError, ValueError):
                continue
        return ids

    @staticmethod
    def get_key_count(session_id: int, player_id: int) -> int:
        """
        Return how many items of type 'quest' the player owns.
        Safely ignores malformed inventory keys.
        """
        inv = SessionPlayerModel.get_inventory(session_id, player_id)
        candidates = SessionPlayerModel._quest_item_ids_from_inventory(inv)
        if not candidates:
            return 0

        placeholders = ",".join(["%s"] * len(candidates))
        db = Database()
        conn = db.get_connection()
        try:
            with conn.cursor(dictionary=True) as cur:
                cur.execute(
                    f"SELECT item_id FROM items "
                    f"WHERE type='quest' AND item_id IN ({placeholders})",
                    tuple(candidates),
                )
                quest_ids = {r["item_id"] for r in cur.fetchall()}
            return sum(inv.get(str(i), 0) for i in quest_ids)
        except Exception:
            logger.exception("Error counting key items")
            return 0
        finally:
            conn.close()

    @staticmethod
    def consume_key(session_id: int, player_id: int) -> bool:
        """
        Remove one quest-type item if available. Returns True on success.
        """
        inv = SessionPlayerModel.get_inventory(session_id, player_id)
        candidates = SessionPlayerModel._quest_item_ids_from_inventory(inv)
        if not candidates:
            return False

        placeholders = ",".join(["%s"] * len(candidates))
        db = Database()
        conn = db.get_connection()
        try:
            with conn.cursor(dictionary=True) as cur:
                cur.execute(
                    f"SELECT item_id FROM items "
                    f"WHERE type='quest' AND item_id IN ({placeholders}) LIMIT 1",
                    tuple(candidates),
                )
                hit = cur.fetchone()
                if not hit:
                    return False
                iid = int(hit["item_id"])
            SessionPlayerModel.remove_inventory_item(session_id, player_id, iid, 1)
            return True
        except Exception:
            logger.exception("Error consuming key item")
            return False
        finally:
            conn.close()

    # ── misc getters / setters ─────────────────────────────────────────
    @staticmethod
    def get_players(session_id: int) -> List[int]:
        db = Database()
        conn = db.get_connection()
        cur  = conn.cursor()
        try:
            cur.execute(
                "SELECT player_id FROM session_players "
                "WHERE session_id=%s ORDER BY joined_at ASC",
                (session_id,),
            )
            return [r[0] for r in cur.fetchall()]
        except Exception:
            logger.exception("Error fetching players for session %s", session_id)
            return []
        finally:
            cur.close()
            conn.close()

    @staticmethod
    def get_player_states(session_id: int) -> List[dict]:
        db = Database()
        conn = db.get_connection()
        cur  = conn.cursor(dictionary=True)
        try:
            cur.execute(
                "SELECT * FROM players WHERE session_id=%s "
                "ORDER BY player_id ASC",
                (session_id,),
            )
            return cur.fetchall()
        except Exception:
            logger.exception("Error fetching player states")
            return []
        finally:
            cur.close()
            conn.close()

    # ── status‐effects helpers ─────────────────────────────────────────
    @staticmethod
    def get_status_effects(session_id: int, player_id: int) -> List[Dict[str, Any]]:
        """
        Return the list of active status effects on this player
        exactly as stored in players.status_effects JSON.
        Each entry must already include:
          - effect_id
          - effect_name
          - icon_url
          - remaining_turns
        """
        conn = Database().get_connection()
        try:
            cur = conn.cursor(dictionary=True)
            cur.execute(
                "SELECT status_effects "
                "  FROM players "
                " WHERE session_id = %s "
                "   AND player_id  = %s",
                (session_id, player_id)
            )
            row = cur.fetchone()
            cur.close()

            if not row or not row.get("status_effects"):
                return []
            raw = json.loads(row["status_effects"])
            return raw if isinstance(raw, list) else []
        except Exception:
            logger.exception("Error fetching status effects")
            return []
        finally:
            conn.close()

    @staticmethod
    def update_status_effects(session_id: int, player_id: int,
                              effects: List[Dict[str, Any]]) -> None:
        """
        Overwrite the player’s active status effects JSON array.
        """
        conn = Database().get_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                "UPDATE players SET status_effects=%s "
                " WHERE session_id=%s AND player_id=%s",
                (json.dumps(effects), session_id, player_id)
            )
            conn.commit()
        except Exception:
            logger.exception("Error updating status effects")
        finally:
            cur.close()
            conn.close()

            
    @staticmethod
    def modify_hp(session_id: int, player_id: int, heal: int = 0, damage: int = 0):
        """Apply a heal or damage to a player’s HP in the database."""
        conn = Database().get_connection()
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE players
                   SET hp = LEAST(max_hp, GREATEST(0, hp + %s - %s))
                 WHERE session_id=%s AND player_id=%s
                """,
                (heal, damage, session_id, player_id)
            )
        conn.commit()
        conn.close()

    @staticmethod
    def get_mp(session_id: int, player_id: int) -> Optional[Dict[str, int]]:
        conn = Database().get_connection()
        try:
            cur = conn.cursor(dictionary=True)
            cur.execute(
                "SELECT mp, max_mp FROM players WHERE session_id=%s AND player_id=%s",
                (session_id, player_id),
            )
            return cur.fetchone()
        except Exception:
            logger.exception("Error fetching player MP")
            return None
        finally:
            cur.close()
            conn.close()

    @staticmethod
    def update_mp(session_id: int, player_id: int, mp: int) -> None:
        conn = Database().get_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                "UPDATE players SET mp=%s WHERE session_id=%s AND player_id=%s",
                (mp, session_id, player_id),
            )
            conn.commit()
        except Exception:
            logger.exception("Error updating player MP")
        finally:
            cur.close()
            conn.close()

    @staticmethod
    def has_out_of_battle_eidolon_support(session_id: int, player_id: int) -> bool:
        conn = Database().get_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT 1
                  FROM player_eidolons pe
                  JOIN eidolon_abilities ea
                    ON ea.eidolon_id = pe.eidolon_id
                   AND ea.unlock_level <= pe.level
                  JOIN abilities a
                    ON a.ability_id = ea.ability_id
                 WHERE pe.session_id = %s
                   AND pe.player_id = %s
                   AND a.target_type IN ('self', 'ally', 'any')
                 LIMIT 1
                """,
                (session_id, player_id),
            )
            return cur.fetchone() is not None
        except Exception:
            logger.exception("Error checking eidolon support abilities")
            return False
        finally:
            cur.close()
            conn.close()

    @staticmethod
    def get_unlocked_eidolons(session_id: int, player_id: int) -> List[Dict[str, Any]]:
        conn = Database().get_connection()
        try:
            cur = conn.cursor(dictionary=True)
            cur.execute(
                """
                SELECT pe.eidolon_id, pe.level, pe.experience,
                       e.name, e.description, e.required_level, e.summon_mp_cost
                  FROM player_eidolons pe
                  JOIN eidolons e ON e.eidolon_id = pe.eidolon_id
                 WHERE pe.session_id = %s
                   AND pe.player_id = %s
                 ORDER BY pe.eidolon_id
                """,
                (session_id, player_id),
            )
            return cur.fetchall()
        except Exception:
            logger.exception("Error fetching unlocked eidolons")
            return []
        finally:
            cur.close()
            conn.close()

    @staticmethod
    def unlock_eidolon(session_id: int, player_id: int, eidolon_id: int) -> None:
        conn = Database().get_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                """
                INSERT IGNORE INTO player_eidolons (session_id, player_id, eidolon_id)
                VALUES (%s,%s,%s)
                """,
                (session_id, player_id, eidolon_id),
            )
            conn.commit()
        except Exception:
            logger.exception("Error unlocking eidolon")
        finally:
            cur.close()
            conn.close()

    @staticmethod
    def award_eidolon_experience(
        session_id: int,
        player_id: int,
        eidolon_id: int,
        xp_gain: int,
    ) -> Optional[Dict[str, Any]]:
        conn = Database().get_connection()
        try:
            cur = conn.cursor(dictionary=True)
            cur.execute(
                """
                SELECT level, experience
                  FROM player_eidolons
                 WHERE session_id=%s AND player_id=%s AND eidolon_id=%s
                """,
                (session_id, player_id, eidolon_id),
            )
            row = cur.fetchone()
            if not row:
                return None

            total_xp = row["experience"] + xp_gain
            new_level = row["level"]

            while True:
                cur.execute("SELECT required_exp FROM levels WHERE level=%s", (new_level + 1,))
                nxt = cur.fetchone()
                if not nxt or total_xp < nxt["required_exp"]:
                    break
                total_xp -= nxt["required_exp"]
                new_level += 1

            cur.execute(
                """
                UPDATE player_eidolons
                   SET experience=%s, level=%s
                 WHERE session_id=%s AND player_id=%s AND eidolon_id=%s
                """,
                (total_xp, new_level, session_id, player_id, eidolon_id),
            )
            conn.commit()
            return {"level": new_level, "experience": total_xp}
        except Exception:
            logger.exception("Error awarding eidolon experience")
            return None
        finally:
            cur.close()
            conn.close()



    # ── class selection ───────────────────────────────────────────────
    @staticmethod
    def update_player_class(session_id: int, player_id: int,
                            class_id: int) -> None:
        db = Database()
        conn = db.get_connection()
        cur  = conn.cursor(dictionary=True)
        try:
            cur.execute(
                """
                SELECT base_hp, base_attack, base_magic, base_mp, base_defense,
                       base_magic_defense, base_accuracy,
                       base_evasion, base_speed
                  FROM classes WHERE class_id=%s
                """,
                (class_id,),
            )
            stats = cur.fetchone()
            if stats:
                cur.execute(
                    """
                    UPDATE players SET class_id=%s,
                        hp=%s, max_hp=%s,
                        mp=%s, max_mp=%s,
                        attack_power=%s, defense=%s,
                        magic_power=%s, magic_defense=%s,
                        accuracy=%s, evasion=%s, speed=%s
                    WHERE session_id=%s AND player_id=%s
                    """,
                    (
                        class_id,
                        stats["base_hp"], stats["base_hp"],
                        stats.get("base_mp", 0), stats.get("base_mp", 0),
                        stats["base_attack"], stats["base_defense"],
                        stats["base_magic"], stats["base_magic_defense"],
                        stats["base_accuracy"], stats["base_evasion"],
                        stats["base_speed"],
                        session_id, player_id,
                    ),
                )
            else:
                cur.execute(
                    "UPDATE players SET class_id=%s "
                    "WHERE session_id=%s AND player_id=%s",
                    (class_id, session_id, player_id),
                )
            conn.commit()
        except Exception:
            logger.exception("Error updating player class")
        finally:
            cur.close()
            conn.close()


# ────────────────────────────────────────────────────────────────────────
#  ClassModel
# ────────────────────────────────────────────────────────────────────────
class ClassModel:
    @staticmethod
    def get_class_name(class_id: int) -> str:
        db = Database()
        conn = db.get_connection()
        cur  = conn.cursor()
        try:
            cur.execute(
                "SELECT class_name FROM classes WHERE class_id=%s",
                (class_id,),
            )
            row = cur.fetchone()
            return row[0] if row else "Unknown"
        except Exception:
            logger.exception("Error fetching class name")
            return "Unknown"
        finally:
            cur.close()
            conn.close()

    @staticmethod
    def get_class_image_url(class_id: int) -> Optional[str]:
        db = Database()
        conn = db.get_connection()
        cur  = conn.cursor()
        try:
            cur.execute(
                "SELECT image_url FROM classes WHERE class_id=%s",
                (class_id,),
            )
            row = cur.fetchone()
            return row[0] if row and row[0] else None
        except Exception:
            logger.exception("Error fetching class image URL")
            return None
        finally:
            cur.close()
            conn.close()
