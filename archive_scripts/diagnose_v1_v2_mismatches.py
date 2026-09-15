import csv
import json
import re
from datetime import datetime

import psycopg


PASSWORD_FILE = r'C:\Users\MainUser\Desktop\postgreSQL_password.txt'
REPLAY_FILE = 'v1_v2_replay_results.csv'
V1_LOG_FILE = 'v1_night_log.txt'
OUTPUT_FILE = 'v1_v2_mismatch_diagnostics.csv'

USER_AMOUNT = 10000
PAYMENT_ID = '14'
MIN_ORDERS = 500
MIN_COMPLETION_RATE = 98


FIRST_LINE_PATTERN = re.compile(
    r'^\[(?P<checked_at>[^\]]+)\] '
    r'(?P<status>MATCH|NO MATCH): '
    r'(?P<merchant>.*?) \| '
    r'P2P=(?P<price>[0-9.]+) \| '
)

SECOND_LINE_PATTERN = re.compile(
    r'^order_id=(?P<order_id>\S+) \| '
    r'limits=(?P<min_amount>[0-9.]+)-(?P<max_amount>[0-9.]+) \| '
    r'orders=(?P<recent_order_num>\d+) \| '
    r'rate=(?P<recent_execute_rate>[0-9.]+)% \| '
    r'raw=(?P<raw_orders>\d+) \| '
    r'qualified=(?P<qualified_orders>\d+)'
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


def read_v1_log():
    with open(V1_LOG_FILE, 'r', encoding='utf-8') as file:
        lines = file.read().splitlines()

    checks = {}

    for index, line in enumerate(lines):
        first_match = FIRST_LINE_PATTERN.match(line)

        if not first_match:
            continue

        if index + 1 >= len(lines):
            continue

        second_match = SECOND_LINE_PATTERN.match(lines[index + 1])

        if not second_match:
            continue

        checked_at = first_match.group('checked_at')

        checks[checked_at] = {
            'order_id': second_match.group('order_id'),
            'merchant': first_match.group('merchant'),
            'price': float(first_match.group('price')),
            'min_amount': float(second_match.group('min_amount')),
            'max_amount': float(second_match.group('max_amount')),
            'recent_order_num': int(second_match.group('recent_order_num')),
            'recent_execute_rate': float(
                second_match.group('recent_execute_rate')
            ),
            'raw_orders': int(second_match.group('raw_orders')),
            'qualified_orders': int(
                second_match.group('qualified_orders')
            ),
        }

    return checks


def read_mismatches():
    with open(
        REPLAY_FILE,
        'r',
        encoding='utf-8-sig',
        newline='',
    ) as file:
        rows = list(csv.DictReader(file))

    return [
        row
        for row in rows
        if row['result'] == 'MISMATCH'
    ]


def get_snapshot(connection, snapshot_id):
    return connection.execute(
        '''
        SELECT
            collection_started_at,
            collection_finished_at
        FROM market_snapshots
        WHERE id = %s;
        ''',
        (snapshot_id,),
    ).fetchone()


def get_order(connection, snapshot_id, order_id):
    return connection.execute(
        '''
        SELECT
            order_id,
            merchant,
            price,
            min_amount,
            max_amount,
            recent_order_num,
            recent_execute_rate,
            payments,
            verification_required,
            trading_preferences
        FROM market_orders
        WHERE snapshot_id = %s
          AND order_id = %s;
        ''',
        (
            snapshot_id,
            order_id,
        ),
    ).fetchone()


def payment_matches(payments):
    if payments is None:
        return False

    return (
        PAYMENT_ID in payments
        or int(PAYMENT_ID) in payments
    )


def order_checks(order):
    if order is None:
        return {
            'amount_ok': False,
            'payment_ok': False,
            'quality_ok': False,
        }

    min_amount = float(order[3])
    max_amount = float(order[4])
    recent_order_num = int(order[5])
    recent_execute_rate = float(order[6])
    payments = order[7]

    return {
        'amount_ok': (
            min_amount <= USER_AMOUNT <= max_amount
        ),
        'payment_ok': payment_matches(payments),
        'quality_ok': (
            recent_order_num >= MIN_ORDERS
            and recent_execute_rate >= MIN_COMPLETION_RATE
        ),
    }


def diagnose(v1_live, v1_snapshot, v2_snapshot):
    if v1_snapshot is None:
        return (
            'V1_ORDER_ABSENT_FROM_V2_SNAPSHOT',
            'Likely timing / market change during V2 crawl',
        )

    checks = order_checks(v1_snapshot)

    snapshot_price = float(v1_snapshot[2])

    if abs(snapshot_price - v1_live['price']) > 0.0001:
        return (
            'V1_ORDER_PRICE_CHANGED',
            'Same order exists, but its price changed between V1 and V2 observations',
        )

    if not checks['amount_ok']:
        return (
            'V1_ORDER_AMOUNT_STATE_CHANGED',
            'Same order exists, but snapshot min/max no longer includes 10000 RUB',
        )

    if not checks['payment_ok']:
        return (
            'V1_ORDER_PAYMENT_STATE_CHANGED',
            'Same order exists, but V2 snapshot payment data no longer includes bank_transfer',
        )

    if not checks['quality_ok']:
        return (
            'V1_ORDER_QUALITY_STATE_CHANGED',
            'Same order exists, but merchant stats crossed the 500/98 gate',
        )

    v2_price = float(v2_snapshot[2])

    if v2_price < v1_live['price']:
        if v1_live['raw_orders'] == 100:
            return (
                'V2_FOUND_CHEAPER_ELIGIBLE_ORDER',
                'Potential V1 first-page truncation (raw=100) or hidden Bybit filtering/ranking',
            )

        return (
            'V2_FOUND_CHEAPER_ELIGIBLE_ORDER',
            'Potential hidden Bybit filtering; V1 returned fewer than 100 raw orders',
        )

    return (
        'UNEXPLAINED',
        'Needs manual inspection',
    )


v1_checks = read_v1_log()
mismatches = read_mismatches()

diagnostic_rows = []

with connect_to_database() as connection:
    for mismatch in mismatches:
        checked_at_iso = mismatch['checked_at']
        checked_at = datetime.fromisoformat(checked_at_iso)
        checked_at_key = checked_at.strftime(
            '%Y-%m-%d %H:%M:%S'
        )

        v1_live = v1_checks[checked_at_key]

        snapshot_id = int(mismatch['snapshot_id'])

        snapshot = get_snapshot(
            connection,
            snapshot_id,
        )

        v1_snapshot = get_order(
            connection,
            snapshot_id,
            mismatch['v1_order_id'],
        )

        v2_snapshot = get_order(
            connection,
            snapshot_id,
            mismatch['v2_order_id'],
        )

        v1_checks_in_snapshot = order_checks(
            v1_snapshot
        )

        v2_checks_in_snapshot = order_checks(
            v2_snapshot
        )

        diagnosis, explanation = diagnose(
            v1_live,
            v1_snapshot,
            v2_snapshot,
        )

        diagnostic_rows.append({
            'checked_at': checked_at_iso,
            'snapshot_id': snapshot_id,
            'snapshot_started_at': snapshot[0],
            'snapshot_finished_at': snapshot[1],

            'v1_live_order_id': v1_live['order_id'],
            'v1_live_merchant': v1_live['merchant'],
            'v1_live_price': v1_live['price'],
            'v1_raw_orders': v1_live['raw_orders'],
            'v1_qualified_orders': v1_live['qualified_orders'],

            'v1_order_present_in_v2': v1_snapshot is not None,
            'v1_snapshot_price': (
                float(v1_snapshot[2])
                if v1_snapshot is not None
                else ''
            ),
            'v1_snapshot_amount_ok': (
                v1_checks_in_snapshot['amount_ok']
            ),
            'v1_snapshot_payment_ok': (
                v1_checks_in_snapshot['payment_ok']
            ),
            'v1_snapshot_quality_ok': (
                v1_checks_in_snapshot['quality_ok']
            ),

            'v2_replay_order_id': mismatch['v2_order_id'],
            'v2_replay_merchant': mismatch['v2_merchant'],
            'v2_replay_price': mismatch['v2_price'],
            'v2_amount_ok': v2_checks_in_snapshot['amount_ok'],
            'v2_payment_ok': v2_checks_in_snapshot['payment_ok'],
            'v2_quality_ok': v2_checks_in_snapshot['quality_ok'],
            'v2_payments': (
                json.dumps(v2_snapshot[7], ensure_ascii=False)
                if v2_snapshot is not None
                else ''
            ),
            'v2_verification_required': (
                v2_snapshot[8]
                if v2_snapshot is not None
                else ''
            ),
            'v2_trading_preferences': (
                json.dumps(
                    v2_snapshot[9],
                    ensure_ascii=False,
                )
                if v2_snapshot is not None
                else ''
            ),

            'diagnosis': diagnosis,
            'explanation': explanation,
        })


fieldnames = list(diagnostic_rows[0].keys())

with open(
    OUTPUT_FILE,
    'w',
    encoding='utf-8-sig',
    newline='',
) as file:
    writer = csv.DictWriter(
        file,
        fieldnames=fieldnames,
    )
    writer.writeheader()
    writer.writerows(diagnostic_rows)


print()
print('V1 / V2 MISMATCH DIAGNOSTICS')
print(f'Mismatches: {len(diagnostic_rows)}')
print()

for row in diagnostic_rows:
    print(
        f'{row["checked_at"]} | '
        f'snapshot={row["snapshot_id"]}'
    )

    print(
        f'  V1 live: '
        f'{row["v1_live_merchant"]} '
        f'{row["v1_live_price"]} | '
        f'raw={row["v1_raw_orders"]} | '
        f'qualified={row["v1_qualified_orders"]}'
    )

    if row['v1_order_present_in_v2']:
        print(
            f'  V1 order in V2: PRESENT | '
            f'price={row["v1_snapshot_price"]} | '
            f'amount={row["v1_snapshot_amount_ok"]} | '
            f'payment={row["v1_snapshot_payment_ok"]} | '
            f'quality={row["v1_snapshot_quality_ok"]}'
        )
    else:
        print(
            '  V1 order in V2: ABSENT'
        )

    print(
        f'  V2 replay: '
        f'{row["v2_replay_merchant"]} '
        f'{row["v2_replay_price"]}'
    )

    print(
        f'  => {row["diagnosis"]}'
    )

    print(
        f'     {row["explanation"]}'
    )

    print()


print(
    f'Full diagnostics saved to: '
    f'{OUTPUT_FILE}'
)
