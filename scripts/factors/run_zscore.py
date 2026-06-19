from app.factors.momentum import compute_momentum
from app.factors.size import compute_size
from app.factors.volatility import compute_volatility
from app.factors.zscore import compute_zscore

import psycopg

from dotenv import load_dotenv
import os
load_dotenv()


#Create Connection and Cursor
conn = psycopg.connect(
    host = os.getenv("DB_HOST"),
    port=int(os.getenv("DB_PORT")),
    dbname=os.getenv("DB_NAME"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD")
)

# 12m = 252, 6m = 126, 3m= 63
lookback_days = int(input("Enter number of days to lookback (For Momentum and Volatility) [252,126,63]: "))

momentum = compute_momentum(conn,lookback_days)
volatility = compute_volatility(conn,lookback_days)
size = compute_size(conn)

momentum_z = compute_zscore(momentum)
volatility_z = compute_zscore(volatility)
size_z = compute_zscore(size)


print(f"Top 10 Z-Scores for Momentum: ")
print(f"{momentum_z[:10]}")
print(f"Bottom 10 Z-Scores for Momentum: ")
print(f"{momentum_z[-10:]}")

print(f"Top 10 Z-Scores for Volatility: ")
print(f"{volatility_z[:10]}")
print(f"Bottom 10 Z-Scores for Volatility: ")
print(f"{volatility_z[-10:]}")

print(f"Top 10 Z-Scores for Size: ")
print(f"{size_z[:10]}")
print(f"Bottom 10 Z-Scores for Size: ")
print(f"{size_z[-10:]}")

conn.close()