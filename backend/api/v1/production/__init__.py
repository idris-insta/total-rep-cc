"""
Production API Module
Aggregates all Production-related routes
"""
from fastapi import APIRouter

from .machines import router as machines_router
from .order_sheets import router as order_sheets_router
from .work_orders import router as work_orders_router

# Create main Production router
router = APIRouter(prefix="/production", tags=["Production"])

# Include sub-routers
router.include_router(machines_router)
router.include_router(order_sheets_router)
router.include_router(work_orders_router)

__all__ = ["router"]
