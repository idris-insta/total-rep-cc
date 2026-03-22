"""
Settings API Routes - System Settings
"""
from fastapi import APIRouter, Depends, Query
from typing import Optional, Any

from core.security import get_current_user, require_manager
from services.settings.service import system_setting_service
from models.schemas.settings import SystemSettingCreate

router = APIRouter(prefix="/system", tags=["Settings - System"])


@router.get("")
async def get_settings(
    category: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Get all system settings"""
    return await system_setting_service.get_all_settings(category)


@router.get("/{key}")
async def get_setting(
    key: str,
    current_user: dict = Depends(get_current_user)
):
    """Get a specific setting"""
    value = await system_setting_service.get_setting(key)
    return {"key": key, "value": value}


@router.post("")
async def set_setting(
    data: SystemSettingCreate,
    current_user: dict = Depends(require_manager)
):
    """Set a system setting (Manager only)"""
    return await system_setting_service.set_setting(data.key, data.value, current_user['id'], data.category)
