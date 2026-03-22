"""
CRM API Routes - Accounts
API endpoints for Account management
"""
from fastapi import APIRouter, Depends, Query
from typing import Optional

from core.security import get_current_user
from services.crm.service import account_service
from models.schemas.crm import AccountCreate, AccountUpdate

router = APIRouter(prefix="/accounts", tags=["CRM - Accounts"])


@router.get("")
async def get_accounts(
    account_type: str = Query("all", description="Filter by account type"),
    current_user: dict = Depends(get_current_user)
):
    """Get all accounts with optional type filter"""
    return await account_service.get_all_accounts(account_type)


@router.get("/{account_id}")
async def get_account(
    account_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get a single account with balance information"""
    return await account_service.get_account(account_id)


@router.post("")
async def create_account(
    data: AccountCreate,
    current_user: dict = Depends(get_current_user)
):
    """Create a new account"""
    return await account_service.create_account(data.model_dump(), current_user['id'])


@router.put("/{account_id}")
async def update_account(
    account_id: str,
    data: AccountUpdate,
    current_user: dict = Depends(get_current_user)
):
    """Update an existing account"""
    update_data = {k: v for k, v in data.model_dump().items() if v is not None}
    return await account_service.update_account(account_id, update_data, current_user['id'])


@router.delete("/{account_id}")
async def delete_account(
    account_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Delete an account"""
    await account_service.delete_account(account_id)
    return {"message": "Account deleted successfully"}


@router.get("/{account_id}/health")
async def get_customer_health(
    account_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get customer health metrics"""
    return await account_service.get_customer_health(account_id)
