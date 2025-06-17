import json
import os
import sys
import types

# Stub mysql & discord modules like other tests
sys.modules.setdefault("mysql", types.ModuleType("mysql"))
sys.modules.setdefault("mysql.connector", types.ModuleType("connector"))
sys.modules.setdefault("aiomysql", types.ModuleType("aiomysql"))
sys.modules["mysql"].connector = sys.modules["mysql.connector"]
sys.modules["mysql.connector"].connection = types.SimpleNamespace(MySQLConnection=object)

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from utils.ability_engine import AbilityEngine

class FakeCursor:
    def __init__(self, rows):
        self.rows = rows
        self.result = None
    def execute(self, sql, params=None):
        for r in self.rows:
            if r["enemy_id"] == params[0] and r["element_id"] == params[1]:
                self.result = {"multiplier": r["multiplier"]}
                break
        else:
            self.result = None
    def fetchone(self):
        return self.result
    def close(self):
        pass

class FakeConnection:
    def __init__(self, rows):
        self.rows = rows
    def cursor(self, dictionary=False):
        return FakeCursor(self.rows)
    def close(self):
        pass


def make_engine(rows, monkeypatch):
    engine = AbilityEngine(lambda: FakeConnection(rows), damage_variance=0)
    monkeypatch.setattr(AbilityEngine, "_attach_table_status_effects", lambda self, r, a: r)
    monkeypatch.setattr(AbilityEngine, "_enrich_status_effects", lambda self, r: r)
    return engine


def base_entities():
    user = {"attack_power": 10, "hp": 50, "max_hp": 50}
    enemy = {"enemy_id": 1, "defense": 0, "hp": 50, "max_hp": 50}
    ability = {"ability_name": "Test", "effect": json.dumps({"base_damage": 0}), "element_id": 1}
    return user, enemy, ability


def test_resistance_multiplier(monkeypatch):
    engine = make_engine([{"enemy_id": 1, "element_id": 1, "multiplier": 0.5}], monkeypatch)
    user, enemy, ability = base_entities()
    result = engine.resolve(user, enemy, ability)
    assert result.amount == 5


def test_weakness_multiplier(monkeypatch):
    engine = make_engine([{"enemy_id": 1, "element_id": 1, "multiplier": 1.5}], monkeypatch)
    user, enemy, ability = base_entities()
    result = engine.resolve(user, enemy, ability)
    assert result.amount == 15


def test_absorb_multiplier(monkeypatch):
    engine = make_engine([{"enemy_id": 1, "element_id": 1, "multiplier": -1}], monkeypatch)
    user, enemy, ability = base_entities()
    result = engine.resolve(user, enemy, ability)
    assert result.amount == -10
