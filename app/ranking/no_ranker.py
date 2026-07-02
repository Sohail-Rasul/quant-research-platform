from app.ranking.base_ranker import BaseRanker
from app.strategies.strategy_state import StrategyState

class NoRanker(BaseRanker):
    
    def rank(self, state : StrategyState):
        
        pass