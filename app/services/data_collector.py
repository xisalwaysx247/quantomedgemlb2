from app.services.loader import fetch_teams, fetch_roster, fetch_player_stats

# Example usage of the updated API logic
def collect_team_data():
    """Collect data for all teams."""
    teams = fetch_teams()
    for team in teams:
        team_id = team.get("id")
        team_name = team.get("name")
        print(f"Fetching roster for {team_name}...")
        roster = fetch_roster(team_id)
        for player in roster:
            player_id = player.get("person", {}).get("id")
            player_name = player.get("person", {}).get("fullName")
            print(f"Fetching stats for {player_name}...")
            stats = fetch_player_stats(player_id, group="hitting")
            print(stats)