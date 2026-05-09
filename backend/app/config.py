from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    DATABASE_URL: str = "mysql+pymysql://openclaw:openclaw_pass_2024@localhost:3306/openclaw_center"
    JWT_SECRET_KEY: str = "openclaw-jwt-secret-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 480
    ENCRYPTION_KEY: str = "tgVInpjWvO3JPbQ5auy-zETHeI7QgYv6z8sqbW0LBVg="
    UPLOAD_DIR: str = "./uploads"
    CORS_ORIGINS: List[str] = ["http://localhost:5173", "http://localhost:3000"]

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "ignore"}


settings = Settings()
