# earnings_scraper.py

import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import csv

def get_next_week_dates():
    today = datetime.now()
    return [(today + timedelta(days=i)).strftime('%Y-%m-%d') for i in range(7)]

def scrape_yahoo_earnings():
    base_url = "https://finance.yahoo.com/calendar/earnings?day="
    earnings = []

    for date_str in get_next_week_dates():
        url = base_url + date_str
        print(f"Scraping: {url}")
        try:
            res = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
            soup = BeautifulSoup(res.text, "html.parser")

            rows = soup.select("table tbody tr")
            for row in rows:
                cols = row.find_all("td")
                if len(cols) < 3:
                    continue
                ticker = cols[0].text.strip()
                name = cols[1].text.strip()
                time_of_day = cols[2].text.strip()
                earnings.append([date_str, ticker, name, time_of_day])
        except Exception as e:
            print(f"Error scraping {url}: {e}")

    return earnings

def save_to_csv(data, filename="earnings_next_week.csv"):
    with open(filename, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Date", "Ticker", "Company", "Time"])
        writer.writerows(data)

if __name__ == "__main__":
    earnings_data = scrape_yahoo_earnings()
    save_to_csv(earnings_data)
    print(f"Saved {len(earnings_data)} earnings rows.")
