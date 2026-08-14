import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from app.core.zones import ZONE_CONFIGS
from app.db.session import get_sessionmaker
from app.services.fred_cache import refresh_series

logger = logging.getLogger(__name__)

DAILY_REFRESH_HOUR_UTC = 6
"""Once a day is enough — these are monthly economic indicators, not something that
benefits from real-time polling. Arbitrary off-peak UTC hour, no deadline to hit."""


def _all_series_ids() -> list[str]:
    """Every FRED series id referenced by any zone, deduplicated (e.g. the
    inflation series could in principle be reused across zones)."""
    ids: set[str] = set()
    for zone in ZONE_CONFIGS.values():
        ids.add(zone.pmi_series_id)
        ids.add(zone.inflation_series_id)
        ids.add(zone.rate_series_id)
        if zone.yield_curve_long_series_id:
            ids.add(zone.yield_curve_long_series_id)
        if zone.yield_curve_short_series_id:
            ids.add(zone.yield_curve_short_series_id)
    return sorted(ids)


async def refresh_all_series() -> None:
    """The scheduled job body. Refreshes each series in its own session/transaction
    so one bad series (FRED outage, a renamed/retired series id) can't roll back
    the others — logged and skipped instead."""
    session_factory = get_sessionmaker()
    for series_id in _all_series_ids():
        try:
            async with session_factory() as session:
                await refresh_series(session, series_id)
        except Exception:
            logger.exception("Failed to refresh FRED series %s", series_id)


def build_scheduler() -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler(timezone="UTC")
    scheduler.add_job(
        refresh_all_series,
        trigger=CronTrigger(hour=DAILY_REFRESH_HOUR_UTC, minute=0),
        id="refresh_fred_series",
        replace_existing=True,
    )
    return scheduler
