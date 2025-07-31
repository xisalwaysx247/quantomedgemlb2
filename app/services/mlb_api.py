import requests
import logging
import os
import json
from datetime import datetime, timedelta

BASE_URL = "https://statsapi.mlb.com/api/v1"

# Set logging to WARNING to hide debug logs
logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)

def get_all_teams():
    """Fetch all MLB teams from the updated API."""
    endpoint = f"{BASE_URL}/teams"
    response = requests.get(endpoint, params={"sportId": 1})
    response.raise_for_status()
    return response.json().get("teams", [])

def get_team_roster(team_id):
    """Fetch the roster for a specific team."""
    endpoint = f"{BASE_URL}/teams/{team_id}/roster"
    response = requests.get(endpoint)
    response.raise_for_status()
    return response.json().get("roster", [])

def get_player_stats(player_id, group, season):
    """Fetch stats for a specific player."""
    endpoint = f"{BASE_URL}/people/{player_id}/stats"
    params = {
        "stats": "season",
        "group": group,
        "season": season,
    }
    response = requests.get(endpoint, params=params)
    response.raise_for_status()
    return response.json().get("stats", [])

def get_last_10_games(player_id, group="hitting", season=2025):
    """Fetch the last 10 games for a player."""
    endpoint = f"{BASE_URL}/people/{player_id}/stats"
    params = {
        "stats": "gameLog",
        "group": group,
        "season": season,
    }
    response = requests.get(endpoint, params=params)
    response.raise_for_status()
    
    # Get all game splits and sort them by date descending (most recent first)
    all_splits = response.json().get("stats", [])[0].get("splits", [])
    
    # Sort by date descending to get most recent games first
    sorted_splits = sorted(all_splits, key=lambda x: x.get("date", ""), reverse=True)
    
    # Return the most recent 10 games
    return sorted_splits[:10]

def get_hit_streak(player_id: int, num_games: int = 10) -> int:
    """Calculate the hit streak for a player based on their last N games with proper chronological sorting."""
    try:
        # Get the last N games sorted by date (most recent first)
        games = get_last_10_games(player_id, group="hitting", season=2025)
        
        if not games:
            return 0
        
        # Filter out future games and games without valid dates
        from datetime import datetime, date
        current_date = date.today()
        valid_games = []
        
        for game in games:
            game_date_str = game.get("date", "")
            if not game_date_str:
                continue
                
            try:
                game_date = datetime.strptime(game_date_str, "%Y-%m-%d").date()
                # Only include games that have been played (not future games)
                if game_date <= current_date:
                    valid_games.append(game)
            except ValueError:
                continue
        
        if not valid_games:
            return 0
        
        # Games are already sorted by date descending (most recent first)
        # Calculate consecutive hit streak from most recent games
        streak = 0
        for game in valid_games[:num_games]:
            hits = game.get("stat", {}).get("hits", 0)
            if hits > 0:
                streak += 1
            else:
                # Streak broken, stop counting
                break
        
        return streak
        
    except Exception as e:
        logger.debug(f"Error calculating hit streak for player {player_id}: {e}")
        return 0

def is_weak_pitcher(pitcher_stats):
    """Determine if a pitcher is weak based on specific thresholds."""
    logger.debug(f"Evaluating pitcher stats: {pitcher_stats}")
    
    # Convert string values to floats for comparison
    try:
        era = float(pitcher_stats.get("era", 0))
        whip = float(pitcher_stats.get("whip", 0))
        batting_avg_against = float(pitcher_stats.get("battingAverageAgainst", pitcher_stats.get("avg", 0)))
        hits_per_nine = float(pitcher_stats.get("hitsPer9Inn", 0))
        strikeouts_per_nine = float(pitcher_stats.get("strikeoutsPer9Inn", 0))
        walks_per_nine = float(pitcher_stats.get("walksPer9Inn", 0))
        innings_pitched = float(pitcher_stats.get("inningsPitched", 0))
    except (ValueError, TypeError):
        logger.warning(f"Could not convert pitcher stats to numbers: {pitcher_stats}")
        return False
    
    # More realistic weak pitcher criteria
    weak_criteria_met = 0
    
    # Primary indicators (weighted more heavily)
    if era > 4.75:
        weak_criteria_met += 2
    if whip > 1.35:
        weak_criteria_met += 2
    if hits_per_nine > 9.0:
        weak_criteria_met += 1
    
    # Secondary indicators
    if batting_avg_against > 0.260:
        weak_criteria_met += 1
    if strikeouts_per_nine < 7.5:
        weak_criteria_met += 1
    if walks_per_nine > 3.0:
        weak_criteria_met += 1
    
    # Must have sufficient innings pitched
    if innings_pitched < 20:
        return False
    
    # Need at least 4 points to be considered weak (can be from primary criteria alone)
    logger.debug(f"Weak criteria points: {weak_criteria_met} (ERA: {era}, WHIP: {whip}, H/9: {hits_per_nine}, IP: {innings_pitched})")
    return weak_criteria_met >= 4

def classify_hitter(hitter_stats):
    """Classify a hitter based on ERA thresholds."""
    # Helper function to safely convert string values to float
    def safe_float(value, default=0):
        if isinstance(value, str):
            try:
                return float(value)
            except (ValueError, TypeError):
                return default
        return value if value is not None else default
    
    # Get ERA for classification
    era = safe_float(hitter_stats.get("era", 0))
    
    # Check if we have any meaningful stats to classify
    has_data = (
        era > 0 or  # Has ERA
        safe_float(hitter_stats.get("avg", 0)) > 0 or  # Has batting average
        safe_float(hitter_stats.get("homeRuns", 0)) > 0 or  # Has home runs
        safe_float(hitter_stats.get("rbi", 0)) > 0 or     # Has RBIs
        safe_float(hitter_stats.get("gamesPlayed", 0)) > 0  # Has games played
    )
    
    # Only return insufficient data if we truly have no meaningful stats
    if not has_data:
        return "❓"
    
    # Classify based on ERA thresholds
    if era >= 0.280:
        return "🟢"  # Strong hitter
    elif era >= 0.225:
        return "🟡"  # Bubble hitter
    elif era > 0 and era <= 0.220:
        return "🔴"  # Weak hitter
    else:
        # If ERA is 0 or invalid, fallback to other stats for basic classification
        avg = safe_float(hitter_stats.get("avg", 0))
        if avg >= 0.280:
            return "🟢"
        elif avg >= 0.225:
            return "🟡"
        else:
            return "🔴"

def save_matchup_cache(date, games_data):
    """Save matchup report data to cache."""
    cache_dir = os.path.join("data", "matchup_cache")
    os.makedirs(cache_dir, exist_ok=True)
    
    cache_file = os.path.join(cache_dir, f"matchup_{date}.json")
    
    cache_data = {
        "date": date,
        "cached_at": datetime.now().isoformat(),
        "games": games_data
    }
    
    with open(cache_file, "w") as f:
        json.dump(cache_data, f, indent=4)
    
    logger.debug(f"Saved matchup cache for {date} to {cache_file}")

def load_matchup_cache(date):
    """Load matchup report data from cache if available and recent."""
    cache_file = os.path.join("data", "matchup_cache", f"matchup_{date}.json")
    
    if not os.path.exists(cache_file):
        logger.debug(f"No cache file found for {date}")
        return None
    
    try:
        with open(cache_file, "r") as f:
            cache_data = json.load(f)
        
        # Check if cache is recent (within last 6 hours for same day, or if it's a future/past date)
        cached_at = datetime.fromisoformat(cache_data["cached_at"])
        now = datetime.now()
        
        # For today's games, refresh cache every 6 hours
        # For future/past games, cache is valid for 24 hours
        cache_expiry_hours = 6 if date == now.strftime("%Y-%m-%d") else 24
        
        if now - cached_at < timedelta(hours=cache_expiry_hours):
            logger.debug(f"Using cached data for {date} (cached at {cached_at})")
            return cache_data["games"]
        else:
            logger.debug(f"Cache for {date} is expired (cached at {cached_at})")
            return None
            
    except Exception as e:
        logger.warning(f"Error loading cache for {date}: {e}")
        return None

def fetch_games_for_date(date: str, use_cache: bool = True):
    """Fetch all games scheduled for a given date with caching support."""
    
    # Try to load from cache first
    if use_cache:
        cached_games = load_matchup_cache(date)
        if cached_games:
            logger.info(f"Using cached data for {date}")
            return cached_games
    
    logger.info(f"Fetching fresh data from API for {date}")
    
    endpoint = f"{BASE_URL}/schedule"
    params = {
        "sportId": 1,
        "date": date,
        "hydrate": "probablePitcher"
    }
    response = requests.get(endpoint, params=params)
    response.raise_for_status()
    data = response.json()

    # Log the API response for debugging
    logger.debug(f"API Response for {date}: {data}")

    games = data.get("dates", [])[0].get("games", []) if data.get("dates") else []

    # Process each game to extract probable pitcher information
    for game in games:
        game_id = game.get("gamePk")
        
        # Try to get probable pitchers from the schedule data first
        home_pitcher = game.get("teams", {}).get("home", {}).get("probablePitcher", {})
        away_pitcher = game.get("teams", {}).get("away", {}).get("probablePitcher", {})
        
        # If no probable pitchers in schedule, try boxscore as fallback
        if not home_pitcher and not away_pitcher and game_id:
            try:
                game_endpoint = f"{BASE_URL}/game/{game_id}/boxscore"
                game_response = requests.get(game_endpoint)
                game_response.raise_for_status()
                boxscore = game_response.json()
                
                home_pitcher = boxscore.get("teams", {}).get("home", {}).get("probablePitcher", {})
                away_pitcher = boxscore.get("teams", {}).get("away", {}).get("probablePitcher", {})
            except Exception as e:
                logger.warning(f"Could not fetch boxscore for game {game_id}: {e}")
        
        # If still no probable pitchers, mark as TBD
        if not home_pitcher:
            home_pitcher = {
                "id": None,
                "fullName": "TBD",
                "stats": {}
            }
        if not away_pitcher:
            away_pitcher = {
                "id": None,
                "fullName": "TBD", 
                "stats": {}
            }
        
        # Fetch stats for pitchers if we have their IDs
        for pitcher in [home_pitcher, away_pitcher]:
            if pitcher.get("id") and pitcher.get("fullName") != "TBD":
                try:
                    # Fetch pitcher's season stats
                    pitcher_id = pitcher.get("id")
                    stats_endpoint = f"{BASE_URL}/people/{pitcher_id}/stats"
                    stats_params = {
                        "stats": "season",
                        "group": "pitching",
                        "season": 2025,
                    }
                    stats_response = requests.get(stats_endpoint, params=stats_params)
                    stats_response.raise_for_status()
                    stats_data = stats_response.json()
                    
                    # Extract pitching stats
                    if stats_data.get("stats") and len(stats_data["stats"]) > 0:
                        season_stats = stats_data["stats"][0].get("splits", [])
                        if season_stats and len(season_stats) > 0:
                            pitcher["stats"] = season_stats[0].get("stat", {})
                    
                    logger.debug(f"Fetched stats for pitcher {pitcher.get('fullName')}: {pitcher.get('stats', {})}")
                    
                except Exception as e:
                    logger.warning(f"Could not fetch stats for pitcher {pitcher.get('fullName', 'Unknown')}: {e}")
                    pitcher["stats"] = {}
        
        game["home_pitcher"] = home_pitcher
        game["away_pitcher"] = away_pitcher

        # Log probable pitcher data for debugging
        logger.debug(f"Game ID {game_id}: Home Pitcher Data: {home_pitcher}")
        logger.debug(f"Game ID {game_id}: Away Pitcher Data: {away_pitcher}")

    # Save to cache after processing all games
    if use_cache:
        save_matchup_cache(date, games)
    
    return games

def fetch_team_roster(team_id):
    """Fetch the roster for a specific team."""
    endpoint = f"{BASE_URL}/teams/{team_id}/roster"
    response = requests.get(endpoint)
    response.raise_for_status()
    return response.json().get("roster", [])