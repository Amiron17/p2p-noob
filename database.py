import time

import psycopg
from psycopg.types.json import Jsonb


PASSWORD_FILE = r'C:\Users\MainUser\Desktop\postgreSQL_password.txt'


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


def create_snapshot(
    connection,
    token_id,
    currency_id,
    side,
    collection_started_at,
    collection_finished_at,
    order_count,
    collection_duration_seconds,
):
    result = connection.execute(
        """
        INSERT INTO market_snapshots (
            collection_started_at,
            collection_finished_at,
            token_id,
            currency_id,
            side,
            order_count,
            collection_duration_seconds
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        RETURNING id;
        """,
        (
            collection_started_at,
            collection_finished_at,
            token_id,
            currency_id,
            side,
            order_count,
            collection_duration_seconds,
        ),
    ).fetchone()

    return result[0]


def save_order(connection, snapshot_id, order):
    connection.execute(
        """
        INSERT INTO market_orders (
            snapshot_id,
            order_id,
            merchant_id,
            merchant,
            price,
            min_amount,
            max_amount,
            recent_order_num,
            recent_execute_rate,
            order_created_at,
            payment_period,
            payments,
            last_quantity,
            quantity,
            executed_quantity,
            latest_release_time,
            latest_pay_time,
            remark,
            verification_required,
            verification_amount,
            verification_labels,
            trading_preferences
        )
        VALUES (
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
        );
        """,
        (
            snapshot_id,
            order['order_id'],
            order['merchant_id'],
            order['merchant'],
            order['price'],
            order['min_amount'],
            order['max_amount'],
            order['recent_order_num'],
            order['recent_execute_rate'],
            order['created_at'],
            order['payment_period'],
            Jsonb(order['payments']),
            order['last_quantity'],
            order['quantity'],
            order['executed_quantity'],
            order['latest_release_time'],
            order['latest_pay_time'],
            order['remark'],
            order['verification_required'],
            order['verification_amount'],
            Jsonb(order['verification_labels']),
            Jsonb(order['trading_preferences']),
        ),
    )


def save_market_snapshot(
    orders,
    token_id,
    currency_id,
    side,
    collection_started_at,
    collection_finished_at,
):
    total_started_at = time.perf_counter()

    order_count = len(orders)

    collection_duration_seconds = (
        collection_finished_at - collection_started_at
    ).total_seconds()

    connect_started_at = time.perf_counter()

    connection = connect_to_database()

    connect_time = time.perf_counter() - connect_started_at

    transaction_started_at = time.perf_counter()

    with connection:
        create_snapshot_started_at = time.perf_counter()

        snapshot_id = create_snapshot(
            connection,
            token_id,
            currency_id,
            side,
            collection_started_at,
            collection_finished_at,
            order_count,
            collection_duration_seconds,
        )

        create_snapshot_time = (
            time.perf_counter() - create_snapshot_started_at
        )

        save_orders_started_at = time.perf_counter()

        for order in orders:
            save_order(
                connection,
                snapshot_id,
                order,
            )

        save_orders_time = time.perf_counter() - save_orders_started_at

    transaction_time = time.perf_counter() - transaction_started_at
    total_time = time.perf_counter() - total_started_at

    if order_count > 0:
        average_order_save_ms = (
            save_orders_time / order_count * 1000
        )
    else:
        average_order_save_ms = 0.0

    performance = {
        'connect_time': connect_time,
        'create_snapshot_time': create_snapshot_time,
        'save_orders_time': save_orders_time,
        'transaction_time': transaction_time,
        'total_time': total_time,
        'average_order_save_ms': average_order_save_ms,
        'saved_orders': order_count,
    }

    return snapshot_id, performance
