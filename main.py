from bybit import get_orders
from collector import collect_market_snapshot

min_orders = 500
min_completion_rate = 98
suitable_orders = get_orders(min_orders, min_completion_rate)

if len(suitable_orders) == 0:
    print('No suitable orders found')
else:
    print('BEST ORDERS:')
    print()
    for order in suitable_orders[:3]:
        print(f"Merchant: {order['merchant']}")
        print(f"Price: {order['price']}")
        print(f"Limits: {order['min_amount']} - {order['max_amount']}")
        print(f"Orders: {order['recent_order_num']}")
        print(f"Execute rate: {order['recent_execute_rate']}")
        print('---')



snapshot = collect_market_snapshot('100000')

print(f'Collected orders: {len(snapshot)}')
print(snapshot[:3])