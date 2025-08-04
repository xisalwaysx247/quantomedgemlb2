#!/usr/bin/env python3

import sys
sys.path.append('./MLB-StatsAPI')
import statsapi

def explore_game_log():
    """Explore the gameLog data structure to understand H2H possibilities"""
    print("=== Exploring Game Log Data ===")
    
    batter_id = "605141"  # Mookie Betts
    pitcher_id = "543243"  # Sonny Gray
    season = "2024"
    
    try:
        # Get game log for Mookie Betts in 2024
        params = {
            "stats": "gameLog",
            "group": "hitting", 
            "season": season,
            "personId": batter_id
        }
        
        print(f"Getting game log for player {batter_id} in {season}")
        data = statsapi.get("stats", params)
        
        if 'stats' in data and data['stats']:
            stats_obj = data['stats'][0]
            splits = stats_obj.get('splits', [])
            print(f"Found {len(splits)} games")
            
            # Look at a few games to understand the structure
            print(f"\n=== Examining first few games ===")
            for i, split in enumerate(splits[:3]):
                print(f"\nGame {i+1}:")
                print(f"  Keys: {list(split.keys())}")
                
                if 'game' in split:
                    game = split['game']
                    print(f"  Game keys: {list(game.keys())}")
                    print(f"  Game ID: {game.get('gamePk')}")
                    print(f"  Date: {game.get('gameDate')}")
                    
                    if 'teams' in game:
                        teams = game['teams']
                        print(f"  Home: {teams['home']['team']['name']}")
                        print(f"  Away: {teams['away']['team']['name']}")
                
                if 'opponent' in split:
                    opponent = split['opponent']
                    print(f"  Opponent: {opponent.get('name', 'Unknown')}")
                
                if 'stat' in split:
                    stat = split['stat']
                    print(f"  AB: {stat.get('atBats', 0)}, H: {stat.get('hits', 0)}")
            
            # Now search for games against Sonny Gray's team
            print(f"\n=== Searching for games where they might have faced each other ===")
            
            # First, let's get Sonny Gray's team info
            gray_data = statsapi.get("person", {"personId": pitcher_id})
            gray_team = None
            if 'people' in gray_data and gray_data['people']:
                gray_player = gray_data['people'][0]
                print(f"Sonny Gray: {gray_player.get('fullName')}")
                if 'currentTeam' in gray_player:
                    gray_team = gray_player['currentTeam']
                    print(f"  Current Team: {gray_team.get('name')} (ID: {gray_team.get('id')})")
            
            # Look for games against Gray's team
            potential_games = []
            for split in splits:
                if 'opponent' in split:
                    opponent = split['opponent']
                    if gray_team and opponent.get('id') == gray_team.get('id'):
                        potential_games.append(split)
            
            print(f"\nFound {len(potential_games)} games against {gray_team.get('name', 'Gray team') if gray_team else 'unknown team'}")
            
            for i, game in enumerate(potential_games):
                print(f"\nPotential H2H Game {i+1}:")
                if 'game' in game:
                    game_info = game['game']
                    print(f"  Date: {game_info.get('gameDate')}")
                    print(f"  Game ID: {game_info.get('gamePk')}")
                if 'stat' in game:
                    stat = game['stat']
                    print(f"  Stats: {stat.get('atBats', 0)}-{stat.get('hits', 0)}")
                    
                # Now get detailed game info to see if Gray pitched
                if 'game' in game:
                    game_pk = game['game'].get('gamePk')
                    if game_pk:
                        print(f"  Checking if Sonny Gray pitched in game {game_pk}...")
                        try:
                            game_detail = statsapi.get("game", {"gamePk": game_pk})
                            # This would be complex to parse, but we could check the pitchers
                            print(f"    Got game detail data")
                        except Exception as e:
                            print(f"    Error getting game detail: {e}")
                        
    except Exception as e:
        print(f"Error: {e}")

def test_simpler_h2h():
    """Test a simpler approach using team-level filtering"""
    print("\n\n=== Testing Simpler H2H Approach ===")
    
    # Try using the schedule to find games between teams
    try:
        # Get schedule for 2024 Dodgers vs Cardinals/Twins (Gray's teams)
        print("Getting 2024 schedule...")
        
        # This is a simplified approach - get games between teams
        schedule_data = statsapi.schedule(start_date="2024-04-01", end_date="2024-09-30", team=119)  # Dodgers
        
        print(f"Found {len(schedule_data)} Dodgers games")
        
        # Look for games against teams Sonny Gray might have been on
        gray_teams = [142, 134]  # Cardinals, Twins (example team IDs)
        
        relevant_games = []
        for game in schedule_data[:10]:  # Check first 10 games
            print(f"Game: {game}")
            
    except Exception as e:
        print(f"Error with schedule approach: {e}")

if __name__ == "__main__":
    explore_game_log()
    test_simpler_h2h()
