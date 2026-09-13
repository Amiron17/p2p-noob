from datetime import datetime, timezone
from bybit import fetch_orders, normalize_orders


def collect_market_snapshot() -> tuple[list[dict], datetime, datetime]:
    url = 'https://www.bybit.com/x-api/fiat/otc/item/online'

    page = 1
    page_size = 100

    collection_started_at = datetime.now(timezone.utc)

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

    items = fetch_orders(url, payload)

    print(f'Page {page}: ')
    print(f'{len(items)} orders')

    collection_finished_at = datetime.now(timezone.utc)

    orders = normalize_orders(items)

    return orders, collection_started_at, collection_finished_at


    # Старая версия с pagination.
    # Пока не удаляем — просто оставляем закомментированной.
    #
    # items_by_id = {}
    #
    # collection_started_at = datetime.now(timezone.utc)
    #
    # while True:
    #     payload = {
    #         'amount': '',
    #         'authMaker': True,
    #         'bulkMaker': False,
    #         'canTrade': True,
    #         'countryCode': '',
    #         'currencyId': 'RUB',
    #         'itemRegion': 1,
    #         'page': str(page),
    #         'payment': [],
    #         'paymentPeriod': [],
    #         'side': '1',
    #         'size': str(page_size),
    #         'sortStrategyCode': 'DEFAULT_SELL',
    #         'sortType': 'OVERALL_RANKING',
    #         'tokenId': 'USDT',
    #         'tradeWith': False,
    #         'userId': '',
    #         'vaMaker': False,
    #         'verificationFilter': 0,
    #     }
    #
    #     items = fetch_orders(url, payload)
    #
    #     print(f'Page {page}: ')
    #     print(f'{len(items)} orders')
    #
    #     if not items:
    #         break
    #
    #     for item in items:
    #         items_by_id[item['id']] = item
    #
    #     if len(items) < page_size:
    #         break
    #
    #     page += 1
    #
    # collection_finished_at = datetime.now(timezone.utc)
    #
    # all_items = list(items_by_id.values())
    # orders = normalize_orders(all_items)
    #
    # return orders, collection_started_at, collection_finished_at
