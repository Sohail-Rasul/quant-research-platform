#Imports
import pandas as pd
import psycopg

from dotenv import load_dotenv
import os

from app.metadata import insert_stock_metadata
load_dotenv()

#Create Connection
conn = psycopg.connect(
    host = os.getenv("DB_HOST"),
    port=int(os.getenv("DB_PORT")),
    dbname=os.getenv("DB_NAME"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD")
)

#Read CSV
df = pd.read_csv("data/NSE_500.csv")
symbols = df["Symbol"]

#Convert to proper format and call function to insert data
success_ctr=0
fail_ctr=0
failed_tickers = []
for symbol in symbols:
    ticker = symbol+".NS"
    print(f"Processing {ticker}....\n")
    if insert_stock_metadata(conn,ticker):
        success_ctr+=1
    else:
        fail_ctr+=1
        failed_tickers.append(ticker)


conn.commit()
conn.close()

print(f"Successful Inserts: {success_ctr}")
print(f"Failed Inserts: {fail_ctr}")
print(f"Failed Tickers: \n{failed_tickers}")







