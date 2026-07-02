def compute_size(conn, as_of_date = None):
    cur = conn.cursor()

    if as_of_date is None:
        cur.execute("SELECT MAX(date) FROM prices;")
        result = cur.fetchone()[0]
        as_of_date = result

    cur.execute(
        """SELECT 
            s.ticker,
            p.date,
            (
                LN(adj_close * s.shares_outstanding)
            ) AS ln_market_cap
        FROM prices p JOIN stocks s
        ON p.stock_id = s.stock_id
        WHERE s.shares_outstanding IS NOT NULL
        AND p.date = %s
        ORDER BY ln_market_cap DESC;
        """,
        (as_of_date,)
    )

    result = cur.fetchall()
    cur.close()

    return result