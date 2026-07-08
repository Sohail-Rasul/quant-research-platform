from app.backtesting.portfolio import Portfolio
from app.strategies.strategy_state import StrategyState
import pandas as pd

class BacktestEngine:
    def __init__(self,strategy,prices_df,metadata_df,initial_capital:float,transaction_cost:float = 0.0):
        self.strategy = strategy
        self.prices_df = prices_df
        self.metadata_df = metadata_df
        self.portfolio = Portfolio(initial_capital)
        self.transaction_cost = transaction_cost
        self.trade_log = []

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

    def _sell(self,date,ticker:str, shares:int, price: float):
        trade_value = shares*price
        trade_cost = trade_value*self.transaction_cost

        total_gain = trade_value - trade_cost

        self.portfolio.cash += total_gain
        self.portfolio.sell(ticker,shares)

        self.trade_log.append(
            {
                "date":date,
                "action": "SELL",
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


    def _initialize_portfolio(self,date,current_prices: dict[str,float]):

        historical_data = self._get_historical_data(date)
        state = StrategyState(date=date, historical_data=historical_data, tickers = [], selected_tickers=[], metadata=self.metadata_df,)

        weights = self.strategy.generate_weights(state)

        portfolio_value = self.portfolio.cash

        for ticker,weight in weights.items():

            allocation = portfolio_value * weight
            effective_budget = (allocation /(1 + self.transaction_cost))

            price = current_prices[ticker]

            shares = int(effective_budget/price)

            if shares>0:
                self._buy(date,ticker,shares,price)


    #To convert price dataframe to dictionary for faster lookups
    def _prepare_price_data(self):
        price_data = {}

        for index ,row in self.prices_df.iterrows():
            date = row["date"]
            if date not in price_data:
                price_data[date]={}

            ticker = row["ticker"]
            price = float(row["adj_close"])

            price_data[date][ticker] = price

        self.price_data = price_data

        self.price_matrix = (self.prices_df.pivot(
            index = "date",
            columns = "ticker",
            values = "adj_close"
        ))


    def _rebalance(self,date,current_prices: dict[str,float]):
        historical_data = self._get_historical_data(date)
        state = StrategyState(
            date=date,
            historical_data=historical_data,
            tickers=[],
            selected_tickers=[],
            metadata=self.metadata_df,
        )

        #Generate new weights
        weights = self.strategy.generate_weights(state)
        
        #Current Portfolio Value
        portfolio_value = (self.portfolio.total_value(current_prices))

        #Shares Being completely sold
        for ticker in list(self.portfolio.positions):
            if ticker not in weights:
                shares = (self.portfolio.positions[ticker].shares)

                price = current_prices[ticker]

                self._sell(date,ticker,shares,price)
        
        
        for ticker,weight in weights.items():
            #Target Shares
            target_value = portfolio_value * weight
            effective_target = (target_value /(1 + self.transaction_cost))

            price = current_prices[ticker]
            target_shares = int(effective_target / price)

            #Current Shares
            if ticker in self.portfolio.positions:
                current_shares = self.portfolio.positions[ticker].shares
            else:
                current_shares =0
            
            #Share Difference
            share_difference = target_shares - current_shares

            #Buy OR Sell 
            if share_difference < 0:
                self._sell(date,ticker,abs(share_difference),price)
            elif share_difference >0:
                self._buy(date,ticker,share_difference,price)
        
        
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
            raise ValueError("No price data available")
        
        warmup = max(indicator.warmup_period for indicator in self.strategy.indicators)

        if len(dates) < warmup:
            raise ValueError(
                f"Not enough historical data. "
                f"Need at least {warmup} rows, "
                f"but only {len(dates)} are available."
            )

        first_date = dates[warmup] 
        previous_month = (first_date.year, first_date.month)

        self._initialize_portfolio(first_date,
            self.price_data[first_date]
        )

        equity_curve = []

        for date in dates[warmup:]:

            current_month = (date.year,date.month)
            current_prices = self.price_data[date]

            #Run Rebalance
            if current_month != previous_month:
                self._rebalance(date,current_prices)
                previous_month = current_month
            
            portfolio_value = (
                self.portfolio.total_value(
                    current_prices
                )
            )

            equity_curve.append(
                {
                    "date": date,
                    "portfolio_value": portfolio_value
                }
            )

        return pd.DataFrame(equity_curve)
