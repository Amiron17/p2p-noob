import requests
import time

def get_orders(min_orders: int, min_completion_rate: float) -> list[dict]:
    url = 'https://www.bybit.com/x-api/fiat/otc/item/online'

    payload = {
        'amount': '',
        'authMaker': True,
        'bulkMaker': False,
        'canTrade': True,
        'countryCode': '',
        'currencyId': 'RUB',
        'itemRegion': 1,
        'page': '1',
        'payment': [],
        'paymentPeriod': [],
        'side': '1',
        'size': '10',
        'sortStrategyCode': 'DEFAULT_SELL',
        'sortType': 'OVERALL_RANKING',
        'tokenId': 'USDT',
        'tradeWith': False,
        'userId': '',
        'vaMaker': False,
        'verificationFilter': 0,
    }

    items = fetch_orders(url, payload)
    orders = normalize_orders(items)
    suitable_orders = filter_orders(orders, min_orders, min_completion_rate)

    return suitable_orders


def normalize_orders(items: list[dict]) -> list[dict]:
    orders = []

    for item in items:
        order = {
            # Identity
            'order_id': item['id'],
            'merchant_id': item['userMaskId'],
            'merchant': item['nickName'],

            # Price and limits
            'price': float(item['price']),
            'min_amount': float(item['minAmount']),
            'max_amount': float(item['maxAmount']),

            # Merchant stats
            'recent_order_num': int(item['recentOrderNum']),
            'recent_execute_rate': float(item['recentExecuteRate']),

            # Order context
            'created_at': int(item['createDate']),
            'payment_period': int(item['paymentPeriod']),

            # Potentially useful for liquidity analysis
            'last_quantity': float(item['lastQuantity']),
            'quantity': float(item['quantity']),
            'executed_quantity': float(item['executedQuantity']),

            # Potentially useful merchant timing signals
            'latest_release_time': int(item['latestReleaseTime']),
            'latest_pay_time': int(item['latestPayTime']),

            # Raw trading conditions text
            'remark': item['remark'],
        }

        orders.append(order)

    return orders


def filter_orders(orders: list[dict], min_orders: int, min_completion_rate: float) -> list[dict]:
    suitable_orders = []

    for order in orders:
        if order['recent_order_num'] >= min_orders and order['recent_execute_rate'] >= min_completion_rate:
            suitable_orders.append(order)

    return suitable_orders


def fetch_orders(url: str, payload: dict) -> list[dict]:
    max_attempts = 3
    for attempt in range(1, max_attempts + 1):
        try:
            response = requests.post(url, json=payload, timeout=15)
            break
            
        except (requests.Timeout, requests.ConnectionError) as error:
            print(f'Bybit request failed, attempt {attempt}/{max_attempts}: {error}')
            if attempt == max_attempts:
                raise

            time.sleep(attempt)

    response.raise_for_status()

    data = response.json()

    if data['result'] is None:
        raise RuntimeError(f'Bybit returned an error: {data}')

    items = data['result']['items']

    return items