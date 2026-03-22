"""
Procurement API Routes - GRN (Goods Receipt Notes)
"""
from fastapi import APIRouter, Depends, Query
from typing import Optional

from core.security import get_current_user
from services.procurement.service import grn_service
from models.schemas.procurement import GRNCreate

router = APIRouter(prefix="/grn", tags=["Procurement - GRN"])


@router.get("")
async def get_grns(
    po_id: Optional[str] = None,
    supplier_id: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Get all GRNs with optional filters"""
    filters = {}
    if po_id:
        filters['po_id'] = po_id
    if supplier_id:
        filters['supplier_id'] = supplier_id
    return await grn_service.get_all_grns(filters)


@router.post("")
async def create_grn(
    data: GRNCreate,
    current_user: dict = Depends(get_current_user)
):
    """Create a GRN and update inventory"""
    return await grn_service.create_grn(data.model_dump(), current_user['id'])
