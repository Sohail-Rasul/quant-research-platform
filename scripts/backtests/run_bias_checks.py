"""
Bias / sanity checks. Answers: "is my CAGR coming from the FACTOR MODEL,
or from the universe and the time period?"

It runs, over the SAME dates and the SAME stocks:
  1. Your strategy                       (config below)
  2. Random Top-N picks (several seeds)  -> if this is close to (1), the factors add little
  3. Equal-weight buy & hold             -> the passive baseline on your (survivor) universe
  4. Nifty 500 index (^CRSLDX)           -> the real market; skipped if Yahoo has no data

Read the result like this:
  (3) far above (4)  -> your universe is biased upward (survivorship / hindsight)
  (1) close to (2)   -> the factor model adds little over random picking
  (1) far above both -> factors may help, but only trust it after the bias fixes

Usage: python scripts/backtests/run_bias_checks.py
"""
import statistics

import pandas as pd

from app.analytics.reports import generate_results
from app.backtesting.backtest_engine import BacktestEngine
from app.backtesting.runner import run_backtest
from app.backtesting.strategy_config import StrategyConfig
from app.data.loaders import load_all_tickers, load_metadata, load_prices
from app.ranking.random_ranker import RandomRanker
from app.strategies.buy_and_hold import BuyAndHoldStrategy
from app.universe.user_universe import UserUniverse
from app.weighting.equal_weight import EqualWeight

# ---------------- EDIT THESE ----------------
START_DATE = "2020-01-01"
END_DATE = "2024-01-01"
TOP_N = 20
N_RANDOM_RUNS = 5          # each run reloads data, so keep this modest
# --------------------------------------------


def fmt(metrics):
    return (f"CAGR {metrics['cagr']:>7.2%} | Sharpe {metrics['sharpe']:>5.2f} | "
            f"MaxDD {metrics['max_drawdown']:>7.2%}")


def buy_and_hold(tickers, first_date):
    """Equal-weight buy & hold starting on the same day as the strategy."""
    prices = load_prices(tickers, START_DATE, END_DATE)
    dates = sorted(prices["date"].unique())
    prev_date = dates[max(dates.index(first_date) - 1, 0)]       # BuyAndHold signals one day before it trades
    prices = prices[prices["date"] >= prev_date]
    on_start = set(prices[prices["date"] == first_date]["ticker"])  # only stocks that exist on day 1
    held = [t for t in tickers if t in on_start]

    engine = BacktestEngine(
        strategy=BuyAndHoldStrategy(UserUniverse(held), EqualWeight()),
        prices_df=prices[prices["ticker"].isin(held)],
        metadata_df=load_metadata(held),
        initial_capital=1_000_000,
        transaction_cost=0.0025,
    )
    return generate_results(engine.run()), len(held)


def index_benchmark(first_date, last_date):
    try:
        import yfinance as yf
        data = yf.download("^CRSLDX", start=str(first_date), end=str(last_date), progress=False)
        close = data["Close"].squeeze().dropna()
        if len(close) < 20:
            return None
        frame = pd.DataFrame({"date": close.index, "portfolio_value": close.values})
        return generate_results(frame)
    except Exception as exc:
        print(f"   (index benchmark skipped: {exc})")
        return None


def main():
    tickers = load_all_tickers()
    config = StrategyConfig(tickers=tickers, start_date=START_DATE, end_date=END_DATE, top_n=TOP_N)

    print("1) Strategy ...")
    output = run_backtest(config)
    results = output["results"]
    first_date, last_date = results["date"].iloc[0], results["date"].iloc[-1]
    strategy_metrics = output["metrics"]

    print(f"2) Random picks x{N_RANDOM_RUNS} ...")
    random_cagrs = []
    for seed in range(N_RANDOM_RUNS):
        out = run_backtest(config, ranker=RandomRanker("composite", TOP_N, seed=seed))
        random_cagrs.append(out["metrics"]["cagr"])

    print("3) Equal-weight buy & hold ...")
    bh_metrics, n_held = buy_and_hold(tickers, first_date)

    print("4) Nifty 500 index ...")
    index_metrics = index_benchmark(first_date, last_date)

    print("\n" + "=" * 78)
    print(f"Period: {first_date} -> {last_date}")
    print("=" * 78)
    print(f"Strategy (Top {TOP_N})        : {fmt(strategy_metrics)}")
    print(f"Random Top {TOP_N} (avg/min/max): CAGR {statistics.mean(random_cagrs):.2%} / "
          f"{min(random_cagrs):.2%} / {max(random_cagrs):.2%}")
    print(f"Buy & hold ({n_held} stocks)   : {fmt(bh_metrics)}")
    print(f"Nifty 500 index            : {fmt(index_metrics) if index_metrics else 'unavailable'}")
    print("=" * 78)

    if index_metrics:
        gap = bh_metrics["cagr"] - index_metrics["cagr"]
        print(f"Buy&hold on your universe minus the index: {gap:+.2%} CAGR "
              f"(a large positive gap is the survivorship / hindsight signature)")
    print(f"Strategy minus random picks: {strategy_metrics['cagr'] - statistics.mean(random_cagrs):+.2%} CAGR "
          f"(the part the factors actually add)")


if __name__ == "__main__":
    main()
