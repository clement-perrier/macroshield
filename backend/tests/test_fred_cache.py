from collections.abc import AsyncIterator
from datetime import UTC, date, datetime, timedelta

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.db.base import Base
from app.services.fred_cache import get_cached_series, refresh_series
from app.services.fred_client import FredObservation


@pytest.fixture
async def session() -> AsyncIterator[AsyncSession]:
    # In-memory sqlite, not Postgres — this is a test-only speed/isolation choice
    # (see the _insert() comment in fred_cache.py), the real target stays Postgres.
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    sessionmaker = async_sessionmaker(engine, expire_on_commit=False)
    async with sessionmaker() as s:
        yield s

    await engine.dispose()


FAKE_OBSERVATIONS = [
    FredObservation(date=date(2024, 1, 1), value=1.23),
    FredObservation(date=date(2024, 2, 1), value=None),
    FredObservation(date=date(2024, 3, 1), value=1.45),
]


async def test_refresh_series_upserts_observations(
    session: AsyncSession, monkeypatch: pytest.MonkeyPatch
) -> None:
    async def fake_fetch_series(series_id: str, observation_start: date | None = None):
        return FAKE_OBSERVATIONS

    monkeypatch.setattr("app.services.fred_cache.fetch_series", fake_fetch_series)

    await refresh_series(session, "TESTSERIES")

    cached = await get_cached_series(session, "TESTSERIES")
    assert [o.date for o in cached] == [o.date for o in FAKE_OBSERVATIONS]
    assert cached[0].value == 1.23
    assert cached[1].value is None


async def test_refresh_series_revises_existing_values(
    session: AsyncSession, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls = {"n": 0}

    async def fake_fetch_series(series_id: str, observation_start: date | None = None):
        calls["n"] += 1
        value = 1.0 if calls["n"] == 1 else 9.99  # simulate FRED revising a prior print
        return [FredObservation(date=date(2024, 1, 1), value=value)]

    monkeypatch.setattr("app.services.fred_cache.fetch_series", fake_fetch_series)

    await refresh_series(session, "TESTSERIES")
    await refresh_series(session, "TESTSERIES")

    cached = await get_cached_series(session, "TESTSERIES")
    assert len(cached) == 1  # upsert, not a duplicate row
    assert cached[0].value == 9.99


async def test_get_cached_series_serves_fresh_cache_without_refetching(
    session: AsyncSession, monkeypatch: pytest.MonkeyPatch
) -> None:
    fetch_calls = {"n": 0}

    async def fake_fetch_series(series_id: str, observation_start: date | None = None):
        fetch_calls["n"] += 1
        return FAKE_OBSERVATIONS

    monkeypatch.setattr("app.services.fred_cache.fetch_series", fake_fetch_series)

    await get_cached_series(session, "TESTSERIES")
    assert fetch_calls["n"] == 1

    await get_cached_series(session, "TESTSERIES")
    assert fetch_calls["n"] == 1  # second call served from cache, no refetch


async def test_get_cached_series_refetches_when_stale(
    session: AsyncSession, monkeypatch: pytest.MonkeyPatch
) -> None:
    fetch_calls = {"n": 0}

    async def fake_fetch_series(series_id: str, observation_start: date | None = None):
        fetch_calls["n"] += 1
        return FAKE_OBSERVATIONS

    monkeypatch.setattr("app.services.fred_cache.fetch_series", fake_fetch_series)

    await refresh_series(session, "TESTSERIES")

    # Force the cached rows to look old enough to trigger a refetch.
    from app.models.fred_cache import FredObservationCache

    stale_time = datetime.now(UTC) - timedelta(hours=48)
    await session.execute(FredObservationCache.__table__.update().values(fetched_at=stale_time))
    await session.commit()

    await get_cached_series(session, "TESTSERIES")
    assert fetch_calls["n"] == 2  # refresh_series (1) + refetch triggered by staleness (1)


async def test_get_cached_series_filters_by_observation_start(
    session: AsyncSession, monkeypatch: pytest.MonkeyPatch
) -> None:
    async def fake_fetch_series(series_id: str, observation_start: date | None = None):
        return FAKE_OBSERVATIONS

    monkeypatch.setattr("app.services.fred_cache.fetch_series", fake_fetch_series)

    cached = await get_cached_series(session, "TESTSERIES", observation_start=date(2024, 2, 1))
    assert [o.date for o in cached] == [date(2024, 2, 1), date(2024, 3, 1)]


async def test_refresh_series_batches_large_series(
    session: AsyncSession, monkeypatch: pytest.MonkeyPatch
) -> None:
    # A real daily series' full history (e.g. T10Y2Y since 1976) is tens of
    # thousands of rows — enough to exceed Postgres's 32,767-bind-parameter
    # limit in a single upsert statement if not batched. 20k rows here is
    # comfortably past the ~8191-row batch size to prove multiple batches run.
    large_series = [
        FredObservation(date=date(1970, 1, 1) + timedelta(days=i), value=float(i))
        for i in range(20_000)
    ]

    async def fake_fetch_series(series_id: str, observation_start: date | None = None):
        return large_series

    monkeypatch.setattr("app.services.fred_cache.fetch_series", fake_fetch_series)

    await refresh_series(session, "BIGSERIES")

    cached = await get_cached_series(session, "BIGSERIES")
    assert len(cached) == 20_000
    assert cached[0].date == date(1970, 1, 1)
    assert cached[-1].date == large_series[-1].date
