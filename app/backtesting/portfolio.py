from app.backtesting.position import Position


#Storing Positions
class Portfolio:

    def __init__(self,initial_cash: float):
        self.cash = initial_cash
        self.positions: dict[str,Position] ={}

    def buy(self,ticker:str,shares:int):
        if shares<0:
            raise ValueError(f"Shares must be positive")
        
        if ticker in self.positions:
            self.positions[ticker].shares += shares
        else: 
            self.positions[ticker] = Position(ticker,shares)

    def sell(self,ticker:str,shares:int):
        if ticker not in self.positions:
            raise ValueError(f"{ticker} is not owned.")
        
        if shares<0:
            raise ValueError(f"Shares must be positive")

        position = self.positions[ticker]

        if shares > position.shares:
            raise ValueError(f"Cannot sell {shares} shares of {ticker}. Only {position.shares} owned.")
        
        position.shares -= shares
        if position.shares ==0:
            del self.positions[ticker]

    def total_value(self, current_prices: dict[str,float]) -> float:
        total = self.cash
        
        for position in self.positions.values():

            # FIX: current_prices[position.ticker] raised a bare KeyError if a
            # held ticker had no price row for this exact date (data gap), which
            # is confusing to debug. This makes the failure explicit instead.
            price = current_prices.get(position.ticker)
            if price is None:
                raise ValueError(
                    f"Missing price for held position '{position.ticker}' on this date "
                    f"— likely a data gap in the prices table that needs to be resolved."
                )

            total += (price*position.shares)

        return total