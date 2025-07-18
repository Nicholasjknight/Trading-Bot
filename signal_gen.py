# signal_gen.py

import pandas as pd
import yfinance as yf
import numpy as np

INPUT_FILE = "earnings_options_data.csv"
OUTPUT_FILE = "filtered_signals.csv"

# === STRATEGY PARAMETERS ===
BUY_THRESHOLD = 6.0    # Buy straddle if expected move > 6%
SELL_THRESHOLD = 4.0   # Sell straddle if expected move < 4%
# Between = No clear edge (skip)

def fetch_price(ticker):
    try:
        data = yf.Ticker(ticker)
        price = data.history(period="1d")["Close"].iloc[-1]
        return round(float(price), 2)
    except Exception as e:
        print(f"[WARN] Failed to fetch price for {ticker}: {e}")
        return np.nan

def generate_signals():
    df = pd.read_csv(INPUT_FILE)
    assert "Earnings Date" in df.columns, "Missing 'Earnings Date' column in earnings_options_data.csv"
    signals = []

    for _, row in df.iterrows():
        move = row['Expected Move %']
        ticker = row['Ticker']

        if move >= BUY_THRESHOLD:
            play = "BUY straddle"
        elif move <= SELL_THRESHOLD:
            play = "SELL straddle"
        else:
            continue  # skip trades with no edge

        est_val = fetch_price(ticker)

        signals.append({
            "Ticker": ticker,
            "Earnings Date": row["Earnings Date"],
            "Spot Price": row["Spot Price"],
            "Strike": row["Strike"],
            "Straddle Cost": row["Straddle Cost"],
            "Expected Move %": move,
            "Expiration": row["Expiration"],
            "Play": play,
            "Current Est Value": est_val
        })

    signal_df = pd.DataFrame(signals)
    signal_df.to_csv(OUTPUT_FILE, index=False)
    print(f"[✅] Signals saved to: {OUTPUT_FILE} ({len(signal_df)} entries)")

if __name__ == "__main__":
    generate_signals()
