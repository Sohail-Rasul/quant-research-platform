import yfinance as yf

def insert_stock_metadata(conn,ticker):
    cur = conn.cursor()
    stock = yf.Ticker(ticker)
    info = stock.info
    company_name = info.get("longName")
    shares_outstanding = info.get("sharesOutstanding")

    #Check if metadata is valid
    if company_name is None:
        cur.close()
        return False

    #Load Data into Table
    cur.execute(
        "INSERT INTO stocks (ticker,company_name,shares_outstanding) VALUES (%s, %s,%s) ON CONFLICT (ticker) DO UPDATE SET shares_outstanding = EXCLUDED.shares_outstanding, company_name = EXCLUDED.company_name;",
        (ticker,company_name,shares_outstanding)
    )

    cur.close()
    return True


