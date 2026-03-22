"""
HRMS API Routes - Employees
"""
from fastapi import APIRouter, Depends, Query
from typing import Optional

from core.security import get_current_user
from services.hrms.service import employee_service
from models.schemas.hrms import EmployeeCreate, EmployeeUpdate

router = APIRouter(prefix="/employees", tags=["HRMS - Employees"])


@router.get("")
async def get_employees(
    department: Optional[str] = None,
    status: Optional[str] = None,
    search: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Get all employees with optional filters"""
    filters = {}
    if department:
        filters['department'] = department
    if status:
        filters['status'] = status
    if search:
        filters['search'] = search
    return await employee_service.get_all_employees(filters)


@router.get("/{employee_id}")
async def get_employee(
    employee_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get a single employee"""
    return await employee_service.get_employee(employee_id)


@router.post("")
async def create_employee(
    data: EmployeeCreate,
    current_user: dict = Depends(get_current_user)
):
    """Create a new employee"""
    return await employee_service.create_employee(data.model_dump(), current_user['id'])


@router.put("/{employee_id}")
async def update_employee(
    employee_id: str,
    data: EmployeeUpdate,
    current_user: dict = Depends(get_current_user)
):
    """Update an existing employee"""
    update_data = {k: v for k, v in data.model_dump().items() if v is not None}
    return await employee_service.update_employee(employee_id, update_data, current_user['id'])


@router.put("/{employee_id}/terminate")
async def terminate_employee(
    employee_id: str,
    termination_date: str,
    reason: str,
    current_user: dict = Depends(get_current_user)
):
    """Terminate an employee"""
    return await employee_service.terminate_employee(employee_id, termination_date, reason, current_user['id'])
