# 🧠 Quantum Edge CLI

A futuristic MLB analytics tool that provides advanced baseball insights, player analysis, and matchup reports with cutting-edge data visualization.

## ✨ Features

- 📊 **Complete Roster Analysis** - View entire team rosters with tier-based player ratings
- ⚾ **Hit Streak Tracking** - Identify players on active hit streaks with advanced analytics
- 🎯 **Daily Matchup Reports** - Get strategic insights against weak pitchers
- 📈 **Advanced Player Statistics** - Comprehensive performance metrics and analysis
- 🏟️ **Team Depth Analysis** - Compare starting lineups vs bench strength
- 💡 **Smart Recommendations** - Context-aware advice based on pitcher vs lineup matchups
- 🔄 **Interactive Menu System** - Easy-to-use command-line interface
- 💾 **Intelligent Caching** - Fast performance with automatic data caching

## 🚀 Quick Start

### Prerequisites
- **Python 3.8 or higher** ([Download Python](https://python.org/downloads/))
- **Git** ([Download Git](https://git-scm.com/downloads/))

### Installation

#### 1. Clone the Repository
```bash
git clone https://github.com/YOUR_USERNAME/quantum-edge-cli.git
cd quantum-edge-cli
```

#### 2. Set Up Virtual Environment

**For macOS/Linux:**
```bash
python -m venv .venv
source .venv/bin/activate
```

**For Windows (Command Prompt):**
```cmd
python -m venv .venv
.venv\Scripts\activate
```

**For Windows (PowerShell):**
```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

#### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

#### 4. Run the Application
```bash
python quantum_edge.py
```

## 🎮 Usage

### Interactive Menu (Recommended for Beginners)
```bash
python quantum_edge.py menu
```

This launches the interactive menu where you can select options by number:
```
🧠 Quantum Edge CLI
Explore MLB Data with Futuristic Analytics

Available Commands:
┏━━━━━━━━┳━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Number ┃ Command          ┃ Description                                            ┃
┡━━━━━━━━╇━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ 1      │ pull-teams       │ Pull all teams and save them to /data/teams.json.     │
│ 2      │ pull-rosters     │ Pull full rosters for all teams and save them.        │
│ 3      │ pull-player-stats│ Pull advanced stats for all players.                  │
│ 9      │ matchup_report   │ Generate a Daily Weak Pitcher Matchup Report.         │
│ 12     │ all-games        │ View all games for a date with interactive analysis.   │
└────────┴──────────────────┴────────────────────────────────────────────────────────┘
```

### Direct Commands

#### Initial Data Setup (Run These First)
```bash
# Pull all team data
python quantum_edge.py pull-teams

# Pull complete rosters for all teams  
python quantum_edge.py pull-rosters

# Pull advanced stats for all players
python quantum_edge.py pull-player-stats

# Or run all three at once
python quantum_edge.py update-all
```

#### Analysis Commands
```bash
# Analyze players on hit streaks
python quantum_edge.py streaks

# Generate weak pitcher matchup report for today
python quantum_edge.py matchup-report --date 2025-07-31

# View all games with interactive analysis
python quantum_edge.py all-games --date 2025-07-31

# Update hit streak cache
python quantum_edge.py update-streaks
```

#### Individual Lookups
```bash
# View specific team info
python quantum_edge.py view-team "Yankees"

# View specific player stats  
python quantum_edge.py view-player "Aaron Judge"
```

## 📋 Command Reference

| Command | Description | Example |
|---------|-------------|---------|
| `pull-teams` | Download all MLB teams data | `python quantum_edge.py pull-teams` |
| `pull-rosters` | Download complete rosters for all teams | `python quantum_edge.py pull-rosters` |
| `pull-player-stats` | Download advanced stats for all players | `python quantum_edge.py pull-player-stats` |
| `update-all` | Run all data sync commands in sequence | `python quantum_edge.py update-all` |
| `view-team [name]` | Display team info and roster | `python quantum_edge.py view-team "Dodgers"` |
| `view-player [name]` | Show detailed player analysis | `python quantum_edge.py view-player "Mike Trout"` |
| `streaks` | Find players on active hit streaks | `python quantum_edge.py streaks` |
| `matchup-report` | Generate daily weak pitcher report | `python quantum_edge.py matchup-report --date 2025-07-31` |
| `all-games` | Interactive game analysis for any date | `python quantum_edge.py all-games --date 2025-07-31` |
| `update-streaks` | Refresh hit streak data cache | `python quantum_edge.py update-streaks` |
| `clear-cache` | Clear all cached data | `python quantum_edge.py clear-cache` |
| `refresh-report` | Generate fresh report (bypass cache) | `python quantum_edge.py refresh-report --date 2025-07-31` |

## 🎯 Key Features Explained

### 📊 Complete Roster Analysis
- Shows **entire team rosters**, not just starting lineups
- **Tier-based ratings**: 🟢 Strong, 🟡 Bubble, 🔴 Weak, ❓ No Data
- **Bench depth analysis**: See available pinch-hitting options
- **Lineup vs roster breakdown**: Compare starters to full roster strength

### ⚾ Hit Streak Tracking
- Identifies players on **2+ game hit streaks**
- **Smart caching** for fast performance
- **Tier integration** shows which strong hitters are hot
- **Team-based organization** for easy analysis

### 🎯 Matchup Reports
- **Weak pitcher identification** using advanced metrics (ERA, WHIP, BAA)
- **Interactive game selection** - choose specific games to analyze
- **Complete opponent analysis** - see full roster vs starting lineup
- **Strategic recommendations** based on pitcher strength vs lineup quality

### 💡 Smart Recommendations
The CLI provides context-aware insights:
- **vs Weak Pitchers**: Highlights offensive opportunities
- **vs Strong Pitchers**: Assesses competitive matchups
- **Bench Depth**: Identifies late-game substitution advantages
- **Lineup Quality**: Compares likely starters to full roster

## 📁 Data Storage

The application creates these folders automatically:
```
quantum-edge-cli/
├── data/
│   ├── teams.json              # All MLB teams
│   ├── hit_streaks_cache.json  # Players on active streaks
│   ├── detailed_streaks_cache.json # Complete streak data
│   ├── rosters/                # Team roster files
│   │   ├── 109.json           # (e.g., Arizona Diamondbacks)
│   │   └── ...
│   ├── players/               # Individual player stats
│   │   ├── 545361.json        # (e.g., Mike Trout)
│   │   └── ...
│   └── matchup_cache/         # Cached game data
│       ├── matchup_2025-07-31.json
│       └── ...
```

## 🔧 Troubleshooting

### Virtual Environment Issues
**Problem:** `command not found: source` (Windows)
**Solution:** Use the Windows-specific activation command:
```cmd
.venv\Scripts\activate
```

**Problem:** `cannot activate virtual environment`
**Solution:** Make sure you're in the project directory:
```bash
cd quantum-edge-cli
ls -la  # Should see .venv folder
```

### Python Version Issues
**Problem:** `python: command not found`
**Solution:** Try using `python3` instead:
```bash
python3 -m venv .venv
python3 quantum_edge.py
```

### Permission Issues (macOS/Linux)
**Problem:** `Permission denied`
**Solution:** Make the script executable:
```bash
chmod +x quantum_edge.py
```

### Missing Data
**Problem:** `No teams data found`
**Solution:** Run the initial setup commands:
```bash
python quantum_edge.py update-all
```

## 📝 Example Workflow

Here's a typical workflow for using Quantum Edge CLI:

### 1. Initial Setup (First Time Only)
```bash
# Install and set up the application
git clone https://github.com/YOUR_USERNAME/quantum-edge-cli.git
cd quantum-edge-cli
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# Download initial data
python quantum_edge.py update-all
```

### 2. Daily Analysis
```bash
# Activate environment (if not already active)
source .venv/bin/activate

# Check today's games and matchups
python quantum_edge.py all-games --date 2025-07-31

# Look for weak pitcher opportunities  
python quantum_edge.py matchup-report --date 2025-07-31

# Check current hit streaks
python quantum_edge.py streaks
```

### 3. Player Research
```bash
# Look up specific players
python quantum_edge.py view-player "Ronald Acuña Jr."
python quantum_edge.py view-team "Braves"
```

## 🤝 Contributing

We welcome contributions! Here's how to get started:

1. **Fork the repository**
2. **Create a feature branch**
   ```bash
   git checkout -b feature/amazing-feature
   ```
3. **Make your changes**
4. **Commit your changes**
   ```bash
   git commit -m 'Add amazing feature'
   ```
5. **Push to your branch**
   ```bash
   git push origin feature/amazing-feature
   ```
6. **Open a Pull Request**

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

- **Issues**: [Open an issue on GitHub](https://github.com/YOUR_USERNAME/quantum-edge-cli/issues)
- **Questions**: Check existing issues or create a new one
- **Feature Requests**: We'd love to hear your ideas!

## 🙏 Acknowledgments

- Built on top of the excellent [MLB-StatsAPI](https://github.com/toddrob99/MLB-StatsAPI)
- Uses [Rich](https://github.com/Textualize/rich) for beautiful terminal output
- Powered by [Typer](https://github.com/tiangolo/typer) for the CLI interface

---

**Happy analyzing! ⚾️📊**
