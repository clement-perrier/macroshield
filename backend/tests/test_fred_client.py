import pytest
import respx
from httpx import Response

from app.core.config import get_settings
from app.services.fred_client import fetch_t10y2y_series

FAKE_FRED_RESPONSE = {
    "realtime_start": "2026-07-25",
    "realtime_end": "2026-07-25",
    "observation_start": "1976-06-01",
    "observation_end": "9999-12-31",
    "units": "lin",
    "output_type": 1,
    "file_type": "json",
    "order_by": "observation_date",
    "sort_order": "asc",
    "count": 3,
    "offset": 0,
    "limit": 100000,
    "observations": [
        {
            "realtime_start": "2026-07-25",
            "realtime_end": "2026-07-25",
            "date": "2024-01-01",
            "value": "1.23",
        },
        {
            "realtime_start": "2026-07-25",
            "realtime_end": "2026-07-25",
            "date": "2024-02-01",
            "value": ".",
        },
        {
            "realtime_start": "2026-07-25",
            "realtime_end": "2026-07-25",
            "date": "2024-03-01",
            "value": "-0.15",
        },
    ],
}


@pytest.fixture(autouse=True)
def fred_api_key(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("FRED_API_KEY", "test-key")
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


@respx.mock
async def test_fetch_t10y2y_series_parses_observations() -> None:
    respx.get("https://api.stlouisfed.org/fred/series/observations").mock(
        return_value=Response(200, json=FAKE_FRED_RESPONSE)
    )

    observations = await fetch_t10y2y_series()

    assert len(observations) == 3
    assert observations[0].value == 1.23
    assert observations[1].value is None  # "." parsed as missing
    assert observations[2].value == -0.15


async def test_fetch_t10y2y_series_requires_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("FRED_API_KEY", "")
    get_settings.cache_clear()

    with pytest.raises(RuntimeError, match="FRED_API_KEY"):
        await fetch_t10y2y_series()
