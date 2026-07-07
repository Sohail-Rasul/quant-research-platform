# Quantitative Research Platform

A modular, incrementally-built research and backtesting framework for equity strategies, developed as a learning project spanning data engineering, quantitative factor research, and software architecture.

> **Educational project.** This is a personal learning platform, not a production trading system. Where functionality is incomplete or simplified, this document says so explicitly.

---

## 1. Project Overview

This repository is a from-scratch quantitative research platform built to answer one question honestly: *can I design, build, and defend every layer of a systematic equity strategy pipeline myself?* It combines:

- A **PostgreSQL-backed historical data layer** for prices and stock metadata.
- A set of **factor research scripts** (momentum, volatility, size, cross-sectional z-scores, composite scoring) written directly against SQL.
- A **class-based strategy framework** (`StrategyState`, `PipelineStrategy`, and a family of abstract base classes) that turns those ad-hoc factors into a reusable, swappable pipeline.
- A **backtesting engine** that simulates monthly-rebalanced portfolios with transaction costs.
- **Analytics and visualization** modules for total return, CAGR, volatility, Sharpe ratio, and drawdown.

The project was built module by module (M1–M4, described below), and the architecture reflects that history — earlier modules are simpler and more direct; later modules are more abstract because direct experience with the earlier modules exposed their limitations.

## 2. Motivation

The motivation was not "build a backtester" as an end in itself. It was to force myself through the full arc of a quant research workflow: ingesting real data, computing factors correctly (including subtleties like sample vs. population standard deviation), simulating a strategy against realistic constraints (transaction costs, integer share counts, monthly rebalancing), and measuring performance with the same metrics used in industry (Sharpe, CAGR, max drawdown). Doing this myself, end to end, was the point and not outsourcing any layer to an existing library like `zipline` or `backtrader`.

## 3. Problem Statement

- How do you evaluate different signals (momentum, volatility, size) without duplicating logic every time?
- How do you compose several signals into one score without hardcoding assumptions about which signals are involved?
- How do you simulate a portfolio without look-ahead bias, while still handling monthly rebalancing, warmup periods, and transaction costs realistically?
- How do you keep the codebase extensible as new indicators, filters, rankers, and weighting schemes are added, without rewriting the backtest engine every time?

This project's later modules exist specifically to solve these problems.

## 4. Goals

- Build a working, correct backtesting engine.
- Learn the mathematics behind each component well enough to derive it on a whiteboard.
- Design an architecture where new indicators, filters, rankers, and weighting schemes can be added without modifying existing code (open/closed principle).
- Keep the system honest: no feature is claimed unless it is implemented and testable.

## 5. Technology Stack

| Layer | Technology |
|---|---|
| Data storage | PostgreSQL |
| Data access | `psycopg` (raw SQL, no ORM) |
| Data ingestion | `yfinance` |
| Numerical computing | `pandas`, `numpy` |
| Visualization | `matplotlib` |
| Configuration | `python-dotenv` (`.env` for DB credentials) |
| Language | Python 3.11 |

There is no web framework, no task queue, and no ORM — this is a research codebase run via standalone scripts, not a deployed service.

## 6. High-Level Architecture

The platform has two distinct implementation styles that coexist in the repo, reflecting its evolution:

1. **SQL-first factor scripts** (`scripts/factors/`, `app/indicators/momentum.py`, `volatility.py`, `size.py`, `zscore.py`, `composite_score.py`) — these compute factors directly via SQL window functions (`LAG`, `STDDEV_SAMP`) against the `prices`/`stocks` tables, for a single as-of date. This was the M2 research style.
2. **Pandas-based pipeline framework** (`app/strategies/`, `app/indicators/*_indicator.py`, `app/factor_models/`, `app/filters/`, `app/ranking/`, `app/weighting/`) — this is the M4 framework used by the actual backtesting engine. It operates on a `StrategyState` object carrying a historical price DataFrame, and every stage (indicator → factor model → filter → ranker → weighter) mutates or reads that shared state.

> **Design Decision:** The SQL scripts and the pipeline framework are *not* wired together. The SQL scripts were the original research tools for validating factor logic against the database; the pipeline framework reimplements the same ideas (momentum, volatility, z-score, composite score) in pandas so they can run inside a backtest loop without a live DB round-trip per rebalance. This is an intentional, honest architectural seam, not an oversight — but it does mean the SQL-based factor scripts are currently a separate, standalone research tool rather than a component the backtester calls into.

```
                 ┌───────────────────────────┐
                 │        PostgreSQL          │
                 │  stocks / prices tables    │
                 └─────────────┬─────────────┘
                               │ load_prices()
                               ▼
                    ┌─────────────────────┐
                    │   prices_df (pandas) │
                    └──────────┬──────────┘
                               ▼
                    ┌─────────────────────┐
                    │   BacktestEngine     │
                    │  (monthly loop)      │
                    └──────────┬──────────┘
                               │ builds StrategyState per rebalance date
                               ▼
        ┌───────────────────────────────────────────────┐
        │                PipelineStrategy                │
        │  Universe → Indicators → Factor Model →         │
        │  Filters → Ranker → Weighting                   │
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
                 │ Sharpe, CAGR, Drawdown, ...│
                 └───────────────────────────┘
```

## 7. Folder Structure

```
quant-research-platform/
├── app/
│   ├── backtesting/        # BacktestEngine, Portfolio, Position
│   ├── strategies/         # StrategyState, PipelineStrategy, BuyAndHoldStrategy
│   ├── universe/           # BaseUniverse, UserUniverse
│   ├── indicators/         # Class-based indicators + legacy SQL factor scripts
│   ├── factor_models/      # BaseFactorModel, CompositeFactorModel
│   ├── filters/            # BaseFilter, NoFilter, ThresholdFilter
│   ├── ranking/             # BaseRanker, TopNRanker, NoRanker
│   ├── weighting/          # BaseWeighting, EqualWeight, InverseVolatilityWeight
│   ├── analytics/          # performance.py, reports.py
│   ├── visualization/      # plots.py (matplotlib)
│   ├── data/                # loaders.py (psycopg-based price loading)
│   ├── utils/                # statistics.py (z-score helper)
│   ├── update.py / backfill.py / metadata.py   # yfinance ingestion scripts
├── scripts/
│   ├── stocks_prices/      # backfill/update price scripts
│   ├── stocks_metadata/    # universe & metadata ingestion
│   ├── factors/             # SQL-based factor research scripts (M2)
│   └── backtests/           # run_pipeline.py, run_buy_and_hold.py
├── sql/                      # 001_create_tables.sql, 002_add_shares_outstanding.sql
├── data/                      # NSE_500.csv (universe reference file)
├── tests/                    # currently empty — no automated tests yet
└── docs/, notebooks/          # currently empty placeholders
```

> **Honesty note:** `tests/`, `docs/`, and `notebooks/` currently exist as empty directories. There is no automated test suite yet — correctness has been validated manually by inspecting backtest output, not via `pytest`. This is worth stating plainly rather than implying otherwise.

## 8. Module Overview (M1–M4)

| Module | Focus | Key Deliverable |
|---|---|---|
| **M1** | Historical Data Platform | PostgreSQL schema (`stocks`, `prices`), ingestion via `yfinance` (`backfill.py`, `update.py`, `metadata.py`), data validation (OHLC sanity checks in `backfill_prices`) |
| **M2** | Factor Research | SQL-based momentum, volatility, size, and z-score computations as standalone research scripts |
| **M3** | Backtesting Engine | `Portfolio`, `Position`, buy/sell execution, monthly rebalancing, transaction costs, equity curve, performance analytics |
| **M4** | Strategy Framework | `StrategyState`, `PipelineStrategy`, and abstract base classes (`BaseIndicator`, `BaseFactorModel`, `BaseFilter`, `BaseRanker`, `BaseWeighting`) generalizing the whole thing into a composable pipeline |

Each module is covered in depth, including the *why* behind its design, in `Module Breakdown.md`.

## 9. Current Features

- **Data ingestion**: backfill full price history and incrementally update it via `yfinance`, with row-level OHLC validation (rows with impossible highs/lows/opens/closes are skipped, not silently inserted).
- **Universe definition**: a simple `UserUniverse` (explicit ticker list) implementing `BaseUniverse`. There is a static `NSE_500.csv` reference file in `data/`, but universe selection in code is currently manual, not dynamically sourced from that file.
- **Indicators**: class-based `MomentumIndicator` (simple price-ratio momentum over a lookback) and `VolatilityIndicator` (annualized standard deviation of daily returns, sample statistics, `sqrt(252)` scaling).
- **Composite factor model**: `CompositeFactorModel` combines multiple z-scored indicators into a single weighted composite score.
- **Filters**: `NoFilter` (pass-through) and `ThresholdFilter` (keep/drop tickers based on an operator + threshold against any indicator).
- **Ranking**: `NoRanker` (pass-through) and `TopNRanker` (select the top/bottom N tickers by any indicator).
- **Weighting**: `EqualWeight` and `InverseVolatilityWeight`.
- **Backtesting**: monthly rebalancing, integer share sizing, transaction costs applied symmetrically on buys and sells, warmup-period handling so indicators never see insufficient history.
- **Analytics**: total return, CAGR, annualized volatility, Sharpe ratio, max drawdown.
- **Visualization**: equity curve and drawdown plots via `matplotlib`.

## 10. Example Strategy Pipeline

The canonical example (`scripts/backtests/run_pipeline.py`) wires the framework together like this:

```
Universe:  UserUniverse(["RELIANCE.NS", "TCS.NS", "INFY.NS"])
Indicators: MomentumIndicator(63), VolatilityIndicator(63)
Factor Model: CompositeFactorModel({"momentum": 0.6, "volatility": -0.4})
Filters:    [NoFilter()]
Ranker:     TopNRanker(indicator="composite", n=1, ascending=False)
Weighting:  InverseVolatilityWeight(indicator="volatility")
```

This selects the single best composite-scoring stock each month (out of a 3-ticker universe) and sizes the position using inverse-volatility weighting — with only one surviving ticker, the weighting step trivially assigns it 100%. This is intentionally a small, easy-to-trace example rather than a production universe.

## 11. Example Usage

```python
from app.data.loaders import load_prices
from app.backtesting.backtest_engine import BacktestEngine
from app.universe.user_universe import UserUniverse
from app.indicators.momentum_indicator import MomentumIndicator
from app.indicators.volatility_indicator import VolatilityIndicator
from app.factor_models.composite_factor_model import CompositeFactorModel
from app.filters.no_filter import NoFilter
from app.ranking.topNranker import TopNRanker
from app.weighting.inverse_volatility_weight import InverseVolatilityWeight
from app.strategies.pipeline_strategy import PipelineStrategy
from app.analytics.reports import generate_results

tickers = ["RELIANCE.NS", "TCS.NS", "INFY.NS"]
prices = load_prices(tickers, start_date="2020-01-01", end_date="2024-01-01")

strategy = PipelineStrategy(
    universe=UserUniverse(tickers),
    indicators=[MomentumIndicator(63), VolatilityIndicator(63)],
    factor_model=CompositeFactorModel({"momentum": 0.6, "volatility": -0.4}),
    filters=[NoFilter()],
    ranker=TopNRanker(indicator="composite", n=1, ascending=False),
    weighting=InverseVolatilityWeight(indicator="volatility"),
)

engine = BacktestEngine(strategy, prices, initial_capital=1_000_000, transaction_cost=0.0001)
results = engine.run()
print(generate_results(results))
```

## 12. Key Design Principles

- **Composition over inheritance-heavy hierarchies.** Every pipeline stage (indicator, filter, ranker, weighting) is a small, independently swappable object implementing one abstract method. `PipelineStrategy` doesn't know or care which concrete implementations it's holding.
- **Shared mutable state, explicit contract.** `StrategyState` is the single object every stage reads from and writes to (`historical_data`, `tickers`, `selected_tickers`, `indicator_results`). This trades some of the safety of pure functions for a simpler mental model: one snapshot of "what does the strategy know right now."
- **No look-ahead bias by construction.** `BacktestEngine._get_historical_data` always slices `price_matrix.loc[:current_date]` — the strategy never sees future prices when generating weights for a given rebalance date.
- **Warmup periods are computed, not hardcoded.** The engine computes `max(indicator.warmup_period for indicator in strategy.indicators)` and skips dates until enough history exists, rather than assuming a fixed number of days.
- **Honesty over completeness.** Where something isn't implemented (tests, dynamic universe loading from `NSE_500.csv`, portfolio optimization), it's stated as a gap rather than glossed over.

## 13. Future Roadmap (M5+)

M5 is **not yet implemented**. Planned scope:

- Portfolio optimization (e.g., mean-variance / Markowitz-style allocation) to replace the current heuristic weighting schemes.
- Formal risk models (factor covariance, position/sector limits).
- Multi-factor portfolios that combine more than two signals with a more principled weighting scheme than the current linear composite.
- Benchmark comparison (e.g., strategy vs. NSE 500 buy-and-hold) — currently `BuyAndHoldStrategy` exists but is only run as a separate script, not compared side-by-side with the pipeline strategy in one report.
- Performance attribution (which factor contributed how much to returns).

---

For the full architectural reasoning behind each component — including trade-offs and interview framing — see **`Project Architecture.md`**, **`Module Breakdown.md`**, **`Mathematics Behind the Platform.md`**, and **`Interview Handbook.md`**.