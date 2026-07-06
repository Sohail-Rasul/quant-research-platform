import pandas as pd

# Calculate Normalized Score: (Value - Mean) / Std Deviation
def calculate_zscore(series : pd.Series) -> pd.Series:
    series = series.astype(float)

    mean = series.mean()
    std = series.std(ddof=1)

    if std == 0:
        return series*0
    
    return (series - mean) / std