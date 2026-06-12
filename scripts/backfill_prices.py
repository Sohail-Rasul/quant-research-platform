#Import packages
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

#Load yfinance data
ticker = "RELIANCE.NS"
stock = yf.Ticker(ticker)

#SQL Statement - We need to get the stock_id of the ticker (stock) so we can get the data for that id since we identify using the stock_id
cur.execute(
    "SELECT stock_id FROM stocks WHERE ticker = %s;",
    (ticker,)
)

#Storing the respective stock_id
result = cur.fetchone()
if result is None:
    print("The Ticker does not exist. Exiting Now.")
    exit()
stock_id = result[0]

#Load History
history = stock.history(auto_adjust = False, period="max")
rows_to_insert = []

#Create tuple for each row
for date, row in history.iterrows():
    data = (stock_id,date.date(),row["Open"],row["High"],row["Low"],row["Close"],row["Adj Close"],row["Volume"])
    rows_to_insert.append(data)

#Bulk Insert
cur.executemany(
    """INSERT INTO prices(stock_id,date,open,high,low,close,adj_close,volume)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
        ON CONFLICT (stock_id,date) DO NOTHING;""",
        rows_to_insert
)

conn.commit()
cur.close()
conn.close()

