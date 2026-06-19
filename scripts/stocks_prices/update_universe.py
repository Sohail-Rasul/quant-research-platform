import psycopg

from dotenv import load_dotenv
import os

from app.update import update_prices
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
    ticker = result_row[0]
    if update_prices(conn,ticker):
        success_ctr+=1
        print(f"Updated: {ticker}")
    else:
        fail_ctr +=1
        print(f"Failed to update: {ticker}")
        failed_tickers.append(ticker)

print(f"Successful Updates: {success_ctr}")
print(f"Failed Updates: {fail_ctr}")
print(f"Failed Tickers: {failed_tickers}")

conn.commit()
conn.close()
