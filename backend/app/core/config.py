"""Centralized application settings.

All business/attendance policy defaults live here so nothing is hardcoded
across the codebase. Per-company overrides live on the `companies` /
`company_locations` tables (see models).
"""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore", case_sensitive=False
    )

    # Environment
    ENVIRONMENT: str = "development"

    # Database
    DATABASE_URL: str = "postgresql+psycopg://worktrack:worktrack@localhost:5432/worktrack"

    # JWT / Auth
    JWT_SECRET: str = "dev-insecure-secret-change-me"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 30

    # CORS (comma separated)
    CORS_ORIGINS: str = "http://localhost:5173,http://localhost:3000"

    # Attendance policy defaults (overridable per-company)
    DEFAULT_ALLOWED_RADIUS_METERS: int = 150
    MAX_ACCEPTABLE_ACCURACY_METERS: float = 100.0
    DEFAULT_TIMEZONE: str = "Asia/Kolkata"

    # Login rate limiting
    LOGIN_RATE_LIMIT_ATTEMPTS: int = 5
    LOGIN_RATE_LIMIT_WINDOW_SECONDS: int = 300

    # Initial super admin (seed script only)
    SUPERADMIN_EMAIL: str = "superadmin@worktrack.local"
    SUPERADMIN_PASSWORD: str = "ChangeMe123!"

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT.lower() == "production"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
