"""Async client for Bank of Korea (한국은행) ECOS API.

Retrieves economic statistics data such as base rate (기준금리),
exchange rates (환율), consumer price index (소비자물가), etc.
API docs: https://ecos.bok.or.kr/api/
"""

import os
from dataclasses import dataclass
from typing import Any

import httpx


BASE_URL = "https://ecos.bok.or.kr/api"


# Major statistics code registry
STAT_CODES: dict[str, dict[str, str]] = {
    # Interest rates
    "base_rate": {
        "code": "722Y001",
        "item": "0101000",
        "cycle": "M",
        "name": "BOK Base Rate (한국은행 기준금리)",
        "unit": "% p.a.",
    },
    "cd_rate": {
        "code": "817Y002",
        "item": "010502000",
        "cycle": "D",
        "name": "CD (91-day) Rate",
        "unit": "% p.a.",
    },
    "treasury_3y": {
        "code": "817Y002",
        "item": "010200000",
        "cycle": "D",
        "name": "Treasury Bond (3-year) Yield (국고채 3년)",
        "unit": "% p.a.",
    },
    "treasury_10y": {
        "code": "817Y002",
        "item": "010210000",
        "cycle": "D",
        "name": "Treasury Bond (10-year) Yield (국고채 10년)",
        "unit": "% p.a.",
    },
    # Exchange rates
    "usd_krw": {
        "code": "731Y003",
        "item": "0000003",
        "cycle": "D",
        "name": "USD/KRW Exchange Rate (closing)",
        "unit": "KRW",
    },
    "jpy_krw": {
        "code": "731Y003",
        "item": "0000007",
        "cycle": "D",
        "name": "JPY 100/KRW Exchange Rate (closing)",
        "unit": "KRW",
    },
    "eur_krw": {
        "code": "731Y003",
        "item": "0000005",
        "cycle": "D",
        "name": "EUR/KRW Exchange Rate (closing)",
        "unit": "KRW",
    },
    "cny_krw": {
        "code": "731Y003",
        "item": "0000027",
        "cycle": "D",
        "name": "CNY/KRW Exchange Rate (closing)",
        "unit": "KRW",
    },
    # Prices
    "cpi": {
        "code": "901Y009",
        "item": "0",
        "cycle": "M",
        "name": "Consumer Price Index (소비자물가지수, All Items)",
        "unit": "2020=100",
    },
    # Money supply
    "m2": {
        "code": "101Y003",
        "item": "BBGA00",
        "cycle": "M",
        "name": "M2 Broad Money (광의통화)",
        "unit": "billion KRW",
    },
    # GDP
    "gdp": {
        "code": "200Y002",
        "item": "10111",
        "cycle": "Q",
        "name": "Real GDP (실질 국내총생산)",
        "unit": "billion KRW",
    },
}


@dataclass
class EcosDataPoint:
    """A single ECOS data point."""

    stat_code: str
    stat_name: str
    item_name: str
    time: str  # YYYYMM or YYYYMMDD
    value: float
    unit: str


class EcosClient:
    """Async client for Bank of Korea (한국은행) ECOS API.

    Args:
        api_key: ECOS API authentication key. If not provided, reads from
                 the ``ECOS_API_KEY`` environment variable.

    Example::

        async with EcosClient(api_key="YOUR_KEY") as client:
            data = await client.get_base_rate("202401", "202412")
            for d in data:
                print(f"{d.time}: {d.value}%")
    """

    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or os.environ.get("ECOS_API_KEY", "")
        if not self.api_key:
            raise ValueError(
                "ECOS API key is required. "
                "Provide it via the ECOS_API_KEY environment variable "
                "or pass it to the constructor."
            )
        self._client = httpx.AsyncClient(timeout=30.0)

    async def close(self) -> None:
        """Close the HTTP client."""
        await self._client.aclose()

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        await self.close()

    async def _request(
        self,
        service: str,
        params: list[str],
    ) -> dict:
        """Send a request to the ECOS API."""
        parts = [BASE_URL, service, self.api_key, "json", "kr"] + params
        url = "/".join(parts)

        resp = await self._client.get(url)
        resp.raise_for_status()
        data = resp.json()

        if "RESULT" in data:
            code = data["RESULT"].get("CODE", "")
            msg = data["RESULT"].get("MESSAGE", "")
            if code == "INFO-200":
                return {"rows": []}  # No data available
            raise EcosApiError(f"ECOS API error: {msg} ({code})", code)

        return data

    # -- Generic query --

    async def get_statistic(
        self,
        stat_code: str,
        cycle: str,
        start_date: str,
        end_date: str,
        item_code: str,
        start_no: int = 1,
        end_no: int = 1000,
    ) -> list[EcosDataPoint]:
        """Retrieve statistical data from ECOS.

        Args:
            stat_code: Statistics table code.
            cycle: Frequency (D=daily, M=monthly, Q=quarterly, A=annual).
            start_date: Start date (YYYYMMDD or YYYYMM).
            end_date: End date.
            item_code: Statistics item code.
            start_no: Starting row number for pagination.
            end_no: Ending row number for pagination.

        Returns:
            A list of EcosDataPoint objects.
        """
        data = await self._request(
            "StatisticSearch",
            [
                str(start_no),
                str(end_no),
                stat_code,
                cycle,
                start_date,
                end_date,
                item_code,
            ],
        )

        rows = data.get("StatisticSearch", {}).get("row", [])
        result = []
        for row in rows:
            val_str = row.get("DATA_VALUE", "")
            try:
                value = float(val_str.replace(",", ""))
            except (ValueError, TypeError):
                continue

            result.append(
                EcosDataPoint(
                    stat_code=row.get("STAT_CODE", ""),
                    stat_name=row.get("STAT_NAME", ""),
                    item_name=row.get("ITEM_NAME1", ""),
                    time=row.get("TIME", ""),
                    value=value,
                    unit=row.get("UNIT_NAME", ""),
                )
            )
        return result

    # -- Registry-based convenience methods --

    async def get_by_key(
        self,
        key: str,
        start_date: str,
        end_date: str,
    ) -> list[EcosDataPoint]:
        """Query by STAT_CODES registry key.

        Args:
            key: A STAT_CODES key (e.g. ``"base_rate"``, ``"usd_krw"``).
            start_date: Start date.
            end_date: End date.
        """
        if key not in STAT_CODES:
            raise ValueError(
                f"Unknown key: {key}. Available keys: {list(STAT_CODES.keys())}"
            )
        info = STAT_CODES[key]
        return await self.get_statistic(
            stat_code=info["code"],
            cycle=info["cycle"],
            start_date=start_date,
            end_date=end_date,
            item_code=info["item"],
        )

    async def get_base_rate(
        self, start_date: str, end_date: str
    ) -> list[EcosDataPoint]:
        """Retrieve the BOK base rate (한국은행 기준금리)."""
        return await self.get_by_key("base_rate", start_date, end_date)

    async def get_exchange_rate(
        self,
        currency: str = "usd",
        start_date: str = "",
        end_date: str = "",
    ) -> list[EcosDataPoint]:
        """Retrieve exchange rates.

        Args:
            currency: ``"usd"``, ``"jpy"``, ``"eur"``, ``"cny"``
        """
        key = f"{currency}_krw"
        return await self.get_by_key(key, start_date, end_date)

    async def get_cpi(
        self, start_date: str, end_date: str
    ) -> list[EcosDataPoint]:
        """Retrieve the Consumer Price Index (소비자물가지수)."""
        return await self.get_by_key("cpi", start_date, end_date)

    async def get_treasury_yield(
        self,
        maturity: str = "10y",
        start_date: str = "",
        end_date: str = "",
    ) -> list[EcosDataPoint]:
        """Retrieve Treasury Bond yield (국고채 금리).

        Args:
            maturity: ``"3y"`` or ``"10y"``
        """
        key = f"treasury_{maturity}"
        return await self.get_by_key(key, start_date, end_date)

    async def get_gdp(
        self, start_date: str, end_date: str
    ) -> list[EcosDataPoint]:
        """Retrieve real GDP (실질 GDP) data (quarterly)."""
        return await self.get_by_key("gdp", start_date, end_date)

    async def get_available_keys(self) -> list[dict]:
        """Return a list of available statistics keys."""
        return [
            {"key": k, "name": v["name"], "unit": v["unit"], "cycle": v["cycle"]}
            for k, v in STAT_CODES.items()
        ]


class EcosApiError(Exception):
    """ECOS API error."""

    def __init__(self, message: str, code: str = ""):
        super().__init__(message)
        self.code = code
