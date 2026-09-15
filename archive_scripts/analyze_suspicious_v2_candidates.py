import csv

import psycopg


PASSWORD_FILE = r'C:\Users\MainUser\Desktop\postgreSQL_password.txt'
REPLAY_FILE = 'v1_v2_replay_results.csv'
OUTPUT_FILE = 'suspicious_v2_candidates_history.csv'

USER_AMOUNT = 10000
PAYMENT_ID = '14'
MIN_ORDERS = 500
MIN_COMPLETION_RATE = 98


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


def read_suspicious_cases():
    with open(
        REPLAY_FILE,
        'r',
        encoding='utf-8-sig',
        newline='',
    ) as file:
        rows = list(csv.DictReader(file))

    cases = []

    for row in rows:
        if row['result'] != 'MISMATCH':
            continue

        if float(row['v2_price']) >= float(row['v1_price']):
            continue

        cases.append(row)

    return cases


def get_candidate_identity(connection, snapshot_id, order_id):
    return connection.execute(
        '''
        SELECT
            merchant_id,
            merchant
        FROM market_orders
        WHERE snapshot_id = %s
          AND order_id = %s;
        ''',
        (
            snapshot_id,
            order_id,
        ),
    ).fetchone()


def get_nearby_snapshots(connection, snapshot_id):
    return connection.execute(
        '''
        WITH target AS (
            SELECT collection_started_at
            FROM market_snapshots
            WHERE id = %s
        )
        SELECT
            id,
            collection_started_at,
            collection_finished_at
        FROM market_snapshots
        WHERE collection_started_at BETWEEN
              (SELECT collection_started_at FROM target) - INTERVAL '10 minutes'
          AND (SELECT collection_started_at FROM target) + INTERVAL '10 minutes'
        ORDER BY collection_started_at;
        ''',
        (snapshot_id,),
    ).fetchall()


def get_exact_order(connection, snapshot_id, order_id):
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
            payments
        FROM market_orders
        WHERE snapshot_id = %s
          AND order_id = %s;
        ''',
        (
            snapshot_id,
            order_id,
        ),
    ).fetchone()


def get_merchant_best(connection, snapshot_id, merchant_id):
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
            payments
        FROM market_orders
        WHERE snapshot_id = %s
          AND merchant_id = %s
        ORDER BY price
        LIMIT 1;
        ''',
        (
            snapshot_id,
            merchant_id,
        ),
    ).fetchone()


def get_replay_best(connection, snapshot_id):
    return connection.execute(
        '''
        SELECT
            order_id,
            merchant_id,
            merchant,
            price
        FROM market_orders
        WHERE snapshot_id = %s

          AND min_amount <= %s
          AND max_amount >= %s

          AND recent_order_num >= %s
          AND recent_execute_rate >= %s

          AND (
              payments @> %s::jsonb
              OR payments @> %s::jsonb
          )

        ORDER BY price
        LIMIT 1;
        ''',
        (
            snapshot_id,
            USER_AMOUNT,
            USER_AMOUNT,
            MIN_ORDERS,
            MIN_COMPLETION_RATE,
            f'["{PAYMENT_ID}"]',
            f'[{PAYMENT_ID}]',
        ),
    ).fetchone()


def payment_matches(payments):
    if payments is None:
        return False

    return (
        PAYMENT_ID in payments
        or int(PAYMENT_ID) in payments
    )


def eligibility(order):
    if order is None:
        return {
            'amount_ok': False,
            'payment_ok': False,
            'quality_ok': False,
            'eligible': False,
        }

    amount_ok = (
        float(order[3]) <= USER_AMOUNT <= float(order[4])
    )

    payment_ok = payment_matches(order[7])

    quality_ok = (
        int(order[5]) >= MIN_ORDERS
        and float(order[6]) >= MIN_COMPLETION_RATE
    )

    return {
        'amount_ok': amount_ok,
        'payment_ok': payment_ok,
        'quality_ok': quality_ok,
        'eligible': (
            amount_ok
            and payment_ok
            and quality_ok
        ),
    }


cases = read_suspicious_cases()
rows = []

with connect_to_database() as connection:
    for case in cases:
        target_snapshot_id = int(case['snapshot_id'])
        candidate_order_id = case['v2_order_id']

        identity = get_candidate_identity(
            connection,
            target_snapshot_id,
            candidate_order_id,
        )

        merchant_id = identity[0]
        merchant_name = identity[1]

        nearby_snapshots = get_nearby_snapshots(
            connection,
            target_snapshot_id,
        )

        print()
        print('=' * 90)
        print(
            f'TARGET mismatch snapshot={target_snapshot_id} | '
            f'V1={case["v1_merchant"]} {case["v1_price"]} | '
            f'V2={case["v2_merchant"]} {case["v2_price"]}'
        )
        print(
            f'Candidate order_id={candidate_order_id} | '
            f'merchant_id={merchant_id}'
        )
        print()

        for snapshot in nearby_snapshots:
            snapshot_id = snapshot[0]
            started_at = snapshot[1]

            exact_order = get_exact_order(
                connection,
                snapshot_id,
                candidate_order_id,
            )

            merchant_best = get_merchant_best(
                connection,
                snapshot_id,
                merchant_id,
            )

            replay_best = get_replay_best(
                connection,
                snapshot_id,
            )

            exact_checks = eligibility(exact_order)
            merchant_checks = eligibility(merchant_best)

            exact_price = (
                float(exact_order[2])
                if exact_order is not None
                else ''
            )

            merchant_order_id = (
                merchant_best[0]
                if merchant_best is not None
                else ''
            )

            merchant_price = (
                float(merchant_best[2])
                if merchant_best is not None
                else ''
            )

            replay_best_order_id = (
                replay_best[0]
                if replay_best is not None
                else ''
            )

            replay_best_merchant_id = (
                replay_best[1]
                if replay_best is not None
                else ''
            )

            replay_best_merchant = (
                replay_best[2]
                if replay_best is not None
                else ''
            )

            replay_best_price = (
                float(replay_best[3])
                if replay_best is not None
                else ''
            )

            is_target = snapshot_id == target_snapshot_id

            rows.append({
                'target_snapshot_id': target_snapshot_id,
                'target_v1_merchant': case['v1_merchant'],
                'target_v1_price': case['v1_price'],
                'candidate_merchant': merchant_name,
                'candidate_order_id': candidate_order_id,

                'snapshot_id': snapshot_id,
                'snapshot_started_at': started_at,
                'is_target_snapshot': is_target,

                'exact_order_present': exact_order is not None,
                'exact_order_price': exact_price,
                'exact_amount_ok': exact_checks['amount_ok'],
                'exact_payment_ok': exact_checks['payment_ok'],
                'exact_quality_ok': exact_checks['quality_ok'],
                'exact_eligible': exact_checks['eligible'],

                'same_merchant_present': merchant_best is not None,
                'same_merchant_order_id': merchant_order_id,
                'same_merchant_price': merchant_price,
                'same_merchant_eligible': merchant_checks['eligible'],

                'replay_best_order_id': replay_best_order_id,
                'replay_best_merchant_id': replay_best_merchant_id,
                'replay_best_merchant': replay_best_merchant,
                'replay_best_price': replay_best_price,

                'candidate_is_replay_best': (
                    replay_best_order_id == candidate_order_id
                ),
                'same_merchant_is_replay_best': (
                    replay_best_merchant_id == merchant_id
                ),
            })

            marker = ' <-- TARGET' if is_target else ''

            if exact_order is None:
                exact_text = 'exact order ABSENT'
            else:
                exact_text = (
                    f'exact={exact_price:.2f} '
                    f'eligible={exact_checks["eligible"]}'
                )

            if merchant_best is None:
                merchant_text = 'merchant ABSENT'
            else:
                merchant_text = (
                    f'merchant_best={merchant_price:.2f} '
                    f'eligible={merchant_checks["eligible"]}'
                )

            if replay_best is None:
                replay_text = 'replay_best=NONE'
            else:
                replay_text = (
                    f'replay_best={replay_best_merchant} '
                    f'{replay_best_price:.2f}'
                )

            print(
                f'{started_at} | snapshot={snapshot_id} | '
                f'{exact_text} | '
                f'{merchant_text} | '
                f'{replay_text}'
                f'{marker}'
            )


if rows:
    fieldnames = list(rows[0].keys())

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
        writer.writerows(rows)

    print()
    print(
        f'Full history saved to: '
        f'{OUTPUT_FILE}'
    )
else:
    print('No suspicious cases found.')
