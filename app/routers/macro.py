from fastapi import APIRouter, HTTPException

from app.services.fred_client import (
    CPIAUCSL_SERIES_ID,
    FEDFUNDS_SERIES_ID,
    IPMAN_SERIES_ID,
    T10Y2Y_SERIES_ID,
    fetch_series,
)
from app.services.macro_engine import (
    InsufficientDataError,
    classify_phase,
    classify_rate_trend,
    classify_yield_curve,
    growth_score_from_ipman,
    inflation_score_from_cpi,
)

router = APIRouter(prefix="/zones", tags=["macro"])


@router.get("/{zone}/macro")
async def get_zone_macro(zone: str) -> dict:
    if zone != "us":
        raise HTTPException(status_code=404, detail=f"Zone '{zone}' is not supported yet")

    pmi_obs = await fetch_series(IPMAN_SERIES_ID)
    inflation_obs = await fetch_series(CPIAUCSL_SERIES_ID)
    rate_obs = await fetch_series(FEDFUNDS_SERIES_ID)
    curve_obs = await fetch_series(T10Y2Y_SERIES_ID)

    try:
        growth_score = growth_score_from_ipman(pmi_obs)
        inflation_score = inflation_score_from_cpi(inflation_obs)
    except InsufficientDataError as e:
        raise HTTPException(status_code=422, detail=str(e)) from e

    yield_curve_state = classify_yield_curve(curve_obs)
    rate_trend = classify_rate_trend(rate_obs)

    result = classify_phase(growth_score, inflation_score, yield_curve_state)

    return {
        "phase": result.phase,
        "confidence": round(result.confidence, 3),
        "is_transition": result.is_transition,
        "recession_override": result.recession_override,
        "metrics": [
            {
                "series_id": IPMAN_SERIES_ID,
                "label": "PMI proxy (IPMAN) growth momentum",
                "date": pmi_obs[-1].date,
                "value": pmi_obs[-1].value,
                "growth_score": round(growth_score, 3),
            },
            {
                "series_id": CPIAUCSL_SERIES_ID,
                "label": "Inflation (CPI) momentum",
                "date": inflation_obs[-1].date,
                "value": inflation_obs[-1].value,
                "inflation_score": round(inflation_score, 3),
            },
            {
                "series_id": FEDFUNDS_SERIES_ID,
                "label": "Central bank rate (Fed Funds)",
                "date": rate_obs[-1].date,
                "value": rate_obs[-1].value,
                "trend": rate_trend,
            },
            {
                "series_id": T10Y2Y_SERIES_ID,
                "label": "Yield curve (10Y-2Y)",
                "date": curve_obs[-1].date,
                "value": curve_obs[-1].value,
                "trend": yield_curve_state,
            },
        ],
    }
