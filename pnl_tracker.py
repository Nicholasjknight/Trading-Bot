# pnl_tracker.py (tolerant version)

import pandas as pd
import os

TRADE_LOG_FILE = "trade_log.csv"
SIGNALS_FILE = "filtered_signals.csv"

def calculate_pnl():
    if not os.path.exists(TRADE_LOG_FILE):
        print(f"[ERROR] File not found: {TRADE_LOG_FILE}")
        return

    if not os.path.exists(SIGNALS_FILE):
        print(f"[ERROR] File not found: {SIGNALS_FILE}")
        return

    trades = pd.read_csv(TRADE_LOG_FILE)
    signals = pd.read_csv(SIGNALS_FILE)

    if "Current Est Value" not in signals.columns:
        print("[WARN] 'Current Est Value' missing in signals — skipping PnL calc.")
        return

    signals = signals.set_index("Ticker")

    trades = trades.dropna(subset=["Fill Price", "Quantity", "Ticker"])
    if trades.empty:
        print("[WARN] No valid trades to evaluate.")
        return

    results = []
    total_pnl = 0.0

    for _, trade in trades.iterrows():
        ticker = trade["Ticker"]
        qty = float(trade["Quantity"])
        entry = float(trade["Fill Price"])

        if ticker not in signals.index:
            print(f"[WARN] No signal found for {ticker}.")
            continue

        try:
            current_val = float(signals.loc[ticker]["Current Est Value"])
        except Exception as e:
            print(f"[ERROR] Cannot parse current est value for {ticker}: {e}")
            continue

        pnl = (current_val - entry) * qty
        total_pnl += pnl
        results.append((ticker, round(pnl, 2)))

    if results:
        print("\n[📊] PnL by Position:")
        for ticker, pnl in results:
            status = "Profit" if pnl > 0 else "Loss"
            print(f" - {ticker}: ${pnl} ({status})")
        print(f"\n[💵] Total Net PnL: ${round(total_pnl, 2)}")
    else:
        print("[INFO] No trades matched for PnL calculation.")

if __name__ == "__main__":
    calculate_pnl()
