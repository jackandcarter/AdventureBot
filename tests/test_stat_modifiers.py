import os
import sys
import types
import asyncio
import pytest

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
ext_mod.commands.Cog.listener = lambda *a, **k: (lambda f: f)

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from game.battle_system import BattleSystem
from utils.status_engine import StatusEffectEngine
from models.session_models import SessionPlayerModel

@pytest.mark.parametrize(
    "key,attr,expected",[
        ("attack_power_up","attack_power",15),
        ("defense_down","defense",5),
        ("magic_power_up","magic_power",15),
        ("magic_defense_up","magic_defense",15),
    ]
)
def test_stat_modifiers_apply_and_expire(monkeypatch, key, attr, expected):
    monkeypatch.setattr(SessionPlayerModel, "modify_hp", lambda *a, **k: None)
    monkeypatch.setattr(SessionPlayerModel, "update_status_effects", lambda *a, **k: None)

    bot = types.SimpleNamespace(get_cog=lambda name: None)
    bs = BattleSystem(bot)

    effect = {"effect_name": "Buff", key: 5, "remaining": 2}
    session = types.SimpleNamespace(
        session_id=1,
        current_turn=1,
        battle_state={"player_effects": [effect], "enemy_effects": [], "enemy": {"enemy_name": "E", "hp": 10, "max_hp": 10}},
        game_log=[],
    )
    session._status_engine = StatusEffectEngine(session, lambda *a: None)

    base = {"attack_power":10, "defense":10, "magic_power":10, "magic_defense":10}
    stats = bs._apply_stat_modifiers(base, session.battle_state["player_effects"])
    assert stats[attr] == expected

    asyncio.run(session._status_engine.tick_combat("player"))
    stats = bs._apply_stat_modifiers(base, session.battle_state["player_effects"])
    assert stats[attr] == expected

    asyncio.run(session._status_engine.tick_combat("player"))
    stats = bs._apply_stat_modifiers(base, session.battle_state["player_effects"])
    assert stats[attr] == 10
