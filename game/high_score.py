import logging
from typing import Any, Dict, List

from models.database import Database

logger = logging.getLogger("HighScore")
logger.setLevel(logging.DEBUG)


def record_score(data: Dict[str, Any]) -> bool:
    """Insert a new record into the ``high_scores`` table.

    Parameters
    ----------
    data: dict
        Mapping of column names to values. Keys should match columns in the
        ``high_scores`` table.

    Returns
    -------
    bool
        ``True`` if the insert succeeded, ``False`` otherwise.
    """
    db = Database()
    conn = db.get_connection()
    cursor = conn.cursor()
    try:
        if not data:
            logger.error("record_score called with empty data")
            return False

        columns = ",".join(data.keys())
        placeholders = ",".join(["%s"] * len(data))
        values = tuple(data.values())
        sql = f"INSERT INTO high_scores ({columns}) VALUES ({placeholders})"
        cursor.execute(sql, values)
        conn.commit()

        cursor.execute(
            "SELECT score_id FROM high_scores WHERE guild_id=%s "
            "ORDER BY score_value DESC",
            (data.get("guild_id"),),
        )
        ids = [row[0] for row in cursor.fetchall()]
        if len(ids) > 20:
            extras = ids[20:]
            placeholders_del = ",".join(["%s"] * len(extras))
            del_sql = (
                f"DELETE FROM high_scores WHERE score_id IN ({placeholders_del}) "
                "AND guild_id=%s"
            )
            cursor.execute(del_sql, tuple(extras) + (data.get("guild_id"),))
            conn.commit()
        return True
    except Exception as e:  # pylint: disable=broad-except
        logger.error("Error recording score: %s", e, exc_info=True)
        return False
    finally:
        cursor.close()
        conn.close()


def fetch_scores(
    limit: int = 20, sort_by: str = "score_value", guild_id: int | None = None
) -> List[Dict[str, Any]]:
    """Fetch high score rows.

    Parameters
    ----------
    limit: int, optional
        Maximum number of rows to return. Default ``20``.
    sort_by: str, optional
        Column to sort by. Defaults to ``"score_value"`` which sorts by the
        computed RPG score. Other fields sort descending by value.

    Returns
    -------
    list[dict]
        List of score rows. Returns an empty list if any error occurs.
    """
    valid_columns = {
        "score_value",
        "enemies_defeated",
        "bosses_defeated",
        "gil",
        "player_level",
        "rooms_visited",
    }
    order_clause = "score_value DESC"
    if sort_by in valid_columns and sort_by != "score_value":
        order_clause = f"{sort_by} DESC"

    db = Database()
    conn = db.get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        sql = "SELECT * FROM high_scores"
        params: List[Any] = []
        if guild_id is not None:
            sql += " WHERE guild_id=%s"
            params.append(guild_id)
        sql += f" ORDER BY {order_clause} LIMIT %s"
        params.append(limit)
        cursor.execute(sql, tuple(params))
        return cursor.fetchall()
    except Exception as e:  # pylint: disable=broad-except
        logger.error("Error fetching high scores: %s", e, exc_info=True)
        return []
    finally:
        cursor.close()
        conn.close()
