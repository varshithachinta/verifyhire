from pydantic_settings import BaseSettings
from pydantic import field_validator
from pathlib import Path


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "postgresql+asyncpg://verifyhire_user:verifyhire_pass@localhost:5432/verifyhire_db"
    SYNC_DATABASE_URL: str = "postgresql://verifyhire_user:verifyhire_pass@localhost:5432/verifyhire_db"

    # JWT
    SECRET_KEY: str = "change-this-in-production-minimum-32-characters"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # File Storage
    UPLOAD_DIR: str = "uploads"
    MAX_VIDEO_SIZE_MB: int = 100

    # AI Models
    WHISPER_MODEL: str = "base"
    YOLO_MODEL: str = "yolov8n-face.pt"
    SBERT_MODEL: str = "all-MiniLM-L6-v2"

    # App
    APP_NAME: str = "VerifyHire"
    APP_ENV: str = "development"
    CORS_ORIGINS: str = "http://localhost:3000"

    model_config = {"env_file": ".env", "extra": "ignore"}

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",")]

    @property
    def videos_dir(self) -> Path:
        return Path(self.UPLOAD_DIR) / "videos"

    @property
    def audio_dir(self) -> Path:
        return Path(self.UPLOAD_DIR) / "audio"

    @property
    def faces_dir(self) -> Path:
        return Path(self.UPLOAD_DIR) / "faces"

    @property
    def max_video_bytes(self) -> int:
        return self.MAX_VIDEO_SIZE_MB * 1024 * 1024


settings = Settings()
