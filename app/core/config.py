from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="",
        case_sensitive=False,
        env_file=".env",
        env_file_encoding="utf-8",
    )

    mongodb_uri: str = "mongodb://localhost:27017"
    db_name: str = "ynot_hub"

    # OAuth / Auth settings
    oauth_provider: str = "google"
    oauth_client_id: str = ""
    oauth_client_secret: str = ""
    oauth_redirect_uri: str = "http://localhost:8000/auth/callback"

    jwt_secret_key: str = "change-me"
    jwt_algorithm: str = "HS256"
    jwt_expires_minutes: int = 60

    session_cookie_name: str = "ynot_session"
    session_cookie_secure: bool = False
    session_cookie_samesite: str = "lax"

    resource_upload_dir: str = "uploads/resources"


settings = Settings()
