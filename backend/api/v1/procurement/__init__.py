"""
Procurement API Module
"""
from fastapi import APIRouter

from .suppliers import router as suppliers_router
from .purchase_orders import router as purchase_orders_router
from .grn import router as grn_router

router = APIRouter(prefix="/procurement", tags=["Procurement"])

router.include_router(suppliers_router)
router.include_router(purchase_orders_router)
router.include_router(grn_router)

__all__ = ["router"]
