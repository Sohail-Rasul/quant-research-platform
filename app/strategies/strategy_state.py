from dataclasses import dataclass, field
import pandas as pd


#This object represents the entire market as my strategy currently sees it
@dataclass
class StrategyState:

    date : pd.Timestamp

    historical_data : pd.DataFrame

    tickers: list[str]

    selected_tickers: list[str]


    indicator_results: dict = field(default_factory=dict) #default_factory=dict creates a new dictionary for every instance

    metadata: pd.DataFrame | None = None

    # NEW: historical volume, aligned the same way as historical_data (price).
    # Added to support a liquidity filter (avg traded value = price * volume).
    # Optional / defaults to None so existing code that doesn't use it is unaffected.
    volume_data: pd.DataFrame | None = None