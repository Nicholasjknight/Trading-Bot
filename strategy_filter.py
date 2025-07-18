# strategy_filter.py (AI-Grade Robust: Defensive Loading + Schema Validation + Logging)

import pandas as pd
from datetime import datetime
import os

INPUT_FILE = "signals_with_history.csv"
FILTERED_FILE = "filtered_signals.csv"
RANKED_FILE = "ranked_signals.csv"

if os.path.getsize(INPUT_FILE) == 0:
    print(f"{INPUT_FILE} is empty. Exiting.")
    exit(1)

REQUIRED_COLS = ["Ticker", "Play", "Expected Move %", "Move %"]

def log(msg, level="INFO"):
    print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} [{level}] {msg}")

def calculate_confidence(row):
    try:
        expected = float(row['Expected Move %'])
        actual = float(row['Move %'])
        play = row['Play']
        if expected <= 0 or actual < 0:
            return 0
        ratio = actual / expected if expected != 0 else 0
        if play == "BUY straddle":
            score = ratio * 100
        elif play == "SELL straddle":
            score = (2 - ratio) * 100
        else:
            return 0
        return round(max(min(score, 100), 0), 2)
    except Exception as e:
        log(f"Confidence calc failed for {row.get('Ticker', 'N/A')}: {e}", "ERROR")
        return 0

def filter_signals():
    # Defensive CSV load
    try:
        df = pd.read_csv(INPUT_FILE)
        if df.empty:
            log(f"{INPUT_FILE} is empty. No signals to filter.", "WARN")
            pd.DataFrame().to_csv(FILTERED_FILE, index=False)
            pd.DataFrame().to_csv(RANKED_FILE, index=False)
            return
    except Exception as e:
        log(f"Failed to read {INPUT_FILE}: {e}", "ERROR")
        pd.DataFrame().to_csv(FILTERED_FILE, index=False)
        pd.DataFrame().to_csv(RANKED_FILE, index=False)
        return

    # Schema validation
    missing_cols = [col for col in REQUIRED_COLS if col not in df.columns]
    if missing_cols:
        log(f"Missing columns in input: {missing_cols}", "ERROR")
        pd.DataFrame().to_csv(FILTERED_FILE, index=False)
        pd.DataFrame().to_csv(RANKED_FILE, index=False)
        return

    filtered = []
    ranked = []

    for i, row in df.iterrows():
        ticker = row.get("Ticker", f"Row {i}")
        play = row.get("Play")
        try:
            expected = float(row["Expected Move %"])
            actual = float(row["Move %"])
        except Exception as e:
            log(f"[SKIP] {ticker}: missing move data — {e}", "WARN")
            continue

        confidence = calculate_confidence(row)
        row["Confidence"] = confidence
        ranked.append(row)

        # Only filter in strong signals
        if play == "BUY straddle" and actual > expected and confidence >= 55:
            filtered.append(row)
        elif play == "SELL straddle" and actual < expected and confidence >= 55:
            filtered.append(row)
        else:
            log(f"[SKIP] {ticker}: confidence={confidence}, play={play}, expected={expected}, actual={actual}", "INFO")

    pd.DataFrame(filtered).to_csv(FILTERED_FILE, index=False)
    pd.DataFrame(ranked).to_csv(RANKED_FILE, index=False)

    log(f"Filtered trades: {len(filtered)} → {FILTERED_FILE}", "INFO")
    log(f"Ranked signals (all): {len(ranked)} → {RANKED_FILE}", "INFO")

if __name__ == "__main__":
    log("=== Running strategy_filter.py ===", "INFO")
    filter_signals()
