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

The database_setup.py script is needed for successful bot startup, it is used to check and verify a standard database with minimal default setup.
The included seed info in this script is legacy and depricated, but is considered the base install of the database which is required for the bot to work. 

A more recent version of the schema (based on patch 3.0.9) is provided at `database/dump.sql`. Import it if you need to prepopulate the database:

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
