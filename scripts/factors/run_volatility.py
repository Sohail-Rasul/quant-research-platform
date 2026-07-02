import psycopg

from dotenv import load_dotenv
import os
load_dotenv()

from app.indicators.volatility import compute_volatility

#Create Connection and Cursor
conn = psycopg.connect(
    host = os.getenv("DB_HOST"),
    port=int(os.getenv("DB_PORT")),
    dbname=os.getenv("DB_NAME"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD")
)

lookback_days = int(input("Enter Lookback Days (252,126,63): "))
results = compute_volatility(conn,lookback_days)

print(f"Evaluation Date: {results[0][1]}")
print(f"Stocks Ranked: {len(results)}")

print(f"Top 10 Stocks:\n")
for row in results[:10]:
    print(row)

print(f"Bottom 10 Stocks:\n")
for row in results[-10:]:
    print(row)


conn.close()

