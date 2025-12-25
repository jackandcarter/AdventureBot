import random
import json
import mysql.connector
from typing import Any, Dict, List, Optional


class AbilityResult:
    """
    A normalized result from using an ability.
    type: 'damage'|'heal'|'miss'|'dot'|'hot'|'set_hp'|'pilfer'|'mug'|'scan'|'absorb_mp'
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
        element_relation: Optional[str] = None,
        element_multiplier: Optional[float] = None,
        hp_drain: int = 0,
        mp_drain: int = 0,
        hit_count: Optional[int] = None,
    ):
        self.type = type
        self.amount = amount
        self.dot = dot or {}
        self.logs = logs or []
        self.status_effects = status_effects or []
        self.element_relation = element_relation
        self.element_multiplier = element_multiplier
        self.hp_drain = hp_drain
        self.mp_drain = mp_drain
        self.hit_count = hit_count


class AbilityEngine:
    def __init__(self, db_connect, damage_variance: float = 0.0):
        """
        db_connect: callable returning a MySQL connection
        damage_variance: e.g. 0.1 for ±10% random variance
        """
        self.db_connect = db_connect
        self.variance = damage_variance

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

    def _apply_damage_modifiers(
        self,
        dmg: int,
        effect_data: Dict[str, Any],
        target: Dict[str, Any]
    ) -> int:
        if dmg <= 0:
            return dmg

        execute = effect_data.get("execute") or {}
        if execute:
            threshold = float(execute.get("threshold", 0))
            multiplier = float(execute.get("multiplier", 1.0))
            max_hp = target.get("max_hp", 0) or 0
            hp_pct = (target.get("hp", 0) / max_hp) if max_hp else 1.0
            if hp_pct <= threshold:
                dmg = int(dmg * multiplier)

        bonus_vs_role = effect_data.get("bonus_vs_role") or {}
        if bonus_vs_role:
            roles = {r.lower() for r in bonus_vs_role.get("roles", [])}
            multiplier = float(bonus_vs_role.get("multiplier", 1.0))
            if roles and (target.get("role", "").lower() in roles):
                dmg = int(dmg * multiplier)

        return dmg

    def _calculate_mp_drain(self, cfg: Any, target: Dict[str, Any]) -> int:
        amount = 0
        if isinstance(cfg, dict):
            if "amount" in cfg:
                amount = int(cfg.get("amount", 0))
            elif "percent" in cfg:
                amount = int((target.get("max_mp", 0) or 0) * cfg.get("percent", 0))
            elif "percent_current" in cfg:
                amount = int((target.get("mp", 0) or 0) * cfg.get("percent_current", 0))
        else:
            amount = int(cfg or 0)
        return max(amount, 0)

    def _extract_status_effects(
        self,
        effect_data: Dict[str, Any],
        ability: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        raw_effects = []
        if effect_data.get("status_effect"):
            raw_effects.append(effect_data["status_effect"])
        raw_effects.extend(effect_data.get("status_effects", []) or [])

        status_effects = []
        for se in raw_effects:
            if not se:
                continue
            name = se.get("name") or se.get("effect_name")
            if not name:
                continue
            chance = float(se.get("chance", 1.0))
            if chance < 1.0 and random.random() > chance:
                continue
            duration = int(se.get("duration", ability.get("status_duration", 1) or 1))
            status_effects.append(
                {
                    "effect_name": name,
                    "remaining": duration,
                    "target": se.get("target", ability.get("target_type", "enemy")),
                }
            )
        return status_effects

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

    def _get_elemental_modifier(
        self,
        target: Dict[str, Any],
        element_id: Optional[int]
    ) -> Optional[Dict[str, Any]]:
        if not element_id or not target or "enemy_id" not in target:
            return None

        conn = self.db_connect()
        cur = conn.cursor(dictionary=True)
        cur.execute(
            """
            SELECT relation, multiplier
            FROM enemy_resistances
            WHERE enemy_id = %s AND element_id = %s
            """,
            (target["enemy_id"], element_id),
        )
        row = cur.fetchone()
        cur.close()
        conn.close()
        if not row:
            return None
        return row

    def _apply_elemental_modifier(
        self,
        result: AbilityResult,
        ability: Dict[str, Any],
        target: Dict[str, Any]
    ) -> AbilityResult:
        mod = self._get_elemental_modifier(target, ability.get("element_id"))
        if not mod:
            return result

        relation = (mod.get("relation") or "normal").lower()
        default_multiplier = {
            "weak": 1.5,
            "resist": 0.5,
            "immune": 0.0,
            "absorb": 1.0,
            "normal": 1.0,
        }
        multiplier = mod.get("multiplier")
        if multiplier is None:
            multiplier = default_multiplier.get(relation, 1.0)

        result.element_relation = relation
        result.element_multiplier = multiplier

        if result.type == "damage":
            base = result.amount
            if relation == "immune":
                result.amount = 0
            elif relation == "absorb":
                result.type = "heal"
                result.amount = max(int(base * multiplier), 0)
                target_name = target.get("enemy_name", "The enemy")
                result.logs = [
                    f"{target_name} absorbs {ability['ability_name']} and recovers {result.amount} HP."
                ]
            else:
                if base > 0:
                    result.amount = max(int(base * multiplier), 1)
                else:
                    result.amount = 0
        elif result.type == "dot":
            dot_damage = result.dot.get("damage_per_turn")
            if dot_damage is None:
                return result
            if relation == "immune":
                result.dot["damage_per_turn"] = 0
            elif relation == "absorb":
                result.type = "hot"
                result.dot.pop("damage_per_turn", None)
                result.dot["heal_per_turn"] = max(int(dot_damage * multiplier), 0)
            else:
                if dot_damage > 0:
                    result.dot["damage_per_turn"] = max(int(dot_damage * multiplier), 1)
                else:
                    result.dot["damage_per_turn"] = 0

        return result

    def _get_enemy_resistance_profile(self, target: Dict[str, Any]) -> Dict[str, List[str]]:
        if not target or "enemy_id" not in target:
            return {}

        conn = self.db_connect()
        cur = conn.cursor(dictionary=True)
        cur.execute(
            """
            SELECT e.element_name, er.relation
            FROM enemy_resistances er
            JOIN elements e ON e.element_id = er.element_id
            WHERE er.enemy_id = %s
            """,
            (target["enemy_id"],),
        )
        rows = cur.fetchall()
        cur.close()
        conn.close()
        profile: Dict[str, List[str]] = {}
        for row in rows:
            relation = (row.get("relation") or "normal").lower()
            if relation == "normal":
                continue
            profile.setdefault(relation, []).append(row["element_name"])
        return profile
    
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

            if result is None and effect_data.get("scan"):
                target_name = target.get("enemy_name", "the enemy")
                logs.append(f"{name} scans {target_name}.")
                logs.append(
                    f"HP: {target.get('hp', 0)}/{target.get('max_hp', 0)}"
                )
                profile = self._get_enemy_resistance_profile(target)
                if not profile:
                    logs.append("No elemental weaknesses detected.")
                else:
                    for relation in ("weak", "resist", "immune", "absorb"):
                        elements = profile.get(relation, [])
                        if elements:
                            pretty = ", ".join(elements)
                            label = relation.capitalize()
                            logs.append(f"{label}: {pretty}")
                result = AbilityResult(type="scan", logs=logs)

            # multi-hit damage
            if result is None and "multi_hit" in effect_data:
                multi_cfg = effect_data.get("multi_hit")
                if isinstance(multi_cfg, int):
                    multi_cfg = {"hits": multi_cfg}
                hits = int(multi_cfg.get("hits", 2))
                base = multi_cfg.get("base_damage", effect_data.get("base_damage", 0))
                stat = multi_cfg.get("scaling_stat", effect_data.get("scaling_stat", "attack_power"))
                factor = float(multi_cfg.get("scaling_factor", effect_data.get("scaling_factor", 1.0)))
                total = 0
                for _ in range(max(hits, 1)):
                    total += self.jrpg_damage(user, target, base, stat, factor)
                total = self._apply_damage_modifiers(total, effect_data, target)
                logs.append(f"{name} hits {hits} time(s) for {total} damage.")
                result = AbilityResult(type="damage", amount=total, logs=logs, hit_count=hits)

            # flat, defense‑ignoring damage (e.g., Cactuar's Needles)
            if result is None and "flat_damage" in effect_data:
                dmg = int(effect_data.get("flat_damage", 0))
                dmg = self._apply_damage_modifiers(dmg, effect_data, target)
                logs.append(f"{name} deals {dmg} damage.")
                result = AbilityResult(type="damage", amount=dmg, logs=logs)

            # stat‑scaled base damage from JSON
            if result is None and ("base_damage" in effect_data or "damage" in effect_data):
                base = effect_data.get("base_damage", effect_data.get("damage", 0))
                stat = effect_data.get("scaling_stat", "attack_power")
                factor = effect_data.get("scaling_factor", 1.0)
                dmg = self.jrpg_damage(user, target, base, stat, factor)
                dmg = self._apply_damage_modifiers(dmg, effect_data, target)
                logs.append(f"{name} deals {dmg} damage.")
                result = AbilityResult(type="damage", amount=dmg, logs=logs)

            if result is None and "heal" in effect_data:
                amt = int(effect_data.get("heal", 0))
                logs.append(f"{name} restores {amt} HP.")
                result = AbilityResult(type="heal", amount=amt, logs=logs)

            if result is None and "heal_current_pct" in effect_data:
                pct = effect_data["heal_current_pct"]
                amt = int(target["hp"] * pct)
                logs.append(f"{name} restores {amt} HP.")
                result = AbilityResult(type="heal", amount=amt, logs=logs)

            # lucky_7
            if result is None and effect_data.get("lucky_7"):
                hp_str = str(user["hp"])
                if "7" not in hp_str:
                    dmg = 1
                    logs.append(f"{name}: no ‘7’ in {user['hp']} → deals {dmg}.")
                else:
                    dmg = random.choice([7, 77, 777, 7777])
                    logs.append(f"{name} JACKPOT! Deals {dmg}.")
                result = AbilityResult(type="damage", amount=dmg, logs=logs)

            # percent_damage
            elif result is None and "percent_damage" in effect_data:
                pct = effect_data["percent_damage"]
                dmg = int(target["hp"] * pct)
                logs.append(f"{name} deals {dmg} ({int(pct*100)}%).")
                result = AbilityResult(type="damage", amount=dmg, logs=logs)

            # absorb MP (drain from target to user)
            elif result is None and "absorb_mp" in effect_data:
                amount = self._calculate_mp_drain(effect_data["absorb_mp"], target)
                target_name = target.get("enemy_name", "the target")
                logs.append(f"{name} drains {amount} MP from {target_name}.")
                result = AbilityResult(type="absorb_mp", amount=amount, logs=logs, mp_drain=amount)

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
                mug_cfg = effect_data["mug"]
                base = mug_cfg.get("damage", 0)
                dmg  = self.jrpg_damage(user, target, base, "attack_power", 1.0)
                pool = target.get("gil_pool", 0)
                steal = 0
                if pool > 0:
                    multiplier = float(mug_cfg.get("steal_multiplier", 1.0))
                    low  = max(1, int(pool * 0.1 * multiplier))
                    high = max(low, int(pool * 0.25 * multiplier))
                    steal = min(pool, random.randint(low, high))
                logs.append(f"{name} deals {dmg} and pilfers {steal} Gil!")
                result = AbilityResult(type="mug", amount=dmg, logs=logs)

            # status-only abilities
            if result is None and effect_data.get("status_only"):
                logs.append(f"{name} applies lingering effects.")
                result = AbilityResult(type="buff", amount=0, logs=logs)

        # 5) Fallback physical damage
        if result is None:
            dmg = self.jrpg_damage(user, target, 0, "attack_power", 1.0)
            logs.append(f"{name} deals {dmg} damage.")
            result = AbilityResult(type="damage", amount=dmg, logs=logs)

        # 5b) Attach any status effects specified in JSON
        json_effects = self._extract_status_effects(effect_data, ability)
        if json_effects:
            result.status_effects.extend(json_effects)

        mp_cfg = effect_data.get("absorb_mp")
        if mp_cfg and result.type != "absorb_mp":
            result.mp_drain = self._calculate_mp_drain(mp_cfg, target)
            if result.mp_drain:
                target_name = target.get("enemy_name", "the target")
                result.logs.append(f"{name} drains {result.mp_drain} MP from {target_name}.")

        # 6) Apply elemental modifiers (weak/resist/absorb/immune)
        result = self._apply_elemental_modifier(result, ability, target)

        # 6b) Apply HP drain after elemental adjustments
        if result.type == "damage":
            hp_drain_pct = effect_data.get("hp_drain_pct")
            if hp_drain_pct:
                result.hp_drain += max(int(result.amount * float(hp_drain_pct)), 0)
            hp_drain_flat = effect_data.get("hp_drain_flat")
            if hp_drain_flat:
                result.hp_drain += max(int(hp_drain_flat), 0)
        
        # 7) Attach any table‑driven status effects (single + many‑to‑many)
        result = self._attach_table_status_effects(result, ability)

        # 8) Enrich and normalize *all* status effects
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
