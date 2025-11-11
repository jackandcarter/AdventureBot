# AdventureBot on Ubuntu 24.04

This guide walks through installing and running AdventureBot on a fresh Ubuntu 24.04 LTS server (or VPS) with Python and MariaDB. The steps assume you have sudo access.

## 1. Install system packages

Update the package index and install the tools required to build Python wheels and talk to MariaDB:

```bash
sudo apt update
sudo apt install -y python3 python3-pip python3-venv build-essential libffi-dev libssl-dev pkg-config git mariadb-server
```

Ubuntu 24.04 ships with Python 3.12 by default, which satisfies the project's Python 3.10+ requirement. The extra development packages ensure that `aiomysql` can compile optional speedups if available.

## 2. Secure and start MariaDB

Enable MariaDB at boot and run the hardening script if you have not already:

```bash
sudo systemctl enable --now mariadb
sudo mysql_secure_installation
```

During the secure installation process you can set a root password, remove anonymous users, disallow remote root login, and drop the test database.

## 3. Create the AdventureBot database and user

Connect to MariaDB and create the database, user, and permissions AdventureBot expects. Replace `bot_password` with a strong password of your choosing.

```bash
sudo mariadb
```

Inside the MariaDB shell run:

```sql
CREATE DATABASE adventure CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'adventurebot'@'localhost' IDENTIFIED BY 'bot_password';
GRANT ALL PRIVILEGES ON adventure.* TO 'adventurebot'@'localhost';
FLUSH PRIVILEGES;
EXIT;
```

## 4. Clone the project

```bash
git clone https://github.com/<your-org>/AdventureBot.git
cd AdventureBot
```

## 5. Create and activate a virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate
```

If you prefer not to use a virtual environment, ensure that the user running the bot has permission to install Python packages globally.

## 6. Install Python dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

The requirements include both synchronous (`mysql-connector-python`) and asynchronous (`aiomysql`) clients for MySQL/MariaDB servers. They work with MariaDB 10.5+ out of the box.

## 7. Configure credentials

AdventureBot reads configuration from `config.json` in the project root and allows environment variables to override any value. You can use either approach:

### Option A – `config.json`

Copy the example configuration and edit it:

```bash
cp config.example.json config.json
```

Update the file with your Discord bot token and the MariaDB credentials created above:

```json
{
    "discord_token": "YOUR_BOT_TOKEN",
    "mysql": {
        "host": "127.0.0.1",
        "user": "adventurebot",
        "password": "bot_password",
        "database": "adventure"
    }
}
```

### Option B – Environment variables

Export the variables before starting the bot or add them to your shell profile/systemd unit:

```bash
export DISCORD_TOKEN="YOUR_BOT_TOKEN"
export MYSQL_HOST="127.0.0.1"
export MYSQL_USER="adventurebot"
export MYSQL_PASSWORD="bot_password"
export MYSQL_DATABASE="adventure"
```

Environment variables override values stored in `config.json` at runtime.

## 8. Initialize the database schema and seed data

AdventureBot ships with a schema and seed data in `database/dump.sql`. The easiest way to apply it is by running the setup script, which connects using the credentials in your configuration and creates any missing tables:

```bash
python database/database_setup.py
```

Alternatively, you can import the SQL dump manually:

```bash
mysql -u adventurebot -p adventure < database/dump.sql
```

## 9. Run AdventureBot

With your virtual environment still active:

```bash
python bot.py
```

Keep the process running in a terminal multiplexer (such as `tmux` or `screen`) or create a `systemd` service to manage it in the background. The bot requires a Discord channel named `Adventurebot` in the target server and the appropriate intents enabled in the Discord developer portal.

## 10. Troubleshooting tips

- **Connection errors**: Confirm the MariaDB service is running (`systemctl status mariadb`) and that the credentials match what is in `config.json` or environment variables.
- **Dependency compilation issues**: Ensure `build-essential`, `libffi-dev`, and `libssl-dev` are installed before running `pip install -r requirements.txt`.
- **Locale problems importing SQL**: Set your terminal locale to UTF-8 (`export LC_ALL=C.UTF-8`) before running the setup script if you encounter encoding errors.

Once these steps are complete the bot should be ready to use on Ubuntu 24.04.
