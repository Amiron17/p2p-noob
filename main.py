from bybit import get_orders
from collector import collect_market_snapshot
from database import save_market_snapshot
from analysis import get_market_support


# V1 collect current top orders with basic filters
user_amount = '10000'

# обосновать кол-во сделок и рейтинг впоследствии
eligible_orders = get_orders(user_amount, 'bank_transfer')

for order in eligible_orders[:3]:
    print(f"Merchant: {order['merchant']}")
    print(f"Price: {order['price']}")
    print(f"Limits: {order['min_amount']} - {order['max_amount']}")
    print(f"Orders: {order['recent_order_num']}")
    print(f"Execute rate: {order['recent_execute_rate']}")

    print(
        f"Additional verification: "
        f"{'Yes' if order['verification_required'] else 'No'}"
    )

    if order['verification_required']:
        print(f"Verification labels: {order['verification_labels']}")

    print('---')
