import pandas as pd
import yfinance as yf
from datetime import datetime
import os
import pytz

SIGNALS_FILE = "filtered_signals.csv"
OUTPUT_FILE = "signals_with_history.csv"

def log(msg, level="INFO"):
    print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} [{level}] {msg}")

def main():
    # === Defensive read ===
    try:
        if not os.path.exists(SIGNALS_FILE) or os.path.getsize(SIGNALS_FILE) == 0:
            log(f"{SIGNALS_FILE} is empty or missing. Exiting.", "ERROR")
            pd.DataFrame(columns=["Ticker", "Event Date", "Pre Close", "Post Open", "Move %"]).to_csv(OUTPUT_FILE, index=False)
            return
        df = pd.read_csv(SIGNALS_FILE)
        if df.empty or df.shape[1] == 0:
            log(f"{SIGNALS_FILE} has no valid data/columns. Exiting.", "ERROR")
            pd.DataFrame(columns=["Ticker", "Event Date", "Pre Close", "Post Open", "Move %"]).to_csv(OUTPUT_FILE, index=False)
            return
    except Exception as e:
        log(f"Failed to load {SIGNALS_FILE}: {e}", "ERROR")
        pd.DataFrame(columns=["Ticker", "Event Date", "Pre Close", "Post Open", "Move %"]).to_csv(OUTPUT_FILE, index=False)
        return

    results = []
    for idx, row in df.iterrows():
        ticker = row["Ticker"]
        log(f"Analyzing {ticker}...", "INFO")
        try:
            stock = yf.Ticker(ticker)
            hist = stock.history(period="1y")
            date = row.get("Earnings Date")
            if pd.isna(date):
                log(f"{ticker}: Missing earnings date.", "WARN")
                continue
            # Parse and localize earnings date to match history index tz
            date = pd.to_datetime(date)
            idx_tz = hist.index.tz
            if idx_tz and not date.tzinfo:
                date = date.tz_localize(idx_tz)
            elif not date.tzinfo:
                # Fallback: assume NYSE timezone if no tz info
                date = date.tz_localize('America/New_York')
            # Now comparisons will work!
            pre_close_series = hist.loc[hist.index <= date]['Close']
            if pre_close_series.empty:
                log(f"{ticker}: No pre-event data for {date}.", "WARN")
                continue
            pre_close = pre_close_series.iloc[-1]
            post_open_series = hist.loc[hist.index > date]['Open']
            if post_open_series.empty:
                log(f"{ticker}: No post-event data for {date}. Will use next available trading day when it appears.", "WARN")
                continue
            post_open = post_open_series.iloc[0]
            move = ((post_open - pre_close) / pre_close) * 100
            results.append({
                "Ticker": ticker,
                "Event Date": date.strftime("%Y-%m-%d"),
                "Pre Close": pre_close,
                "Post Open": post_open,
                "Move %": round(move, 2),
            })
        except Exception as e:
            log(f"Event {row.get('Earnings Date', 'UNKNOWN')}: {e}", "WARN")

    # Always write a header, even if results is empty
    cols = ["Ticker", "Event Date", "Pre Close", "Post Open", "Move %"]
    out_df = pd.DataFrame(results, columns=cols)
    out_df.to_csv(OUTPUT_FILE, index=False)
    log(f"Saved historical analysis to: {OUTPUT_FILE}", "INFO")

if __name__ == "__main__":
    main()
