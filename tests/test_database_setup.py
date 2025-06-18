import os
import sys
import types

# Stub mysql and discord modules similar to existing tests
sys.modules.setdefault("mysql", types.ModuleType("mysql"))
sys.modules.setdefault("mysql.connector", types.ModuleType("connector"))
sys.modules.setdefault("aiomysql", types.ModuleType("aiomysql"))
sys.modules["mysql"].connector = sys.modules["mysql.connector"]
sys.modules["mysql.connector"].connection = types.SimpleNamespace(MySQLConnection=object)
sys.modules["mysql.connector"].Error = Exception

sys.modules.setdefault("discord", types.ModuleType("discord"))
sys.modules.setdefault("discord.ext", types.ModuleType("ext"))
ext_mod = sys.modules["discord.ext"]
ext_mod.commands = types.ModuleType("commands")
sys.modules["discord.ext.commands"] = ext_mod.commands
ext_mod.commands.Cog = type("Cog", (), {})
ext_mod.commands.Bot = object
ext_mod.commands.command = lambda *a, **k: (lambda f: f)
ext_mod.commands.Cog.listener = lambda *a, **k: (lambda f: f)
ext_mod.commands.has_guild_permissions = lambda **k: (lambda f: f)
ext_mod.commands.has_permissions = lambda **k: (lambda f: f)
ext_mod.commands.Context = object

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import importlib

from database import database_setup

class FakeCursor:
    def __init__(self, log):
        self.log = log
        self.result = None
    def execute(self, sql, params=None):
        self.log.append(sql)
        if sql.startswith("SELECT COUNT(*) FROM"):
            self.result = (0,)
        elif sql.startswith("SHOW COLUMNS"):
            self.result = None
        else:
            self.result = None
    def executemany(self, sql, params):
        self.log.append(sql)
    def fetchone(self):
        return self.result
    def fetchall(self):
        return []
    def __enter__(self):
        return self
    def __exit__(self, exc_type, exc, tb):
        pass
    def close(self):
        pass

class FakeConnection:
    def __init__(self, log):
        self.log = log
    def cursor(self, dictionary=False):
        return FakeCursor(self.log)
    def commit(self):
        pass
    def close(self):
        pass
    def __enter__(self):
        return self
    def __exit__(self, exc_type, exc, tb):
        pass


def test_main_creates_crystal_templates(monkeypatch):
    log = []
    monkeypatch.setattr(
        database_setup.mysql.connector,
        "connect",
        lambda **kw: FakeConnection(log),
        raising=False,
    )
    # Skip column checks and seed inserts
    monkeypatch.setattr(database_setup, "ensure_all_columns", lambda cur: None)
    for fn in [
        "insert_difficulties",
        "insert_floor_room_rules",
        "insert_elements",
        "insert_abilities_and_classes",
        "insert_levels",
        "insert_intro_steps",
        "insert_room_templates",
        "insert_crystal_templates",
        "insert_npc_vendors",
        "insert_items",
        "insert_enemies_and_abilities",
        "insert_enemy_drops",
        "insert_enemy_resistances",
        "insert_npc_vendor_items",
        "insert_new_relational_tables",
        "insert_hub_embeds",
    ]:
        monkeypatch.setattr(database_setup, fn, lambda cur: None)

    database_setup.main()

    assert any("CREATE TABLE" in q and "crystal_templates" in q for q in log)
