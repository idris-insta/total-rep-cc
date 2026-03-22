"""
Inventory API Routes - Stock Adjustments
API endpoints for Stock Adjustment management
"""
from fastapi import APIRouter, Depends, Query
from typing import Optional

from core.security import get_current_user, require_manager
from services.inventory.service import stock_adjustment_service
from models.schemas.inventory import StockAdjustmentCreate

router = APIRouter(prefix="/adjustments", tags=["Inventory - Stock Adjustments"])


@router.get("")
async def get_adjustments(
    status: Optional[str] = None,
    adjustment_type: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Get all stock adjustments with optional filters"""
    query = {}
    if status:
        query['status'] = status
    if adjustment_type:
        query['adjustment_type'] = adjustment_type
    return await stock_adjustment_service.repo.get_all(query)


@router.get("/pending")
async def get_pending_adjustments(
    current_user: dict = Depends(get_current_user)
):
    """Get adjustments pending approval"""
    return await stock_adjustment_service.repo.get_pending_approval()


@router.post("")
async def create_adjustment(
    data: StockAdjustmentCreate,
    current_user: dict = Depends(get_current_user)
):
    """Create a stock adjustment"""
    return await stock_adjustment_service.create_adjustment(data.model_dump(), current_user['id'])


@router.put("/{adjustment_id}/approve")
async def approve_adjustment(
    adjustment_id: str,
    current_user: dict = Depends(require_manager)
):
    """Approve and apply a stock adjustment (Manager/Admin only)"""
    return await stock_adjustment_service.approve_adjustment(adjustment_id, current_user['id'])
