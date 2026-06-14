import yfinance as yf

def backfill_prices(conn,ticker):
    #Create Cursor
    cur = conn.cursor()


    # SQL Statement - We need to get the stock_id of the ticker (stock) so we can get the data for that id since we identify using the stock_id
    cur.execute(
        "SELECT stock_id FROM stocks WHERE ticker = %s;",
        (ticker,)
    )

    result = cur.fetchone()
    if result is None:
        cur.close()
        return False
    stock_id = result[0]

    #Load Data
    stock = yf.Ticker(ticker)

    #Load History and validate
    history = stock.history(auto_adjust = False, period = "max")
    if history.empty:
        cur.close()
        return False

    #Storing the respective stock_id
    rows_to_insert = []
    invalid_rows=0
    #Create tuple for each row
    for date, row in history.iterrows():
        #For negative adj close values (Skipping)
        open_price = row["Open"]
        high_price = row["High"]
        low_price = row["Low"]
        close_price = row["Close"]
        adj_close = row["Adj Close"]
        volume = row["Volume"]

        if (
            adj_close < 0 or
            volume < 0 or
            low_price > high_price or
            open_price < low_price or
            open_price > high_price or
            close_price < low_price or
            close_price > high_price
        ):
            invalid_rows+=1
            continue    
        data = (stock_id,date.date(),row["Open"],row["High"],row["Low"],row["Close"],row["Adj Close"],row["Volume"])
        rows_to_insert.append(data)

    if invalid_rows > 0:
        print(f"{ticker}: skipped {invalid_rows} invalid rows")
    
    #Bulk Insert
    cur.executemany(
        """INSERT INTO prices(stock_id,date,open,high,low,close,adj_close,volume)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
            ON CONFLICT (stock_id,date) DO NOTHING;""",
            rows_to_insert
    )
    
    cur.close()

    return True
    

