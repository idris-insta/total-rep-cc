"""
Settings API Module
"""
from fastapi import APIRouter

from .field_registry import router as field_registry_router
from .system import router as system_router
from .branches import router as branches_router
from .users import router as users_router

router = APIRouter(prefix="/settings", tags=["Settings"])

router.include_router(field_registry_router)
router.include_router(system_router)
router.include_router(branches_router)
router.include_router(users_router)

__all__ = ["router"]
