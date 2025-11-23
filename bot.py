"""AdventureBot Discord entry point.

This module boots the bot, loads configuration and extensions and
starts the Discord client used for gameplay.
"""

# pylint: disable=import-error

import asyncio
import importlib
import logging
import os
import subprocess
import sys

import discord
from discord.ext import commands

# ---------------------
#   LOGGING SETUP
# ---------------------
logging.basicConfig(
    level=logging.WARNING,   # Global: only show warnings and errors by default
    format='[%(asctime)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger("AdventureBot")
logger.setLevel(logging.DEBUG)  # Your bot logs are still DEBUG

# --- LOGGING VERBOSITY CLEANUP ---
logging.getLogger("discord").setLevel(logging.WARNING)
logging.getLogger("discord.gateway").setLevel(logging.WARNING)
logging.getLogger("discord.http").setLevel(logging.WARNING)
from utils.helpers import get_bot_root, load_config
from utils.mail_client import MailClient

# ---------------------
#   CONFIG LOADING
# ---------------------
config = load_config()
TOKEN = config.get('discord_token')
DB_CONFIG = config.get('mysql', {})
MAIL_CONFIG = config.get('mail', {})

# ---------------------
#   DATABASE SETUP
# ---------------------
def run_database_setup():
    """Run the database setup helper script.

    Ensures all database tables exist before the bot begins processing
    events. The bot exits if the setup script cannot be executed.
    """
    bot_root = get_bot_root()
    db_setup_path = os.path.join(bot_root, 'database', 'database_setup.py')
    if not os.path.exists(db_setup_path):
        logger.error("\u274c Database setup script not found at %s. Exiting...", db_setup_path)
        sys.exit(1)
    logger.info("\U0001f501 Running database setup script at %s", db_setup_path)
    result = subprocess.run(["python3", db_setup_path], check=False)
    if result.returncode == 0:
        logger.info("\u2705 Database setup complete.")
    else:
        logger.error("\u274c Database setup encountered an error. Exiting bot.")
        sys.exit(1)


def log_mail_health():
    """Verify mail connectivity for password reset and verification flows."""

    if not MAIL_CONFIG or not MAIL_CONFIG.get("host"):
        logger.info("✉️ Mail configuration not provided; skipping mail health check.")
        return

    mail_client = MailClient(MAIL_CONFIG)
    mail_client.health_check(logger)

# ---------------------
#   BOT INTENTS
# ---------------------
intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True

# ---------------------
#   BOT INITIALIZATION
# ---------------------
bot = commands.Bot(command_prefix="/", intents=intents)

@bot.event
async def on_ready():
    """Handle the :code:`on_ready` event and sync slash commands."""
    logger.info(
        "\U0001f916 %s is online and ready! Connected to %s server(s).",
        bot.user.name,
        len(bot.guilds),
    )
    await bot.wait_until_ready()
    if not bot.application_id:
        bot.application_id = (await bot.application_info()).id
    try:
        await bot.tree.sync()
        synced_guilds = [guild.id for guild in bot.guilds]
        logger.info(
            "\u2705 Slash commands synced for %s guilds: %s",
            len(synced_guilds),
            synced_guilds,
        )
    except Exception as e:
        logger.error("\u274c Failed to sync slash commands: %s", e)
    await bot.change_presence(activity=discord.Game(name="Dungeon Adventure!"))

@bot.event
async def on_shard_connect(shard_id):
    """Log when a new Discord shard establishes a connection."""
    logger.debug("Shard %s connected.", shard_id)

# ---------------------
#   DYNAMIC COG LOADING
# ---------------------
def discover_cogs(root_dirs):
    """Return a list of cog modules found in the given directories.

    Parameters
    ----------
    root_dirs: list[str]
        Directories relative to the bot root that should be scanned for
        extensions.
    """
    cogs = []
    bot_root = get_bot_root()
    for directory in root_dirs:
        dir_path = os.path.join(bot_root, directory)
        if not os.path.exists(dir_path):
            logger.debug("Directory not found (skipping): %s", dir_path)
            continue
        for root, _, files in os.walk(dir_path):
            for file in files:
                if not file.endswith(".py") or file == "__init__.py":
                    continue
                rel_path = os.path.relpath(os.path.join(root, file), bot_root)
                module_path = rel_path[:-3].replace(os.sep, ".")
                try:
                    mod = importlib.import_module(module_path)
                except Exception as e:
                    logger.error("Error importing module %s: %s", module_path, e)
                    continue
                if hasattr(mod, "setup") and callable(mod.setup):
                    cogs.append(module_path)
                else:
                    logger.debug("Skipping non-cog module: %s", module_path)
    return cogs

# Only include directories that actually contain cogs.
# Our design supports multi-session management and vendor data isolation.
cog_directories = ["game", "hub"]
modules = discover_cogs(cog_directories)
logger.info("Discovered cog modules: %s", modules)

# ---------------------
#   MAIN BOT START
# ---------------------
async def main():
    """Start the bot and load all discovered extensions."""
    run_database_setup()
    log_mail_health()

    if not TOKEN:
        logger.error("\u274c Discord token not found in config. Exiting...")
        sys.exit(1)

    for module in modules:
        try:
            await bot.load_extension(module)
            logger.info("\u2705 Loaded module: %s", module)
        except Exception as e:
            logger.error("\u274c Failed to load module '%s': %s", module, e)

    # Start the bot using an asynchronous context for proper cleanup.
    async with bot:
        await bot.start(TOKEN)

if __name__ == '__main__':
    asyncio.run(main())
