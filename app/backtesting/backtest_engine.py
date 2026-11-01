from app.backtesting.portfolio import Portfolio
from app.strategies.strategy_state import StrategyState
import pandas as pd

class BacktestEngine:
    def __init__(self,strategy,prices_df,metadata_df,initial_capital:float,transaction_cost:float = 0.0,rebalance_frequency: str = "monthly",delisting_haircut: float = 0.0,delisting_grace_days: int = 30):
        self.strategy = strategy
        self.prices_df = prices_df
        self.metadata_df = metadata_df
        self.portfolio = Portfolio(initial_capital)
        self.transaction_cost = transaction_cost
        self.rebalance_frequency = rebalance_frequency
        self.trade_log = []

        # NEW: last price seen for every ticker so far. Used ONLY to value
        # positions on days when a held stock has no price row (data gap or
        # delisting). Trading still only happens at real prices.
        self.last_known_prices = {}

        # NEW: delisting handling. If a stock's price data ENDS (more than
        # `delisting_grace_days` before the end of the dataset) while it is held,
        # it is force-sold at its last price * (1 - delisting_haircut) instead of
        # sitting in the portfolio frozen forever. Real delistings often end far
        # below the last traded price, so treat `delisting_haircut` as a
        # sensitivity parameter (0.0 = sell at last price, 1.0 = total loss).
        self.delisting_haircut = delisting_haircut
        self.delisting_grace_days = delisting_grace_days
        self.delisting_log = []  # (date, ticker, shares, sale_price)

        # NEW: (date, ticker) pairs where a held stock had no price that day
        # and was valued at its last known price. Check this after a run.
        self.stale_price_log = []

        self._prepare_price_data()

    def _buy(self,date, ticker:str, shares: int, price: float):
        trade_value = shares*price
        trade_cost = (trade_value*self.transaction_cost)

        total_cost = trade_value + trade_cost

        self.portfolio.cash -= total_cost
        self.portfolio.buy(ticker,shares)

        self.trade_log.append(
            {
                "date": date,
                "action": "BUY",
                "ticker": ticker,
                "shares": shares,
                "price": price,
                "trade_value": trade_value,
                "transaction_cost": trade_cost,
                "cash_after": self.portfolio.cash
            }
        )

    def _sell(self,date,ticker:str, shares:int, price: float, action: str = "SELL"):
        trade_value = shares*price
        trade_cost = trade_value*self.transaction_cost

        total_gain = trade_value - trade_cost

        self.portfolio.cash += total_gain
        self.portfolio.sell(ticker,shares)

        self.trade_log.append(
            {
                "date":date,
                "action": action,
                "ticker": ticker,
                "shares": shares,
                "price": price,
                "trade_value": trade_value,
                "transaction_cost": trade_cost,
                "cash_after": self.portfolio.cash
            }
        )

    #HELPER FUNCTION: To Return Historical Data up to a certain date
    def _get_historical_data(self,current_date):
        return self.price_matrix.loc[:current_date]

    # NEW: same idea as _get_historical_data, but for volume instead of price.
    # Needed so a liquidity filter can see historical traded volume.
    def _get_historical_volume(self,current_date):
        return self.volume_matrix.loc[:current_date]


    def _initialize_portfolio(
        self,
        signal_date,
        execution_date,
        execution_prices: dict[str, float]
    ):
        historical_data = self._get_historical_data(signal_date)

        state = StrategyState(
            date=signal_date,
            historical_data=historical_data,
            tickers=[],
            selected_tickers=[],
            metadata=self.metadata_df,
            volume_data=self._get_historical_volume(signal_date),  # NEW: for liquidity filter
        )

        weights = self.strategy.generate_weights(state)

        portfolio_value = self.portfolio.cash

        for ticker, weight in weights.items():

            if ticker not in execution_prices:
                continue

            allocation = portfolio_value * weight
            effective_budget = allocation / (1 + self.transaction_cost)

            price = execution_prices[ticker]

            shares = int(effective_budget / price)

            if shares > 0:
                self._buy(
                    execution_date,
                    ticker,
                    shares,
                    price
                )

    #To convert price dataframe to dictionary for faster lookups
    def _prepare_price_data(self):
        # PERF: replaces a row-by-row iterrows() loop (~18s for 454 stocks).
        # Output is identical: {date: {ticker: float_price}}.
        df = self.prices_df
        price_data = {}
        for date, group in df.groupby("date", sort=False):
            price_data[date] = dict(zip(group["ticker"], group["adj_close"].astype(float)))

        self.price_data = price_data

        # NEW: last date each ticker has a price (used to detect delistings)
        self.last_price_date = df.groupby("ticker")["date"].max().to_dict()
        self.dataset_end = df["date"].max()

        self.price_matrix = (self.prices_df.pivot(
            index = "date",
            columns = "ticker",
            values = "adj_close"
        ))

        # NEW: volume matrix, built the same way as price_matrix, so a
        # liquidity filter can compute historical traded value (price * volume).
        self.volume_matrix = (self.prices_df.pivot(
            index = "date",
            columns = "ticker",
            values = "volume"
        ))


    def _get_rebalance_period(self, date):
        if self.rebalance_frequency == "monthly":
            return (date.year, date.month)

        elif self.rebalance_frequency == "quarterly":
            quarter = (date.month - 1) // 3 + 1
            return (date.year, quarter)

        else:
            raise ValueError(
                f"Unsupported rebalance frequency: "
                f"{self.rebalance_frequency}"
            )

    def _rebalance(
        self,
        signal_date,
        execution_date,
        execution_prices: dict[str, float]
    ):
        historical_data = self._get_historical_data(signal_date)

        state = StrategyState(
            date=signal_date,
            historical_data=historical_data,
            tickers=[],
            selected_tickers=[],
            metadata=self.metadata_df,
            volume_data=self._get_historical_volume(signal_date),  # NEW: for liquidity filter
        )

        # Generate new target weights using information
        # available only up to signal_date.
        weights = self.strategy.generate_weights(state)

        # Portfolio value immediately before execution.
        # CHANGED: value with last-known prices as a fallback, so one missing
        # price day for a held stock no longer aborts the whole backtest.
        # Orders below still execute only at real prices (execution_prices).
        valuation_prices = {**self.last_known_prices, **self.price_data[execution_date]}

        portfolio_value = self.portfolio.total_value(valuation_prices)

        # Sell positions that are no longer selected.
        for ticker in list(self.portfolio.positions):

            if ticker not in weights:

                shares = self.portfolio.positions[ticker].shares

                if ticker in execution_prices:
                    price = execution_prices[ticker]

                    self._sell(
                        execution_date,
                        ticker,
                        shares,
                        price
                    )

        # Move existing positions toward target weights.
        pending_buys = []

        for ticker, weight in weights.items():

            if ticker not in execution_prices:
                continue

            target_value = portfolio_value * weight
            effective_target = target_value / (1 + self.transaction_cost)

            price = execution_prices[ticker]

            target_shares = int(effective_target / price)

            if ticker in self.portfolio.positions:
                current_shares = self.portfolio.positions[ticker].shares
            else:
                current_shares = 0

            share_difference = target_shares - current_shares

            if share_difference < 0:

                self._sell(
                    execution_date,
                    ticker,
                    abs(share_difference),
                    price
                )

            elif share_difference > 0:
                # FIX: buys used to execute immediately, in dict order, so a buy
                # could run BEFORE a later sell had raised the cash for it. Collect
                # buys here and run them only after ALL sells are done (below).
                pending_buys.append((ticker, price, share_difference))

        # FIX: cap every buy by cash actually on hand. Previously target sizes were
        # based on pre-trade portfolio value and ignored the transaction cost paid
        # on the sells, so cash could go slightly NEGATIVE (free, interest-free
        # leverage of roughly cost x turnover). Now cash can never drop below zero.
        for ticker, price, share_difference in pending_buys:
            affordable = int(self.portfolio.cash / (price * (1 + self.transaction_cost)))
            shares_to_buy = min(share_difference, affordable)

            if shares_to_buy > 0:
                self._buy(
                    execution_date,
                    ticker,
                    shares_to_buy,
                    price
                )
        
        
    def get_trade_log(self):

        trades = pd.DataFrame(self.trade_log)

        return trades.round({
            "price": 2,
            "trade_value": 2,
            "transaction_cost": 2,
            "cash_after": 2
        })


    def run(self):

        dates = sorted(self.price_data.keys())

        if not dates:
            raise ValueError("No price data available.")

        # FIX: Not every Strategy has an `.indicators` list (e.g. BuyAndHoldStrategy
        # does not). The old code did `max(ind.warmup_period for ind in self.strategy.indicators)`
        # which raised AttributeError for such strategies, crashing the buy-and-hold benchmark.
        # This now falls back to warmup=1 (no warmup needed) when there are no indicators.
        warmup = max(
            (
                getattr(indicator, "warmup_period", 1)
                for indicator in getattr(self.strategy, "indicators", [])
            ),
            default=1,
        )

        if len(dates) <= warmup:
            raise ValueError(
                f"Not enough historical data. "
                f"Need more than {warmup} rows, "
                f"but only {len(dates)} are available."
            )

        # --------------------------------------------------
        # INITIAL SIGNAL
        # --------------------------------------------------

        signal_index = warmup - 1
        execution_index = warmup

        signal_date = dates[signal_index]
        execution_date = dates[execution_index]

        self._initialize_portfolio(
            signal_date=signal_date,
            execution_date=execution_date,
            execution_prices=self.price_data[execution_date]
        )

        equity_curve = []

        previous_month = (
            execution_date.year,
            execution_date.month
        )

        # --------------------------------------------------
        # BACKTEST LOOP
        # --------------------------------------------------

        for i in range(execution_index, len(dates)):

            date = dates[i]

            current_prices = self.price_data[date]

            # NEW: remember the latest real price of every ticker, and record
            # any held stock that has no price today (valued at last price).
            self.last_known_prices.update(current_prices)

            # NEW: force-sell held stocks whose price history has ended (delisted)
            for held_ticker in list(self.portfolio.positions):
                last_date = self.last_price_date.get(held_ticker)
                if (
                    last_date is not None
                    and date > last_date
                    and (self.dataset_end - last_date).days > self.delisting_grace_days
                ):
                    shares = self.portfolio.positions[held_ticker].shares
                    sale_price = self.last_known_prices[held_ticker] * (1 - self.delisting_haircut)
                    self._sell(date, held_ticker, shares, sale_price, action="DELIST_SELL")
                    self.delisting_log.append((date, held_ticker, shares, sale_price))

            for held_ticker in self.portfolio.positions:
                if held_ticker not in current_prices:
                    self.stale_price_log.append((date, held_ticker))

            # --------------------------------------------------
            # MONTHLY REBALANCE
            # --------------------------------------------------

            current_month = (
                date.year,
                date.month
            )

            if current_month != previous_month:

                # Previous trading day is the signal date.
                signal_date = dates[i - 1]

                self._rebalance(
                    signal_date=signal_date,
                    execution_date=date,
                    execution_prices=current_prices
                )

                previous_month = current_month

            # --------------------------------------------------
            # MARK PORTFOLIO TO MARKET
            # --------------------------------------------------

            # CHANGED: use last-known-price fallback (see note above).
            portfolio_value = self.portfolio.total_value(
                self.last_known_prices
            )

            equity_curve.append(
                {
                    "date": date,
                    "portfolio_value": portfolio_value
                }
            )

        return pd.DataFrame(equity_curve)
