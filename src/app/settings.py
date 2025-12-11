from functools import lru_cache
from pydantic import BaseSettings

class Settings(BaseSettings): # load the settings and the .env
    app_name: str = "News_Sentiment_Analyzer"
    environment: str = "dev"
    api_timeout_seconds: int = 30
    
    class Config:
        env_file = ".env"







@ lru_cache
def get_settings() -> BaseSettings:
    return Settings()