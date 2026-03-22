from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
import uuid
from server import db, get_current_user

router = APIRouter()

class CustomField(BaseModel):
    field_name: str
    field_label: str
    field_type: str  # text, number, date, select, checkbox
    module: str  # crm, inventory, production, etc.
    entity: str  # leads, items, work_orders, etc.
    options: Optional[List[str]] = None  # for select fields
    required: bool = False
    default_value: Optional[Any] = None

class CustomFieldResponse(BaseModel):
    id: str
    field_name: str
    field_label: str
    field_type: str
    module: str
    entity: Optional[str] = None
    options: Optional[List[str]] = None
    required: Optional[bool] = False
    default_value: Optional[Any] = None
    created_at: Optional[str] = None
    created_by: Optional[str] = None
    # Additional fields from Power Settings
    section: Optional[str] = None
    placeholder: Optional[str] = None
    help_text: Optional[str] = None
    is_searchable: Optional[bool] = False
    is_filterable: Optional[bool] = False
    show_in_list: Optional[bool] = False
    display_order: Optional[int] = 0
    is_active: Optional[bool] = True

class ReportTemplate(BaseModel):
    name: str
    description: Optional[str] = None
    module: str
    query_filters: Dict[str, Any]
    columns: List[Dict[str, str]]
    group_by: Optional[List[str]] = None
    sort_by: Optional[Dict[str, str]] = None
    chart_type: Optional[str] = None

class ReportTemplateResponse(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    module: str
    query_filters: Dict[str, Any]
    columns: List[Dict[str, str]]
    group_by: Optional[List[str]] = None
    sort_by: Optional[Dict[str, str]] = None
    chart_type: Optional[str] = None
    created_at: str
    created_by: str


@router.post("/custom-fields", response_model=CustomFieldResponse)
async def create_custom_field(field_data: CustomField, current_user: dict = Depends(get_current_user)):
    """
    Add custom fields to any module dynamically
    """
    if current_user['role'] not in ['admin']:
        raise HTTPException(status_code=403, detail="Only admins can create custom fields")
    
    existing = await db.custom_fields.find_one({
        'module': field_data.module,
        'entity': field_data.entity,
        'field_name': field_data.field_name
    }, {'_id': 0})
    
    if existing:
        raise HTTPException(status_code=400, detail="Custom field already exists")
    
    field_id = str(uuid.uuid4())
    field_doc = {
        'id': field_id,
        **field_data.model_dump(),
        'created_at': datetime.now(timezone.utc).isoformat(),
        'created_by': current_user['id']
    }
    
    await db.custom_fields.insert_one(field_doc)
    return CustomFieldResponse(**{k: v for k, v in field_doc.items() if k != '_id'})

@router.get("/custom-fields", response_model=List[CustomFieldResponse])
async def get_custom_fields(module: Optional[str] = None, entity: Optional[str] = None, current_user: dict = Depends(get_current_user)):
    """
    Get all custom fields for a module/entity
    """
    query = {}
    if module:
        query['module'] = module
    if entity:
        query['entity'] = entity
    
    fields = await db.custom_fields.find(query, {'_id': 0}).to_list(1000)
    return [CustomFieldResponse(**field) for field in fields]

@router.delete("/custom-fields/{field_id}")
async def delete_custom_field(field_id: str, current_user: dict = Depends(get_current_user)):
    """
    Delete a custom field
    """
    if current_user['role'] not in ['admin']:
        raise HTTPException(status_code=403, detail="Only admins can delete custom fields")
    
    result = await db.custom_fields.delete_one({'id': field_id})
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Custom field not found")
    
    return {'message': 'Custom field deleted successfully'}


@router.post("/report-templates", response_model=ReportTemplateResponse)
async def create_report_template(report_data: ReportTemplate, current_user: dict = Depends(get_current_user)):
    """
    Create custom report templates
    """
    report_id = str(uuid.uuid4())
    report_doc = {
        'id': report_id,
        **report_data.model_dump(),
        'created_at': datetime.now(timezone.utc).isoformat(),
        'created_by': current_user['id']
    }
    
    await db.report_templates.insert_one(report_doc)
    return ReportTemplateResponse(**{k: v for k, v in report_doc.items() if k != '_id'})

@router.get("/report-templates", response_model=List[ReportTemplateResponse])
async def get_report_templates(module: Optional[str] = None, current_user: dict = Depends(get_current_user)):
    """
    Get all report templates
    """
    query = {}
    if module:
        query['module'] = module
    
    templates = await db.report_templates.find(query, {'_id': 0}).to_list(1000)
    return [ReportTemplateResponse(**template) for template in templates]

@router.post("/report-templates/{template_id}/execute")
async def execute_report(template_id: str, current_user: dict = Depends(get_current_user)):
    """
    Execute a saved report template
    """
    template = await db.report_templates.find_one({'id': template_id}, {'_id': 0})
    if not template:
        raise HTTPException(status_code=404, detail="Report template not found")
    
    collection_map = {
        'crm': 'leads',
        'inventory': 'stock',
        'production': 'work_orders',
        'accounts': 'invoices',
        'hrms': 'employees',
        'quality': 'qc_inspections'
    }
    
    collection_name = collection_map.get(template['module'])
    if not collection_name:
        raise HTTPException(status_code=400, detail="Invalid module")
    
    collection = db[collection_name]
    
    query_filters = template.get('query_filters', {})
    data = await collection.find(query_filters, {'_id': 0}).to_list(10000)
    
    return {
        'template': template,
        'data': data,
        'count': len(data),
        'executed_at': datetime.now(timezone.utc).isoformat()
    }


@router.get("/audit-trail")
async def get_audit_trail(
    module: Optional[str] = None,
    entity_id: Optional[str] = None,
    user_id: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """
    Get audit trail / change history
    """
    query = {}
    if module:
        query['module'] = module
    if entity_id:
        query['entity_id'] = entity_id
    if user_id:
        query['user_id'] = user_id
    if start_date:
        query['timestamp'] = {'$gte': start_date}
    if end_date:
        if 'timestamp' not in query:
            query['timestamp'] = {}
        query['timestamp']['$lte'] = end_date
    
    audit_logs = await db.audit_trail.find(query, {'_id': 0}).sort('timestamp', -1).to_list(1000)
    
    return {
        'logs': audit_logs,
        'count': len(audit_logs)
    }


async def log_audit_trail(module: str, entity: str, entity_id: str, action: str, user_id: str, old_value: Any = None, new_value: Any = None):
    """
    Helper function to log changes to audit trail
    """
    audit_doc = {
        'id': str(uuid.uuid4()),
        'module': module,
        'entity': entity,
        'entity_id': entity_id,
        'action': action,
        'user_id': user_id,
        'old_value': old_value,
        'new_value': new_value,
        'timestamp': datetime.now(timezone.utc).isoformat()
    }
    
    await db.audit_trail.insert_one(audit_doc)