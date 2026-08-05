import logging
from datetime import date, timedelta

from fastapi import APIRouter, HTTPException

from app.core.zones import ZONE_CONFIGS
from app.services.fred_client import FredObservation, fetch_series
from app.services.macro_engine import (
    MOMENTUM_WINDOW_MONTHS,
    TRAILING_HISTORY_MONTHS,
    InsufficientDataError,
    classify_phase,
    classify_rate_trend,
    classify_yield_curve,
    compute_yield_curve_observations,
    momentum_zscore,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/zones", tags=["macro"])

BUFFER_MONTHS = 6
FETCH_LOOKBACK_DAYS = 30 * (TRAILING_HISTORY_MONTHS + MOMENTUM_WINDOW_MONTHS + BUFFER_MONTHS)
"""How far back to ask FRED for data. Derived from macro_engine's own momentum_zscore
requirement (its largest lookback) plus a buffer, rather than a standalone guess —
so it can't silently drift out of sync if that requirement changes later."""

RATE_LOG_LOOKBACK_MONTHS = 12


def _monthly_samples(observations: list[FredObservation], months: int) -> list[FredObservation]:
    """One observation per calendar month (the latest in that month) over the
    trailing `months` months. Series here are monthly (FEDFUNDS) or daily
    (ECBMRRFR) — this collapses either down to a monthly cadence for logging."""
    cutoff = observations[-1].date - timedelta(days=30 * months)
    by_month: dict[tuple[int, int], FredObservation] = {}
    for o in observations:
        if o.value is None or o.date < cutoff:
            continue
        by_month[(o.date.year, o.date.month)] = o
    return sorted(by_month.values(), key=lambda o: o.date)


@router.get("/{zone}/macro")
async def get_zone_macro(zone: str) -> dict:
    zone_config = ZONE_CONFIGS.get(zone)
    if zone_config is None:
        raise HTTPException(status_code=404, detail=f"Zone '{zone}' is not supported yet")

    observation_start = date.today() - timedelta(days=FETCH_LOOKBACK_DAYS)

    pmi_obs = await fetch_series(zone_config.pmi_series_id, observation_start)
    inflation_obs = await fetch_series(zone_config.inflation_series_id, observation_start)
    rate_obs = await fetch_series(zone_config.rate_series_id, observation_start)

    monthly_rates = _monthly_samples(rate_obs, RATE_LOG_LOOKBACK_MONTHS)
    logger.info(
        "%s rate, last %d months: %s",
        zone_config.rate_series_id,
        RATE_LOG_LOOKBACK_MONTHS,
        ", ".join(f"{o.date}={o.value}" for o in monthly_rates),
    )

    try:
        growth_score = momentum_zscore(pmi_obs)
        inflation_score = momentum_zscore(inflation_obs)
    except InsufficientDataError as e:
        raise HTTPException(status_code=422, detail=str(e)) from e

    rate_trend = classify_rate_trend(rate_obs)

    metrics = [
        {
            "series_id": zone_config.pmi_series_id,
            "label": "PMI proxy growth momentum",
            "date": pmi_obs[-1].date,
            "value": pmi_obs[-1].value,
            "growth_score": round(growth_score, 3),
        },
        {
            "series_id": zone_config.inflation_series_id,
            "label": "Inflation momentum",
            "date": inflation_obs[-1].date,
            "value": inflation_obs[-1].value,
            "inflation_score": round(inflation_score, 3),
        },
        {
            "series_id": zone_config.rate_series_id,
            "label": "Central bank rate",
            "date": rate_obs[-1].date,
            "value": rate_obs[-1].value,
            "trend": rate_trend,
        },
    ]

    yield_curve_state = None
    if zone_config.yield_curve_long_series_id is not None:
        long_obs = await fetch_series(zone_config.yield_curve_long_series_id, observation_start)
        short_obs = None
        if zone_config.yield_curve_short_series_id is not None:
            short_obs = await fetch_series(
                zone_config.yield_curve_short_series_id, observation_start
            )

        curve_obs = compute_yield_curve_observations(long_obs, short_obs)
        yield_curve_state = classify_yield_curve(curve_obs)
        metrics.append(
            {
                "series_id": zone_config.yield_curve_long_series_id,
                "label": "Yield curve",
                "date": curve_obs[-1].date,
                "value": curve_obs[-1].value,
                "trend": yield_curve_state,
            }
        )

    result = classify_phase(growth_score, inflation_score, yield_curve_state)

    return {
        "phase": result.phase,
        "confidence": round(result.confidence, 3),
        "is_transition": result.is_transition,
        "recession_override": result.recession_override,
        "metrics": metrics,
    }
