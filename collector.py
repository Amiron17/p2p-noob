from bybit import fetch_orders, normalize_orders


def collect_market_snapshot(amount: str) -> list[dict]:
    url = 'https://www.bybit.com/x-api/fiat/otc/item/online'

    page = 1
    page_size = 100
    all_items = []

    while True:
        payload = {
            'amount': amount,
            'authMaker': True,
            'bulkMaker': False,
            'canTrade': True,
            'countryCode': '',
            'currencyId': 'RUB',
            'itemRegion': 1,
            'page': str(page),
            'payment': [],
            'paymentPeriod': [],
            'side': '1',
            'size': str(page_size),
            'sortStrategyCode': 'DEFAULT_SELL',
            'sortType': 'OVERALL_RANKING',
            'tokenId': 'USDT',
            'tradeWith': False,
            'userId': '',
            'vaMaker': False,
            'verificationFilter': 0,
        }

        items = fetch_orders(url, payload)

        if not items:
            break

        all_items.extend(items)

        if len(items) < page_size:
            break

        page += 1

    orders = normalize_orders(all_items)

    return orders