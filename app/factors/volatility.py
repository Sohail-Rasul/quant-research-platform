def compute_volatility(conn,lookback_days,as_of_date = None):
    cur = conn.cursor()

    if as_of_date is None:
        cur.execute("SELECT MAX(date) FROM prices;")
        as_of_date = cur.fetchone()[0]

    window_size = lookback_days-1

    cur.execute(
        f"""WITH daily_returns AS (
            SELECT 
                p.stock_id,
                s.ticker,
                p.date,
                (
                    p.adj_close / LAG(p.adj_close,1) OVER(
                        PARTITION BY p.stock_id
                        ORDER BY p.date
                    ) -1
                ) AS daily_return
            FROM prices p JOIN stocks s
            ON p.stock_id = s.stock_id
        ),
        
        volatility_data AS (
            SELECT 
                ticker,
                date,
                STDDEV_SAMP(daily_return) OVER (
                    PARTITION BY stock_id
                    ORDER BY date
                    ROWS BETWEEN {window_size} PRECEDING AND CURRENT ROW
                ) AS volatility
            FROM daily_returns
        )

        SELECT 
            ticker,
            date,
            ROUND(volatility::numeric,6) AS volatility
        FROM volatility_data
        WHERE date = %s
            AND volatility IS NOT NULL
        ORDER BY volatility DESC;
        """
        ,(as_of_date,)
    )

    result = cur.fetchall()
    cur.close()
    return result