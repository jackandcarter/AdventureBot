import os
import json

def get_bot_root():
    # Get the parent directory of the utils folder (i.e., the project root)
    return os.path.dirname(os.path.abspath(os.path.join(__file__, '..')))

def load_config():
    # Look for config.json in the project root instead of in a 'utils' folder
    config_path = os.path.join(get_bot_root(), 'config.json')
    if not os.path.exists(config_path):
        print("❌ Config file missing. Please create 'config.json' in the project root.")
        return None
    with open(config_path, 'r') as f:
        config = json.load(f)
    return config
