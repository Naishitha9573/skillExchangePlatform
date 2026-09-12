from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parents[2]

class Settings(BaseSettings):
    PROJECT_NAME: str = "SkillSwap AI"
    SECRET_KEY: str = ""
    DATABASE_URL: str = "sqlite:///./skillswap.db"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440
    CORS_ORIGINS: str = "http://localhost:5173"
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    GOOGLE_REDIRECT_URI: str = "http://localhost:5173/auth/google/callback"
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-2.5-flash"
    DEMO_MODE: bool = True
    STUN_URLS: str = "stun:stun.l.google.com:19302"
    TURN_URLS: str = ""
    TURN_SECRET: str = ""
    TURN_CREDENTIAL_TTL_SECONDS: int = 14400
    model_config = SettingsConfigDict(env_file=BACKEND_DIR / ".env", extra="ignore")
    @property
    def cors_origins(self):
        return [x.strip() for x in self.CORS_ORIGINS.split(",") if x.strip()]
settings = Settings()
