import random
import json
import mysql.connector
from typing import Any, Dict, List, Optional


class AbilityResult:
    """
    A normalized result from using an ability.
    type: 'damage'|'heal'|'miss'|'dot'|'hot'|'set_hp'|'pilfer'|'mug'
    amount: numeric for damage/heal/set_hp/pilfer/mug
    dot: dict with keys 'damage_per_turn' or 'heal_per_turn', 'remaining_turns', 'effect_name'
    logs: list of strings for the battle log
    status_effects: list of dicts with 'effect_id','effect_name','icon_url','remaining_turns','target'
    """
    def __init__(
        self,
        type: str,
        amount: int = 0,
        dot: Optional[Dict[str, Any]] = None,
        logs: Optional[List[str]] = None,
        status_effects: Optional[List[Dict[str, Any]]] = None,
    ):
        self.type = type
        self.amount = amount
        self.dot = dot or {}
        self.logs = logs or []
        self.status_effects = status_effects or []


class AbilityEngine:
    def __init__(self, db_connect, damage_variance: float = 0.0):
        """
        db_connect: callable returning a MySQL connection
        damage_variance: e.g. 0.1 for ±10% random variance
        """
        self.db_connect = db_connect
        self.variance = damage_variance

    # ------------------------------------------------------------------
    # Elemental resistances
    # ------------------------------------------------------------------
    def fetch_enemy_resistance(self, enemy_id: int, element_id: int) -> float:
        """Return the elemental damage multiplier for ``enemy_id`` and ``element_id``."""
        conn = self.db_connect()
        cur = conn.cursor(dictionary=True)
        cur.execute(
            "SELECT multiplier FROM enemy_resistances WHERE enemy_id=%s AND element_id=%s",
            (enemy_id, element_id),
        )
        row = cur.fetchone()
        cur.close()
        conn.close()
        if row and row.get("multiplier") is not None:
            try:
                return float(row["multiplier"])
            except (TypeError, ValueError):
                return 1.0
        return 1.0

    def _apply_elemental_multiplier(
        self, dmg: int, target: Dict[str, Any], ability: Dict[str, Any]
    ) -> int:
        """Apply elemental resistance/weakness multiplier if applicable."""
        el = ability.get("element_id")
        eid = target.get("enemy_id")
        if el and eid:
            factor = self.fetch_enemy_resistance(eid, el)
            dmg = int(dmg * factor)
        return dmg

    def jrpg_damage(
        self,
        attacker: Dict[str, Any],
        defender: Dict[str, Any],
        base_damage: int,
        scaling_stat: str,
        scaling_factor: float
    ) -> int:
        """
        Classic JRPG ratio‑based damage with optional variance.
        """
        atk = attacker.get(scaling_stat, 0) + base_damage
        if scaling_stat == "magic_power":
            def_stat = defender.get("magic_defense", 0)
        else:
            def_stat = defender.get("defense", 0)

        total = atk + def_stat
        ratio = atk / total if total > 0 else 1.0
        dmg = atk * ratio * scaling_factor

        if self.variance > 0:
            factor = random.uniform(1 - self.variance, 1 + self.variance)
            dmg *= factor

        return max(int(dmg), 1)

    def _enrich_status_effects(self, result: AbilityResult) -> AbilityResult:
        """
        Look up each status_effect['effect_name'] in the single `status_effects`
        table and fill in effect_id + icon_url.
        """
        if not result.status_effects:
            return result

        names = [se["effect_name"] for se in result.status_effects]
        placeholders = ",".join("%s" for _ in names)

        conn = self.db_connect()
        cur  = conn.cursor(dictionary=True)
        cur.execute(
            f"SELECT effect_id, effect_name, icon_url FROM status_effects "
            f"WHERE effect_name IN ({placeholders})",
            tuple(names),
        )
        meta = { row["effect_name"]: row for row in cur.fetchall() }
        cur.close()
        conn.close()

        for inst in result.status_effects:
            m = meta.get(inst["effect_name"])
            if m:
                inst["effect_id"] = m["effect_id"]
                inst["icon_url"]  = m["icon_url"]
            # Normalize duration key & icon for UI
            #  - use 'remaining' everywhere
            inst["remaining"] = inst.pop("remaining_turns", inst.get("remaining", 0))
            #  - alias icon field
            inst["icon"]      = inst.get("icon") or inst.get("icon_url", "")
            # remove any stray duration keys
            inst.pop("remaining_turns", None)
        return result
    
    def _attach_table_status_effects(
        self,
        result: AbilityResult,
        ability: Dict[str, Any]
    ) -> AbilityResult:
        """
        Instead of unconditionally appending, we:
        1) Fetch all table‑driven effects for this ability.
        2) For each, if an effect with the same name is already in result.status_effects,
            we update its effect_id/icon_url.
        3) Otherwise we append it as a brand‐new status_effect.
        """
        aid = ability.get("ability_id")
        dur = ability.get("status_duration") or 0
        if not aid or dur <= 0:
            return result

        # 1) load all the legacy table links
        conn = self.db_connect()
        cur  = conn.cursor(dictionary=True)

        to_attach = []
        # a) single-link
        se_id = ability.get("status_effect_id")
        if se_id:
            cur.execute(
                "SELECT effect_id, effect_name, icon_url "
                "FROM status_effects WHERE effect_id=%s",
                (se_id,)
            )
            row = cur.fetchone()
            if row:
                to_attach.append(row)

        # b) many-to-many extras
        cur.execute(
            """
            SELECT se.effect_id, se.effect_name, se.icon_url
            FROM ability_status_effects ase
            JOIN status_effects se USING (effect_id)
            WHERE ase.ability_id = %s
            """,
            (aid,)
        )
        to_attach.extend(cur.fetchall())

        cur.close()
        conn.close()

        # 2) merge or append
        for meta in to_attach:
            inst = {
                "effect_id":       meta["effect_id"],
                "effect_name":     meta["effect_name"],
                "icon_url":        meta["icon_url"],
                "remaining_turns": dur,
                "target":          ability.get("target_type", "enemy"),
            }

            # look for an existing JSON‑driven effect with the same name
            merged = False
            for existing in result.status_effects:
                if existing.get("effect_name") == inst["effect_name"]:
                    # update it in-place
                    existing["effect_id"]       = inst["effect_id"]
                    existing["icon_url"]        = inst["icon_url"]
                    # also normalize the duration key if you want consistency
                    existing["remaining"]       = inst["remaining_turns"]
                    existing.pop("remaining_turns", None)
                    merged = True
                    break

            # if nothing matched, append as new
            if not merged:
                result.status_effects.append(inst)

        return result


    def resolve(
        self,
        user: Dict[str, Any],
        target: Dict[str, Any],
        ability: Dict[str, Any]
    ) -> AbilityResult:
        """
        Unify player & enemy abilities. Expects `ability` to include
        any enemy_abilities columns as well as normal `abilities` fields.
        """
        logs: List[str] = []
        name = ability["ability_name"]
        result: Optional[AbilityResult] = None

        # 1) Healing (enemy only)
        if ability.get("can_heal"):
            pct = user["hp"] / user["max_hp"]
            if pct <= (ability.get("heal_threshold_pct") or 0):
                amt = int(user["max_hp"] * (ability.get("heal_amount_pct") or 0))
                logs.append(f"{name} heals for {amt} HP.")
                result = AbilityResult(type="heal", amount=amt, logs=logs)

        # 2) Accuracy / miss
        if result is None:
            accuracy = ability.get("accuracy", user.get("accuracy", 100))
            evasion = target.get("evasion", 0)
            if random.randint(1, 100) > max(accuracy - evasion, 0):
                logs.append(f"{name} misses!")
                result = AbilityResult(type="miss", logs=logs)

        # 3) Special "break" effect
        if result is None and ability.get("special_effect") == "break":
            logs.append(f"{name} shatters guard—sets HP to 1!")
            result = AbilityResult(type="set_hp", amount=1, logs=logs)

        # 4) JSON‑driven effects
        effect_data: Dict[str, Any] = {}
        if result is None and ability.get("effect"):
            try:
                effect_data = json.loads(ability["effect"])
            except json.JSONDecodeError:
                effect_data = {}

            # stat‑scaled base damage from JSON
            if result is None and ("base_damage" in effect_data or "damage" in effect_data):
                base = effect_data.get("base_damage", effect_data.get("damage", 0))
                stat = effect_data.get("scaling_stat", "attack_power")
                factor = effect_data.get("scaling_factor", 1.0)
                dmg = self.jrpg_damage(user, target, base, stat, factor)
                dmg = self._apply_elemental_multiplier(dmg, target, ability)
                logs.append(f"{name} deals {dmg} damage.")
                result = AbilityResult(type="damage", amount=dmg, logs=logs)

            # lucky_7
            if result is None and effect_data.get("lucky_7"):
                hp_str = str(user["hp"])
                if "7" not in hp_str:
                    dmg = 1
                    logs.append(f"{name}: no ‘7’ in {user['hp']} → deals {dmg}.")
                else:
                    dmg = random.choice([7, 77, 777, 7777])
                    dmg = self._apply_elemental_multiplier(dmg, target, ability)
                    logs.append(f"{name} JACKPOT! Deals {dmg}.")
                result = AbilityResult(type="damage", amount=dmg, logs=logs)

            # percent_damage
            elif result is None and "percent_damage" in effect_data:
                pct = effect_data["percent_damage"]
                dmg = int(target["hp"] * pct)
                dmg = self._apply_elemental_multiplier(dmg, target, ability)
                logs.append(f"{name} deals {dmg} ({int(pct*100)}%).")
                result = AbilityResult(type="damage", amount=dmg, logs=logs)

            # damage_over_time (DoT)
            elif result is None and "damage_over_time" in effect_data:
                dot_cfg = effect_data["damage_over_time"]
                if isinstance(dot_cfg, (int, float)):
                    dot_cfg = {"damage_per_turn": dot_cfg, "duration": 1}
                dot_inst = {
                    "damage_per_turn":  dot_cfg["damage_per_turn"],
                    "remaining":        dot_cfg["duration"],
                    "effect_name":      effect_data.get("dot_name", name),
                    "icon":             "",  # filled in by _enrich
                }
                logs.append(
                    f"{name} applies **{dot_inst['effect_name']}** "
                    f"for {dot_inst['remaining']} turn(s)."
                )
                result = AbilityResult(
                    type="dot",
                    dot=dot_inst,
                    logs=logs,
                    status_effects=[{
                        "effect_name": dot_inst["effect_name"],
                        "remaining":   dot_inst["remaining"],
                        "target":      ability.get("target_type", "enemy"),
                    }]
                )

            # healing_over_time (HoT)
            elif result is None and "healing_over_time" in effect_data:
                hot_cfg = effect_data["healing_over_time"]
                if isinstance(hot_cfg, (int, float)):
                    heal_each = int(target["max_hp"] * hot_cfg)
                    duration = effect_data.get("duration", 1)
                else:
                    duration = hot_cfg.get("duration", 1)
                    if "heal_per_turn" in hot_cfg:
                        heal_each = hot_cfg["heal_per_turn"]
                    else:
                        heal_each = int(target["max_hp"] * hot_cfg.get("percent", 0))
                hot_inst = {
                    "heal_per_turn":   heal_each,
                    "remaining":       duration,
                    "effect_name":     effect_data.get("hot_name", name),
                    "icon":            "",
                }
                logs.append(
                    f"{name} grants **{hot_inst['effect_name']}** "
                    f"for {hot_inst['remaining']} turn(s)."
                )
                result = AbilityResult(
                    type="hot",
                    dot=hot_inst,
                    logs=logs,
                    status_effects=[{
                        "effect_name": hot_inst["effect_name"],
                        "remaining":   hot_inst["remaining"],
                        "heal_per_turn": hot_inst["heal_per_turn"],
                        "target":      ability.get("target_type", "self"),
                    }]
                )

            # pilfer_gil
            elif result is None and effect_data.get("pilfer_gil"):
                pool = target.get("gil_pool", 0)
                if pool <= 0:
                    logs.append(f"{name} finds no Gil.")
                    result = AbilityResult(type="pilfer", amount=0, logs=logs)
                else:
                    low  = max(1, int(pool*0.1))
                    high = max(low, int(pool*0.25))
                    steal = min(pool, random.randint(low, high))
                    logs.append(f"{name} pilfers {steal} Gil!")
                    result = AbilityResult(type="pilfer", amount=steal, logs=logs)

            # mug
            elif result is None and "mug" in effect_data:
                base = effect_data["mug"].get("damage", 0)
                dmg  = self.jrpg_damage(user, target, base, "attack_power", 1.0)
                dmg  = self._apply_elemental_multiplier(dmg, target, ability)
                pool = target.get("gil_pool", 0)
                steal = 0
                if pool > 0:
                    low  = max(1, int(pool*0.1))
                    high = max(low, int(pool*0.25))
                    steal = min(pool, random.randint(low, high))
                logs.append(f"{name} deals {dmg} and pilfers {steal} Gil!")
                result = AbilityResult(type="mug", amount=dmg, logs=logs)

        # 5) Fallback physical damage
        if result is None:
            dmg = self.jrpg_damage(user, target, 0, "attack_power", 1.0)
            dmg = self._apply_elemental_multiplier(dmg, target, ability)
            logs.append(f"{name} deals {dmg} damage.")
            result = AbilityResult(type="damage", amount=dmg, logs=logs)

        
        # 6) Attach any table‑driven status effects (single + many‑to‑many)
        result = self._attach_table_status_effects(result, ability)

        # 7) Enrich and normalize *all* status effects
        result = self._enrich_status_effects(result)
        return result

    def choose_enemy_ability(self, session: Any, enemy: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Pick one of this enemy’s abilities by:
         1) If Silenced → no ability
         2) Else load enemy_abilities rows
         3) If any healers and HP% ≤ their threshold → choose from healers
         4) Otherwise choose from offensives
         5) Weighted‐random by `weight`
         6) Return the merged ability row (abilities + selected enemy_abilities cols)
        """
        # 1) Silence check
        if any(e["effect_name"] == "Silence" for e in session.battle_state.get("enemy_effects", [])):
            return None

        # 2) Fetch all configured enemy_abilities
        conn = self.db_connect()
        cur = conn.cursor(dictionary=True)
        cur.execute("""
            SELECT
              ea.ability_id,
              ea.weight,
              ea.can_heal,
              ea.heal_threshold_pct,
              ea.heal_amount_pct,
              ea.accuracy AS ability_accuracy
            FROM enemy_abilities ea
            WHERE ea.enemy_id = %s
        """, (enemy["enemy_id"],))
        rows = cur.fetchall()
        cur.close()
        conn.close()
        if not rows:
            return None

        # 3) Split healers vs offensives
        hp_pct     = enemy["hp"] / float(enemy["max_hp"])
        healers    = [r for r in rows if r["can_heal"] and hp_pct <= (r["heal_threshold_pct"] or 0)]
        offensives = [r for r in rows if not r["can_heal"]]
        pool       = healers if healers else offensives
        if not pool:
            return None

        # 4) Weighted pick
        total = sum(r["weight"] for r in pool)
        pick  = random.uniform(0, total)
        upto  = 0
        chosen = pool[-1]
        for r in pool:
            upto += r["weight"]
            if pick <= upto:
                chosen = r
                break

        # 5) Load the base ability info
        conn = self.db_connect()
        cur = conn.cursor(dictionary=True)
        cur.execute("""
            SELECT
              ability_id,
              ability_name,
              effect,
              cooldown,
              icon_url,
              target_type,
              special_effect
            FROM abilities
            WHERE ability_id = %s
        """, (chosen["ability_id"],))
        ab = cur.fetchone()
        cur.close()
        conn.close()
        if not ab:
            return None

        # 6) Merge in the enemy‑specific fields
        ab["can_heal"]           = chosen["can_heal"]
        ab["heal_threshold_pct"] = chosen["heal_threshold_pct"]
        ab["heal_amount_pct"]    = chosen["heal_amount_pct"]
        ab["accuracy"]           = chosen["ability_accuracy"]
        return ab
