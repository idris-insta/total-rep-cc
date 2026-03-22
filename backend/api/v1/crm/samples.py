"""
CRM API Routes - Samples
API endpoints for Sample management
"""
from fastapi import APIRouter, Depends, Query
from typing import Optional

from core.security import get_current_user
from services.crm.service import sample_service
from models.schemas.crm import SampleCreate, SampleUpdate

router = APIRouter(prefix="/samples", tags=["CRM - Samples"])


@router.get("")
async def get_samples(
    status: Optional[str] = None,
    account_id: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Get all samples with optional filters"""
    filters = {}
    if status:
        filters['status'] = status
    if account_id:
        filters['account_id'] = account_id
    return await sample_service.get_all_samples(filters)


@router.get("/pending-feedback")
async def get_pending_feedback(
    current_user: dict = Depends(get_current_user)
):
    """Get samples pending feedback"""
    return await sample_service.repo.get_pending_feedback()


@router.get("/{sample_id}")
async def get_sample(
    sample_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get a single sample"""
    return await sample_service.repo.get_by_id_or_raise(sample_id, "Sample")


@router.post("")
async def create_sample(
    data: SampleCreate,
    current_user: dict = Depends(get_current_user)
):
    """Create a new sample request"""
    return await sample_service.create_sample(data.model_dump(), current_user['id'])


@router.put("/{sample_id}")
async def update_sample(
    sample_id: str,
    data: SampleUpdate,
    current_user: dict = Depends(get_current_user)
):
    """Update an existing sample"""
    update_data = {k: v for k, v in data.model_dump().items() if v is not None}
    return await sample_service.repo.update_or_raise(sample_id, update_data, current_user['id'], "Sample")


@router.put("/{sample_id}/status")
async def update_sample_status(
    sample_id: str,
    status: str,
    current_user: dict = Depends(get_current_user)
):
    """Update sample status"""
    return await sample_service.update_status(sample_id, status, current_user['id'])


@router.post("/{sample_id}/feedback")
async def record_sample_feedback(
    sample_id: str,
    feedback: str,
    status: str = "feedback_received",
    current_user: dict = Depends(get_current_user)
):
    """Record sample feedback"""
    return await sample_service.record_feedback(sample_id, feedback, status, current_user['id'])


@router.delete("/{sample_id}")
async def delete_sample(
    sample_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Delete a sample"""
    await sample_service.repo.delete_or_raise(sample_id, "Sample")
    return {"message": "Sample deleted successfully"}
