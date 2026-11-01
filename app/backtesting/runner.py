from app.data.loaders import load_prices, load_metadata, load_membership, load_all_tickers
from app.backtesting.backtest_engine import BacktestEngine
from app.backtesting.strategy_config import StrategyConfig

from app.analytics.reports import generate_results

from app.universe.user_universe import UserUniverse

from app.indicators.momentum_indicator import MomentumIndicator
from app.indicators.volatility_indicator import VolatilityIndicator
from app.indicators.size_indicator import SizeIndicator

from app.factor_models.composite_factor_model import CompositeFactorModel

from app.filters.no_filter import NoFilter
from app.filters.liquidity_filter import LiquidityFilter
from app.filters.top_liquidity_filter import TopLiquidityFilter
from app.universe.point_in_time_universe import PointInTimeUniverse

from app.ranking.topNranker import TopNRanker

from app.weighting.inverse_volatility_weight import InverseVolatilityWeight
from app.weighting.equal_weight import EqualWeight

from app.strategies.pipeline_strategy import PipelineStrategy


def run_backtest(config : StrategyConfig, ranker=None):
    # `ranker` is optional: pass e.g. RandomRanker to run baseline experiments
    # (see scripts/backtests/run_bias_checks.py). Default behaviour is unchanged.
    tickers = config.tickers
    membership = None

    if config.use_point_in_time_universe:
        # Load every stock that was EVER an index member and has prices,
        # and let PointInTimeUniverse decide who is eligible on each date.
        membership = load_membership()
        if membership.empty:
            raise ValueError(
                "use_point_in_time_universe is on but index_membership is empty. "
                "Import data first: python scripts/stocks_metadata/import_membership.py <file.csv>"
            )
        tickers = sorted(set(membership["ticker"]) & set(load_all_tickers()))

    prices = load_prices(
        tickers = tickers,
        start_date=config.start_date,
        end_date = config.end_date
    )

    metadata = load_metadata(
        tickers=tickers
    )

    # -----------------------------
    # CREATE STRATEGY
    # -----------------------------

    

    if membership is not None:
        universe = PointInTimeUniverse(membership[membership["ticker"].isin(tickers)])
    else:
        universe = UserUniverse(tickers)

    indicators = [
        MomentumIndicator(config.momentum_lookback),
        VolatilityIndicator(config.volatility_lookback),
        SizeIndicator()
    ]

    factor_model = CompositeFactorModel(
        factor_weights={
            "momentum": config.momentum_weight,
            "volatility": config.volatility_weight,
            "size": config.size_weight
        }
    )

    filters = [NoFilter()]

    # CHANGED: liquidity rules now DEFINE the universe, so they run before
    # scoring (universe_filters) and z-scores are computed only across
    # investable stocks. Set min_avg_traded_value = 0 / top_liquid_universe = 0
    # to disable (old behaviour).
    universe_filters = []

    if config.min_avg_traded_value > 0:
        universe_filters.append(
            LiquidityFilter(
                lookback_days=config.liquidity_lookback,
                min_avg_traded_value=config.min_avg_traded_value
            )
        )

    if config.top_liquid_universe > 0:
        universe_filters.append(
            TopLiquidityFilter(
                lookback_days=config.liquidity_lookback,
                top_k=config.top_liquid_universe
            )
        )

    if ranker is None:
        ranker = TopNRanker(
            indicator="composite",
            n=config.top_n,
            ascending=False
        )

    if config.weighting_method == "equal":
        weighting = EqualWeight()

    elif config.weighting_method == "inverse_volatility":
        weighting = InverseVolatilityWeight(
            indicator="volatility"
        )

    else:
        raise ValueError(
            f"Unknown weighting method: {config.weighting_method}"
        )


    strategy = PipelineStrategy(
        universe=universe,
        indicators=indicators,
        filters=filters,
        universe_filters=universe_filters,
        ranker=ranker,
        weighting=weighting,
        factor_model=factor_model
    )

    # -----------------------------
    # RUN BACKTEST
    # -----------------------------

    engine = BacktestEngine(
        strategy=strategy,
        prices_df=prices,
        metadata_df=metadata,
        initial_capital=config.initial_capital,
        transaction_cost=config.transaction_cost,
        rebalance_frequency=config.rebalance_frequency,
        delisting_haircut=config.delisting_haircut
    )

    results = engine.run()

    # Daily returns
    results["returns"] = (
        results["portfolio_value"].pct_change()
    )

    # Trade log
    trades = engine.get_trade_log()

    # Analytics
    metrics = generate_results(results)

    return {
        "results": results,
        "metrics": metrics,
        "trades": trades,
        "engine": engine
    }

if __name__ == "__main__":

    config = StrategyConfig(
        tickers=[
            "RELIANCE.NS",
            "TCS.NS",
            "INFY.NS"
        ],
        start_date="2020-01-01",
        end_date="2024-01-01"
    )

    output = run_backtest(config)

    print(output["results"].head())
    print(output["results"].tail())

    print("\nMetrics:")
    print(output["metrics"])

    print("\nTrades:")
    print(output["trades"].head())

    print("\nFinal Portfolio:")
    print(output["engine"].portfolio.positions)