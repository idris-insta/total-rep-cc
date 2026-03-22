"""
Sales Incentives API Routes - Targets
"""
from fastapi import APIRouter, Depends, Query
from typing import Optional

from core.security import get_current_user, require_manager
from services.sales_incentives.service import sales_target_service
from models.schemas.sales_incentives import SalesTargetCreate, SalesTargetUpdate

router = APIRouter(prefix="/targets", tags=["Sales Incentives - Targets"])


@router.get("")
async def get_targets(
    employee_id: Optional[str] = None,
    period: Optional[str] = None,
    status: Optional[str] = None,
    target_type: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Get all sales targets with optional filters"""
    filters = {}
    if employee_id:
        filters['employee_id'] = employee_id
    if period:
        filters['period'] = period
    if status:
        filters['status'] = status
    if target_type:
        filters['target_type'] = target_type
    return await sales_target_service.get_all_targets(filters)


@router.get("/active")
async def get_active_targets(
    current_user: dict = Depends(get_current_user)
):
    """Get all active targets"""
    return await sales_target_service.repo.get_active_targets()


@router.get("/{target_id}")
async def get_target(
    target_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get a single target"""
    return await sales_target_service.get_target(target_id)


@router.post("")
async def create_target(
    data: SalesTargetCreate,
    current_user: dict = Depends(require_manager)
):
    """Create a new sales target (Manager only)"""
    return await sales_target_service.create_target(data.model_dump(), current_user['id'])


@router.put("/{target_id}/achievement")
async def update_achievement(
    target_id: str,
    achieved_amount: float,
    achieved_quantity: int = 0,
    current_user: dict = Depends(get_current_user)
):
    """Update target achievement"""
    return await sales_target_service.update_achievement(target_id, achieved_amount, achieved_quantity, current_user['id'])
