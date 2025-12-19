from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    APP_NAME: str

    VAULT_ADDR: str
    VAULT_ROLE_ID: str
    VAULT_SECRET_ID: str

settings = Settings()
