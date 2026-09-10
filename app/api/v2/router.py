from fastapi import APIRouter

from app.api.v2.auth import router as auth_router
from app.api.v2.health import router as health_router
from app.api.v2.predict import router as predict_router

api_v2_router = APIRouter(prefix="/v2")
api_v2_router.include_router(health_router)
api_v2_router.include_router(auth_router)
api_v2_router.include_router(predict_router)
