"""
Procurement API Routes - Suppliers
"""
from fastapi import APIRouter, Depends, Query
from typing import Optional

from core.security import get_current_user
from services.procurement.service import supplier_service
from models.schemas.procurement import SupplierCreate, SupplierUpdate

router = APIRouter(prefix="/suppliers", tags=["Procurement - Suppliers"])


@router.get("")
async def get_suppliers(
    supplier_type: Optional[str] = None,
    search: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Get all suppliers with optional filters"""
    filters = {}
    if supplier_type:
        filters['supplier_type'] = supplier_type
    if search:
        filters['search'] = search
    return await supplier_service.get_all_suppliers(filters)


@router.get("/{supplier_id}")
async def get_supplier(
    supplier_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get a single supplier"""
    return await supplier_service.get_supplier(supplier_id)


@router.post("")
async def create_supplier(
    data: SupplierCreate,
    current_user: dict = Depends(get_current_user)
):
    """Create a new supplier"""
    return await supplier_service.create_supplier(data.model_dump(), current_user['id'])


@router.put("/{supplier_id}")
async def update_supplier(
    supplier_id: str,
    data: SupplierUpdate,
    current_user: dict = Depends(get_current_user)
):
    """Update an existing supplier"""
    update_data = {k: v for k, v in data.model_dump().items() if v is not None}
    return await supplier_service.update_supplier(supplier_id, update_data, current_user['id'])
