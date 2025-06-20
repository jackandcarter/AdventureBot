from __future__ import annotations

import asyncio
from typing import Dict, Any

from models.session_models import SessionPlayerModel


class ATBManager:
    """Handle Active Time Battle gauge updates for a session."""

    def __init__(self, tick_ms: int = 500) -> None:
        self.tick_ms = tick_ms
        self._tasks: Dict[int, asyncio.Task] = {}

    def start(self, session: Any, battle_system: Any) -> None:
        """Begin ticking ATB gauges for ``session``."""
        self.stop(session.session_id)
        task = asyncio.create_task(self._tick_loop(session, battle_system))
        self._tasks[session.session_id] = task
        session.atb_task = task

    def stop(self, session_id: int) -> None:
        """Cancel the ticking task for ``session_id`` if running."""
        task = self._tasks.pop(session_id, None)
        if task and not task.done():
            task.cancel()

    async def _tick_loop(self, session: Any, battle_system: Any) -> None:
        """Internal loop advancing ATB gauges until the battle ends."""
        players = {
            p["player_id"]: p.get("speed", 10)
            for p in SessionPlayerModel.get_player_states(session.session_id)
        }
        enemy_speed = session.current_enemy.get("speed", 10) if session.current_enemy else 10

        try:
            while session.battle_state:
                await asyncio.sleep(self.tick_ms / 1000)
                for pid, base in players.items():
                    speed = base
                    for se in session.status_effects.get(pid, []):
                        speed += se.get("speed_up", 0)
                        speed -= se.get("speed_down", 0)
                    session.increment_gauge(pid, speed * self.tick_ms / 1000)
                    if session.is_ready(pid):
                        if hasattr(battle_system, "on_player_ready"):
                            await battle_system.on_player_ready(session, pid)
                        session.reset_gauge(pid)

                e_speed = enemy_speed
                for se in session.battle_state.get("enemy_effects", []):
                    e_speed += se.get("speed_up", 0)
                    e_speed -= se.get("speed_down", 0)
                session.enemy_atb += e_speed * self.tick_ms / 1000
                if session.enemy_atb >= 100:
                    if hasattr(battle_system, "on_enemy_ready"):
                        await battle_system.on_enemy_ready(session)
                    session.enemy_atb = 0
        finally:
            session.atb_task = None
            self._tasks.pop(session.session_id, None)
