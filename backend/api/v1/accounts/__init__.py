"""
Accounts API Module
"""
from fastapi import APIRouter

from .invoices import router as invoices_router
from .payments import router as payments_router

router = APIRouter(prefix="/accounts", tags=["Accounts"])

router.include_router(invoices_router)
router.include_router(payments_router)

__all__ = ["router"]
