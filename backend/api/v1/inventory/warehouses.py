"""
Inventory API Routes - Warehouses
API endpoints for Warehouse management
"""
from fastapi import APIRouter, Depends, Query
from typing import Optional

from core.security import get_current_user
from services.inventory.service import warehouse_service
from models.schemas.inventory import WarehouseCreate, WarehouseUpdate

router = APIRouter(prefix="/warehouses", tags=["Inventory - Warehouses"])


@router.get("")
async def get_warehouses(
    active_only: bool = Query(True, description="Only return active warehouses"),
    current_user: dict = Depends(get_current_user)
):
    """Get all warehouses"""
    return await warehouse_service.get_all_warehouses(active_only)


@router.get("/{warehouse_id}")
async def get_warehouse(
    warehouse_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get a single warehouse"""
    return await warehouse_service.get_warehouse(warehouse_id)


@router.get("/{warehouse_id}/stock")
async def get_warehouse_stock(
    warehouse_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get all stock in a warehouse"""
    return await warehouse_service.get_warehouse_stock(warehouse_id)


@router.post("")
async def create_warehouse(
    data: WarehouseCreate,
    current_user: dict = Depends(get_current_user)
):
    """Create a new warehouse"""
    return await warehouse_service.create_warehouse(data.model_dump(), current_user['id'])


@router.put("/{warehouse_id}")
async def update_warehouse(
    warehouse_id: str,
    data: WarehouseUpdate,
    current_user: dict = Depends(get_current_user)
):
    """Update an existing warehouse"""
    update_data = {k: v for k, v in data.model_dump().items() if v is not None}
    return await warehouse_service.update_warehouse(warehouse_id, update_data, current_user['id'])
