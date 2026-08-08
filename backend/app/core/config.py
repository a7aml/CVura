from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = ""
    migrations_database_url: str = ""
    jwt_secret: str = ""
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 7
    cors_allowed_origins: str = ""
    google_client_id: str = ""
    r2_bucket_name: str = ""
    r2_endpoint_url: str = ""
    r2_access_key_id: str = ""
    r2_secret_access_key: str = ""
    ai_api_key: str = ""
    free_tier_resume_limit: int = 3

    @field_validator("jwt_secret")
    @classmethod
    def _require_jwt_secret(cls, value: str) -> str:
        # An empty secret would make every access/refresh token trivially
        # forgeable (jwt.encode/decode accept "" as a valid HS256 key) — fail
        # startup loudly rather than silently running with a forgeable one.
        if not value:
            raise ValueError("JWT_SECRET must be set")
        return value


settings = Settings()
