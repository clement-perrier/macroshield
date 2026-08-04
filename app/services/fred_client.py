from datetime import date

import httpx
from pydantic import BaseModel, field_validator

from app.core.config import get_settings


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


async def fetch_series(
    series_id: str, observation_start: date | None = None
) -> list[FredObservation]:
    """Fetch any FRED series by ID from the official API (never scraped).

    observation_start optionally limits how far back FRED returns data — without
    it, FRED returns the series' entire history (decades, for most series here),
    even though callers typically only need the last several years.
    """
    settings = get_settings()
    if not settings.fred_api_key:
        raise RuntimeError("FRED_API_KEY environment variable is not set")

    params = {
        "series_id": series_id,
        "api_key": settings.fred_api_key,
        "file_type": "json",
    }
    if observation_start is not None:
        params["observation_start"] = observation_start.isoformat()

    async with httpx.AsyncClient(base_url=settings.fred_base_url, timeout=10.0) as client:
        response = await client.get("/series/observations", params=params)
        response.raise_for_status()
        payload = response.json()

    return [FredObservation.model_validate(obs) for obs in payload["observations"]]


async def fetch_t10y2y_series() -> list[FredObservation]:
    """Fetch the T10Y2Y series (US 10Y-2Y yield curve spread)."""
    return await fetch_series("T10Y2Y")
