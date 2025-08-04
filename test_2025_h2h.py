#!/usr/bin/env python3

import sys
sys.path.append('./MLB-StatsAPI')
import statsapi

def test_2025_dodgers_cardinals():
    """Test the specific 6/6/2025 Dodgers vs Cardinals game"""
    print("=== Testing 6/6/2025 Dodgers vs Cardinals Game ===")
    
    # Get 2025 schedule for Cardinals around June 6, 2025
    try:
        schedule = statsapi.schedule(start_date='2025-06-05', end_date='2025-06-07', team=138)  # Cardinals
        print(f"Found {len(schedule)} Cardinals games around 6/6/2025:")
        
        for game in schedule:
            print(f"Date: {game['game_date']}")
            print(f"  {game['away_name']} @ {game['home_name']}")
            print(f"  Away Pitcher: {game.get('away_probable_pitcher', 'TBD')}")
            print(f"  Home Pitcher: {game.get('home_probable_pitcher', 'TBD')}")
            print(f"  Game ID: {game['game_id']}")
            print(f"  Status: {game['status']}")
            print()
            
    except Exception as e:
        print(f"Error getting schedule: {e}")

def test_2025_player_stats():
    """Test getting 2025 stats for Sonny Gray and Dodgers players"""
    print("=== Testing 2025 Player Stats ===")
    
    # Check if Sonny Gray has 2025 stats
    try:
        sonny_stats = statsapi.get("stats", {
            "stats": "season",
            "group": "pitching", 
            "season": "2025",
            "personId": "543243"  # Sonny Gray
        })
        
        if 'stats' in sonny_stats and sonny_stats['stats']:
            splits = sonny_stats['stats'][0].get('splits', [])
            print(f"Sonny Gray 2025: Found {len(splits)} splits")
            if splits:
                split = splits[0]
                team = split.get('team', {})
                print(f"  Team: {team.get('name')} (ID: {team.get('id')})")
                stat = split.get('stat', {})
                print(f"  Games: {stat.get('gamesStarted', 0)} GS, ERA: {stat.get('era', 'N/A')}")
        else:
            print("No 2025 stats found for Sonny Gray")
            
    except Exception as e:
        print(f"Error getting Sonny Gray 2025 stats: {e}")
    
    # Check Mookie Betts 2025 stats
    try:
        mookie_stats = statsapi.get("stats", {
            "stats": "season",
            "group": "hitting",
            "season": "2025", 
            "personId": "605141"  # Mookie Betts
        })
        
        if 'stats' in mookie_stats and mookie_stats['stats']:
            splits = mookie_stats['stats'][0].get('splits', [])
            print(f"Mookie Betts 2025: Found {len(splits)} splits")
            if splits:
                split = splits[0]
                team = split.get('team', {})
                print(f"  Team: {team.get('name')} (ID: {team.get('id')})")
                stat = split.get('stat', {})
                print(f"  Games: {stat.get('gamesPlayed', 0)} GP, AVG: {stat.get('avg', 'N/A')}")
        else:
            print("No 2025 stats found for Mookie Betts")
            
    except Exception as e:
        print(f"Error getting Mookie Betts 2025 stats: {e}")

def test_game_log_approach():
    """Test using game log to find H2H data"""
    print("\n=== Testing Game Log Approach for H2H ===")
    
    # Get Mookie Betts game log for 2025
    try:
        game_log = statsapi.get("stats", {
            "stats": "gameLog",
            "group": "hitting",
            "season": "2025",
            "personId": "605141"  # Mookie Betts
        })
        
        if 'stats' in game_log and game_log['stats']:
            splits = game_log['stats'][0].get('splits', [])
            print(f"Mookie Betts 2025 game log: Found {len(splits)} games")
            
            # Look for games around 6/6/2025 or against Cardinals
            cardinals_games = []
            june_games = []
            
            for split in splits:
                game_info = split.get('game', {})
                date = split.get('date', '')
                opponent = split.get('opponent', {})
                
                # Check if it's against Cardinals (team ID 138)
                if opponent.get('id') == 138:
                    cardinals_games.append(split)
                    
                # Check if it's in June 2025
                if '2025-06' in date:
                    june_games.append(split)
            
            print(f"Found {len(cardinals_games)} games vs Cardinals")
            print(f"Found {len(june_games)} games in June 2025")
            
            # Show Cardinals games
            for i, game in enumerate(cardinals_games):
                print(f"\nCardinals Game {i+1}:")
                print(f"  Date: {game.get('date')}")
                print(f"  Opponent: {game.get('opponent', {}).get('name')}")
                print(f"  Game: {game.get('game', {})}")
                stat = game.get('stat', {})
                print(f"  Stats: {stat.get('atBats')} AB, {stat.get('hits')} H, {stat.get('avg')} AVG")
                
            # Show specific 6/6 game if found
            for game in june_games:
                if '2025-06-06' in game.get('date', ''):
                    print(f"\n*** FOUND 6/6/2025 GAME! ***")
                    print(f"Date: {game.get('date')}")
                    print(f"Opponent: {game.get('opponent', {}).get('name')}")
                    print(f"Game Info: {game.get('game', {})}")
                    break
                    
        else:
            print("No game log found for Mookie Betts 2025")
            
    except Exception as e:
        print(f"Error getting game log: {e}")

if __name__ == "__main__":
    test_2025_dodgers_cardinals()
    test_2025_player_stats()
    test_game_log_approach()
