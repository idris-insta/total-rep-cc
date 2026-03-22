"""
Production API Routes - Work Orders
API endpoints for Work Order management
"""
from fastapi import APIRouter, Depends, Query
from typing import Optional

from core.security import get_current_user
from services.production.service import work_order_service, production_entry_service
from models.schemas.production import WorkOrderCreate, WorkOrderUpdate, ProductionEntryCreate

router = APIRouter(prefix="/work-orders", tags=["Production - Work Orders"])


@router.get("")
async def get_work_orders(
    stage: Optional[str] = None,
    status: Optional[str] = None,
    order_sheet_id: Optional[str] = None,
    machine_id: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Get all work orders with optional filters"""
    filters = {}
    if stage:
        filters['stage'] = stage
    if status:
        filters['status'] = status
    if order_sheet_id:
        filters['order_sheet_id'] = order_sheet_id
    if machine_id:
        filters['machine_id'] = machine_id
    return await work_order_service.get_all_work_orders(filters)


@router.get("/in-progress")
async def get_in_progress_work_orders(
    current_user: dict = Depends(get_current_user)
):
    """Get work orders in progress"""
    return await work_order_service.repo.get_in_progress()


@router.get("/{work_order_id}")
async def get_work_order(
    work_order_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get a single work order with production entries"""
    return await work_order_service.get_work_order(work_order_id)


@router.post("")
async def create_work_order(
    data: WorkOrderCreate,
    current_user: dict = Depends(get_current_user)
):
    """Create a new work order"""
    return await work_order_service.create_work_order(data.model_dump(), current_user['id'])


@router.put("/{work_order_id}")
async def update_work_order(
    work_order_id: str,
    data: WorkOrderUpdate,
    current_user: dict = Depends(get_current_user)
):
    """Update an existing work order"""
    update_data = {k: v for k, v in data.model_dump().items() if v is not None}
    return await work_order_service.repo.update_or_raise(work_order_id, update_data, current_user['id'], "Work Order")


@router.put("/{work_order_id}/assign-machine/{machine_id}")
async def assign_machine(
    work_order_id: str,
    machine_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Assign a machine to a work order"""
    return await work_order_service.assign_machine(work_order_id, machine_id, current_user['id'])


@router.put("/{work_order_id}/start")
async def start_work_order(
    work_order_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Start a work order"""
    return await work_order_service.start_work_order(work_order_id, current_user['id'])


@router.put("/{work_order_id}/complete")
async def complete_work_order(
    work_order_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Complete a work order"""
    return await work_order_service.complete_work_order(work_order_id, current_user['id'])


# Production Entry endpoints under work order
@router.get("/{work_order_id}/entries")
async def get_work_order_entries(
    work_order_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get production entries for a work order"""
    return await production_entry_service.get_entries_for_work_order(work_order_id)


@router.post("/{work_order_id}/entries")
async def create_production_entry(
    work_order_id: str,
    data: ProductionEntryCreate,
    current_user: dict = Depends(get_current_user)
):
    """Create a production entry for a work order"""
    entry_data = data.model_dump()
    entry_data['work_order_id'] = work_order_id
    return await production_entry_service.create_entry(entry_data, current_user['id'])
