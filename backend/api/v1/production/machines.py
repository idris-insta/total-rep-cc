"""
Production API Routes - Machines
API endpoints for Machine management
"""
from fastapi import APIRouter, Depends, Query
from typing import Optional

from core.security import get_current_user
from services.production.service import machine_service
from models.schemas.production import MachineCreate, MachineUpdate

router = APIRouter(prefix="/machines", tags=["Production - Machines"])


@router.get("")
async def get_machines(
    machine_type: Optional[str] = None,
    status: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Get all machines with optional filters"""
    filters = {}
    if machine_type:
        filters['machine_type'] = machine_type
    if status:
        filters['status'] = status
    return await machine_service.get_all_machines(filters)


@router.get("/available")
async def get_available_machines(
    current_user: dict = Depends(get_current_user)
):
    """Get machines available for production"""
    return await machine_service.repo.get_available()


@router.get("/{machine_id}")
async def get_machine(
    machine_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get a single machine"""
    return await machine_service.get_machine(machine_id)


@router.get("/{machine_id}/utilization")
async def get_machine_utilization(
    machine_id: str,
    start_date: str,
    end_date: str,
    current_user: dict = Depends(get_current_user)
):
    """Get machine utilization metrics"""
    return await machine_service.get_machine_utilization(machine_id, start_date, end_date)


@router.post("")
async def create_machine(
    data: MachineCreate,
    current_user: dict = Depends(get_current_user)
):
    """Create a new machine"""
    return await machine_service.create_machine(data.model_dump(), current_user['id'])


@router.put("/{machine_id}")
async def update_machine(
    machine_id: str,
    data: MachineUpdate,
    current_user: dict = Depends(get_current_user)
):
    """Update an existing machine"""
    update_data = {k: v for k, v in data.model_dump().items() if v is not None}
    return await machine_service.update_machine(machine_id, update_data, current_user['id'])
