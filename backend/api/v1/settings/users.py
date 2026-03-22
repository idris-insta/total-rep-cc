"""
Settings API Routes - Users
"""
from fastapi import APIRouter, Depends, Query
from typing import Optional

from core.security import get_current_user, require_admin
from services.settings.service import user_service
from models.schemas.settings import UserCreate, UserUpdate

router = APIRouter(prefix="/users", tags=["Settings - Users"])


@router.get("")
async def get_users(
    role: Optional[str] = None,
    is_active: Optional[bool] = None,
    current_user: dict = Depends(get_current_user)
):
    """Get all users with optional filters"""
    filters = {}
    if role:
        filters['role'] = role
    if is_active is not None:
        filters['is_active'] = is_active
    users = await user_service.get_all_users(filters)
    # Remove sensitive fields
    for user in users:
        user.pop('hashed_password', None)
    return users


@router.get("/{user_id}")
async def get_user(
    user_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get a single user"""
    user = await user_service.get_user(user_id)
    user.pop('hashed_password', None)
    return user


@router.post("")
async def create_user(
    data: UserCreate,
    current_user: dict = Depends(require_admin)
):
    """Create a new user (Admin only)"""
    user = await user_service.create_user(data.model_dump(), current_user['id'])
    user.pop('hashed_password', None)
    return user


@router.put("/{user_id}")
async def update_user(
    user_id: str,
    data: UserUpdate,
    current_user: dict = Depends(require_admin)
):
    """Update a user (Admin only)"""
    update_data = {k: v for k, v in data.model_dump().items() if v is not None}
    user = await user_service.update_user(user_id, update_data, current_user['id'])
    user.pop('hashed_password', None)
    return user


@router.put("/{user_id}/deactivate")
async def deactivate_user(
    user_id: str,
    current_user: dict = Depends(require_admin)
):
    """Deactivate a user (Admin only)"""
    user = await user_service.deactivate_user(user_id, current_user['id'])
    user.pop('hashed_password', None)
    return user
