CREATE TABLE IF NOT EXISTS market_snapshots (
    id BIGSERIAL PRIMARY KEY,

    collection_started_at TIMESTAMPTZ NOT NULL,
    collection_finished_at TIMESTAMPTZ NOT NULL,

    token_id TEXT NOT NULL,
    currency_id TEXT NOT NULL,
    side TEXT NOT NULL,

    order_count INTEGER,
    collection_duration_seconds NUMERIC(10, 3)
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
    payments JSONB,

    last_quantity NUMERIC(18, 4),
    quantity NUMERIC(18, 4),
    executed_quantity NUMERIC(18, 4),

    latest_release_time BIGINT,
    latest_pay_time BIGINT,

    remark TEXT,

    verification_required BOOLEAN,
    verification_amount NUMERIC(18, 2),
    verification_labels JSONB,
    trading_preferences JSONB,

    PRIMARY KEY (snapshot_id, order_id),

    FOREIGN KEY (snapshot_id)
        REFERENCES market_snapshots(id)
        ON DELETE CASCADE
);


CREATE INDEX IF NOT EXISTS idx_market_orders_merchant_snapshot
ON market_orders (merchant_id, snapshot_id);


CREATE INDEX IF NOT EXISTS idx_market_snapshots_started_at
ON market_snapshots (collection_started_at);