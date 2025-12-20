import os
import json
import logging
import mysql.connector

logger = logging.getLogger("Database")
logger.setLevel(logging.DEBUG)

def load_config():
    """
    Loads config.json from the project root (one directory up from this file).
    """
    script_dir = os.path.dirname(os.path.abspath(__file__))  # e.g. .../AdventureBot/models
    bot_root = os.path.dirname(script_dir)                   # e.g. .../AdventureBot
    config_path = os.path.join(bot_root, 'config.json')
    if not os.path.exists(config_path):
        logger.error("❌ Config file missing at %s", config_path)
        raise FileNotFoundError(f"Config file not found: {config_path}")
    with open(config_path, 'r') as f:
        return json.load(f)

config = load_config()
DB_CONFIG = config['mysql']

class Database:
    """
    A simple database connection helper that loads DB_CONFIG from config.json
    and provides a .get_connection() method returning a MySQL connector.
    """
    def __init__(self):
        self.config = DB_CONFIG

    def get_connection(self):
        try:
            conn = mysql.connector.connect(**self.config)
            return conn
        except mysql.connector.Error as err:
            logger.error("Database connection error in Database: %s", err)
            raise
