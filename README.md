# Quantitative Research Platform

> **README (Through Module 4)**

## Project Overview

The Quantitative Research Platform is a modular framework for
researching, constructing, and backtesting quantitative equity
strategies on Indian equities.

### Goals

-   Learn quantitative finance through implementation.
-   Build a reusable research framework.
-   Apply software engineering principles.
-   Demonstrate data engineering, system design, and analytics skills.

------------------------------------------------------------------------

## Module Progress

### M1 -- Data Platform

-   Universe ingestion
-   Historical data storage
-   PostgreSQL integration
-   Incremental updates

### M2 -- Factor Research

-   Momentum
-   Volatility
-   Size
-   Z-score normalization
-   Composite factor research

### M3 -- Backtesting Engine

-   Portfolio management
-   Buy/Sell execution
-   Transaction costs
-   Monthly rebalancing
-   Performance analytics

### M4 -- Modular Strategy Framework

Pipeline:

Universe → Indicators → Factor Model → Filters → Ranker → Weighting →
Backtesting → Analytics

------------------------------------------------------------------------

## Features

### Indicators

-   Momentum
-   Volatility
-   Size (framework support)

### Factor Models

-   Composite Factor Model
-   Cross-sectional Z-score normalization

### Filters

-   Threshold Filter
-   NoFilter

### Ranking

-   Top-N Ranker

### Weighting

-   Equal Weight
-   Inverse Volatility

### Analytics

-   Total Return
-   CAGR
-   Annualized Volatility
-   Sharpe Ratio
-   Maximum Drawdown

------------------------------------------------------------------------

## Architecture

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
Backtesting
    ↓
Analytics
```

Each stage performs one responsibility, allowing components to be
replaced independently.

------------------------------------------------------------------------

## Technology Stack

-   Python
-   PostgreSQL
-   Pandas
-   NumPy
-   Matplotlib
-   yfinance

------------------------------------------------------------------------

## Current Status

Completed: - M1 - M2 - M3 - M4 (Core)

Next: - M5 Portfolio Optimization & Risk Models

------------------------------------------------------------------------

## Purpose

The project serves as both a learning platform and a portfolio project
demonstrating:

-   Quantitative Research
-   Software Engineering
-   Data Engineering
-   Financial Analytics
-   Object-Oriented Design
