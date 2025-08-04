#!/usr/bin/env python3

import sys
sys.path.append('./MLB-StatsAPI')
import statsapi

def analyze_specific_game():
    """Analyze the 6/6/2025 Dodgers @ Cardinals game in detail"""
    print("=== Analyzing 6/6/2025 Game: Dodgers @ Cardinals ===")
    
    game_id = "777620"
    
    try:
        game_data = statsapi.get('game', {'gamePk': game_id})
        
        # Get team lineups
        live_data = game_data.get('liveData', {})
        boxscore = live_data.get('boxscore', {})
        teams = boxscore.get('teams', {})
        
        print("AWAY TEAM (Dodgers) LINEUP:")
        away_batters = teams.get('away', {}).get('batters', [])
        away_players = teams.get('away', {}).get('players', {})
        
        for batter_id in away_batters:
            player = away_players.get(f'ID{batter_id}', {})
            person = player.get('person', {})
            print(f"  {person.get('fullName', 'Unknown')} (ID: {batter_id})")
            
        print("\nHOME TEAM (Cardinals) PITCHERS:")
        home_pitchers = teams.get('home', {}).get('pitchers', [])
        home_players = teams.get('home', {}).get('players', {})
        
        for pitcher_id in home_pitchers:
            player = home_players.get(f'ID{pitcher_id}', {})
            person = player.get('person', {})
            print(f"  {person.get('fullName', 'Unknown')} (ID: {pitcher_id})")
            
        # Find specific matchups
        print("\nLOOKING FOR SPECIFIC H2H MATCHUPS:")
        
        # Check if any Dodgers batters faced Sonny Gray
        sonny_gray_id = "543243"
        if sonny_gray_id in [str(p) for p in home_pitchers]:
            print(f"✓ Sonny Gray (ID: {sonny_gray_id}) did pitch in this game!")
            
            # Now find a specific batter to test H2H with
            for batter_id in away_batters[:5]:  # Check first 5 batters
                player = away_players.get(f'ID{batter_id}', {})
                person = player.get('person', {})
                batter_name = person.get('fullName', 'Unknown')
                
                print(f"\nTesting H2H: {batter_name} (ID: {batter_id}) vs Sonny Gray")
                
                # Try to get H2H stats for this specific matchup
                try:
                    h2h_data = statsapi.get("stats", {
                        "stats": "gameLog",
                        "group": "hitting",
                        "season": "2025",
                        "personId": str(batter_id)
                    })
                    
                    if 'stats' in h2h_data and h2h_data['stats']:
                        splits = h2h_data['stats'][0].get('splits', [])
                        
                        # Look for this specific game
                        for split in splits:
                            game_info = split.get('game', {})
                            if str(game_info.get('gamePk', '')) == game_id:
                                print(f"  FOUND GAME LOG ENTRY!")
                                stat = split.get('stat', {})
                                print(f"  Stats: {stat.get('atBats', 0)} AB, {stat.get('hits', 0)} H")
                                print(f"  Game: {split.get('date')} vs {split.get('opponent', {}).get('name')}")
                                
                                # This proves the game happened - now try H2H approach
                                return batter_id, sonny_gray_id
                                
                except Exception as e:
                    print(f"  Error getting game log: {e}")
        else:
            print(f"✗ Sonny Gray not found in pitchers list")
            
    except Exception as e:
        print(f"Error analyzing game: {e}")
        
    return None, None

def test_h2h_with_real_matchup(batter_id, pitcher_id):
    """Test H2H calculation with a real matchup from the game"""
    print(f"\n=== Testing H2H Calculation: Batter {batter_id} vs Pitcher {pitcher_id} ===")
    
    # Different approaches to get H2H data
    approaches = [
        {
            "name": "Method 1: vsPitcher stats",
            "params": {
                "stats": "vsPitcher", 
                "group": "hitting",
                "season": "2025",
                "personId": batter_id,
                "opponentId": pitcher_id
            }
        },
        {
            "name": "Method 2: season stats with pitcher filter",
            "params": {
                "stats": "season",
                "group": "hitting", 
                "season": "2025",
                "personId": batter_id,
                "pitcherId": pitcher_id
            }
        },
        {
            "name": "Method 3: splits with opponent",
            "params": {
                "stats": "splits",
                "group": "hitting",
                "season": "2025", 
                "personId": batter_id,
                "opponent": pitcher_id
            }
        }
    ]
    
    for approach in approaches:
        print(f"\n{approach['name']}:")
        print(f"Params: {approach['params']}")
        
        try:
            data = statsapi.get("stats", approach['params'])
            print(f"SUCCESS! Keys: {list(data.keys())}")
            
            if 'stats' in data and data['stats']:
                stats_obj = data['stats'][0] 
                splits = stats_obj.get('splits', [])
                print(f"Found {len(splits)} splits")
                
                for split in splits:
                    stat = split.get('stat', {})
                    ab = stat.get('atBats', 0)
                    hits = stat.get('hits', 0)
                    if ab > 0:  # Only show if there are actual at-bats
                        print(f"  H2H Stats: {hits}-{ab} (.{hits/ab:.3f})")
                        return f"{hits}-{ab}"
            else:
                print("No stats found")
                
        except Exception as e:
            print(f"Failed: {e}")
    
    return "0-0"

if __name__ == "__main__":
    batter_id, pitcher_id = analyze_specific_game()
    
    if batter_id and pitcher_id:
        result = test_h2h_with_real_matchup(batter_id, pitcher_id)
        print(f"\nFinal H2H Result: {result}")
    else:
        print("\nCould not find a valid batter/pitcher matchup to test")
