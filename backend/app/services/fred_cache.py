from datetime import UTC, date, datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.models.fred_cache import FredObservationCache
from app.services.fred_client import FredObservation, fetch_series

_UPSERT_COLUMNS_PER_ROW = 4  # series_id, observation_date, value, fetched_at
_MAX_QUERY_PARAMS = 32_767  # Postgres's hard per-statement bind-parameter limit
_UPSERT_BATCH_SIZE = _MAX_QUERY_PARAMS // _UPSERT_COLUMNS_PER_ROW  # ~8191 rows/statement


def _insert(session: AsyncSession):
    """Postgres is the real target (see backend-CLAUDE.md); sqlite_insert only
    kicks in under pytest's in-memory DB fixture so tests don't need a live
    Postgres instance. Both dialects support the same ON CONFLICT DO UPDATE
    shape, so this is just a compile-target switch, not a storage decision."""
    insert_fn = sqlite_insert if session.get_bind().dialect.name == "sqlite" else pg_insert
    return insert_fn(FredObservationCache)


async def refresh_series(session: AsyncSession, series_id: str) -> None:
    """Pull a series' full history from FRED and upsert it into the cache table.
    Full history (not just the caller's lookback window) so any other caller
    asking for a shorter window is already covered from cache afterwards —
    this is what the daily scheduler job calls, and what get_cached_series
    falls back to when the cache is empty or stale."""
    observations = await fetch_series(series_id)
    if not observations:
        return

    now = datetime.now(UTC)
    rows = [
        {
            "series_id": series_id,
            "observation_date": obs.date,
            "value": obs.value,
            "fetched_at": now,
        }
        for obs in observations
    ]

    # Batched: a daily series' full history (e.g. T10Y2Y since 1976, ~18k rows) times
    # 4 columns blows past Postgres's 32,767-bind-parameter-per-statement limit in one
    # shot — this only ever showed up against a real Postgres instance, since the
    # sqlite test fixture's few fake rows never got close to the limit.
    for i in range(0, len(rows), _UPSERT_BATCH_SIZE):
        batch = rows[i : i + _UPSERT_BATCH_SIZE]
        # ON CONFLICT DO UPDATE keyed on the (series_id, observation_date) primary key:
        # FRED both appends new dates and revises past ones (e.g. preliminary GDP
        # prints get restated), so plain insert-and-ignore would keep stale values.
        stmt = _insert(session).values(batch)
        stmt = stmt.on_conflict_do_update(
            index_elements=[FredObservationCache.series_id, FredObservationCache.observation_date],
            set_={"value": stmt.excluded.value, "fetched_at": stmt.excluded.fetched_at},
        )
        await session.execute(stmt)
    await session.commit()


async def _last_fetched_at(session: AsyncSession, series_id: str) -> datetime | None:
    result = await session.execute(
        select(func.max(FredObservationCache.fetched_at)).where(
            FredObservationCache.series_id == series_id
        )
    )
    last_fetched = result.scalar_one_or_none()
    if last_fetched is not None and last_fetched.tzinfo is None:
        # sqlite (test fixture only — see _insert()) drops tzinfo on round-trip even
        # for a timezone=True column; Postgres doesn't. We always write UTC, so it's
        # safe to reattach it here rather than let the dialects behave differently.
        last_fetched = last_fetched.replace(tzinfo=UTC)
    return last_fetched


async def get_cached_series(
    session: AsyncSession, series_id: str, observation_start: date | None = None
) -> list[FredObservation]:
    """Read-through cache in front of fred_client.fetch_series. Refetches from FRED
    only when the cache is empty or older than fred_cache_max_staleness_hours —
    otherwise serves straight from Postgres, so routers stop hitting the FRED API
    on every request (these are monthly indicators; there's nothing to gain from
    a live call on each page load)."""
    max_staleness = timedelta(hours=get_settings().fred_cache_max_staleness_hours)
    last_fetched = await _last_fetched_at(session, series_id)
    if last_fetched is None or datetime.now(UTC) - last_fetched > max_staleness:
        await refresh_series(session, series_id)

    query = select(FredObservationCache).where(FredObservationCache.series_id == series_id)
    if observation_start is not None:
        query = query.where(FredObservationCache.observation_date >= observation_start)
    query = query.order_by(FredObservationCache.observation_date)

    result = await session.execute(query)
    return [
        FredObservation(date=row.observation_date, value=row.value)
        for row in result.scalars().all()
    ]
