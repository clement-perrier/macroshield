from app.core.zones import ZONE_CONFIGS


def test_zone_configs_has_us_eu_china() -> None:
    assert set(ZONE_CONFIGS) == {"us", "eu", "china"}


def test_every_zone_has_pmi_inflation_and_rate_series() -> None:
    for config in ZONE_CONFIGS.values():
        assert config.pmi_series_id
        assert config.inflation_series_id
        assert config.rate_series_id


def test_us_yield_curve_is_a_direct_series() -> None:
    us = ZONE_CONFIGS["us"]
    assert us.yield_curve_long_series_id == "T10Y2Y"
    assert us.yield_curve_short_series_id is None


def test_eu_yield_curve_is_computed_from_two_series() -> None:
    eu = ZONE_CONFIGS["eu"]
    assert eu.yield_curve_long_series_id is not None
    assert eu.yield_curve_short_series_id is not None


def test_china_has_no_yield_curve_proxy() -> None:
    china = ZONE_CONFIGS["china"]
    assert china.yield_curve_long_series_id is None
    assert china.yield_curve_short_series_id is None
