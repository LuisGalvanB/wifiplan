#backend>app>main.py
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.api.v1.router import api_router

logging.basicConfig(level=settings.LOG_LEVEL.upper())
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup / shutdown hooks."""
    logger.info("Starting WifiPlan API...")

    # Ensure S3 buckets exist
    try:
        from app.services.storage import ensure_buckets
        ensure_buckets()
        logger.info("S3 buckets ready")
    except Exception as e:
        logger.warning(f"S3 setup failed (storage unavailable?): {e}")

    yield

    logger.info("Shutting down WifiPlan API")


app = FastAPI(
    title="WifiPlan API",
    description="Browser-based wireless network planning platform",
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)


#--------------------------
#CORS (Cross-Origin Resource Sharing)  permite que la aplicación web (frontend) acceda a una API.

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

#--------------------------

app.include_router(api_router, prefix=settings.API_V1_PREFIX)


@app.get("/health")
def health():
    return {"status": "ok", "version": "0.1.0"}
