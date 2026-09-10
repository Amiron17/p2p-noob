# P2P NOOB 

A Python project for monitoring Bybit P2P offers.

## Current version: V1

The script:

- fetches live P2P offers from Bybit for RUB/USDT;
- keeps only verified advertisers;
- normalizes raw API response data;
- filters merchants by minimum number of completed orders;
- filters merchants by minimum completion rate;
- shows the best offers returned by Bybit.

## Tech stack

- Python
- requests
- HTTP / JSON
- Git
- GitHub

## Project roadmap

### V1
Live P2P offer monitoring.

### V2
P2P market analysis:
- price distribution;
- outlier detection;
- market-wide anomalies;
- merchant statistics;
- historical analysis with SQL.

### V3
Transaction cost calculation:
- RUB → USDT;
- USDT → USD;
- exchange fees;
- USD → local currency;
- card / FX fees.

### V4
User interface or Telegram bot.

## Status

V1 prototype is complete.