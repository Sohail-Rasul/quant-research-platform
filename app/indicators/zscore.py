import numpy as np

def compute_zscore(factor_results):

    """
    Convert factor values into cross-sectional z-scores.

    Input:
        [
            (ticker, date, factor_value),
            ...
        ]

    Output:
        [
            (ticker, date, factor_value, zscore),
            ...
        ]
    """

    factor_values = []

    for stock in factor_results:
        factor_values.append(float(stock[2]))

    mean = np.mean(factor_values)
    std_dev = np.std(factor_values,ddof=1)
    if std_dev == 0:
        return [
            (
                stock[0],
                stock[1],
                stock[2],
                0.0
            )
            for stock in factor_results
        ]

    zscore_results = []

    for stock in factor_results:
        zscore = round((float(stock[2]) - mean) / std_dev, 6)

        zscore_results.append(
            (
                stock[0],
                stock[1],
                stock[2],
                zscore
            )
        )

    return zscore_results
        
