"""
CRM API Module
Aggregates all CRM-related routes
"""
from fastapi import APIRouter

from .leads import router as leads_router
from .accounts import router as accounts_router
from .quotations import router as quotations_router
from .samples import router as samples_router

# Create main CRM router
router = APIRouter(prefix="/crm", tags=["CRM"])

# Include sub-routers
router.include_router(leads_router)
router.include_router(accounts_router)
router.include_router(quotations_router)
router.include_router(samples_router)

__all__ = ["router"]
