from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    app_env: str = "development"
    redis_url: str = ""
    route_cache_ttl_seconds: int = 3600
    mock_mcp_enabled: bool = True


settings = Settings()
