#!/usr/bin/env python3

import sys
sys.path.append('./MLB-StatsAPI')
import statsapi

def test_specific_h2h_matchups():
    """Test H2H with actual players from 6/6/2025 Dodgers @ Cardinals game"""
    print("=== Testing Real H2H Matchups from 6/6/2025 Game ===")
    
    # Real matchups from the game
    matchups = [
        {"batter": "660271", "batter_name": "Shohei Ohtani", "pitcher": "543243", "pitcher_name": "Sonny Gray"},
        {"batter": "605141", "batter_name": "Mookie Betts", "pitcher": "543243", "pitcher_name": "Sonny Gray"},
        {"batter": "518692", "batter_name": "Freddie Freeman", "pitcher": "543243", "pitcher_name": "Sonny Gray"},
        {"batter": "606192", "batter_name": "Teoscar Hernández", "pitcher": "543243", "pitcher_name": "Sonny Gray"},
    ]
    
    for matchup in matchups:
        print(f"\n=== {matchup['batter_name']} vs {matchup['pitcher_name']} ===")
        
        # Test different H2H approaches
        methods = [
            {
                "name": "Game Log Analysis",
                "method": "gameLog"
            },
            {
                "name": "Splits Analysis", 
                "method": "splits"
            },
            {
                "name": "Season with Pitcher Filter",
                "method": "season_filter"
            }
        ]
        
        for method in methods:
            result = test_h2h_method(matchup['batter'], matchup['pitcher'], method)
            if result != "0-0":
                print(f"SUCCESS with {method['name']}: {result}")
                return result
    
    return "0-0"

def test_h2h_method(batter_id, pitcher_id, method_info):
    """Test a specific H2H method"""
    method_name = method_info['name']
    method_type = method_info['method']
    
    print(f"\nTrying {method_name}...")
    
    try:
        if method_type == "gameLog":
            # Get batter's game log and look for games against pitcher's team
            data = statsapi.get("stats", {
                "stats": "gameLog",
                "group": "hitting",
                "season": "2025",
                "personId": batter_id
            })
            
            if 'stats' in data and data['stats']:
                splits = data['stats'][0].get('splits', [])
                
                # Look for games against Cardinals (Sonny Gray's team in that game)
                cardinals_games = []
                for split in splits:
                    opponent = split.get('opponent', {})
                    if opponent.get('id') == 138:  # Cardinals team ID
                        cardinals_games.append(split)
                
                print(f"  Found {len(cardinals_games)} games vs Cardinals")
                
                # Sum up stats from Cardinals games (approximates H2H vs Cardinals pitchers)
                total_ab = 0
                total_hits = 0
                
                for game in cardinals_games:
                    stat = game.get('stat', {})
                    ab = stat.get('atBats', 0)
                    hits = stat.get('hits', 0)
                    total_ab += ab
                    total_hits += hits
                    
                    print(f"    {game.get('date')}: {hits}-{ab}")
                
                if total_ab > 0:
                    return f"{total_hits}-{total_ab}"
                    
        elif method_type == "splits":
            # Try to get splits data
            data = statsapi.get("stats", {
                "stats": "season",
                "group": "hitting",
                "season": "2025",
                "personId": batter_id,
                "splitId": "vs_team_138"  # Try Cardinals team split
            })
            
            print(f"  Splits result: {list(data.keys()) if data else 'No data'}")
            
        elif method_type == "season_filter":
            # Try season stats with various filters
            filters = [
                {"opponentId": pitcher_id},
                {"pitcherId": pitcher_id},
                {"opponent": pitcher_id},
                {"teamId": "138"}  # Cardinals team
            ]
            
            for filter_params in filters:
                try:
                    params = {
                        "stats": "season",
                        "group": "hitting",
                        "season": "2025",
                        "personId": batter_id
                    }
                    params.update(filter_params)
                    
                    print(f"    Trying filter: {filter_params}")
                    data = statsapi.get("stats", params)
                    
                    if 'stats' in data and data['stats']:
                        splits = data['stats'][0].get('splits', [])
                        if splits:
                            print(f"    Found {len(splits)} splits!")
                            for split in splits:
                                stat = split.get('stat', {})
                                ab = stat.get('atBats', 0)
                                hits = stat.get('hits', 0)
                                if ab > 0:
                                    return f"{hits}-{ab}"
                except Exception as e:
                    print(f"    Filter failed: {e}")
    
    except Exception as e:
        print(f"  Method failed: {e}")
    
    return "0-0"

def test_alternative_approach():
    """Try a completely different approach using boxscore data"""
    print("\n=== Testing Boxscore Approach ===")
    
    game_id = "777620"  # 6/6/2025 game
    
    try:
        # Get boxscore data 
        boxscore = statsapi.boxscore(game_id)
        print("Boxscore keys:", list(boxscore.keys()) if boxscore else "No data")
        
        # The boxscore might contain player vs pitcher matchup data
        if boxscore:
            print("Found boxscore data - this could contain H2H info!")
            
            # Look for player-specific data
            for key, value in boxscore.items():
                if 'batter' in key.lower() or 'pitcher' in key.lower():
                    print(f"  {key}: {type(value)}")
        
    except Exception as e:
        print(f"Boxscore approach failed: {e}")

if __name__ == "__main__":
    result = test_specific_h2h_matchups()
    print(f"\nFinal H2H Result: {result}")
    
    if result == "0-0":
        test_alternative_approach()
