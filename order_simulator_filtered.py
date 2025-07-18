# order_simulator_filtered.py

import pandas as pd
import random

INPUT_FILE = "filtered_signals.csv"
OUTPUT_FILE = "filtered_simulated_trades.csv"

# === STRATEGY PARAMETERS ===
STOP_LOSS = 0.40     # Exit if loss exceeds 40%
TAKE_PROFIT = 0.70   # Exit if gain exceeds 70%
SIM_MOVE_RANGE = (0.85, 1.15)  # Simulated % move range (85% to 115%)

def simulate_trade(play, straddle_cost):
    move = random.uniform(*SIM_MOVE_RANGE)

    if play == "BUY straddle":
        pnl_pct = move - 1.0
    elif play == "SELL straddle":
        pnl_pct = 1.0 - move
    else:
        return None

    if pnl_pct >= TAKE_PROFIT:
        pnl_pct = TAKE_PROFIT
    elif pnl_pct <= -STOP_LOSS:
        pnl_pct = -STOP_LOSS

    pnl_usd = round(pnl_pct * straddle_cost, 2)
    return round(pnl_pct * 100, 2), pnl_usd

def main():
    df = pd.read_csv(INPUT_FILE)
    results = []

    for _, row in df.iterrows():
        play = row['Play']
        cost = float(row['Straddle Cost'])

        sim_pct, sim_usd = simulate_trade(play, cost)
        results.append({
            "Ticker": row["Ticker"],
            "Play": play,
            "Straddle Cost": cost,
            "Simulated P/L %": sim_pct,
            "Simulated P/L $": sim_usd
        })

    out_df = pd.DataFrame(results)
    out_df.to_csv(OUTPUT_FILE, index=False)
    print(f"Filtered simulation complete → {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
