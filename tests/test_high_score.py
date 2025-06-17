import os
import sys
import types
import pytest

# Stub mysql module to satisfy models.database import
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


sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from game import high_score
from models.database import Database

class FakeCursor:
    def __init__(self, conn, dictionary=False):
        self.conn = conn
        self.dictionary = dictionary
        self.result = None

    def execute(self, sql, params=None):
        params = params or tuple()
        if sql.startswith("INSERT INTO high_scores"):
            columns = sql.split("(",1)[1].split(")",1)[0].split(',')
            row = dict(zip([c.strip() for c in columns], params))
            row['score_id'] = len(self.conn.rows) + 1
            self.conn.rows.append(row)
            self.result = None
        elif sql.startswith("SELECT score_id FROM high_scores"):
            rows = self.conn.rows
            if "WHERE guild_id=%s" in sql:
                guild_id = params[0]
                rows = [r for r in rows if r['guild_id'] == guild_id]
            rows = sorted(rows, key=lambda r: r['score_value'], reverse=True)
            self.result = [(r['score_id'],) for r in rows]
        elif sql.startswith("DELETE FROM high_scores"):
            guild_id = None
            if "AND guild_id=%s" in sql:
                guild_id = params[-1]
                ids = set(params[:-1])
            else:
                ids = set(params)
            self.conn.rows = [
                r for r in self.conn.rows
                if not (r['score_id'] in ids and (guild_id is None or r['guild_id'] == guild_id))
            ]
            self.result = None
        elif sql.startswith("SELECT * FROM high_scores"):
            rows = self.conn.rows
            order_clause = sql.split("ORDER BY",1)[1].split("LIMIT",1)[0].strip()
            if "WHERE guild_id=%s" in sql:
                guild_id = params[0]
                rows = [r for r in rows if r['guild_id'] == guild_id]
                limit = params[1]
            else:
                limit = params[0]
            if order_clause == "score_value DESC":
                sorted_rows = sorted(rows, key=lambda r: r['score_value'], reverse=True)
            else:
                col, direction = order_clause.split()
                rev = direction.upper() == 'DESC'
                sorted_rows = sorted(rows, key=lambda r: r[col], reverse=rev)
            self.result = [r.copy() for r in sorted_rows[:limit]]
        elif sql.startswith("SELECT guild_id, difficulty, created_at FROM sessions"):
            sid = params[0]
            for r in self.conn.sessions:
                if r["session_id"] == sid:
                    self.result = r.copy()
                    break
            else:
                self.result = None
        elif sql.strip().startswith("SELECT p.username"):
            sid, pid = params
            for r in self.conn.players:
                if r["session_id"] == sid and r["player_id"] == pid:
                    self.result = r.copy()
                    break
            else:
                self.result = None
        else:
            raise ValueError(f"Unhandled SQL: {sql}")

    def fetchall(self):
        return self.result or []

    def fetchone(self):
        if isinstance(self.result, list):
            return self.result[0] if self.result else None
        return self.result

    def close(self):
        pass

class FakeConnection:
    def __init__(self):
        self.rows = []
        self.sessions = []
        self.players = []

    def cursor(self, dictionary=False):
        return FakeCursor(self, dictionary)

    def commit(self):
        pass

    def close(self):
        pass

def test_record_score_prunes_to_20(monkeypatch):
    conn = FakeConnection()

    def fake_get_connection(self):
        return conn

    monkeypatch.setattr(Database, "get_connection", fake_get_connection)

    base_data = {
        "player_name": "Player",
        "guild_id": 1,
        "player_level": 1,
        "player_class": "Warrior",
        "gil": 0,
        "enemies_defeated": 0,
        "bosses_defeated": 0,
        "score_value": 0,
    }

    for i in range(20):
        data = base_data.copy()
        data["player_name"] = f"P{i}"
        data["score_value"] = i
        assert high_score.record_score(data)

    worst = base_data.copy()
    worst["player_name"] = "Worst"
    worst["score_value"] = -1

    assert high_score.record_score(worst)

    scores = high_score.fetch_scores(limit=25)
    names = [s["player_name"] for s in scores]
    assert len(names) == 20
    assert "Worst" not in names


def test_fetch_scores_rooms_visited_sort(monkeypatch):
    conn = FakeConnection()

    def fake_get_connection(self):
        return conn

    monkeypatch.setattr(Database, "get_connection", fake_get_connection)

    base = {
        "player_name": "P",
        "guild_id": 1,
        "player_level": 1,
        "player_class": "Mage",
        "gil": 0,
        "enemies_defeated": 0,
        "bosses_defeated": 0,
        "score_value": 0,
    }

    for i in range(5):
        data = base.copy()
        data["player_name"] = f"P{i}"
        data["score_value"] = i
        data["rooms_visited"] = i
        assert high_score.record_score(data)

    scores = high_score.fetch_scores(limit=5, sort_by="rooms_visited")
    rooms_list = [s["rooms_visited"] for s in scores]
    assert rooms_list == sorted(rooms_list, reverse=True)


def test_per_guild_pruning_and_fetch(monkeypatch):
    conn = FakeConnection()

    def fake_get_connection(self):
        return conn

    monkeypatch.setattr(Database, "get_connection", fake_get_connection)

    base = {
        "player_name": "P",
        "guild_id": 1,
        "player_level": 1,
        "player_class": "Rogue",
        "gil": 0,
        "enemies_defeated": 0,
        "bosses_defeated": 0,
        "score_value": 0,
    }

    # Populate two guilds with 20 scores each
    for g in (1, 2):
        for i in range(20):
            data = base.copy()
            data["player_name"] = f"G{g}P{i}"
            data["guild_id"] = g
            data["score_value"] = i
            assert high_score.record_score(data)

    # Add a low score to guild 1 and ensure it is pruned
    low = base.copy()
    low["player_name"] = "Low"
    low["guild_id"] = 1
    low["score_value"] = -5
    assert high_score.record_score(low)

    g1_scores = high_score.fetch_scores(limit=25, guild_id=1)
    g2_scores = high_score.fetch_scores(limit=25, guild_id=2)

    assert len(g1_scores) == 20
    assert len(g2_scores) == 20
    assert all(r["guild_id"] == 1 for r in g1_scores)
    assert all(r["guild_id"] == 2 for r in g2_scores)
    assert all(r["player_name"] != "Low" for r in g1_scores)


def test_compute_score_and_qualification(monkeypatch):
    conn = FakeConnection()

    def fake_get_connection(self):
        return conn

    monkeypatch.setattr(Database, "get_connection", fake_get_connection)

    conn.sessions.append({
        "session_id": 1,
        "guild_id": 1,
        "difficulty": "Easy",
        "created_at": "2025",
    })
    conn.players.append({
        "session_id": 1,
        "player_id": 10,
        "username": "Hero",
        "level": 2,
        "gil": 50,
        "enemies_defeated": 2,
        "bosses_defeated": 1,
        "rooms_visited": 5,
        "class_name": "Warrior",
    })

    base = {
        "player_name": "X",
        "guild_id": 1,
        "player_level": 1,
        "player_class": "Mage",
        "gil": 0,
        "enemies_defeated": 0,
        "bosses_defeated": 0,
        "score_value": 0,
    }
    for i in range(5):
        d = base.copy()
        d["player_name"] = f"P{i}"
        d["score_value"] = i
        assert high_score.record_score(d)

    from game.session_manager import SessionManager

    sm = SessionManager(None)
    sm.db_connect = lambda: conn

    data = sm.compute_player_score_data(1, 10)
    assert data["score_value"] == 2 + 1 * 5 + 5

    top = high_score.fetch_scores(guild_id=1)
    qualifies = len(top) < 20 or data["score_value"] >= top[-1]["score_value"]
    assert qualifies


class FakeResp:
    def __init__(self):
        self._done = False

    def is_done(self):
        return self._done

    async def send_message(self, *args, **kwargs):
        self._done = True


def test_high_score_yes_no_flow(monkeypatch):
    conn = FakeConnection()

    def fake_get_connection(self):
        return conn

    monkeypatch.setattr(Database, "get_connection", fake_get_connection)

    from core.game_session import GameSession

    session = GameSession(1, 1, "123", 1)

    data = {
        "player_name": "Hero",
        "player_class": "Warrior",
        "gil": 0,
        "enemies_defeated": 1,
        "bosses_defeated": 0,
        "rooms_visited": 2,
        "score_value": 3,
        "guild_id": 1,
        "player_level": 1,
        "difficulty": "Easy",
    }

    session.pending_high_score[42] = {"data": data}

    # Simulate "Yes"
    assert high_score.record_score(session.pending_high_score[42]["data"])
    session.pending_high_score.pop(42, None)
    assert len(conn.rows) == 1
    assert 42 not in session.pending_high_score

    # Simulate "No"
    session.pending_high_score[42] = {"data": data}
    session.pending_high_score.pop(42, None)
    assert len(conn.rows) == 1
