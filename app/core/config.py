from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="", case_sensitive=False)

    mongodb_uri: str = "mongodb://localhost:27017"
    db_name: str = "ynot_hub"


settings = Settings()
