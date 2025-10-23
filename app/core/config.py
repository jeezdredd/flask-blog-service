from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    database_url: str
    app_debug: bool = False

    model_config = SettingsConfigDict(env_file=".env", env_prefix="", case_sensitive=False)

settings = Settings(database_url="postgresql+psycopg2://microblog:microblog@db:5432/microblog")