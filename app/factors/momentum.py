def compute_momentum(conn, lookback_days ,as_of_date=None):

    cur = conn.cursor()

    if as_of_date is None:
        cur.execute("SELECT MAX(date) from prices;")
        as_of_date = cur.fetchone()[0]

    cur.execute(
        """WITH momentum_data AS (
            SELECT
                p.stock_id,
                s.ticker,
                p.date,
                p.adj_close,
                LAG(p.adj_close, %s) OVER (
                    PARTITION BY p.stock_id
                    ORDER BY p.date
                ) AS adj_close_old
            FROM prices p
            JOIN stocks s
                ON p.stock_id = s.stock_id
        )
        SELECT
            ticker,
            date,
            ROUND(
                (adj_close / adj_close_old - 1)::numeric,
                6
            ) AS momentum
        FROM momentum_data
        WHERE date = %s
            AND adj_close_old IS NOT NULL
        ORDER BY momentum DESC;""",
        (lookback_days,as_of_date,)
    )

    result = cur.fetchall()
    cur.close()
    return result

