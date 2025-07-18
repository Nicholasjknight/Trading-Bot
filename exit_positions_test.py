# exit_positions_test.py

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

HOLD_THRESHOLD_HOURS = 18
TAKE_PROFIT_THRESHOLD = 0.15  # +15%
STOP_LOSS_THRESHOLD = -0.10   # -10%

def get_positions():
    r = requests.get(f"{BASE_URL}/v2/positions", headers=HEADERS)
    r.raise_for_status()
    return r.json()

def get_order_times():
    r = requests.get(f"{BASE_URL}/v2/orders?status=all&limit=100", headers=HEADERS)
    r.raise_for_status()
    orders = r.json()
    submitted = {}
    for order in orders:
        if order["symbol"] not in submitted and order["side"] == "buy" and order["submitted_at"]:
            submitted[order["symbol"]] = order["submitted_at"]
    return submitted

def main():
    positions = get_positions()
    if not positions:
        print("✅ No open positions.")
        return

    submitted_times = get_order_times()
    now = datetime.now(timezone.utc)

    for pos in positions:
        symbol = pos["symbol"]
        qty = float(pos["qty"])
        unrealized_plpc = float(pos["unrealized_plpc"])  # percent as decimal

        submitted_at_str = submitted_times.get(symbol)
        held_duration_ok = False

        if submitted_at_str:
            submitted_at = datetime.fromisoformat(submitted_at_str.replace("Z", "+00:00"))
            held_for = now - submitted_at
            held_duration_ok = held_for > timedelta(hours=HOLD_THRESHOLD_HOURS)
        else:
            print(f"[WARN] No order time found for {symbol}, skipping time rule.")

        print(f"⏳ {symbol}: Qty={qty}, P/L={unrealized_plpc:.2%}")

        if unrealized_plpc >= TAKE_PROFIT_THRESHOLD:
            print(f"[DRY RUN] {symbol} would be closed for TAKE-PROFIT at {unrealized_plpc:.2%}")
        elif unrealized_plpc <= STOP_LOSS_THRESHOLD:
            print(f"[DRY RUN] {symbol} would be closed for STOP-LOSS at {unrealized_plpc:.2%}")
        elif held_duration_ok:
            print(f"[DRY RUN] {symbol} would be closed for TIME (> {HOLD_THRESHOLD_HOURS}h)")
        else:
            print(f"[HOLDING] {symbol} still within conditions.")

if __name__ == "__main__":
    main()
