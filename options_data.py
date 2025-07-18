# options_data.py (Now Includes Earnings Date Propagation)

import yfinance as yf
import pandas as pd
from datetime import datetime

EARNINGS_FILE = "earnings_next_week.csv"
OUTPUT_FILE = "earnings_options_data.csv"

def log(msg, level="INFO"):
    print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} [{level}] {msg}")

def load_earnings_df():
    return pd.read_csv(EARNINGS_FILE)[["Ticker", "Date"]]

def fetch_option_data(ticker):
    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period="1d")
        if hist.empty or 'Close' not in hist.columns:
            log(f"SKIPPED: {ticker} — No price data found.", "WARN")
            return None
        spot_price = hist['Close'].iloc[-1]

        expirations = stock.options
        if not expirations or len(expirations) == 0:
            log(f"SKIPPED: {ticker} — No options chain data.", "WARN")
            return None

        nearest_exp = expirations[0]  # Soonest expiry
        opt_chain = stock.option_chain(nearest_exp)
        calls = opt_chain.calls
        puts = opt_chain.puts

        if calls.empty or puts.empty:
            log(f"SKIPPED: {ticker} — Empty calls/puts.", "WARN")
            return None

        closest_strike = min(calls['strike'], key=lambda x: abs(x - spot_price))
        call_row = calls[calls['strike'] == closest_strike]
        put_row = puts[puts['strike'] == closest_strike]

        if call_row.empty or put_row.empty:
            log(f"SKIPPED: {ticker} — No ATM strike available.", "WARN")
            return None

        call_price = float(call_row['lastPrice'].iloc[0])
        put_price = float(put_row['lastPrice'].iloc[0])
        straddle_cost = call_price + put_price
        expected_move_pct = (straddle_cost / spot_price) * 100

        log(f"SUCCESS: {ticker} | Spot={spot_price}, Strike={closest_strike}, Straddle={straddle_cost:.2f}", "INFO")

        return {
            "Ticker": ticker,
            "Spot Price": round(spot_price, 2),
            "Strike": round(closest_strike, 2),
            "Call Price": round(call_price, 2),
            "Put Price": round(put_price, 2),
            "Straddle Cost": round(straddle_cost, 2),
            "Expected Move %": round(expected_move_pct, 2),
            "Expiration": nearest_exp
        }
    except Exception as e:
        log(f"ERROR: {ticker}: {e}", "ERROR")
        return None

def main():
    earnings_df = load_earnings_df()  # Loads Ticker + Date (earnings date)
    tickers = earnings_df['Ticker'].unique()
    results = []
    total = 0
    skipped = 0

    for ticker in tickers:
        log(f"Processing {ticker}...", "INFO")
        data = fetch_option_data(ticker)
        if data:
            # Attach earnings date (if available)
            edate = earnings_df[earnings_df['Ticker'] == ticker]['Date']
            data['Earnings Date'] = edate.values[0] if not edate.empty else None
            results.append(data)
            total += 1
        else:
            skipped += 1

    df = pd.DataFrame(results)
    # Move Earnings Date to first/second column if you want
    if not df.empty:
        cols = df.columns.tolist()
        cols.insert(1, cols.pop(cols.index("Earnings Date")))
        df = df[cols]
    df.to_csv(OUTPUT_FILE, index=False)
    log(f"\nSaved option data for {total} tickers (Skipped: {skipped}) to: {OUTPUT_FILE}", "INFO")

if __name__ == "__main__":
    main()
