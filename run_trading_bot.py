# run_trading_bot.py

import subprocess
import datetime

scripts = [
    "earnings_scraper.py",             # Scrape upcoming earnings
    "options_data.py",                 # Fetch option chain data
    "signal_gen.py",                   # Generate straddle signals
    "historical_move_analyzer.py",     # Analyze past earnings moves
    "strategy_filter.py",              # Filter for quality trades
    "order_simulator_filtered.py",     # Simulate trades for review
    "broker_api.py",                   # Execute real (paper) trades
    "exit_positions.py",               # Exit old positions if needed
    "pnl_tracker.py"                   # Track profit/loss for the day
]

print(f"🔁 Starting automated trading bot ({datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')})")
print("=" * 60)

for script in scripts:
    print(f"▶️ Running {script}...")
    try:
        subprocess.run(["python", script], check=True)
    except subprocess.CalledProcessError as e:
        print(f"[❌ ERROR] {script} failed with exit code {e.returncode}")
        break

print("=" * 60)
print(f"✅ Trading bot run complete ({datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')})")
