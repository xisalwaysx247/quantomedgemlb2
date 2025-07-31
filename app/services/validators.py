import logging
from typing import Any, List, Dict

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def safe_get(obj: Dict, key: str, default: Any = None) -> Any:
    """
    Safely get a value from a dictionary by key.
    """
    if key in obj:
        return obj[key]
    logger.warning(f"Key '{key}' not found in object. Returning default: {default}")
    return default

def safe_nested_get(obj: Dict, keys: List[str], default: Any = None) -> Any:
    """
    Safely traverse nested keys in a dictionary.
    """
    current = obj
    for key in keys:
        if isinstance(current, dict) and key in current:
            current = current[key]
        else:
            logger.warning(f"Key path '{' -> '.join(keys)}' not found. Returning default: {default}")
            return default
    return current

def validate_player_stats(data: Dict) -> Dict:
    """
    Validate player stats response structure.
    """
    stats = safe_get(data, "stats", [])
    if not stats or not isinstance(stats, list):
        logger.warning("Invalid or missing 'stats' in player stats data. Returning empty dict.")
        return {}

    splits = safe_get(stats[0], "splits", []) if stats else []
    if not splits or not isinstance(splits, list):
        logger.warning("Invalid or missing 'splits' in player stats data. Returning empty dict.")
        return {}

    return safe_get(splits[0], "stat", {})

def validate_team_roster(data: Dict) -> List[Dict]:
    """
    Validate team roster response structure.
    """
    roster = safe_get(data, "roster", [])
    if not isinstance(roster, list):
        logger.warning("Invalid or missing 'roster' in team data. Returning empty list.")
        return []
    return roster

def is_valid_schedule(data: Dict) -> bool:
    """
    Check if schedule data contains at least one valid game.
    """
    dates = safe_get(data, "dates", [])
    if not dates or not isinstance(dates, list):
        logger.warning("Invalid or missing 'dates' in schedule data.")
        return False

    games = safe_get(dates[0], "games", []) if dates else []
    if not games or not isinstance(games, list):
        logger.warning("No valid games found in schedule data.")
        return False

    return True