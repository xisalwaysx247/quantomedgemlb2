import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from app.services.loader import fetch_teams, fetch_roster, fetch_player_stats, fetch_team_stats, fetch_last_5_games
from app.services.mlb_api import fetch_games_for_date
from app.db.session import SessionLocal as Session
from sqlalchemy import text
from tabulate import tabulate
import json
import os
import logging
from datetime import datetime

# Configure logging - Set to WARNING to hide debug logs
logging.basicConfig(level=logging.WARNING, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Initialize Typer app and Rich console
app = typer.Typer()
console = Console()

# Base data folder
DATA_FOLDER = "data"
ROSTERS_FOLDER = os.path.join(DATA_FOLDER, "rosters")
PLAYERS_FOLDER = os.path.join(DATA_FOLDER, "players")
os.makedirs(ROSTERS_FOLDER, exist_ok=True)
os.makedirs(PLAYERS_FOLDER, exist_ok=True)

def quantum_banner():
    """Display the Quantum Edge CLI banner."""
    console.print(Panel("[bold cyan]🧠 Quantum Edge CLI[/bold cyan]\n[green]Explore MLB Data with Futuristic Analytics[/green]", expand=False))

def list_commands():
    """Display available commands in a table format."""
    table = Table(title="Available Commands", show_header=True, header_style="bold cyan")
    table.add_column("Command", style="bright_blue")
    table.add_column("Description", style="green")

    table.add_row("serve", "🌐 Launch Quantum Edge web server.")
    table.add_row("pull-teams", "Pull all teams and save them to /data/teams.json.")
    table.add_row("pull-rosters", "Pull full rosters for all teams and save them.")
    table.add_row("pull-player-stats", "Pull advanced stats for all players.")
    table.add_row("view-team [team_id]", "Show team info and display player list.")
    table.add_row("view-player [player_id]", "Show full advanced stat report for a player.")
    table.add_row("update-all", "Run all data syncs in order.")
    table.add_row("streaks", "Identify players on hit streaks based on their last 5 games.")
    table.add_row("matchup_report", "Generate a Daily Weak Pitcher Matchup Report.")
    table.add_row("all_games", "View all games for a date with interactive matchup analysis.")
    table.add_row("update_streaks", "Update hit streak data for all players and cache results.")
    table.add_row("clear_cache", "Clear all cached matchup report data.")
    table.add_row("refresh_report", "Generate matchup report with fresh data (bypass cache).")

    console.print(table)

@app.command()
def backup_picks():
    """
    💾 Create a backup of the Pick Tank database
    
    Creates a timestamped backup of the entire database to ensure
    your picks are never lost.
    """
    console.print("\n💾 [bold cyan]Creating Pick Tank Backup[/bold cyan]\n")
    
    try:
        from app.db.session import backup_database, DATABASE_FILE
        import os
        
        if not os.path.exists(DATABASE_FILE):
            console.print("[red]❌ Database file not found![/red]")
            return
        
        backup_file = backup_database()
        if backup_file:
            file_size = os.path.getsize(backup_file)
            console.print(f"[green]✅ Backup created successfully![/green]")
            console.print(f"[dim]📁 File: {backup_file}[/dim]")
            console.print(f"[dim]📊 Size: {file_size:,} bytes[/dim]")
            
            # Show some stats
            from app.db.schema import Pick
            from app.db.session import SessionLocal
            
            db = SessionLocal()
            try:
                total_picks = db.query(Pick).count()
                console.print(f"[dim]🎯 Total picks backed up: {total_picks}[/dim]")
            except Exception as e:
                console.print(f"[yellow]⚠️ Could not count picks: {e}[/yellow]")
            finally:
                db.close()
        else:
            console.print("[red]❌ Backup failed![/red]")
            
    except Exception as e:
        console.print(f"[red]❌ Error creating backup: {e}[/red]")

@app.command()
def verify_picks():
    """
    🔍 Verify Pick Tank data integrity
    
    Checks that the picks database is working correctly and
    shows statistics about stored picks.
    """
    console.print("\n🔍 [bold cyan]Pick Tank Data Verification[/bold cyan]\n")
    
    try:
        from app.db.schema import Pick
        from app.db.session import SessionLocal, verify_picks_table
        from sqlalchemy import func
        
        # Verify table exists
        if not verify_picks_table():
            console.print("[red]❌ Pick Tank table verification failed![/red]")
            return
        
        db = SessionLocal()
        try:
            # Test database connection
            from sqlalchemy import text
            db.execute(text("SELECT 1"))
            console.print("[green]✅ Database connection successful[/green]")
            
            # Count total picks
            total_picks = db.query(Pick).count()
            console.print(f"[cyan]📊 Total picks in database: {total_picks}[/cyan]")
            
            if total_picks > 0:
                # Get pick statistics
                pick_types = db.query(Pick.pick_type, func.count(Pick.id)).group_by(Pick.pick_type).all()
                star_dist = db.query(Pick.stars, func.count(Pick.id)).group_by(Pick.stars).order_by(Pick.stars).all()
                
                console.print("\n[bold]📈 Pick Type Distribution:[/bold]")
                for pick_type, count in pick_types:
                    console.print(f"  {pick_type}: {count}")
                
                console.print("\n[bold]⭐ Star Rating Distribution:[/bold]")
                for stars, count in star_dist:
                    star_display = "⭐" * stars
                    console.print(f"  {star_display} ({stars}): {count}")
                
                # Show recent picks
                recent_picks = db.query(Pick).order_by(Pick.created_at.desc()).limit(5).all()
                if recent_picks:
                    console.print("\n[bold]🕒 Recent Picks:[/bold]")
                    for pick in recent_picks:
                        created = pick.created_at.strftime("%Y-%m-%d %H:%M") if pick.created_at else "Unknown"
                        stars = "⭐" * pick.stars
                        console.print(f"  {stars} {pick.selection} ({created})")
            else:
                console.print("[yellow]No picks found in database[/yellow]")
                console.print("[dim]Add picks through the web interface: python quantum_edge.py serve[/dim]")
            
            console.print(f"\n[green]✅ Pick Tank verification complete[/green]")
            
        except Exception as e:
            console.print(f"[red]❌ Database error: {e}[/red]")
        finally:
            db.close()
            
    except Exception as e:
        console.print(f"[red]❌ Verification error: {e}[/red]")

@app.command()
def list_picks(date: str = None):
    """
    📋 List betting picks for a specific date
    
    Shows all picks stored in the Pick Tank for analysis and tracking.
    
    Args:
        date: Date to show picks for (YYYY-MM-DD). Defaults to today.
    """
    if not date:
        date = datetime.now().strftime("%Y-%m-%d")
    
    try:
        # Validate date format
        datetime.strptime(date, "%Y-%m-%d")
    except ValueError:
        console.print("[red]❌ Invalid date format. Use YYYY-MM-DD[/red]")
        return
    
    console.print(f"\n🎯 [bold cyan]Pick Tank - {date}[/bold cyan]\n")
    
    # Import here to avoid circular imports
    from app.db.schema import Pick
    from app.db.session import SessionLocal
    
    db = SessionLocal()
    try:
        # Get picks for the date (we'll approximate by created_at date)
        from datetime import timedelta
        start_date = datetime.strptime(date, "%Y-%m-%d")
        end_date = start_date + timedelta(days=1)
        
        picks = db.query(Pick).filter(
            Pick.created_at >= start_date,
            Pick.created_at < end_date
        ).order_by(Pick.created_at.desc()).all()
        
        if not picks:
            console.print(f"[yellow]No picks found for {date}[/yellow]")
            console.print("[dim]Add picks through the web interface: python quantum_edge.py serve[/dim]")
            return
        
        # Group picks by game
        picks_by_game = {}
        for pick in picks:
            if pick.game_pk not in picks_by_game:
                picks_by_game[pick.game_pk] = []
            picks_by_game[pick.game_pk].append(pick)
        
        total_picks = len(picks)
        console.print(f"[green]Found {total_picks} pick(s) across {len(picks_by_game)} game(s)[/green]\n")
        
        for game_pk, game_picks in picks_by_game.items():
            console.print(f"[bold]🔷 Game {game_pk}[/bold]")
            
            # Create table for this game's picks
            table = Table(show_header=True, header_style="bold magenta")
            table.add_column("⭐", style="cyan", width=8)
            table.add_column("Type", style="yellow", width=8)
            table.add_column("Market", style="blue", width=20)
            table.add_column("Selection", style="green", width=25)
            table.add_column("Odds", style="magenta", width=8)
            table.add_column("Comment", style="white", width=30)
            table.add_column("Time", style="dim", width=8)
            
            for pick in game_picks:
                stars = "⭐" * pick.stars
                comment = (pick.comment[:27] + "...") if pick.comment and len(pick.comment) > 30 else (pick.comment or "")
                time_str = pick.created_at.strftime("%H:%M") if pick.created_at else ""
                
                table.add_row(
                    stars,
                    pick.pick_type,
                    pick.market,
                    pick.selection,
                    pick.odds or "",
                    comment,
                    time_str
                )
            
            console.print(table)
            console.print()
        
        # Export as JSON option
        export_data = []
        for pick in picks:
            export_data.append({
                "game_pk": pick.game_pk,
                "pick_type": pick.pick_type,
                "market": pick.market,
                "selection": pick.selection,
                "odds": pick.odds,
                "stars": pick.stars,
                "comment": pick.comment,
                "created_at": pick.created_at.isoformat() if pick.created_at else None
            })
        
        console.print(f"[dim]💾 Data available as JSON: {json.dumps(export_data, indent=2)}[/dim]")
        
    except Exception as e:
        console.print(f"[red]❌ Error fetching picks: {e}[/red]")
    finally:
        db.close()

@app.command()
def main():
    """Main entry point for the CLI."""
    quantum_banner()
    list_commands()

@app.command()
def pull_teams():
    """Pull all teams and save them to /data/teams.json."""
    console.print("[cyan]Pulling all teams...[/cyan]")
    teams = fetch_teams()
    file_path = os.path.join(DATA_FOLDER, "teams.json")
    with open(file_path, "w") as f:
        json.dump(teams, f, indent=4)
    console.print(f"[green]Teams data saved to {file_path}[/green]")

@app.command()
def pull_rosters():
    """For each team, pull full roster and save as /data/rosters/{team_id}.json."""
    console.print("[cyan]Pulling rosters for all teams...[/cyan]")
    teams_file = os.path.join(DATA_FOLDER, "teams.json")
    if not os.path.exists(teams_file):
        console.print("[red]Teams data not found. Please run 'pull-teams' first.[/red]")
        return

    with open(teams_file, "r") as f:
        teams = json.load(f)

    for team in teams:
        team_id = team.get("id")
        if team_id:
            roster = fetch_roster(team_id)
            roster_file = os.path.join(ROSTERS_FOLDER, f"{team_id}.json")
            with open(roster_file, "w") as f:
                json.dump(roster, f, indent=4)
            console.print(f"[green]Roster for team {team_id} saved to {roster_file}[/green]")

@app.command()
def pull_player_stats():
    """For each player, pull advanced stats and store in /data/players/{player_id}.json."""
    console.print("[cyan]Pulling player stats for all rosters...[/cyan]")
    logger.debug("Starting to pull player stats for all rosters.")
    for roster_file in os.listdir(ROSTERS_FOLDER):
        roster_path = os.path.join(ROSTERS_FOLDER, roster_file)
        logger.debug(f"Processing roster file: {roster_path}")
        with open(roster_path, "r") as f:
            roster = json.load(f)
            logger.debug(f"Loaded roster data: {roster}")

        for player in roster:
            player_id = player.get("person", {}).get("id")
            full_name = player.get("person", {}).get("fullName", "Unknown")
            logger.debug(f"Processing player: {full_name} (ID: {player_id})")
            if player_id:
                group = "pitching" if player.get("position", {}).get("abbreviation") == "P" else "hitting"
                stats_response = fetch_player_stats(player_id, group)
                logger.debug(f"Raw stats response for player {full_name}: {stats_response}")
                
                # Extract the actual stats from the API response structure
                extracted_stats = {}
                if stats_response and len(stats_response) > 0:
                    splits = stats_response[0].get("splits", [])
                    if splits and len(splits) > 0:
                        extracted_stats = splits[0].get("stat", {})
                
                # Add player metadata
                extracted_stats["id"] = player_id
                extracted_stats["fullName"] = full_name
                extracted_stats["position"] = player.get("position", {}).get("abbreviation", "")
                
                logger.debug(f"Extracted stats for player {full_name}: {extracted_stats}")
                player_file = os.path.join(PLAYERS_FOLDER, f"{player_id}.json")
                with open(player_file, "w") as f:
                    json.dump(extracted_stats, f, indent=4)
                logger.debug(f"Saved stats for player {full_name} to {player_file}")
                console.print(f"[green]Stats for player {full_name} (ID: {player_id}) saved to {player_file}[/green]")

@app.command()
def view_team(team_name: str):
    """Show team info and display team averages only."""
    team, stats = get_team_stats_by_name_from_files(team_name)
    if not team:
        console.print(f"[red]Team '{team_name}' not found in JSON files.[/red]")
        return

    # Display team stats
    console.print(Panel(f"[bold cyan]Team {team_name} Overall Season Averages[/bold cyan]", expand=False))
    if stats:
        for key, value in stats.items():
            console.print(f"[green]{key}:[/green] {value}")
    else:
        console.print("[yellow]No stats available for this team.[/yellow]")

def get_player_id_by_name_from_files(player_name):
    """Search for a player ID by name in the JSON files."""
    for player_file in os.listdir(PLAYERS_FOLDER):
        player_path = os.path.join(PLAYERS_FOLDER, player_file)
        try:
            with open(player_path, "r") as f:
                player_data = json.load(f)
                if player_name.lower() in player_data.get("fullName", "").lower():
                    return player_data.get("id")
        except json.JSONDecodeError as e:
            logger.error(f"Error decoding JSON in file {player_path}: {e}")
        except Exception as e:
            logger.error(f"Unexpected error while processing file {player_path}: {e}")
    return None

@app.command()
def view_player(player_name):
    """Show full advanced stat report in CLI with rich formatting."""
    player_id = get_player_id_by_name_from_files(player_name)
    if not player_id:
        console.print(f"[red]Player '{player_name}' not found in JSON files.[/red]")
        logger.debug(f"Player '{player_name}' not found in JSON files.")
        return

    player_file = os.path.join(PLAYERS_FOLDER, f"{player_id}.json")
    if not os.path.exists(player_file):
        console.print(f"[red]Stats for player {player_name} not found. Please run 'pull-player-stats' first.[/red]")
        logger.debug(f"Stats for player {player_name} not found. File does not exist: {player_file}")
        return

    try:
        with open(player_file, "r") as f:
            stats = json.load(f)
    except Exception as e:
        console.print(f"[red]Error loading stats for player {player_name}: {e}[/red]")
        logger.error(f"Error loading stats for player {player_name}: {e}")
        return

    console.print(Panel(f"[bold cyan]Player {player_name} Advanced Stats[/bold cyan]", expand=False))

    # Display advanced stats in a table
    stats_table = Table(title=f"Player {player_name} Advanced Stats", show_header=True, header_style="bold cyan")
    stats_table.add_column("Stat", style="green")
    stats_table.add_column("Value", style="bright_blue")

    for key, value in stats.items():
        stats_table.add_row(key, str(value))

    console.print(stats_table)

    # Fetch and display last 5 games' stats in a more focused format
    last_5_games = fetch_last_5_games(player_id, "pitching")

    if last_5_games:
        games_table = Table(title="Last 5 Games Stats", show_header=True, header_style="bold cyan")
        games_table.add_column("Date", style="green")
        games_table.add_column("Opponent", style="bright_blue")
        games_table.add_column("Result", style="yellow")
        games_table.add_column("Strikeouts", style="magenta")
        games_table.add_column("Earned Runs", style="magenta")
        games_table.add_column("Base on Balls", style="magenta")

        for game in last_5_games:
            stats = game.get('stats', {})
            games_table.add_row(
                game['date'],
                game['opponent'],
                "Win" if game['result'] else "Loss",
                str(stats.get('strikeOuts', "N/A")),
                str(stats.get('earnedRuns', "N/A")),
                str(stats.get('baseOnBalls', "N/A"))
            )

        console.print(games_table)
    else:
        console.print("[yellow]No game logs available for this player.[/yellow]")

@app.command()
def update_all():
    """Run all data syncs above in order."""
    console.print("[cyan]Running full data sync...[/cyan]")
    pull_teams()
    pull_rosters()
    pull_player_stats()
    console.print("[green]All data synced successfully![/green]")

# Updated main menu to exclude search functionality
def main_menu():
    """Display the main menu with numbered commands and handle user selection."""
    quantum_banner()

    table = Table(title="Available Commands", show_header=True, header_style="bold cyan")
    table.add_column("Number", style="bright_blue")
    table.add_column("Command", style="green")
    table.add_column("Description", style="green")

    commands = [
        ("1", "serve", "🌐 Launch Quantum Edge web server."),
        ("2", "pull-teams", "Pull all teams and save them to /data/teams.json."),
        ("3", "pull-rosters", "Pull full rosters for all teams and save them."),
        ("4", "pull-player-stats", "Pull advanced stats for all players."),
        ("5", "view-team", "Show team info and display player list."),
        ("6", "view-player", "Show full advanced stat report for a player."),
        ("7", "update-all", "Run all data syncs in order."),
        ("8", "exit", "Exit the CLI."),
        ("9", "streaks", "Identify players on hit streaks based on their last 5 games."),
        ("10", "matchup_report", "Generate a Daily Weak Pitcher Matchup Report."),
        ("11", "clear_cache", "Clear all cached matchup report data."),
        ("12", "refresh_report", "Generate matchup report with fresh data (bypass cache)."),
        ("13", "all-games", "View all games for a date with interactive matchup analysis."),
        ("14", "update-streaks", "Update hit streak data for all players and cache results."),
    ]

    for command in commands:
        table.add_row(*command)

    console.print(table)

    while True:
        choice = console.input("[bold cyan]Select a command by number: [/bold cyan]")
        if choice == "1":
            serve()
        elif choice == "2":
            pull_teams()
        elif choice == "3":
            pull_rosters()
        elif choice == "4":
            pull_player_stats()
        elif choice == "5":
            team_name = console.input("[bold cyan]Enter team name: [/bold cyan]")
            view_team(team_name)
        elif choice == "6":
            player_name = console.input("[bold cyan]Enter player name: [/bold cyan]")
            view_player(player_name)
        elif choice == "7":
            update_all()
        elif choice == "8":
            console.print("[bold green]Exiting Quantum Edge CLI. Goodbye![/bold green]")
            break
        elif choice == "9":
            streaks()
        elif choice == "10":
            date = console.input("[bold cyan]Enter date for matchup report (YYYY-MM-DD): [/bold cyan]")
            matchup_report(date=date)
        elif choice == "11":
            clear_cache()
        elif choice == "12":
            date = console.input("[bold cyan]Enter date for matchup report (YYYY-MM-DD): [/bold cyan]")
            matchup_report(date=date, force_refresh=True)
        elif choice == "13":
            date = console.input("[bold cyan]Enter date for all games report (YYYY-MM-DD): [/bold cyan]")
            all_games(date=date)
        elif choice == "14":
            update_streaks()
        else:
            console.print("[bold red]Invalid choice. Please select a valid command number.[/bold red]")

# Add an interactive menu command
@app.command("menu")
def interactive_menu():
    """Launch the interactive menu with numbered commands."""
    main_menu()

def get_team_stats_by_name_from_files(team_name):
    """Search for a team by name in the JSON file and fetch overall season stats."""
    teams_file = os.path.join(DATA_FOLDER, "teams.json")
    if not os.path.exists(teams_file):
        console.print("[red]Teams data not found. Please run 'pull-teams' first.[/red]")
        return None, None

    with open(teams_file, "r") as f:
        teams = json.load(f)
        for team in teams:
            if team_name.lower() in team.get("name", "").lower():
                team_id = team.get("id")
                stats = fetch_team_stats(team_id)  # Fetch overall season stats from the API
                return team, stats
    return None, None

def search_player(player_id: int, group: str = "hitting"):
    """Search for a player and display their details along with the last 5 games' stats."""
    try:
        print(f"Searching for player ID: {player_id}...")

        # Fetch last 5 games' stats
        last_5_games = fetch_last_5_games(player_id, group)

        if not last_5_games:
            print("No game logs available for this player.")
            return

        # Display the stats in an organized format
        print("\nLast 5 Games Stats:")
        for game in last_5_games:
            print(f"Date: {game['date']}, Opponent: {game['opponent']}, Result: {game['result']}")
            print(f"Stats: {game['stats']}")
            print("-" * 40)

    except Exception as e:
        print(f"Error fetching player details: {e}")

@app.command()
def update_player_stats():
    """Update player JSON files with missing stats (strikeouts, earned runs, base on balls)."""
    console.print("[cyan]Updating player stats...[/cyan]")
    logger.debug("Starting to update player stats.")

    for player_file in os.listdir(PLAYERS_FOLDER):
        player_path = os.path.join(PLAYERS_FOLDER, player_file)
        logger.debug(f"Processing player file: {player_path}")

        with open(player_path, "r") as f:
            player_data = json.load(f)

        player_id = player_data.get("id")
        if not player_id:
            logger.warning(f"Player ID missing in file: {player_file}")
            continue

        group = "pitching" if player_data.get("position", {}).get("abbreviation") == "P" else "hitting"

        try:
            stats = fetch_player_stats(player_id, group)
            player_data.update({
                "strikeouts": stats.get("strikeOuts", "N/A"),
                "earned_runs": stats.get("earnedRuns", "N/A"),
                "base_on_balls": stats.get("baseOnBalls", "N/A"),
            })

            with open(player_path, "w") as f:
                json.dump(player_data, f, indent=4)

            logger.debug(f"Updated stats for player ID {player_id} in file {player_file}.")
        except Exception as e:
            logger.error(f"Failed to update stats for player ID {player_id}: {e}")

    console.print("[green]Player stats update completed.[/green]")

@app.command()
def streaks():
    """Identify hitters on hit streaks of 2 or more games and cache the results dynamically."""
    from app.services.mlb_api import get_hit_streak, get_last_10_games
    import os
    import json

    console.print("[cyan]Updating cached list of hitters on hit streaks...[/cyan]")

    players_folder = os.path.join("data", "players")
    teams_file = os.path.join("data", "teams.json")
    cache_file = os.path.join("data", "hit_streaks_cache.json")

    if not os.path.exists(teams_file):
        console.print("[red]Teams data not found. Please run 'pull-teams' first.[/red]")
        return

    with open(teams_file, "r") as f:
        teams = {team["id"]: team["name"] for team in json.load(f)}

    hitters_on_streak = []

    for player_file in os.listdir(players_folder):
        if player_file.endswith(".json"):
            player_path = os.path.join(players_folder, player_file)
            with open(player_path, "r") as f:
                player_data = json.load(f)

            player_id = player_data.get("id")
            full_name = player_data.get("fullName", "Unknown")
            team_id = player_data.get("currentTeam", {}).get("id")
            team_name = teams.get(team_id, "Unknown Team")

            # If team_name is still "Unknown Team", attempt to fetch it from player data
            if team_name == "Unknown Team":
                team_name = player_data.get("currentTeam", {}).get("name", "Unknown Team")

            # Fetch team name using helper function
            team_name = get_team_name(team_id, teams)

            # If team_name is still "Unknown Team", attempt to find it by player name
            if team_name == "Unknown Team":
                team_name = find_team_name_by_player_name(full_name, teams)

            # Skip players who are not hitters
            position = player_data.get("primaryPosition", {}).get("abbreviation", "")
            if position == "P":
                continue

            try:
                games = get_last_10_games(player_id, group="hitting", season=2025)
                if not games:
                    console.print(f"[yellow]No game logs found for player {full_name}.[/yellow]")
                    continue

                streak = get_hit_streak(player_id, num_games=10)
                if streak >= 2:
                    hitters_on_streak.append({"name": full_name, "team": team_name, "streak": streak})
            except IndexError:
                console.print(f"[yellow]No valid game data for player {full_name}.[/yellow]")
            except Exception as e:
                console.print(f"[red]Error processing player {full_name}: {e}[/red]")

    # Sort hitters by streak length in descending order
    hitters_on_streak.sort(key=lambda x: x["streak"], reverse=True)

    # Cache the sorted results
    with open(cache_file, "w") as f:
        json.dump(hitters_on_streak, f, indent=4)

    console.print("[green]Cached list of hitters on hit streaks updated successfully![/green]")

    # Display the cached results
    if hitters_on_streak:
        table = Table(title="Hitters on Hit Streaks (2+ Games)", show_header=True, header_style="bold green")
        table.add_column("Player", style="cyan")
        table.add_column("Team", style="magenta")
        table.add_column("Hit Streak", style="yellow")
        table.add_row("", "", "")  # Add a line separator

        for hitter in hitters_on_streak:
            table.add_row(hitter["name"], hitter["team"], str(hitter["streak"]))
            table.add_row("", "", "")  # Add a line separator after each player

        console.print(table)
    else:
        console.print("[red]No hitters on hit streaks of 2 or more games found.[/red]")

def get_team_name(team_id, teams):
    """Helper function to fetch the team name for a given team ID."""
    return teams.get(team_id, "Unknown Team")

def find_team_name_by_player_name(player_name, teams):
    """Search for a player's team name by matching the player's name in the teams data."""
    for team_id, team_name in teams.items():
        roster_file = os.path.join("data", "rosters", f"{team_id}.json")
        if os.path.exists(roster_file):
            with open(roster_file, "r") as f:
                roster = json.load(f)
                for player in roster:
                    if player_name.lower() in player.get("person", {}).get("fullName", "").lower():
                        return team_name
    return "Unknown Team"

@app.command()
def matchup_report(weak_pitchers: bool = False, date: str = None, use_cache: bool = True, force_refresh: bool = False):
    """Generate a Daily Weak Pitcher Matchup Report with interactive game selection."""
    from app.services.mlb_api import is_weak_pitcher, classify_hitter, get_hit_streak, fetch_team_roster
    import os
    import json
    from datetime import datetime

    # Helper function to safely format numeric values from JSON
    def safe_format(value, decimals=3, default="N/A"):
        if value is None or value == "N/A":
            return default
        try:
            return f"{float(value):.{decimals}f}"
        except (ValueError, TypeError):
            return default

    if not date:
        console.print("[red]Please provide a date in the format YYYY-MM-DD.[/red]")
        return

    try:
        report_date = datetime.strptime(date, "%Y-%m-%d")
    except ValueError:
        console.print("[red]Invalid date format. Please use YYYY-MM-DD.[/red]")
        return

    if force_refresh:
        use_cache = False
    
    # Fetch games for the given date (silently)
    games = fetch_games_for_date(date, use_cache=use_cache)
    if not games:
        console.print(f"[yellow]No games found for {date}.[/yellow]")
        return

    weak_pitcher_games = []
    
    # First pass: identify games with weak pitchers
    for game in games:
        home_team = game.get("teams", {}).get("home", {}).get("team", {}).get("name", "Unknown")
        away_team = game.get("teams", {}).get("away", {}).get("team", "Unknown")
        home_team_id = game.get("teams", {}).get("home", {}).get("team", {}).get("id")
        away_team_id = game.get("teams", {}).get("away", {}).get("team", {}).get("id")
        
        home_pitcher = game.get("home_pitcher", {})
        away_pitcher = game.get("away_pitcher", {})
        
        # Check each pitcher for weakness
        weak_pitchers_found = []
        
        for pitcher_key, opponent_team_id, pitcher_team, opponent_team in [
            ("home_pitcher", away_team_id, home_team, away_team), 
            ("away_pitcher", home_team_id, away_team, home_team)
        ]:
            pitcher = game.get(pitcher_key, {})
            pitcher_name = pitcher.get("fullName", "Unknown")
            
            if pitcher_name != "TBD" and pitcher and is_weak_pitcher(pitcher.get("stats", {})):
                weak_pitchers_found.append({
                    "pitcher": pitcher,
                    "pitcher_team": pitcher_team,
                    "opponent_team": opponent_team,
                    "opponent_team_id": opponent_team_id
                })
        
        if weak_pitchers_found:
            weak_pitcher_games.append({
                "game": game,
                "home_team": home_team,
                "away_team": away_team,
                "weak_pitchers": weak_pitchers_found
            })

    if not weak_pitcher_games:
        console.print(f"[green]🎯 No weak pitchers identified for {date}[/green]")
        console.print(f"[yellow]All pitchers meet strength criteria - no favorable matchups found.[/yellow]")
        return

    # Display header and menu
    console.print(f"\n[bold red]⚠️ WEAK PITCHER ALERT - {date} ⚠️[/bold red]")
    console.print(f"[green]Found {len(weak_pitcher_games)} game(s) with weak pitcher matchups![/green]\n")

    # Create interactive menu for game selection
    def display_game_menu():
        table = Table(title=f"Weak Pitcher Games - {date}", show_header=True, header_style="bold cyan")
        table.add_column("Game #", style="bright_blue", width=8)
        table.add_column("Matchup", style="green", width=35)
        table.add_column("Weak Pitcher", style="red", width=25)

        for i, game_info in enumerate(weak_pitcher_games, 1):
            # Clean team name extraction
            away_team = game_info.get('away_team', 'Unknown')
            home_team = game_info.get('home_team', 'Unknown')
            
            # Ensure we only show team names, not API objects
            if isinstance(away_team, dict):
                away_team = away_team.get('name', 'Unknown')
            if isinstance(home_team, dict):
                home_team = home_team.get('name', 'Unknown')
                
            matchup = f"{away_team} @ {home_team}"
            
            # Get clean pitcher name for display
            weak_pitchers_list = game_info.get('weak_pitchers', [])
            if weak_pitchers_list:
                pitcher = weak_pitchers_list[0].get('pitcher', {})
                pitcher_name = pitcher.get('fullName', 'Unknown')
                # If multiple weak pitchers, show the first one with indicator
                if len(weak_pitchers_list) > 1:
                    pitcher_display = f"{pitcher_name} (+{len(weak_pitchers_list)-1})"
                else:
                    pitcher_display = pitcher_name
            else:
                pitcher_display = "Unknown"
            
            # Add row to table with clean data only
            table.add_row(
                str(i), 
                matchup, 
                pitcher_display
            )

        console.print(table)
        console.print(f"\n[cyan]Select a game (1-{len(weak_pitcher_games)}) | 'all' for complete report | 'back' to main menu[/cyan]")

    def display_game_analysis(game_index):
        """Display detailed analysis for a specific game."""
        if game_index < 0 or game_index >= len(weak_pitcher_games):
            console.print("[red]Invalid game number.[/red]")
            return

        game_info = weak_pitcher_games[game_index]
        game = game_info["game"]
        
        console.print(f"\n[bold blue]🔷 GAME ANALYSIS: {game_info['away_team']} @ {game_info['home_team']}[/bold blue]")
        
        for weak_pitcher_info in game_info["weak_pitchers"]:
            pitcher = weak_pitcher_info["pitcher"]
            pitcher_team = weak_pitcher_info["pitcher_team"]
            opponent_team = weak_pitcher_info["opponent_team"]
            opponent_team_id = weak_pitcher_info["opponent_team_id"]
            
            pitcher_name = pitcher.get("fullName", "Unknown")
            stats = pitcher.get("stats", {})
            
            # Pitcher Summary Table
            console.print(f"\n[bold red]⚠️ WEAK PITCHER: {pitcher_name} ({pitcher_team})[/bold red]")
            
            pitcher_table = Table(title=f"{pitcher_name} - Season Stats", show_header=True, header_style="bold red")
            pitcher_table.add_column("Stat", style="white")
            pitcher_table.add_column("Value", style="red")
            pitcher_table.add_column("MLB Avg", style="dim")
            
            pitcher_table.add_row("ERA", f"{stats.get('era', 'N/A')}", "~4.20")
            pitcher_table.add_row("WHIP", f"{stats.get('whip', 'N/A')}", "~1.30")
            pitcher_table.add_row("BAA", f"{stats.get('avg', 'N/A')}", "~.240")
            pitcher_table.add_row("H/9", f"{stats.get('hitsPer9Inn', 'N/A')}", "~8.50")
            pitcher_table.add_row("K/9", f"{stats.get('strikeoutsPer9Inn', 'N/A')}", "~8.50")
            pitcher_table.add_row("BB/9", f"{stats.get('walksPer9Inn', 'N/A')}", "~3.20")
            pitcher_table.add_row("IP", f"{stats.get('inningsPitched', 'N/A')}", "-")
            pitcher_table.add_row("Hits", f"{stats.get('hits', 'N/A')}", "-")
            
            # Format win-loss record
            wins = stats.get('wins', 0)
            losses = stats.get('losses', 0)
            win_loss_record = f"{wins}-{losses}" if wins != 'N/A' and losses != 'N/A' else "N/A"
            pitcher_table.add_row("W-L", win_loss_record, "-")
            
            console.print(pitcher_table)
            
            # Opponent Hitting Table
            console.print(f"\n[bold green]🎯 {opponent_team} Hitters vs Weak Pitcher[/bold green]")
            
            roster = fetch_team_roster(opponent_team_id)
            if roster:
                hitting_table = Table(title=f"{opponent_team} Lineup Analysis", show_header=True, header_style="bold green")
                hitting_table.add_column("Tier", style="cyan", width=6)
                hitting_table.add_column("Player", style="magenta", width=20)
                hitting_table.add_column("Pos", style="white", width=4)
                hitting_table.add_column("AVG", style="yellow", width=6)
                hitting_table.add_column("HR", style="yellow", width=4)
                hitting_table.add_column("RBI", style="yellow", width=4)
                hitting_table.add_column("OPS", style="yellow", width=6)
                hitting_table.add_column("Streak", style="bright_yellow", width=6)

                # Collect all hitters first
                all_hitters = []
                
                # Initialize the tier count lists here
                strong_hitters = []
                bubble_hitters = []
                weak_hitters = []
                
                for player in roster:
                    # Skip pitchers
                    position = player.get("position", {}).get("abbreviation", "")
                    if position == "P":
                        continue
                        
                    player_id = player.get("person", {}).get("id")
                    player_name = player.get("person", {}).get("fullName", "Unknown")
                    
                    # Try to get player stats from local files
                    hitter_stats = {}
                    hit_streak = 0
                    try:
                        player_file = os.path.join("data", "players", f"{player_id}.json")
                        if os.path.exists(player_file):
                            with open(player_file, "r") as f:
                                player_data = json.load(f)
                                hitter_stats = player_data
                        hit_streak = get_hit_streak(player_id) if player_id else 0
                    except Exception as e:
                        logger.debug(f"Could not get stats for player {player_name}: {e}")
                    
                    tier = classify_hitter(hitter_stats)
                    
                    # Helper function to safely get ERA
                    def get_era_value(stats):
                        era = stats.get('era', 0)
                        try:
                            return float(era) if era else 0.0
                        except (ValueError, TypeError):
                            return 0.0
                    
                    era_value = get_era_value(hitter_stats)
                    
                    player_row = {
                        "tier": tier,
                        "name": player_name,
                        "position": position,
                        "era": era_value,
                        "avg": safe_format(hitter_stats.get('avg')),
                        "hr": str(hitter_stats.get("homeRuns", "N/A")),
                        "rbi": str(hitter_stats.get("rbi", "N/A")),
                        "ops": safe_format(hitter_stats.get('ops')),
                        "streak": str(hit_streak) if hit_streak > 0 else "0",
                    }
                    
                    all_hitters.append(player_row)

                # Sort hitters by batting average in descending order, then by tier priority
                def sort_key(hitter):
                    # Primary sort: Batting Average descending (highest first)
                    # Secondary sort: Tier priority (Strong > Bubble > Weak > No Data)
                    tier_priority = {"🟢": 0, "🟡": 1, "🔴": 2, "❓": 3}
                    
                    # Get batting average value for sorting
                    avg_str = hitter["avg"]
                    try:
                        avg_value = float(avg_str) if avg_str != "N/A" else 0.0
                    except (ValueError, TypeError):
                        avg_value = 0.0
                    
                    return (-avg_value, tier_priority.get(hitter["tier"], 4))
                
                all_hitters.sort(key=sort_key)

                # Add top 9 hitters to table (likely lineup) and categorize them
                for i, hitter in enumerate(all_hitters):
                    hitting_table.add_row(
                        hitter["tier"],
                        hitter["name"],
                        hitter["position"],
                        hitter["avg"],
                        hitter["hr"],
                        hitter["rbi"],
                        hitter["ops"],
                        hitter["streak"]
                    )
                    
                    # Count by tier for summary
                    if hitter["tier"] == "🟢":
                        strong_hitters.append(hitter)
                    elif hitter["tier"] == "🟡":
                        bubble_hitters.append(hitter)
                    else:  # 🔴 or ❓
                        weak_hitters.append(hitter)

                console.print(hitting_table)
                
                # Display roster depth information
                console.print(f"\n[bold cyan]📊 Complete Roster Analysis ({len(all_hitters)} total hitters)[/bold cyan]")
                
                # Summary for ALL hitters with context-aware recommendations
                if len(all_hitters) > 0:
                    strong_pct = len(strong_hitters) / len(all_hitters) * 100
                    bubble_pct = len(bubble_hitters) / len(all_hitters) * 100
                    weak_pct = len(weak_hitters) / len(all_hitters) * 100
                    
                    # Summary stats table for entire roster
                    summary_table = Table(title=f"{opponent_team} Complete Roster Summary", show_header=True, header_style="bold cyan")
                    summary_table.add_column("Category", style="cyan")
                    summary_table.add_column("Count", style="yellow")
                    summary_table.add_column("Percentage", style="green")
                    
                    summary_table.add_row("🟢 Strong Hitters", str(len(strong_hitters)), f"{strong_pct:.1f}%")
                    summary_table.add_row("🟡 Bubble Hitters", str(len(bubble_hitters)), f"{bubble_pct:.1f}%")
                    summary_table.add_row("🔴 Weak Hitters", str(len(weak_hitters)), f"{weak_pct:.1f}%")
                    summary_table.add_row("Total Roster Hitters", str(len(all_hitters)), "100.0%")
                    
                    # Add likely starting lineup analysis
                    if len(all_hitters) >= 9:
                        top_9_strong = sum(1 for h in all_hitters[:9] if h["tier"] == "🟢")
                        top_9_bubble = sum(1 for h in all_hitters[:9] if h["tier"] == "🟡")
                        top_9_weak = 9 - top_9_strong - top_9_bubble
                        
                        summary_table.add_row("", "", "")  # Separator
                        summary_table.add_row("🏟️ Likely Lineup (Top 9)", "", "")
                        summary_table.add_row("  🟢 Strong in Lineup", str(top_9_strong), f"{top_9_strong/9*100:.1f}%")
                        summary_table.add_row("  🟡 Bubble in Lineup", str(top_9_bubble), f"{top_9_bubble/9*100:.1f}%")
                        summary_table.add_row("  🔴 Weak in Lineup", str(top_9_weak), f"{top_9_weak/9*100:.1f}%")
                    
                    console.print(summary_table)
                    
                    # Bench depth analysis
                    if len(all_hitters) > 9:
                        bench_hitters = all_hitters[9:]
                        bench_strong = sum(1 for h in bench_hitters if h["tier"] == "🟢")
                        bench_bubble = sum(1 for h in bench_hitters if h["tier"] == "🟡")
                        bench_weak = len(bench_hitters) - bench_strong - bench_bubble
                        
                        console.print(f"\n[bold yellow]🛏️ Bench Depth Analysis ({len(bench_hitters)} players)[/bold yellow]")
                        console.print(f"[green]🟢 Strong bench players: {bench_strong}[/green]")
                        console.print(f"[yellow]🟡 Bubble bench players: {bench_bubble}[/yellow]")
                        console.print(f"[red]🔴 Weak bench players: {bench_weak}[/red]")
                        
                        if bench_strong > 2:
                            console.print(f"[bold green]💪 EXCELLENT DEPTH: {bench_strong} strong hitters available off the bench![/bold green]")
                        elif bench_strong > 0:
                            console.print(f"[green]✅ GOOD DEPTH: {bench_strong} strong bench option(s) available[/green]")
                        else:
                            console.print(f"[yellow]⚠️ LIMITED DEPTH: No strong hitters on the bench[/yellow]")

                    # Context-aware recommendations based on pitcher strength
                    is_weak_pitcher_result = is_weak_pitcher(stats)
                    if is_weak_pitcher_result:
                        # Against weak pitchers - look for offensive opportunities
                        lineup_strong_pct = (top_9_strong/9*100) if len(all_hitters) >= 9 else strong_pct
                        if lineup_strong_pct > 30:
                            console.print(f"[bold green]💰 EXCELLENT OPPORTUNITY: {lineup_strong_pct:.1f}% strong hitters in likely lineup vs weak pitcher![/bold green]")
                        elif lineup_strong_pct > 15:
                            console.print(f"[bold yellow]⚡ GOOD OPPORTUNITY: {lineup_strong_pct:.1f}% strong hitters in likely lineup vs weak pitcher![/bold yellow]")
                        elif len(all_hitters) >= 9 and (top_9_bubble/9*100) > 40:
                            console.print(f"[yellow]📊 MODERATE OPPORTUNITY: {top_9_bubble/9*100:.1f}% bubble hitters in lineup vs weak pitcher[/yellow]")
                        else:
                            console.print(f"[dim]📋 LIMITED OPPORTUNITY: Mostly weak lineup vs weak pitcher[/dim]")
                    else:
                        # Against strong pitchers - assess difficulty
                        lineup_strong_pct = (top_9_strong/9*100) if len(all_hitters) >= 9 else strong_pct
                        lineup_weak_pct = (top_9_weak/9*100) if len(all_hitters) >= 9 else weak_pct
                        if lineup_strong_pct > 40:
                            console.print(f"[bold cyan]⚔️ ELITE MATCHUP: {lineup_strong_pct:.1f}% strong hitters vs strong pitcher - Battle of strengths![/bold cyan]")
                        elif lineup_strong_pct > 25:
                            console.print(f"[cyan]🔥 COMPETITIVE MATCHUP: {lineup_strong_pct:.1f}% strong hitters vs strong pitcher![/cyan]")
                        elif lineup_weak_pct > 50:
                            console.print(f"[dim]🛡️ PITCHER ADVANTAGE: {lineup_weak_pct:.1f}% weak hitters vs strong pitcher[/dim]")
                        else:
                            console.print(f"[yellow]⚖️ BALANCED MATCHUP: Mixed lineup vs strong pitcher[/yellow]")
            else:
                console.print(f"[yellow]No roster data found for {opponent_team}.[/yellow]")
            
            console.print("\n" + "="*60 + "\n")

    def display_all_games():
        """Display analysis for all games at once."""
        for i, game_info in enumerate(weak_pitcher_games):
            display_game_analysis(i)

    # Interactive menu loop
    while True:
        display_game_menu()
        
        choice = console.input("\n[bold cyan]Enter your choice: [/bold cyan]").strip().lower()
        
        if choice in ['back', 'exit', 'quit', 'q', 'main']:
            console.print("[green]Returning to main menu...[/green]")
            break
        elif choice == 'all':
            display_all_games()
            console.print(f"\n[bold green]✅ Complete Weak Pitcher Report for {date}[/bold green]")
            console.print(f"[cyan]💡 Focus on games with high percentages of strong hitters vs weak pitchers![/cyan]")
            break
        else:
            try:
                game_num = int(choice)
                if 1 <= game_num <= len(weak_pitcher_games):
                    display_game_analysis(game_num - 1)
                    console.print("\n[cyan]Press Enter to return to game menu...[/cyan]")
                    console.input()
                else:
                    console.print(f"[red]Please enter a number between 1 and {len(weak_pitcher_games)}.[/red]")
            except ValueError:
                console.print("[red]Invalid input. Please enter a game number, 'all', or 'back'.[/red]")

@app.command()
def all_games(date: str = None, use_cache: bool = True):
    """View all games for a date with interactive matchup analysis."""
    from app.services.mlb_api import is_weak_pitcher, classify_hitter, get_hit_streak, fetch_team_roster
    import os
    import json
    from datetime import datetime

    # Helper function to safely format numeric values from JSON
    def safe_format(value, decimals=3, default="N/A"):
        if value is None or value == "N/A":
            return default
        try:
            return f"{float(value):.{decimals}f}"
        except (ValueError, TypeError):
            return default

    if not date:
        console.print("[red]Please provide a date in the format YYYY-MM-DD.[/red]")
        return

    try:
        report_date = datetime.strptime(date, "%Y-%m-%d")
    except ValueError:
        console.print("[red]Invalid date format. Please use YYYY-MM-DD.[/red]")
        return
    
    # Fetch games for the given date
    games = fetch_games_for_date(date, use_cache=use_cache)
    if not games:
        console.print(f"[yellow]No games found for {date}.[/yellow]")
        return

    # Process all games for display
    all_games_list = []
    
    for game in games:
        # Extract team names more safely to avoid API data leakage
        home_team_data = game.get("teams", {}).get("home", {}).get("team", {})
        away_team_data = game.get("teams", {}).get("away", {}).get("team", {})
        
        # Get clean team names only
        home_team = home_team_data.get("name", "Unknown") if isinstance(home_team_data, dict) else "Unknown"
        away_team = away_team_data.get("name", "Unknown") if isinstance(away_team_data, dict) else "Unknown"
        home_team_id = home_team_data.get("id") if isinstance(home_team_data, dict) else None
        away_team_id = away_team_data.get("id") if isinstance(away_team_data, dict) else None
        
        # Get game status and time
        status = game.get("status", {}).get("detailedState", "Unknown")
        game_time = game.get("gameDate", "")
        
        # Format game time
        formatted_time = "TBD"
        if game_time:
            try:
                dt = datetime.fromisoformat(game_time.replace('Z', '+00:00'))
                formatted_time = dt.strftime("%I:%M %p ET")
            except:
                formatted_time = "TBD"
        
        home_pitcher = game.get("home_pitcher", {})
        away_pitcher = game.get("away_pitcher", {})
        
        # Check for weak pitchers
        weak_pitcher_count = 0
        weak_pitcher_names = []
        
        for pitcher in [home_pitcher, away_pitcher]:
            pitcher_name = pitcher.get("fullName", "TBD")
            if pitcher_name != "TBD" and pitcher and is_weak_pitcher(pitcher.get("stats", {})):
                weak_pitcher_count += 1
                weak_pitcher_names.append(pitcher_name)
        
        all_games_list.append({
            "game": game,
            "home_team": home_team,
            "away_team": away_team,
            "home_team_id": home_team_id,
            "away_team_id": away_team_id,
            "home_pitcher": home_pitcher,
            "away_pitcher": away_pitcher,
            "status": status,
            "time": formatted_time,
            "weak_pitcher_count": weak_pitcher_count,
            "weak_pitcher_names": weak_pitcher_names
        })

    # Display header
    console.print(f"\n[bold blue]🏟️ ALL GAMES FOR {date} 🏟️[/bold blue]")
    console.print(f"[green]Found {len(all_games_list)} game(s) scheduled[/green]\n")

    # Create interactive menu for game selection
    def display_all_games_menu():
        table = Table(title=f"All Games - {date}", show_header=True, header_style="bold cyan")
        table.add_column("Game #", style="bright_blue", width=8)
        table.add_column("Matchup", style="green", width=35)
        table.add_column("Home Pitcher", style="white", width=20)
        table.add_column("Away Pitcher", style="white", width=20)
        table.add_column("Alert", style="red", width=8)

        for i, game_info in enumerate(all_games_list, 1):
            # Clean team name extraction
            away_team = game_info.get('away_team', 'Unknown')
            home_team = game_info.get('home_team', 'Unknown')
            
            # Ensure we only show team names, not API objects
            if isinstance(away_team, dict):
                away_team = away_team.get('name', 'Unknown')
            if isinstance(home_team, dict):
                home_team = home_team.get('name', 'Unknown')
                
            matchup = f"{away_team} @ {home_team}"
            
            # Clean pitcher name extraction
            home_pitcher_name = game_info.get('home_pitcher', {}).get('fullName', 'TBD')
            away_pitcher_name = game_info.get('away_pitcher', {}).get('fullName', 'TBD')
            
            # Ensure pitcher names are strings
            if not isinstance(home_pitcher_name, str):
                home_pitcher_name = 'TBD'
            if not isinstance(away_pitcher_name, str):
                away_pitcher_name = 'TBD'
            
            # Truncate pitcher names if too long
            if len(home_pitcher_name) > 18:
                home_pitcher_name = home_pitcher_name[:15] + "..."
            if len(away_pitcher_name) > 18:
                away_pitcher_name = away_pitcher_name[:15] + "..."
            
            # Alert for weak pitchers
            alert = "⚠️ WEAK" if game_info.get('weak_pitcher_count', 0) > 0 else ""
            
            table.add_row(
                str(i), 
                matchup, 
                home_pitcher_name,
                away_pitcher_name,
                alert
            )

        console.print(table)
        console.print(f"\n[cyan]Select a game (1-{len(all_games_list)}) | 'weak' for weak pitcher games only | 'back' to main menu[/cyan]")

    def display_game_matchup_analysis(game_index):
        """Display detailed matchup analysis for a specific game."""
        if game_index < 0 or game_index >= len(all_games_list):
            console.print("[red]Invalid game number.[/red]")
            return

        game_info = all_games_list[game_index]
        game = game_info["game"]
        
        console.print(f"\n[bold blue]🔷 GAME MATCHUP ANALYSIS: {game_info['away_team']} @ {game_info['home_team']}[/bold blue]")
        console.print(f"[dim]Time: {game_info['time']} | Status: {game_info['status']}[/dim]")
        
        # Analyze both pitchers and their opposing lineups
        for pitcher_side, opponent_team_id, opponent_team in [
            ("home_pitcher", game_info["away_team_id"], game_info["away_team"]),
            ("away_pitcher", game_info["home_team_id"], game_info["home_team"])
        ]:
            pitcher = game_info.get(pitcher_side, {})
            pitcher_name = pitcher.get("fullName", "TBD")
            pitcher_team = game_info["home_team"] if pitcher_side == "home_pitcher" else game_info["away_team"]
            
            if pitcher_name == "TBD":
                console.print(f"\n[yellow]🤷 {pitcher_team} Pitcher: TBD[/yellow]")
                continue
                
            stats = pitcher.get("stats", {})
            is_weak = is_weak_pitcher(stats)
            
            # Pitcher Summary Table
            pitcher_color = "red" if is_weak else "green"
            pitcher_status = "⚠️ WEAK PITCHER" if is_weak else "✅ STRONG PITCHER"
            console.print(f"\n[bold {pitcher_color}]{pitcher_status}: {pitcher_name} ({pitcher_team})[/bold {pitcher_color}]")
            
            pitcher_table = Table(title=f"{pitcher_name} - Season Stats", show_header=True, header_style=f"bold {pitcher_color}")
            pitcher_table.add_column("Stat", style="white")
            pitcher_table.add_column("Value", style=pitcher_color)
            pitcher_table.add_column("MLB Avg", style="dim")
            
            pitcher_table.add_row("ERA", f"{stats.get('era', 'N/A')}", "~4.20")
            pitcher_table.add_row("WHIP", f"{stats.get('whip', 'N/A')}", "~1.30")
            pitcher_table.add_row("BAA", f"{stats.get('avg', 'N/A')}", "~.240")
            pitcher_table.add_row("H/9", f"{stats.get('hitsPer9Inn', 'N/A')}", "~8.50")
            pitcher_table.add_row("K/9", f"{stats.get('strikeoutsPer9Inn', 'N/A')}", "~8.50")
            pitcher_table.add_row("BB/9", f"{stats.get('walksPer9Inn', 'N/A')}", "~3.20")
            pitcher_table.add_row("IP", f"{stats.get('inningsPitched', 'N/A')}", "-")
            
            # Format win-loss record
            wins = stats.get('wins', 0)
            losses = stats.get('losses', 0)
            win_loss_record = f"{wins}-{losses}" if wins != 'N/A' and losses != 'N/A' else "N/A"
            pitcher_table.add_row("W-L", win_loss_record, "-")
            
            console.print(pitcher_table)
            
            # Show opponent hitting analysis for BOTH weak and strong pitchers
            matchup_context = "vs Weak Pitcher" if is_weak else "vs Strong Pitcher"
            console.print(f"\n[bold green]🎯 {opponent_team} Hitters {matchup_context}[/bold green]")
            
            roster = fetch_team_roster(opponent_team_id)
            if roster:
                hitting_table = Table(title=f"{opponent_team} Lineup Analysis", show_header=True, header_style="bold green")
                hitting_table.add_column("Tier", style="cyan", width=6)
                hitting_table.add_column("Player", style="magenta", width=20)
                hitting_table.add_column("Pos", style="white", width=4)
                hitting_table.add_column("AVG", style="yellow", width=6)
                hitting_table.add_column("HR", style="yellow", width=4)
                hitting_table.add_column("RBI", style="yellow", width=4)
                hitting_table.add_column("OPS", style="yellow", width=6)
                hitting_table.add_column("Streak", style="bright_yellow", width=6)

                # Collect all hitters first
                all_hitters = []
                
                # Initialize the tier count lists here
                strong_hitters = []
                bubble_hitters = []
                weak_hitters = []
                
                for player in roster:
                    # Skip pitchers
                    position = player.get("position", {}).get("abbreviation", "")
                    if position == "P":
                        continue
                        
                    player_id = player.get("person", {}).get("id")
                    player_name = player.get("person", {}).get("fullName", "Unknown")
                    
                    # Try to get player stats from local files
                    hitter_stats = {}
                    hit_streak = 0
                    try:
                        player_file = os.path.join("data", "players", f"{player_id}.json")
                        if os.path.exists(player_file):
                            with open(player_file, "r") as f:
                                player_data = json.load(f)
                                hitter_stats = player_data
                        hit_streak = get_hit_streak(player_id) if player_id else 0
                    except Exception as e:
                        logger.debug(f"Could not get stats for player {player_name}: {e}")
                    
                    tier = classify_hitter(hitter_stats)
                    
                    # Helper function to safely get ERA
                    def get_era_value(stats):
                        era = stats.get('era', 0)
                        try:
                            return float(era) if era else 0.0
                        except (ValueError, TypeError):
                            return 0.0
                    
                    era_value = get_era_value(hitter_stats)
                    
                    player_row = {
                        "tier": tier,
                        "name": player_name,
                        "position": position,
                        "era": era_value,
                        "avg": safe_format(hitter_stats.get('avg')),
                        "hr": str(hitter_stats.get("homeRuns", "N/A")),
                        "rbi": str(hitter_stats.get("rbi", "N/A")),
                        "ops": safe_format(hitter_stats.get('ops')),
                        "streak": str(hit_streak) if hit_streak > 0 else "0",
                    }
                    
                    all_hitters.append(player_row)

                # Sort hitters by batting average in descending order, then by tier priority
                def sort_key(hitter):
                    # Primary sort: Batting Average descending (highest first)
                    # Secondary sort: Tier priority (Strong > Bubble > Weak > No Data)
                    tier_priority = {"🟢": 0, "🟡": 1, "🔴": 2, "❓": 3}
                    
                    # Get batting average value for sorting
                    avg_str = hitter["avg"]
                    try:
                        avg_value = float(avg_str) if avg_str != "N/A" else 0.0
                    except (ValueError, TypeError):
                        avg_value = 0.0
                    
                    return (-avg_value, tier_priority.get(hitter["tier"], 4))
                
                all_hitters.sort(key=sort_key)

                # Add top 9 hitters to table (likely lineup) and categorize them
                for i, hitter in enumerate(all_hitters):
                    hitting_table.add_row(
                        hitter["tier"],
                        hitter["name"],
                        hitter["position"],
                        hitter["avg"],
                        hitter["hr"],
                        hitter["rbi"],
                        hitter["ops"],
                        hitter["streak"]
                    )
                    
                    # Count by tier for summary
                    if hitter["tier"] == "🟢":
                        strong_hitters.append(hitter)
                    elif hitter["tier"] == "🟡":
                        bubble_hitters.append(hitter)
                    else:  # 🔴 or ❓
                        weak_hitters.append(hitter)

                console.print(hitting_table)
                
                # Display roster depth information
                console.print(f"\n[bold cyan]📊 Complete Roster Analysis ({len(all_hitters)} total hitters)[/bold cyan]")
                
                # Summary for ALL hitters with context-aware recommendations
                if len(all_hitters) > 0:
                    strong_pct = len(strong_hitters) / len(all_hitters) * 100
                    bubble_pct = len(bubble_hitters) / len(all_hitters) * 100
                    weak_pct = len(weak_hitters) / len(all_hitters) * 100
                    
                    # Summary stats table for entire roster
                    summary_table = Table(title=f"{opponent_team} Complete Roster Summary", show_header=True, header_style="bold cyan")
                    summary_table.add_column("Category", style="cyan")
                    summary_table.add_column("Count", style="yellow")
                    summary_table.add_column("Percentage", style="green")
                    
                    summary_table.add_row("🟢 Strong Hitters", str(len(strong_hitters)), f"{strong_pct:.1f}%")
                    summary_table.add_row("🟡 Bubble Hitters", str(len(bubble_hitters)), f"{bubble_pct:.1f}%")
                    summary_table.add_row("🔴 Weak Hitters", str(len(weak_hitters)), f"{weak_pct:.1f}%")
                    summary_table.add_row("Total Roster Hitters", str(len(all_hitters)), "100.0%")
                    
                    # Add likely starting lineup analysis
                    if len(all_hitters) >= 9:
                        top_9_strong = sum(1 for h in all_hitters[:9] if h["tier"] == "🟢")
                        top_9_bubble = sum(1 for h in all_hitters[:9] if h["tier"] == "🟡")
                        top_9_weak = 9 - top_9_strong - top_9_bubble
                        
                        summary_table.add_row("", "", "")  # Separator
                        summary_table.add_row("🏟️ Likely Lineup (Top 9)", "", "")
                        summary_table.add_row("  🟢 Strong in Lineup", str(top_9_strong), f"{top_9_strong/9*100:.1f}%")
                        summary_table.add_row("  🟡 Bubble in Lineup", str(top_9_bubble), f"{top_9_bubble/9*100:.1f}%")
                        summary_table.add_row("  🔴 Weak in Lineup", str(top_9_weak), f"{top_9_weak/9*100:.1f}%")
                    
                    console.print(summary_table)
                    
                    # Bench depth analysis
                    if len(all_hitters) > 9:
                        bench_hitters = all_hitters[9:]
                        bench_strong = sum(1 for h in bench_hitters if h["tier"] == "🟢")
                        bench_bubble = sum(1 for h in bench_hitters if h["tier"] == "🟡")
                        bench_weak = len(bench_hitters) - bench_strong - bench_bubble
                        
                        console.print(f"\n[bold yellow]🛏️ Bench Depth Analysis ({len(bench_hitters)} players)[/bold yellow]")
                        console.print(f"[green]🟢 Strong bench players: {bench_strong}[/green]")
                        console.print(f"[yellow]🟡 Bubble bench players: {bench_bubble}[/yellow]")
                        console.print(f"[red]🔴 Weak bench players: {bench_weak}[/red]")
                        
                        if bench_strong > 2:
                            console.print(f"[bold green]💪 EXCELLENT DEPTH: {bench_strong} strong hitters available off the bench![/bold green]")
                        elif bench_strong > 0:
                            console.print(f"[green]✅ GOOD DEPTH: {bench_strong} strong bench option(s) available[/green]")
                        else:
                            console.print(f"[yellow]⚠️ LIMITED DEPTH: No strong hitters on the bench[/yellow]")

                    # Context-aware recommendations based on pitcher strength
                    is_weak_pitcher_result = is_weak_pitcher(stats)
                    if is_weak_pitcher_result:
                        # Against weak pitchers - look for offensive opportunities
                        lineup_strong_pct = (top_9_strong/9*100) if len(all_hitters) >= 9 else strong_pct
                        if lineup_strong_pct > 30:
                            console.print(f"[bold green]💰 EXCELLENT OPPORTUNITY: {lineup_strong_pct:.1f}% strong hitters in likely lineup vs weak pitcher![/bold green]")
                        elif lineup_strong_pct > 15:
                            console.print(f"[bold yellow]⚡ GOOD OPPORTUNITY: {lineup_strong_pct:.1f}% strong hitters in likely lineup vs weak pitcher![/bold yellow]")
                        elif len(all_hitters) >= 9 and (top_9_bubble/9*100) > 40:
                            console.print(f"[yellow]📊 MODERATE OPPORTUNITY: {top_9_bubble/9*100:.1f}% bubble hitters in lineup vs weak pitcher[/yellow]")
                        else:
                            console.print(f"[dim]📋 LIMITED OPPORTUNITY: Mostly weak lineup vs weak pitcher[/dim]")
                    else:
                        # Against strong pitchers - assess difficulty
                        lineup_strong_pct = (top_9_strong/9*100) if len(all_hitters) >= 9 else strong_pct
                        lineup_weak_pct = (top_9_weak/9*100) if len(all_hitters) >= 9 else weak_pct
                        if lineup_strong_pct > 40:
                            console.print(f"[bold cyan]⚔️ ELITE MATCHUP: {lineup_strong_pct:.1f}% strong hitters vs strong pitcher - Battle of strengths![/bold cyan]")
                        elif lineup_strong_pct > 25:
                            console.print(f"[cyan]🔥 COMPETITIVE MATCHUP: {lineup_strong_pct:.1f}% strong hitters vs strong pitcher![/cyan]")
                        elif lineup_weak_pct > 50:
                            console.print(f"[dim]🛡️ PITCHER ADVANTAGE: {lineup_weak_pct:.1f}% weak hitters vs strong pitcher[/dim]")
                        else:
                            console.print(f"[yellow]⚖️ BALANCED MATCHUP: Mixed lineup vs strong pitcher[/yellow]")
            else:
                console.print(f"[yellow]No roster data found for {opponent_team}.[/yellow]")
            
            console.print("\n" + "="*60 + "\n")

    def display_weak_pitcher_games_only():
        """Display only games with weak pitchers."""
        weak_games = [game for game in all_games_list if game.get('weak_pitcher_count', 0) > 0]
        
        if not weak_games:
            console.print(f"[green]🎯 No weak pitchers identified for {date}[/green]")
            console.print(f"[yellow]All pitchers meet strength criteria - no favorable matchups found.[/yellow]")
            return
        
        console.print(f"\n[bold red]⚠️ WEAK PITCHER GAMES ONLY - {date} ⚠️[/bold red]")
        console.print(f"[green]Found {len(weak_games)} game(s) with weak pitcher matchups![/green]\n")
        
        table = Table(title=f"Weak Pitcher Games - {date}", show_header=True, header_style="bold red")
        table.add_column("Game #", style="bright_blue", width=8)
        table.add_column("Matchup", style="green", width=35)
        table.add_column("Weak Pitcher(s)", style="red", width=30)

        for i, game_info in enumerate(weak_games, 1):
            away_team = game_info.get('away_team', 'Unknown')
            home_team = game_info.get('home_team', 'Unknown')
            matchup = f"{away_team} @ {home_team}"
            
            weak_pitchers = ", ".join(game_info.get('weak_pitcher_names', []))
            
            table.add_row(str(i), matchup, weak_pitchers)

        console.print(table)
        console.print("\n[cyan]Press Enter to return to all games menu...[/cyan]")
        console.input()

    # Interactive menu loop
    while True:
        display_all_games_menu()
        
        choice = console.input("\n[bold cyan]Enter your choice: [/bold cyan]").strip().lower()
        
        if choice in ['back', 'exit', 'quit', 'q', 'main']:
            console.print("[green]Returning to main menu...[/green]")
            break
        elif choice == 'weak':
            display_weak_pitcher_games_only()
        else:
            try:
                game_num = int(choice)
                if 1 <= game_num <= len(all_games_list):
                    display_game_matchup_analysis(game_num - 1)
                    console.print("\n[cyan]Press Enter to return to games menu...[/cyan]")
                    console.input()
                else:
                    console.print(f"[red]Please enter a number between 1 and {len(all_games_list)}.[/red]")
            except ValueError:
                console.print("[red]Invalid input. Please enter a game number, 'weak', or 'back'.[/red]")

@app.command()
def clear_cache():
    """Clear all cached matchup report data."""
    import shutil

    cache_folder = os.path.join("data", "matchup_cache")
    if os.path.exists(cache_folder):
        shutil.rmtree(cache_folder)
        console.print("[green]All cached matchup data cleared successfully.[/green]")
    else:
        console.print("[yellow]No cache folder found. Nothing to clear.[/yellow]")

@app.command()
def refresh_report(date: str = None):
    """Generate matchup report with fresh data (bypass cache)."""
    if not date:
        date = console.input("[bold cyan]Enter date for fresh matchup report (YYYY-MM-DD): [/bold cyan]")
    matchup_report(force_refresh=True, date=date)

@app.command()
def serve(host: str = "0.0.0.0", port: int = 8000):
    """Launch Quantum Edge web UI."""
    import uvicorn
    import webbrowser
    import threading
    import time
    
    console.print(f"[bold cyan]🌐 Starting Quantum Edge Web Server...[/bold cyan]")
    console.print(f"[green]🚀 Server will be available at: http://{host}:{port}[/green]")
    console.print(f"[yellow]💡 Press Ctrl+C to stop the server[/yellow]\n")
    
    # Start server in background thread
    def run_server():
        uvicorn.run("app.web_main:app", host=host, port=port, reload=False, log_level="info")
    
    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()
    
    # Wait a moment for server to start
    time.sleep(2)
    
    # Open browser
    try:
        webbrowser.open(f"http://{host}:{port}")
        console.print(f"[green]🌐 Opening browser to http://{host}:{port}[/green]")
    except Exception as e:
        console.print(f"[yellow]Could not open browser automatically: {e}[/yellow]")
        console.print(f"[cyan]Please manually navigate to: http://{host}:{port}[/cyan]")
    
    try:
        # Keep main thread alive
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        console.print(f"\n[red]🛑 Shutting down Quantum Edge Web Server...[/red]")
        console.print(f"[green]👋 Thanks for using Quantum Edge Analytics![/green]")

@app.command()
def update_streaks():
    """Update hit streak data for all players with improved logic and cache results."""
    from app.services.mlb_api import get_last_10_games, classify_hitter, get_hit_streak
    import os
    import json
    from datetime import datetime, date

    console.print("[cyan]🔄 Updating hit streak data for all players...[/cyan]")
    
    players_folder = os.path.join("data", "players")
    teams_file = os.path.join("data", "teams.json")
    cache_file = os.path.join("data", "hit_streaks_cache.json")
    detailed_cache_file = os.path.join("data", "detailed_streaks_cache.json")

    if not os.path.exists(teams_file):
        console.print("[red]Teams data not found. Please run 'pull-teams' first.[/red]")
        return

    if not os.path.exists(players_folder):
        console.print("[red]Players data not found. Please run 'pull-player-stats' first.[/red]")
        return

    with open(teams_file, "r") as f:
        teams = {team["id"]: team["name"] for team in json.load(f)}

    hitters_on_streak = []
    detailed_streak_data = []
    processed_count = 0
    total_players = len([f for f in os.listdir(players_folder) if f.endswith(".json")])

    for player_file in os.listdir(players_folder):
        if player_file.endswith(".json"):
            processed_count += 1
            if processed_count % 50 == 0:
                console.print(f"[dim]Processed {processed_count}/{total_players} players...[/dim]")
                
            player_path = os.path.join(players_folder, player_file)
            try:
                with open(player_path, "r") as f:
                    player_data = json.load(f)
            except Exception as e:
                logger.debug(f"Error reading player file {player_file}: {e}")
                continue

            player_id = player_data.get("id")
            full_name = player_data.get("fullName", "Unknown")
            
            if not player_id:
                continue

            # Skip players who are not hitters
            position = player_data.get("position", "")
            if position == "P":
                continue

            # Get team name with multiple fallback methods
            team_id = player_data.get("currentTeam", {}).get("id") if isinstance(player_data.get("currentTeam"), dict) else None
            team_name = teams.get(team_id, "Unknown Team")

            # Fallback team name methods
            if team_name == "Unknown Team":
                team_name = player_data.get("currentTeam", {}).get("name", "Unknown Team") if isinstance(player_data.get("currentTeam"), dict) else "Unknown Team"

            if team_name == "Unknown Team":
                team_name = get_team_name(team_id, teams)

            if team_name == "Unknown Team":
                team_name = find_team_name_by_player_name(full_name, teams)

            try:
                # Use the improved hit streak calculation that looks at last 10 games
                streak = get_hit_streak(player_id, num_games=10)
                
                # Get player tier for additional context
                tier = classify_hitter(player_data)
                
                # Create detailed entry for all players (including those with 0 streak)
                detailed_entry = {
                    "player_id": player_id,
                    "name": full_name,
                    "team": team_name,
                    "position": position,
                    "streak": streak,
                    "tier": tier,
                    "avg": player_data.get("avg", "N/A"),
                    "ops": player_data.get("ops", "N/A"),
                    "last_updated": datetime.now().isoformat()
                }
                detailed_streak_data.append(detailed_entry)
                
                # Only include players with streaks of 2 or more in the main cache
                if streak >= 2:
                    hitters_on_streak.append({
                        "name": full_name,
                        "team": team_name,
                        "streak": streak,
                        "tier": tier,
                        "avg": player_data.get("avg", "N/A")
                    })
                    
            except Exception as e:
                logger.debug(f"Error processing player {full_name}: {e}")
                continue

    # Sort hitters by streak length (descending), then by batting average (descending)
    hitters_on_streak.sort(key=lambda x: (-x["streak"], -float(x["avg"]) if x["avg"] != "N/A" else 0))
    
    # Sort detailed data by streak length
    detailed_streak_data.sort(key=lambda x: (-x["streak"], -float(x["avg"]) if x["avg"] != "N/A" else 0))

    # Cache the sorted results
    with open(cache_file, "w") as f:
        json.dump(hitters_on_streak, f, indent=4)
    
    with open(detailed_cache_file, "w") as f:
        json.dump(detailed_streak_data, f, indent=4)

    console.print(f"[green]✅ Hit streak data updated for {len(detailed_streak_data)} players![/green]")
    console.print(f"[green]📊 Found {len(hitters_on_streak)} players on hit streaks of 2+ games[/green]")

    # Display the results
    if hitters_on_streak:
        table = Table(title="Hitters on Hit Streaks (2+ Games)", show_header=True, header_style="bold green")
        table.add_column("Player", style="cyan", width=25)
        table.add_column("Team", style="magenta", width=20)
        table.add_column("Streak", style="yellow", width=8)
        table.add_column("Tier", style="white", width=6)
        table.add_column("AVG", style="bright_blue", width=8)

        for hitter in hitters_on_streak[:15]:  # Show top 15
            table.add_row(
                hitter["name"], 
                hitter["team"], 
                str(hitter["streak"]),
                hitter["tier"],
                str(hitter["avg"])
            )

        console.print(table)
        
        if len(hitters_on_streak) > 15:
            console.print(f"[dim]... and {len(hitters_on_streak) - 15} more players with active streaks[/dim]")
    else:
        console.print("[red]No hitters on hit streaks of 2 or more games found.[/red]")

# Make the default behavior launch the interactive menu
@app.callback(invoke_without_command=True)
def main_callback(ctx: typer.Context):
    """Default callback - launch interactive menu when no command is provided."""
    if ctx.invoked_subcommand is None:
        quantum_banner()
        console.print("[yellow]💡 Tip: You can also use specific commands like 'python quantum_edge.py pull-teams' or 'python quantum_edge.py menu' for interactive mode[/yellow]\n")
        
        # Ask user if they want interactive menu or see command list
        choice = console.input("[bold cyan]Press 'm' for interactive menu, or Enter to see available commands: [/bold cyan]").strip().lower()
        
        if choice == 'm':
            main_menu()
        else:
            list_commands()
            console.print(f"\n[dim]Use 'python quantum_edge.py <command>' to run a specific command[/dim]")
            console.print(f"[dim]Use 'python quantum_edge.py menu' for interactive mode[/dim]")

# Remove the problematic line that was causing issues
# app.callback()(main)

# Add proper entry point
if __name__ == "__main__":
    app()