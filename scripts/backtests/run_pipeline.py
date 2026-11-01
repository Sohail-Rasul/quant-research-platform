from app.backtesting.runner import run_backtest
from app.backtesting.strategy_config import StrategyConfig
from app.visualization.plots import plot_drawdown, plot_equity_curve


tickers = [
    "RELIANCE.NS",
    "TCS.NS",
    "INFY.NS"
]


config = StrategyConfig(
    tickers=tickers,
    start_date="2020-01-01",
    end_date="2024-01-01"
)


output = run_backtest(config)

results = output["results"]
metrics = output["metrics"]
trades = output["trades"]
engine = output["engine"]


# TRADE LOG
print("=====================")
print("     TRADE LOG")
print("=====================")

print(trades.head())
print("...")
print(trades.tail())


# RESULTS
print(results.head())
print(results.tail())


# PORTFOLIO
print(f"Leftover Cash: {engine.portfolio.cash}")
print(f"Portfolio Positions: {engine.portfolio.positions}")


# ANALYTICS
print("==========================")
print("        ANALYTICS")
print("==========================")

print(f"Total Trades Executed: {len(trades)}")
print(f"Total Return: {metrics['total_return']:.2%}")
print(f"CAGR: {metrics['cagr']:.2%}")
print(f"Annualized Volatility: {metrics['volatility']:.2%}")
print(f"Sharpe Ratio: {metrics['sharpe']:.2f}")
print(f"Max Drawdown: {metrics['max_drawdown']:.2%}")


# VISUALIZATION
plot_equity_curve(results)
plot_drawdown(results)