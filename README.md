# AdventureBot

AdventureBot is a Discord bot that powers a turn‑based dungeon adventure. It uses MySQL to store game sessions and data while gameplay logic lives in the `game` package. The `hub` package manages server setup and player interactions.

## Prerequisites

- **Python** 3.10+
- **MySQL** server
- A Discord application with a bot token and the necessary intent permissions
- Python packages `discord.py` and `mysql-connector-python`

Install the dependencies with:

```bash
pip install discord.py mysql-connector-python
```

## Configuration

Edit `config.json` in the project root and provide your own credentials. A typical configuration looks like:

```json
{
    "discord_token": "YOUR_BOT_TOKEN",
    "mysql": {
        "host": "localhost",
        "user": "root",
        "password": "password",
        "database": "adventure"
    }
}
```

## Database setup (optional)

A sample schema is provided at `database/dump.sql`. Import it if you need to prepopulate the database:

```bash
mysql -u <user> -p <database> < database/dump.sql
```

## Running the bot

Create a small launcher script that instantiates `commands.Bot`, loads the cogs from the `hub` and `game` packages, and then calls `bot.run()` using the token from `config.json`.

Once the launcher is ready, start the bot with:

```bash
python run_bot.py
```

Slash commands such as `/adventuresetup` will then be available in your server.
