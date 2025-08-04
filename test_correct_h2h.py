#!/usr/bin/env python3

import sys
sys.path.append('./MLB-StatsAPI')
import statsapi

def test_player_info():
    """Test basic player info call"""
    print("=== Testing Player Info ===")
    try:
        player_data = statsapi.get("person", {"personId": "543243"})  # Sonny Gray
        print(f"Success! Player data keys: {list(player_data.keys())}")
        if 'people' in player_data:
            player = player_data['people'][0]
            print(f"Player: {player.get('fullName', 'Unknown')} (ID: {player.get('id')})")
    except Exception as e:
        print(f"Error: {e}")

def test_player_stats():
    """Test different ways to get player stats"""
    print("\n=== Testing Player Stats Types ===")
    
    # Try to get stats for Mookie Betts
    player_id = "605141"  # Mookie Betts
    season = "2024"
    
    # Test different stats types
    stats_types = [
        "season",
        "hitting", 
        "pitching",
        "fielding",
        "sabermetrics",
        "advanced",
        "vs",
        "vsP",
        "vsL",
        "vsR",
        "vsPitcher",
        "vsL_season",
        "vsR_season"
    ]
    
    for stats_type in stats_types:
        try:
            print(f"\nTrying stats type: {stats_type}")
            params = {
                "stats": stats_type,
                "group": "hitting",
                "season": season,
                "personId": player_id
            }
            print(f"Params: {params}")
            data = statsapi.get("stats", params)
            
            if 'stats' in data and data['stats']:
                splits = data['stats'][0].get('splits', [])
                print(f"SUCCESS! Found {len(splits)} splits")
                if splits:
                    split = splits[0]
                    print(f"First split keys: {list(split.keys())}")
                    if 'stat' in split:
                        print(f"Stat keys: {list(split['stat'].keys())}")
            else:
                print("No stats found")
                
        except Exception as e:
            print(f"Failed: {e}")

def test_vs_pitcher_methods():
    """Test methods to get vs pitcher stats"""
    print("\n=== Testing Vs Pitcher Methods ===")
    
    # Try different approaches for H2H data
    batter_id = "605141"  # Mookie Betts
    pitcher_id = "543243"  # Sonny Gray
    season = "2024"
    
    methods = [
        # Method 1: Use stats endpoint with vs type
        {
            "endpoint": "stats",
            "params": {
                "stats": "vsP",
                "group": "hitting", 
                "season": season,
                "personId": batter_id,
                "opponentId": pitcher_id
            }
        },
        # Method 2: Try gameLog to find games they played
        {
            "endpoint": "stats", 
            "params": {
                "stats": "gameLog",
                "group": "hitting",
                "season": season,
                "personId": batter_id
            }
        },
        # Method 3: Try with different parameter name
        {
            "endpoint": "stats",
            "params": {
                "stats": "season",
                "group": "hitting",
                "season": season,
                "personId": batter_id,
                "pitcherId": pitcher_id  
            }
        }
    ]
    
    for i, method in enumerate(methods, 1):
        print(f"\n--- Method {i}: {method['endpoint']} ---")
        print(f"Params: {method['params']}")
        try:
            data = statsapi.get(method["endpoint"], method["params"])
            print(f"SUCCESS! Keys: {list(data.keys())}")
            
            if 'stats' in data and data['stats']:
                stats_obj = data['stats'][0]
                splits = stats_obj.get('splits', [])
                print(f"Found {len(splits)} splits")
                
                # Look for relevant splits
                for j, split in enumerate(splits[:5]):  # Check first 5
                    print(f"  Split {j+1}: {list(split.keys())}")
                    if 'opponent' in split:
                        print(f"    Opponent: {split['opponent']}")
                    if 'game' in split:
                        print(f"    Game info available")
                        
        except Exception as e:
            print(f"Failed: {e}")

if __name__ == "__main__":
    test_player_info()
    test_player_stats()  
    test_vs_pitcher_methods()
