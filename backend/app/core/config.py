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
    # Public base URL resumes are served from (R2 custom domain or the
    # bucket's r2.dev URL). Distinct from r2_endpoint_url, which is the
    # private S3 API endpoint used to upload — that endpoint is not
    # publicly fetchable.
    r2_public_url_base: str = ""
    ai_api_key: str = ""


settings = Settings()
