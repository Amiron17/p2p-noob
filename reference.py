import json
import os
import time
import requests

from datetime import datetime, timezone

from pathlib import Path


API_KEY_FILE = r'C:\Users\MainUser\Desktop\twelve_data_api_key.txt'

DATA_DIR = Path(__file__).resolve().parent / 'data'
DATA_DIR.mkdir(exist_ok=True)
CACHE_FILE = DATA_DIR / 'usd_rub_reference_cache.json'

CACHE_MAX_AGE_SECONDS = 120


def get_usd_rub_reference() -> tuple[dict, dict]:
    total_started_at = time.perf_counter()

    now = datetime.now(timezone.utc)

    if CACHE_FILE.exists():
        with open(CACHE_FILE, 'r', encoding='utf-8') as file:
            cached = json.load(file)

        cached_fetched_at = datetime.fromisoformat(
            cached['fetched_at']
        )

        cache_age = (
            now - cached_fetched_at
        ).total_seconds()

        if cache_age <= CACHE_MAX_AGE_SECONDS:
            reference = {
                'rate': float(cached['rate']),
                'quote_timestamp': datetime.fromisoformat(
                    cached['quote_timestamp']
                ),
                'fetched_at': cached_fetched_at,
            }

            performance = {
                'key_read_time': 0.0,
                'request_time': 0.0,
                'json_time': 0.0,
                'parse_time': 0.0,
                'total_time': time.perf_counter() - total_started_at,
                'source': 'CACHED',
                'cache_age': cache_age,
            }

            return reference, performance

    key_read_started_at = time.perf_counter()

    with open(API_KEY_FILE, 'r', encoding='utf-8') as file:
        api_key = file.read().strip()

    key_read_time = time.perf_counter() - key_read_started_at

    request_started_at = time.perf_counter()

    response = requests.get(
        'https://api.twelvedata.com/exchange_rate',
        params={
            'symbol': 'USD/RUB',
            'apikey': api_key,
        },
        timeout=15,
    )

    request_time = time.perf_counter() - request_started_at

    response.raise_for_status()

    json_started_at = time.perf_counter()

    data = response.json()

    json_time = time.perf_counter() - json_started_at

    parse_started_at = time.perf_counter()

    rate = float(data['rate'])

    quote_timestamp = datetime.fromtimestamp(
        data['timestamp'],
        tz=timezone.utc,
    )

    fetched_at = datetime.now(timezone.utc)

    parse_time = time.perf_counter() - parse_started_at

    reference = {
        'rate': rate,
        'quote_timestamp': quote_timestamp,
        'fetched_at': fetched_at,
    }

    cache_data = {
        'rate': rate,
        'quote_timestamp': quote_timestamp.isoformat(),
        'fetched_at': fetched_at.isoformat(),
    }

    temporary_cache_file = CACHE_FILE.with_name(
        f'{CACHE_FILE.name}.{os.getpid()}.tmp'
    )

    with open(temporary_cache_file, 'w', encoding='utf-8') as file:
        json.dump(cache_data, file)

    os.replace(
        temporary_cache_file,
        CACHE_FILE,
    )

    performance = {
        'key_read_time': key_read_time,
        'request_time': request_time,
        'json_time': json_time,
        'parse_time': parse_time,
        'total_time': time.perf_counter() - total_started_at,
        'source': 'REFRESHED',
        'cache_age': 0.0,
    }

    return reference, performance
