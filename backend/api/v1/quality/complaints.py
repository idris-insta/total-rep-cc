"""
Quality API Routes - Complaints
"""
from fastapi import APIRouter, Depends, Query
from typing import Optional

from core.security import get_current_user
from services.quality.service import customer_complaint_service
from models.schemas.quality import CustomerComplaintCreate, CustomerComplaintUpdate

router = APIRouter(prefix="/complaints", tags=["Quality - Complaints"])


@router.get("")
async def get_complaints(
    status: Optional[str] = None,
    severity: Optional[str] = None,
    account_id: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Get all complaints with optional filters"""
    filters = {}
    if status:
        filters['status'] = status
    if severity:
        filters['severity'] = severity
    if account_id:
        filters['account_id'] = account_id
    return await customer_complaint_service.get_all_complaints(filters)


@router.get("/open")
async def get_open_complaints(
    current_user: dict = Depends(get_current_user)
):
    """Get all open complaints"""
    return await customer_complaint_service.get_open_complaints()


@router.get("/stats")
async def get_complaint_stats(
    current_user: dict = Depends(get_current_user)
):
    """Get complaint statistics"""
    return await customer_complaint_service.get_complaint_stats()


@router.get("/{complaint_id}")
async def get_complaint(
    complaint_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get a single complaint"""
    return await customer_complaint_service.get_complaint(complaint_id)


@router.post("")
async def create_complaint(
    data: CustomerComplaintCreate,
    current_user: dict = Depends(get_current_user)
):
    """Create a new complaint"""
    return await customer_complaint_service.create_complaint(data.model_dump(), current_user['id'])


@router.put("/{complaint_id}/status")
async def update_complaint_status(
    complaint_id: str,
    status: str,
    resolution: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Update complaint status"""
    return await customer_complaint_service.update_status(complaint_id, status, resolution, current_user['id'])
