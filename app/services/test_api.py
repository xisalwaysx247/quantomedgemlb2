from app.services.mlb_api import get_all_teams, get_team_roster, get_player_hitting_stats, get_player_pitching_stats

def test_get_all_teams():
    teams = get_all_teams()
    assert teams is not None, "Failed to fetch teams"
    assert "teams" in teams, "Response missing 'teams' key"

def test_get_team_roster():
    team_id = 147  # Example team ID
    roster = get_team_roster(team_id)
    assert roster is not None, "Failed to fetch team roster"
    assert "roster" in roster, "Response missing 'roster' key"

def test_get_player_hitting_stats():
    player_id = 660271  # Example player ID
    stats = get_player_hitting_stats(player_id)
    assert stats is not None, "Failed to fetch player hitting stats"
    assert "stats" in stats, "Response missing 'stats' key"

def test_get_player_pitching_stats():
    player_id = 605141  # Example player ID
    stats = get_player_pitching_stats(player_id)
    assert stats is not None, "Failed to fetch player pitching stats"
    assert "stats" in stats, "Response missing 'stats' key"

if __name__ == "__main__":
    test_get_all_teams()
    print("get_all_teams passed")

    test_get_team_roster()
    print("get_team_roster passed")

    test_get_player_hitting_stats()
    print("get_player_hitting_stats passed")

    test_get_player_pitching_stats()
    print("get_player_pitching_stats passed")