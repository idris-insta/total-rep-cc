"""
HRMS API Module
"""
from fastapi import APIRouter

from .employees import router as employees_router
from .attendance import router as attendance_router
from .leave_requests import router as leave_requests_router
from .payroll import router as payroll_router

router = APIRouter(prefix="/hrms", tags=["HRMS"])

router.include_router(employees_router)
router.include_router(attendance_router)
router.include_router(leave_requests_router)
router.include_router(payroll_router)

__all__ = ["router"]
