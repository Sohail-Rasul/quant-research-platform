from app.backtesting.position import Position


#Storing Positions
class Portfolio:

    def __init__(self,initial_cash: float):
        self.cash = initial_cash
        self.positions: dict[str,Position] ={}

    
    def add_position(self, position:Position):
       if position.ticker in self.positions:
           raise ValueError(
               f"{position.ticker} already exists in portfolio"
            )
       
       self.positions[position.ticker] = position

    def remove_position(self, ticker:str):
        del self.positions[ticker]

    def total_value(self, current_prices: dict[str,float]) -> float:
        total = self.cash
        
        for position in self.positions.values():

            price = current_prices[position.ticker]

            total += (price*position.shares)

        return total
    
        


