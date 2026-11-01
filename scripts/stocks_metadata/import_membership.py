"""
Import index membership history from a CSV you assemble (NSE index files,
rebalance announcements, or a vendor export).

CSV columns (header required):  ticker, added_date, removed_date
  - ticker        e.g. RELIANCE.NS   (must already exist in `stocks`)
  - added_date    YYYY-MM-DD  (earliest date it was in the index)
  - removed_date  YYYY-MM-DD, or empty if still a member

Usage:  python scripts/stocks_metadata/import_membership.py membership.csv
Re-running is safe: existing (stock, added_date) rows are updated.
"""
import os
import sys

import pandas as pd
import psycopg
from dotenv import load_dotenv

load_dotenv()

if len(sys.argv) != 2:
    sys.exit(__doc__)

df = pd.read_csv(sys.argv[1])
missing_cols = {"ticker", "added_date", "removed_date"} - set(df.columns)
if missing_cols:
    sys.exit(f"CSV is missing columns: {missing_cols}")

df["added_date"] = pd.to_datetime(df["added_date"]).dt.date
df["removed_date"] = pd.to_datetime(df["removed_date"]).dt.date

conn = psycopg.connect(
    host=os.getenv("DB_HOST"), port=int(os.getenv("DB_PORT")),
    dbname=os.getenv("DB_NAME"), user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
)
cur = conn.cursor()
cur.execute("SELECT ticker, stock_id FROM stocks;")
stock_ids = dict(cur.fetchall())

inserted, unknown = 0, set()
for row in df.itertuples(index=False):
    stock_id = stock_ids.get(row.ticker)
    if stock_id is None:
        unknown.add(row.ticker)      # no row in `stocks` -> add the stock + prices first
        continue
    removed = None if pd.isna(row.removed_date) else row.removed_date
    cur.execute(
        """INSERT INTO index_membership (stock_id, added_date, removed_date)
           VALUES (%s, %s, %s)
           ON CONFLICT (stock_id, added_date) DO UPDATE SET removed_date = EXCLUDED.removed_date;""",
        (stock_id, row.added_date, removed),
    )
    inserted += 1

conn.commit()
conn.close()
print(f"Imported/updated {inserted} membership rows.")
if unknown:
    print(f"{len(unknown)} tickers are not in `stocks` and were skipped: {sorted(unknown)[:20]}")
