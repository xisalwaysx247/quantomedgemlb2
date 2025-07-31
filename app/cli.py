import sys
import os

# Ensure the parent directory is in the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Add the MLB-StatsAPI directory to the Python path
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "MLB-StatsAPI"))

# Add the statsapi directory explicitly to the Python path
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "MLB-StatsAPI", "statsapi"))

import typer
from app.db.session import Base, engine
from app.services.loader import load_data
from app.services.data_collector import get_all_teams, get_team_roster, get_player_hitting_stats, get_player_pitching_stats
from quantum_edge import app as quantum_edge_app
import click
from services.mlb_api import get_hit_streak

app = typer.Typer()

@app.command()
def init_db():
    """Create all tables in the database."""
    Base.metadata.create_all(bind=engine)
    typer.echo("Database tables created successfully.")

@app.command()
def sync_data(season: int = 2025):
    """Pull all teams, rosters, and player stats for the given season and store them."""
    typer.echo(f"Syncing data for season {season}...")
    load_data()
    typer.echo("Data sync completed successfully.")

@app.command()
def refresh_database():
    """Refresh the player and team database."""
    try:
        teams = get_all_teams()
        for team in teams:
            typer.echo(f"Processing team: {team['name']}")
            roster = get_team_roster(team['id'])
            for player in roster:
                typer.echo(f"  Player: {player['full_name']} ({player['position']})")
                if player['position'] == 'P':
                    stats = get_player_pitching_stats(player['player_id'])
                else:
                    stats = get_player_hitting_stats(player['player_id'])
                typer.echo(f"    Stats: {stats}")
    except Exception as e:
        typer.echo(f"Error refreshing database: {e}")

@app.command()
def view_player(player_id: int, group: str = "hitting"):
    """View a player's details and last 5 games' stats."""
    from app.services.loader import fetch_last_5_games

    try:
        typer.echo(f"Fetching details for player ID: {player_id}...")

        # Fetch last 5 games' stats
        last_5_games = fetch_last_5_games(player_id, group)

        if not last_5_games:
            typer.echo("No game logs available for this player.")
            return

        # Display the stats in an organized format
        typer.echo("\nLast 5 Games Stats:")
        for game in last_5_games:
            typer.echo(f"Date: {game['date']}, Opponent: {game['opponent']}, Result: {game['result']}")
            typer.echo(f"Stats: {game['stats']}")
            typer.echo("-" * 40)

    except Exception as e:
        typer.echo(f"Error fetching player details: {e}")

@app.command()
@click.option('--player-id', required=True, type=int, help='Player ID to fetch hit streak for.')
def streak(player_id):
    """Fetch and display the hit streak for a player."""
    streak = get_hit_streak(player_id)
    click.echo(f"📈 Hit Streak: {streak} games (last 5 games)")

# Update CLI home screen
app.add_typer(quantum_edge_app, name="quantum-edge")

if __name__ == "__main__":
    typer.echo("[3] Refresh Player + Team Database")
    app()