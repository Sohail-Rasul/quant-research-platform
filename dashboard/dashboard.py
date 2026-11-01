import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


import streamlit as st

from app.backtesting.runner import run_backtest
from app.backtesting.strategy_config import StrategyConfig
from app.data.loaders import load_all_tickers


st.set_page_config(
    page_title="Quant Research Platform",
    layout="wide"
)

st.title("Quant Research Platform")
st.caption("Indian Equities Quantitative Research Dashboard")


# ============================================================
# STRATEGY CONFIGURATION
# ============================================================

st.header("Strategy Configuration")


# Universe
st.subheader("Universe")

available_tickers = load_all_tickers()

selected_tickers = st.multiselect(
    "Select stocks",
    options=available_tickers,
    default=["RELIANCE.NS",
        "TCS.NS",
        "INFY.NS"]
)


# Backtest period
st.subheader("Backtest Period")

col1, col2 = st.columns(2)

with col1:
    start_date = st.date_input(
        "Start Date",
        value=None
    )

with col2:
    end_date = st.date_input(
        "End Date",
        value=None
    )


# Indicator parameters
st.subheader("Indicators")

col1, col2 = st.columns(2)

with col1:
    momentum_lookback = st.number_input(
        "Momentum Lookback",
        min_value=1,
        value=63,
        step=1
    )

with col2:
    volatility_lookback = st.number_input(
        "Volatility Lookback",
        min_value=1,
        value=63,
        step=1
    )


# Factor weights
st.subheader("Factor Weights")

col1, col2, col3 = st.columns(3)

with col1:
    momentum_weight = st.number_input(
        "Momentum Weight",
        value=0.6,
        step=0.1
    )

with col2:
    volatility_weight = st.number_input(
        "Volatility Weight",
        value=-0.2,
        step=0.1
    )

with col3:
    size_weight = st.number_input(
        "Size Weight",
        value=-0.2,
        step=0.1
    )


# Ranking
st.subheader("Ranking")

top_n = st.number_input(
    "Number of Stocks",
    min_value=1,
    value=1,
    step=1
)

# Weighting

st.subheader("Weighting")

weighting_method = st.selectbox(
    "Weighting Method",
    options=[
        "inverse_volatility",
        "equal"
    ],
    format_func=lambda x: {
        "inverse_volatility": "Inverse Volatility",
        "equal": "Equal Weight"
    }[x]
)

# Rebalancing

st.subheader("Rebalancing")

rebalance_frequency = st.selectbox(
    "Rebalance Frequency",
    options=[
        "monthly",
        "quarterly"
    ],
    format_func=lambda x: {
        "monthly": "Monthly",
        "quarterly": "Quarterly"
    }[x]
)

# NEW: Costs & Liquidity — added so the audit-flagged assumptions
# (unrealistically low flat transaction cost, no liquidity filter) are
# visible and tunable from the UI instead of hidden defaults in code.
st.subheader("Costs & Liquidity")

col1, col2 = st.columns(2)

with col1:
    transaction_cost = st.number_input(
        "Transaction Cost (as a fraction, e.g. 0.0025 = 25 bps)",
        min_value=0.0,
        value=0.0025,
        step=0.0005,
        format="%.4f",
        help="Applied to every buy/sell trade value. The old default (0.0001 = 1 bps) "
             "was unrealistically low for Indian equities once brokerage, STT, and "
             "slippage/market impact are considered — especially for small/illiquid names."
    )

with col2:
    min_avg_traded_value = st.number_input(
        "Min Avg Daily Traded Value (₹, 0 = disabled)",
        min_value=0,
        value=10_000_000,
        step=1_000_000,
        help="Stocks whose average daily traded value (price x volume) over the "
             "lookback window is below this are excluded before ranking. "
             "Set to 0 to disable (old behavior — no liquidity filter at all)."
    )

liquidity_lookback = st.number_input(
    "Liquidity Lookback (days)",
    min_value=1,
    value=20,
    step=1
)

# NEW: initial capital was previously fixed at the StrategyConfig default.
initial_capital = st.number_input(
    "Initial Capital (₹)",
    min_value=1000,
    value=1_000_000,
    step=100_000
)

# NEW: survivorship-bias controls
st.subheader("Survivorship Bias Controls")

top_liquid_universe = st.number_input(
    "Restrict to K most-traded stocks per date (0 = off)",
    min_value=0,
    value=0,
    step=50,
    help="Point-in-time universe: on each rebalance only the K stocks with the "
         "highest average traded value on that date are eligible. Uses no hindsight."
)

delisting_haircut = st.slider(
    "Loss when a held stock delists",
    min_value=0.0,
    max_value=1.0,
    value=0.0,
    step=0.05,
    help="0 = sold at last price, 1 = total loss. Only matters once delisted "
         "stocks exist in your prices table."
)

use_point_in_time_universe = st.checkbox(
    "Use index membership history (needs index_membership table)",
    value=False,
    help="Each date only sees stocks that were index members then. Ignores the stock picker above."
)


# Run button
run_backtest_button = st.button(
    "Run Backtest",
    type="primary"
)


# ============================================================
# RUN
# ============================================================

if run_backtest_button:

    if not selected_tickers and not use_point_in_time_universe:
        st.error("Select at least one stock.")

    # FIX: start/end dates default to None; comparing None >= None raised a
    # TypeError and crashed the app when Run was clicked without picking dates.
    elif start_date is None or end_date is None:
        st.error("Please select both a start date and an end date.")

    elif start_date >= end_date:
        st.error("Start date must be before end date.")

    elif top_n > len(selected_tickers) and not use_point_in_time_universe:
        st.error("Top-N cannot be greater than the number of selected stocks.")

    else:

        config = StrategyConfig(
            tickers=selected_tickers,
            start_date=str(start_date),
            end_date=str(end_date),

            momentum_lookback=momentum_lookback,
            volatility_lookback=volatility_lookback,

            momentum_weight=momentum_weight,
            volatility_weight=volatility_weight,
            size_weight=size_weight,

            top_n=top_n,

            weighting_method=weighting_method,

            rebalance_frequency=rebalance_frequency,

            # NEW: wired from the Costs & Liquidity section above
            initial_capital=initial_capital,
            top_liquid_universe=top_liquid_universe,
            delisting_haircut=delisting_haircut,
            use_point_in_time_universe=use_point_in_time_universe,
            transaction_cost=transaction_cost,
            min_avg_traded_value=min_avg_traded_value,
            liquidity_lookback=liquidity_lookback,
        )

        with st.spinner("Running backtest..."):
            output = run_backtest(config)


        results = output["results"]
        metrics = output["metrics"]
        trades = output["trades"]
        engine = output["engine"]


        # ====================================================
        # PERFORMANCE
        # ====================================================

        st.divider()

        st.header("Performance")

        col1, col2, col3, col4, col5 = st.columns(5)

        col1.metric(
            "Total Return",
            f"{metrics['total_return']:.2%}"
        )

        col2.metric(
            "CAGR",
            f"{metrics['cagr']:.2%}"
        )

        col3.metric(
            "Volatility",
            f"{metrics['volatility']:.2%}"
        )

        col4.metric(
            "Sharpe Ratio",
            f"{metrics['sharpe']:.2f}"
        )

        col5.metric(
            "Max Drawdown",
            f"{metrics['max_drawdown']:.2%}"
        )


        # ====================================================
        # EQUITY CURVE
        # ====================================================

        st.header("Equity Curve")

        st.line_chart(
            results.set_index("date")["portfolio_value"]
        )


        # ====================================================
        # DRAWDOWN
        # ====================================================

        st.header("Drawdown")

        drawdown = (
            results["portfolio_value"]
            / results["portfolio_value"].cummax()
            - 1
        )

        drawdown_df = results[["date"]].copy()
        drawdown_df["drawdown"] = drawdown.values

        st.line_chart(
            drawdown_df.set_index("date")["drawdown"]
        )


        # ====================================================
        # PORTFOLIO
        # ====================================================

        st.header("Portfolio")

        col1, col2 = st.columns(2)

        with col1:

            st.subheader("Current Positions")

            positions = []

            for ticker, position in engine.portfolio.positions.items():

                positions.append({
                    "Ticker": ticker,
                    "Shares": position.shares
                })

            st.dataframe(
                positions,
                use_container_width=True
            )


        with col2:

            st.subheader("Portfolio Summary")

            final_value = results["portfolio_value"].iloc[-1]
            cash = engine.portfolio.cash

            st.metric(
                "Final Portfolio Value",
                f"₹{final_value:,.2f}"
            )

            st.metric(
                "Cash",
                f"₹{cash:,.2f}"
            )


        # ====================================================
        # DATA QUALITY (new)
        # ====================================================

        if engine.stale_price_log or engine.delisting_log:
            st.warning(
                f"Data issues during this run: {len(engine.stale_price_log)} stock-days "
                f"valued at a stale price, {len(engine.delisting_log)} delisting sale(s)."
            )

        # ====================================================
        # TRADE LOG
        # ====================================================

        st.header("Trade Log")

        st.dataframe(
            trades,
            use_container_width=True
        )