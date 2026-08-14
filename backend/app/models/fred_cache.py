from datetime import date, datetime

from sqlalchemy import Date, DateTime, Float, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class FredObservationCache(Base):
    """One cached (series_id, date) observation pulled from FRED. Backs the
    read-through cache in app/services/fred_cache.py so routers stop hitting the
    FRED API on every request — see backend-CLAUDE.md's storage-layer note."""

    __tablename__ = "fred_observation_cache"

    series_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    observation_date: Mapped[date] = mapped_column(Date, primary_key=True)
    value: Mapped[float | None] = mapped_column(Float, nullable=True)
    fetched_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
