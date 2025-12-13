from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+asyncpg://resplanet:resplanet123@localhost:5432/resplanet_db"
    REDIS_URL: str = "redis://localhost:6379/0"

    GOOGLE_API_KEY: str
    
    SECRET_KEY: str = "supersecret"

    class Config:
        env_file = ".env"
        extra = "ignore" 

settings = Settings()