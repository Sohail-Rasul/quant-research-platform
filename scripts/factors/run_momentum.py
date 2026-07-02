import psycopg

from dotenv import load_dotenv
import os
load_dotenv()

from app.indicators.momentum import compute_momentum

#Create Connection and Cursor
conn = psycopg.connect(
    host = os.getenv("DB_HOST"),
    port=int(os.getenv("DB_PORT")),
    dbname=os.getenv("DB_NAME"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD")
)
# 12m = 252, 6m = 126, 3m= 63
lookback_days = int(input("Enter number of days to lookback (252,126,63): "))
results = compute_momentum(conn,lookback_days)

print(f"Evaluation Date: {results[0][1]}")
print(f"Stocks Ranked: {len(results)}")

print(f"Top 10 Stocks:\n")
for row in results[:10]:
    print(row)

print(f"Bottom 10 Stocks:\n")
for row in results[-10:]:
    print(row)


conn.close()

