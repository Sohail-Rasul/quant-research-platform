# quant_fixes_v3 - cumulative: includes everything from v1 and v2
Copy this folder's contents over your project root (same paths). Then:

    pip install -r requirements.txt
    python -m pytest tests          # 19 tests, no database needed
    psql ... -f sql/003_create_index_membership.sql     # only when you have membership data

## What each change does
| File | Why |
|---|---|
| app/backtesting/backtest_engine.py | Cash can no longer go negative on rebalance (buys wait for all sells, capped by cash); delisted holdings are force-sold with a configurable loss; missing price days are valued at last price and logged; price prep 18s -> 1s |
| app/strategies/pipeline_strategy.py | New `universe_filters` stage that runs BEFORE scoring |
| app/factor_models/composite_factor_model.py | Z-scores computed only across investable stocks (was: every loaded ticker) |
| app/filters/top_liquidity_filter.py (new) | Point-in-time universe: K most-traded stocks on each date, no hindsight |
| app/filters/liquidity_filter.py (new) | Minimum average traded value |
| app/ranking/random_ranker.py (new) | Random-picks baseline |
| app/universe/point_in_time_universe.py (new) | Uses index membership history |
| sql/003_create_index_membership.sql, scripts/stocks_metadata/import_membership.py, app/data/loaders.py | Store/import/load membership history |
| app/backtesting/runner.py, strategy_config.py | Wire it all together; new config options |
| scripts/backtests/run_bias_checks.py (new) | Strategy vs random vs buy&hold vs Nifty 500 |
| app/update.py, app/backfill.py, scripts/stocks_prices/refresh_all_prices.py (new) | Stop stale adj_close after splits/dividends; reject NaN/0 prices |
| app/strategies/buy_and_hold.py, strategy_state.py | Buy&hold benchmark works; volume plumbing |
| dashboard/dashboard.py | New inputs, date crash fixed, data-quality warning |
| requirements.txt | Complete, UTF-8 |
| tests/ | 19 automated tests |
