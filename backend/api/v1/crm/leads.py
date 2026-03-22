"""
CRM API Routes - Leads
API endpoints for Lead management
"""
from fastapi import APIRouter, Depends, Query
from typing import Optional, List

from core.security import get_current_user
from services.crm.service import lead_service
from models.schemas.crm import LeadCreate, LeadUpdate, LeadResponse

router = APIRouter(prefix="/leads", tags=["CRM - Leads"])


@router.get("")
async def get_leads(
    status: Optional[str] = None,
    assigned_to: Optional[str] = None,
    source: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Get all leads with optional filters"""
    filters = {}
    if status:
        filters['status'] = status
    if assigned_to:
        filters['assigned_to'] = assigned_to
    if source:
        filters['source'] = source
    
    return await lead_service.get_all_leads(filters)


@router.get("/kanban/view")
async def get_kanban_view(
    current_user: dict = Depends(get_current_user)
):
    """Get leads organized for Kanban view"""
    # Get stages from field registry or use defaults
    from core.legacy_db import db
    config = await db.field_configurations.find_one(
        {'module': 'crm', 'entity': 'leads'},
        {'_id': 0, 'kanban_stages': 1}
    )
    
    stages = []
    if config and config.get('kanban_stages'):
        stages = [s['value'] for s in config['kanban_stages'] if s.get('is_active', True)]
    
    if not stages:
        stages = ['new', 'hot_leads', 'cold_leads', 'contacted', 'qualified', 
                  'proposal', 'negotiation', 'converted', 'customer', 'lost']
    
    kanban_data = await lead_service.get_kanban_view(stages)
    return {"stages": stages, "leads": kanban_data}


@router.get("/{lead_id}")
async def get_lead(
    lead_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get a single lead by ID"""
    return await lead_service.get_lead(lead_id)


@router.post("")
async def create_lead(
    data: LeadCreate,
    current_user: dict = Depends(get_current_user)
):
    """Create a new lead"""
    return await lead_service.create_lead(data.model_dump(), current_user['id'])


@router.put("/{lead_id}")
async def update_lead(
    lead_id: str,
    data: LeadUpdate,
    current_user: dict = Depends(get_current_user)
):
    """Update an existing lead"""
    update_data = {k: v for k, v in data.model_dump().items() if v is not None}
    return await lead_service.update_lead(lead_id, update_data, current_user['id'])


@router.delete("/{lead_id}")
async def delete_lead(
    lead_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Delete a lead"""
    await lead_service.delete_lead(lead_id)
    return {"message": "Lead deleted successfully"}


@router.put("/{lead_id}/stage")
async def update_lead_stage(
    lead_id: str,
    stage: str,
    current_user: dict = Depends(get_current_user)
):
    """Move lead to a new stage"""
    return await lead_service.move_to_stage(lead_id, stage, current_user['id'])


@router.post("/{lead_id}/convert")
async def convert_lead_to_account(
    lead_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Convert a qualified lead to a customer account"""
    return await lead_service.convert_to_account(lead_id, current_user['id'])
