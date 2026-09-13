import psycopg


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
):
    result = connection.execute(
        '''
        INSERT INTO market_snapshots (
            collection_started_at,
            collection_finished_at,
            token_id,
            currency_id,
            side
        )
        VALUES (%s, %s, %s, %s, %s)
        RETURNING id;
        ''',
        (
            collection_started_at,
            collection_finished_at,
            token_id,
            currency_id,
            side,
        ),
    ).fetchone()

    return result[0]


def save_order(connection, snapshot_id, order):
    connection.execute(
        '''
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
            last_quantity,
            quantity,
            executed_quantity,
            latest_release_time,
            latest_pay_time,
            remark
        )
        VALUES (
            %s, %s, %s, %s, %s, %s, %s, %s, %s,
            %s, %s, %s, %s, %s, %s, %s, %s
        );
        ''',
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
            order['last_quantity'],
            order['quantity'],
            order['executed_quantity'],
            order['latest_release_time'],
            order['latest_pay_time'],
            order['remark'],
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
    with connect_to_database() as connection:
        snapshot_id = create_snapshot(
            connection,
            token_id,
            currency_id,
            side,
            collection_started_at,
            collection_finished_at,
        )

        for order in orders:
            save_order(
                connection,
                snapshot_id,
                order,
            )

    return snapshot_id
