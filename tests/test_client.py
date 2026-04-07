"""ecos_enhanced.client 유닛 테스트 (네트워크 불필요)."""

import pytest
from ecos_enhanced import EcosClient, EcosApiError, EcosDataPoint, STAT_CODES


class TestEcosClientInit:
    def test_no_api_key_raises(self):
        with pytest.raises(ValueError, match="ECOS API 키"):
            EcosClient(api_key="")

    def test_with_api_key(self):
        client = EcosClient(api_key="test-key-12345")
        assert client.api_key == "test-key-12345"


class TestEcosApiError:
    def test_message(self):
        err = EcosApiError("test error", "INFO-200")
        assert str(err) == "test error"
        assert err.code == "INFO-200"

    def test_empty_code(self):
        err = EcosApiError("some error")
        assert err.code == ""


class TestEcosDataPoint:
    def test_fields(self):
        dp = EcosDataPoint(
            stat_code="722Y001",
            stat_name="한국은행 기준금리",
            item_name="기준금리",
            time="202401",
            value=3.5,
            unit="연%",
        )
        assert dp.stat_code == "722Y001"
        assert dp.value == 3.5
        assert dp.time == "202401"


class TestStatCodes:
    def test_registry_has_keys(self):
        expected = [
            "base_rate", "cd_rate", "treasury_3y", "treasury_10y",
            "usd_krw", "jpy_krw", "eur_krw", "cny_krw",
            "cpi", "m2", "gdp",
        ]
        for key in expected:
            assert key in STAT_CODES, f"{key} not in STAT_CODES"

    def test_registry_structure(self):
        for key, info in STAT_CODES.items():
            assert "code" in info, f"{key}: missing 'code'"
            assert "item" in info, f"{key}: missing 'item'"
            assert "cycle" in info, f"{key}: missing 'cycle'"
            assert "name" in info, f"{key}: missing 'name'"
            assert "unit" in info, f"{key}: missing 'unit'"
            assert info["cycle"] in ("D", "M", "Q", "A"), f"{key}: invalid cycle"

    def test_exchange_rate_keys(self):
        for currency in ("usd", "jpy", "eur", "cny"):
            key = f"{currency}_krw"
            assert key in STAT_CODES

    def test_treasury_keys(self):
        assert "treasury_3y" in STAT_CODES
        assert "treasury_10y" in STAT_CODES


class TestGetByKeyValidation:
    @pytest.mark.asyncio
    async def test_invalid_key_raises(self):
        client = EcosClient(api_key="test-key")
        with pytest.raises(ValueError, match="알 수 없는 키"):
            await client.get_by_key("nonexistent_key", "202401", "202412")
        await client.close()

    @pytest.mark.asyncio
    async def test_available_keys(self):
        client = EcosClient(api_key="test-key")
        keys = await client.get_available_keys()
        assert len(keys) == len(STAT_CODES)
        for item in keys:
            assert "key" in item
            assert "name" in item
        await client.close()
