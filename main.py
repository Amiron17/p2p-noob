from bybit import get_orders
from collector import collect_market_snapshot
from database import save_market_snapshot


# V1 — current best qualified order
user_amount = '10000'
payment_method = 'bank_transfer'

# обосновать кол-во сделок и рейтинг впоследствии
qualified_orders = get_orders(user_amount, payment_method)
best_order = qualified_orders[0]

print('BEST QUALIFIED ORDER')
print(f"Merchant: {best_order['merchant']}")
print(f"Merchant ID: {best_order['merchant_id']}")
print(f"Order ID: {best_order['order_id']}")
print(f"Price: {best_order['price']}")
print(f"Limits: {best_order['min_amount']} - {best_order['max_amount']}")
print(f"Orders: {best_order['recent_order_num']}")
print(f"Execute rate: {best_order['recent_execute_rate']}")
print(f"Payment method: {payment_method}")
print(
    f"Additional verification: "
    f"{'Yes' if best_order['verification_required'] else 'No'}"
)

if best_order['verification_required']:
    print(f"Verification amount: {best_order['verification_amount']}")
    print(f"Verification labels: {best_order['verification_labels']}")