"""
Quality Services Package
"""
from .service import (
    qc_inspection_service,
    customer_complaint_service,
    tds_service,
    qc_parameter_service
)

__all__ = [
    "qc_inspection_service",
    "customer_complaint_service",
    "tds_service",
    "qc_parameter_service"
]
