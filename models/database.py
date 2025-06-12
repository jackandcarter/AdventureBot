import logging
import mysql.connector
import aiomysql
from utils.helpers import load_config

logger = logging.getLogger("Database")
logger.setLevel(logging.DEBUG)

config = load_config()
DB_CONFIG = config.get('mysql', {})

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


class AsyncDatabase:
    """Asynchronous counterpart using aiomysql."""

    def __init__(self):
        self.config = DB_CONFIG

    async def get_connection(self):
        try:
            cfg = self.config.copy()
            if "database" in cfg:
                cfg["db"] = cfg.pop("database")
            conn = await aiomysql.connect(**cfg, autocommit=True)
            return conn
        except aiomysql.MySQLError as err:
            logger.error("Async DB connection error: %s", err)
            raise
