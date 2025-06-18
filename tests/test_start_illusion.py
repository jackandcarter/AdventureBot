import sys
import types
import random
import os
import pytest

# Stub mysql and discord modules like other tests
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

discord = sys.modules["discord"]
discord.InteractionType = types.SimpleNamespace(component=1)
discord.ui = types.SimpleNamespace(View=object, Button=object)
discord.ui.button = lambda *a, **k: (lambda f: f)
discord.ButtonStyle = types.SimpleNamespace(primary=1, secondary=2, success=3, danger=4, blurple=5)
discord.Color = types.SimpleNamespace(purple=lambda: None)
discord.Interaction = type("Interaction", (), {})

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import types as typ

from game.game_master import GameMaster
from core.game_session import GameSession

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
    def close(self):
        pass

class FakeSessionManager:
    def __init__(self, session):
        self.session = session
    def get_session(self, thread_id):
        return self.session

class FakeEmbedManager:
    def __init__(self):
        self.called_with = None

    async def send_illusion_crystal_embed(self, *a, **k):
        self.called_with = ("crystal", a, k)

    async def send_illusion_embed(self, *a, **k):
        self.called_with = ("embed", a, k)

    async def send_illusion_count_embed(self, *a, **k):
        self.called_with = ("count", a, k)

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
        self.channel = typ.SimpleNamespace(id=1)
        self.followup = FakeFollowup()
        self.user = typ.SimpleNamespace(id=42, display_name="Hero")

def test_start_illusion_challenge_order(monkeypatch):
    session = GameSession(1, 1, "1", 1)
    sm = FakeSessionManager(session)
    em = FakeEmbedManager()
    bot = FakeBot(sm, em)
    gm = GameMaster(bot)

    crystals = [
        {"element_id": 1, "element_name": "Fire", "name": "F", "description": "", "image_url": ""},
        {"element_id": 2, "element_name": "Ice", "name": "I", "description": "", "image_url": ""},
        {"element_id": 3, "element_name": "Holy", "name": "H", "description": "", "image_url": ""},
    ]

    monkeypatch.setattr(gm, "db_connect", lambda: FakeConnection(crystals))
    monkeypatch.setattr(random, "choice", lambda seq: "elemental_crystal")
    def fake_randint(a, b):
        return 4 if (a, b) == (2, 6) else 0

    monkeypatch.setattr(random, "randint", fake_randint)

    interaction = FakeInteraction()
    import asyncio
    asyncio.run(gm.start_illusion_challenge(interaction, {"description": ""}))
    order = session.game_state.get("illusion_crystal_order", [])
    assert 2 <= len(order) <= 6


def test_start_illusion_guess_room(monkeypatch):
    session = GameSession(1, 1, "1", 1)
    sm = FakeSessionManager(session)
    em = FakeEmbedManager()
    bot = FakeBot(sm, em)
    gm = GameMaster(bot)

    choices = ["guess_room", "illusion_enemy"]

    def fake_choice(seq):
        return choices.pop(0)

    monkeypatch.setattr(random, "choice", fake_choice)
    monkeypatch.setattr(gm, "db_connect", lambda: FakeConnection([{"image_url": "dark.png"}]))

    interaction = FakeInteraction()
    import asyncio
    asyncio.run(gm.start_illusion_challenge(interaction, {"description": ""}))

    challenge = session.game_state.get("illusion_challenge")
    assert challenge["type"] == "guess_room"
    assert challenge["answer"] == "illusion_enemy"
    assert em.called_with and em.called_with[0] == "embed"


def test_start_illusion_enemy_count(monkeypatch):
    session = GameSession(1, 1, "1", 1)
    sm = FakeSessionManager(session)
    em = FakeEmbedManager()
    bot = FakeBot(sm, em)
    gm = GameMaster(bot)

    choices = ["enemy_count", "illusion_treasure"]

    def fake_choice(seq):
        return choices.pop(0)

    monkeypatch.setattr(random, "choice", fake_choice)
    monkeypatch.setattr(random, "randint", lambda a, b: 1)

    rows = [
        {"enemies_defeated": 2},
        {"image_url": "dark.png"},
    ]

    monkeypatch.setattr(gm, "db_connect", lambda: FakeConnection(rows))

    interaction = FakeInteraction()
    import asyncio
    asyncio.run(gm.start_illusion_challenge(interaction, {"description": ""}))

    challenge = session.game_state.get("illusion_challenge")
    assert challenge["type"] == "enemy_count"
    assert challenge["answer"] == 2
    assert em.called_with and em.called_with[0] == "count"
