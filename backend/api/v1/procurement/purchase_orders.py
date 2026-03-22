"""
Procurement API Routes - Purchase Orders
"""
from fastapi import APIRouter, Depends, Query
from typing import Optional

from core.security import get_current_user
from services.procurement.service import purchase_order_service
from models.schemas.procurement import PurchaseOrderCreate, PurchaseOrderUpdate

router = APIRouter(prefix="/purchase-orders", tags=["Procurement - Purchase Orders"])


@router.get("")
async def get_purchase_orders(
    status: Optional[str] = None,
    supplier_id: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Get all purchase orders with optional filters"""
    filters = {}
    if status:
        filters['status'] = status
    if supplier_id:
        filters['supplier_id'] = supplier_id
    return await purchase_order_service.get_all_orders(filters)


@router.get("/pending")
async def get_pending_orders(
    current_user: dict = Depends(get_current_user)
):
    """Get pending purchase orders"""
    return await purchase_order_service.repo.get_pending()


@router.get("/{order_id}")
async def get_purchase_order(
    order_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get a single purchase order"""
    return await purchase_order_service.get_order(order_id)


@router.post("")
async def create_purchase_order(
    data: PurchaseOrderCreate,
    current_user: dict = Depends(get_current_user)
):
    """Create a new purchase order"""
    return await purchase_order_service.create_order(data.model_dump(), current_user['id'])


@router.put("/{order_id}/send")
async def send_order(
    order_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Mark PO as sent to supplier"""
    return await purchase_order_service.send_order(order_id, current_user['id'])


@router.put("/{order_id}/cancel")
async def cancel_order(
    order_id: str,
    reason: str,
    current_user: dict = Depends(get_current_user)
):
    """Cancel a purchase order"""
    return await purchase_order_service.cancel_order(order_id, reason, current_user['id'])
