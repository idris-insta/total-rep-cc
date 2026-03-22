"""
Settings API Routes - Field Registry
"""
from fastapi import APIRouter, Depends, Query
from typing import Optional

from core.security import get_current_user, require_manager
from services.settings.service import field_configuration_service
from models.schemas.settings import FieldConfigurationCreate

router = APIRouter(prefix="/field-registry", tags=["Settings - Field Registry"])


@router.get("")
async def get_configurations(
    module: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Get all field configurations"""
    return await field_configuration_service.get_all_configurations(module)


@router.get("/modules")
async def get_available_modules(
    current_user: dict = Depends(get_current_user)
):
    """Get list of available modules"""
    return await field_configuration_service.get_available_modules()


@router.get("/{module}/{entity}")
async def get_configuration(
    module: str,
    entity: str,
    current_user: dict = Depends(get_current_user)
):
    """Get configuration for a specific module and entity"""
    return await field_configuration_service.get_configuration(module, entity)


@router.post("/{module}/{entity}")
async def save_configuration(
    module: str,
    entity: str,
    data: FieldConfigurationCreate,
    current_user: dict = Depends(require_manager)
):
    """Save field configuration (Manager only)"""
    return await field_configuration_service.save_configuration(module, entity, data.model_dump(), current_user['id'])
