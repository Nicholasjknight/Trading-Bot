# exit_positions.py

import requests
from datetime import datetime, timezone, timedelta

# === CONFIG ===
API_KEY = "PK21XRY4HEJ7KYUZOFZY"
SECRET_KEY = "X07FLgrwJP0aQyKgC79dCQM78DgLD5xXdFRTtLcB"
BASE_URL = "https://paper-api.alpaca.markets"

HEADERS = {
    "APCA-API-KEY-ID": API_KEY,
    "APCA-API-SECRET-KEY": SECRET_KEY
}

# === EXIT RULES ===
TAKE_PROFIT_THRESHOLD = 0.15  # +15%
STOP_LOSS_THRESHOLD = -0.10   # -10%
MAX_HOLD_DAYS = 3             # 3 calendar days

def get_positions():
    r = requests.get(f"{BASE_URL}/v2/positions", headers=HEADERS)
    r.raise_for_status()
    return r.json()

def get_order_times():
    """
    Returns a dict: { 'AAPL': datetime object (UTC) }
    """
    r = requests.get(f"{BASE_URL}/v2/orders?status=all&limit=100", headers=HEADERS)
    r.raise_for_status()
    orders = r.json()

    submitted = {}
    for order in orders:
        if order["side"] != "buy":
            continue
        symbol = order["symbol"]
        if symbol in submitted:
            continue
        ts = order.get("submitted_at")
        if ts:
            submitted[symbol] = datetime.fromisoformat(ts.replace("Z", "+00:00"))
    return submitted

def close_position(symbol):
    r = requests.delete(f"{BASE_URL}/v2/positions/{symbol}", headers=HEADERS)
    if r.status_code == 200:
        print(f"✔️ Closed position: {symbol}")
    else:
        print(f"[ERROR] Failed to close {symbol}: {r.status_code} - {r.text}")

def main():
    print("🔍 Checking open positions...\n")
    try:
        positions = get_positions()
        if not positions:
            print("✅ No open positions.")
            return
    except Exception as e:
        print(f"[ERROR] Could not fetch positions: {e}")
        return

    order_times = get_order_times()
    now = datetime.now(timezone.utc)

    for pos in positions:
        symbol = pos["symbol"]
        qty = float(pos["qty"])
        unrealized_plpc = float(pos["unrealized_plpc"])

        submitted_at = order_times.get(symbol)
        if submitted_at:
            days_held = (now - submitted_at).days
        else:
            print(f"[WARN] No order time for {symbol} — assuming held 1 day")
            days_held = 1

        print(f"⏳ {symbol}: Qty={qty}, P/L={unrealized_plpc:.2%}, Held={days_held}d")

        if unrealized_plpc >= TAKE_PROFIT_THRESHOLD:
            print(f"→ Taking profit on {symbol}")
            close_position(symbol)
        elif unrealized_plpc <= STOP_LOSS_THRESHOLD:
            print(f"→ Stopping loss on {symbol}")
            close_position(symbol)
        elif days_held > MAX_HOLD_DAYS:
            print(f"→ Max holding period exceeded for {symbol}")
            close_position(symbol)
        else:
            print(f"[HOLDING] {symbol} still within conditions.\n")

if __name__ == "__main__":
    main()
