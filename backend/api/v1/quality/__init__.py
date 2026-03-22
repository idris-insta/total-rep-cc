"""
Quality API Module
"""
from fastapi import APIRouter

from .inspections import router as inspections_router
from .complaints import router as complaints_router

router = APIRouter(prefix="/quality", tags=["Quality"])

router.include_router(inspections_router)
router.include_router(complaints_router)

__all__ = ["router"]
