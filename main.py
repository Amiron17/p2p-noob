from bybit import get_orders
from collector import collect_market_snapshot
from database import save_market_snapshot
from analysis import get_price_context

min_orders = 500
min_completion_rate = 98

# =================================== V1
# suitable_orders = get_orders(min_orders, min_completion_rate)

# if len(suitable_orders) == 0:
#     print('No suitable orders found')
# else:
#     print('BEST ORDERS:')
#     print()

#     for order in suitable_orders[:3]:
#         print(f"Merchant: {order['merchant']}")
#         print(f"Price: {order['price']}")
#         print(f"Limits: {order['min_amount']} - {order['max_amount']}")
#         print(f"Orders: {order['recent_order_num']}")
#         print(f"Execute rate: {order['recent_execute_rate']}")
#         print('---')


# =================================== V2
market_orders, collection_started_at, collection_finished_at = collect_market_snapshot('100000')
sorted_orders = sorted(market_orders, key=lambda order: order['price'])

for order in sorted_orders[:10]:
    print(order['price'], order['merchant'], order['merchant_id'])

price_context = get_price_context(market_orders)
print(price_context)
snapshot_id = save_market_snapshot(market_orders, token_id='USDT', currency_id='RUB', amount=100000, 
                                   collection_started_at=collection_started_at, 
                                   collection_finished_at=collection_finished_at,
                                )

print(f'Collected orders: {len(market_orders)}')
print(f'Saved snapshot: {snapshot_id}')