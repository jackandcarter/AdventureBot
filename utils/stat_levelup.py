import mysql.connector
import json
import logging
from utils.helpers import load_config

logger = logging.getLogger("StatLevelUp")
logger.setLevel(logging.DEBUG)

# Load configuration
config = load_config()
db_config = config['mysql']

def db_connect():
    """Create and return a new MySQL connection."""
    try:
        return mysql.connector.connect(**db_config)
    except Exception as e:
        logger.error("DB connection error in StatLevelUp: %s", e)
        raise

def get_level_growth(level: int) -> dict:
    """
    Retrieves growth multipliers for a given level from the levels table.
    
    Returns a dict with the keys:
      - hp_increase, attack_increase, magic_increase, defense_increase,
        magic_defense_increase, accuracy_increase, evasion_increase, speed_increase.
    """
    try:
        conn = db_connect()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM levels WHERE level = %s", (level,))
        row = cursor.fetchone()
        cursor.close()
        conn.close()
        if row:
            # Extract only the growth multipliers.
        growth_keys = [
            "hp_increase", "attack_increase", "magic_increase", "defense_increase",
            "magic_defense_increase", "accuracy_increase", "evasion_increase", "speed_increase",
            "mp_increase",
        ]
            growth = {key: row.get(key, 0) for key in growth_keys}
            return growth
        else:
            logger.error("No growth data found for level %s", level)
            return {}
    except Exception as e:
        logger.error("Error fetching growth data for level %s: %s", level, e)
        return {}

def get_class_base_stats(class_id: int) -> dict:
    """
    Retrieves base stats for the given class_id from the classes table.
    
    Returns a dict with:
      - base_hp, base_attack, base_magic, base_defense, base_magic_defense,
        base_accuracy, base_evasion, base_speed, base_mp.
    """
    try:
        conn = db_connect()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT base_hp, base_attack, base_magic, base_mp, base_defense,
                   base_magic_defense, base_accuracy, base_evasion, base_speed
            FROM classes
            WHERE class_id = %s
        """, (class_id,))
        row = cursor.fetchone()
        cursor.close()
        conn.close()
        if row:
            return row
        else:
            logger.error("No base stats found for class_id %s", class_id)
            return {}
    except Exception as e:
        logger.error("Error retrieving base stats: %s", e)
        return {}

def calculate_effective_stats(base_stats: dict, growth: dict, level: int) -> dict:
    """
    Calculates effective stats based on the player's base stats and growth multipliers.

    The formula used is:
        effective_stat = base_stat * (1 + growth_factor * (level - 1))
    
    Returns a dict with keys: hp, attack, magic, defense, magic_defense, accuracy, evasion, speed.
    """
    # Define a mapping of the base stat column names to the corresponding growth keys.
    mapping = {
        "base_hp": "hp_increase",
        "base_attack": "attack_increase",
        "base_magic": "magic_increase",
        "base_defense": "defense_increase",
        "base_magic_defense": "magic_defense_increase",
        "base_accuracy": "accuracy_increase",
        "base_evasion": "evasion_increase",
        "base_speed": "speed_increase",
        "base_mp": "mp_increase",
    }
    effective = {}
    for base_key, growth_key in mapping.items():
        base_value = base_stats.get(base_key, 0)
        growth_factor = growth.get(growth_key, 0)
        # Calculate effective stat
        effective_value = int(base_value * (1 + growth_factor * (level - 1)))
        # Remove the prefix "base_" for a cleaner stat key.
        effective[base_key.replace("base_", "")] = effective_value
    return effective

def update_player_stats(player_id: int, session_id: int, new_level: int, class_id: int) -> bool:
    """
    Recalculates and updates the effective stats for the player in the 'players' table based on their new level.

    This function:
      1. Retrieves the class's base stats using class_id.
      2. Retrieves the growth multipliers for the new level from the levels table.
      3. Calculates effective stats using the formula.
      4. Updates the player's record with the new effective stats.
    
    Returns True if the update succeeds; otherwise, False.
    """
    base_stats = get_class_base_stats(class_id)
    if not base_stats:
        logger.error("Cannot update player stats: base stats not found for class_id %s", class_id)
        return False
    growth = get_level_growth(new_level)
    if not growth:
        logger.error("Cannot update player stats: growth data not found for level %s", new_level)
        return False
    effective_stats = calculate_effective_stats(base_stats, growth, new_level)
    try:
        conn = db_connect()
        cursor = conn.cursor()
        # Update the player's effective stats. Here we assume that the player's current
        # hp and max_hp are both set to the effective hp upon leveling. Adjust if you use a different model.
        update_query = """
            UPDATE players
            SET hp = %s,
                max_hp = %s,
                mp = %s,
                max_mp = %s,
                attack_power = %s,
                magic_power = %s,
                defense = %s,
                magic_defense = %s,
                accuracy = %s,
                evasion = %s,
                speed = %s
            WHERE player_id = %s AND session_id = %s
        """
        cursor.execute(update_query, (
            effective_stats.get("hp", 0),               # hp
            effective_stats.get("hp", 0),               # max_hp
            effective_stats.get("mp", 0),               # mp
            effective_stats.get("mp", 0),               # max_mp
            effective_stats.get("attack", 0),           # attack_power
            effective_stats.get("magic", 0),            # magic_power
            effective_stats.get("defense", 0),          # defense
            effective_stats.get("magic_defense", 0),    # magic_defense
            effective_stats.get("accuracy", 0),         # accuracy
            effective_stats.get("evasion", 0),          # evasion
            effective_stats.get("speed", 0),            # speed
            player_id,
            session_id
        ))
        conn.commit()
        cursor.close()
        conn.close()
        logger.debug("Player %s stats updated for level %s: %s", player_id, new_level, effective_stats)
        return True
    except Exception as e:
        logger.error("Error updating player stats: %s", e)
        return False

if __name__ == "__main__":
    # Test block for local testing; replace these values with ones from your system as needed.
    test_player_id = 123456789       # Replace with an actual player_id.
    test_session_id = 1              # Replace with an actual session_id.
    test_class_id = 1                # Replace with the class_id of the player (e.g., Warrior).
    new_level = 2                    # The new level we're updating to.
    
    if update_player_stats(test_player_id, test_session_id, new_level, test_class_id):
        logger.info("Player stats updated successfully.")
    else:
        logger.info("Failed to update player stats.")
