from statistics import median

def get_price_context(orders: list[dict]) -> dict:
    prices = sorted(order['price'] for order in orders) # must-have after deduplication

    cheapest_price = prices[0]
    next_price = prices[1]
    median_price = median(prices)

    gap_to_next_pct = ((next_price - cheapest_price)/ next_price * 100)
    gap_to_median_pct = ((median_price - cheapest_price)/ median_price * 100)

    return {
        'cheapest_price': cheapest_price,
        'next_price': next_price,
        'median_price': median_price,
        'gap_to_next_pct': gap_to_next_pct,
        'gap_to_median_pct': gap_to_median_pct,
    }