"""
Settings API Routes - Branches
"""
from fastapi import APIRouter, Depends, Query
from typing import Optional

from core.security import get_current_user, require_manager
from services.settings.service import branch_service
from models.schemas.settings import BranchCreate, BranchUpdate

router = APIRouter(prefix="/branches", tags=["Settings - Branches"])


@router.get("")
async def get_branches(
    active_only: bool = Query(True, description="Only return active branches"),
    current_user: dict = Depends(get_current_user)
):
    """Get all branches"""
    return await branch_service.get_all_branches(active_only)


@router.get("/head-office")
async def get_head_office(
    current_user: dict = Depends(get_current_user)
):
    """Get the head office branch"""
    return await branch_service.get_head_office()


@router.get("/{branch_id}")
async def get_branch(
    branch_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get a single branch"""
    return await branch_service.get_branch(branch_id)


@router.post("")
async def create_branch(
    data: BranchCreate,
    current_user: dict = Depends(require_manager)
):
    """Create a new branch (Manager only)"""
    return await branch_service.create_branch(data.model_dump(), current_user['id'])


@router.put("/{branch_id}")
async def update_branch(
    branch_id: str,
    data: BranchUpdate,
    current_user: dict = Depends(require_manager)
):
    """Update a branch (Manager only)"""
    update_data = {k: v for k, v in data.model_dump().items() if v is not None}
    return await branch_service.update_branch(branch_id, update_data, current_user['id'])
