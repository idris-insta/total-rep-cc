"""
Custom Field Registry - Meta-Data Driven UI
Allows dynamic field configuration for different modules
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
import uuid
import os
from core.legacy_db import db

router = APIRouter()

# Auth dependency
from server import get_current_user

# ==================== MODELS ====================
class CustomFieldCreate(BaseModel):
    module: str  # crm, inventory, production, accounts, hrms, etc.
    field_name: str
    field_label: str
    field_type: str  # text, number, date, select, multiselect, checkbox, textarea, file
    is_required: bool = False
    default_value: Optional[str] = None
    options: Optional[List[str]] = None  # For select/multiselect
    validation_rules: Optional[Dict[str, Any]] = None  # min, max, pattern, etc.
    display_order: int = 0
    section: Optional[str] = None  # Group fields into sections
    placeholder: Optional[str] = None
    help_text: Optional[str] = None
    is_searchable: bool = False
    is_filterable: bool = False
    show_in_list: bool = False

class ModuleConfigCreate(BaseModel):
    module: str
    display_name: str
    icon: Optional[str] = None
    primary_field: str  # Main identifier field
    secondary_field: Optional[str] = None
    list_columns: List[str] = []
    search_fields: List[str] = []
    default_sort: Optional[str] = None
    enable_import: bool = True
    enable_export: bool = True
    enable_bulk_actions: bool = True

# ==================== CUSTOM FIELD ENDPOINTS ====================
@router.get("/modules")
async def list_available_modules(current_user: dict = Depends(get_current_user)):
    """List all available modules for customization"""
    modules = [
        {"id": "crm_leads", "name": "CRM - Leads", "icon": "UserPlus"},
        {"id": "crm_accounts", "name": "CRM - Accounts/Customers", "icon": "Building"},
        {"id": "crm_quotations", "name": "CRM - Quotations", "icon": "FileText"},
        {"id": "inventory_items", "name": "Inventory - Items", "icon": "Package"},
        {"id": "inventory_warehouses", "name": "Inventory - Warehouses", "icon": "Warehouse"},
        {"id": "production_work_orders", "name": "Production - Work Orders", "icon": "Factory"},
        {"id": "production_machines", "name": "Production - Machines", "icon": "Cog"},
        {"id": "accounts_invoices", "name": "Accounts - Invoices", "icon": "Receipt"},
        {"id": "accounts_payments", "name": "Accounts - Payments", "icon": "CreditCard"},
        {"id": "hrms_employees", "name": "HRMS - Employees", "icon": "Users"},
        {"id": "procurement_suppliers", "name": "Procurement - Suppliers", "icon": "Truck"},
        {"id": "procurement_purchase_orders", "name": "Procurement - Purchase Orders", "icon": "ShoppingCart"},
    ]
    return modules

@router.get("/fields/{module}")
async def get_module_fields(module: str, current_user: dict = Depends(get_current_user)):
    """Get all custom fields for a module"""
    fields = await db.custom_fields.find({"module": module, "is_active": True}, {"_id": 0}).sort("display_order", 1).to_list(100)
    return fields

@router.post("/fields")
async def create_custom_field(data: CustomFieldCreate, current_user: dict = Depends(get_current_user)):
    """Create a new custom field"""
    # Check for duplicate
    existing = await db.custom_fields.find_one({
        "module": data.module,
        "field_name": data.field_name,
        "is_active": True
    })
    if existing:
        raise HTTPException(status_code=400, detail="Field with this name already exists for this module")
    
    field_doc = {
        "id": str(uuid.uuid4()),
        **data.model_dump(),
        "is_active": True,
        "created_by": current_user.get("user_id"),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    await db.custom_fields.insert_one(field_doc)
    return {k: v for k, v in field_doc.items() if k != '_id'}

@router.put("/fields/{field_id}")
async def update_custom_field(field_id: str, data: CustomFieldCreate, current_user: dict = Depends(get_current_user)):
    """Update a custom field"""
    result = await db.custom_fields.update_one(
        {"id": field_id},
        {"$set": {
            **data.model_dump(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "updated_by": current_user.get("user_id")
        }}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Field not found")
    return {"message": "Field updated successfully"}

@router.delete("/fields/{field_id}")
async def delete_custom_field(field_id: str, current_user: dict = Depends(get_current_user)):
    """Soft delete a custom field"""
    result = await db.custom_fields.update_one(
        {"id": field_id},
        {"$set": {"is_active": False, "deleted_at": datetime.now(timezone.utc).isoformat()}}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Field not found")
    return {"message": "Field deleted successfully"}

@router.post("/fields/reorder")
async def reorder_fields(module: str, field_orders: List[Dict[str, int]], current_user: dict = Depends(get_current_user)):
    """Reorder fields for a module"""
    for item in field_orders:
        await db.custom_fields.update_one(
            {"id": item["field_id"]},
            {"$set": {"display_order": item["order"]}}
        )
    return {"message": "Fields reordered successfully"}

# ==================== MODULE CONFIGURATION ====================
@router.get("/config/{module}")
async def get_module_config(module: str, current_user: dict = Depends(get_current_user)):
    """Get module configuration"""
    config = await db.module_configs.find_one({"module": module}, {"_id": 0})
    if not config:
        # Return default config
        return {
            "module": module,
            "display_name": module.replace("_", " ").title(),
            "list_columns": [],
            "search_fields": [],
            "enable_import": True,
            "enable_export": True
        }
    return config

@router.post("/config")
async def save_module_config(data: ModuleConfigCreate, current_user: dict = Depends(get_current_user)):
    """Save module configuration"""
    config_doc = {
        "id": str(uuid.uuid4()),
        **data.model_dump(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "updated_by": current_user.get("user_id")
    }
    await db.module_configs.update_one(
        {"module": data.module},
        {"$set": config_doc},
        upsert=True
    )
    return {"message": "Configuration saved successfully"}

# ==================== FORM TEMPLATES ====================
@router.get("/templates")
async def list_form_templates(current_user: dict = Depends(get_current_user)):
    """List all form templates"""
    templates = await db.form_templates.find({"is_active": True}, {"_id": 0}).to_list(100)
    return templates

@router.post("/templates")
async def create_form_template(
    name: str,
    module: str,
    template_type: str,  # create, edit, view, list
    layout: Dict[str, Any],
    current_user: dict = Depends(get_current_user)
):
    """Create a form template"""
    template_doc = {
        "id": str(uuid.uuid4()),
        "name": name,
        "module": module,
        "template_type": template_type,
        "layout": layout,
        "is_active": True,
        "created_by": current_user.get("user_id"),
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.form_templates.insert_one(template_doc)
    return {k: v for k, v in template_doc.items() if k != '_id'}

# ==================== DROPDOWN OPTIONS ====================
@router.get("/dropdown-options/{option_type}")
async def get_dropdown_options(option_type: str, current_user: dict = Depends(get_current_user)):
    """Get dropdown options for a type"""
    options = await db.dropdown_options.find({"type": option_type, "is_active": True}, {"_id": 0}).to_list(500)
    return options

@router.post("/dropdown-options")
async def add_dropdown_option(
    option_type: str,
    value: str,
    label: str,
    parent_value: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Add a dropdown option"""
    doc = {
        "id": str(uuid.uuid4()),
        "type": option_type,
        "value": value,
        "label": label,
        "parent_value": parent_value,
        "is_active": True,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.dropdown_options.insert_one(doc)
    return {k: v for k, v in doc.items() if k != '_id'}

# ==================== DEFAULT FIELD DEFINITIONS ====================
@router.post("/seed-defaults")
async def seed_default_fields(current_user: dict = Depends(get_current_user)):
    """Seed default custom fields for all modules"""
    default_fields = [
        # CRM - Leads
        {"module": "crm_leads", "field_name": "industry", "field_label": "Industry", "field_type": "select", 
         "options": ["Manufacturing", "Retail", "Wholesale", "E-commerce", "Packaging", "Automotive", "Electronics", "Other"],
         "display_order": 1, "section": "Business Info"},
        {"module": "crm_leads", "field_name": "annual_revenue", "field_label": "Annual Revenue", "field_type": "number",
         "display_order": 2, "section": "Business Info"},
        {"module": "crm_leads", "field_name": "employee_count", "field_label": "No. of Employees", "field_type": "select",
         "options": ["1-10", "11-50", "51-200", "201-500", "500+"], "display_order": 3, "section": "Business Info"},
        
        # Inventory - Items  
        {"module": "inventory_items", "field_name": "hsn_code", "field_label": "HSN Code", "field_type": "text",
         "display_order": 1, "section": "Tax & Compliance", "is_searchable": True},
        {"module": "inventory_items", "field_name": "shelf_life_days", "field_label": "Shelf Life (Days)", "field_type": "number",
         "display_order": 2, "section": "Product Info"},
        {"module": "inventory_items", "field_name": "storage_conditions", "field_label": "Storage Conditions", "field_type": "textarea",
         "display_order": 3, "section": "Product Info"},
        
        # HRMS - Employees
        {"module": "hrms_employees", "field_name": "blood_group", "field_label": "Blood Group", "field_type": "select",
         "options": ["A+", "A-", "B+", "B-", "O+", "O-", "AB+", "AB-"], "display_order": 1, "section": "Personal"},
        {"module": "hrms_employees", "field_name": "emergency_contact", "field_label": "Emergency Contact", "field_type": "text",
         "display_order": 2, "section": "Personal"},
        {"module": "hrms_employees", "field_name": "pan_number", "field_label": "PAN Number", "field_type": "text",
         "display_order": 3, "section": "Documents", "validation_rules": {"pattern": "[A-Z]{5}[0-9]{4}[A-Z]{1}"}},
        {"module": "hrms_employees", "field_name": "aadhaar_number", "field_label": "Aadhaar Number", "field_type": "text",
         "display_order": 4, "section": "Documents"},
    ]
    
    created_count = 0
    for field in default_fields:
        existing = await db.custom_fields.find_one({
            "module": field["module"],
            "field_name": field["field_name"]
        })
        if not existing:
            field["id"] = str(uuid.uuid4())
            field["is_active"] = True
            field["created_at"] = datetime.now(timezone.utc).isoformat()
            await db.custom_fields.insert_one(field)
            created_count += 1
    
    return {"message": f"Seeded {created_count} default fields"}
