import os
from typing import Optional
from dotenv import load_dotenv

load_dotenv()


class Settings:
    PROJECT_NAME: str = "YuktiSync"
    VERSION: str = "1.0.0"
    API_PREFIX: str = "/api"
    SECRET_KEY: str = os.getenv("SECRET_KEY", "yuktisync-dev-secret-key-32bytes-long-123456")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    MONGO_URI: str = os.getenv("MONGO_URI", "mongodb://localhost:27017")
    DATABASE_NAME: str = "yuktisync_db"
    OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY", None)
    ANTHROPIC_API_KEY: Optional[str] = os.getenv("ANTHROPIC_API_KEY", None)
    INVITE_TOKEN_EXPIRE_DAYS: int = 7


settings = Settings()
