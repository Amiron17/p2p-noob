import csv
import re
from datetime import datetime, timedelta, timezone

import psycopg


PASSWORD_FILE = r'C:\Users\MainUser\Desktop\postgreSQL_password.txt'
V1_LOG_FILE = 'v1_night_log.txt'
OUTPUT_FILE = 'v1_v2_replay_results.csv'

USER_AMOUNT = 10000
PAYMENT_ID = '14'
MIN_ORDERS = 500
MIN_COMPLETION_RATE = 98

LOG_TIMEZONE = timezone(timedelta(hours=4))


FIRST_LINE_PATTERN = re.compile(
    r'^\[(?P<checked_at>[^\]]+)\] '
    r'(?P<status>MATCH|NO MATCH): '
    r'(?P<merchant>.*?) \| '
    r'P2P=(?P<price>[0-9.]+) \| '
)

SECOND_LINE_PATTERN = re.compile(
    r'^order_id=(?P<order_id>\S+)'
)


def connect_to_database():
    with open(PASSWORD_FILE, 'r', encoding='utf-8') as file:
        password = file.read().strip()

    return psycopg.connect(
        dbname='p2p_monitor',
        user='postgres',
        password=password,
        host='localhost',
        port=5432,
    )


def read_v1_checks():
    with open(V1_LOG_FILE, 'r', encoding='utf-8') as file:
        lines = file.read().splitlines()

    checks = []

    for index, line in enumerate(lines):
        first_match = FIRST_LINE_PATTERN.match(line)

        if not first_match:
            continue

        if index + 1 >= len(lines):
            continue

        second_match = SECOND_LINE_PATTERN.match(lines[index + 1])

        if not second_match:
            continue

        checked_at = datetime.strptime(
            first_match.group('checked_at'),
            '%Y-%m-%d %H:%M:%S',
        ).replace(tzinfo=LOG_TIMEZONE)

        checks.append({
            'checked_at': checked_at,
            'status': first_match.group('status'),
            'merchant': first_match.group('merchant'),
            'price': float(first_match.group('price')),
            'order_id': second_match.group('order_id'),
        })

    return checks


def find_overlapping_snapshot(connection, checked_at):
    return connection.execute(
        """
        SELECT
            id,
            collection_started_at,
            collection_finished_at
        FROM market_snapshots
        WHERE collection_started_at <= %s
          AND collection_finished_at >= %s
        ORDER BY collection_started_at DESC
        LIMIT 1;
        """,
        (
            checked_at,
            checked_at,
        ),
    ).fetchone()


def replay_snapshot(connection, snapshot_id):
    return connection.execute(
        """
        SELECT
            order_id,
            merchant,
            price,
            min_amount,
            max_amount,
            recent_order_num,
            recent_execute_rate,
            payments
        FROM market_orders
        WHERE snapshot_id = %s

          AND min_amount <= %s
          AND max_amount >= %s

          AND recent_order_num >= %s
          AND recent_execute_rate >= %s

          AND payments @> %s::jsonb

        ORDER BY price
        LIMIT 1;
        """,
        (
            snapshot_id,
            USER_AMOUNT,
            USER_AMOUNT,
            MIN_ORDERS,
            MIN_COMPLETION_RATE,
            f'["{PAYMENT_ID}"]',
        ),
    ).fetchone()


def classify_result(v1_check, replay_order):
    if replay_order is None:
        return 'NO_V2_CANDIDATE'

    replay_order_id = replay_order[0]
    replay_merchant = replay_order[1]
    replay_price = float(replay_order[2])

    same_order = replay_order_id == v1_check['order_id']
    same_merchant = replay_merchant == v1_check['merchant']
    same_price = abs(replay_price - v1_check['price']) < 0.0001

    if same_order and same_price:
        return 'EXACT'

    if same_order:
        return 'SAME_ORDER_DIFFERENT_PRICE'

    if same_merchant and same_price:
        return 'SAME_MERCHANT_PRICE'

    if same_price:
        return 'SAME_PRICE_DIFFERENT_ORDER'

    return 'MISMATCH'


checks = read_v1_checks()

results = []

with connect_to_database() as connection:
    for check in checks:
        snapshot = find_overlapping_snapshot(
            connection,
            check['checked_at'],
        )

        if snapshot is None:
            results.append({
                'checked_at': check['checked_at'].isoformat(),
                'snapshot_id': '',
                'v1_order_id': check['order_id'],
                'v1_merchant': check['merchant'],
                'v1_price': check['price'],
                'v2_order_id': '',
                'v2_merchant': '',
                'v2_price': '',
                'result': 'NO_OVERLAPPING_SNAPSHOT',
            })
            continue

        snapshot_id = snapshot[0]
        replay_order = replay_snapshot(
            connection,
            snapshot_id,
        )

        if replay_order is None:
            v2_order_id = ''
            v2_merchant = ''
            v2_price = ''
        else:
            v2_order_id = replay_order[0]
            v2_merchant = replay_order[1]
            v2_price = float(replay_order[2])

        results.append({
            'checked_at': check['checked_at'].isoformat(),
            'snapshot_id': snapshot_id,
            'v1_order_id': check['order_id'],
            'v1_merchant': check['merchant'],
            'v1_price': check['price'],
            'v2_order_id': v2_order_id,
            'v2_merchant': v2_merchant,
            'v2_price': v2_price,
            'result': classify_result(
                check,
                replay_order,
            ),
        })


fieldnames = [
    'checked_at',
    'snapshot_id',
    'v1_order_id',
    'v1_merchant',
    'v1_price',
    'v2_order_id',
    'v2_merchant',
    'v2_price',
    'result',
]

with open(OUTPUT_FILE, 'w', newline='', encoding='utf-8-sig') as file:
    writer = csv.DictWriter(
        file,
        fieldnames=fieldnames,
    )
    writer.writeheader()
    writer.writerows(results)


counts = {}

for result in results:
    result_type = result['result']
    counts[result_type] = counts.get(result_type, 0) + 1


print()
print('V1 -> V2 HISTORICAL REPLAY')
print(f'V1 checks parsed: {len(checks)}')
print()

for result_type in [
    'EXACT',
    'SAME_ORDER_DIFFERENT_PRICE',
    'SAME_MERCHANT_PRICE',
    'SAME_PRICE_DIFFERENT_ORDER',
    'MISMATCH',
    'NO_V2_CANDIDATE',
    'NO_OVERLAPPING_SNAPSHOT',
]:
    print(
        f'{result_type}: '
        f'{counts.get(result_type, 0)}'
    )


comparable = sum(
    1
    for result in results
    if result['result']
    not in {
        'NO_V2_CANDIDATE',
        'NO_OVERLAPPING_SNAPSHOT',
    }
)

exact = counts.get('EXACT', 0)

if comparable > 0:
    print()
    print(
        f'Exact match rate: '
        f'{exact / comparable * 100:.1f}% '
        f'({exact}/{comparable})'
    )


mismatches = [
    result
    for result in results
    if result['result']
    not in {
        'EXACT',
        'NO_OVERLAPPING_SNAPSHOT',
    }
]

if mismatches:
    print()
    print('FIRST 15 NON-EXACT RESULTS:')

    for result in mismatches[:15]:
        print(
            f'{result["checked_at"]} | '
            f'snapshot={result["snapshot_id"]} | '
            f'{result["result"]} | '
            f'V1={result["v1_merchant"]} '
            f'{result["v1_price"]} | '
            f'V2={result["v2_merchant"]} '
            f'{result["v2_price"]}'
        )


print()
print(f'Full results saved to: {OUTPUT_FILE}')
