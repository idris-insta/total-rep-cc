"""
HRMS API Routes - Attendance
"""
from fastapi import APIRouter, Depends, Query
from typing import Optional

from core.security import get_current_user
from services.hrms.service import attendance_service
from models.schemas.hrms import AttendanceCreate

router = APIRouter(prefix="/attendance", tags=["HRMS - Attendance"])


@router.get("")
async def get_attendance(
    employee_id: Optional[str] = None,
    date: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Get attendance records"""
    return await attendance_service.get_attendance(employee_id, date)


@router.post("")
async def mark_attendance(
    data: AttendanceCreate,
    current_user: dict = Depends(get_current_user)
):
    """Mark attendance for an employee"""
    return await attendance_service.mark_attendance(data.model_dump(), current_user['id'])


@router.post("/{employee_id}/check-in")
async def check_in(
    employee_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Record employee check-in"""
    return await attendance_service.check_in(employee_id, current_user['id'])


@router.post("/{employee_id}/check-out")
async def check_out(
    employee_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Record employee check-out"""
    return await attendance_service.check_out(employee_id, current_user['id'])


@router.get("/{employee_id}/monthly-summary")
async def get_monthly_summary(
    employee_id: str,
    year: int,
    month: int,
    current_user: dict = Depends(get_current_user)
):
    """Get monthly attendance summary"""
    return await attendance_service.get_monthly_summary(employee_id, year, month)
