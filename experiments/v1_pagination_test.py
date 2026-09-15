import time
from datetime import datetime
from pathlib import Path

import requests


USER_AMOUNT = '10000'
PAYMENT_ID = '14'  # bank_transfer
MIN_ORDERS = 400
MIN_COMPLETION_RATE = 99
PAGE_SIZE = 100
INTERVAL_SECONDS = 180

PROJECT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_DIR / 'data'
DATA_DIR.mkdir(exist_ok=True)
LOG_FILE = DATA_DIR / 'v1_pagination_test_log.txt'

URL = 'https://www.bybit.com/x-api/fiat/otc/item/online'


def fetch_page(page: int) -> tuple[list[dict], float]:
    payload = {
        'amount': USER_AMOUNT,
        'authMaker': True,
        'bulkMaker': False,
        'canTrade': True,
        'countryCode': '',
        'currencyId': 'RUB',
        'itemRegion': 1,
        'page': str(page),
        'payment': [PAYMENT_ID],
        'paymentPeriod': [],
        'side': '1',
        'size': str(PAGE_SIZE),
        'sortStrategyCode': 'DEFAULT_SELL',
        'sortType': 'OVERALL_RANKING',
        'tokenId': 'USDT',
        'tradeWith': False,
        'userId': '',
        'vaMaker': False,
        'verificationFilter': 0,
    }

    max_attempts = 3

    for attempt in range(1, max_attempts + 1):
        request_started_at = time.perf_counter()

        try:
            response = requests.post(
                URL,
                json=payload,
                timeout=15,
            )
            request_time = time.perf_counter() - request_started_at
            break

        except (requests.Timeout, requests.ConnectionError) as error:
            print(
                f'Bybit request failed on page {page}, '
                f'attempt {attempt}/{max_attempts}: {error}'
            )

            if attempt == max_attempts:
                raise

            time.sleep(attempt)

    response.raise_for_status()
    data = response.json()

    if data['result'] is None:
        raise RuntimeError(f'Bybit returned an error: {data}')

    return data['result']['items'], request_time


def normalize_order(item: dict, page: int) -> dict:
    return {
        'order_id': item['id'],
        'merchant': item['nickName'],
        'price': float(item['price']),
        'min_amount': float(item['minAmount']),
        'max_amount': float(item['maxAmount']),
        'recent_order_num': int(item['recentOrderNum']),
        'recent_execute_rate': float(item['recentExecuteRate']),
        'page': page,
    }


def filter_orders(orders: list[dict]) -> list[dict]:
    suitable_orders = []

    for order in orders:
        if (
            order['recent_order_num'] >= MIN_ORDERS
            and order['recent_execute_rate'] >= MIN_COMPLETION_RATE
        ):
            suitable_orders.append(order)

    return sorted(
        suitable_orders,
        key=lambda order: order['price'],
    )


def format_order(prefix: str, order: dict) -> str:
    return (
        f'{prefix}: '
        f'{order["merchant"]} | '
        f'{order["price"]:.2f} RUB | '
        f'order_id={order["order_id"]} | '
        f'orders={order["recent_order_num"]} | '
        f'rate={order["recent_execute_rate"]}% | '
        f'limits={order["min_amount"]:.0f}-{order["max_amount"]:.0f} | '
        f'page={order["page"]}'
    )


while True:
    cycle_started_at = time.perf_counter()
    checked_at = datetime.now().astimezone()

    lines = [f'[{checked_at:%Y-%m-%d %H:%M:%S}]']

    page = 1
    all_orders_by_id = {}
    total_raw_orders = 0
    duplicates = 0

    page_1_items, page_1_request_time = fetch_page(page)
    total_raw_orders += len(page_1_items)

    page_1_orders = [
        normalize_order(item, page=1)
        for item in page_1_items
    ]

    for order in page_1_orders:
        all_orders_by_id[order['order_id']] = order

    page_1_suitable = filter_orders(page_1_orders)

    lines.append(
        f'PAGE 1: raw={len(page_1_items)} | '
        f'request={page_1_request_time:.3f}s'
    )

    if page_1_suitable:
        page_1_best = page_1_suitable[0]
        lines.append(format_order('PAGE 1 BEST', page_1_best))
    else:
        page_1_best = None
        lines.append('PAGE 1 BEST: NO QUALIFIED ORDER')

    while len(page_1_items) == PAGE_SIZE:
        page += 1

        items, request_time = fetch_page(page)
        total_raw_orders += len(items)

        lines.append(
            f'PAGE {page}: raw={len(items)} | '
            f'request={request_time:.3f}s'
        )

        for item in items:
            order = normalize_order(item, page=page)

            if order['order_id'] in all_orders_by_id:
                duplicates += 1
                continue

            all_orders_by_id[order['order_id']] = order

        if len(items) < PAGE_SIZE:
            break

        page_1_items = items

    all_orders = list(all_orders_by_id.values())
    all_suitable = filter_orders(all_orders)

    lines.append(
        f'ALL PAGES: pages={page} | '
        f'raw={total_raw_orders} | '
        f'unique={len(all_orders)} | '
        f'duplicates={duplicates} | '
        f'qualified={len(all_suitable)}'
    )

    if all_suitable:
        all_best = all_suitable[0]
        lines.append(format_order('ALL PAGES BEST', all_best))
    else:
        all_best = None
        lines.append('ALL PAGES BEST: NO QUALIFIED ORDER')

    if page_1_best is None and all_best is None:
        result = 'RESULT: NO QUALIFIED ORDER'

    elif page_1_best is None and all_best is not None:
        result = (
            'RESULT: LATER PAGE FOUND FIRST QUALIFIED | '
            f'page={all_best["page"]}'
        )

    elif page_1_best is not None and all_best is None:
        result = 'RESULT: UNEXPECTED - PAGE 1 BEST DISAPPEARED'

    elif page_1_best['order_id'] == all_best['order_id']:
        result = 'RESULT: SAME BEST'

    else:
        improvement = (
            (page_1_best['price'] - all_best['price'])
            / page_1_best['price']
            * 100
        )

        result = (
            'RESULT: LATER PAGE BETTER | '
            f'page={all_best["page"]} | '
            f'improvement={improvement:+.3f}%'
        )

    lines.append(result)

    cycle_time = time.perf_counter() - cycle_started_at
    lines.append(f'CYCLE: {cycle_time:.3f}s')

    block = '\n'.join(lines)

    print(block)
    print()

    with open(LOG_FILE, 'a', encoding='utf-8') as file:
        file.write(block + '\n\n')

    sleep_seconds = max(
        0,
        INTERVAL_SECONDS - cycle_time,
    )

    time.sleep(sleep_seconds)
