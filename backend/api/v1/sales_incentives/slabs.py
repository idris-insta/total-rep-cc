"""
Sales Incentives API Routes - Slabs
"""
from fastapi import APIRouter, Depends, Query
from typing import Optional

from core.security import get_current_user, require_manager
from services.sales_incentives.service import incentive_slab_service
from models.schemas.sales_incentives import IncentiveSlabCreate, IncentiveSlabUpdate

router = APIRouter(prefix="/slabs", tags=["Sales Incentives - Slabs"])


@router.get("")
async def get_slabs(
    active_only: bool = Query(True, description="Only return active slabs"),
    current_user: dict = Depends(get_current_user)
):
    """Get all incentive slabs"""
    return await incentive_slab_service.get_all_slabs(active_only)


@router.post("")
async def create_slab(
    data: IncentiveSlabCreate,
    current_user: dict = Depends(require_manager)
):
    """Create a new incentive slab (Manager only)"""
    return await incentive_slab_service.create_slab(data.model_dump(), current_user['id'])


@router.put("/{slab_id}")
async def update_slab(
    slab_id: str,
    data: IncentiveSlabUpdate,
    current_user: dict = Depends(require_manager)
):
    """Update an incentive slab (Manager only)"""
    update_data = {k: v for k, v in data.model_dump().items() if v is not None}
    return await incentive_slab_service.update_slab(slab_id, update_data, current_user['id'])
