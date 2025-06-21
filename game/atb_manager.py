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
            delta = self.tick_ms / 1000
            notified = {pid: False for pid in players}
            enemy_notified = False
            while session.battle_state:
                await asyncio.sleep(delta)
                if session.atb_paused:
                    continue

                for pid, base in players.items():
                    if session.atb_paused:
                        break
                    max_val = session.atb_maxes.get(pid, 5)
                    if session.atb_gauges.get(pid, 0) < max_val:
                        effective = base + sum(
                            se.get("speed_up", 0) - se.get("speed_down", 0)
                            for se in session.status_effects.get(pid, [])
                        )
                        session.increment_gauge(pid, effective * delta)
                        if session.atb_gauges[pid] >= max_val:
                            session.atb_gauges[pid] = max_val
                    if session.atb_gauges.get(pid, 0) >= max_val:
                        if not notified[pid] and hasattr(battle_system, "on_player_ready"):
                            session.atb_paused = True
                            await battle_system.on_player_ready(session, pid)
                            notified[pid] = True
                    else:
                        notified[pid] = False

                if session.atb_paused:
                    continue

                max_enemy = session.enemy_atb_max
                if session.enemy_atb < max_enemy:
                    e_effective = enemy_speed + sum(
                        se.get("speed_up", 0) - se.get("speed_down", 0)
                        for se in session.battle_state.get("enemy_effects", [])
                    )
                    session.enemy_atb += e_effective * delta
                    if session.enemy_atb >= max_enemy:
                        session.enemy_atb = max_enemy
                if session.enemy_atb >= max_enemy:
                    if not enemy_notified and hasattr(battle_system, "on_enemy_ready"):
                        session.atb_paused = True
                        await battle_system.on_enemy_ready(session)
                        enemy_notified = True
                else:
                    enemy_notified = False

                if hasattr(battle_system, "on_tick"):
                    await battle_system.on_tick(session)
        finally:
            session.atb_task = None
            self._tasks.pop(session.session_id, None)
