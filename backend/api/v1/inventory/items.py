"""
Inventory API Routes - Items
API endpoints for Item management
"""
from fastapi import APIRouter, Depends, Query
from typing import Optional

from core.security import get_current_user
from services.inventory.service import item_service
from models.schemas.inventory import ItemCreate, ItemUpdate

router = APIRouter(prefix="/items", tags=["Inventory - Items"])


@router.get("")
async def get_items(
    category: Optional[str] = None,
    item_type: Optional[str] = None,
    search: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Get all items with optional filters"""
    filters = {}
    if category:
        filters['category'] = category
    if item_type:
        filters['item_type'] = item_type
    if search:
        filters['search'] = search
    return await item_service.get_all_items(filters)


@router.get("/low-stock")
async def get_low_stock_items(
    current_user: dict = Depends(get_current_user)
):
    """Get items below reorder level"""
    return await item_service.get_low_stock_items()


@router.get("/{item_id}")
async def get_item(
    item_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get a single item"""
    return await item_service.get_item(item_id)


@router.get("/{item_id}/stock")
async def get_item_stock(
    item_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get stock summary for an item"""
    return await item_service.get_stock_summary(item_id)


@router.post("")
async def create_item(
    data: ItemCreate,
    current_user: dict = Depends(get_current_user)
):
    """Create a new item"""
    return await item_service.create_item(data.model_dump(), current_user['id'])


@router.put("/{item_id}")
async def update_item(
    item_id: str,
    data: ItemUpdate,
    current_user: dict = Depends(get_current_user)
):
    """Update an existing item"""
    update_data = {k: v for k, v in data.model_dump().items() if v is not None}
    return await item_service.update_item(item_id, update_data, current_user['id'])


@router.delete("/{item_id}")
async def delete_item(
    item_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Delete an item"""
    await item_service.delete_item(item_id)
    return {"message": "Item deleted successfully"}
