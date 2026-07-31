from dataclasses import dataclass
from datetime import timedelta
from enum import StrEnum
from statistics import mean, stdev
from typing import Literal

from app.services.fred_client import FredObservation

RateTrend = Literal["low_stable", "rising", "high", "falling_fast"]
YieldCurveState = Literal["normal", "inverted", "normalizing_post_inversion"]

MOMENTUM_WINDOW_MONTHS = 3
"""Matches backend-CLAUDE.md's "3-month trend" framing for inflation; reused for
growth so both axes are computed the same way."""

TRAILING_HISTORY_MONTHS = 5 * 12
"""5-year trailing window, per backend-CLAUDE.md's Z-score normalization section."""

YIELD_CURVE_LOOKBACK_DAYS = 730
"""~24 months. A positive T10Y2Y today still counts as "normalizing_post_inversion"
(not "normal") if the curve was inverted at any point in this window."""


class Phase(StrEnum):
    RECOVERY = "recovery"
    EXPANSION = "expansion"
    SLOWDOWN = "slowdown"
    RECESSION = "recession"


class InsufficientDataError(Exception):
    """Raised when there isn't enough historical data to compute a Z-score or trend."""


@dataclass
class PhaseResult:
    phase: Phase
    confidence: float  # 0.0 = right on the boundary, 1.0 = deep in quadrant
    growth_score: float
    inflation_score: float
    recession_override: bool  # True if the yield-curve alarm forced the call
    is_transition: bool  # True if too close to the crossroads to trust as-is


def zscore(current_value: float, historical_series: list[float]) -> float:
    """How many standard deviations current_value is from its own history."""
    m = mean(historical_series)
    s = stdev(historical_series)
    return (current_value - m) / s if s else 0.0


def _momentum_series(observations: list[FredObservation], window: int) -> list[float]:
    """Annualized % change over `window` months, for every point with enough lookback.
    Assumes monthly-frequency observations (true for IPMAN and CPIAUCSL).
    """
    values = [o.value for o in observations if o.value is not None]
    periods_per_year = 12 / window
    momentum = []
    for i in range(window, len(values)):
        past = values[i - window]
        if past == 0:
            continue
        momentum.append(((values[i] / past) ** periods_per_year - 1) * 100)
    return momentum


def _zscore_latest_momentum(observations: list[FredObservation]) -> float:
    momentum = _momentum_series(observations, MOMENTUM_WINDOW_MONTHS)
    required = TRAILING_HISTORY_MONTHS + 1
    if len(momentum) < required:
        raise InsufficientDataError(
            f"Need at least {required} momentum observations, got {len(momentum)}"
        )
    window = momentum[-required:]
    *history, current = window
    return zscore(current, history)


def growth_score_from_ipman(observations: list[FredObservation]) -> float:
    """Z-score of IPMAN's 3-month annualized % change against its own trailing 5-year
    history. Momentum, not level — the raw IPMAN level doesn't swing enough around
    its own trailing mean to be a useful cycle signal (see backend-CLAUDE.md notes)."""
    return _zscore_latest_momentum(observations)


def inflation_score_from_cpi(observations: list[FredObservation]) -> float:
    """Z-score of CPI's 3-month annualized % change against its own trailing 5-year
    history. Momentum, not level — CPI's raw level is ~monotonically increasing, so
    Z-scoring the level directly would be meaningless."""
    return _zscore_latest_momentum(observations)


def classify_rate_trend(observations: list[FredObservation]) -> RateTrend:
    """Compare the latest central bank rate to 3 months ago, per backend-CLAUDE.md.
    Simplification: only distinguishes rising/falling_fast/low_stable — the docs
    note that "high plateau" vs "low plateau" isn't automatable from the rate alone.
    Not fed into classify_phase — kept as a tie-breaker/confidence input for later.
    """
    latest, three_months_ago = observations[-1], observations[-4]
    if latest.value is None or three_months_ago.value is None:
        raise ValueError("Cannot classify rate trend from a missing observation")

    if latest.value > three_months_ago.value:
        return "rising"
    if latest.value < three_months_ago.value:
        return "falling_fast"
    return "low_stable"


def classify_yield_curve(observations: list[FredObservation]) -> YieldCurveState:
    """Sign-plus-trajectory read of T10Y2Y: negative today is "inverted"; positive
    today but inverted within the trailing lookback window is "normalizing_post_inversion"
    (the curve re-steepening after an inversion); otherwise "normal".
    """
    latest = observations[-1]
    if latest.value is None:
        raise ValueError("Cannot classify yield curve from a missing observation")

    if latest.value < 0:
        return "inverted"

    lookback_cutoff = latest.date - timedelta(days=YIELD_CURVE_LOOKBACK_DAYS)
    was_inverted_recently = any(
        o.value is not None and o.value < 0 and o.date >= lookback_cutoff for o in observations
    )
    return "normalizing_post_inversion" if was_inverted_recently else "normal"


def classify_phase(
    growth_score: float,
    inflation_score: float,
    yield_curve_state: YieldCurveState,
    transition_threshold: float = 0.6,
) -> PhaseResult:
    """Classify the economic cycle phase from two continuous momentum Z-scores
    (the growth/inflation quadrant framework). Exhaustive by construction: every
    (growth_score, inflation_score) pair falls into exactly one of 4 quadrants,
    unlike the earlier 4-row categorical matrix this replaces.
    """
    if growth_score is None or inflation_score is None:
        raise InsufficientDataError("growth_score or inflation_score missing")

    if yield_curve_state == "normalizing_post_inversion" and growth_score < 0:
        return PhaseResult(
            phase=Phase.RECESSION,
            confidence=min(1.0, abs(growth_score) / 2),
            growth_score=growth_score,
            inflation_score=inflation_score,
            recession_override=True,
            is_transition=False,
        )

    if growth_score >= 0 and inflation_score < 0:
        phase = Phase.RECOVERY
    elif growth_score >= 0 and inflation_score >= 0:
        phase = Phase.EXPANSION
    elif growth_score < 0 and inflation_score >= 0:
        phase = Phase.SLOWDOWN
    else:
        phase = Phase.RECESSION

    # Magnitude: raw distance from the origin, in combined Z-score units.
    magnitude = (growth_score**2 + inflation_score**2) ** 0.5
    # Confidence: how strongly to trust this phase call, scaled/capped to 0-1 for display.
    confidence = min(1.0, magnitude / 2.0)

    return PhaseResult(
        phase=phase,
        confidence=confidence,
        growth_score=growth_score,
        inflation_score=inflation_score,
        recession_override=False,
        # is_transition: too close to the crossroads to trust a single phase label.
        is_transition=magnitude < transition_threshold,
    )
