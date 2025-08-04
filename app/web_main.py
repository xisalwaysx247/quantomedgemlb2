"""
FastAPI Web Interface for Quantum Edge CLI
Provides web access to MLB analytics and matchup data
"""

from fastapi import FastAPI, Request, HTTPException, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from datetime import datetime, timedelta
import os
import json
import logging

# Import existing analytics functions
from app.services.mlb_api import (
    is_weak_pitcher, 
    classify_hitter, 
    get_hit_streak, 
    fetch_team_roster,
    fetch_games_for_date
)
from app.services.h2h import hitter_vs_pitcher_season

# Import database components
from app.db.schema import Base, Pick
from app.db.session import get_db, SessionLocal

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="🧠 Quantum Edge Analytics",
    description="Advanced MLB Analytics and Market Intelligence",
    version="1.0.0"
)

# Initialize database tables
try:
    Base.metadata.create_all(bind=SessionLocal().bind)
    logger.info("Database tables created successfully")
except Exception as e:
    logger.error(f"Database initialization error: {e}")

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Templates
templates = Jinja2Templates(directory="app/templates")

def safe_format(value, decimals=3, default="N/A"):
    """Safely format numeric values for display"""
    if value is None or value == "N/A":
        return default
    try:
        return f"{float(value):.{decimals}f}"
    except (ValueError, TypeError):
        return default

def get_team_roster(team_id: int):
    """Get team roster data with analytics"""
    try:
        roster = fetch_team_roster(team_id)
        if not roster:
            return None
            
        hitters = []
        pitchers = []
        
        for player in roster:
            position = player.get("position", {}).get("abbreviation", "")
            player_id = player.get("person", {}).get("id")
            player_name = player.get("person", {}).get("fullName", "Unknown")
            
            if position == "P":
                # Process pitcher
                pitcher_stats = {}
                try:
                    player_file = os.path.join("data", "players", f"{player_id}.json")
                    if os.path.exists(player_file):
                        with open(player_file, "r") as f:
                            pitcher_stats = json.load(f)
                except:
                    pass
                
                pitchers.append({
                    "player_id": player_id,
                    "name": player_name,
                    "role": position,
                    "era": safe_format(pitcher_stats.get('era')),
                    "whip": safe_format(pitcher_stats.get('whip')),
                    "wins": pitcher_stats.get("wins", 0),
                    "losses": pitcher_stats.get("losses", 0),
                    "strikeouts_per_nine": safe_format(pitcher_stats.get('strikeoutsPer9Inn')),
                    "status": "Strong" if not is_weak_pitcher(pitcher_stats) else "Weak",
                    "status_class": "strong" if not is_weak_pitcher(pitcher_stats) else "weak"
                })
            else:
                # Process hitter
                hitter_stats = {}
                hit_streak = 0
                try:
                    player_file = os.path.join("data", "players", f"{player_id}.json")
                    if os.path.exists(player_file):
                        with open(player_file, "r") as f:
                            hitter_stats = json.load(f)
                    hit_streak = get_hit_streak(player_id) if player_id else 0
                except:
                    pass
                
                tier = classify_hitter(hitter_stats)
                
                hitters.append({
                    "player_id": player_id,
                    "name": player_name,
                    "position": position,
                    "tier": tier,
                    "avg": safe_format(hitter_stats.get('avg')),
                    "hr": str(hitter_stats.get("homeRuns", "0")),
                    "rbi": str(hitter_stats.get("rbi", "0")),
                    "ops": safe_format(hitter_stats.get('ops')),
                    "streak": str(hit_streak) if hit_streak > 0 else "0"
                })
        
        # Sort hitters by batting average and tier
        def sort_key(hitter):
            tier_priority = {"🟢": 0, "🟡": 1, "🔴": 2, "❓": 3}
            try:
                avg_value = float(hitter["avg"]) if hitter["avg"] != "N/A" else 0.0
            except:
                avg_value = 0.0
            return (-avg_value, tier_priority.get(hitter["tier"], 4))
        
        hitters.sort(key=sort_key)
        
        # Calculate roster stats
        total_hitters = len(hitters)
        strong_count = sum(1 for h in hitters if h["tier"] == "🟢")
        bubble_count = sum(1 for h in hitters if h["tier"] == "🟡")
        weak_count = sum(1 for h in hitters if h["tier"] == "🔴")
        
        roster_stats = {
            "total_hitters": total_hitters,
            "strong_count": strong_count,
            "bubble_count": bubble_count,
            "weak_count": weak_count,
            "strong_pct": f"{(strong_count/total_hitters*100):.1f}" if total_hitters > 0 else "0.0",
            "bubble_pct": f"{(bubble_count/total_hitters*100):.1f}" if total_hitters > 0 else "0.0",
            "weak_pct": f"{(weak_count/total_hitters*100):.1f}" if total_hitters > 0 else "0.0"
        }
        
        # Lineup analysis (top 9)
        if total_hitters >= 9:
            top_9_strong = sum(1 for h in hitters[:9] if h["tier"] == "🟢")
            top_9_bubble = sum(1 for h in hitters[:9] if h["tier"] == "🟡")
            top_9_weak = 9 - top_9_strong - top_9_bubble
            
            roster_stats["lineup_analysis"] = {
                "strong_in_lineup": top_9_strong,
                "bubble_in_lineup": top_9_bubble,
                "weak_in_lineup": top_9_weak,
                "strong_pct": f"{(top_9_strong/9*100):.1f}",
                "bubble_pct": f"{(top_9_bubble/9*100):.1f}",
                "weak_pct": f"{(top_9_weak/9*100):.1f}"
            }
            
            # Bench analysis
            if total_hitters > 9:
                bench_hitters = hitters[9:]
                bench_strong = sum(1 for h in bench_hitters if h["tier"] == "🟢")
                bench_bubble = sum(1 for h in bench_hitters if h["tier"] == "🟡")
                bench_weak = len(bench_hitters) - bench_strong - bench_bubble
                
                if bench_strong > 2:
                    depth_message = f"💪 EXCELLENT DEPTH: {bench_strong} strong hitters available off the bench!"
                    depth_class = "excellent"
                elif bench_strong > 0:
                    depth_message = f"✅ GOOD DEPTH: {bench_strong} strong bench option(s) available"
                    depth_class = "good"
                else:
                    depth_message = "⚠️ LIMITED DEPTH: No strong hitters on the bench"
                    depth_class = "limited"
                
                roster_stats["bench_analysis"] = {
                    "bench_count": len(bench_hitters),
                    "bench_strong": bench_strong,
                    "bench_bubble": bench_bubble,
                    "bench_weak": bench_weak,
                    "depth_message": depth_message,
                    "depth_class": depth_class
                }
        
        return {
            "hitters": hitters,
            "pitchers": pitchers
        }, roster_stats
        
    except Exception as e:
        logger.error(f"Error getting team roster {team_id}: {e}")
        return None, None

def clean_team_name(team_name):
    """Clean team name to remove location and keep just the team name"""
    if not team_name or team_name == "Unknown":
        return team_name
    
    # Common location prefixes to remove
    locations_to_remove = [
        "Los Angeles", "San Francisco", "San Diego", "New York", 
        "St. Louis", "Kansas City", "Tampa Bay", "Washington"
    ]
    
    for location in locations_to_remove:
        if team_name.startswith(location):
            return team_name.replace(location, "").strip()
    
    return team_name

def build_weak_pitcher_matchups(date: str):
    """Build weak pitcher matchup data for web display (simplified)"""
    try:
        games = fetch_games_for_date(date, use_cache=True)
        if not games:
            return []
        
        weak_pitcher_games = []
        
        for game in games:
            home_team_raw = game.get("teams", {}).get("home", {}).get("team", {}).get("name", "Unknown")
            away_team_raw = game.get("teams", {}).get("away", {}).get("team", {}).get("name", "Unknown")
            home_team = clean_team_name(home_team_raw)
            away_team = clean_team_name(away_team_raw)
            home_team_id = game.get("teams", {}).get("home", {}).get("team", {}).get("id")
            away_team_id = game.get("teams", {}).get("away", {}).get("team", {}).get("id")
            
            logger.debug(f"🏟️ Processing game: {away_team} @ {home_team}")
            
            home_pitcher = game.get("home_pitcher", {})
            away_pitcher = game.get("away_pitcher", {})
            
            weak_pitchers_found = []
            
            for pitcher_key, opponent_team_id, pitcher_team, opponent_team in [
                ("home_pitcher", away_team_id, home_team, away_team),
                ("away_pitcher", home_team_id, away_team, home_team)
            ]:
                try:
                    pitcher = game.get(pitcher_key, {})
                    pitcher_name = pitcher.get("fullName", "Unknown")
                    
                    logger.debug(f"🔍 Checking pitcher: {pitcher_name} ({pitcher_team})")
                    
                    if pitcher_name != "TBD" and pitcher and is_weak_pitcher(pitcher.get("stats", {})):
                        logger.info(f"⚠️ Weak pitcher found: {pitcher_name} ({pitcher_team})")
                        
                        # Use same robust processing as all games pages
                        roster_data = fetch_team_roster(opponent_team_id)
                        roster = []
                        
                        if roster_data:
                            logger.debug(f"🔍 Processing {len(roster_data)} players for {opponent_team} vs weak pitcher {pitcher_name}")
                        
                        for player in roster_data:
                            position = player.get("position", {}).get("abbreviation", "")
                            if position != "P":  # Only hitters
                                player_id = player.get("person", {}).get("id")
                                player_name = player.get("person", {}).get("fullName", "Unknown")
                                
                                logger.debug(f"🔍 Processing player: {player_name} (ID: {player_id})")
                                
                                # Use same robust stats processing as all games
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
                                
                                # Get H2H stats vs the weak pitcher
                                pitcher_id = pitcher.get("id")
                                h2h_stats = "0-0"
                                if pitcher_id and player_id:
                                    h2h_stats = hitter_vs_pitcher_season(player_id, pitcher_id, "2025")
                                
                                roster.append({
                                    "player_id": player_id,
                                    "name": player_name,
                                    "position": position,
                                    "tier": tier,
                                    "avg": safe_format(hitter_stats.get('avg')),
                                    "hr": str(hitter_stats.get("homeRuns", "N/A")),
                                    "rbi": str(hitter_stats.get("rbi", "N/A")),
                                    "ops": safe_format(hitter_stats.get('ops')),
                                    "streak": str(hit_streak) if hit_streak > 0 else "0",
                                    "h2h": h2h_stats
                                })
                        
                        logger.debug(f"✅ Processed {len(roster)} hitters for {opponent_team}")
                        
                        # Sort by batting average - same as all games
                        def sort_key(hitter):
                            try:
                                avg_value = float(hitter["avg"]) if hitter["avg"] != "N/A" else 0.0
                            except:
                                avg_value = 0.0
                            tier_priority = {"🟢": 0, "🟡": 1, "🔴": 2, "❓": 3}
                            return (-avg_value, tier_priority.get(hitter["tier"], 4))
                        
                        roster.sort(key=sort_key)
                        
                        # Calculate comprehensive stats - same as all games
                        if roster:
                            total = len(roster)
                            strong_count = sum(1 for h in roster if h["tier"] == "🟢")
                            bubble_count = sum(1 for h in roster if h["tier"] == "🟡") 
                            weak_count = sum(1 for h in roster if h["tier"] == "🔴")
                            
                            strong_pct = f"{(strong_count/total*100):.1f}" if total > 0 else "0.0"
                            bubble_pct = f"{(bubble_count/total*100):.1f}" if total > 0 else "0.0"
                            weak_pct = f"{(weak_count/total*100):.1f}" if total > 0 else "0.0"
                            
                            # Enhanced recommendation logic - same as all games
                            lineup_strong_pct = float(strong_pct)
                            if len(roster) >= 9:
                                top_9_strong = sum(1 for h in roster[:9] if h["tier"] == "🟢")
                                lineup_strong_pct = (top_9_strong/9*100)
                            
                            if lineup_strong_pct > 30:
                                recommendation = {
                                    "type": "excellent",
                                    "icon": "💰",
                                    "text": f"EXCELLENT OPPORTUNITY: {lineup_strong_pct:.1f}% strong hitters vs weak pitcher!"
                                }
                            elif lineup_strong_pct > 15:
                                recommendation = {
                                    "type": "good", 
                                    "icon": "⚡",
                                    "text": f"GOOD OPPORTUNITY: {lineup_strong_pct:.1f}% strong hitters vs weak pitcher!"
                                }
                            else:
                                recommendation = {
                                    "type": "limited",
                                    "icon": "📋", 
                                    "text": "LIMITED OPPORTUNITY: Mostly weak lineup vs weak pitcher"
                                }
                            
                            logger.info(f"✅ {opponent_team} vs {pitcher_name}: {strong_count}🟢 {bubble_count}🟡 {weak_count}🔴")
                        else:
                            strong_count = bubble_count = weak_count = 0
                            strong_pct = bubble_pct = weak_pct = "0.0"
                            recommendation = None
                            logger.warning(f"⚠️ No roster data for {opponent_team}")
                        
                        weak_pitchers_found.append({
                            "pitcher": {
                                **pitcher,
                                "stats": pitcher.get("stats", {})  # Ensure stats key always exists
                            },
                            "pitcher_team": pitcher_team,
                            "opponent_team": opponent_team,
                            "opponent_team_id": opponent_team_id,
                            "roster": roster,
                            "strong_count": strong_count,
                            "bubble_count": bubble_count,
                            "weak_count": weak_count,
                            "strong_pct": strong_pct,
                            "bubble_pct": bubble_pct,
                            "weak_pct": weak_pct,
                            "recommendation": recommendation
                        })
                    
                except Exception as e:
                    logger.error(f"❌ Error processing pitcher {pitcher_key} for game {game.get('gamePk', 'Unknown')}: {e}")
                    import traceback
                    logger.error(f"Pitcher processing traceback: {traceback.format_exc()}")
                    continue
            
            if weak_pitchers_found:
                weak_pitcher_games.append({
                    "game": game,
                    "home_team": home_team,
                    "away_team": away_team,
                    "weak_pitchers": weak_pitchers_found
                })
                logger.info(f"✅ Added game with {len(weak_pitchers_found)} weak pitcher(s): {away_team} @ {home_team}")
        
        logger.info(f"🎯 Found {len(weak_pitcher_games)} games with weak pitchers")
        return weak_pitcher_games
        
    except Exception as e:
        logger.error(f"Error building weak pitcher matchups: {e}")
        return []

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Home page with welcome and feature overview"""
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/matchups", response_class=HTMLResponse)
async def matchups_page(request: Request, date: str = None):
    """Weak pitcher matchups page - shows list of games"""
    if not date:
        date = datetime.now().strftime("%Y-%m-%d")
    
    try:
        # Validate date format
        datetime.strptime(date, "%Y-%m-%d")
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
    
    games = build_weak_pitcher_matchups(date)
    
    return templates.TemplateResponse("matchups.html", {
        "request": request,
        "games": games,
        "date": date
    })

@app.get("/game/{game_id}", response_class=HTMLResponse)
async def game_detail(request: Request, game_id: str, date: str = None):
    """Individual game detail page with full roster analysis"""
    if not date:
        date = datetime.now().strftime("%Y-%m-%d")
    
    try:
        # Validate date format
        datetime.strptime(date, "%Y-%m-%d")
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
    
    # Get all games and find the specific one
    all_games = build_weak_pitcher_matchups(date)
    game_data = None
    
    for game in all_games:
        if str(game.get("game", {}).get("gamePk")) == game_id:
            game_data = game
            break
    
    if not game_data:
        raise HTTPException(status_code=404, detail="Game not found")
    
    return templates.TemplateResponse("game_detail.html", {
        "request": request,
        "game": game_data,
        "date": date
    })

# All Games Routes
@app.get("/games", response_class=HTMLResponse)
async def all_games_page(request: Request, date: str = None):
    """All games page - shows complete MLB schedule for any date"""
    if not date:
        date = datetime.now().strftime("%Y-%m-%d")
    
    try:
        # Validate date format
        datetime.strptime(date, "%Y-%m-%d")
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
    
    # Get all games for the date
    try:
        games = fetch_games_for_date(date, use_cache=True)
        if not games:
            games = []
    except Exception as e:
        logger.error(f"Error fetching games for all games page: {e}")
        games = []
    
    # Enhance games with formatted data
    enhanced_games = []
    for game in games:
        game_pk = game.get("gamePk")
        home_team_raw = game.get("teams", {}).get("home", {}).get("team", {}).get("name", "Unknown")
        away_team_raw = game.get("teams", {}).get("away", {}).get("team", {}).get("name", "Unknown")
        home_team = clean_team_name(home_team_raw)
        away_team = clean_team_name(away_team_raw)
        
        # Get game status and time
        status = game.get("status", {})
        detailed_state = status.get("detailedState", "Unknown")
        game_date = game.get("gameDate", "")
        
        # Format game time (extract time portion)
        game_time = ""
        if game_date:
            try:
                dt = datetime.fromisoformat(game_date.replace('Z', '+00:00'))
                game_time = dt.strftime("%I:%M %p ET")
            except:
                game_time = "TBD"
        
        # Get pitcher information if available
        home_pitcher = game.get("home_pitcher", {})
        away_pitcher = game.get("away_pitcher", {})
        
        enhanced_games.append({
            "game_pk": game_pk,
            "home_team": home_team,
            "away_team": away_team,
            "game_time": game_time,
            "status": detailed_state,
            "home_pitcher": home_pitcher.get("fullName", "TBD"),
            "away_pitcher": away_pitcher.get("fullName", "TBD"),
            "is_final": "Final" in detailed_state,
            "is_live": "Progress" in detailed_state or "Live" in detailed_state,
            "is_scheduled": detailed_state in ["Scheduled", "Pre-Game"]
        })
    
    # Calculate navigation dates
    try:
        current_date = datetime.strptime(date, "%Y-%m-%d")
        prev_date = (current_date - timedelta(days=1)).strftime("%Y-%m-%d")
        next_date = (current_date + timedelta(days=1)).strftime("%Y-%m-%d")
        today = datetime.now().strftime("%Y-%m-%d")
    except ValueError:
        # Fallback if date parsing fails
        prev_date = ""
        next_date = ""
        today = datetime.now().strftime("%Y-%m-%d")
    
    return templates.TemplateResponse("all_games.html", {
        "request": request,
        "games": enhanced_games,
        "date": date,
        "prev_date": prev_date,
        "next_date": next_date,
        "today": today,
        "total_games": len(enhanced_games)
    })

@app.get("/games/{game_id}", response_class=HTMLResponse)
async def single_game_detail(request: Request, game_id: str, date: str = None):
    """Individual game detail page from all games view"""
    logger.info(f"📍 Loading game detail for game_id={game_id}, date={date}")
    
    if not date:
        date = datetime.now().strftime("%Y-%m-%d")
    
    try:
        # Validate date format
        datetime.strptime(date, "%Y-%m-%d")
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
    
    # Get all games and find the specific one
    try:
        games = fetch_games_for_date(date, use_cache=True)
        game_data = None
        
        logger.info(f"📊 Found {len(games)} games for {date}")
        
        for game in games:
            if str(game.get("gamePk")) == game_id:
                game_data = game
                break
        
        if not game_data:
            logger.error(f"❌ Game {game_id} not found in {len(games)} games")
            raise HTTPException(status_code=404, detail="Game not found")
        
        logger.info(f"✅ Found game: {game_data.get('teams', {}).get('away', {}).get('team', {}).get('name', 'Unknown')} @ {game_data.get('teams', {}).get('home', {}).get('team', {}).get('name', 'Unknown')}")
        
        # Enhanced game data processing
        home_team_raw = game_data.get("teams", {}).get("home", {}).get("team", {}).get("name", "Unknown")
        away_team_raw = game_data.get("teams", {}).get("away", {}).get("team", {}).get("name", "Unknown")
        home_team = clean_team_name(home_team_raw)
        away_team = clean_team_name(away_team_raw)
        
        # Get detailed team rosters for both teams - CLI style
        home_team_id = game_data.get("teams", {}).get("home", {}).get("team", {}).get("id")
        away_team_id = game_data.get("teams", {}).get("away", {}).get("team", {}).get("id")
        
        # Get pitcher information for H2H stats
        home_pitcher = game_data.get("home_pitcher", {})
        away_pitcher = game_data.get("away_pitcher", {})
        home_pitcher_id = home_pitcher.get("id") if home_pitcher else None
        away_pitcher_id = away_pitcher.get("id") if away_pitcher else None
        
        logger.info(f"🏠 Home team ID: {home_team_id}, Away team ID: {away_team_id}")
        logger.info(f"⚾ Home pitcher ID: {home_pitcher_id}, Away pitcher ID: {away_pitcher_id}")
        
        home_roster = []
        away_roster = []
        
        # Get home team roster - CLI style processing
        if home_team_id:
            try:
                logger.info(f"🔍 Fetching home roster for team {home_team_id}")
                home_roster_data = fetch_team_roster(home_team_id)  # Don't convert to int here - let the function handle it
                logger.info(f"📋 Home roster data retrieved: {len(home_roster_data) if home_roster_data else 0} players")
                
                if home_roster_data:
                    for player in home_roster_data:
                        position = player.get("position", {}).get("abbreviation", "")
                        if position != "P":  # Only hitters for now
                            player_id = player.get("person", {}).get("id")
                            player_name = player.get("person", {}).get("fullName", "Unknown")
                            
                            logger.debug(f"🔍 Processing home player: {player_name} (ID: {player_id})")
                            
                            # CLI-style stats processing - much simpler
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
                                logger.debug(f"Could not get stats for home player {player_name}: {e}")
                            
                            tier = classify_hitter(hitter_stats)
                            
                            # Get H2H stats vs the away pitcher
                            h2h_stats = "0-0"
                            if away_pitcher_id and player_id:
                                h2h_stats = hitter_vs_pitcher_season(player_id, away_pitcher_id, "2025")
                            
                            home_roster.append({
                                "player_id": player_id,
                                "name": player_name,
                                "position": position,
                                "tier": tier,
                                "avg": safe_format(hitter_stats.get('avg')),
                                "hr": str(hitter_stats.get("homeRuns", "N/A")),
                                "rbi": str(hitter_stats.get("rbi", "N/A")),
                                "ops": safe_format(hitter_stats.get('ops')),
                                "streak": str(hit_streak) if hit_streak > 0 else "0",
                                "h2h": h2h_stats
                            })
                
                logger.info(f"✅ Processed {len(home_roster)} home hitters")
                            
            except Exception as e:
                logger.error(f"❌ Error fetching home roster: {e}")
                import traceback
                logger.error(f"Home roster traceback: {traceback.format_exc()}")
        
        # Get away team roster - CLI style processing
        if away_team_id:
            try:
                logger.info(f"🔍 Fetching away roster for team {away_team_id}")
                away_roster_data = fetch_team_roster(away_team_id)  # Don't convert to int here - let the function handle it
                logger.info(f"📋 Away roster data retrieved: {len(away_roster_data) if away_roster_data else 0} players")
                
                if away_roster_data:
                    for player in away_roster_data:
                        position = player.get("position", {}).get("abbreviation", "")
                        if position != "P":  # Only hitters for now
                            player_id = player.get("person", {}).get("id")
                            player_name = player.get("person", {}).get("fullName", "Unknown")
                            
                            logger.debug(f"🔍 Processing away player: {player_name} (ID: {player_id})")
                            
                            # CLI-style stats processing - much simpler
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
                                logger.debug(f"Could not get stats for away player {player_name}: {e}")
                            
                            tier = classify_hitter(hitter_stats)
                            
                            # Get H2H stats vs the home pitcher
                            h2h_stats = "0-0"
                            if home_pitcher_id and player_id:
                                h2h_stats = hitter_vs_pitcher_season(player_id, home_pitcher_id, "2025")
                            
                            away_roster.append({
                                "player_id": player_id,
                                "name": player_name,
                                "position": position,
                                "tier": tier,
                                "avg": safe_format(hitter_stats.get('avg')),
                                "hr": str(hitter_stats.get("homeRuns", "N/A")),
                                "rbi": str(hitter_stats.get("rbi", "N/A")),
                                "ops": safe_format(hitter_stats.get('ops')),
                                "streak": str(hit_streak) if hit_streak > 0 else "0",
                                "h2h": h2h_stats
                            })
                
                logger.info(f"✅ Processed {len(away_roster)} away hitters")
                            
            except Exception as e:
                logger.error(f"❌ Error fetching away roster: {e}")
                import traceback
                logger.error(f"Away roster traceback: {traceback.format_exc()}")
        
        # Sort rosters - CLI style
        def sort_key(hitter):
            try:
                avg_value = float(hitter["avg"]) if hitter["avg"] != "N/A" else 0.0
            except:
                avg_value = 0.0
            tier_priority = {"🟢": 0, "🟡": 1, "🔴": 2, "❓": 3}
            return (-avg_value, tier_priority.get(hitter["tier"], 4))
        
        home_roster.sort(key=sort_key)
        away_roster.sort(key=sort_key)
        
        logger.info(f"🎯 Final roster counts - Home: {len(home_roster)}, Away: {len(away_roster)}")
        
        # Calculate roster statistics like the CLI does
        def calculate_roster_stats(roster):
            total = len(roster)
            strong_count = sum(1 for h in roster if h["tier"] == "🟢")
            bubble_count = sum(1 for h in roster if h["tier"] == "🟡")
            weak_count = sum(1 for h in roster if h["tier"] == "🔴")
            
            if total > 0:
                strong_pct = f"{(strong_count/total*100):.1f}"
                bubble_pct = f"{(bubble_count/total*100):.1f}"
                weak_pct = f"{(weak_count/total*100):.1f}"
            else:
                strong_pct = bubble_pct = weak_pct = "0.0"
            
            return {
                "total": total,
                "strong_count": strong_count,
                "bubble_count": bubble_count,
                "weak_count": weak_count,
                "strong_pct": strong_pct,
                "bubble_pct": bubble_pct,
                "weak_pct": weak_pct
            }
        
        home_stats = calculate_roster_stats(home_roster)
        away_stats = calculate_roster_stats(away_roster)
        
        enhanced_game = {
            "game_pk": game_data.get("gamePk"),
            "home_team": home_team,
            "away_team": away_team,
            "home_roster": home_roster,
            "away_roster": away_roster,
            "home_stats": home_stats,
            "away_stats": away_stats,
            "home_pitcher": game_data.get("home_pitcher", {}),
            "away_pitcher": game_data.get("away_pitcher", {}),
            "status": game_data.get("status", {}).get("detailedState", "Unknown"),
            "game_date": game_data.get("gameDate", "")
        }
        
        logger.info(f"✅ Game detail processing complete for {away_team} @ {home_team}")
        
        return templates.TemplateResponse("single_game_detail.html", {
            "request": request,
            "game": enhanced_game,
            "date": date
        })
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error fetching game detail: {e}")
        import traceback
        logger.error(f"Full traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail="Error loading game details")

@app.get("/api/player/{player_id}")
async def get_player_data(player_id: int):
    """API endpoint to get comprehensive player data"""
    try:
        logger.info(f"🔍 Player API called for ID: {player_id}")
        
        # Data folder path
        data_folder = os.path.join(os.getcwd(), "data")
        players_folder = os.path.join(data_folder, "players")
        
        # Load player stats from JSON file
        player_file = os.path.join(players_folder, f"{player_id}.json")
        logger.info(f"📂 Looking for player file: {player_file}")
        
        if not os.path.exists(player_file):
            logger.error(f"❌ Player file not found: {player_file}")
            # List available files for debugging
            if os.path.exists(players_folder):
                available_files = os.listdir(players_folder)[:10]  # First 10 files
                logger.info(f"📋 Available player files (sample): {available_files}")
            raise HTTPException(status_code=404, detail=f"Player {player_id} data not found")
        
        try:
            with open(player_file, "r") as f:
                player_stats = json.load(f)
                logger.info(f"✅ Successfully loaded player stats for {player_id}")
        except Exception as e:
            logger.error(f"❌ Error loading player file {player_file}: {e}")
            raise HTTPException(status_code=500, detail="Error loading player data")
        
        # Get player name - try multiple sources
        player_name = None
        
        # First, check if name is in the player stats file itself
        if "fullName" in player_stats:
            player_name = player_stats["fullName"]
            logger.info(f"✅ Found player name in stats file: {player_name}")
        else:
            # Fallback: search roster files
            rosters_folder = os.path.join(data_folder, "rosters")
            
            if os.path.exists(rosters_folder):
                for roster_file in os.listdir(rosters_folder):
                    roster_path = os.path.join(rosters_folder, roster_file)
                    try:
                        with open(roster_path, "r") as f:
                            roster_data = json.load(f)
                            for player in roster_data:
                                if player.get("id") == player_id:
                                    player_name = player.get("fullName", f"Player {player_id}")
                                    logger.info(f"✅ Found player name in roster: {player_name}")
                                    break
                            if player_name:
                                break
                    except Exception as e:
                        logger.error(f"Error reading roster file {roster_path}: {e}")
                        continue
        
        if not player_name:
            player_name = f"Player {player_id}"
            logger.warning(f"⚠️  Using fallback name: {player_name}")
        
        # Return comprehensive player data
        response_data = {
            "id": player_id,
            "name": player_name,
            "stats": player_stats
        }
        
        logger.info(f"✅ Successfully returning data for {player_name}")
        return response_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Unexpected error fetching player data for {player_id}: {e}")
        import traceback
        logger.error(f"Full traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail="Error fetching player data")

# Player Route (for handling direct navigation attempts)
@app.get("/player/{player_id}", response_class=HTMLResponse)
async def player_redirect(request: Request, player_id: int):
    """Handle direct player navigation by redirecting back with modal trigger"""
    # Get the referer URL to redirect back to the original page
    referer = request.headers.get("referer", "/")
    
    # Add player parameter to the referer URL
    if "?" in referer:
        redirect_url = f"{referer}&player={player_id}"
    else:
        redirect_url = f"{referer}?player={player_id}"
    
    return RedirectResponse(url=redirect_url, status_code=302)

# Pick Tank Routes
@app.get("/pick-tank", response_class=HTMLResponse)
async def pick_tank_index(request: Request, date: str = None):
    """Pick Tank main page - shows today's games with existing picks"""
    if not date:
        date = datetime.now().strftime("%Y-%m-%d")
    
    try:
        # Validate date format
        datetime.strptime(date, "%Y-%m-%d")
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
    
    # Get today's games
    try:
        games = fetch_games_for_date(date, use_cache=True)
        if not games:
            games = []
    except Exception as e:
        logger.error(f"Error fetching games for pick tank: {e}")
        games = []
    
    # Get existing picks for today's games
    db = next(get_db())
    try:
        game_pks = [game.get("gamePk") for game in games if game.get("gamePk")]
        picks = db.query(Pick).filter(Pick.game_pk.in_(game_pks)).all() if game_pks else []
        
        # Group picks by game
        picks_by_game = {}
        for pick in picks:
            if pick.game_pk not in picks_by_game:
                picks_by_game[pick.game_pk] = []
            picks_by_game[pick.game_pk].append(pick)
        
    except Exception as e:
        logger.error(f"Error fetching picks: {e}")
        picks_by_game = {}
    finally:
        db.close()
    
    # Enhance games with team names and picks
    enhanced_games = []
    for game in games:
        game_pk = game.get("gamePk")
        home_team_raw = game.get("teams", {}).get("home", {}).get("team", {}).get("name", "Unknown")
        away_team_raw = game.get("teams", {}).get("away", {}).get("team", {}).get("name", "Unknown")
        home_team = clean_team_name(home_team_raw)
        away_team = clean_team_name(away_team_raw)
        
        enhanced_games.append({
            "game_pk": game_pk,
            "home_team": home_team,
            "away_team": away_team,
            "game_time": game.get("gameDate", ""),
            "status": game.get("status", {}).get("detailedState", "Unknown"),
            "picks": picks_by_game.get(game_pk, [])
        })
    
    return templates.TemplateResponse("pick_tank/index.html", {
        "request": request,
        "games": enhanced_games,
        "date": date
    })

@app.get("/pick-tank/new", response_class=HTMLResponse)
async def pick_tank_new_form(request: Request, game_pk: int):
    """Show form to add a new pick"""
    # Get game info for context
    try:
        date = datetime.now().strftime("%Y-%m-%d")
        games = fetch_games_for_date(date, use_cache=True)
        game_info = None
        
        for game in games:
            if game.get("gamePk") == game_pk:
                home_team_raw = game.get("teams", {}).get("home", {}).get("team", {}).get("name", "Unknown")
                away_team_raw = game.get("teams", {}).get("away", {}).get("team", {}).get("name", "Unknown")
                home_team = clean_team_name(home_team_raw)
                away_team = clean_team_name(away_team_raw)
                home_team_id = game.get("teams", {}).get("home", {}).get("team", {}).get("id")
                away_team_id = game.get("teams", {}).get("away", {}).get("team", {}).get("id")
                
                # Fetch rosters for both teams
                home_roster = []
                away_roster = []
                
                try:
                    if home_team_id:
                        home_roster_data = fetch_team_roster(home_team_id)
                        home_roster = [
                            {
                                "id": player.get("person", {}).get("id"),
                                "name": player.get("person", {}).get("fullName"),
                                "position": player.get("position", {}).get("name", "Unknown")
                            }
                            for player in home_roster_data 
                            if player.get("person", {}).get("fullName")
                        ]
                except Exception as e:
                    logger.error(f"Error fetching home roster for team {home_team_id}: {e}")
                
                try:
                    if away_team_id:
                        away_roster_data = fetch_team_roster(away_team_id)
                        away_roster = [
                            {
                                "id": player.get("person", {}).get("id"),
                                "name": player.get("person", {}).get("fullName"),
                                "position": player.get("position", {}).get("name", "Unknown")
                            }
                            for player in away_roster_data 
                            if player.get("person", {}).get("fullName")
                        ]
                except Exception as e:
                    logger.error(f"Error fetching away roster for team {away_team_id}: {e}")
                
                game_info = {
                    "game_pk": game_pk,
                    "home_team": home_team,
                    "away_team": away_team,
                    "matchup": f"{away_team} @ {home_team}",
                    "home_roster": home_roster,
                    "away_roster": away_roster
                }
                break
        
        if not game_info:
            raise HTTPException(status_code=404, detail="Game not found")
            
    except Exception as e:
        logger.error(f"Error fetching game info: {e}")
        raise HTTPException(status_code=500, detail="Error loading game information")
    
    return templates.TemplateResponse("pick_tank/new.html", {
        "request": request,
        "game": game_info
    })

@app.post("/pick-tank/new", response_class=RedirectResponse)
async def pick_tank_create_pick(
    request: Request,
    game_pk: int = Form(...),
    pick_type: str = Form(...),
    market: str = Form(...),
    selection: str = Form(...),
    stars: int = Form(...),
    odds: str = Form(""),
    comment: str = Form("")
):
    """Create a new pick with enhanced persistence and validation"""
    
    # Enhanced validation
    if stars < 1 or stars > 5:
        raise HTTPException(status_code=422, detail="Star rating must be between 1 and 5")
    
    if len(market.strip()) == 0:
        raise HTTPException(status_code=422, detail="Market is required")
        
    if len(selection.strip()) == 0:
        raise HTTPException(status_code=422, detail="Selection is required")
    
    if len(market.strip()) > 120:
        raise HTTPException(status_code=422, detail="Market description too long (max 120 characters)")
        
    if len(selection.strip()) > 120:
        raise HTTPException(status_code=422, detail="Selection description too long (max 120 characters)")
        
    if len(comment.strip()) > 500:
        raise HTTPException(status_code=422, detail="Comment too long (max 500 characters)")
    
    if pick_type not in ["TEAM", "PLAYER"]:
        raise HTTPException(status_code=422, detail="Pick type must be TEAM or PLAYER")
    
    # Create the pick with enhanced error handling
    db = next(get_db())
    try:
        # Verify database connection
        from sqlalchemy import text
        db.execute(text("SELECT 1"))
        
        new_pick = Pick(
            game_pk=game_pk,
            pick_type=pick_type.upper(),
            market=market.strip(),
            selection=selection.strip(),
            odds=odds.strip() if odds else None,
            stars=stars,
            comment=comment.strip() if comment else None
        )
        
        db.add(new_pick)
        db.commit()
        
        # Verify the pick was saved
        db.refresh(new_pick)
        pick_id = new_pick.id
        
        logger.info(f"✅ Pick saved successfully: ID={pick_id}, Game={game_pk}, Selection={new_pick.selection}")
        
        # Double-check persistence by querying back
        verification = db.query(Pick).filter(Pick.id == pick_id).first()
        if not verification:
            raise Exception("Pick was not properly persisted")
        
        logger.info(f"✅ Pick persistence verified: {verification.selection}")
        
    except Exception as e:
        db.rollback()
        logger.error(f"❌ Error creating pick: {e}")
        # Try to backup database before failing
        from app.db.session import backup_database
        backup_database()
        raise HTTPException(status_code=500, detail=f"Error saving pick: {str(e)}")
    finally:
        db.close()
    
    # Redirect back to pick tank with anchor to the game
    return RedirectResponse(url=f"/pick-tank#game-{game_pk}", status_code=303)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
