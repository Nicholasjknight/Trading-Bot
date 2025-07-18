# broker_api.py

import pandas as pd
import requests
import time
import os
from datetime import datetime, timezone

# === CONFIG ===
API_KEY = "PK21XRY4HEJ7KYUZOFZY"
SECRET_KEY = "X07FLgrwJP0aQyKgC79dCQM78DgLD5xXdFRTtLcB"
BASE_URL = "https://paper-api.alpaca.markets"

HEADERS = {
    "APCA-API-KEY-ID": API_KEY,
    "APCA-API-SECRET-KEY": SECRET_KEY
}

SIGNALS_FILE = "filtered_signals.csv"
TRADE_LOG_FILE = "trade_log.csv"
CAPITAL_PER_TRADE = 200  # dollars

def place_order(symbol, qty, side):
    data = {
        "symbol": symbol,
        "qty": qty,
        "side": side,
        "type": "market",
        "time_in_force": "gtc"
    }
    print(f"[DEBUG] Placing Order: {data}")
    r = requests.post(f"{BASE_URL}/v2/orders", headers=HEADERS, json=data)
    
    if r.status_code != 200:
        print(f"[ERROR] Order request failed for {symbol}: {r.status_code} {r.text}")
        return None

    order_id = r.json().get('id')
    if not order_id:
        print(f"[ERROR] No order ID returned for {symbol}.")
        return None

    # Polling the order status for fill price
    timeout = 15  # seconds
    poll_interval = 1  # second
    elapsed_time = 0
    
    while elapsed_time < timeout:
        status_response = requests.get(f"{BASE_URL}/v2/orders/{order_id}", headers=HEADERS)
        if status_response.status_code == 200:
            order_info = status_response.json()
            filled_avg_price = order_info.get("filled_avg_price")
            if filled_avg_price:
                print(f"[INFO] {symbol} filled at ${filled_avg_price}")
                return order_info
            else:
                print(f"[WAITING] {symbol} order not filled yet, retrying...")
        else:
            print(f"[ERROR] Order status check failed for {symbol}: {status_response.status_code} {status_response.text}")
            return None

        time.sleep(poll_interval)
        elapsed_time += poll_interval

    print(f"[TIMEOUT] Order fill price unavailable after {timeout} seconds for {symbol}")
    return None

def run_trades():
    try:
        df = pd.read_csv(SIGNALS_FILE)
    except Exception as e:
        print(f"[ERROR] Reading signals file: {e}")
        return

    if df.empty:
        print("[INFO] No signals to trade.")
        return

    logs = []
    for _, row in df.iterrows():
        symbol = row['Ticker']
        cost = float(row['Straddle Cost'])
        expiration = row['Expiration']
        strike = float(row['Strike'])
        play = row['Play'].upper()

        qty = int(CAPITAL_PER_TRADE // cost)
        if qty < 1:
            print(f"[SKIP] {symbol}: straddle too expensive (${cost})")
            continue

        side = "buy" if "BUY" in play else "sell"
        print(f"📈 Placing order for {symbol}: {qty}x straddle ({side})")

        result = place_order(symbol, qty, side)
        if result is None:
            continue

        time.sleep(1)  # brief pause between orders

        fill_price = result.get("filled_avg_price")
        if fill_price is None:
            print(f"[WARN] No fill price returned for {symbol}. Skipping this trade.")
            continue

        try:
            fill_price = float(fill_price)
        except Exception as e:
            print(f"[ERROR] Invalid fill price for {symbol}: {fill_price}. Skipping this trade. ({e})")
            continue

        log_entry = {
            "Ticker": symbol,
            "Play": play,
            "Quantity": qty,
            "Strike": strike,
            "Straddle Cost": cost,
            "Expiration": expiration,
            "Order ID": result.get("id", "N/A"),
            "Fill Price": fill_price,
            "Timestamp": datetime.now(timezone.utc).isoformat()
        }

        logs.append(log_entry)

    if logs:
        df_out = pd.DataFrame(logs)
        if not os.path.exists(TRADE_LOG_FILE):
            df_out.to_csv(TRADE_LOG_FILE, index=False)
        else:
            df_out.to_csv(TRADE_LOG_FILE, mode='a', index=False, header=False)
        print(f"[✅] Logged {len(logs)} trades to {TRADE_LOG_FILE}")
    else:
        print("[INFO] No trades placed.")

if __name__ == "__main__":
    run_trades()
