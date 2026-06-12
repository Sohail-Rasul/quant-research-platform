import yfinance as yf
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

cur = conn.cursor()

#yfinance
ticker = "RELIANCE.NS"
stock=yf.Ticker(ticker)

info = stock.info
company_name = info.get("longName")

print(company_name)

#SQL Statement
cur.execute(
    "INSERT INTO stocks(ticker,company_name) VALUES (%s,%s);",
    (ticker,company_name)
)

#Commit and Close
conn.commit()
cur.close()
conn.close()

