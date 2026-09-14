import time
from datetime import datetime, timezone

from bybit import get_orders
from reference import get_usd_rub_reference


user_amount = '10000'
payment_method = 'bank_transfer'
desired_edge = -2.00

interval_seconds = 180

log_file = 'v1_night_log.txt'


while True:
    cycle_started_at = time.perf_counter()

    reference, reference_performance = get_usd_rub_reference()

    qualified_orders, bybit_performance = get_orders(
        user_amount,
        payment_method,
    )

    best_order = qualified_orders[0]

    edge = (
        (reference['rate'] - best_order['price'])
        / reference['rate']
        * 100
    )

    if edge >= desired_edge:
        status = 'MATCH'
    else:
        status = 'NO MATCH'

    checked_at = datetime.now().astimezone()

    quote_age = (
        datetime.now(timezone.utc)
        - reference['quote_timestamp']
    ).total_seconds()

    cycle_time = time.perf_counter() - cycle_started_at

    first_line = (
        f'[{checked_at:%Y-%m-%d %H:%M:%S}] '
        f'{status}: '
        f'{best_order["merchant"]} | '
        f'P2P={best_order["price"]:.2f} | '
        f'USD/RUB={reference["rate"]:.5f} | '
        f'edge={edge:+.3f}% | '
        f'target={desired_edge:+.3f}%'
    )

    second_line = (
        f'order_id={best_order["order_id"]} | '
        f'limits={best_order["min_amount"]:.0f}-{best_order["max_amount"]:.0f} | '
        f'orders={best_order["recent_order_num"]} | '
        f'rate={best_order["recent_execute_rate"]}% | '
        f'raw={bybit_performance["raw_orders"]} | '
        f'qualified={bybit_performance["qualified_orders"]} | '
        f'quote_age={quote_age:.0f}s'
    )

    third_line = (
        f'PERF: '
        f'reference_total={reference_performance["total_time"]:.3f}s | '
        f'reference_key_read={reference_performance["key_read_time"]:.4f}s | '
        f'reference_http={reference_performance["request_time"]:.3f}s | '
        f'reference_json={reference_performance["json_time"]:.4f}s | '
        f'reference_parse={reference_performance["parse_time"]:.4f}s | '
        f'bybit_total={bybit_performance["total_time"]:.3f}s | '
        f'bybit_fetch={bybit_performance["fetch_time"]:.3f}s | '
        f'normalize={bybit_performance["normalize_time"]:.4f}s | '
        f'filter={bybit_performance["filter_time"]:.4f}s | '
        f'sort={bybit_performance["sort_time"]:.4f}s | '
        f'cycle={cycle_time:.3f}s'
    )

    print(first_line)
    print(second_line)
    print(third_line)
    print()

    with open(log_file, 'a', encoding='utf-8') as file:
        file.write(first_line + '\n')
        file.write(second_line + '\n')
        file.write(third_line + '\n')
        file.write('\n')

    sleep_seconds = max(0, interval_seconds - cycle_time)
    time.sleep(sleep_seconds)
