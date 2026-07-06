# Project Architecture

> Quantitative Research Platform (Through Module 4)

------------------------------------------------------------------------

# Overall Architecture

The framework is built as a pipeline. Every stage performs exactly one
responsibility.

``` text
Universe
    ↓
Indicators
    ↓
Factor Model
    ↓
Filters
    ↓
Ranking
    ↓
Weighting
    ↓
Backtest Engine
    ↓
Analytics & Visualization
```

This separation makes the framework easy to extend. New indicators,
filters, ranking methods, or weighting schemes can be added without
changing the rest of the code.

------------------------------------------------------------------------

# Data Flow

1.  Load historical price data.
2.  Select the investment universe.
3.  Compute indicators.
4.  Build factor scores.
5.  Filter the universe.
6.  Rank remaining stocks.
7.  Generate portfolio weights.
8.  Execute trades.
9.  Track portfolio value.
10. Calculate performance metrics.

------------------------------------------------------------------------

# StrategyState

## Purpose

`StrategyState` is the shared object passed throughout the pipeline.

Instead of every component recalculating or storing its own information,
everything reads from and writes to one state object.

## Stores

-   Current date
-   Historical prices
-   Universe
-   Selected tickers
-   Indicator results

This keeps every stage independent while allowing them to communicate.

------------------------------------------------------------------------

# Universe

Responsible for defining **which stocks may be considered**.

Examples: - User-defined list - NSE 500 - Future dynamic universes

The universe does **not** rank or filter stocks. It only provides
candidates.

------------------------------------------------------------------------

# Indicators

Indicators transform historical prices into measurable signals.

Current implementations:

-   Momentum
-   Volatility

Every indicator: - Receives `StrategyState` - Uses historical data -
Returns a Pandas Series indexed by ticker

Because every indicator follows the same interface, new indicators can
be added without modifying the strategy.

------------------------------------------------------------------------

# Factor Model

A factor model combines multiple indicators into one signal.

Current implementation:

-   CompositeFactorModel

Workflow:

1.  Read indicator values.
2.  Normalize each factor using Z-scores.
3.  Apply user-defined weights.
4.  Produce one composite score.

Why normalize?

Different indicators have different numerical scales. Standardization
ensures each factor contributes according to its assigned weight rather
than its raw magnitude.

------------------------------------------------------------------------

# Filters

Filters remove stocks that do not satisfy predefined conditions.

Examples:

-   ThresholdFilter
-   NoFilter

Filters operate sequentially, meaning each filter only evaluates stocks
that survived previous stages.

------------------------------------------------------------------------

# Ranking

Ranking determines **which** stocks enter the portfolio.

Current implementation:

-   TopNRanker

Supports: - Highest values - Lowest values

Ranking changes the selected universe but does not decide capital
allocation.

------------------------------------------------------------------------

# Weighting

Weighting determines **how much capital** is allocated to each selected
stock.

Current implementations:

-   Equal Weight
-   Inverse Volatility Weight

Separating weighting from ranking allows the same stock selection
strategy to be tested with multiple allocation methods.

------------------------------------------------------------------------

# Backtest Engine

Responsibilities:

-   Portfolio initialization
-   Monthly rebalancing
-   Buy/Sell execution
-   Transaction costs
-   Cash accounting
-   Equity curve generation

The engine knows nothing about momentum or volatility. It only executes
the weights provided by the strategy.

------------------------------------------------------------------------

# Portfolio

The portfolio tracks:

-   Cash
-   Positions
-   Shares owned
-   Portfolio value

Portfolio value is updated daily using current market prices.

------------------------------------------------------------------------

# Analytics

Current metrics:

-   Total Return
-   CAGR
-   Annualized Volatility
-   Sharpe Ratio
-   Maximum Drawdown

These evaluate strategy performance after the simulation finishes.

------------------------------------------------------------------------

# Design Principles

-   Single Responsibility Principle
-   Separation of Concerns
-   Modular Components
-   Reusable Interfaces
-   Easy Extensibility

The architecture was intentionally designed so that research ideas can
be tested by replacing individual components instead of rewriting
complete strategies.

------------------------------------------------------------------------

# Summary

The framework separates the investment process into independent stages:

1.  Find candidate stocks.
2.  Measure them.
3.  Combine signals.
4.  Remove unsuitable candidates.
5.  Rank the survivors.
6.  Allocate capital.
7.  Simulate execution.
8.  Evaluate results.

This mirrors the workflow used in many quantitative research teams while
keeping the implementation simple and extensible.
