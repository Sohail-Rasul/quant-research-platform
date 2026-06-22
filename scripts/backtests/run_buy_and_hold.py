from app.data.loaders import load_prices
from app.strategies.buy_and_hold import BuyAndHoldStrategy
from app.backtesting.backtest_engine import BacktestEngine
from app.visualization.plots import (plot_equity_curve,plot_drawdown)

from app.analytics.reports import generate_results

tickers = [
    "RELIANCE.NS",
    "TCS.NS",
    "INFY.NS"
]

prices = load_prices(
    tickers=["RELIANCE.NS", "TCS.NS", "INFY.NS"],
    start_date="2020-01-01",
    end_date="2024-01-01"
)

strategy = BuyAndHoldStrategy(tickers)

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