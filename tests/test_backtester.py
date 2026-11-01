import contextlib
import io
import sys
import types

import numpy as np
import pandas as pd
import pytest

from app.analytics.performance import calculate_cagr
from app.backtesting.backtest_engine import BacktestEngine
from app.factor_models.composite_factor_model import CompositeFactorModel
from app.filters.liquidity_filter import LiquidityFilter
from app.filters.no_filter import NoFilter
from app.filters.top_liquidity_filter import TopLiquidityFilter
from app.indicators.momentum_indicator import MomentumIndicator
from app.indicators.size_indicator import SizeIndicator
from app.indicators.volatility_indicator import VolatilityIndicator
from app.ranking.random_ranker import RandomRanker
from app.ranking.topNranker import TopNRanker
from app.strategies.buy_and_hold import BuyAndHoldStrategy
from app.strategies.pipeline_strategy import PipelineStrategy
from app.strategies.strategy_state import StrategyState
from app.universe.point_in_time_universe import PointInTimeUniverse
from app.universe.user_universe import UserUniverse
from app.weighting.equal_weight import EqualWeight
from app.weighting.inverse_volatility_weight import InverseVolatilityWeight

TICKERS = ["A.NS", "B.NS", "C.NS", "D.NS", "E.NS"]


def make_prices(tickers=TICKERS, days=260, seed=1, drop=None, gap=None, volume=None):
    rng = np.random.default_rng(seed)
    dates = pd.bdate_range("2022-01-03", periods=days)
    rows = []
    for t in tickers:
        price = 100.0
        for i, d in enumerate(dates):
            price *= 1 + rng.normal(0.0004, 0.018)
            if drop and t == drop[0] and i >= drop[1]:
                continue
            if gap and t == gap[0] and i == gap[1]:
                continue
            vol = (volume or {}).get(t, 5000)
            rows.append(dict(date=d, ticker=t, adj_close=price, volume=vol))
    return pd.DataFrame(rows)


def make_meta(tickers=TICKERS):
    return pd.DataFrame({"shares_outstanding": [1_000_000] * len(tickers)},
                        index=pd.Index(tickers, name="ticker"))


def pipeline(tickers=TICKERS, top_n=3, weighting=None, universe=None,
             universe_filters=None, ranker=None, factors=None):
    return PipelineStrategy(
        universe=universe or UserUniverse(tickers),
        indicators=[MomentumIndicator(63), VolatilityIndicator(63), SizeIndicator()],
        ranker=ranker or TopNRanker("composite", top_n),
        weighting=weighting or EqualWeight(),
        filters=[NoFilter()],
        factor_model=CompositeFactorModel(factors or {"momentum": .6, "volatility": -.2, "size": -.2}),
        universe_filters=universe_filters,
    )


def run(strategy, prices, cost=0.0, **kw):
    engine = BacktestEngine(strategy, prices, make_meta(sorted(prices.ticker.unique())),
                            1_000_000, cost, **kw)
    with contextlib.redirect_stdout(io.StringIO()):
        results = engine.run()
    return engine, results


# ---------------------------------------------------------------- timing / look-ahead
def test_signal_uses_only_prior_day_data():
    seen = []

    class Spy(PipelineStrategy):
        def generate_weights(self, state):
            seen.append((state.date, state.historical_data.index.max()))
            return super().generate_weights(state)

    base = pipeline()
    spy = Spy(base.universe, base.indicators, base.ranker, base.weighting, base.filters, base.factor_model)
    prices = make_prices()
    engine, _ = run(spy, prices)
    first_trade = pd.Timestamp(engine.get_trade_log()["date"].iloc[0])
    for signal_date, last_data in seen:
        assert last_data <= signal_date          # never sees data after the signal date
    assert seen[0][0] < first_trade              # first signal is strictly before first trade


def test_future_prices_cannot_change_past_trades():
    prices = make_prices()
    cutoff = sorted(prices.date.unique())[150]
    contaminated = prices.copy()
    rng = np.random.default_rng(99)
    mask = contaminated.date > cutoff
    contaminated.loc[mask, "adj_close"] *= rng.uniform(0.3, 3.0, mask.sum())

    a, _ = run(pipeline(), prices)
    b, _ = run(pipeline(), contaminated)
    ta, tb = a.get_trade_log(), b.get_trade_log()
    ta = ta[pd.to_datetime(ta.date) <= cutoff].reset_index(drop=True)
    tb = tb[pd.to_datetime(tb.date) <= cutoff].reset_index(drop=True)
    pd.testing.assert_frame_equal(ta, tb)


# ---------------------------------------------------------------- accounting
def test_cash_never_negative_and_value_consistent():
    engine, results = run(pipeline(top_n=3), make_prices(), cost=0.0025)
    assert (engine.get_trade_log()["cash_after"] >= -1e-6).all()
    last = results.iloc[-1]
    held = sum(engine.last_known_prices[t] * p.shares for t, p in engine.portfolio.positions.items())
    assert last.portfolio_value == pytest.approx(engine.portfolio.cash + held)


def test_buy_and_hold_matches_price_return_without_costs():
    prices = make_prices(["A.NS"])
    strat = BuyAndHoldStrategy(UserUniverse(["A.NS"]), EqualWeight())
    engine, results = run(strat, prices, cost=0.0)
    first, last = prices.adj_close.iloc[1], prices.adj_close.iloc[-1]       # trades on day 2
    assert results.portfolio_value.iloc[-1] / results.portfolio_value.iloc[0] == pytest.approx(last / first, rel=1e-3)


def test_cagr_formula():
    curve = pd.DataFrame({"date": pd.to_datetime(["2020-01-01", "2022-01-01"]),
                          "portfolio_value": [100.0, 200.0]})
    years = (pd.Timestamp("2022-01-01") - pd.Timestamp("2020-01-01")).days / 365.25
    assert calculate_cagr(curve) == pytest.approx(2 ** (1 / years) - 1)


def test_costs_reduce_final_value():
    p = make_prices()
    _, free = run(pipeline(), p, cost=0.0)
    _, costly = run(pipeline(), p, cost=0.01)
    assert costly.portfolio_value.iloc[-1] < free.portfolio_value.iloc[-1]


# ---------------------------------------------------------------- data gaps / delistings
def test_missing_price_day_does_not_crash_and_is_logged():
    engine, results = run(pipeline(top_n=5), make_prices(gap=("A.NS", 150)))
    assert len(results) > 0 and engine.stale_price_log


def test_delisting_force_sells_with_haircut():
    prices = make_prices(drop=("B.NS", 140))
    engine, _ = run(pipeline(top_n=5), prices, cost=0.0, delisting_haircut=0.4)
    assert engine.delisting_log, "held stock that vanished must be force-sold"
    date, ticker, shares, sale_price = engine.delisting_log[0]
    assert ticker == "B.NS" and "B.NS" not in engine.portfolio.positions
    assert sale_price == pytest.approx(engine.last_known_prices["B.NS"] * 0.6)
    assert "DELIST_SELL" in set(engine.get_trade_log()["action"])


def test_late_ipo_excluded_until_full_history():
    prices = make_prices()
    late = prices[(prices.ticker == "E.NS") & (prices.date >= prices.date.unique()[200])]
    prices = pd.concat([prices[prices.ticker != "E.NS"], late])
    engine, _ = run(pipeline(top_n=5), prices)
    assert "E.NS" not in set(engine.get_trade_log()["ticker"])   # only ~60 days of history -> never eligible


# ---------------------------------------------------------------- universe / filters
def _state(prices, last_n=None):
    pm = prices.pivot(index="date", columns="ticker", values="adj_close")
    vm = prices.pivot(index="date", columns="ticker", values="volume")
    return StrategyState(date=pm.index[-1], historical_data=pm, tickers=list(pm.columns),
                         selected_tickers=list(pm.columns), volume_data=vm, metadata=make_meta(list(pm.columns)))


def test_top_liquidity_filter_keeps_most_traded():
    prices = make_prices(volume={"A.NS": 100, "B.NS": 9000, "C.NS": 5000, "D.NS": 7000, "E.NS": 1})
    state = _state(prices)
    TopLiquidityFilter(20, 2).apply(state)
    assert set(state.selected_tickers) == {"B.NS", "D.NS"}


def test_min_traded_value_filter():
    prices = make_prices(volume={"A.NS": 1})
    state = _state(prices)
    LiquidityFilter(20, 10_000).apply(state)
    assert "A.NS" not in state.selected_tickers and len(state.selected_tickers) == 4


def test_zscores_computed_only_over_investable_universe():
    prices = make_prices(volume={"A.NS": 9000, "B.NS": 8000, "C.NS": 7000, "D.NS": 1, "E.NS": 1})
    strat = pipeline(top_n=2, universe_filters=[TopLiquidityFilter(20, 3)])
    state = _state(prices)
    strat.generate_weights(state)
    assert set(state.indicator_results["composite"].index) == {"A.NS", "B.NS", "C.NS"}


def test_point_in_time_universe_membership():
    membership = pd.DataFrame({
        "ticker": ["A.NS", "B.NS", "C.NS"],
        "added_date": ["2010-01-01", "2022-06-01", "2010-01-01"],
        "removed_date": [None, None, "2022-03-01"],
    })
    uni = PointInTimeUniverse(membership)
    uni.set_date("2022-01-15")
    assert set(uni.get_tickers()) == {"A.NS", "C.NS"}      # B not yet added
    uni.set_date("2022-07-01")
    assert set(uni.get_tickers()) == {"A.NS", "B.NS"}      # C removed, B added


def test_pipeline_with_point_in_time_universe_never_trades_non_members():
    prices = make_prices()
    dates = sorted(prices.date.unique())
    membership = pd.DataFrame({
        "ticker": TICKERS,
        "added_date": ["2010-01-01"] * 4 + [str(dates[200].date())],   # E joins late
        "removed_date": [None] * 5,
    })
    engine, _ = run(pipeline(top_n=5, universe=PointInTimeUniverse(membership)), prices)
    trades = engine.get_trade_log()
    e_trades = trades[trades.ticker == "E.NS"]
    assert e_trades.empty or pd.to_datetime(e_trades.date).min() > dates[200]


def test_random_ranker_is_seeded_and_respects_eligibility():
    state = _state(make_prices())
    state.indicator_results["composite"] = pd.Series({"A.NS": 1.0, "B.NS": np.nan, "C.NS": 2.0, "D.NS": 3.0, "E.NS": 4.0})
    picks = []
    for _ in range(2):
        s = _state(make_prices()); s.indicator_results = state.indicator_results
        RandomRanker("composite", 3, seed=7).rank(s)
        picks.append(s.selected_tickers)
    assert picks[0] == picks[1] and "B.NS" not in picks[0] and len(picks[0]) == 3


def test_inverse_vol_weights_sum_to_one():
    state = _state(make_prices())
    strat = pipeline(top_n=3, weighting=InverseVolatilityWeight("volatility"))
    weights = strat.generate_weights(state)
    assert sum(weights.values()) == pytest.approx(1.0) and all(w > 0 for w in weights.values())


# ---------------------------------------------------------------- runner wiring (DB stubbed)
def test_runner_end_to_end_with_stubbed_loader(monkeypatch):
    loaders = sys.modules["app.data.loaders"]
    prices = make_prices()
    monkeypatch.setattr(loaders, "load_prices", lambda *a, **k: prices)
    monkeypatch.setattr(loaders, "load_metadata", lambda *a, **k: make_meta())
    for name in ("app.backtesting.runner",):
        sys.modules.pop(name, None)
    from app.backtesting.runner import run_backtest
    from app.backtesting.strategy_config import StrategyConfig

    cfg = StrategyConfig(tickers=TICKERS, start_date="2022-01-01", end_date="2023-01-01",
                         top_n=3, weighting_method="equal", transaction_cost=0.0025,
                         min_avg_traded_value=1000, top_liquid_universe=4)
    with contextlib.redirect_stdout(io.StringIO()):
        out = run_backtest(cfg)
        rnd = run_backtest(cfg, ranker=RandomRanker("composite", 3, seed=1))
    assert set(out["metrics"]) == {"total_return", "cagr", "volatility", "sharpe", "max_drawdown"}
    assert len(rnd["results"]) == len(out["results"])
