from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")

    BASE_URL: str = "http://localhost:5173"
    SESSION_TTL_HOURS: int = 2
    PORT: int = 8000


settings = Settings()
