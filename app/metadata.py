import yfinance as yf

def insert_stock_metadata(conn,ticker):
    cur = conn.cursor()
    stock = yf.Ticker(ticker)
    info = stock.info
    company_name = info.get("longName")

    #Check if metadata is valid
    if company_name is None:
        cur.close()
        return False

    #Load Data into Table
    cur.execute(
        "INSERT INTO stocks (ticker,company_name) VALUES (%s, %s) ON CONFLICT (ticker) DO NOTHING;",
        (ticker,company_name)
    )

    cur.close()
    return True


