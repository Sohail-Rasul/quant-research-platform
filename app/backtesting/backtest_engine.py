from app.backtesting.portfolio import Portfolio
from app.backtesting.position import Position
import pandas as pd

class BacktestEngine:
    def __init__(self,strategy,prices_df,initial_capital:float):
        self.strategy = strategy
        self.prices_df = prices_df
        self.portfolio = Portfolio(initial_capital)

        self._prepare_price_data()

    def _initialize_portfolio(self,current_prices: dict[str,float]):

        weights = self.strategy.generate_weights()

        portfolio_value = self.portfolio.cash

        for ticker,weight in weights.items():
            allocation = portfolio_value * weight
            price = current_prices[ticker]

            shares = int(allocation/price)

            if shares>0:
                position = Position(ticker = ticker,shares = shares)
                self.portfolio.add_position(position)

                cash_used = shares * price

                self.portfolio.cash -= cash_used

    #To conver price dataframe to dictionary for faster lookups
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


    def run(self):

        dates = sorted(self.price_data.keys())
        if not dates:
            raise ValueError("No price data available")

        first_date = dates[0]

        self._initialize_portfolio(
            self.price_data[first_date]
        )

        equity_curve = []

        for date in dates:

            current_prices = self.price_data[date]

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
