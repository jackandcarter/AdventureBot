import os
import sys
import types
import pytest

# Stub mysql and discord modules like other tests
sys.modules.setdefault("mysql", types.ModuleType("mysql"))
sys.modules.setdefault("mysql.connector", types.ModuleType("connector"))
sys.modules.setdefault("aiomysql", types.ModuleType("aiomysql"))
sys.modules["mysql"].connector = sys.modules["mysql.connector"]

sys.modules.setdefault("discord", types.ModuleType("discord"))
sys.modules.setdefault("discord.ext", types.ModuleType("ext"))
ext_mod = sys.modules["discord.ext"]
ext_mod.commands = types.ModuleType("commands")
sys.modules["discord.ext.commands"] = ext_mod.commands
ext_mod.commands.Cog = type("Cog", (), {})
ext_mod.commands.Bot = object
ext_mod.commands.command = lambda *a, **k: (lambda f: f)
ext_mod.commands.has_guild_permissions = lambda **k: (lambda f: f)
ext_mod.commands.Cog.listener = lambda *a, **k: (lambda f: f)
ext_mod.commands.has_permissions = lambda **k: (lambda f: f)
ext_mod.commands.Context = object

discord = sys.modules["discord"]
discord.InteractionType = types.SimpleNamespace(component=1)
discord.ui = types.SimpleNamespace(View=object, Button=object)
discord.ui.button = lambda *a, **k: (lambda f: f)
discord.ButtonStyle = types.SimpleNamespace(primary=1, secondary=2, success=3, danger=4, blurple=5)
discord.Color = types.SimpleNamespace(gold=lambda: None, blue=lambda: None, purple=lambda: None, green=lambda: None)
discord.Interaction = type("Interaction", (), {})
discord.Embed = type("Embed", (), {"__init__": lambda self, **k: None, "add_field": lambda *a, **k: None, "set_image": lambda *a, **k: None})
discord.abc = types.SimpleNamespace(Messageable=object)
discord.Message = type("Message", (), {})
discord.Thread = type("Thread", (), {})
discord.Member = type("Member", (), {})
discord.Guild = type("Guild", (), {})
discord.TextChannel = type("TextChannel", (), {})
discord.ChannelType = types.SimpleNamespace(private_thread=1)

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from game.battle_system import BattleSystem

class FakeCursor:
    def __init__(self, row):
        self.row = row
    def execute(self, sql, params=None):
        pass
    def fetchone(self):
        return self.row
    def close(self):
        pass

class FakeConnection:
    def __init__(self, row):
        self.row = row
    def cursor(self, dictionary=True):
        return FakeCursor(self.row)
    def close(self):
        pass


def test_reduce_player_cooldowns_speed(monkeypatch):
    bot = types.SimpleNamespace(get_cog=lambda name: None)
    bs = BattleSystem(bot)

    rows = [
        {"speed": 10, "class_id": 1},
        {"base_speed": 10},
    ]
    def db_connect():
        return FakeConnection(rows.pop(0))
    monkeypatch.setattr(bs, "db_connect", db_connect)

    session = types.SimpleNamespace(
        session_id=1,
        battle_state={"player_effects": [{"effect_name": "Haste", "speed_up": 10, "remaining": 1}]},
        ability_cooldowns={1: {5: 3}},
    )

    bs.reduce_player_cooldowns(session, 1)
    assert session.ability_cooldowns[1][5] == 1
