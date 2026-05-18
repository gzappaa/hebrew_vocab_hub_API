from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    DATABASE_URL: str
    ENV: str = "env"
    DEBUG: bool = False

    model_config = SettingsConfigDict(env_file=".env.dev")

settings = Settings()