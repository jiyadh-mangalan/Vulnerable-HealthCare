from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application configuration settings."""

    app_name: str = "Secure Healthcare Management System"
    environment: str = "development"

    # Security
    secret_key: str = "CHANGE_ME_IN_PRODUCTION"
    access_token_expire_minutes: int = 60
    algorithm: str = "HS256"

    # Database
    db_host: str = "db"
    db_port: int = 5432
    db_user: str = "healthcare"
    db_password: str = "healthcare"
    db_name: str = "healthcare"

    # Misc
    enable_docs: bool = True

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()


