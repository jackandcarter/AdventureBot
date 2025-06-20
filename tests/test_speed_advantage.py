import types
import os
import sys

# Stub mysql and discord modules like other tests
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
discord.Color = types.SimpleNamespace(gold=lambda: None, blue=lambda: None, purple=lambda: None, green=lambda: None)
discord.Interaction = type("Interaction", (), {})
discord.Embed = type("Embed", (), {"__init__": lambda self, **k: None, "add_field": lambda *a, **k: None, "set_image": lambda *a, **k: None})
discord.abc = types.SimpleNamespace(Messageable=object)
discord.Message = type("Message", (), {})
discord.Thread = type("Thread", (), {})
discord.Member = type("Member", (), {})
discord.Guild = type("Guild", (), {})
discord.TextChannel = type("TextChannel", (), {})

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from game.battle_system import BattleSystem


def test_speed_advantage_only_once():
    bot = types.SimpleNamespace(get_cog=lambda name: None)
    bs = BattleSystem(bot)

    session = types.SimpleNamespace(
        session_id=1,
        current_turn=1,
        battle_state={"player_effects": [], "enemy_effects": [], "enemy": {}},
        game_log=[],
    )

    player = {"speed": 20}
    enemy = {"speed": 0}

    adv1 = bs._check_speed_advantage(session, player, enemy)
    assert adv1 == "player"

    adv2 = bs._check_speed_advantage(session, player, enemy)
    assert adv2 is None

    # simulate end of turn reset
    session.battle_state.pop("speed_advantage_used", None)

    adv3 = bs._check_speed_advantage(session, player, enemy)
    assert adv3 == "player"
