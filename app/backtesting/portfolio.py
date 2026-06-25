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

            price = current_prices[position.ticker]

            total += (price*position.shares)

        return total
    
        

            


        


