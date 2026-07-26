from datetime import date

import httpx
from pydantic import BaseModel, field_validator

from app.core.config import get_settings

FRED_SERIES_ID = "T10Y2Y"
"""US 10Y-2Y Treasury yield curve spread. See CLAUDE.md zones table for why this series."""


class FredObservation(BaseModel):
    date: date
    value: float | None

    @field_validator("value", mode="before")
    @classmethod
    def parse_missing_value(cls, raw_value: object) -> object:
        # FRED uses "." to mark a missing observation for that date.
        if raw_value == ".":
            return None
        return raw_value


async def fetch_t10y2y_series() -> list[FredObservation]:
    """Fetch the T10Y2Y series from the official FRED API (never scraped)."""
    settings = get_settings()
    if not settings.fred_api_key:
        raise RuntimeError("FRED_API_KEY environment variable is not set")

    params = {
        "series_id": FRED_SERIES_ID,
        "api_key": settings.fred_api_key,
        "file_type": "json",
    }

    async with httpx.AsyncClient(base_url=settings.fred_base_url, timeout=10.0) as client:
        response = await client.get("/series/observations", params=params)
        response.raise_for_status()
        payload = response.json()

    return [FredObservation.model_validate(obs) for obs in payload["observations"]]
