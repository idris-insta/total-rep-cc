"""
Services Layer - Business Logic
"""
from .crm.service import lead_service, account_service, quotation_service, sample_service

__all__ = [
    "lead_service",
    "account_service", 
    "quotation_service",
    "sample_service"
]
