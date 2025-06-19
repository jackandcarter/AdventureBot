import os
import sys
import types
import asyncio

import pytest

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
discord.Color = types.SimpleNamespace(purple=lambda: None)
discord.Interaction = type("Interaction", (), {})
discord.Embed = type("Embed", (), {"__init__": lambda self, **k: None})

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from game.game_master import GameMaster
from core.game_session import GameSession
from models import session_models


class FakeCursor:
    def __init__(self, rows):
        self.rows = rows
        self.index = 0

    def execute(self, sql, params=None):
        pass

    def fetchall(self):
        return self.rows

    def fetchone(self):
        if isinstance(self.rows, list):
            if self.index < len(self.rows):
                res = self.rows[self.index]
                self.index += 1
                return res
            return None
        return self.rows

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        pass

    def close(self):
        pass


class FakeConnection:
    def __init__(self, rows):
        self.rows = rows

    def cursor(self, dictionary=False):
        return FakeCursor(self.rows)

    def commit(self):
        pass

    def close(self):
        pass


class FakeSessionManager:
    def __init__(self, session):
        self.session = session
        self.called_with = None

    def get_session(self, thread_id):
        return self.session

    def set_initial_turn(self, session_id):
        self.called_with = session_id
        self.session.current_turn = self.session.owner_id


class FakeDungeonGenerator:
    async def generate_dungeon_for_session(self, *a, **k):
        pass


class FakeEmbedManager:
    async def send_or_update_embed(self, *a, **k):
        pass

    async def send_class_selection_embed(self, *a, **k):
        pass


class FakeHubManager:
    async def cleanup_lfg_posts(self, *a, **k):
        pass


class FakeBot:
    def __init__(self, sm, dg, em=None, hub=None):
        self._cogs = {
            "SessionManager": sm,
            "DungeonGenerator": dg,
            "EmbedManager": em,
            "HubManager": hub,
        }

    def get_cog(self, name):
        return self._cogs.get(name)


class FakeResponse:
    def __init__(self):
        self._done = False

    def is_done(self):
        return self._done

    async def defer(self):
        self._done = True


class FakeFollowup:
    async def send(self, *a, **k):
        pass


class FakeInteraction:
    def __init__(self):
        self.channel = types.SimpleNamespace(id=1)
        self.response = FakeResponse()
        self.followup = FakeFollowup()
        self.user = types.SimpleNamespace(id=42, display_name="Hero")
        self.data = {}
        self.type = discord.InteractionType.component
        self.id = 123456789


def test_initial_turn_after_intro(monkeypatch):
    session = GameSession(1, 1, "1", 42)
    session.current_turn = None
    sm = FakeSessionManager(session)
    dg = FakeDungeonGenerator()
    em = FakeEmbedManager()
    bot = FakeBot(sm, dg, em)
    gm = GameMaster(bot)

    conns = [
        FakeConnection([{"difficulty": "Easy"}]),
        FakeConnection([{"floor_id": 1}]),
        FakeConnection([]),
        FakeConnection([{"room_id": 1}]),
    ]

    def fake_db_connect():
        return conns.pop(0)

    monkeypatch.setattr(gm, "db_connect", fake_db_connect)
    monkeypatch.setattr(gm, "append_game_log", lambda *a, **k: None)

    async def _noop(*a, **k):
        return None

    monkeypatch.setattr(gm, "update_permanent_discovered_room", _noop)
    monkeypatch.setattr(gm, "update_room_view", _noop)

    interaction = FakeInteraction()
    asyncio.run(gm.finish_intro_and_generate(interaction, 1))

    assert sm.called_with == session.session_id
    assert session.current_turn == session.owner_id


def test_initial_turn_after_all_join(monkeypatch):
    session = GameSession(1, 1, "1", 42)
    session.players = [42, 99]
    session.current_turn = None
    sm = FakeSessionManager(session)
    dg = FakeDungeonGenerator()
    em = FakeEmbedManager()
    hub = FakeHubManager()
    bot = FakeBot(sm, dg, em, hub)
    gm = GameMaster(bot)

    monkeypatch.setattr(session_models.SessionModel, "is_owner", lambda sid, pid: pid == 42)
    monkeypatch.setattr(session_models.SessionPlayerModel, "get_players", lambda sid: session.players)
    monkeypatch.setattr(session_models.SessionModel, "update_num_players", lambda sid, n: None)

    interaction = FakeInteraction()
    interaction.data = {"custom_id": "start_game"}

    asyncio.run(gm.on_interaction(interaction))

    assert sm.called_with == session.session_id
    assert session.current_turn == session.owner_id

