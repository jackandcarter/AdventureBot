import os
import sys
import types
import asyncio

# Stub mysql and discord modules similar to other tests
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
discord.Color = types.SimpleNamespace(purple=lambda: None, dark_gold=lambda: None, dark_red=lambda: None)
discord.Interaction = type("Interaction", (), {})
discord.Embed = type("Embed", (), {"__init__": lambda self, **k: None, "add_field": lambda *a, **k: None, "set_image": lambda *a, **k: None})
discord.abc = types.SimpleNamespace(Messageable=object)
discord.Message = type("Message", (), {})
discord.Thread = type("Thread", (), {})

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from game.battle_system import BattleSystem
from core.game_session import GameSession
from models.session_models import SessionPlayerModel

# Ensure colour helpers exist even if other tests modify the stub
discord.Color.dark_red = getattr(discord.Color, "dark_red", lambda: None)


class FakeCursor:
    def __init__(self, result):
        self.result = result

    def execute(self, sql, params=None):
        self.sql = sql

    def fetchone(self):
        if "SELECT hp" in self.sql:
            return self.result
        return None

    def close(self):
        pass


class FakeConnection:
    def __init__(self, result):
        self.result = result

    def cursor(self, dictionary=False):
        return FakeCursor(self.result)

    def close(self):
        pass


class FakeSessionManager:
    def __init__(self, session):
        self.session = session

    def get_session(self, thread_id):
        return self.session


class FakeEmbedManager:
    def __init__(self):
        self.buttons = None

    async def send_or_update_embed(self, *_, **kwargs):
        self.buttons = kwargs.get("buttons")
        return None


class FakeBot:
    def __init__(self, sm, em):
        self.sm = sm
        self.em = em

    def get_cog(self, name):
        return {"SessionManager": self.sm, "EmbedManager": self.em}.get(name)


class FakeFollowup:
    async def send(self, *a, **k):
        pass


class FakeInteraction:
    def __init__(self):
        self.channel = types.SimpleNamespace(id=1)
        self.response = types.SimpleNamespace(is_done=lambda: True)
        self.followup = FakeFollowup()


def _make_battle_system(monkeypatch, session, player_speed):
    discord.Color.dark_red = getattr(discord.Color, "dark_red", lambda: None)
    if not hasattr(discord, "Embed") or not hasattr(discord.Embed, "add_field"):
        discord.Embed = type(
            "Embed",
            (),
            {
                "__init__": lambda self, **_: None,
                "add_field": lambda *_, **__: None,
                "set_image": lambda *_, **__: None,
            },
        )
    else:
        def _add_field(self, *_, **__):
            return None

        def _set_image(self, *_, **__):
            return None

        discord.Embed.add_field = _add_field
        discord.Embed.set_image = _set_image
    sm = FakeSessionManager(session)
    em = FakeEmbedManager()
    bot = FakeBot(sm, em)
    bs = BattleSystem(bot)

    result = {
        "hp": 10,
        "max_hp": 10,
        "defense": 0,
        "attack_power": 0,
        "speed": player_speed,
    }

    monkeypatch.setattr(bs, "db_connect", lambda: FakeConnection(result))
    monkeypatch.setattr(SessionPlayerModel, "get_status_effects", lambda *a, **k: [])
    monkeypatch.setattr(bs, "_append_battle_log", lambda *a, **k: None)

    return bs, em


def test_player_turn_first_when_faster(monkeypatch):
    session = GameSession(1, 1, "1", 42)
    session.players = [42]
    session.current_turn = 42

    bs, em = _make_battle_system(monkeypatch, session, player_speed=15)

    interaction = FakeInteraction()
    enemy = {"enemy_id": 99, "enemy_name": "Goblin", "hp": 10, "max_hp": 10, "speed": 10}

    asyncio.run(bs.start_battle(interaction, 42, enemy))

    assert session.battle_state["active_combatant"] == "player"
    assert em.buttons[0][4] is False  # buttons enabled


def test_enemy_preemptive_when_faster(monkeypatch):
    session = GameSession(1, 1, "1", 42)
    session.players = [42]
    session.current_turn = 42

    bs, em = _make_battle_system(monkeypatch, session, player_speed=5)

    interaction = FakeInteraction()
    enemy = {"enemy_id": 99, "enemy_name": "Goblin", "hp": 10, "max_hp": 10, "speed": 12}

    called = False

    async def fake_enemy_turn(*_args, **_kwargs):
        nonlocal called
        called = True
        return None

    monkeypatch.setattr(bs, "enemy_turn", fake_enemy_turn)

    asyncio.run(bs.start_battle(interaction, 42, enemy))

    assert called is True
    assert session.battle_state["active_combatant"] == "enemy"
    assert em.buttons[0][4] is True  # buttons disabled while enemy acts
