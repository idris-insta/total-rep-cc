"""
Production API Routes - Order Sheets
API endpoints for Order Sheet (Production Order) management
"""
from fastapi import APIRouter, Depends, Query
from typing import Optional

from core.security import get_current_user
from services.production.service import order_sheet_service
from models.schemas.production import OrderSheetCreate, OrderSheetUpdate

router = APIRouter(prefix="/order-sheets", tags=["Production - Order Sheets"])


@router.get("")
async def get_order_sheets(
    status: Optional[str] = None,
    customer_id: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Get all order sheets with optional filters"""
    filters = {}
    if status:
        filters['status'] = status
    if customer_id:
        filters['customer_id'] = customer_id
    return await order_sheet_service.get_all_order_sheets(filters)


@router.get("/pending")
async def get_pending_order_sheets(
    current_user: dict = Depends(get_current_user)
):
    """Get pending order sheets"""
    return await order_sheet_service.repo.get_pending()


@router.get("/{order_sheet_id}")
async def get_order_sheet(
    order_sheet_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get a single order sheet with work orders"""
    return await order_sheet_service.get_order_sheet(order_sheet_id)


@router.post("")
async def create_order_sheet(
    data: OrderSheetCreate,
    current_user: dict = Depends(get_current_user)
):
    """Create a new order sheet"""
    return await order_sheet_service.create_order_sheet(data.model_dump(), current_user['id'])


@router.put("/{order_sheet_id}")
async def update_order_sheet(
    order_sheet_id: str,
    data: OrderSheetUpdate,
    current_user: dict = Depends(get_current_user)
):
    """Update an existing order sheet"""
    update_data = {k: v for k, v in data.model_dump().items() if v is not None}
    return await order_sheet_service.update_order_sheet(order_sheet_id, update_data, current_user['id'])


@router.put("/{order_sheet_id}/start")
async def start_production(
    order_sheet_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Start production for an order sheet"""
    return await order_sheet_service.start_production(order_sheet_id, current_user['id'])


@router.put("/{order_sheet_id}/complete")
async def complete_order_sheet(
    order_sheet_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Complete an order sheet"""
    return await order_sheet_service.complete_order_sheet(order_sheet_id, current_user['id'])
