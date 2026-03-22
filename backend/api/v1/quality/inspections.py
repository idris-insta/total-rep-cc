"""
Quality API Routes - Inspections
"""
from fastapi import APIRouter, Depends, Query
from typing import Optional

from core.security import get_current_user
from services.quality.service import qc_inspection_service
from models.schemas.quality import QCInspectionCreate

router = APIRouter(prefix="/inspections", tags=["Quality - Inspections"])


@router.get("")
async def get_inspections(
    inspection_type: Optional[str] = None,
    result: Optional[str] = None,
    item_id: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Get all QC inspections with optional filters"""
    filters = {}
    if inspection_type:
        filters['inspection_type'] = inspection_type
    if result:
        filters['result'] = result
    if item_id:
        filters['item_id'] = item_id
    return await qc_inspection_service.get_all_inspections(filters)


@router.get("/failed")
async def get_failed_inspections(
    current_user: dict = Depends(get_current_user)
):
    """Get all failed inspections"""
    return await qc_inspection_service.repo.get_failed_inspections()


@router.get("/stats")
async def get_inspection_stats(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Get inspection statistics"""
    return await qc_inspection_service.get_inspection_stats(start_date, end_date)


@router.get("/{inspection_id}")
async def get_inspection(
    inspection_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get a single inspection"""
    return await qc_inspection_service.get_inspection(inspection_id)


@router.post("")
async def create_inspection(
    data: QCInspectionCreate,
    current_user: dict = Depends(get_current_user)
):
    """Create a new QC inspection"""
    return await qc_inspection_service.create_inspection(data.model_dump(), current_user['id'])
