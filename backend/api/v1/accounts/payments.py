"""
Accounts API Routes - Payments
"""
from fastapi import APIRouter, Depends, Query
from typing import Optional

from core.security import get_current_user
from services.accounts.service import payment_service
from models.schemas.accounts import PaymentCreate

router = APIRouter(prefix="/payments", tags=["Accounts - Payments"])


@router.get("")
async def get_payments(
    payment_type: Optional[str] = None,
    account_id: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Get all payments with optional filters"""
    filters = {}
    if payment_type:
        filters['payment_type'] = payment_type
    if account_id:
        filters['account_id'] = account_id
    return await payment_service.get_all_payments(filters)


@router.post("")
async def create_payment(
    data: PaymentCreate,
    current_user: dict = Depends(get_current_user)
):
    """Create a payment"""
    return await payment_service.create_payment(data.model_dump(), current_user['id'])
