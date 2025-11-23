import json
import os
from urllib.parse import urlparse

def get_bot_root():
    # Get the parent directory of the utils folder (i.e., the project root)
    return os.path.dirname(os.path.abspath(os.path.join(__file__, '..')))

def _parse_db_url(url: str) -> dict:
    """Parse a database URL into a mysql.connector compatible dict."""

    parsed = urlparse(url)
    return {
        "host": parsed.hostname,
        "user": parsed.username,
        "password": parsed.password,
        "database": parsed.path.lstrip("/") if parsed.path else None,
        "port": parsed.port,
    }


def _parse_mail_url(url: str) -> dict:
    """Parse an SMTP URL into a configuration dictionary."""

    parsed = urlparse(url)
    return {
        "host": parsed.hostname,
        "port": parsed.port,
        "username": parsed.username,
        "password": parsed.password,
        "use_tls": parsed.scheme == "smtp+tls",
        "use_ssl": parsed.scheme == "smtps",
    }


def load_config():
    """Load configuration from ``config.json`` and environment variables."""

    config_path = os.path.join(get_bot_root(), 'config.json')
    config = {"mysql": {}, "mail": {}}

    if os.path.exists(config_path):
        with open(config_path, 'r') as f:
            config.update(json.load(f))

    # Environment variables override values from the file
    env_token = os.getenv("DISCORD_TOKEN")
    if env_token:
        config["discord_token"] = env_token

    mysql_conf = config.get("mysql", {})
    db_url = os.getenv("DATABASE_URL") or config.get("database_url")
    if db_url:
        mysql_conf.update({k: v for k, v in _parse_db_url(db_url).items() if v})
    for key, env_var in [
        ("host", "MYSQL_HOST"),
        ("user", "MYSQL_USER"),
        ("password", "MYSQL_PASSWORD"),
        ("database", "MYSQL_DATABASE"),
        ("port", "MYSQL_PORT"),
    ]:
        val = os.getenv(env_var)
        if val:
            mysql_conf[key] = val if key != "port" else int(val)
    config["mysql"] = mysql_conf

    mail_conf = config.get("mail", {})
    mail_url = os.getenv("MAIL_URL") or config.get("mail_url")
    if mail_url:
        mail_conf.update({k: v for k, v in _parse_mail_url(mail_url).items() if v is not None})
    for key, env_var in [
        ("host", "MAIL_HOST"),
        ("port", "MAIL_PORT"),
        ("username", "MAIL_USERNAME"),
        ("password", "MAIL_PASSWORD"),
        ("use_tls", "MAIL_USE_TLS"),
        ("use_ssl", "MAIL_USE_SSL"),
    ]:
        val = os.getenv(env_var)
        if val:
            if key in {"use_tls", "use_ssl"}:
                val = val.lower() in {"1", "true", "yes"}
            elif key == "port":
                val = int(val)
            mail_conf[key] = val
    config["mail"] = mail_conf

    return config
