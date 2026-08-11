from datetime import date, timedelta

import pytest

from app.services.fred_client import FredObservation
from app.services.macro_engine import (
    InsufficientDataError,
    Phase,
    classify_phase,
    classify_rate_trend,
    classify_yield_curve,
    compute_yield_curve_observations,
    momentum_zscore,
    zscore,
)


def _make_observations(values: list[float], start: date, step_days: int) -> list[FredObservation]:
    return [
        FredObservation(date=start + timedelta(days=step_days * i), value=v)
        for i, v in enumerate(values)
    ]


def test_zscore_at_the_mean_is_zero() -> None:
    assert zscore(10, [8, 9, 10, 11, 12]) == 0.0


def test_zscore_above_mean_is_positive() -> None:
    assert zscore(14, [8, 9, 10, 11, 12]) > 0


def test_zscore_below_mean_is_negative() -> None:
    assert zscore(6, [8, 9, 10, 11, 12]) < 0


def test_zscore_handles_zero_stdev() -> None:
    assert zscore(5, [5, 5, 5, 5]) == 0.0


def test_classify_yield_curve_inverted() -> None:
    observations = _make_observations([0.5, 0.3, -0.2], start=date(2025, 1, 1), step_days=30)
    assert classify_yield_curve(observations) == "inverted"


def test_classify_yield_curve_normal_when_never_inverted() -> None:
    observations = _make_observations([0.5, 0.6, 0.7], start=date(2025, 1, 1), step_days=30)
    assert classify_yield_curve(observations) == "normal"


def test_classify_yield_curve_normalizing_post_inversion() -> None:
    observations = _make_observations([-0.4, -0.1, 0.2], start=date(2026, 1, 1), step_days=30)
    assert classify_yield_curve(observations) == "normalizing_post_inversion"


def test_classify_yield_curve_ignores_old_inversion_outside_lookback() -> None:
    observations = [
        FredObservation(date=date(2010, 1, 1), value=-0.5),  # inverted, but 16 years ago
        FredObservation(date=date(2026, 1, 1), value=0.4),
    ]
    assert classify_yield_curve(observations) == "normal"


@pytest.mark.parametrize(
    "growth_score, inflation_score, expected_phase",
    [
        (1.0, -1.0, Phase.RECOVERY),
        (1.0, 1.0, Phase.EXPANSION),
        (-1.0, 1.0, Phase.SLOWDOWN),
        (-1.0, -1.0, Phase.RECESSION),
    ],
)
def test_classify_phase_covers_all_four_quadrants(
    growth_score: float, inflation_score: float, expected_phase: Phase
) -> None:
    result = classify_phase(growth_score, inflation_score, yield_curve_state="normal")
    assert result.phase == expected_phase
    assert result.recession_override is False


def test_classify_phase_never_raises_for_any_sign_combination() -> None:
    # Exhaustive by construction: unlike the old 4-row matrix, no input combination
    # should ever fall through un-handled.
    for growth_score in (-3.0, -0.01, 0.0, 0.01, 3.0):
        for inflation_score in (-3.0, -0.01, 0.0, 0.01, 3.0):
            classify_phase(growth_score, inflation_score, yield_curve_state="normal")


def test_classify_phase_yield_curve_override_forces_recession() -> None:
    result = classify_phase(
        growth_score=-0.5,
        inflation_score=1.5,  # would otherwise be Slowdown
        yield_curve_state="normalizing_post_inversion",
    )
    assert result.phase == Phase.RECESSION
    assert result.recession_override is True


def test_classify_phase_override_requires_negative_growth() -> None:
    result = classify_phase(
        growth_score=0.5,  # positive growth: override does not apply
        inflation_score=1.5,
        yield_curve_state="normalizing_post_inversion",
    )
    assert result.recession_override is False
    assert result.phase == Phase.EXPANSION


def test_classify_phase_near_origin_is_flagged_as_transition() -> None:
    result = classify_phase(growth_score=0.05, inflation_score=-0.05, yield_curve_state="normal")
    assert result.is_transition is True


def test_classify_phase_deep_in_quadrant_is_not_a_transition() -> None:
    result = classify_phase(growth_score=2.0, inflation_score=2.0, yield_curve_state="normal")
    assert result.is_transition is False


def test_classify_phase_raises_insufficient_data_for_missing_scores() -> None:
    with pytest.raises(InsufficientDataError):
        classify_phase(None, 1.0, yield_curve_state="normal")


def test_classify_phase_handles_no_yield_curve_proxy() -> None:
    # China has no yield curve proxy at all (backend-CLAUDE.md flags no clean FRED
    # equivalent) — yield_curve_state=None should classify normally, override never fires.
    result = classify_phase(growth_score=-1.0, inflation_score=-1.0, yield_curve_state=None)
    assert result.phase == Phase.RECESSION
    assert result.recession_override is False


def test_compute_yield_curve_observations_passthrough_when_no_short_series() -> None:
    long_obs = _make_observations([0.4, 0.5], start=date(2026, 1, 1), step_days=30)
    assert compute_yield_curve_observations(long_obs) == long_obs


def test_compute_yield_curve_observations_computes_spread() -> None:
    long_obs = [
        FredObservation(date=date(2026, 1, 1), value=3.0),
        FredObservation(date=date(2026, 2, 1), value=3.2),
    ]
    short_obs = [
        FredObservation(date=date(2026, 1, 1), value=2.5),
        FredObservation(date=date(2026, 2, 1), value=3.5),
    ]
    spread = compute_yield_curve_observations(long_obs, short_obs)
    assert [o.value for o in spread] == pytest.approx([0.5, -0.3])


def test_compute_yield_curve_observations_skips_unmatched_dates() -> None:
    long_obs = [
        FredObservation(date=date(2026, 1, 1), value=3.0),
        FredObservation(date=date(2026, 2, 1), value=3.2),
    ]
    short_obs = [FredObservation(date=date(2026, 1, 1), value=2.5)]  # missing Feb
    spread = compute_yield_curve_observations(long_obs, short_obs)
    assert len(spread) == 1
    assert spread[0].date == date(2026, 1, 1)


def test_classify_rate_trend_rising() -> None:
    # 4 monthly points spanning 90 days, so a reference ~3 months back exists.
    observations = _make_observations([1.0, 1.1, 1.25, 1.5], start=date(2026, 1, 1), step_days=30)
    assert classify_rate_trend(observations) == "rising"


def test_classify_rate_trend_falling() -> None:
    observations = _make_observations([1.5, 1.25, 1.1, 1.0], start=date(2026, 1, 1), step_days=30)
    assert classify_rate_trend(observations) == "falling_fast"


def test_classify_rate_trend_works_on_daily_frequency_series() -> None:
    # EU's rate series (ECBMRRFR) is daily, unlike US/China's monthly ones — the
    # lookback must be date-based, not a fixed index offset, to handle this.
    # 91 daily points spanning exactly 90 days, so a reference 90 days back exists.
    observations = _make_observations([2.0] * 90 + [2.5], start=date(2026, 1, 1), step_days=1)
    assert classify_rate_trend(observations) == "rising"


def test_classify_rate_trend_small_move_within_tolerance_is_stable() -> None:
    # 1bp drift over 3 months — noise/rounding, not a real policy move.
    observations = _make_observations(
        [2.15, 2.15, 2.15, 2.16], start=date(2026, 1, 1), step_days=30
    )
    assert classify_rate_trend(observations) == "low_stable"


def test_classify_rate_trend_move_at_tolerance_boundary_is_stable() -> None:
    # diff exactly equals RATE_TREND_TOLERANCE (0.1) — boundary is exclusive.
    # 0.0 -> 0.1 keeps the float subtraction exact (2.15 -> 2.25 lands on
    # 0.10000000000000009 due to float rounding, which would flip this test).
    observations = _make_observations([0.0, 0.0, 0.0, 0.1], start=date(2026, 1, 1), step_days=30)
    assert classify_rate_trend(observations) == "low_stable"


def test_classify_rate_trend_move_above_tolerance_is_rising() -> None:
    # Real EU ECBMRRFR example: 2.15 -> 2.4, a genuine +25bp hike.
    observations = _make_observations(
        [2.15, 2.15, 2.15, 2.4], start=date(2026, 1, 1), step_days=30
    )
    assert classify_rate_trend(observations) == "rising"


def test_classify_rate_trend_raises_without_enough_history() -> None:
    observations = _make_observations([1.0, 1.1], start=date(2026, 1, 1), step_days=1)
    with pytest.raises(InsufficientDataError):
        classify_rate_trend(observations)


def test_momentum_zscore_raises_without_enough_history() -> None:
    observations = _make_observations([100.0] * 10, start=date(2020, 1, 1), step_days=30)
    with pytest.raises(InsufficientDataError):
        momentum_zscore(observations)
