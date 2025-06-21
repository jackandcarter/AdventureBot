import os
import sys
import types
import asyncio

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
discord.Color = types.SimpleNamespace(red=lambda: None)
discord.Interaction = type("Interaction", (), {})
discord.abc = types.SimpleNamespace(Messageable=object)

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from game.atb_manager import ATBManager
from core.game_session import GameSession
from models import session_models

class DummyBS:
    def __init__(self):
        self.ticks = 0
    async def on_tick(self, session):
        self.ticks += 1
    async def on_player_ready(self, *a, **k):
        pass
    async def on_enemy_ready(self, *a, **k):
        pass


def run_loop(speed, duration=0.15):
    session = GameSession(1, 1, "1", 1)
    session.players = [1]
    session.current_turn = 1
    session.atb_maxes = {1: 5}
    session.enemy_atb_max = 5
    session.status_effects = {1: []}
    session.battle_state = {"player_effects": [], "enemy_effects": []}
    session.current_enemy = {"speed": speed}

    bs = DummyBS()
    manager = ATBManager(tick_ms=10, update_interval=0.05)
    session_models.SessionPlayerModel.get_player_states = staticmethod(lambda sid: [{"player_id": 1, "speed": speed}])

    async def _run():
        task = asyncio.create_task(manager._tick_loop(session, bs))
        await asyncio.sleep(duration)
        session.battle_state = None
        await asyncio.sleep(0.02)
        task.cancel()
        return bs.ticks
    return asyncio.run(_run())


def test_throttle_reduces_ticks():
    slow = run_loop(0)
    fast = run_loop(50)
    assert slow < fast
    assert slow <= 3
