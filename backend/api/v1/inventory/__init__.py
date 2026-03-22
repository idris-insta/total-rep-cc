"""
Inventory API Module
Aggregates all Inventory-related routes
"""
from fastapi import APIRouter

from .items import router as items_router
from .warehouses import router as warehouses_router
from .transfers import router as transfers_router
from .adjustments import router as adjustments_router

# Create main Inventory router
router = APIRouter(prefix="/inventory", tags=["Inventory"])

# Include sub-routers
router.include_router(items_router)
router.include_router(warehouses_router)
router.include_router(transfers_router)
router.include_router(adjustments_router)

__all__ = ["router"]
