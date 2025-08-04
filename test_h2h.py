#!/usr/bin/env python3
"""
Test script to debug H2H function and understand the MLB API response
"""
import statsapi
import json

def test_h2h_debug(batter_id: int, pitcher_id: int, season: str = "2025"):
    """
    Debug version of the H2H function to see what's actually happening
    """
    print(f"\n=== Testing H2H: Batter {batter_id} vs Pitcher {pitcher_id} in {season} ===")
    
    try:
        # Test the API call
        print(f"Making API call with parameters:")
        params = {
            "stats": "vsPitcher",
            "group": "hitting", 
            "playerId": batter_id,
            "opponentId": pitcher_id,
            "season": season
        }
        print(f"  {params}")
        
        data = statsapi.get("stats", params)
        
        print(f"\nRaw API Response:")
        print(json.dumps(data, indent=2))
        
        # Parse the response
        stats_list = data.get("stats", [])
        print(f"\nStats list length: {len(stats_list)}")
        
        if stats_list:
            first_stat = stats_list[0]
            print(f"First stat keys: {first_stat.keys()}")
            
            splits = first_stat.get("splits", [])
            print(f"Splits length: {len(splits)}")
            
            if splits:
                for i, split in enumerate(splits):
                    print(f"\nSplit {i}:")
                    print(f"  Keys: {split.keys()}")
                    stat = split.get("stat", {})
                    print(f"  Stat keys: {stat.keys()}")
                    print(f"  Hits: {stat.get('hits', 'N/A')}")
                    print(f"  At Bats: {stat.get('atBats', 'N/A')}")
                    
                    h = int(stat.get("hits", 0))
                    ab = int(stat.get("atBats", 0))
                    result = f"{h}-{ab}"
                    print(f"  H2H Result: {result}")
            else:
                print("No splits found")
        else:
            print("No stats found")
            
    except Exception as e:
        print(f"Error occurred: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()

def get_player_info(player_id: int):
    """Get basic player info to verify the ID is correct"""
    try:
        player = statsapi.get("player", {"playerId": player_id})
        print(f"Player {player_id}: {player.get('fullName', 'Unknown')} ({player.get('currentTeam', {}).get('name', 'No Team')})")
        return player
    except Exception as e:
        print(f"Error getting player {player_id}: {e}")
        return None

if __name__ == "__main__":
    # Let's test with some known player IDs
    # Sonny Gray's MLB ID (need to find this)
    # Let's first try with some known players
    
    print("=== Finding Sonny Gray and some Dodgers players ===")
    
    # Let's look up some Dodgers players first
    # Mookie Betts: 605141
    # Freddie Freeman: 518692  
    # Max Muncy: 571970
    
    print("\n=== Testing with known player IDs ===")
    
    # Test with Mookie Betts vs a known pitcher
    betts_id = 605141
    freeman_id = 518692
    
    print(f"\nGetting player info:")
    get_player_info(betts_id)
    get_player_info(freeman_id)
    
    # Let's try to find Sonny Gray's ID by searching
    print("\n=== Searching for Sonny Gray ===")
    try:
        # Search for players (this might not work, but let's try)
        players = statsapi.get("search_players", {"query": "Sonny Gray"})
        print(f"Search results: {players}")
    except Exception as e:
        print(f"Search failed: {e}")
    
    # Sonny Gray's actual MLB ID is 543243
    sonny_gray_id = 543243
    print(f"\nTesting Sonny Gray info:")
    get_player_info(sonny_gray_id)
    
    # Test H2H between Sonny Gray and Mookie Betts
    print(f"\n=== Testing H2H: Mookie Betts vs Sonny Gray ===")
    test_h2h_debug(betts_id, sonny_gray_id, "2025")
    
    # Test H2H between Sonny Gray and Freddie Freeman
    print(f"\n=== Testing H2H: Freddie Freeman vs Sonny Gray ===")
    test_h2h_debug(freeman_id, sonny_gray_id, "2025")
    
    # Also test with 2024 data to see if the API works with previous seasons
    print(f"\n=== Testing 2024 data: Mookie Betts vs Sonny Gray ===")
    test_h2h_debug(betts_id, sonny_gray_id, "2024")
