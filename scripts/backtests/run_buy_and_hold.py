from app.data.loaders import load_prices
from app.strategies.buy_and_hold import BuyAndHoldStrategy
from app.backtesting.backtest_engine import BacktestEngine

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
    initial_capital=1_000_000
)

results = engine.run()
results["returns"] = (
    results["portfolio_value"].pct_change()
)

print(results.head())
print(results.tail())

print(f"Leftover Cash: {engine.portfolio.cash}")
print(f"Portfolio Positions: {engine.portfolio.positions}")

