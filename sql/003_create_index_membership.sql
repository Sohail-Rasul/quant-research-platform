-- Point-in-time index membership (fixes the "universe = today's index" bias).
-- One row per membership spell. removed_date NULL = still a member today.
CREATE TABLE IF NOT EXISTS index_membership (
    stock_id     BIGINT NOT NULL REFERENCES stocks(stock_id),
    added_date   DATE   NOT NULL,
    removed_date DATE,
    PRIMARY KEY (stock_id, added_date),
    CHECK (removed_date IS NULL OR removed_date >= added_date)
);
