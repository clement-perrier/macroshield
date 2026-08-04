from dataclasses import dataclass


@dataclass
class ZoneConfig:
    pmi_series_id: str
    inflation_series_id: str
    rate_series_id: str
    yield_curve_long_series_id: str | None = None
    yield_curve_short_series_id: str | None = None
    """If set alongside yield_curve_long_series_id, the yield curve is computed as
    long - short (e.g. EU: DE 10Y minus 3-month interbank). If only
    yield_curve_long_series_id is set, that series already IS the spread (e.g. US's
    T10Y2Y, precomputed by FRED). If neither is set, the zone has no yield curve
    proxy at all (e.g. China) — omitted rather than inventing a shaky one, per
    backend-CLAUDE.md's explicit instruction."""


ZONE_CONFIGS: dict[str, ZoneConfig] = {
    "us": ZoneConfig(
        pmi_series_id="IPMAN",
        # NOT the canonical INDPRO/MANEMP from backend-CLAUDE.md's zones table —
        # deliberately chosen instead, per explicit instruction earlier in this project.
        inflation_series_id="CPIAUCSL",
        rate_series_id="FEDFUNDS",
        yield_curve_long_series_id="T10Y2Y",
    ),
    "eu": ZoneConfig(
        # BSCICP02DEM460S: German manufacturing business confidence composite.
        # backend-CLAUDE.md's originally-listed BSCILM02DEM160S no longer exists on
        # FRED (verified: 400 Bad Request) — this is its live replacement.
        pmi_series_id="BSCICP02DEM460S",
        inflation_series_id="CP0000EZ19M086NEST",
        # ECBMRRFR: ECB Main Refinancing Operations Rate. backend-CLAUDE.md's
        # originally-listed ECBMAINREFTR no longer exists on FRED (verified: 400
        # Bad Request) — this is its live replacement. Daily frequency, unlike the
        # US/China rate series (monthly) — classify_rate_trend must not assume a
        # fixed monthly cadence because of this.
        rate_series_id="ECBMRRFR",
        yield_curve_long_series_id="IRLTLT01DEM156N",  # DE 10Y long-term rate
        yield_curve_short_series_id="IR3TIB01DEM156N",  # 3-month interbank, as 2Y stand-in
    ),
    "china": ZoneConfig(
        # CHNLOLITOAASTSAM: OECD Composite Leading Indicator (amplitude adjusted).
        # backend-CLAUDE.md's originally-listed CHIPRMNTO01G00M no longer exists on
        # FRED (verified: 400 Bad Request); the direct industrial-production
        # alternatives found are stale (last updated 2023) — this CLI series is
        # still updating monthly and is arguably a better fit anyway, since it's
        # purpose-built to signal cycle turning points rather than raw output level.
        pmi_series_id="CHNLOLITOAASTSAM",
        inflation_series_id="CHNCPIALLMINMEI",
        rate_series_id="INTDSRCNM193N",
        # No yield_curve_long_series_id / yield_curve_short_series_id: China has no
        # clean FRED yield-curve equivalent (backend-CLAUDE.md flags this directly).
        # Omitted rather than invented, per explicit instruction.
    ),
}
