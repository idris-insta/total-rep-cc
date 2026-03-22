"""
API V1 Package - Version 1 of the API
"""
from .crm import router as crm_router
from .inventory import router as inventory_router
from .production import router as production_router
from .accounts import router as accounts_router
from .hrms import router as hrms_router
from .procurement import router as procurement_router
from .quality import router as quality_router
from .sales_incentives import router as sales_incentives_router
from .settings import router as settings_router

__all__ = [
    "crm_router",
    "inventory_router",
    "production_router",
    "accounts_router",
    "hrms_router",
    "procurement_router",
    "quality_router",
    "sales_incentives_router",
    "settings_router"
]
