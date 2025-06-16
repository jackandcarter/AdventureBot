"""Game session utilities.

This module defines :class:`GameSession`, a container class used by the
AdventureBot runtime to track players, turns, dungeon state and various
temporary battle attributes while a game is in progress.
"""

from typing import List, Optional, Dict, Any


class GameSession:
    """In-memory representation of a single game session."""

    # pylint: disable=too-many-instance-attributes, too-many-arguments
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
        """Initialize session metadata and state containers.

        Parameters
        ----------
        session_id:
            Unique identifier used for persistence.
        guild_id:
            Discord guild identifier this session belongs to.
        thread_id:
            Discord thread identifier where gameplay occurs.
        owner_id:
            Player that created the session.
        """
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
        # ── status effects ───────────────────────────────────────────────
        # { player_id: [ { "effect_id": int, "remaining": int }, … ] }
        self.status_effects: Dict[int, List[Dict[str, Any]]] = {}

    def add_player(self, player_id: int) -> None:
        """Add a player to the session.

        Raises
        ------
        Exception
            If the player is already in the session or the maximum
            number of participants has been reached.
        """
        if player_id in self.players or len(self.players) >= 6:
            raise Exception("Cannot add player.")
        self.players.append(player_id)
        self.num_players = len(self.players)
        if self.current_turn is None:
            self.current_turn = player_id

    def remove_player(self, player_id: int) -> None:
        """Remove a player from the session.

        Raises
        ------
        Exception
            If the player is not currently part of the session.
        """
        if player_id not in self.players:
            raise Exception("Player not in session.")
        self.players.remove(player_id)
        self.num_players = len(self.players)
        if self.current_turn == player_id:
            self.advance_turn()

    def advance_turn(self) -> Optional[int]:
        """Advance to the next player's turn.

        Returns
        -------
        Optional[int]
            The player ID whose turn is now active, or ``None`` if the
            session has no players.
        """
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
        """Append a line to the session log.

        Only the ten most recent log lines are retained.
        """
        self.game_log.append(message)
        if len(self.game_log) > 10:
            self.game_log = self.game_log[-10:]

    def set_battle_state(self, info: Dict[str, Any]) -> None:
        """Store active battle information for the current encounter."""
        self.battle_state = info

    def clear_battle_state(self) -> None:
        """Reset all stored data about the current battle."""
        self.battle_state = None
        self.current_enemy = None

    def update_ability_cooldown(self, player_id: int, ability_id: int, cd: float) -> None:
        """Set the cooldown timer for a player's ability."""
        self.ability_cooldowns.setdefault(player_id, {})[ability_id] = cd

    def reduce_all_cooldowns(self, amount: float) -> None:
        """Reduce all tracked cooldowns by a given amount.

        Cooldowns will never drop below zero.
        """
        for _, cds in self.ability_cooldowns.items():
            for aid in list(cds):
                cds[aid] = max(cds[aid] - amount, 0.0)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize the session to a dictionary for persistence."""
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
            "trance_states": self.trance_states,
            "status_effects": self.status_effects,
            "current_enemy": self.current_enemy
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "GameSession":
        """Create a :class:`GameSession` instance from serialized data."""
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
        gs.trance_states     = data.get("trance_states", {})
        gs.status_effects    = data.get("status_effects", {})
        gs.current_enemy     = data.get("current_enemy")
        return gs

    def __repr__(self) -> str:
        """Return a concise textual representation of this session."""
        return (
            f"<GameSession id={self.session_id}"
            f" owner={self.owner_id}"
            f" players={self.players}"
            f" turn={self.current_turn}"
            f" floor={self.current_floor}/{self.total_floors}"
            f" enemy={self.current_enemy}>"
        )
