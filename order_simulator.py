# order_simulator.py

import pandas as pd
import random

INPUT_FILE = "earnings_signals.csv"
OUTPUT_FILE = "simulated_trades.csv"

# === STRATEGY PARAMETERS ===
STOP_LOSS = 0.40     # Exit if -40%
TAKE_PROFIT = 0.70   # Exit if +70%
SIM_MOVE_RANGE = (0.85, 1.15)  # Simulated move range (85% to 115% of straddle cost)

def simulate_trade(play, straddle_cost):
    """
    Simulate a price movement and return profit or loss.
    """
    move_multiplier = random.uniform(*SIM_MOVE_RANGE)

    if play == "BUY straddle":
        outcome = (move_multiplier - 1.0)  # Long volatility
    elif play == "SELL straddle":
        outcome = (1.0 - move_multiplier)  # Short volatility
    else:
        return None  # Skip

    # Apply SL/TP
    if outcome >= TAKE_PROFIT:
        return TAKE_PROFIT
    elif outcome <= -STOP_LOSS:
        return -STOP_LOSS
    else:
        return round(outcome, 3)

def main():
    df = pd.read_csv(INPUT_FILE)
    results = []

    for _, row in df.iterrows():
        play = row['Play']
        cost = row['Straddle Cost']

        if play == "SKIP":
            continue

        pnl_pct = simulate_trade(play, cost)
        if pnl_pct is None:
            continue

        pnl_usd = round(pnl_pct * cost, 2)

        results.append({
            "Ticker": row["Ticker"],
            "Play": play,
            "Straddle Cost": cost,
            "Simulated P/L %": round(pnl_pct * 100, 2),
            "Simulated P/L $": pnl_usd
        })

    out_df = pd.DataFrame(results)
    out_df.to_csv(OUTPUT_FILE, index=False)
    print(f"Simulated trades saved to: {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
