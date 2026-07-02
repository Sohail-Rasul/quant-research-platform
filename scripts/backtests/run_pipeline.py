from app.data.loaders import load_prices
from app.backtesting.backtest_engine import BacktestEngine

from app.visualization.plots import (plot_drawdown,plot_equity_curve)
from app.analytics.reports import generate_results

from app.universe.user_universe import UserUniverse
from app.indicators.momentum_indicator import MomentumIndicator
from app.filters.no_filter import NoFilter
from app.ranking.no_ranker import NoRanker
from app.weighting.equal_weight import EqualWeight

from app.strategies.pipeline_strategy import PipelineStrategy

#LOAD TICKERS
tickers = [
    "RELIANCE.NS",
    "TCS.NS",
    "INFY.NS"
]

#LOAD PRICES
prices = load_prices(
    tickers=tickers,
    start_date="2020-01-01",
    end_date="2024-01-01"
)

#CREATE STRATEGY PIPELINE
universe = UserUniverse(tickers)

indicators = [MomentumIndicator(63)] #LIST

filters = [NoFilter()] #LIST

ranker = NoRanker()

weighting = EqualWeight()

strategy = PipelineStrategy(
    universe=universe,
    indicators=indicators,
    filters=filters,
    ranker=ranker,
    weighting=weighting
)

#RUN BACKTESTING ENGINE
engine = BacktestEngine(
    strategy=strategy,
    prices_df=prices,
    initial_capital=1_000_000,
    transaction_cost=0.0001
)

results = engine.run()

results["returns"] = (
    results["portfolio_value"].pct_change()
)

print(results.head())
print(results.tail())

print(f"Leftover Cash: {engine.portfolio.cash}")
print(f"Portfolio Positions: {engine.portfolio.positions}")


#ANALYTICS
metrics = generate_results(results)
print(f"==========================")
print(f"        ANALYTICS        ")
print(f"==========================")
#Total Return
print(f"Total Return: {metrics['total_return']:.2%}")

#CAGR
print(f"CAGR: {metrics['cagr']:.2%}")

#Volatility
print(f"Annualized Volatility: {metrics['volatility']:.2%}")

#Sharpe Ratio
print(f"Sharpe Ratio: {metrics['sharpe']:.2f}")

#Max Drawdown
print(f"Max Drawdown: {metrics['max_drawdown']:.2%}")

plot_equity_curve(results)

plot_drawdown(results)