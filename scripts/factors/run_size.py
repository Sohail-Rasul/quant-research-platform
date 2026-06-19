import psycopg

from dotenv import load_dotenv
import os
load_dotenv()

from app.factors.size import compute_size

#Create Connection and Cursor
conn = psycopg.connect(
    host = os.getenv("DB_HOST"),
    port=int(os.getenv("DB_PORT")),
    dbname=os.getenv("DB_NAME"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD")
)


results = compute_size(conn)

print(f"Evaluation Date: {results[0][1]}")
print(f"Stocks Ranked: {len(results)}")

print(f"Top 10 Stocks:\n")
for row in results[:10]:
    print(row)

print(f"Bottom 10 Stocks:\n")
for row in results[-10:]:
    print(row)


conn.close()

