import psycopg

from dotenv import load_dotenv
import os

from app.backfill import backfill_prices
load_dotenv()

#Create Connection
conn = psycopg.connect(
    host = os.getenv("DB_HOST"),
    port=int(os.getenv("DB_PORT")),
    dbname=os.getenv("DB_NAME"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD")
)

cur = conn.cursor()

cur.execute(
    "SELECT ticker FROM stocks;"
)

result = cur.fetchall()
cur.close()

success_ctr=0
fail_ctr=0
failed_tickers = []
for result_row in result:
    ticker = result_row[0] #Because the result we get is in the form => ('ticker_name.NS',)
    print(f"[{success_ctr + fail_ctr + 1}/{len(result)}] Processing {ticker}...")
    if backfill_prices(conn,ticker):
        success_ctr+=1
    else:
        fail_ctr+=1
        failed_tickers.append(ticker)


conn.commit()
conn.close()

print(f"Successful Backfills: {success_ctr}")
print(f"Failed Backfills: {fail_ctr}")
print(f"Failed Tickers: {failed_tickers}")