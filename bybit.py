import requests
import time
from pprint import pprint

PAYMENT_METHODS = {
    'mobile_top_up': '40',
    'cash_in_person': '90',
    'bank_transfer': '14',
    'cash_deposit_to_bank': '18',
    'pay_api': '784',
    'neopass_qr_payments_api': '824',
    'qr_pay_api': '825',
}

def get_orders(amount: str, payment_method: str) -> list[dict]:
    url = 'https://www.bybit.com/x-api/fiat/otc/item/online'

    payment_id = PAYMENT_METHODS[payment_method]

    payload = {
        'amount': amount,
        'authMaker': True,
        'bulkMaker': False,
        'canTrade': True,
        'countryCode': '',
        'currencyId': 'RUB',
        'itemRegion': 1,
        'page': '1',
        'payment': [payment_id],
        'paymentPeriod': [],
        'side': '1',
        'size': '100',
        'sortStrategyCode': 'DEFAULT_SELL',
        'sortType': 'OVERALL_RANKING',
        'tokenId': 'USDT',
        'tradeWith': False,
        'userId': '',
        'vaMaker': False,
        'verificationFilter': 0,
    }

    items = fetch_orders(url, payload)
    pprint(items[0])
    orders = normalize_orders(items)
    suitable_orders = filter_orders(orders)

    if not suitable_orders:
        raise ValueError('No suitable orders found')

    # на всякий пожарный, если вдруг что сьедет после фильтрации и нормализации. время это не сжирает
    suitable_orders = sorted(suitable_orders, key=lambda order: order['price'])

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

            # Additional verification requirements
            'verification_required': bool(item['verificationOrderSwitch']),
            'verification_labels': item['verificationOrderLabels'],
        }

        orders.append(order)

    return orders


def filter_orders(orders: list[dict]) -> list[dict]:
    min_orders = 500
    min_completion_rate = 98
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
