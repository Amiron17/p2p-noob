CREATE TABLE IF NOT EXISTS market_snapshots (
    id BIGSERIAL PRIMARY KEY,
    collection_started_at TIMESTAMPTZ NOT NULL,
    collection_finished_at TIMESTAMPTZ NOT NULL,
    token_id TEXT NOT NULL,
    currency_id TEXT NOT NULL,
    amount NUMERIC(18, 2) NOT NULL
);

CREATE TABLE IF NOT EXISTS market_orders (
    snapshot_id BIGINT NOT NULL,
    order_id TEXT NOT NULL,
    merchant_id TEXT NOT NULL,
    merchant TEXT NOT NULL,

    price NUMERIC(18, 4) NOT NULL,
    min_amount NUMERIC(18, 2) NOT NULL,
    max_amount NUMERIC(18, 2) NOT NULL,

    recent_order_num INTEGER NOT NULL,
    recent_execute_rate NUMERIC(5, 2) NOT NULL,

    order_created_at BIGINT,
    payment_period INTEGER,

    last_quantity NUMERIC(18, 4),
    quantity NUMERIC(18, 4),
    executed_quantity NUMERIC(18, 4),

    latest_release_time BIGINT,
    latest_pay_time BIGINT,

    remark TEXT,

    PRIMARY KEY (snapshot_id, order_id),

    FOREIGN KEY (snapshot_id)
        REFERENCES market_snapshots(id)
        ON DELETE CASCADE
);