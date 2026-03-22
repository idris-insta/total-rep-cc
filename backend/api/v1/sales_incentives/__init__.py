"""
Sales Incentives API Module
"""
from fastapi import APIRouter

from .targets import router as targets_router
from .slabs import router as slabs_router
from .payouts import router as payouts_router

router = APIRouter(prefix="/sales-incentives", tags=["Sales Incentives"])

router.include_router(targets_router)
router.include_router(slabs_router)
router.include_router(payouts_router)

__all__ = ["router"]
