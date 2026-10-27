from fastapi import APIRouter
from app.api.v1.endpoints.auth import router as auth_router
from app.api.v1.endpoints.projects import router as projects_router
from app.api.v1.endpoints.floors import router as floors_router
from app.api.v1.endpoints.floorplans import router as floorplans_router
from app.api.v1.endpoints.geometry import router as geometry_router
from app.api.v1.endpoints.ap import catalog_router, placement_router
from app.api.v1.endpoints.jobs import jobs_router, rf_router
from app.api.v1.endpoints.reports import router as reports_router

api_router = APIRouter()

api_router.include_router(auth_router)
api_router.include_router(projects_router)
api_router.include_router(floors_router)
api_router.include_router(floorplans_router)
api_router.include_router(geometry_router)
api_router.include_router(catalog_router)
api_router.include_router(placement_router)
api_router.include_router(jobs_router)
api_router.include_router(rf_router)
api_router.include_router(reports_router)
