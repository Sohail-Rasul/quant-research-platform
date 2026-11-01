from dataclasses import dataclass


@dataclass
class StrategyConfig:

    # Universe
    tickers: list[str]

    # Backtest period
    start_date: str
    end_date: str

    # Capital / costs
    initial_capital: float = 1_000_000

    # CHANGED: default was 0.0001 (1 bps), which is unrealistically low for
    # Indian equities once you include brokerage + STT + slippage/market impact,
    # especially for the small/momentum names this strategy favors. 0.0025 (25 bps)
    # is a more realistic floor for a reasonably liquid large/mid-cap name.
    # Still adjust this per your actual broker/cost structure — use the
    # dashboard's Transaction Cost input to test sensitivity (see test #6
    # in the audit report: vary this and watch how much CAGR moves).
    transaction_cost: float = 0.0025

    # Indicator parameters
    momentum_lookback: int = 63
    volatility_lookback: int = 63

    # Factor model
    momentum_weight: float = 0.6
    volatility_weight: float = -0.2
    size_weight: float = -0.2

    # Ranking
    top_n: int = 1

    # Weighting
    weighting_method: str = "inverse_volatility"

    # Rebalancing
    rebalance_frequency: str = "monthly"

    # NEW: Liquidity filter (addresses audit finding: no liquidity filter
    # existed, allowing selection of thinly-traded stocks). Set
    # min_avg_traded_value = 0 to disable the filter entirely.
    # Default of ₹1 crore (10,000,000) is a starting point, not a researched
    # number for your specific universe/capital size — tune it.
    liquidity_lookback: int = 20
    min_avg_traded_value: float = 10_000_000

    # NEW (survivorship-bias work):
    # Keep only the K most-traded stocks as of each signal date (0 = disabled).
    # A point-in-time universe using only data that existed on that date.
    top_liquid_universe: int = 0

    # Loss applied when a held stock's price history ends (delisting).
    # 0.0 = sold at last price, 1.0 = total loss. Only matters once delisted
    # stocks exist in your prices table; run it at several values.
    delisting_haircut: float = 0.0

    # Use the index_membership table (sql/003) so each date only sees stocks
    # that were actually index members then. Needs data you import yourself.
    use_point_in_time_universe: bool = False