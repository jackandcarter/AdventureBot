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
    def get_high_scores():
        """
        Retrieves the top 10 high scores from the 'high_scores' table,
        ordered primarily by play_time ascending and then enemies_defeated descending.
        Returns a list of dictionaries.
        """
        db = Database()
        conn = db.get_connection()
        cursor = conn.cursor(dictionary=True)
        try:
            sql = "SELECT * FROM high_scores ORDER BY play_time ASC, enemies_defeated DESC LIMIT 10"
            cursor.execute(sql)
            scores = cursor.fetchall()
            return scores
        except Exception as e:
            logger.error("Error retrieving high scores: %s", e, exc_info=True)
            return []
        finally:
            cursor.close()
            conn.close()
