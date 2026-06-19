import pandas as pd
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


def load_prices(
    tickers: list[str],
    start_date: str,
    end_date: str
) -> pd.DataFrame:
    
    cur = conn.cursor()

    cur.execute(""" 
                SELECT
                    p.date,
                    s.ticker,
                    p.open,
                    p.high,
                    p.low,
                    p.close,
                    p.adj_close,
                    p.volume
                FROM prices p JOIN stocks s 
                    ON p.stock_id = s.stock_id
                WHERE s.ticker = ANY(%s)
                    AND p.date BETWEEN %s AND %s
                ORDER BY p.date,s.ticker;
                """,
                (tickers,start_date,end_date,)
    )

    df = pd.DataFrame(
        cur.fetchall(),
        columns=[
            "date",
            "ticker",
            "open",
            "high",
            "low",
            "close",
            "adj_close",
            "volume"
        ]
    )

    cur.close()
    
    return df


