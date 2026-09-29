from fastapi import APIRouter
from app.api.routes.health import router as health_router
from app.api.routes.agents import router as agents_router
from app.api.routes.scripts import router as scripts_router
from app.api.routes.jobs import router as jobs_router
from app.api.routes.artifacts import router as artifacts_router
from app.api.routes.detections import router as detections_router

api_v1_router = APIRouter(prefix="/api/v1")
api_v1_router.include_router(agents_router)
api_v1_router.include_router(scripts_router)
api_v1_router.include_router(jobs_router)
api_v1_router.include_router(artifacts_router)
api_v1_router.include_router(detections_router)

__all__ = ["api_v1_router", "health_router"]
