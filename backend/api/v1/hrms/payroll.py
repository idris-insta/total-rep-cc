"""
HRMS API Routes - Payroll
"""
from fastapi import APIRouter, Depends, Query
from typing import Optional

from core.security import get_current_user, require_manager
from services.hrms.service import payroll_service

router = APIRouter(prefix="/payroll", tags=["HRMS - Payroll"])


@router.get("")
async def get_payroll(
    employee_id: Optional[str] = None,
    year: Optional[int] = None,
    month: Optional[int] = None,
    current_user: dict = Depends(get_current_user)
):
    """Get payroll records"""
    return await payroll_service.get_payroll(employee_id, year, month)


@router.post("/generate")
async def generate_payroll(
    employee_id: str,
    year: int,
    month: int,
    current_user: dict = Depends(require_manager)
):
    """Generate payroll for an employee (Manager only)"""
    return await payroll_service.generate_payroll(employee_id, year, month, current_user['id'])
