"""
CRM API Routes - Quotations
API endpoints for Quotation management
"""
from fastapi import APIRouter, Depends, Query
from typing import Optional

from core.security import get_current_user
from services.crm.service import quotation_service
from models.schemas.crm import QuotationCreate, QuotationUpdate

router = APIRouter(prefix="/quotations", tags=["CRM - Quotations"])


@router.get("")
async def get_quotations(
    status: Optional[str] = None,
    account_id: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Get all quotations with optional filters"""
    filters = {}
    if status:
        filters['status'] = status
    if account_id:
        filters['account_id'] = account_id
    return await quotation_service.get_all_quotations(filters)


@router.get("/{quote_id}")
async def get_quotation(
    quote_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get a single quotation"""
    return await quotation_service.get_quotation(quote_id)


@router.post("")
async def create_quotation(
    data: QuotationCreate,
    current_user: dict = Depends(get_current_user)
):
    """Create a new quotation"""
    return await quotation_service.create_quotation(data.model_dump(), current_user['id'])


@router.put("/{quote_id}")
async def update_quotation(
    quote_id: str,
    data: QuotationUpdate,
    current_user: dict = Depends(get_current_user)
):
    """Update an existing quotation"""
    update_data = {k: v for k, v in data.model_dump().items() if v is not None}
    return await quotation_service.update_quotation(quote_id, update_data, current_user['id'])


@router.delete("/{quote_id}")
async def delete_quotation(
    quote_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Delete a quotation"""
    await quotation_service.delete_quotation(quote_id)
    return {"message": "Quotation deleted successfully"}


@router.post("/{quote_id}/convert-to-so")
async def convert_to_sales_order(
    quote_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Convert quotation to sales order"""
    return await quotation_service.convert_to_sales_order(quote_id, current_user['id'])
