import types
import sys
import random
import pytest
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Stub discord and mysql modules
sys.modules.setdefault("mysql", types.ModuleType("mysql"))
sys.modules.setdefault("mysql.connector", types.ModuleType("connector"))
sys.modules.setdefault("aiomysql", types.ModuleType("aiomysql"))
sys.modules["mysql"].connector = sys.modules["mysql.connector"]
conn_mod = sys.modules["mysql.connector"]
conn_mod.connection = types.SimpleNamespace(MySQLConnection=object)
conn_mod.Error = Exception
sys.modules.setdefault("discord", types.ModuleType("discord"))
sys.modules.setdefault("discord.ext", types.ModuleType("ext"))
ext_mod = sys.modules["discord.ext"]
ext_mod.commands = types.ModuleType("commands")
sys.modules["discord.ext.commands"] = ext_mod.commands
ext_mod.commands.Cog = type("Cog", (), {"listener": staticmethod(lambda *a, **k: (lambda f: f))})
ext_mod.commands.Bot = object
ext_mod.commands.command = lambda *a, **k: (lambda f: f)
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
discord.Thread = type("Thread", (), {})
discord.Member = type("Member", (), {})
discord.Guild = type("Guild", (), {})
discord.Message = type("Message", (), {})
discord.TextChannel = type("TextChannel", (), {})
discord.ChannelType = types.SimpleNamespace(private_thread=1)
discord.Embed = type("Embed", (), {"__init__": lambda self, **k: None, "add_field": lambda *a, **k: None, "set_footer": lambda *a, **k: None, "set_image": lambda *a, **k: None})

discord.Interaction = type("Interaction", (), {"channel": type("Ch", (), {"id": 1})(), "followup": type("F", (), {"send": lambda *a, **k: None})(), "response": type("R", (), {"is_done": lambda self: True})()})

def test_tables_include_crystal_templates():
    from database import database_setup as ds

    assert 'crystal_templates' in ds.TABLES
    idx = ds.TABLE_ORDER.index('room_templates')
    assert ds.TABLE_ORDER[idx + 1] == 'crystal_templates'

def test_start_illusion_challenge_fetches_crystals(monkeypatch):
    ext_mod.commands.Cog = type("Cog", (), {"listener": staticmethod(lambda *a, **k: (lambda f: f))})
    discord.Interaction = type("Interaction", (), {"channel": type("Ch", (), {"id": 1})(), "followup": type("F", (), {"send": lambda *a, **k: None})(), "response": type("R", (), {"is_done": lambda self: True})()})
    from game import game_master
    from core.game_session import GameSession

    bot = types.SimpleNamespace(get_cog=lambda name: None)
    gm = game_master.GameMaster(bot)
    session = GameSession(1, 1, "t", 1)

    sm = types.SimpleNamespace(get_session=lambda cid: session)
    async def dummy(*a, **k):
        return None
    em = types.SimpleNamespace(send_illusion_crystal_embed=dummy,
                               send_illusion_embed=dummy)

    def fake_get_cog(name):
        return {'SessionManager': sm, 'EmbedManager': em}.get(name)

    bot.get_cog = fake_get_cog

    class FakeCursor:
        def execute(self, *a, **k):
            pass
        def fetchall(self):
            return [
                {"template_id":1,"element_id":1,"name":"Fire","description":"D","image_url":"U"},
                {"template_id":2,"element_id":2,"name":"Ice","description":"D","image_url":"U"},
            ]
        def close(self):
            pass
        def __enter__(self):
            return self
        def __exit__(self, exc_type, exc, tb):
            pass
    class FakeConn:
        def cursor(self, dictionary=True):
            return FakeCursor()
        def close(self):
            pass
    monkeypatch.setattr(gm, 'db_connect', lambda: FakeConn())
    monkeypatch.setattr(random, 'choice', lambda seq: 'elemental_crystal')
    interaction = discord.Interaction()
    pytest.run_coroutine = lambda coro: coro
    # call
    import asyncio
    loop = asyncio.new_event_loop()
    loop.run_until_complete(gm.start_illusion_challenge(interaction, {}))
    loop.close()
    assert session.game_state.get('illusion_crystal_order')
    assert session.game_state['illusion_challenge']['type'] == 'elemental_crystal'

