"""
Inventory API Routes - Stock Transfers
API endpoints for Stock Transfer management
"""
from fastapi import APIRouter, Depends, Query
from typing import Optional

from core.security import get_current_user
from services.inventory.service import stock_transfer_service
from models.schemas.inventory import StockTransferCreate, StockTransferUpdate

router = APIRouter(prefix="/transfers", tags=["Inventory - Stock Transfers"])


@router.get("")
async def get_transfers(
    status: Optional[str] = None,
    from_warehouse: Optional[str] = None,
    to_warehouse: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Get all stock transfers with optional filters"""
    filters = {}
    if status:
        filters['status'] = status
    if from_warehouse:
        filters['from_warehouse'] = from_warehouse
    if to_warehouse:
        filters['to_warehouse'] = to_warehouse
    return await stock_transfer_service.get_all_transfers(filters)


@router.post("")
async def create_transfer(
    data: StockTransferCreate,
    current_user: dict = Depends(get_current_user)
):
    """Create a new stock transfer"""
    return await stock_transfer_service.create_transfer(data.model_dump(), current_user['id'])


@router.put("/{transfer_id}/dispatch")
async def dispatch_transfer(
    transfer_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Dispatch a transfer (mark as in transit)"""
    return await stock_transfer_service.dispatch_transfer(transfer_id, current_user['id'])


@router.put("/{transfer_id}/receive")
async def receive_transfer(
    transfer_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Receive a transfer at destination warehouse"""
    return await stock_transfer_service.receive_transfer(transfer_id, current_user['id'])
