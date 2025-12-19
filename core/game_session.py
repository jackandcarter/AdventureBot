"""
core/game_session.py

Encapsulates an in‑memory representation of a game session,
including players, turn order, dungeon state, battle state, cooldowns, and trance state.
"""

from typing import List, Optional, Dict, Any


class GameSession:
    def __init__(
        self,
        session_id: int,
        guild_id: int,
        thread_id: str,
        owner_id: int,
        difficulty: str = "Easy",
        num_players: int = 1,
        status: str = "active",
        current_floor: int = 1,
        total_floors: int = 1,
        message_id: Optional[int] = None,
        game_log: Optional[List[str]] = None,
        game_state: Optional[Dict[str, Any]] = None
    ):
        # ── identity & persistence ────────────────────────────────────────
        self.session_id: int = session_id
        self.guild_id: int    = guild_id
        self.thread_id: str   = thread_id
        self.owner_id: int    = owner_id

        self.difficulty: str    = difficulty
        self.num_players: int   = num_players
        self.status: str        = status
        self.current_floor: int = current_floor
        self.total_floors: int  = total_floors
        self.message_id: Optional[int] = message_id

        # ── turn / players ───────────────────────────────────────────────
        self.players: List[int] = []              # join order
        self.current_turn: Optional[int] = None   # player_id whose turn it is

        # ── world state ─────────────────────────────────────────────────
        self.game_log: List[str] = game_log or []                     # rolling log
        self.game_state: Dict[str, Any] = game_state or {}            # dungeon layout, etc.

        # ── battle state ────────────────────────────────────────────────
        self.battle_state: Optional[Dict[str, Any]] = None
        self.current_enemy: Optional[Dict[str, Any]] = None

        # ── trance state ────────────────────────────────────────────────
        # { player_id: { "trance_id": int, "name": str, "remaining": int, "max": int } }
        self.trance_states: Dict[int, Dict[str, Any]] = {}

        # ── ability cooldowns ────────────────────────────────────────────
        # { player_id: { ability_id: remaining_seconds } }
        self.ability_cooldowns: Dict[int, Dict[int, float]] = {}
        # ── temporary ability cooldowns ──────────────────────────────────
        # { player_id: { temp_ability_id: remaining_turns } }
        self.temp_ability_cooldowns: Dict[int, Dict[int, int]] = {}
        # ── status effects ───────────────────────────────────────────────
        # { player_id: [ { "effect_id": int, "remaining": int }, … ] }
        self.status_effects: Dict[int, List[Dict[str, Any]]] = {}
        # ── illusion rooms ───────────────────────────────────────────────
        # { player_id: {"room_id": int, "sequence": [...], "current_index": int, "failures": int} }
        self.illusion_states: Dict[int, Dict[str, Any]] = {}
        # { player_id: [room_id, ...] }
        self.illusion_cleared: Dict[int, List[int]] = {}

    def add_player(self, player_id: int) -> None:
        if player_id in self.players or len(self.players) >= 6:
            raise Exception("Cannot add player.")
        self.players.append(player_id)
        self.num_players = len(self.players)
        if self.current_turn is None:
            self.current_turn = player_id

    def remove_player(self, player_id: int) -> None:
        if player_id not in self.players:
            raise Exception("Player not in session.")
        self.players.remove(player_id)
        self.num_players = len(self.players)
        if self.current_turn == player_id:
            self.advance_turn()

    def advance_turn(self) -> Optional[int]:
        if not self.players:
            self.current_turn = None
            return None
        if self.current_turn not in self.players:
            self.current_turn = self.players[0]
        else:
            idx = self.players.index(self.current_turn)
            self.current_turn = self.players[(idx + 1) % len(self.players)]
        return self.current_turn

    def append_log(self, message: str) -> None:
        self.game_log.append(message)
        if len(self.game_log) > 10:
            self.game_log = self.game_log[-10:]

    def set_battle_state(self, info: Dict[str, Any]) -> None:
        self.battle_state = info

    def clear_battle_state(self) -> None:
        self.battle_state = None
        self.current_enemy = None

    def update_ability_cooldown(self, player_id: int, ability_id: int, cd: float) -> None:
        self.ability_cooldowns.setdefault(player_id, {})[ability_id] = cd

    def reduce_all_cooldowns(self, amount: float) -> None:
        for pid, cds in self.ability_cooldowns.items():
            for aid in list(cds):
                cds[aid] = max(cds[aid] - amount, 0.0)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "session_id": self.session_id,
            "guild_id": self.guild_id,
            "thread_id": self.thread_id,
            "owner": self.owner_id,
            "difficulty": self.difficulty,
            "num_players": self.num_players,
            "players": self.players,
            "current_turn": self.current_turn,
            "status": self.status,
            "current_floor": self.current_floor,
            "total_floors": self.total_floors,
            "message_id": self.message_id,
            "game_log": self.game_log,
            "game_state": self.game_state,
            "battle_state": self.battle_state,
            "ability_cooldowns": self.ability_cooldowns,
            "temp_ability_cooldowns": self.temp_ability_cooldowns,
            "trance_states": self.trance_states,
            "status_effects": self.status_effects,
            "current_enemy": self.current_enemy,
            "illusion_states": self.illusion_states,
            "illusion_cleared": self.illusion_cleared
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "GameSession":
        gs = cls(
            session_id    = data["session_id"],
            guild_id      = data["guild_id"],
            thread_id     = data["thread_id"],
            owner_id      = data["owner"],
            difficulty    = data.get("difficulty", "Easy"),
            num_players   = data.get("num_players", 1),
            status        = data.get("status", "active"),
            current_floor = data.get("current_floor", 1),
            total_floors  = data.get("total_floors", 1),
            message_id    = data.get("message_id"),
            game_log      = data.get("game_log", []),
            game_state    = data.get("game_state", {})
        )
        gs.players           = data.get("players", [])
        gs.current_turn      = data.get("current_turn")
        gs.battle_state      = data.get("battle_state")
        gs.ability_cooldowns = data.get("ability_cooldowns", {})
        gs.temp_ability_cooldowns = data.get("temp_ability_cooldowns", {})
        gs.trance_states     = data.get("trance_states", {})
        gs.status_effects    = data.get("status_effects", {})
        gs.current_enemy     = data.get("current_enemy")
        gs.illusion_states   = data.get("illusion_states", {})
        gs.illusion_cleared  = data.get("illusion_cleared", {})
        return gs

    def __repr__(self) -> str:
        return (
            f"<GameSession id={self.session_id}"
            f" owner={self.owner_id}"
            f" players={self.players}"
            f" turn={self.current_turn}"
            f" floor={self.current_floor}/{self.total_floors}"
            f" enemy={self.current_enemy}>"
        )
