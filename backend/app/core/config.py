# backend/app/core/config.py
from pydantic_settings import BaseSettings
class Settings(BaseSettings):
    # App
    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "info"
    API_V1_PREFIX: str = "/api/v1"
    ALLOWED_ORIGINS: str = "http://localhost:3000,http://127.0.0.1:3000"

    # Auth
    SECRET_KEY: str = "change-me-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Database
    
    DATABASE_URL: str = "postgresql://wifiplan:wifiplan@postgres:5432/wifiplan"

    # Redis / Celery
   
    REDIS_URL: str = "redis://redis:6379/0"
    CELERY_BROKER_URL: str = "redis://redis:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://redis:6379/1"

    # S3 / MinIO
    S3_ENDPOINT_URL: str = "http://minio:9000"  # Para conexiones internas
    S3_PUBLIC_URL: str = "http://localhost:9000"  # Para URLs públicas
    S3_ACCESS_KEY: str = "minioadmin"
    S3_SECRET_KEY: str = "minioadmin"
    S3_BUCKET_FLOORPLANS: str = "floorplans"
    S3_BUCKET_HEATMAPS: str = "heatmaps"
    S3_REGION: str = "us-east-1"

    # Model inference (stub)
    MODEL_INFERENCE_URL: str = "http://localhost:8010"
    MODEL_INFERENCE_ENABLED: bool = False

    @property
    def allowed_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",") if origin.strip()]

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
