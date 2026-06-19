import yfinance as yf

def update_prices(conn,ticker):
    stock = yf.Ticker(ticker)

    cur = conn.cursor()

    cur.execute(
        "SELECT stock_id FROM stocks WHERE ticker = %s;",
        (ticker,)
    )

    result = cur.fetchone()
    if result is None:
        print("The Ticker does not exist. Exiting Now.")
        return False
    stock_id = result[0]

    cur.execute(
    "SELECT MAX(date) FROM prices WHERE stock_id=%s;",
    (stock_id,)
    )
    result=cur.fetchone()
    if result[0] is None:
        print("No backdata exists, run backfill_prices first!")
        return False
    last_date = result[0]
    history = stock.history(start=last_date,auto_adjust = False)

    #Create tuple for each row
    rows_to_insert = []
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

    cur.close()
    return True