"""
ONE-TIME CLEANUP: re-download full history for every stock and OVERWRITE stored rows.
Run this once if the SQL check shows split-like jumps in adj_close (see chat).
Usage: python scripts/stocks_prices/refresh_all_prices.py
"""
import os

import psycopg
from dotenv import load_dotenv

from app.backfill import backfill_prices

load_dotenv()

conn = psycopg.connect(
    host=os.getenv("DB_HOST"), port=int(os.getenv("DB_PORT")),
    dbname=os.getenv("DB_NAME"), user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
)

cur = conn.cursor()
cur.execute("SELECT ticker FROM stocks ORDER BY ticker;")
tickers = [r[0] for r in cur.fetchall()]
cur.close()

failed = []
for i, ticker in enumerate(tickers, 1):
    print(f"[{i}/{len(tickers)}] {ticker}")
    try:
        ok = backfill_prices(conn, ticker, overwrite=True)
        conn.commit()                      # commit per ticker so progress is kept
        if not ok:
            failed.append(ticker)
    except Exception as e:
        conn.rollback()
        failed.append(ticker)
        print(f"   failed: {e}")

conn.close()
print(f"Done. {len(tickers) - len(failed)} refreshed, {len(failed)} failed: {failed}")
