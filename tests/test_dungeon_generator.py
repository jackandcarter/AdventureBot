import os
import sys
import types
import random

# Stub mysql and discord modules similar to test_high_score
sys.modules.setdefault("mysql", types.ModuleType("mysql"))
sys.modules.setdefault("mysql.connector", types.ModuleType("connector"))
sys.modules.setdefault("aiomysql", types.ModuleType("aiomysql"))
sys.modules["mysql"].connector = sys.modules["mysql.connector"]
sys.modules["mysql.connector"].connection = types.SimpleNamespace(MySQLConnection=object)
sys.modules.setdefault("discord", types.ModuleType("discord"))
sys.modules.setdefault("discord.ext", types.ModuleType("ext"))
ext_mod = sys.modules["discord.ext"]
ext_mod.commands = types.ModuleType("commands")
sys.modules["discord.ext.commands"] = ext_mod.commands
ext_mod.commands.Cog = object
ext_mod.commands.Bot = object
ext_mod.commands.command = lambda *a, **k: (lambda f: f)
ext_mod.commands.has_guild_permissions = lambda **k: (lambda f: f)
ext_mod.commands.has_permissions = lambda **k: (lambda f: f)
ext_mod.commands.Context = object

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from game.dungeon_generator import DungeonGenerator


def test_single_boss_room(monkeypatch):
    gen = DungeonGenerator(None)
    monkeypatch.setattr(gen, "fetch_floor_rules", lambda d, f: [])
    random.seed(42)
    rooms, _ = gen.generate_rooms_for_floor(
        1, 4, 4, 4, 0.5, 0, 0, True, 0, 0, 3, 3, "Easy", 1
    )
    boss_cells = [r for r in rooms if r[3] == "boss"]
    assert len(boss_cells) == 1

