import requests

def get_orders(min_orders, min_completion_rate):
    url = 'https://www.bybit.com/x-api/fiat/otc/item/online'

    payload = {
        'amount': '', # amount of money I paste
        'authMaker': True, # verified users
        'bulkMaker': False,
        'canTrade': True,
        'countryCode': "",
        'currencyId': "RUB",
        'itemRegion': 1,
        'page': "1",
        'payment': [],
        'paymentPeriod': [],
        'side': "1",
        'size': "10",
        'sortStrategyCode': "DEFAULT_SELL",
        'sortType': "OVERALL_RANKING", #from lowest to highest
        'tokenId': "USDT",
        'tradeWith': False,
        'userId': "",
        'vaMaker': False,
        'verificationFilter': 0
    }

    items = fetch_orders(url, payload)
    suitable_orders = filter_orders(items, min_orders, min_completion_rate)
    return suitable_orders

def filter_orders(items: list[dict], min_orders:int, min_completion_rate:int) -> list[dict]:
    suitable_orders = []
    orders = []
    for order in items:
        single_order = {
            'merchant': order['nickName'],
            'price': float(order['price']),
            'min_amount': float(order['minAmount']),
            'max_amount': float(order['maxAmount']),
            'recent_execute_rate': float(order['recentExecuteRate']),
            'order_num': int(order['recentOrderNum']),
        }
        orders.append(single_order)

        if int(order['recentOrderNum']) >= min_orders and int(order['recentExecuteRate']) >= min_completion_rate:
            suitable_order = {
                'merchant': order['nickName'],
                'price': float(order['price']),
                'min_amount': float(order['minAmount']),
                'max_amount': float(order['maxAmount']),
                'recent_execute_rate': float(order['recentExecuteRate']),
                'order_num': int(order['recentOrderNum']),
            }
            suitable_orders.append(suitable_order)
    print(len(orders))
    return suitable_orders

def fetch_orders(url:str, payload:dict) -> list[dict]:
    try:
        response = requests.post(url, json=payload, timeout=15)
        response.raise_for_status()

    except requests.RequestException as error:
        print(f'Bybit request failed: {error}')
        return []
    
    data = response.json()

    if data['result'] is None:
        raise RuntimeError(f'Bybit returned an error: {data}')

    items = data['result']['items']
    return items

