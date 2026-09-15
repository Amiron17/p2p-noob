import time

from datetime import datetime, timezone

from bybit import get_orders, filter_orders
from reference import get_usd_rub_reference
from telegram_bot import send_telegram_message
from pathlib import Path
from urllib.parse import quote


user_amount = '10000'
payment_method = 'bank_transfer'
desired_edge = -2.00

interval_seconds = 60

DATA_DIR = Path(__file__).resolve().parent / 'data'
DATA_DIR.mkdir(exist_ok=True)
log_file = DATA_DIR / 'v1_gate_forward_test_log.txt'

sent_order_ids = set()


while True:
    cycle_started_at = time.perf_counter()

    reference, reference_performance = get_usd_rub_reference()

    qualified_orders, normalized_orders, bybit_performance = get_orders(
        user_amount,
        payment_method,
        return_normalized=True,
    )

    best_order = qualified_orders[0]

    baseline_orders = filter_orders(
        normalized_orders,
        min_orders=500,
        min_completion_rate=98,
    )
    baseline_orders = sorted(
        baseline_orders,
        key=lambda order: order['price'],
    )

    if baseline_orders:
        baseline_order = baseline_orders[0]
        gate_advantage = (
            (baseline_order['price'] - best_order['price'])
            / baseline_order['price']
            * 100
        )
        same_order = best_order['order_id'] == baseline_order['order_id']
    else:
        baseline_order = None
        gate_advantage = None
        same_order = False

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

    telegram_time = 0.0

    if (
        status == 'MATCH'
        and best_order['order_id'] not in sent_order_ids
    ):
        merchant_url = (
            'https://www.bybit.com/ru-RU/p2p/profile/'
            f'{best_order["merchant_id"]}/USDT/RUB/item'
        )

        bybit_deep_link = (
            'bybitapp://open/web?url='
            + quote(merchant_url, safe='')
        )

        app_url = (
            'https://app.bybit.com/inapp?by_dp='
            + quote(bybit_deep_link, safe='')
            + '&by_web_link='
            + quote(merchant_url, safe='')
        )

        telegram_message = (
            f'V1 MATCH\n\n'
            f'Merchant: {best_order["merchant"]}\n'
            f'P2P: {best_order["price"]:.2f} RUB\n'
            f'USD/RUB: {reference["rate"]:.5f}\n'
            f'Edge: {edge:+.3f}%\n'
            f'Target: {desired_edge:+.3f}%\n\n'
            f'Amount: {user_amount} RUB\n'
            f'Limits: {best_order["min_amount"]:.0f}-'
            f'{best_order["max_amount"]:.0f} RUB\n'
            f'Orders: {best_order["recent_order_num"]}\n'
            f'Completion rate: {best_order["recent_execute_rate"]}%\n'
            f'Order ID: {best_order["order_id"]}\n\n'
            f'Браузер: {merchant_url}\n'
            f'iPhone приложение: {app_url}'
        )

        telegram_time = send_telegram_message(
            telegram_message
        )

        sent_order_ids.add(
            best_order['order_id']
        )

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
        f'qualified_400_99={bybit_performance["qualified_orders"]} | '
        f'quote_age={quote_age:.0f}s | '
        f'reference={reference_performance["source"]}'
    )

    if baseline_order:
        gate_line = (
            f'GATE TEST: '
            f'400/99={best_order["merchant"]} {best_order["price"]:.2f} | '
            f'500/98={baseline_order["merchant"]} {baseline_order["price"]:.2f} | '
            f'qualified_500_98={len(baseline_orders)} | '
            f'advantage={gate_advantage:+.3f}% | '
            f'same_order={"YES" if same_order else "NO"}'
        )
    else:
        gate_line = (
            f'GATE TEST: '
            f'400/99={best_order["merchant"]} {best_order["price"]:.2f} | '
            f'500/98=NO CANDIDATE | '
            f'qualified_500_98=0 | '
            f'advantage=n/a | '
            f'same_order=NO'
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
        f'telegram={telegram_time:.3f}s | '
        f'cycle={cycle_time:.3f}s'
    )

    print(first_line)
    print(second_line)
    print(gate_line)
    print(third_line)
    print()

    with open(log_file, 'a', encoding='utf-8') as file:
        file.write(first_line + '\n')
        file.write(second_line + '\n')
        file.write(gate_line + '\n')
        file.write(third_line + '\n')
        file.write('\n')

    sleep_seconds = max(
        0,
        interval_seconds - cycle_time,
    )

    time.sleep(sleep_seconds)
