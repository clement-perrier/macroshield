from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    fred_api_key: str = ""
    fred_base_url: str = "https://api.stlouisfed.org/fred"

    # Local default only — points at nothing until a Postgres instance exists
    # (dev machine or the oracle-vm). Never hardcode real credentials here;
    # override via the DATABASE_URL env var / .env.
    database_url: str = "postgresql+asyncpg://macroshield:macroshield@localhost:5432/macroshield"

    fred_cache_max_staleness_hours: int = 20
    """How long a cached series is trusted before an on-demand request triggers a
    refetch, as a fallback for when the daily scheduled refresh hasn't run yet.
    Set below 24h so it can't paper over a broken daily job indefinitely."""


@lru_cache
def get_settings() -> Settings:
    return Settings()
