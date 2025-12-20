# utils/status_engine.py

import logging
from models.session_models import SessionPlayerModel

logger = logging.getLogger("StatusEffectEngine")

class StatusEffectEngine:
    def __init__(self, session, log_callable):
        """
        session: your in-memory GameSession (from SessionManager)
        log_callable: a function that takes (session_id:int, msg:str) and logs it
                      e.g. GameMaster.append_game_log
        """
        self.session = session
        self.log     = log_callable

    async def tick_world(self, player_id: int) -> None:
        """
        Out-of-combat: apply all effects on `player_id`,
        decrement durations, persist back to DB, and log each line.
        """
        raw = SessionPlayerModel.get_status_effects(
            self.session.session_id, player_id
        ) or []
        updated = []

        for se in raw:
            name = se["effect_name"]
            dmg  = se.get("damage_per_turn", 0)
            hot  = se.get("heal_per_turn", 0)

            if dmg:
                SessionPlayerModel.modify_hp(
                    self.session.session_id, player_id, damage=dmg
                )
                self.log(
                    self.session.session_id,
                    f"{name} deals {dmg} damage."
                )

            if hot:
                SessionPlayerModel.modify_hp(
                    self.session.session_id, player_id, heal=hot
                )
                self.log(
                    self.session.session_id,
                    f"{name} heals for {hot} HP."
                )

            rem = se.get("remaining", se.get("remaining_turns", 0)) - 1
            if rem > 0:
                se["remaining"] = rem
                updated.append(se)
            else:
                self.log(
                    self.session.session_id,
                    f"{name} has worn off."
                )

        SessionPlayerModel.update_status_effects(
            self.session.session_id, player_id, updated
        )

    async def tick_combat(self, target: str) -> None:
        """
        In-combat: `target` is either 'player' or 'enemy'.
        Effects live in session.battle_state['player_effects']
        or session.battle_state['enemy_effects'].
        Player HP is stored in the DB; enemy HP lives in memory.
        This method applies each tick, logs the exact amount,
        decrements durations, and cleans up expired effects.
        """
        eff_key = f"{target}_effects"
        effects = self.session.battle_state.get(eff_key, []) or []
        new_effects = []

        for se in effects:
            name = se["effect_name"]
            dmg  = se.get("damage_per_turn", 0)
            hot  = se.get("heal_per_turn", 0)

            if target == "player":
                pid = self.session.current_turn

                # Damage tick
                if dmg:
                    SessionPlayerModel.modify_hp(
                        self.session.session_id, pid, damage=dmg
                    )
                    self.log(
                        self.session.session_id,
                        f"{name} deals {dmg} damage to you!"
                    )

                # Heal tick
                if hot:
                    SessionPlayerModel.modify_hp(
                        self.session.session_id, pid, heal=hot
                    )
                    self.log(
                        self.session.session_id,
                        f"{name} heals you for {hot} HP!"
                    )

            else:  # enemy
                enemy = self.session.battle_state.get("enemy", {})

                # Damage tick
                if dmg:
                    enemy["hp"] = max(enemy.get("hp", 0) - dmg, 0)
                    self.log(
                        self.session.session_id,
                        f"{name} deals {dmg} damage to {enemy.get('enemy_name')}!"
                    )

                # Heal tick
                if hot:
                    old = enemy.get("hp", 0)
                    cap = enemy.get("max_hp", 0)
                    healed = min(hot, cap - old)
                    enemy["hp"] = min(old + hot, cap)
                    self.log(
                        self.session.session_id,
                        f"{name} heals {enemy.get('enemy_name')} for {healed} HP!"
                    )

            # Decrement duration
            se["remaining"] = se.get("remaining", se.get("remaining_turns", 0)) - 1
            if se["remaining"] > 0:
                new_effects.append(se)
            else:
                self.log(
                    self.session.session_id,
                    f"{name} has worn off."
                )

        # Write-back the updated effects
        self.session.battle_state[eff_key] = new_effects

        # Persist only the player's side back to the DB
        if target == "player":
            pid = self.session.current_turn
            SessionPlayerModel.update_status_effects(
                self.session.session_id, pid, new_effects
            )
