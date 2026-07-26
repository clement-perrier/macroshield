from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    fred_api_key: str = ""
    fred_base_url: str = "https://api.stlouisfed.org/fred"


@lru_cache
def get_settings() -> Settings:
    return Settings()
