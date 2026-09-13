def get_cheapest_order_per_merchant(orders: list[dict]) -> list[dict]:
    cheapest_by_merchant = {}

    for order in orders:
        merchant_id = order['merchant_id']

        if merchant_id not in cheapest_by_merchant or order['price'] < cheapest_by_merchant[merchant_id]['price']:
            cheapest_by_merchant[merchant_id] = order

    return sorted(cheapest_by_merchant.values(), key=lambda order: order['price'])


def get_market_support(orders: list[dict]) -> dict:
    if not orders:
        raise ValueError('Cannot analyze an empty order list')

    merchant_orders = get_cheapest_order_per_merchant(orders)

    if len(merchant_orders) < 2:
        raise ValueError('At least two merchants are required for market support analysis')

    candidate = merchant_orders[0]

    nearest_merchants = []

    for order in merchant_orders[1:]:
        distance = order['price'] - candidate['price']
        distance_pct = distance / candidate['price'] * 100

        nearest_merchants.append({
            'merchant': order['merchant'],
            'merchant_id': order['merchant_id'],
            'price': order['price'],
            'distance': distance,
            'distance_pct': distance_pct,
        })

    merchant_gaps = []

    for index in range(len(merchant_orders) - 1):
        current_order = merchant_orders[index]
        next_order = merchant_orders[index + 1]

        gap = next_order['price'] - current_order['price']
        gap_pct = gap / current_order['price'] * 100

        merchant_gaps.append({
            'from_merchant': current_order['merchant'],
            'from_price': current_order['price'],
            'to_merchant': next_order['merchant'],
            'to_price': next_order['price'],
            'gap': gap,
            'gap_pct': gap_pct,
        })

    gap_values = [
        gap['gap_pct']
        for gap in merchant_gaps
    ]

    for gap in merchant_gaps:
        smaller_or_equal = sum(
            other_gap <= gap['gap_pct']
            for other_gap in gap_values
        )

        gap['percentile'] = (
            smaller_or_equal / len(gap_values) * 100
        )

    sorted_gaps = sorted(
        merchant_gaps,
        key=lambda gap: gap['gap_pct'],
        reverse=True,
    )

    for rank, gap in enumerate(sorted_gaps, start=1):
        gap['rank'] = rank

    candidate_merchant_gap = merchant_gaps[0]

    return {
        'candidate': candidate,
        'offer_count': len(orders),
        'merchant_count': len(merchant_orders),
        'nearest_merchants': nearest_merchants,
        'merchant_gaps': merchant_gaps,
        'candidate_merchant_gap': candidate_merchant_gap,
        'merchant_gap_count': len(merchant_gaps),
    }