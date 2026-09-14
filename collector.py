import time
from datetime import datetime, timezone

from bybit import fetch_orders, normalize_orders


def collect_market_snapshot():
    total_started_at = time.perf_counter()

    url = 'https://www.bybit.com/x-api/fiat/otc/item/online'

    page = 1
    page_size = 100

    items_by_id = {}

    raw_order_count = 0
    dedup_time = 0.0
    page_fetch_times = []
    page_order_counts = []

    collection_started_at = datetime.now(timezone.utc)

    while True:
        payload = {
            'amount': '',
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

        page_fetch_started_at = time.perf_counter()

        items = fetch_orders(url, payload)

        page_fetch_time = time.perf_counter() - page_fetch_started_at

        page_fetch_times.append(page_fetch_time)
        page_order_counts.append(len(items))
        raw_order_count += len(items)

        print(
            f'Page {page}: {len(items)} orders | '
            f'fetch_time={page_fetch_time:.3f}s'
        )

        if not items:
            break

        dedup_started_at = time.perf_counter()

        for item in items:
            items_by_id[item['id']] = item

        dedup_time += time.perf_counter() - dedup_started_at

        if len(items) < page_size:
            break

        page += 1

    collection_finished_at = datetime.now(timezone.utc)

    unique_order_count = len(items_by_id)
    duplicate_count = raw_order_count - unique_order_count

    all_items = list(items_by_id.values())

    normalize_started_at = time.perf_counter()

    orders = normalize_orders(all_items)

    normalize_time = time.perf_counter() - normalize_started_at

    total_time = time.perf_counter() - total_started_at

    performance = {
        'page_fetch_times': page_fetch_times,
        'page_order_counts': page_order_counts,
        'fetch_total_time': sum(page_fetch_times),
        'dedup_time': dedup_time,
        'normalize_time': normalize_time,
        'total_time': total_time,
        'pages': len(page_fetch_times),
        'raw_orders': raw_order_count,
        'unique_orders': unique_order_count,
        'duplicates': duplicate_count,
    }

    return (
        orders,
        collection_started_at,
        collection_finished_at,
        performance,
    )
