from datetime import date, timedelta

import pytest

from app.services.fred_client import FredObservation
from app.services.macro_engine import (
    InsufficientDataError,
    Phase,
    classify_phase,
    classify_yield_curve,
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
