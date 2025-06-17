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
    def get_high_scores(limit: int = 10, sort_by: str = "score_value"):
        """Retrieve high score rows ordered by the given stat."""
        db = Database()
        conn = db.get_connection()
        cursor = conn.cursor(dictionary=True)
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
        try:
            cursor.execute(
                f"SELECT * FROM high_scores ORDER BY {order_clause} LIMIT %s",
                (limit,),
            )
            return cursor.fetchall()
        except Exception as e:
            logger.error("Error retrieving high scores: %s", e, exc_info=True)
            return []
        finally:
            cursor.close()
            conn.close()
