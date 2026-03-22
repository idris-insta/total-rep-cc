"""
HRMS API Routes - Leave Requests
"""
from fastapi import APIRouter, Depends, Query
from typing import Optional

from core.security import get_current_user, require_manager
from services.hrms.service import leave_request_service
from models.schemas.hrms import LeaveRequestCreate

router = APIRouter(prefix="/leave-requests", tags=["HRMS - Leave Requests"])


@router.get("")
async def get_leave_requests(
    status: Optional[str] = None,
    employee_id: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Get all leave requests"""
    filters = {}
    if status:
        filters['status'] = status
    if employee_id:
        filters['employee_id'] = employee_id
    return await leave_request_service.get_all_requests(filters)


@router.get("/pending")
async def get_pending_requests(
    current_user: dict = Depends(get_current_user)
):
    """Get all pending leave requests"""
    return await leave_request_service.get_pending_requests()


@router.post("")
async def create_leave_request(
    data: LeaveRequestCreate,
    current_user: dict = Depends(get_current_user)
):
    """Create a leave request"""
    return await leave_request_service.create_request(data.model_dump(), current_user['id'])


@router.put("/{request_id}/approve")
async def approve_request(
    request_id: str,
    current_user: dict = Depends(require_manager)
):
    """Approve a leave request (Manager only)"""
    return await leave_request_service.approve_request(request_id, current_user['id'])


@router.put("/{request_id}/reject")
async def reject_request(
    request_id: str,
    reason: str,
    current_user: dict = Depends(require_manager)
):
    """Reject a leave request (Manager only)"""
    return await leave_request_service.reject_request(request_id, reason, current_user['id'])
