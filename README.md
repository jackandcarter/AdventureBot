# AdventureBot


AdventureBot is a Discord bot that powers a turn‑based dungeon adventure. It uses MySQL to store game sessions and data while gameplay logic lives in the `game` package. The `hub` package manages server setup and player interactions.

## Prerequisites

- **Python** 3.10+
- **MySQL** server
- A Discord application with a bot token and the necessary intent permissions

## Installation

Install the dependencies with:

```bash
pip install -r requirements.txt
```

If you are deploying on Ubuntu 24.04, see the detailed [Ubuntu setup guide](docs/ubuntu-setup.md) for end-to-end instructions covering system packages, MariaDB configuration, and environment variables.

Enable the required Discord intents for your application and initialize the database:

```bash
python database/database_setup.py
```

## Configuration

Create a `config.json` file in the project root and provide your own credentials. An example configuration is available in
`config.example.json`. Environment variables will override values found in
`config.json`:

- `DISCORD_TOKEN`
- `MYSQL_HOST`
- `MYSQL_USER`
- `MYSQL_PASSWORD`
- `MYSQL_DATABASE`

If a variable is not provided, the loader falls back to the value in `config.json`.

A typical configuration looks like:

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

## Database setup 

The `database_setup.py` script is needed for successful bot startup and will seed
the database with the same data found in `database/dump.sql`. You can either run
the script or import the dump to prepopulate your tables:

```bash
mysql -u <user> -p <database> < database/dump.sql
```

## Running the bot

Start the bot with:

```bash
python bot.py
```

Slash commands such as `/adventuresetup` will then be available in your server.

## Game Channel Setup

Ensure there is a channel named "Adventurebot" in the server you intend on using the bot with and give the bot needed permission if necessary.

## High Scores

Scores are recorded automatically when a session ends. The bot inserts player stats such as play time, enemies defeated, rooms visited and gil into the `high_scores` table.
Ensure this table exists by running `python database/database_setup.py` during setup.

From the hub, press the **High Scores** button to view the leaderboard. Entries are sorted by play time (ascending) and then enemies defeated, but you can also sort programmatically by `enemies_defeated`, `gil` or `player_level` when using the API.

## Turn-Based Combat

Battles now use a classic turn-based flow. The side with the higher effective speed stat acts first; if the enemy is faster they gain a pre-emptive strike, while faster players open the battle. Speed-altering effects such as *haste* or *slow* can still grant occasional extra turns when the difference is large enough, preserving the strategic value of speed without the need for visible gauges.
