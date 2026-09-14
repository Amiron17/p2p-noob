import time
import requests
from datetime import datetime, timezone


API_KEY_FILE = r'C:\Users\MainUser\Desktop\twelve_data_api_key.txt'


def get_usd_rub_reference() -> tuple[dict, dict]:
    total_started_at = time.perf_counter()

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

    total_time = time.perf_counter() - total_started_at

    reference = {
        'rate': rate,
        'quote_timestamp': quote_timestamp,
        'fetched_at': fetched_at,
    }

    performance = {
        'key_read_time': key_read_time,
        'request_time': request_time,
        'json_time': json_time,
        'parse_time': parse_time,
        'total_time': total_time,
    }

    return reference, performance
