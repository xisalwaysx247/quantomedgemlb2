#!/usr/bin/env python3

import sys
sys.path.append('./MLB-StatsAPI')
import statsapi

def analyze_boxscore_h2h():
    """Analyze the 6/6/2025 game boxscore to extract H2H data"""
    print("=== Analyzing 6/6/2025 Boxscore for H2H Data ===")
    
    game_id = "777620"  # 6/6/2025 Dodgers @ Cardinals
    
    try:
        # Get full game data with play-by-play
        game_data = statsapi.get('game', {'gamePk': game_id})
        
        # Check what data is available in liveData
        live_data = game_data.get('liveData', {})
        print("LiveData keys:", list(live_data.keys()))
        
        # Look for plays data
        if 'plays' in live_data:
            plays = live_data['plays']
            print("Plays keys:", list(plays.keys()))
            
            if 'allPlays' in plays:
                all_plays = plays['allPlays']
                print(f"Found {len(all_plays)} total plays")
                
                # Analyze plays to find pitcher-batter matchups
                h2h_data = {}
                
                for i, play in enumerate(all_plays):
                    # Look for matchup data in every play
                    if 'matchup' in play:
                        matchup = play['matchup']
                        
                        batter = matchup.get('batter', {})
                        pitcher = matchup.get('pitcher', {})
                        
                        batter_id = batter.get('id')
                        pitcher_id = pitcher.get('id')
                        batter_name = batter.get('fullName', 'Unknown')
                        pitcher_name = pitcher.get('fullName', 'Unknown')
                        
                        # Get play result from the 'result' field
                        result = play.get('result', {})
                        event_type = result.get('event', 'Unknown')
                        
                        if i < 20:  # Show first 20 plays for debugging
                            print(f"\nPlay {i+1}:")
                            print(f"  {batter_name} vs {pitcher_name}")
                            print(f"  Result: {event_type}")
                            print(f"  Result keys: {list(result.keys())}")
                        
                        # Track H2H data
                        key = (batter_id, pitcher_id)
                        if key not in h2h_data:
                            h2h_data[key] = {'at_bats': 0, 'hits': 0, 'matchups': []}
                        
                        # Count at-bats (excluding walks, HBP, etc.)
                        if event_type not in ['Walk', 'Hit By Pitch', 'Catcher Interference', 'Intent Walk']:
                            h2h_data[key]['at_bats'] += 1
                            
                            # Count hits
                            if event_type in ['Single', 'Double', 'Triple', 'Home Run']:
                                h2h_data[key]['hits'] += 1
                        
                        h2h_data[key]['matchups'].append({
                            'event': event_type,
                            'inning': play.get('about', {}).get('inning', 0)
                        })
                
                # Display H2H summary
                print(f"\n=== H2H Summary from Game ===")
                for (batter_id, pitcher_id), stats in h2h_data.items():
                    if stats['at_bats'] > 0:  # Only show actual at-bats
                        batter_name = get_player_name(batter_id)
                        pitcher_name = get_player_name(pitcher_id)
                        hits = stats['hits']
                        at_bats = stats['at_bats']
                        print(f"{batter_name} vs {pitcher_name}: {hits}-{at_bats}")
                        
                        for matchup in stats['matchups']:
                            print(f"  Inning {matchup['inning']}: {matchup['event']}")
                
                return h2h_data
        
        # Also try boxscore approach
        if 'boxscore' in live_data:
            boxscore = live_data['boxscore']
            print("\nBoxscore keys:", list(boxscore.keys()))
            
            teams = boxscore.get('teams', {})
            if 'away' in teams and 'home' in teams:
                print("Away team batters:", len(teams['away'].get('batters', [])))
                print("Home team pitchers:", len(teams['home'].get('pitchers', [])))
        
    except Exception as e:
        print(f"Error analyzing boxscore: {e}")
        import traceback
        traceback.print_exc()

def get_player_name(player_id):
    """Get player name from ID"""
    try:
        player_data = statsapi.get("person", {"personId": str(player_id)})
        if 'people' in player_data and player_data['people']:
            return player_data['people'][0].get('fullName', f'Player {player_id}')
    except:
        pass
    return f'Player {player_id}'

if __name__ == "__main__":
    analyze_boxscore_h2h()
