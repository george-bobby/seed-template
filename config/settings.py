from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class AppConfig(BaseSettings):
    LOG_LEVEL: str = "INFO"
    ANTHROPIC_API_KEY: str = ""
    DEFAULT_MODEL: str = "claude-3-5-haiku-20241022"

    # Application-specific configuration
    APP_API_URL: str = "http://localhost:80"
    APP_ADMIN_EMAIL: str = "admin"
    APP_ADMIN_PASSWORD: str = "admin"
    APP_SITE_NAME: str = "MyApp"
    APP_OWNER_ID: int = 1
    APP_RECRUITER_ID: int = 1

    DATABASE_URL: str = "mysql://dev:dev@localhost:3306/app_db"
    DATA_PATH: Path = Path(__file__).parent.parent.joinpath("data")
    DATA_THEME_SUBJECT: str = "a technology consulting company"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
        case_sensitive=False,
        extra="ignore",
    )

settings = AppConfig()
