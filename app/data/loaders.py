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

def load_metadata(
    tickers: list[str]
) -> pd.DataFrame:

    cur = conn.cursor()

    cur.execute(
        """
        SELECT
            ticker, shares_outstanding
        FROM stocks
        WHERE ticker = ANY(%s);
        """,
        (tickers,)
    )

    df = pd.DataFrame(
        cur.fetchall(),
        columns=[
            "ticker","shares_outstanding"]
    )

    cur.close()

    df.set_index("ticker", inplace=True)

    return df


def load_all_tickers() -> list[str]:

    cur = conn.cursor()

    cur.execute("""
        SELECT ticker
        FROM stocks
        ORDER BY ticker;
    """)

    tickers = [row[0] for row in cur.fetchall()]

    cur.close()

    return tickers

def load_membership() -> pd.DataFrame:
    """Index membership history: ticker, added_date, removed_date (NULL = still a member)."""

    cur = conn.cursor()

    cur.execute("""
        SELECT s.ticker, m.added_date, m.removed_date
        FROM index_membership m JOIN stocks s ON s.stock_id = m.stock_id
        ORDER BY s.ticker, m.added_date;
    """)

    df = pd.DataFrame(
        cur.fetchall(),
        columns=["ticker", "added_date", "removed_date"]
    )

    cur.close()

    return df

if __name__ == "__main__":

    tickers = load_all_tickers()

    print(f"Total tickers: {len(tickers)}")
    print(tickers[:20])