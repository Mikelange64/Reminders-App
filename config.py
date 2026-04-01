from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )
    database_url : str = "sqlite:///./test.db"
    secret_key : SecretStr = SecretStr("temporary-dev-key")
    algorithm : str = "HS256"
    access_token_expire_minutes : int = 30

settings = Settings() # type: ignore[call-arg] # Loaded from .env