def compute_composite_score(momentum_z,volatility_z,size_z):
    momentum_dict={}
    volatility_dict = {}
    size_dict={}

    composite_scores = []

    for stock in momentum_z:
        momentum_dict[stock[0]] = stock[3]
    
    for stock in volatility_z:
        volatility_dict[stock[0]] = stock[3]
    
    for stock in size_z:
        size_dict[stock[0]] = stock[3]

    common_tickers = (
        set(momentum_dict.keys())
        &
        set(volatility_dict.keys())
        &
        set(size_dict.keys())
    )


    for ticker in common_tickers:
        mom=momentum_dict[ticker]
        vol=volatility_dict[ticker]
        size=size_dict[ticker]

        score = mom - vol - size

        composite_scores.append((ticker,mom,vol,size,score))

        
    composite_scores.sort(
        key=lambda x: x[4],
        reverse=True
    )

    return composite_scores

