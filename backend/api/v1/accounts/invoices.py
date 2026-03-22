"""
Accounts API Routes - Invoices
"""
from fastapi import APIRouter, Depends, Query
from typing import Optional

from core.security import get_current_user
from services.accounts.service import invoice_service
from models.schemas.accounts import InvoiceCreate, InvoiceUpdate

router = APIRouter(prefix="/invoices", tags=["Accounts - Invoices"])


@router.get("")
async def get_invoices(
    invoice_type: Optional[str] = None,
    status: Optional[str] = None,
    account_id: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Get all invoices with optional filters"""
    filters = {}
    if invoice_type:
        filters['invoice_type'] = invoice_type
    if status:
        filters['status'] = status
    if account_id:
        filters['account_id'] = account_id
    return await invoice_service.get_all_invoices(filters)


@router.get("/overdue")
async def get_overdue_invoices(
    current_user: dict = Depends(get_current_user)
):
    """Get all overdue invoices"""
    return await invoice_service.get_overdue_invoices()


@router.get("/aging")
async def get_invoice_aging(
    current_user: dict = Depends(get_current_user)
):
    """Get invoice aging summary"""
    return await invoice_service.get_invoice_aging()


@router.get("/{invoice_id}")
async def get_invoice(
    invoice_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get a single invoice"""
    return await invoice_service.get_invoice(invoice_id)


@router.post("")
async def create_invoice(
    data: InvoiceCreate,
    current_user: dict = Depends(get_current_user)
):
    """Create a new invoice"""
    return await invoice_service.create_invoice(data.model_dump(), current_user['id'])


@router.put("/{invoice_id}/status")
async def update_invoice_status(
    invoice_id: str,
    status: str,
    current_user: dict = Depends(get_current_user)
):
    """Update invoice status"""
    return await invoice_service.update_invoice_status(invoice_id, status, current_user['id'])


@router.post("/{invoice_id}/payment")
async def record_payment(
    invoice_id: str,
    amount: float,
    current_user: dict = Depends(get_current_user)
):
    """Record payment against an invoice"""
    return await invoice_service.record_payment(invoice_id, amount, current_user['id'])
