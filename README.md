# ecos-enhanced

**Async Python client for Bank of Korea ECOS API**

An asynchronous Python client for the Bank of Korea Economic Statistics System (ECOS) API. Easily query key economic indicators such as base interest rate, exchange rates, treasury bond yields, consumer price index, GDP, and more.

[![PyPI](https://img.shields.io/pypi/v/ecos-enhanced)](https://pypi.org/project/ecos-enhanced/)
[![Python](https://img.shields.io/pypi/pyversions/ecos-enhanced)](https://pypi.org/project/ecos-enhanced/)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

## Features

- **Async-first** — Asynchronous HTTP client built on `httpx`
- **Built-in registry** — 12 major stat codes included (interest rates, exchange rates, prices, GDP, etc.)
- **Convenience methods** — One-liner queries via `get_base_rate()`, `get_exchange_rate()`, etc.
- **Zero pandas dependency** — Pure Python dataclasses
- **Fully typed** — `py.typed` marker with type hints on all public APIs

## Installation

```bash
pip install ecos-enhanced
```

## Quick Start

```python
import asyncio
from ecos_enhanced import EcosClient

async def main():
    async with EcosClient(api_key="YOUR_ECOS_API_KEY") as client:
        # USD/KRW exchange rate
        rates = await client.get_exchange_rate("usd", "20240101", "20241231")
        for r in rates:
            print(f"{r.time}: {r.value} KRW")

        # Bank of Korea base interest rate
        base = await client.get_base_rate("202401", "202412")
        print(f"Current base rate: {base[-1].value}%")

        # Consumer Price Index
        cpi = await client.get_cpi("202401", "202412")
        print(f"Latest CPI: {cpi[-1].value}")

asyncio.run(main())
```

### Error Handling

```python
from ecos_enhanced import EcosClient, EcosApiError

async with EcosClient() as client:
    try:
        data = await client.get_by_key("usd_krw", "20240101", "20241231")
    except EcosApiError as e:
        print(f"ECOS API error: {e} (code={e.code})")
```

## API Reference

### EcosClient

```python
client = EcosClient(api_key="...")  # or set the ECOS_API_KEY environment variable
```

| Method | Description |
|--------|-------------|
| `get_statistic(stat_code, cycle, start_date, end_date, item_code)` | General-purpose statistics query |
| `get_by_key(key, start_date, end_date)` | Convenient query by registry key |
| `get_base_rate(start_date, end_date)` | Bank of Korea base interest rate |
| `get_exchange_rate(currency, start_date, end_date)` | Exchange rates (usd, jpy, eur, cny) |
| `get_cpi(start_date, end_date)` | Consumer Price Index |
| `get_treasury_yield(maturity, start_date, end_date)` | Treasury bond yields (3y, 10y) |
| `get_gdp(start_date, end_date)` | Real GDP (quarterly) |
| `get_available_keys()` | List available registry keys |
| `close()` | Close HTTP client (called automatically when using context manager) |

### EcosDataPoint

Return type (list) for all query methods:

| Field | Type | Description |
|-------|------|-------------|
| `stat_code` | `str` | Statistics table code |
| `stat_name` | `str` | Statistics table name |
| `item_name` | `str` | Statistics item name |
| `time` | `str` | Time period (YYYYMMDD or YYYYMM) |
| `value` | `float` | Data value |
| `unit` | `str` | Unit |

### Built-in Registry (STAT_CODES)

| Key | Name | Cycle | Unit |
|-----|------|:-----:|------|
| `base_rate` | Bank of Korea Base Rate | M | % p.a. |
| `cd_rate` | CD (91-day) Rate | D | % p.a. |
| `treasury_3y` | Treasury Bond (3-year) Yield | D | % p.a. |
| `treasury_10y` | Treasury Bond (10-year) Yield | D | % p.a. |
| `usd_krw` | USD/KRW Exchange Rate (Closing) | D | KRW |
| `jpy_krw` | JPY 100/KRW Exchange Rate (Closing) | D | KRW |
| `eur_krw` | EUR/KRW Exchange Rate (Closing) | D | KRW |
| `cny_krw` | CNY/KRW Exchange Rate (Closing) | D | KRW |
| `cpi` | Consumer Price Index (All Items) | M | 2020=100 |
| `m2` | M2 (Broad Money) | M | Billion KRW |
| `gdp` | Real Gross Domestic Product (GDP) | Q | Billion KRW |

For statistics not in the registry, use `get_statistic()` to query directly.

### Date Format

| Cycle | Format | Example |
|:-----:|--------|---------|
| D (Daily) | YYYYMMDD | `"20240315"` |
| M (Monthly) | YYYYMM | `"202403"` |
| Q (Quarterly) | YYYYQ | `"2024Q1"` |
| A (Annual) | YYYY | `"2024"` |

## Environment Variables

| Variable | Description |
|----------|-------------|
| `ECOS_API_KEY` | ECOS API authentication key ([Get one here](https://ecos.bok.or.kr/api/)) |

## ECOS API Key

1. Visit the [ECOS API portal](https://ecos.bok.or.kr/api/)
2. Sign up and apply for an authentication key
3. Set the issued key as the `ECOS_API_KEY` environment variable or pass it to `EcosClient(api_key="...")`

## Important Notes

### Async Only

This library is designed for `async/await` usage only. To use it from synchronous code:

```python
import asyncio
result = asyncio.run(main())
```

### Statistics Query Limitations

- The ECOS API queries data using a combination of statistics table codes and item codes.
- For statistics not included in the built-in registry (`STAT_CODES`), look up the codes in the [ECOS API documentation](https://ecos.bok.or.kr/api/) and use `get_statistic()` to query directly.

## Disclaimer

This library is a technical tool for querying the Bank of Korea ECOS API and does not provide investment advice or financial services. Users are responsible for complying with the [ECOS API Terms of Service](https://ecos.bok.or.kr/api/) and all applicable laws and regulations when using the data.

## License

MIT License. See [LICENSE](LICENSE).
