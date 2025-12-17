import discord
from discord.ext import commands
import subprocess
import os
import json
import logging
import asyncio
import importlib

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

# ---------------------
#   CONFIG LOADING
# ---------------------
def get_bot_root():
    """Return the absolute path to the directory containing this script (bot.py)."""
    return os.path.dirname(os.path.abspath(__file__))

CONFIG_PATH = os.path.join(get_bot_root(), 'config.json')

def load_config():
    try:
        with open(CONFIG_PATH, 'r') as f:
            config_data = json.load(f)
            logger.debug("Configuration loaded successfully.")
            return config_data
    except Exception as e:
        logger.error(f"❌ Failed to load config from {CONFIG_PATH}: {e}")
        exit(1)

config = load_config()
TOKEN = config.get('discord_token')
DB_CONFIG = config.get('mysql', {})

# ---------------------
#   DATABASE SETUP
# ---------------------
def run_database_setup():
    """Runs database_setup.py from the database/ folder to ensure tables are ready."""
    bot_root = get_bot_root()
    db_setup_path = os.path.join(bot_root, 'database', 'database_setup.py')
    if not os.path.exists(db_setup_path):
        logger.error(f"❌ Database setup script not found at {db_setup_path}. Exiting...")
        exit(1)
    logger.info(f"🔄 Running database setup script at {db_setup_path}")
    result = subprocess.run(["python3", db_setup_path])
    if result.returncode == 0:
        logger.info("✅ Database setup complete.")
    else:
        logger.error("❌ Database setup encountered an error. Exiting bot.")
        exit(1)

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
    logger.info(f'🤖 {bot.user.name} is online and ready! Connected to {len(bot.guilds)} server(s).')
    await bot.wait_until_ready()
    if not bot.application_id:
        bot.application_id = (await bot.application_info()).id
    try:
        await bot.tree.sync()
        synced_guilds = [guild.id for guild in bot.guilds]
        logger.info(f"✅ Slash commands synced for {len(synced_guilds)} guilds: {synced_guilds}")
    except Exception as e:
        logger.error(f"❌ Failed to sync slash commands: {e}")
    await bot.change_presence(activity=discord.Game(name="Dungeon Adventure!"))

@bot.event
async def on_shard_connect(shard_id):
    logger.debug(f"Shard {shard_id} connected.")

# ---------------------
#   DYNAMIC COG LOADING
# ---------------------
def discover_cogs(root_dirs):
    """
    Recursively scans the given list of directories (relative to bot root) for Python files.
    Only returns modules that define a callable `setup` function.
    """
    cogs = []
    bot_root = get_bot_root()
    for directory in root_dirs:
        dir_path = os.path.join(bot_root, directory)
        if not os.path.exists(dir_path):
            logger.debug(f"Directory not found (skipping): {dir_path}")
            continue  # skip if directory doesn't exist
        for root, _, files in os.walk(dir_path):
            for file in files:
                if file.endswith(".py") and file != "__init__.py":
                    rel_path = os.path.relpath(os.path.join(root, file), bot_root)
                    module_path = rel_path[:-3].replace(os.sep, ".")
                    try:
                        mod = importlib.import_module(module_path)
                        if hasattr(mod, "setup") and callable(mod.setup):
                            cogs.append(module_path)
                        else:
                            logger.debug(f"Skipping non-cog module: {module_path}")
                    except Exception as e:
                        logger.error(f"Error importing module {module_path}: {e}")
    return cogs

# Only include directories that actually contain cogs.
# Our design supports multi-session management and vendor data isolation.
cog_directories = ["game", "hub"]
modules = discover_cogs(cog_directories)
logger.info(f"Discovered cog modules: {modules}")

# ---------------------
#   MAIN BOT START
# ---------------------
async def main():
    run_database_setup()

    if not TOKEN:
        logger.error("❌ Discord token not found in config. Exiting...")
        return

    for module in modules:
        try:
            await bot.load_extension(module)
            logger.info(f"✅ Loaded module: {module}")
        except Exception as e:
            logger.error(f"❌ Failed to load module '{module}': {e}")

    # Start the bot using an asynchronous context for proper cleanup.
    async with bot:
        await bot.start(TOKEN)

if __name__ == '__main__':
    asyncio.run(main())
