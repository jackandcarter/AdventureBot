import os
import json

def get_bot_root():
    # Get the parent directory of the utils folder (i.e., the project root)
    return os.path.dirname(os.path.abspath(os.path.join(__file__, '..')))

def load_config():
    """Load configuration from ``config.json`` and environment variables."""

    config_path = os.path.join(get_bot_root(), 'config.json')
    config = {"mysql": {}}

    if os.path.exists(config_path):
        with open(config_path, 'r') as f:
            config.update(json.load(f))

    # Environment variables override values from the file
    env_token = os.getenv("DISCORD_TOKEN")
    if env_token:
        config["discord_token"] = env_token

    mysql_conf = config.get("mysql", {})
    for key, env_var in [
        ("host", "MYSQL_HOST"),
        ("user", "MYSQL_USER"),
        ("password", "MYSQL_PASSWORD"),
        ("database", "MYSQL_DATABASE"),
    ]:
        val = os.getenv(env_var)
        if val:
            mysql_conf[key] = val
    config["mysql"] = mysql_conf

    return config
