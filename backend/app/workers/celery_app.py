from celery import Celery
from app.core.config import settings

celery_app = Celery(
    "wifiplan",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=["app.workers.tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_routes={
        "app.workers.tasks.analyze_floor_plan": {"queue": "cv_pipeline"},
        "app.workers.tasks.run_rf_simulation": {"queue": "rf_engine"},
    },
    task_track_started=True,
)
