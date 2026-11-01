# Quantitative Research Platform

A modular, incrementally-built research and backtesting framework for equity strategies, developed as a learning project spanning data engineering, quantitative factor research, and software architecture.

> **Educational project.** This is a personal learning platform, not a production trading system. Where functionality is incomplete or simplified, this document says so explicitly.

> **Status (November 2026).** The backtest engine is tested and its mechanics are verified. The *results* are not yet trustworthy as return estimates: the stock universe is survivor-biased (see [Backtest Integrity Findings](#12-backtest-integrity-findings) and [Known Limitations](#13-known-limitations)). Treat every CAGR this platform currently reports as an upper bound.

---

## 1. Project Overview

This repository is a from-scratch quantitative research platform built to answer one question honestly: *can I design, build, and defend every layer of a systematic equity strategy pipeline myself?* It combines:

- A **PostgreSQL-backed historical data layer** for prices and stock metadata.
- A set of **factor research scripts** (momentum, volatility, size, cross-sectional z-scores, composite scoring) written directly against SQL.
- A **class-based strategy framework** (`StrategyState`, `PipelineStrategy`, and a family of abstract base classes) that turns those ad-hoc factors into a reusable, swappable pipeline.
- A **backtesting engine** that simulates periodically rebalanced portfolios with transaction costs.
- **Analytics and visualization** modules for total return, CAGR, volatility, Sharpe ratio, and drawdown.
- A **Streamlit dashboard** that runs the same backtest as the terminal scripts, with configurable strategy, cost, liquidity, and bias-control settings.
- An **automated test suite** (19 tests, no database required) and a **bias-check script** that benchmarks the strategy against random picks, buy-and-hold, and the Nifty 500.

The project was built module by module (M1–M4, plus a dashboard and integrity phase, described below), and the architecture reflects that history — earlier modules are simpler and more direct; later modules are more abstract because direct experience with the earlier modules exposed their limitations.

## 2. Motivation

The motivation was not "build a backtester" as an end in itself. It was to force myself through the full arc of a quant research workflow: ingesting real data, computing factors correctly (including subtleties like sample vs. population standard deviation), simulating a strategy against realistic constraints (transaction costs, integer share counts, periodic rebalancing), and measuring performance with the same metrics used in industry (Sharpe, CAGR, max drawdown). Doing this myself, end to end, was the point and not outsourcing any layer to an existing library like `zipline` or `backtrader`.

When early runs reported CAGRs between 30% and 110%, the project took a second, equally important direction: finding out whether those numbers could be trusted, and why not.

## 3. Problem Statement

- How do you evaluate different signals (momentum, volatility, size) without duplicating logic every time?
- How do you compose several signals into one score without hardcoding assumptions about which signals are involved?
- How do you simulate a portfolio without look-ahead bias, while still handling rebalancing, warmup periods, and transaction costs realistically?
- How do you keep the codebase extensible as new indicators, filters, rankers, and weighting schemes are added, without rewriting the backtest engine every time?
- How do you tell whether a very high backtested return comes from the strategy, or from the data and the time period?

This project's later modules exist specifically to solve these problems.

## 4. Goals

- Build a working, correct backtesting engine. *(Done and tested.)*
- Learn the mathematics behind each component well enough to derive it on a whiteboard.
- Design an architecture where new indicators, filters, rankers, and weighting schemes can be added without modifying existing code (open/closed principle). *(Done for filters, rankers, weighting, and universes.)*
- Keep the system honest: no feature is claimed unless it is implemented and testable.
- Produce results that are scientifically defensible. *(In progress. Blocked on data, not code.)*

## 5. Technology Stack

| Layer | Technology |
|---|---|
| Data storage | PostgreSQL |
| Data access | `psycopg` (raw SQL, no ORM) |
| Data ingestion | `yfinance` |
| Numerical computing | `pandas`, `numpy` |
| Visualization | `matplotlib`, Streamlit |
| Testing | `pytest` |
| Configuration | `python-dotenv` (`.env` for DB credentials) |
| Language | Python 3.11 |

There is no task queue and no ORM — this is a research codebase run via standalone scripts and a local Streamlit dashboard, not a deployed service.

## 6. High-Level Architecture

The platform has two distinct implementation styles that coexist in the repo, reflecting its evolution:

1. **SQL-first factor scripts** (`scripts/factors/`, `app/indicators/momentum.py`, `volatility.py`, `size.py`, `zscore.py`, `composite_score.py`) — these compute factors directly via SQL window functions (`LAG`, `STDDEV_SAMP`) against the `prices`/`stocks` tables, for a single as-of date. This was the M2 research style.
2. **Pandas-based pipeline framework** (`app/strategies/`, `app/indicators/*_indicator.py`, `app/factor_models/`, `app/filters/`, `app/ranking/`, `app/weighting/`) — this is the M4 framework used by the actual backtesting engine. It operates on a `StrategyState` object carrying historical price (and volume) DataFrames, and every stage (universe filters → indicators → factor model → filters → ranker → weighter) mutates or reads that shared state.

> **Design Decision:** The SQL scripts and the pipeline framework are *not* wired together. The SQL scripts were the original research tools for validating factor logic against the database; the pipeline framework reimplements the same ideas (momentum, volatility, size, z-score, composite score) in pandas so they can run inside a backtest loop without a live DB round-trip per rebalance. This is an intentional, honest architectural seam, not an oversight — the SQL factor scripts are a separate, standalone research tool rather than a component the backtester calls into.

```
                 ┌───────────────────────────┐
                 │        PostgreSQL          │
                 │ stocks / prices /          │
                 │ index_membership (optional)│
                 └─────────────┬─────────────┘
                               │ load_prices(), load_metadata()
                               ▼
                    ┌─────────────────────┐
                    │   prices_df (pandas) │
                    └──────────┬──────────┘
                               ▼
                    ┌─────────────────────┐
                    │   BacktestEngine     │
                    │  (rebalance loop)    │
                    └──────────┬──────────┘
                               │ builds StrategyState per rebalance date
                               ▼
        ┌───────────────────────────────────────────────┐
        │                PipelineStrategy                │
        │  Universe → Universe filters → Indicators →     │
        │  Factor Model → Filters → Ranker → Weighting    │
        └──────────────────────┬──────────────────────────┘
                               │ weights: dict[ticker, float]
                               ▼
                    ┌─────────────────────┐
                    │      Portfolio       │
                    │  cash + positions    │
                    └──────────┬──────────┘
                               ▼
                    ┌─────────────────────┐
                    │   Equity Curve (df)  │
                    └──────────┬──────────┘
                               ▼
                 ┌───────────────────────────┐
                 │ Analytics + Visualization  │
                 │ + Streamlit dashboard      │
                 └───────────────────────────┘
```

**Execution convention.** A signal is generated from the *previous* trading day's close and the trade executes at the *next* trading day's close (a market-on-close style order). The strategy never sees the price it trades at when it decides.

## 7. Folder Structure

```
quant-research-platform/
├── app/
│   ├── backtesting/        # BacktestEngine, Portfolio, Position, StrategyConfig, runner
│   ├── strategies/         # StrategyState, PipelineStrategy, BuyAndHoldStrategy
│   ├── universe/           # BaseUniverse, UserUniverse, PointInTimeUniverse
│   ├── indicators/         # Class-based indicators + legacy SQL factor scripts
│   ├── factor_models/      # BaseFactorModel, CompositeFactorModel
│   ├── filters/            # BaseFilter, NoFilter, ThresholdFilter, LiquidityFilter, TopLiquidityFilter
│   ├── ranking/            # BaseRanker, TopNRanker, NoRanker, RandomRanker
│   ├── weighting/          # BaseWeighting, EqualWeight, InverseVolatilityWeight
│   ├── analytics/          # performance.py, reports.py
│   ├── visualization/      # plots.py (matplotlib)
│   ├── data/               # loaders.py (psycopg-based price, metadata, membership loading)
│   ├── utils/              # statistics.py (z-score helper)
│   └── update.py / backfill.py / metadata.py   # yfinance ingestion
├── dashboard/              # dashboard.py (Streamlit front end for run_backtest)
├── scripts/
│   ├── stocks_prices/      # backfill/update/refresh price scripts
│   ├── stocks_metadata/    # universe, metadata, and index-membership ingestion
│   ├── factors/            # SQL-based factor research scripts (M2)
│   └── backtests/          # run_pipeline.py, run_buy_and_hold.py, run_bias_checks.py
├── sql/                    # 001_create_tables, 002_add_shares_outstanding, 003_create_index_membership
├── data/                   # NSE_500.csv (universe reference file)
├── tests/                  # 19 automated tests (synthetic data, no database needed)
└── docs/                   # backtest-integrity-research.md
```

## 8. Module Overview

| Module | Focus | Key Deliverable |
|---|---|---|
| **M1** | Historical Data Platform | PostgreSQL schema (`stocks`, `prices`), ingestion via `yfinance` (`backfill.py`, `update.py`, `metadata.py`), data validation (OHLC sanity checks, NaN and non-positive price rejection) |
| **M2** | Factor Research | SQL-based momentum, volatility, size, and z-score computations as standalone research scripts |
| **M3** | Backtesting Engine | `Portfolio`, `Position`, buy/sell execution, periodic rebalancing, transaction costs, equity curve, performance analytics |
| **M4** | Strategy Framework | `StrategyState`, `PipelineStrategy`, and abstract base classes (`BaseIndicator`, `BaseFactorModel`, `BaseFilter`, `BaseRanker`, `BaseWeighting`) generalizing the whole thing into a composable pipeline |
| **Dashboard & Integrity** | Trust in results | Streamlit dashboard, liquidity and point-in-time universe controls, delisting handling, test suite, bias-check script, research write-up |


## 9. Getting Started

**1. Install**

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows; use source .venv/bin/activate elsewhere
pip install -r requirements.txt
pip install pytest
```

**2. Configure the database.** Create a PostgreSQL database and a `.env` file in the project root:

```
DB_HOST=localhost
DB_PORT=5432
DB_NAME=...
DB_USER=...
DB_PASSWORD=...
```

Then apply the schema: `sql/001_create_tables.sql`, `sql/002_add_shares_outstanding.sql`, and (only if you will use index-membership history) `sql/003_create_index_membership.sql`.

**3. Load data** (run from the project root):

```bash
python -m scripts.stocks_metadata.ingest_universe      # stocks + metadata from data/NSE_500.csv
python -m scripts.stocks_prices.backfill_universe      # full price history for every stock
python -m scripts.stocks_prices.update_universe        # later: incremental updates
```

**4. Verify, then run**

```bash
python -m pytest tests                    # expect: 19 passed (no database needed)
streamlit run dashboard/dashboard.py      # interactive backtests
python -m scripts.backtests.run_bias_checks   # strategy vs random vs buy-and-hold vs Nifty 500
```

## 10. Current Features

- **Data ingestion**: backfill full price history and incrementally update it via `yfinance`, with row-level validation (impossible highs/lows/opens/closes, NaN, and non-positive prices are skipped, not silently inserted). `update_prices` re-downloads and overwrites a stock's history when a split or dividend has occurred since the last update, because `yfinance` re-scales past adjusted prices. `refresh_all_prices.py` rebuilds all stored prices once.
- **Universe definition**: `UserUniverse` (explicit ticker list), and `PointInTimeUniverse`, which uses an `index_membership` table so each date only sees stocks that were members then. The second needs data that is not yet loaded.
- **Indicators**: class-based `MomentumIndicator`, `VolatilityIndicator` (annualized standard deviation of daily returns, sample statistics, `sqrt(252)` scaling), and `SizeIndicator` (log of shares outstanding × price).
- **Composite factor model**: `CompositeFactorModel` combines multiple z-scored indicators into a single weighted composite score. Z-scores are computed across the investable stocks on each date.
- **Universe filters** (run before scoring): `LiquidityFilter` (minimum average daily traded value) and `TopLiquidityFilter` (keep the K most-traded stocks on each date, using only data available then).
- **Filters**: `NoFilter` (pass-through) and `ThresholdFilter` (keep/drop tickers based on an operator + threshold against any indicator).
- **Ranking**: `NoRanker`, `TopNRanker` (select the top/bottom N tickers by any indicator), and `RandomRanker` (a random-picks baseline).
- **Weighting**: `EqualWeight` and `InverseVolatilityWeight`.
- **Backtesting**: monthly or quarterly rebalancing, integer share sizing, transaction costs applied symmetrically on buys and sells, warmup-period handling, buys capped by available cash so cash never goes negative, held stocks with a missing price day valued at their last known price (logged in `engine.stale_price_log`), and force-sale of held stocks whose price history ends (delisting) at a configurable loss (`engine.delisting_log`).
- **Analytics**: total return, CAGR, annualized volatility, Sharpe ratio (0% risk-free rate), max drawdown.
- **Visualization**: equity curve and drawdown plots, in `matplotlib` and in the dashboard.
- **Dashboard**: strategy, cost, liquidity, K-most-traded, delisting-loss, and membership controls, with a warning when a run had data-quality issues.
- **Tests**: 19 tests covering look-ahead contamination, signal timing, cash accounting, costs, data gaps, delistings, late IPOs, the filters and universes, and the runner wiring.

## 11. Example Usage

The simplest way to run a backtest is through the same entry point the dashboard uses:

```python
from app.backtesting.runner import run_backtest
from app.backtesting.strategy_config import StrategyConfig
from app.data.loaders import load_all_tickers

config = StrategyConfig(
    tickers=load_all_tickers(),
    start_date="2020-01-01",
    end_date="2024-01-01",
    top_n=20,
    weighting_method="inverse_volatility",
    transaction_cost=0.0025,          # 25 bps; the old 1 bp default was unrealistic
    min_avg_traded_value=10_000_000,  # liquidity floor; 0 disables it
    top_liquid_universe=0,            # 0 = off; e.g. 200 keeps the 200 most-traded stocks per date
)

output = run_backtest(config)
print(output["metrics"])              # total_return, cagr, volatility, sharpe, max_drawdown
print(output["trades"].head())
```

`run_backtest` assembles the pipeline (universe → liquidity filters → `MomentumIndicator`, `VolatilityIndicator`, `SizeIndicator` → `CompositeFactorModel` weighted 0.6 / −0.2 / −0.2 by default → `TopNRanker` → weighting) and returns `results`, `metrics`, `trades`, and the `engine`. To assemble the components by hand, read `app/backtesting/runner.py`, which is the canonical wiring. `scripts/backtests/run_pipeline.py` is the terminal equivalent.

## 12. Backtest Integrity Findings

Early runs gave CAGRs between 30% and 110%. I investigated whether the engine or the data was responsible. The full write-up is in `docs/backtest-integrity-research.md`; the short version:

- **The mechanics are sound.** Signals use only past data, trades execute afterwards, and the return maths is correct.
- **The inputs are biased.** The universe is today's NSE 500 applied to past dates, and the price history contains no stocks that were delisted or failed. This survivorship bias is the main reason the headline numbers are too high.

| Run (454 stocks, Top 20, 2020-04-03 to 2024-01-01) | CAGR | Sharpe |
|---|---|---|
| Original assumptions (1 bp cost, no liquidity filter) | 107.76% | 3.12 |
| 25 bps cost | 100.78% | 2.99 |
| + ₹1 crore/day liquidity floor | 99.27% | 2.96 |
| + only the 200 most-traded stocks per date | 56.78% | 2.00 |
| + size weight 0 | 49.71% | 1.88 |

| Benchmarks, same dates | CAGR |
|---|---|
| Random Top 20 (5 runs, average) | 46.82% |
| Equal-weight buy-and-hold (374 stocks) | 58.83% |
| Nifty 500 index | 33.29% |

Reading: trading costs barely explain the return, but restricting to the most-traded stocks cut CAGR by about 43 points. The strategy beat random picks by about 52 points, so momentum looks informative, but its size is overstated by the same bias. About 50% (the last run) is the most defensible figure and is still an upper bound.

## 13. Known Limitations

- **Survivorship bias is unresolved.** Fixing it needs prices for delisted stocks and historical NSE 500 membership, neither of which is in the database. The code to use them is built (`PointInTimeUniverse`, `index_membership`, delisting handling) but is inactive until that data is loaded.
- **The size factor uses today's share count** for every historical date (`stocks.shares_outstanding` is a single value). Size scores are wrong for past dates.
- **The 2020 start date is the COVID low**, so much of any long-only return in the window is market beta. A later start date has not been tested.
- **The liquidity filter uses rupee traded value with no minimum price**, so low-priced, heavily traded stocks pass it.
- **Costs are a single flat rate** with no market impact; the delisting loss is a free parameter, not an estimate.
- **Only one in-sample period has been tested**, and Sharpe assumes a 0% risk-free rate.
- **Stored prices have not been checked for artificial jumps** left by an older, append-only update routine. `refresh_all_prices.py` rebuilds them.
- **The tests use synthetic data.** The corporate-action refresh logic was tested against a fake data feed, not live `yfinance`.

## 14. Key Design Principles

- **Composition over inheritance-heavy hierarchies.** Every pipeline stage (indicator, filter, ranker, weighting, universe) is a small, independently swappable object implementing one abstract method. `PipelineStrategy` doesn't know or care which concrete implementations it's holding.
- **Shared mutable state, explicit contract.** `StrategyState` is the single object every stage reads from and writes to (`historical_data`, `volume_data`, `tickers`, `selected_tickers`, `indicator_results`). This trades some of the safety of pure functions for a simpler mental model: one snapshot of "what does the strategy know right now."
- **No look-ahead bias by construction, and tested.** The strategy only sees data up to the previous trading day's close when it decides, and trades on the next close. A test rewrites all prices after a cutoff date and checks that every earlier trade is unchanged.
- **Warmup periods are computed, not hardcoded.** The engine computes `max(indicator.warmup_period for indicator in strategy.indicators)` and skips dates until enough history exists. Stocks without a full lookback window get no score instead of a distorted one.
- **Honesty over completeness.** Where something isn't solved (survivorship bias, historical shares outstanding, portfolio optimization), it's stated as a gap rather than glossed over. Results are reported as upper bounds until the data supports more.
