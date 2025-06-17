import os
import sys
import pytest

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
            sorted_rows = sorted(
                self.conn.rows,
                key=lambda r: (r['play_time'], -r['enemies_defeated'])
            )
            self.result = [(r['score_id'],) for r in sorted_rows]
        elif sql.startswith("DELETE FROM high_scores"):
            ids = set(params)
            self.conn.rows = [r for r in self.conn.rows if r['score_id'] not in ids]
            self.result = None
        elif sql.startswith("SELECT * FROM high_scores"):
            order_clause = sql.split("ORDER BY",1)[1].split("LIMIT",1)[0].strip()
            if order_clause == "play_time ASC, enemies_defeated DESC":
                sorted_rows = sorted(
                    self.conn.rows,
                    key=lambda r: (r['play_time'], -r['enemies_defeated'])
                )
            else:
                col, direction = order_clause.split()
                rev = direction.upper() == 'DESC'
                sorted_rows = sorted(self.conn.rows, key=lambda r: r[col], reverse=rev)
            limit = params[0]
            self.result = [r.copy() for r in sorted_rows[:limit]]
        else:
            raise ValueError(f"Unhandled SQL: {sql}")

    def fetchall(self):
        return self.result or []

    def close(self):
        pass

class FakeConnection:
    def __init__(self):
        self.rows = []

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
    }

    for i in range(20):
        data = base_data.copy()
        data["player_name"] = f"P{i}"
        data["play_time"] = i
        assert high_score.record_score(data)

    worst = base_data.copy()
    worst["player_name"] = "Worst"
    worst["play_time"] = 9999

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
    }

    for i in range(5):
        data = base.copy()
        data["player_name"] = f"P{i}"
        data["play_time"] = i
        data["rooms_visited"] = i
        assert high_score.record_score(data)

    scores = high_score.fetch_scores(limit=5, sort_by="rooms_visited")
    rooms_list = [s["rooms_visited"] for s in scores]
    assert rooms_list == sorted(rooms_list, reverse=True)
