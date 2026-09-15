import time

from datetime import datetime
from pathlib import Path

from collector import collect_market_snapshot
from database import save_market_snapshot
from reference import get_usd_rub_reference

interval_seconds = 140

DATA_DIR = Path(__file__).resolve().parent / 'data'
DATA_DIR.mkdir(exist_ok=True)
log_file = DATA_DIR / 'v2_collector_log.txt'


while True:
    run_started_at = time.perf_counter()

    print()
    print('COLLECTION STARTED')

    reference, reference_performance = get_usd_rub_reference()

    (
        orders,
        collection_started_at,
        collection_finished_at,
        collector_performance,
    ) = collect_market_snapshot()

    snapshot_id, database_performance = save_market_snapshot(
        orders=orders,
        token_id='USDT',
        currency_id='RUB',
        side='1',
        collection_started_at=collection_started_at,
        collection_finished_at=collection_finished_at,
        reference_rate=reference['rate'],
        reference_quote_timestamp=reference['quote_timestamp'],
        reference_fetched_at=reference['fetched_at'],
    )

    cycle_time = time.perf_counter() - run_started_at
    checked_at = datetime.now().astimezone()

    quote_age_at_fetch = (
        reference['fetched_at']
        - reference['quote_timestamp']
    ).total_seconds()

    first_line = (
        f'[{checked_at:%Y-%m-%d %H:%M:%S}] '
        f'SNAPSHOT SAVED: '
        f'id={snapshot_id} | '
        f'pages={collector_performance["pages"]} | '
        f'raw={collector_performance["raw_orders"]} | '
        f'unique={collector_performance["unique_orders"]} | '
        f'duplicates={collector_performance["duplicates"]} | '
        f'saved={database_performance["saved_orders"]}'
    )

    reference_line = (
        f'REFERENCE: '
        f'USD/RUB={reference["rate"]:.5f} | '
        f'quote_time={reference["quote_timestamp"].isoformat()} | '
        f'quote_age_at_fetch={quote_age_at_fetch:.0f}s | '
        f'source={reference_performance["source"]} | '
        f'time={reference_performance["total_time"]:.3f}s'
    )

    page_parts = []

    for page_number, page_time in enumerate(
        collector_performance['page_fetch_times'],
        start=1,
    ):
        page_order_count = (
            collector_performance['page_order_counts'][page_number - 1]
        )

        page_parts.append(
            f'page_{page_number}={page_time:.3f}s'
            f'({page_order_count})'
        )

    pages_line = 'PAGES: ' + ' | '.join(page_parts)

    collector_line = (
        f'COLLECTOR: '
        f'fetch_total={collector_performance["fetch_total_time"]:.3f}s | '
        f'dedup={collector_performance["dedup_time"]:.4f}s | '
        f'normalize={collector_performance["normalize_time"]:.4f}s | '
        f'total={collector_performance["total_time"]:.3f}s'
    )

    database_line = (
        f'DATABASE: '
        f'connect={database_performance["connect_time"]:.3f}s | '
        f'create_snapshot={database_performance["create_snapshot_time"]:.4f}s | '
        f'save_orders={database_performance["save_orders_time"]:.3f}s | '
        f'avg_order_save={database_performance["average_order_save_ms"]:.3f}ms | '
        f'transaction={database_performance["transaction_time"]:.3f}s | '
        f'total={database_performance["total_time"]:.3f}s'
    )

    cycle_line = (
        f'CYCLE: total={cycle_time:.3f}s'
    )

    print(first_line)
    print(reference_line)
    print(pages_line)
    print(collector_line)
    print(database_line)
    print(cycle_line)
    print()

    with open(log_file, 'a', encoding='utf-8') as file:
        file.write(first_line + '\n')
        file.write(reference_line + '\n')
        file.write(pages_line + '\n')
        file.write(collector_line + '\n')
        file.write(database_line + '\n')
        file.write(cycle_line + '\n')
        file.write('\n')

    sleep_seconds = max(
        0,
        interval_seconds - cycle_time,
    )

    print(f'Next collection in {sleep_seconds:.1f} seconds')

    time.sleep(sleep_seconds)
