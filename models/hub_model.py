import json
import logging
from models.database import Database

logger = logging.getLogger("HubModel")
logger.setLevel(logging.DEBUG)

class HubModel:
    @staticmethod
    def get_main_hub_config():
        """
        Retrieves the main hub embed configuration from the 'hub_embeds' table 
        where embed_type is 'main'. Returns a dictionary of values if found,
        otherwise returns fallback defaults.
        """
        db = Database()
        conn = db.get_connection()
        cursor = conn.cursor(dictionary=True)
        try:
            sql = "SELECT * FROM hub_embeds WHERE embed_type = 'main' LIMIT 1"
            cursor.execute(sql)
            result = cursor.fetchone()
            if result:
                return result
            else:
                # Fallback configuration if no row is found.
                return {
                    "title": "Welcome to Dungeon Adventure!",
                    "description": "Select an option below:",
                    "image_url": "https://yourdomain.com/path/to/large_logo.jpg",
                    "text_field": "Your journey starts here."
                }
        except Exception as e:
            logger.error("Error retrieving main hub config: %s", e, exc_info=True)
            return {}
        finally:
            cursor.close()
            conn.close()

    @staticmethod
    def get_tutorial_steps():
        """
        Retrieves tutorial steps from the 'hub_embeds' table where embed_type is 'tutorial',
        ordered by the 'step_order' column. Returns a list of dictionaries.
        """
        db = Database()
        conn = db.get_connection()
        cursor = conn.cursor(dictionary=True)
        try:
            sql = "SELECT * FROM hub_embeds WHERE embed_type = 'tutorial' ORDER BY step_order ASC"
            cursor.execute(sql)
            steps = cursor.fetchall()
            return steps
        except Exception as e:
            logger.error("Error retrieving tutorial steps: %s", e, exc_info=True)
            return []
        finally:
            cursor.close()
            conn.close()

    @staticmethod
    def get_high_scores(
        guild_id: int | None = None,
        sort_key: str = "enemies_defeated",
        limit: int = 20
    ):
        """
        Retrieves the top high scores from the 'high_scores' table for a guild,
        ordered by the requested metric and completion time.
        Returns a list of dictionaries.
        """
        sort_options = {
            "enemies_defeated": "DESC",
            "rooms_visited": "DESC",
            "items_found": "DESC",
            "player_level": "DESC",
            "gil": "DESC",
            "play_time": "ASC",
            "completed_at": "DESC"
        }
        db = Database()
        conn = db.get_connection()
        cursor = conn.cursor(dictionary=True)
        try:
            cursor.execute("SHOW COLUMNS FROM high_scores")
            available_columns = {row["Field"] for row in cursor.fetchall()}
            if sort_key not in sort_options or sort_key not in available_columns:
                sort_key = "enemies_defeated"
            sort_direction = sort_options[sort_key]

            where_clause = ""
            params = []
            if guild_id is not None:
                where_clause = "WHERE guild_id = %s"
                params.append(guild_id)

            sql = (
                f"SELECT * FROM high_scores "
                f"{where_clause} "
                f"ORDER BY {sort_key} {sort_direction}, completed_at DESC "
                f"LIMIT %s"
            )
            params.append(limit)
            cursor.execute(sql, params)
            scores = cursor.fetchall()
            return scores
        except Exception as e:
            logger.error("Error retrieving high scores: %s", e, exc_info=True)
            return []
        finally:
            cursor.close()
            conn.close()
