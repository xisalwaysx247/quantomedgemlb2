import requests
import logging
from sqlalchemy.orm import Session
from app.db.session import get_db, SessionLocal
from app.db.schema import Team, Player, HitterStats, PitcherStats, create_team_tables, Base
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy import Column, Integer, Float
from app.services.mlb_api import get_all_teams, get_team_roster, get_player_stats
import os
import json
import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BASE_URL = "https://statsapi.mlb.com/api/v1"
SEASON = 2025

# Initialize database engine and session
engine = create_engine("sqlite:///mlb_stats.db")
Session = sessionmaker(bind=engine)


def fetch_teams():
    """Fetch all teams using the updated API logic."""
    return get_all_teams()


def fetch_roster(team_id):
    """Fetch team roster using the updated API logic."""
    return get_team_roster(team_id)


def fetch_player_stats(player_id, group):
    """Fetch player stats using the updated API logic."""
    return get_player_stats(player_id, group, season=SEASON)


def fetch_team_stats(team_id):
    """Fetch overall season stats for a specific team from the API."""
    try:
        # Construct the endpoint dynamically
        response = requests.get(
            f"{BASE_URL}/teams/{team_id}/stats",
            params={"season": SEASON, "group": "hitting", "stats": "season"}  # Added 'stats' parameter
        )
        response.raise_for_status()
        stats = response.json().get("stats", [])
        return stats[0].get("splits", [{}])[0].get("stat", {}) if stats else {}
    except requests.exceptions.HTTPError as http_err:
        logger.error(f"HTTP error occurred while fetching team stats: {http_err}")
        logger.error(f"Response content: {response.text}")
        return {}
    except Exception as err:
        logger.error(f"An error occurred while fetching team stats: {err}")
        return {}


def load_data():
    db = next(get_db())
    try:
        # Fetch and store teams
        teams = fetch_teams()
        logger.info(f"Fetched {len(teams)} teams.")

        for team_data in teams:
            team = Team(
                id=team_data["id"],
                name=team_data["name"],
                abbreviation=team_data["abbreviation"],
                league=team_data["league"].get("name"),
                division=team_data["division"].get("name"),
            )
            db.merge(team)

            # Fetch and store players
            roster = fetch_roster(team.id)
            logger.info(f"Fetched {len(roster)} players for team {team.name}.")

            for player_data in roster:
                player = Player(
                    id=player_data["person"]["id"],
                    full_name=player_data["person"]["fullName"],
                    team_id=team.id,
                    position=player_data["position"]["abbreviation"],
                    is_pitcher=(player_data["position"]["abbreviation"] == "P"),
                    bats=player_data["person"].get("batSide", {}).get("description", ""),
                    throws=player_data["person"].get("pitchHand", {}).get("description", ""),
                )
                db.merge(player)

                # Fetch and store stats
                if player.is_pitcher:
                    stats = fetch_player_stats(player.id, "pitching")
                    if stats:
                        pitcher_stats = PitcherStats(
                            player_id=player.id,
                            season=SEASON,
                            era=stats.get("era"),
                            whip=stats.get("whip"),
                            k_pct=stats.get("strikeOuts") / stats.get("battersFaced", 1),
                            k9=stats.get("strikeoutsPer9Inn"),
                            whiff_pct=stats.get("whiffPercentage"),
                            strikeout_walk_ratio=stats.get("strikeoutWalkRatio"),
                        )
                        db.merge(pitcher_stats)
                else:
                    stats = fetch_player_stats(player.id, "hitting")
                    if stats:
                        hitter_stats = HitterStats(
                            player_id=player.id,
                            season=SEASON,
                            avg=stats.get("avg"),
                            ops=stats.get("ops"),
                            hr=stats.get("homeRuns"),
                            rbi=stats.get("rbi"),
                            k_pct=stats.get("strikeOuts") / stats.get("plateAppearances", 1),
                            contact_pct=stats.get("contactPercentage"),
                            whiff_pct=stats.get("whiffPercentage"),
                            o_swing_pct=stats.get("outsideSwingPercentage"),
                            z_contact_pct=stats.get("zContactPercentage"),
                        )
                        db.merge(hitter_stats)

            db.commit()
    except Exception as e:
        logger.error(f"Error loading data: {e}")
        db.rollback()
    finally:
        db.close()


def transfer_json_to_db():
    """Transfer all JSON data to the SQLite database."""
    session = Session()
    try:
        # Load teams
        with open("data/teams.json", "r") as f:
            teams = json.load(f)

        for team in teams:
            team_id = team["id"]
            team_name = team["name"]
            logger.info(f"Processing team: {team_name} (ID: {team_id})")

            # Create team tables dynamically
            Roster, Stats = create_team_tables(team_id)
            Base.metadata.create_all(engine)

            # Load roster
            roster_file = f"data/rosters/{team_id}.json"
            if os.path.exists(roster_file):
                with open(roster_file, "r") as roster_f:
                    roster = json.load(roster_f)

                for player in roster:
                    player_data = {
                        "id": player["person"]["id"],
                        "full_name": player["person"]["fullName"],
                        "position": player["position"]["abbreviation"],
                        "is_pitcher": player["position"]["abbreviation"] == "P",
                        "bats": player["person"].get("batSide", {}).get("description", ""),
                        "throws": player["person"].get("pitchHand", {}).get("description", ""),
                    }
                    session.merge(Roster(**player_data))

                    # Load stats
                    player_file = f"data/players/{player_data['id']}.json"
                    if os.path.exists(player_file):
                        with open(player_file, "r") as player_f:
                            stats = json.load(player_f)
                            try:
                                stats_data = {
                                    "player_id": player_data["id"],
                                    "season": 2025,
                                    "avg": stats.get("avg"),
                                    "ops": stats.get("ops"),
                                    "hr": stats.get("homeRuns"),
                                    "rbi": stats.get("rbi"),
                                    "k_pct": stats.get("strikeOuts", 0) / stats.get("plateAppearances", 1) if stats.get("plateAppearances", 1) > 0 else None,
                                    "contact_pct": stats.get("contactPercentage"),
                                    "whiff_pct": stats.get("whiffPercentage"),
                                    "o_swing_pct": stats.get("outsideSwingPercentage"),
                                    "z_contact_pct": stats.get("zContactPercentage"),
                                }
                                session.merge(Stats(**stats_data))
                            except ZeroDivisionError:
                                logger.error(f"Division by zero for player {player_data['full_name']} (ID: {player_data['id']})")

            session.commit()  # Commit after processing each team to avoid long transactions
        logger.info("All data transferred to the database successfully.")
    except Exception as e:
        logger.error(f"Error transferring data to the database: {e}")
        session.rollback()
    finally:
        session.close()  # Ensure the session is closed properly


def transfer_player_data_to_db():
    """Transfer player data to the SQLite database."""
    session = Session()
    try:
        # Iterate through all player JSON files
        player_files = os.listdir("data/players/")
        for player_file in player_files:
            player_path = os.path.join("data/players/", player_file)
            with open(player_path, "r") as f:
                player_data = json.load(f)

            try:
                player_id = int(player_file.split(".")[0])
                full_name = player_data.get("fullName", "Unknown")

                # Insert player stats into the database
                stats_data = {
                    "player_id": player_id,
                    "season": 2025,
                    "avg": player_data.get("avg"),
                    "ops": player_data.get("ops"),
                    "hr": player_data.get("homeRuns"),
                    "rbi": player_data.get("rbi"),
                    "k_pct": player_data.get("strikeOuts", 0) / player_data.get("plateAppearances", 1) if player_data.get("plateAppearances", 1) > 0 else None,
                    "contact_pct": player_data.get("contactPercentage"),
                    "whiff_pct": player_data.get("whiffPercentage"),
                    "o_swing_pct": player_data.get("outsideSwingPercentage"),
                    "z_contact_pct": player_data.get("zContactPercentage"),
                }

                # Log the player being processed
                logger.info(f"Processing player: {full_name} (ID: {player_id})")

                # Dynamically create a stats table for the player if it doesn't exist
                class PlayerStats(Base):
                    __tablename__ = f"player_{player_id}_stats"

                    player_id = Column(Integer, primary_key=True, nullable=False)
                    season = Column(Integer, primary_key=True, nullable=False)
                    avg = Column(Float, nullable=True)
                    ops = Column(Float, nullable=True)
                    hr = Column(Integer, nullable=True)
                    rbi = Column(Integer, nullable=True)
                    k_pct = Column(Float, nullable=True)
                    contact_pct = Column(Float, nullable=True)
                    whiff_pct = Column(Float, nullable=True)
                    o_swing_pct = Column(Float, nullable=True)
                    z_contact_pct = Column(Float, nullable=True)

                PlayerStats.__name__ = f"PlayerStats_{player_id}"
                Base.metadata.create_all(engine)

                # Insert stats into the player's stats table
                session.merge(PlayerStats(**stats_data))

            except Exception as e:
                logger.error(f"Error processing player file {player_file}: {e}")

        session.commit()
        logger.info("All player data transferred to the database successfully.")
    except Exception as e:
        logger.error(f"Error transferring player data to the database: {e}")
        session.rollback()
    finally:
        session.close()


def sync_teams_and_players():
    """Sync all teams and players into the database."""
    session = SessionLocal()
    try:
        # Fetch all teams from the API
        teams = get_all_teams()
        for team in teams:
            # Insert or ignore team data
            session.execute(text("""
                INSERT OR IGNORE INTO teams (id, name, abbreviation, league, division)
                VALUES (:id, :name, :abbreviation, :league, :division)
            """), team)

            # Fetch team roster
            roster = get_team_roster(team['id'])
            for player in roster:
                # Insert or ignore player data
                session.execute(text("""
                    INSERT OR IGNORE INTO players (id, full_name, team_id, position, is_pitcher, bats, throws)
                    VALUES (:id, :full_name, :team_id, :position, :is_pitcher, :bats, :throws)
                """), {
                    "id": player["player_id"],
                    "full_name": player["full_name"],
                    "team_id": team["id"],
                    "position": player["position"],
                    "is_pitcher": player["position"] == "P",
                    "bats": player.get("bats"),
                    "throws": player.get("throws"),
                })

        session.commit()
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()


def sync_player_stats():
    """Sync all player stats into the database."""
    session = SessionLocal()
    try:
        # Fetch all players from the database
        players = session.execute(text("SELECT id, is_pitcher FROM players")).fetchall()
        for player in players:
            player_id = player["id"]
            is_pitcher = player["is_pitcher"]

            # Fetch stats based on player type
            stats = get_player_pitching_stats(player_id) if is_pitcher else get_player_hitting_stats(player_id)

            # Insert or update stats
            if is_pitcher:
                session.execute(text("""
                    INSERT OR REPLACE INTO pitcher_stats (player_id, season, era, whip, k_pct, k9, whiff_pct, strikeout_walk_ratio)
                    VALUES (:player_id, :season, :era, :whip, :k_pct, :k9, :whiff_pct, :strikeout_walk_ratio)
                """), stats)
            else:
                session.execute(text("""
                    INSERT OR REPLACE INTO hitter_stats (player_id, season, avg, ops, hr, rbi, k_pct, contact_pct, whiff_pct, o_swing_pct, z_contact_pct)
                    VALUES (:player_id, :season, :avg, :ops, :hr, :rbi, :k_pct, :contact_pct, :whiff_pct, :o_swing_pct, :z_contact_pct)
                """), stats)

        session.commit()
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()


def fetch_last_5_games(player_id, group):
    """Fetch and return performance data from the last 5 games for a given player."""
    try:
        season = datetime.date.today().year
        current_date = datetime.date.today()

        # Fetch game logs from the MLB API
        response = requests.get(
            f"{BASE_URL}/people/{player_id}/stats",
            params={"stats": "gameLog", "group": group, "season": season},
        )
        response.raise_for_status()
        stats = response.json().get("stats", [])

        if not stats:
            return []

        # Extract all game logs
        game_logs = stats[0].get("splits", [])

        # Filter games that occurred before the current date
        filtered_logs = [
            game for game in game_logs
            if datetime.datetime.strptime(game.get("date", ""), "%Y-%m-%d").date() < current_date
        ]

        # Sort the games by date in descending order and take the last 5
        filtered_logs.sort(
            key=lambda game: datetime.datetime.strptime(game.get("date", ""), "%Y-%m-%d").date(),
            reverse=True
        )
        last_5_games = filtered_logs[:5]

        # Format the data into a readable table format
        formatted_logs = []
        for game in last_5_games:
            game_data = {
                "date": game.get("date", "N/A"),
                "opponent": game.get("opponent", {}).get("name", "N/A"),
                "result": "Win" if game.get("isWin", False) else "Loss",
                "stats": {
                    "strikeOuts": game.get("stat", {}).get("strikeOuts", "N/A"),
                    "baseOnBalls": game.get("stat", {}).get("baseOnBalls", "N/A"),
                    "earnedRuns": game.get("stat", {}).get("earnedRuns", "N/A"),
                },
            }
            formatted_logs.append(game_data)

        return formatted_logs

    except requests.exceptions.HTTPError as http_err:
        logger.error(f"HTTP error occurred while fetching last 5 games: {http_err}")
        logger.error(f"Response content: {response.text}")
        return []
    except Exception as err:
        logger.error(f"An error occurred while fetching last 5 games: {err}")
        return []


def full_data_pull():
    """Perform a full data pull of all teams and players."""
    logger.info("Starting full data pull of all teams and players.")
    try:
        # Fetch and log all teams
        teams = fetch_teams()
        logger.info(f"Total teams fetched: {len(teams)}")

        for team in teams:
            logger.info(f"Processing team: {team['name']} (ID: {team['id']})")

            # Fetch and log team roster
            roster = fetch_roster(team['id'])
            logger.info(f"Total players in roster for {team['name']}: {len(roster)}")

            for player in roster:
                player_id = player['person']['id']
                player_name = player['person']['fullName']
                position = player['position']['abbreviation']
                logger.info(f"Processing player: {player_name} (ID: {player_id}, Position: {position})")

                # Fetch and log player stats
                if position == "P":
                    stats = fetch_player_stats(player_id, "pitching")
                    logger.info(f"Pitching stats for {player_name}: {stats}")
                else:
                    stats = fetch_player_stats(player_id, "hitting")
                    logger.info(f"Hitting stats for {player_name}: {stats}")

        logger.info("Full data pull completed successfully.")
    except Exception as e:
        logger.error(f"Error during full data pull: {e}")


if __name__ == "__main__":
    full_data_pull()