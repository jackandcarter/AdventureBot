import os
import sys
import types

# Stub mysql & discord modules similar to other tests
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
ext_mod.commands.Cog = type("Cog", (), {})
ext_mod.commands.Bot = object
ext_mod.commands.command = lambda *a, **k: (lambda f: f)
ext_mod.commands.Cog.listener = lambda *a, **k: (lambda f: f)
ext_mod.commands.has_guild_permissions = lambda **k: (lambda f: f)
ext_mod.commands.has_permissions = lambda **k: (lambda f: f)
ext_mod.commands.Context = object
discord = sys.modules["discord"]
discord.InteractionType = types.SimpleNamespace(component=1)
discord.ui = types.SimpleNamespace(View=object, Button=object)
discord.ui.button = lambda *a, **k: (lambda f: f)
discord.ButtonStyle = types.SimpleNamespace(primary=1, secondary=2, success=3, danger=4, blurple=5)
discord.Color = types.SimpleNamespace(gold=lambda: None)
discord.Interaction = type("Interaction", (), {})
discord.Embed = type("Embed", (), {"__init__": lambda self, **k: None})
discord.abc = types.SimpleNamespace(Messageable=object)
discord.Message = type("Message", (), {})
discord.Thread = type("Thread", (), {})

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from game.battle_system import BattleSystem

class FakeSession:
    def __init__(self):
        self.battle_state = {"player_effects": [], "enemy_effects": []}
        self.speed_bonus_used = False

bs = BattleSystem(types.SimpleNamespace(get_cog=lambda name: None))


def test_speed_advantage_requires_status():
    session = FakeSession()
    player = {"speed": 20}
    enemy = {"speed": 5}
    assert bs._check_speed_advantage(session, player, enemy) is None

    session.battle_state["player_effects"].append({"speed_up": 5, "effect_name": "Haste", "remaining": 2})
    session.speed_bonus_used = False
    assert bs._check_speed_advantage(session, player, enemy) == "player"
    assert session.speed_bonus_used is True
    # second call should not grant another turn
    assert bs._check_speed_advantage(session, player, enemy) is None

    session.speed_bonus_used = False
    session.battle_state["player_effects"] = []
    session.battle_state["enemy_effects"].append({"speed_down": 5, "effect_name": "Slow", "remaining": 2})
    assert bs._check_speed_advantage(session, player, enemy) == "player"
