"""
Field Registry - The Command Registry Engine
Metadata-Driven Field Configuration System for all modules
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
import uuid
from server import db, get_current_user

router = APIRouter()

# ==================== PYDANTIC MODELS ====================

class FieldOption(BaseModel):
    """Single dropdown option"""
    value: str
    label: str
    color: Optional[str] = None  # For stage badges, status colors
    is_default: Optional[bool] = False
    is_active: Optional[bool] = True
    order: Optional[int] = 0


class FieldConfig(BaseModel):
    """Field configuration for a module entity"""
    field_name: str  # Internal name (snake_case)
    field_label: str  # Display label
    field_type: str  # text, number, date, select, multiselect, checkbox, textarea, phone, email, currency, auto
    section: Optional[str] = "default"  # Group fields by section
    placeholder: Optional[str] = None
    help_text: Optional[str] = None
    is_required: Optional[bool] = False
    is_readonly: Optional[bool] = False
    is_searchable: Optional[bool] = False
    is_filterable: Optional[bool] = False
    show_in_list: Optional[bool] = True
    show_in_form: Optional[bool] = True
    order: Optional[int] = 0
    options: Optional[List[FieldOption]] = None  # For select/multiselect
    default_value: Optional[Any] = None
    validation: Optional[Dict[str, Any]] = None  # min, max, pattern, etc.
    auto_fill_source: Optional[str] = None  # e.g., "pincode" for auto-filling state/city
    depends_on: Optional[str] = None  # Field dependency
    width: Optional[str] = "full"  # full, half, third


class ModuleEntityConfig(BaseModel):
    """Configuration for a module entity (e.g., CRM > Leads)"""
    module: str  # crm, inventory, accounts, etc.
    entity: str  # leads, accounts, quotations, items, etc.
    entity_label: str
    fields: List[FieldConfig]
    kanban_stages: Optional[List[FieldOption]] = None  # For entities with Kanban view
    list_display_fields: Optional[List[str]] = None  # Fields to show in list view
    created_by: Optional[str] = None


class MasterListConfig(BaseModel):
    """Master list configuration"""
    master_type: str  # customer, supplier, item, item_code, price, machine, employee, expense, report_type
    master_label: str
    description: Optional[str] = None
    fields: List[FieldConfig]


# ==================== API ENDPOINTS ====================

@router.get("/modules")
async def get_available_modules(current_user: dict = Depends(get_current_user)):
    """Get list of available modules and entities"""
    modules = {
        "crm": {
            "label": "CRM",
            "icon": "users",
            "entities": {
                "leads": "Leads",
                "customer_accounts": "Customer Accounts",
                "quotations": "Quotations",
                "samples": "Samples"
            }
        },
        "inventory": {
            "label": "Inventory",
            "icon": "package",
            "entities": {
                "stock_items": "Items / Products",
                "warehouses": "Warehouses",
                "stock_transfers": "Stock Transfers",
                "stock_adjustments": "Stock Adjustments",
                "serial_numbers": "Serial No Master",
                "batches": "Batches"
            }
        },
        "production": {
            "label": "Production",
            "icon": "settings",
            "entities": {
                "machines": "Machines",
                "order_sheets": "Order Sheets",
                "work_orders": "Work Orders"
            }
        },
        "accounts": {
            "label": "Finance",
            "icon": "wallet",
            "entities": {
                "invoices": "Sales Invoices",
                "purchase_invoices": "Purchase Invoices",
                "payments": "Payments / Receipts",
                "ledger": "Ledger"
            }
        },
        "procurement": {
            "label": "Procurement",
            "icon": "truck",
            "entities": {
                "purchase_orders": "Purchase Orders",
                "grn": "Goods Receipt (GRN)"
            }
        },
        "quality": {
            "label": "Quality",
            "icon": "clipboard",
            "entities": {
                "inspections": "Quality Inspections",
                "parameters": "QC Parameters"
            }
        },
        "hrms": {
            "label": "HRMS",
            "icon": "users",
            "entities": {
                "employees": "Employees",
                "attendance": "Attendance",
                "leaves": "Leave Applications",
                "payroll": "Payroll"
            }
        },
        "settings": {
            "label": "Settings",
            "icon": "settings",
            "entities": {
                "users": "Users",
                "company": "Company Settings"
            }
        }
    }
    return modules


@router.get("/masters")
async def get_master_types(current_user: dict = Depends(get_current_user)):
    """Get list of master types"""
    masters = [
        {"type": "customer", "label": "Customer Master", "description": "The Revenue Base - GSTIN, Branch, Buying DNA, Credit Limit"},
        {"type": "supplier", "label": "Supplier Master", "description": "The Sourcing Base - Material Category, Lead Time, Reliability"},
        {"type": "item", "label": "Item Master", "description": "The Physics Base - Base Category, UOM, Technical Specs"},
        {"type": "item_code", "label": "Item Code Master", "description": "The Inventory Logic - Internal SKU, Barcode, Warehouse Location"},
        {"type": "price", "label": "Price Master", "description": "The Margin Protector - Customer Pricing, Volume Discounts, MSP"},
        {"type": "machine", "label": "Machine Master", "description": "The Plant Heart - Machine Name, Design Capacity, Maintenance Cycle"},
        {"type": "employee", "label": "Employee Master", "description": "The Accountability Base - Role, Biometric ID, Department, KPIs"},
        {"type": "expense", "label": "Expense Master", "description": "The Leakage Tracker - Category, Budget Cap, Branch Allocation"},
        {"type": "report_type", "label": "Report Type List", "description": "The Executive View - Frequency, Recipients, KPI Focus"}
    ]
    return masters


# ==================== FIELD CONFIGURATION CRUD ====================

@router.post("/config")
async def save_field_config(config: ModuleEntityConfig, current_user: dict = Depends(get_current_user)):
    """Save field configuration for a module entity (Admin only)"""
    import logging
    logger = logging.getLogger(__name__)
    
    if current_user.get('role') not in ['admin', 'director']:
        raise HTTPException(status_code=403, detail="Only admin or director can configure fields")
    
    # Convert to dict and add metadata
    config_dict = config.model_dump()
    now = datetime.now(timezone.utc)
    config_dict['updated_at'] = now
    config_dict['updated_by'] = current_user['id']
    
    logger.info(f"Saving field config for {config.module}/{config.entity} with {len(config.fields)} fields")
    
    # Check if config already exists
    existing = await db.field_configurations.find_one({
        'module': config.module,
        'entity': config.entity
    })
    
    logger.info(f"Existing config found: {existing is not None}")
    
    if existing:
        # Update existing - preserve created_at as datetime or convert from string
        existing_created_at = existing.get('created_at')
        if isinstance(existing_created_at, str):
            try:
                existing_created_at = datetime.fromisoformat(existing_created_at.replace('Z', '+00:00'))
            except (ValueError, TypeError):
                existing_created_at = now
        config_dict['created_at'] = existing_created_at or now
        config_dict['created_by'] = existing.get('created_by', current_user['id'])
        result = await db.field_configurations.update_one(
            {'module': config.module, 'entity': config.entity},
            {'$set': config_dict}
        )
        logger.info(f"Update result: matched={result.matched_count}, modified={result.modified_count}")
    else:
        # Create new
        config_dict['id'] = str(uuid.uuid4())
        config_dict['created_at'] = now
        config_dict['created_by'] = current_user['id']
        result = await db.field_configurations.insert_one(config_dict)
        logger.info(f"Insert result: inserted_id={result.inserted_id}")
    
    # Verify it was saved
    verification = await db.field_configurations.find_one({'module': config.module, 'entity': config.entity})
    logger.info(f"Verification - config exists: {verification is not None}")
    
    return {"message": "Configuration saved successfully", "module": config.module, "entity": config.entity}


@router.get("/config/{module}/{entity}")
async def get_field_config(module: str, entity: str, current_user: dict = Depends(get_current_user)):
    """Get field configuration for a module entity"""
    config = await db.field_configurations.find_one(
        {'module': module, 'entity': entity},
        {'_id': 0}
    )
    
    if not config:
        # Return default config
        default = await get_default_config(module, entity)
        return default
    
    return config


@router.get("/config/{module}")
async def get_module_configs(module: str, current_user: dict = Depends(get_current_user)):
    """Get all field configurations for a module"""
    configs = await db.field_configurations.find(
        {'module': module},
        {'_id': 0}
    ).to_list(100)
    
    return configs


@router.delete("/config/{module}/{entity}")
async def reset_field_config(module: str, entity: str, current_user: dict = Depends(get_current_user)):
    """Reset field configuration to default (Admin only)"""
    if current_user.get('role') not in ['admin', 'director']:
        raise HTTPException(status_code=403, detail="Only admin or director can reset configurations")
    
    await db.field_configurations.delete_one({'module': module, 'entity': entity})
    return {"message": "Configuration reset to default", "module": module, "entity": entity}


# ==================== DROPDOWN OPTIONS MANAGEMENT ====================

@router.post("/options/{module}/{entity}/{field_name}")
async def save_field_options(
    module: str, 
    entity: str, 
    field_name: str, 
    options: List[FieldOption],
    current_user: dict = Depends(get_current_user)
):
    """Save dropdown options for a specific field"""
    if current_user.get('role') not in ['admin', 'director']:
        raise HTTPException(status_code=403, detail="Only admin or director can configure options")
    
    # Get existing config
    config = await db.field_configurations.find_one(
        {'module': module, 'entity': entity}
    )
    
    if not config:
        raise HTTPException(status_code=404, detail="Field configuration not found. Please save the entity config first.")
    
    # Update the specific field's options
    fields = config.get('fields', [])
    updated = False
    for field in fields:
        if field.get('field_name') == field_name:
            field['options'] = [opt.model_dump() for opt in options]
            updated = True
            break
    
    if not updated:
        raise HTTPException(status_code=404, detail=f"Field '{field_name}' not found in configuration")
    
    await db.field_configurations.update_one(
        {'module': module, 'entity': entity},
        {'$set': {'fields': fields, 'updated_at': datetime.now(timezone.utc).isoformat()}}
    )
    
    return {"message": "Options saved successfully", "field": field_name, "options_count": len(options)}


@router.get("/options/{module}/{entity}/{field_name}")
async def get_field_options(module: str, entity: str, field_name: str, current_user: dict = Depends(get_current_user)):
    """Get dropdown options for a specific field"""
    config = await db.field_configurations.find_one(
        {'module': module, 'entity': entity},
        {'_id': 0}
    )
    
    if not config:
        # Return default options
        default_config = await get_default_config(module, entity)
        config = default_config
    
    for field in config.get('fields', []):
        if field.get('field_name') == field_name:
            return field.get('options', [])
    
    return []


# ==================== KANBAN STAGES MANAGEMENT ====================

@router.post("/stages/{module}/{entity}")
async def save_kanban_stages(
    module: str,
    entity: str,
    stages: List[FieldOption],
    current_user: dict = Depends(get_current_user)
):
    """Save Kanban stages for an entity"""
    if current_user.get('role') not in ['admin', 'director']:
        raise HTTPException(status_code=403, detail="Only admin or director can configure stages")
    
    stages_data = [stage.model_dump() for stage in stages]
    
    await db.field_configurations.update_one(
        {'module': module, 'entity': entity},
        {
            '$set': {
                'kanban_stages': stages_data,
                'updated_at': datetime.now(timezone.utc).isoformat()
            }
        },
        upsert=True
    )
    
    return {"message": "Stages saved successfully", "stages_count": len(stages)}


@router.get("/stages/{module}/{entity}")
async def get_kanban_stages(module: str, entity: str, current_user: dict = Depends(get_current_user)):
    """Get Kanban stages for an entity"""
    config = await db.field_configurations.find_one(
        {'module': module, 'entity': entity},
        {'_id': 0, 'kanban_stages': 1}
    )
    
    if config and config.get('kanban_stages'):
        return config['kanban_stages']
    
    # Return default stages for leads
    if module == 'crm' and entity == 'leads':
        return get_default_lead_stages()
    
    return []


# ==================== DEFAULT CONFIGURATIONS ====================

def get_default_lead_stages():
    """Default Kanban stages for Leads"""
    return [
        {"value": "new", "label": "New", "color": "slate", "order": 0, "is_active": True},
        {"value": "hot_leads", "label": "Hot Leads", "color": "red", "order": 1, "is_active": True},
        {"value": "cold_leads", "label": "Cold Leads", "color": "blue", "order": 2, "is_active": True},
        {"value": "contacted", "label": "Contacted", "color": "yellow", "order": 3, "is_active": True},
        {"value": "qualified", "label": "Qualified", "color": "green", "order": 4, "is_active": True},
        {"value": "proposal", "label": "Proposal", "color": "purple", "order": 5, "is_active": True},
        {"value": "negotiation", "label": "Negotiation", "color": "orange", "order": 6, "is_active": True},
        {"value": "converted", "label": "Converted", "color": "emerald", "order": 7, "is_active": True},
        {"value": "customer", "label": "Customer", "color": "teal", "order": 8, "is_active": True},
        {"value": "lost", "label": "Lost", "color": "slate", "order": 9, "is_active": True}
    ]


async def get_default_config(module: str, entity: str):
    """Get default field configuration for a module entity"""
    
    if module == 'crm' and entity == 'leads':
        return {
            "module": "crm",
            "entity": "leads",
            "entity_label": "Leads",
            "kanban_stages": get_default_lead_stages(),
            "fields": [
                # Basic Info
                {"field_name": "company_name", "field_label": "Company Name", "field_type": "text", "section": "basic", "is_required": True, "show_in_list": True, "order": 1},
                {"field_name": "contact_person", "field_label": "Contact Person", "field_type": "text", "section": "basic", "is_required": True, "show_in_list": True, "order": 2},
                {"field_name": "email", "field_label": "Email", "field_type": "email", "section": "basic", "is_required": False, "show_in_list": False, "order": 3},
                {"field_name": "phone", "field_label": "Phone", "field_type": "phone", "section": "basic", "is_required": False, "show_in_list": False, "order": 4},
                {"field_name": "source", "field_label": "Source", "field_type": "select", "section": "basic", "is_required": False, "show_in_list": True, "order": 5,
                    "options": [
                        {"value": "indiamart", "label": "IndiaMart", "order": 0},
                        {"value": "tradeindia", "label": "TradeIndia", "order": 1},
                        {"value": "alibaba", "label": "Alibaba", "order": 2},
                        {"value": "google", "label": "Google", "order": 3},
                        {"value": "exhibition", "label": "Exhibition", "order": 4},
                        {"value": "cold_call", "label": "Cold Call", "order": 5},
                        {"value": "referral", "label": "Referral", "order": 6},
                        {"value": "website", "label": "Website", "order": 7},
                        {"value": "linkedin", "label": "LinkedIn", "order": 8},
                        {"value": "other", "label": "Other", "order": 9}
                    ]
                },
                # Address
                {"field_name": "address", "field_label": "Address", "field_type": "textarea", "section": "address", "is_required": False, "show_in_list": False, "order": 6},
                {"field_name": "country", "field_label": "Country", "field_type": "text", "section": "address", "default_value": "India", "is_required": False, "order": 7},
                {"field_name": "pincode", "field_label": "Pincode", "field_type": "text", "section": "address", "is_required": False, "auto_fill_source": "pincode", "order": 8},
                {"field_name": "state", "field_label": "State", "field_type": "text", "section": "address", "is_required": False, "order": 9},
                {"field_name": "district", "field_label": "District", "field_type": "text", "section": "address", "is_required": False, "order": 10},
                {"field_name": "city", "field_label": "City", "field_type": "text", "section": "address", "is_required": False, "show_in_list": True, "order": 11},
                # Classification
                {"field_name": "customer_type", "field_label": "Customer Type", "field_type": "select", "section": "classification", "is_required": False, "order": 12,
                    "options": [
                        {"value": "manufacturer", "label": "Manufacturer", "order": 0},
                        {"value": "trader", "label": "Trader", "order": 1},
                        {"value": "distributor", "label": "Distributor", "order": 2},
                        {"value": "retailer", "label": "Retailer", "order": 3},
                        {"value": "end_user", "label": "End User", "order": 4}
                    ]
                },
                {"field_name": "assigned_to", "field_label": "Assigned To", "field_type": "select", "section": "classification", "is_required": False, "order": 13,
                    "options": []  # Will be populated from users
                },
                {"field_name": "stage", "field_label": "Stage", "field_type": "select", "section": "classification", "is_required": False, "show_in_list": True, "order": 14,
                    "options": get_default_lead_stages()
                },
                {"field_name": "industry", "field_label": "Industry", "field_type": "select", "section": "classification", "is_required": False, "order": 15,
                    "options": [
                        {"value": "manufacturing", "label": "Manufacturing", "order": 0},
                        {"value": "packaging", "label": "Packaging", "order": 1},
                        {"value": "construction", "label": "Construction", "order": 2},
                        {"value": "automotive", "label": "Automotive", "order": 3},
                        {"value": "electronics", "label": "Electronics", "order": 4},
                        {"value": "fmcg", "label": "FMCG", "order": 5},
                        {"value": "pharmaceutical", "label": "Pharmaceutical", "order": 6},
                        {"value": "textile", "label": "Textile", "order": 7},
                        {"value": "other", "label": "Other", "order": 8}
                    ]
                },
                {"field_name": "products_of_interest", "field_label": "Products of Interest", "field_type": "multiselect", "section": "classification", "is_required": False, "order": 16,
                    "options": [
                        {"value": "bopp_tape", "label": "BOPP Tape", "order": 0},
                        {"value": "masking_tape", "label": "Masking Tape", "order": 1},
                        {"value": "double_sided", "label": "Double Sided Tape", "order": 2},
                        {"value": "cloth_tape", "label": "Cloth Tape", "order": 3},
                        {"value": "pvc_tape", "label": "PVC Tape", "order": 4},
                        {"value": "foam_tape", "label": "Foam Tape", "order": 5},
                        {"value": "custom", "label": "Custom/Special", "order": 6}
                    ]
                },
                # Follow-up
                {"field_name": "estimated_value", "field_label": "Estimated Value", "field_type": "select", "section": "followup", "is_required": False, "order": 17,
                    "options": [
                        {"value": "below_50k", "label": "Below ₹50K", "order": 0},
                        {"value": "50k_1l", "label": "₹50K - ₹1L", "order": 1},
                        {"value": "1l_5l", "label": "₹1L - ₹5L", "order": 2},
                        {"value": "5l_10l", "label": "₹5L - ₹10L", "order": 3},
                        {"value": "above_10l", "label": "Above ₹10L", "order": 4}
                    ]
                },
                {"field_name": "next_followup_date", "field_label": "Next Follow-up Date", "field_type": "date", "section": "followup", "is_required": False, "order": 18},
                {"field_name": "followup_activity", "field_label": "Follow-up Activity", "field_type": "select", "section": "followup", "is_required": False, "order": 19,
                    "options": [
                        {"value": "call", "label": "Call", "order": 0},
                        {"value": "email", "label": "Email", "order": 1},
                        {"value": "meeting", "label": "Meeting", "order": 2},
                        {"value": "visit", "label": "Site Visit", "order": 3},
                        {"value": "sample", "label": "Send Sample", "order": 4},
                        {"value": "quote", "label": "Send Quote", "order": 5}
                    ]
                },
                {"field_name": "notes", "field_label": "Notes", "field_type": "textarea", "section": "followup", "is_required": False, "order": 20}
            ],
            "list_display_fields": ["company_name", "contact_person", "city", "source", "stage", "estimated_value"]
        }
    
    elif module == 'crm' and entity in ['accounts', 'customer_accounts']:
        return {
            "module": "crm",
            "entity": entity,
            "entity_label": "Customer Accounts",
            "fields": [
                # Basic Info Tab
                {"field_name": "customer_name", "field_label": "Customer Name", "field_type": "text", "section": "basic", "is_required": True, "show_in_list": True, "order": 1},
                {"field_name": "account_type", "field_label": "Account Type", "field_type": "select", "section": "basic", "order": 2,
                    "options": [
                        {"value": "customer", "label": "Customer"},
                        {"value": "supplier", "label": "Supplier"},
                        {"value": "both", "label": "Both (Customer & Supplier)"}
                    ]
                },
                {"field_name": "industry", "field_label": "Industry", "field_type": "select", "section": "basic", "order": 3,
                    "options": [
                        {"value": "Manufacturing", "label": "Manufacturing"},
                        {"value": "Packaging", "label": "Packaging"},
                        {"value": "Construction", "label": "Construction"},
                        {"value": "Automotive", "label": "Automotive"},
                        {"value": "Electronics", "label": "Electronics"},
                        {"value": "FMCG", "label": "FMCG"},
                        {"value": "Pharmaceutical", "label": "Pharmaceutical"},
                        {"value": "Textile", "label": "Textile"},
                        {"value": "Other", "label": "Other"}
                    ]
                },
                {"field_name": "gstin", "field_label": "GSTIN", "field_type": "text", "section": "basic", "is_required": True, "placeholder": "27XXXXX0000X1ZX", "order": 4},
                {"field_name": "pan", "field_label": "PAN", "field_type": "text", "section": "basic", "placeholder": "AAAAA0000A", "order": 5},
                {"field_name": "website", "field_label": "Website", "field_type": "text", "section": "basic", "placeholder": "https://example.com", "order": 6},
                {"field_name": "aadhar_no", "field_label": "Aadhar No", "field_type": "text", "section": "basic", "placeholder": "0000 0000 0000", "order": 7},
                {"field_name": "opening_balance", "field_label": "Opening Balance (₹)", "field_type": "currency", "section": "basic", "order": 8, "help_text": "Enter opening receivable balance"},
                {"field_name": "bank_details", "field_label": "Bank Details", "field_type": "textarea", "section": "basic", "order": 9, "placeholder": "Bank Name, A/C No, IFSC Code"},
                {"field_name": "notes", "field_label": "Notes", "field_type": "textarea", "section": "basic", "order": 10},
                
                # Billing Address Tab
                {"field_name": "billing_address", "field_label": "Billing Address", "field_type": "textarea", "section": "billing_address", "is_required": True, "order": 11},
                {"field_name": "billing_country", "field_label": "Country", "field_type": "text", "section": "billing_address", "default_value": "India", "order": 12},
                {"field_name": "billing_pincode", "field_label": "Pincode", "field_type": "text", "section": "billing_address", "auto_fill_source": "pincode", "order": 13},
                {"field_name": "billing_state", "field_label": "State", "field_type": "text", "section": "billing_address", "order": 14},
                {"field_name": "billing_district", "field_label": "District", "field_type": "text", "section": "billing_address", "order": 15},
                {"field_name": "billing_city", "field_label": "City", "field_type": "text", "section": "billing_address", "show_in_list": True, "order": 16},
                
                # Credit & Terms Tab
                {"field_name": "credit_limit", "field_label": "Credit Limit (₹)", "field_type": "currency", "section": "credit_terms", "default_value": 0, "order": 17},
                {"field_name": "credit_days", "field_label": "Credit Days", "field_type": "number", "section": "credit_terms", "default_value": 30, "order": 18},
                {"field_name": "credit_control", "field_label": "Credit Control", "field_type": "select", "section": "credit_terms", "order": 19,
                    "options": [
                        {"value": "strict", "label": "Strict - Block orders when limit exceeded"},
                        {"value": "warning", "label": "Warning - Allow with alert"},
                        {"value": "none", "label": "No Control"}
                    ]
                },
                {"field_name": "payment_terms", "field_label": "Default Payment Terms", "field_type": "select", "section": "credit_terms", "order": 20,
                    "options": [
                        {"value": "advance", "label": "100% Advance"},
                        {"value": "50_advance", "label": "50% Advance"},
                        {"value": "cod", "label": "Cash on Delivery"},
                        {"value": "7_days", "label": "7 Days Credit"},
                        {"value": "15_days", "label": "15 Days Credit"},
                        {"value": "30_days", "label": "30 Days Credit"},
                        {"value": "45_days", "label": "45 Days Credit"},
                        {"value": "60_days", "label": "60 Days Credit"}
                    ]
                },
                {"field_name": "location", "field_label": "Service Location", "field_type": "text", "section": "credit_terms", "placeholder": "Mumbai, Delhi...", "order": 21}
            ],
            "list_display_fields": ["customer_name", "billing_city", "gstin", "receivable_amount", "credit_limit", "payment_terms"]
        }
    
    elif module == 'crm' and entity == 'quotations':
        return {
            "module": "crm",
            "entity": "quotations",
            "entity_label": "Quotations",
            "fields": [
                # Core Fields - These appear at the top of the quotation form
                {"field_name": "account_id", "field_label": "Customer", "field_type": "select", "section": "core", "is_required": True, "auto_suggest": "accounts", "order": 1},
                {"field_name": "contact_person", "field_label": "Contact Person", "field_type": "text", "section": "core", "order": 2},
                {"field_name": "reference", "field_label": "Reference", "field_type": "text", "section": "core", "placeholder": "Enquiry ref, PO ref...", "order": 3},
                {"field_name": "valid_until", "field_label": "Valid Until", "field_type": "date", "section": "core", "is_required": True, "order": 4},
                
                # Header Fields - These appear below core fields in the quotation form
                {"field_name": "transport", "field_label": "Transport", "field_type": "text", "section": "header", "placeholder": "Transporter name or mode", "order": 5},
                {"field_name": "delivery_terms", "field_label": "Delivery Terms", "field_type": "select", "section": "header", "order": 6,
                    "options": [
                        {"value": "ex_works", "label": "Ex-Works (Factory)"},
                        {"value": "for", "label": "FOR Destination"},
                        {"value": "fob", "label": "FOB"},
                        {"value": "cif", "label": "CIF"}
                    ]
                },
                {"field_name": "payment_terms", "field_label": "Payment Terms", "field_type": "select", "section": "header", "order": 7,
                    "options": [
                        {"value": "advance", "label": "100% Advance"},
                        {"value": "50_advance", "label": "50% Advance"},
                        {"value": "cod", "label": "Cash on Delivery"},
                        {"value": "7_days", "label": "7 Days Credit"},
                        {"value": "15_days", "label": "15 Days Credit"},
                        {"value": "30_days", "label": "30 Days Credit"},
                        {"value": "45_days", "label": "45 Days Credit"},
                        {"value": "60_days", "label": "60 Days Credit"}
                    ]
                },
                {"field_name": "validity_days", "field_label": "Validity (Days)", "field_type": "number", "section": "header", "default_value": 30, "order": 8},
                {"field_name": "header_discount_percent", "field_label": "Overall Discount %", "field_type": "number", "section": "header", "default_value": 0, "order": 9},
                {"field_name": "notes", "field_label": "Internal Notes", "field_type": "textarea", "section": "header", "order": 10, "help_text": "Internal notes (not shown to customer)"},
                {"field_name": "terms_conditions", "field_label": "Terms & Conditions", "field_type": "textarea", "section": "header", "order": 11},
                
                # Billing Address Fields
                {"field_name": "billing_address", "field_label": "Billing Address", "field_type": "textarea", "section": "billing", "order": 12},
                {"field_name": "billing_city", "field_label": "Billing City", "field_type": "text", "section": "billing", "order": 13},
                {"field_name": "billing_state", "field_label": "Billing State", "field_type": "text", "section": "billing", "order": 14},
                {"field_name": "billing_pincode", "field_label": "Billing Pincode", "field_type": "text", "section": "billing", "order": 15},
                {"field_name": "gstin", "field_label": "Customer GSTIN", "field_type": "text", "section": "billing", "order": 16},
                
                # Shipping Address Fields
                {"field_name": "shipping_address", "field_label": "Shipping Address", "field_type": "textarea", "section": "shipping", "order": 17},
                {"field_name": "shipping_city", "field_label": "Shipping City", "field_type": "text", "section": "shipping", "order": 18},
                {"field_name": "shipping_state", "field_label": "Shipping State", "field_type": "text", "section": "shipping", "order": 19},
                {"field_name": "shipping_pincode", "field_label": "Shipping Pincode", "field_type": "text", "section": "shipping", "order": 20}
            ],
            "list_display_fields": ["quote_number", "account_name", "quote_date", "grand_total", "status"],
            "line_item_fields": [
                {"field_name": "item_id", "field_label": "Item", "field_type": "select", "auto_suggest": "item_master", "order": 1},
                {"field_name": "item_name", "field_label": "Item Name", "field_type": "text", "order": 2},
                {"field_name": "description", "field_label": "Description", "field_type": "text", "order": 3},
                {"field_name": "hsn_code", "field_label": "HSN Code", "field_type": "text", "order": 4},
                {"field_name": "quantity", "field_label": "Quantity", "field_type": "number", "default_value": 1, "order": 5},
                {"field_name": "unit", "field_label": "Unit", "field_type": "select", "options": [
                    {"value": "Pcs", "label": "PCS"},
                    {"value": "Rolls", "label": "Rolls"},
                    {"value": "Mtr", "label": "MTR"},
                    {"value": "Kg", "label": "KG"},
                    {"value": "Sqm", "label": "SQM"}
                ], "order": 6},
                {"field_name": "unit_price", "field_label": "Unit Price", "field_type": "currency", "order": 7},
                {"field_name": "discount_percent", "field_label": "Discount %", "field_type": "number", "default_value": 0, "order": 8},
                {"field_name": "tax_percent", "field_label": "Tax %", "field_type": "number", "default_value": 18, "order": 9}
            ]
        }
    
    elif module == 'crm' and entity == 'samples':
        return {
            "module": "crm",
            "entity": "samples",
            "entity_label": "Samples",
            "fields": [
                # Core Fields - These appear at the top of the sample form
                {"field_name": "account_id", "field_label": "Customer", "field_type": "select", "section": "core", "is_required": True, "auto_suggest": "accounts", "order": 1},
                {"field_name": "contact_person", "field_label": "Contact Person", "field_type": "text", "section": "core", "order": 2},
                
                # Header Fields - These appear below core fields in the sample form
                {"field_name": "purpose", "field_label": "Purpose", "field_type": "select", "section": "header", "order": 3,
                    "options": [
                        {"value": "new_product", "label": "New Product Trial"},
                        {"value": "quality_check", "label": "Quality Check"},
                        {"value": "replacement", "label": "Replacement"},
                        {"value": "customer_request", "label": "Customer Request"},
                        {"value": "competitor_comparison", "label": "Competitor Comparison"}
                    ]
                },
                {"field_name": "quotation_id", "field_label": "Related Quotation", "field_type": "select", "section": "header", "order": 4, "help_text": "Link to existing quotation if applicable"},
                {"field_name": "from_location", "field_label": "Dispatch Location", "field_type": "select", "section": "header", "order": 5,
                    "options": [
                        {"value": "main_warehouse", "label": "Main Warehouse"},
                        {"value": "factory", "label": "Factory"},
                        {"value": "branch_gj", "label": "Gujarat Branch"},
                        {"value": "branch_mh", "label": "Mumbai Branch"},
                        {"value": "branch_dl", "label": "Delhi Branch"}
                    ]
                },
                {"field_name": "courier", "field_label": "Courier/Transport", "field_type": "text", "section": "header", "placeholder": "Courier name", "order": 6},
                {"field_name": "tracking_number", "field_label": "Tracking Number", "field_type": "text", "section": "header", "order": 7},
                {"field_name": "expected_delivery", "field_label": "Expected Delivery", "field_type": "date", "section": "header", "order": 8},
                {"field_name": "feedback_due_date", "field_label": "Feedback Due Date", "field_type": "date", "section": "header", "order": 9},
                {"field_name": "notes", "field_label": "Notes", "field_type": "textarea", "section": "header", "order": 10}
            ],
            "list_display_fields": ["sample_number", "customer_name", "products", "status", "feedback", "due_date"],
            "sample_item_fields": [
                {"field_name": "product_name", "field_label": "Product Name", "field_type": "select", "auto_suggest": "item_master", "order": 1},
                {"field_name": "product_specs", "field_label": "Product Specs", "field_type": "text", "order": 2},
                {"field_name": "quantity", "field_label": "Qty", "field_type": "number", "default_value": 1, "order": 3},
                {"field_name": "unit", "field_label": "Unit", "field_type": "select", "options": [
                    {"value": "Pcs", "label": "PCS"},
                    {"value": "Roll", "label": "Roll"},
                    {"value": "Mtr", "label": "MTR"},
                    {"value": "Kg", "label": "KG"}
                ], "order": 4}
            ]
        }
    
    # ==================== INVENTORY MODULE ====================
    elif module == 'inventory' and entity in ['items', 'stock_items']:
        return {
            "module": "inventory",
            "entity": entity,
            "entity_label": "Items / Products",
            "fields": [
                # Display Fields
                {"field_name": "item_code", "field_label": "Item Code", "field_type": "text", "section": "display", "is_required": True, "show_in_list": True, "order": 1},
                {"field_name": "item_name", "field_label": "Product Name", "field_type": "text", "section": "display", "is_required": True, "show_in_list": True, "order": 2},
                {"field_name": "category", "field_label": "Category", "field_type": "select", "section": "display", "show_in_list": True, "order": 3,
                    "options": [
                        {"value": "bopp", "label": "BOPP Tape"},
                        {"value": "masking", "label": "Masking Tape"},
                        {"value": "double_sided", "label": "Double Sided"},
                        {"value": "cloth", "label": "Cloth Tape"},
                        {"value": "pvc", "label": "PVC Tape"},
                        {"value": "foam", "label": "Foam Tape"},
                        {"value": "specialty", "label": "Specialty"},
                        {"value": "raw_material", "label": "Raw Material"}
                    ]
                },
                {"field_name": "specs", "field_label": "Specs", "field_type": "text", "section": "display", "show_in_list": True, "is_readonly": True, "order": 4},
                {"field_name": "primary_uom", "field_label": "UOM", "field_type": "select", "section": "display", "show_in_list": True, "order": 5,
                    "options": [
                        {"value": "KG", "label": "KG"},
                        {"value": "SQM", "label": "SQM"},
                        {"value": "PCS", "label": "PCS"},
                        {"value": "ROLL", "label": "Roll"},
                        {"value": "MTR", "label": "Meter"},
                        {"value": "BOX", "label": "Box"},
                        {"value": "CTN", "label": "Carton"}
                    ]
                },
                {"field_name": "current_stock", "field_label": "Stock", "field_type": "number", "section": "display", "show_in_list": True, "is_readonly": True, "order": 6},
                {"field_name": "reorder_level", "field_label": "Reorder", "field_type": "number", "section": "display", "show_in_list": True, "order": 7},
                {"field_name": "item_type", "field_label": "Type", "field_type": "select", "section": "display", "show_in_list": True, "order": 8,
                    "options": [
                        {"value": "finished", "label": "Finished Good"},
                        {"value": "raw", "label": "Raw Material"},
                        {"value": "wip", "label": "Work in Progress"},
                        {"value": "consumable", "label": "Consumable"},
                        {"value": "service", "label": "Service"}
                    ]
                },
                # Basic Section
                {"field_name": "hsn_code", "field_label": "HSN Code", "field_type": "select", "section": "basic", "is_required": True, "order": 9,
                    "options": [
                        {"value": "39199090", "label": "39199090 - Self-adhesive plates, sheets"},
                        {"value": "39191000", "label": "39191000 - In rolls of width <= 20cm"},
                        {"value": "48114100", "label": "48114100 - Self-adhesive paper"},
                        {"value": "48142000", "label": "48142000 - Wall paper"}
                    ]
                },
                {"field_name": "secondary_uom", "field_label": "Secondary UOM", "field_type": "select", "section": "basic", "order": 10,
                    "options": [
                        {"value": "KG", "label": "KG"},
                        {"value": "SQM", "label": "SQM"},
                        {"value": "PCS", "label": "PCS"},
                        {"value": "ROLL", "label": "Roll"},
                        {"value": "MTR", "label": "Meter"}
                    ]
                },
                {"field_name": "uom_conversion", "field_label": "UOM Conversion Method", "field_type": "select", "section": "basic", "order": 11,
                    "options": [
                        {"value": "fixed", "label": "Fixed Ratio"},
                        {"value": "formula", "label": "Formula Based"},
                        {"value": "none", "label": "No Conversion"}
                    ]
                },
                {"field_name": "conversion_factor", "field_label": "Conversion Factor", "field_type": "number", "section": "basic", "order": 12},
                # Specs Section
                {"field_name": "base_material", "field_label": "Base Material", "field_type": "select", "section": "specs", "order": 13,
                    "options": [
                        {"value": "bopp_film", "label": "BOPP Film"},
                        {"value": "pvc_film", "label": "PVC Film"},
                        {"value": "paper", "label": "Paper"},
                        {"value": "cloth", "label": "Cloth"},
                        {"value": "foam", "label": "Foam"},
                        {"value": "pet", "label": "PET"}
                    ]
                },
                {"field_name": "adhesive_type", "field_label": "Adhesive Type", "field_type": "select", "section": "specs", "order": 14,
                    "options": [
                        {"value": "acrylic", "label": "Acrylic"},
                        {"value": "hotmelt", "label": "Hotmelt"},
                        {"value": "solvent", "label": "Solvent"},
                        {"value": "rubber", "label": "Rubber"},
                        {"value": "silicone", "label": "Silicone"}
                    ]
                },
                {"field_name": "thickness", "field_label": "Thickness (Microns)", "field_type": "number", "section": "specs", "order": 15},
                {"field_name": "color", "field_label": "Color", "field_type": "select", "section": "specs", "order": 16,
                    "options": [
                        {"value": "transparent", "label": "Transparent"},
                        {"value": "brown", "label": "Brown"},
                        {"value": "white", "label": "White"},
                        {"value": "black", "label": "Black"},
                        {"value": "red", "label": "Red"},
                        {"value": "yellow", "label": "Yellow"},
                        {"value": "green", "label": "Green"},
                        {"value": "blue", "label": "Blue"},
                        {"value": "printed", "label": "Printed/Custom"}
                    ]
                },
                {"field_name": "width", "field_label": "Width (mm)", "field_type": "number", "section": "specs", "order": 17},
                {"field_name": "length", "field_label": "Length (mtr)", "field_type": "number", "section": "specs", "order": 18},
                # Pricing Section
                {"field_name": "cost_price", "field_label": "Cost Price", "field_type": "currency", "section": "pricing", "is_required": True, "order": 19},
                {"field_name": "margin_percent", "field_label": "Margin %", "field_type": "number", "section": "pricing", "order": 20},
                {"field_name": "min_selling_price", "field_label": "Min Selling Price (MSP)", "field_type": "currency", "section": "pricing", "auto_calculate": True, "order": 21, "help_text": "Auto-calculated: Cost + Margin%"},
                {"field_name": "mrp", "field_label": "MRP", "field_type": "currency", "section": "pricing", "order": 22},
                # Inventory Section
                {"field_name": "safety_stock", "field_label": "Safety Stock Level", "field_type": "number", "section": "inventory", "order": 23},
                {"field_name": "lead_time_days", "field_label": "Lead Time (Days)", "field_type": "number", "section": "inventory", "order": 24},
                {"field_name": "shelf_life_days", "field_label": "Shelf Life (Days)", "field_type": "number", "section": "inventory", "order": 25},
                {"field_name": "label_format", "field_label": "Label Format", "field_type": "select", "section": "inventory", "order": 26,
                    "options": [
                        {"value": "standard", "label": "Standard Label"},
                        {"value": "barcode_only", "label": "Barcode Only"},
                        {"value": "qr_code", "label": "QR Code"},
                        {"value": "custom", "label": "Custom Format"}
                    ]
                },
                {"field_name": "barcode", "field_label": "Barcode", "field_type": "text", "section": "inventory", "is_readonly": True, "order": 27},
                {"field_name": "is_active", "field_label": "Active", "field_type": "checkbox", "section": "inventory", "default_value": True, "order": 28}
            ],
            "list_display_fields": ["item_code", "item_name", "category", "specs", "primary_uom", "current_stock", "reorder_level", "item_type"]
        }
    
    elif module == 'inventory' and entity == 'warehouses':
        return {
            "module": "inventory",
            "entity": "warehouses",
            "entity_label": "Warehouses",
            "fields": [
                # Display Fields
                {"field_name": "warehouse_code", "field_label": "Warehouse Code", "field_type": "text", "section": "display", "is_required": True, "show_in_list": True, "order": 1},
                {"field_name": "warehouse_name", "field_label": "Warehouse Name", "field_type": "text", "section": "display", "is_required": True, "show_in_list": True, "order": 2},
                {"field_name": "gstin", "field_label": "GST No", "field_type": "text", "section": "display", "is_required": True, "show_in_list": True, "order": 3},
                {"field_name": "state", "field_label": "State", "field_type": "text", "section": "display", "show_in_list": True, "order": 4},
                {"field_name": "city", "field_label": "City", "field_type": "text", "section": "display", "show_in_list": True, "order": 5},
                {"field_name": "is_active", "field_label": "Status", "field_type": "checkbox", "section": "display", "show_in_list": True, "order": 6},
                # Form Fields
                {"field_name": "prefix", "field_label": "Document Prefix", "field_type": "text", "section": "form", "is_required": True, "order": 7, "help_text": "Used for serial numbers (e.g., GJ, MH, DL)"},
                {"field_name": "pincode", "field_label": "Pincode", "field_type": "text", "section": "form", "auto_fill_source": "pincode", "order": 8},
                {"field_name": "address", "field_label": "Full Address", "field_type": "textarea", "section": "form", "order": 9},
                {"field_name": "bank_name", "field_label": "Bank Name", "field_type": "text", "section": "bank", "order": 10},
                {"field_name": "bank_account", "field_label": "Account Number", "field_type": "text", "section": "bank", "order": 11},
                {"field_name": "ifsc_code", "field_label": "IFSC Code", "field_type": "text", "section": "bank", "order": 12},
                {"field_name": "bank_branch", "field_label": "Branch", "field_type": "text", "section": "bank", "order": 13},
                {"field_name": "email", "field_label": "Email Address", "field_type": "email", "section": "contact", "order": 14},
                {"field_name": "phone", "field_label": "Contact No", "field_type": "phone", "section": "contact", "order": 15},
                {"field_name": "contact_person", "field_label": "Contact Person", "field_type": "text", "section": "contact", "order": 16}
            ],
            "list_display_fields": ["warehouse_code", "warehouse_name", "gstin", "state", "city", "is_active"]
        }
    
    elif module == 'inventory' and entity == 'stock':
        return {
            "module": "inventory",
            "entity": "stock",
            "entity_label": "Stock Management",
            "fields": [
                {"field_name": "item_code", "field_label": "Item Code", "field_type": "select", "section": "display", "show_in_list": True, "order": 1},
                {"field_name": "item_name", "field_label": "Item Name", "field_type": "text", "section": "display", "show_in_list": True, "is_readonly": True, "order": 2},
                {"field_name": "warehouse", "field_label": "Warehouse", "field_type": "select", "section": "display", "show_in_list": True, "order": 3},
                {"field_name": "batch_no", "field_label": "Batch No", "field_type": "text", "section": "display", "show_in_list": True, "order": 4},
                {"field_name": "quantity", "field_label": "Quantity", "field_type": "number", "section": "display", "show_in_list": True, "order": 5},
                {"field_name": "uom", "field_label": "UOM", "field_type": "text", "section": "display", "show_in_list": True, "order": 6},
                {"field_name": "rack_location", "field_label": "Rack Location", "field_type": "text", "section": "form", "order": 7},
                {"field_name": "expiry_date", "field_label": "Expiry Date", "field_type": "date", "section": "form", "order": 8},
                {"field_name": "cost_price", "field_label": "Cost Price", "field_type": "currency", "section": "form", "order": 9},
                {"field_name": "barcode", "field_label": "Barcode", "field_type": "text", "section": "form", "order": 10}
            ],
            "list_display_fields": ["item_code", "item_name", "warehouse", "batch_no", "quantity", "uom"]
        }
    
    elif module == 'inventory' and entity == 'serial_numbers':
        return {
            "module": "inventory",
            "entity": "serial_numbers",
            "entity_label": "Serial Number Master",
            "fields": [
                {"field_name": "doc_type", "field_label": "Document Type", "field_type": "select", "section": "display", "is_required": True, "show_in_list": True, "order": 1,
                    "options": [
                        {"value": "quotation", "label": "Quotation"},
                        {"value": "sales_order", "label": "Sales Order"},
                        {"value": "invoice", "label": "Sales Invoice"},
                        {"value": "credit_note", "label": "Credit Note"},
                        {"value": "purchase_order", "label": "Purchase Order"},
                        {"value": "grn", "label": "GRN"},
                        {"value": "purchase_invoice", "label": "Purchase Invoice"},
                        {"value": "debit_note", "label": "Debit Note"},
                        {"value": "stock_transfer", "label": "Stock Transfer"},
                        {"value": "batch", "label": "Batch Number"},
                        {"value": "sample", "label": "Sample"}
                    ]
                },
                {"field_name": "warehouse", "field_label": "Warehouse", "field_type": "select", "section": "display", "show_in_list": True, "order": 2},
                {"field_name": "prefix", "field_label": "Prefix", "field_type": "text", "section": "form", "order": 3, "help_text": "e.g., INV, QT, PO"},
                {"field_name": "suffix", "field_label": "Suffix", "field_type": "text", "section": "form", "order": 4},
                {"field_name": "separator", "field_label": "Separator", "field_type": "text", "section": "form", "default_value": "/", "order": 5},
                {"field_name": "include_fy", "field_label": "Include Financial Year", "field_type": "checkbox", "section": "form", "default_value": True, "order": 6},
                {"field_name": "fy_format", "field_label": "FY Format", "field_type": "select", "section": "form", "order": 7,
                    "options": [
                        {"value": "2425", "label": "2425 (Short)"},
                        {"value": "24-25", "label": "24-25"},
                        {"value": "2024-25", "label": "2024-25"}
                    ]
                },
                {"field_name": "number_length", "field_label": "Number Length", "field_type": "number", "section": "form", "default_value": 4, "order": 8},
                {"field_name": "current_number", "field_label": "Current Number", "field_type": "number", "section": "form", "order": 9},
                {"field_name": "reset_on_fy", "field_label": "Reset on New FY", "field_type": "checkbox", "section": "form", "default_value": True, "order": 10},
                {"field_name": "sample_format", "field_label": "Sample Format", "field_type": "text", "section": "display", "is_readonly": True, "show_in_list": True, "order": 11}
            ],
            "list_display_fields": ["doc_type", "warehouse", "prefix", "sample_format"]
        }
    
    elif module == 'inventory' and entity == 'stock_transfers':
        return {
            "module": "inventory",
            "entity": "stock_transfers",
            "entity_label": "Stock Transfers",
            "fields": [
                {"field_name": "transfer_no", "field_label": "Transfer No", "field_type": "auto", "section": "display", "show_in_list": True, "is_readonly": True, "order": 1},
                {"field_name": "transfer_date", "field_label": "Date", "field_type": "date", "section": "display", "show_in_list": True, "order": 2},
                {"field_name": "from_warehouse", "field_label": "From Warehouse", "field_type": "select", "section": "display", "is_required": True, "show_in_list": True, "order": 3},
                {"field_name": "to_warehouse", "field_label": "To Warehouse", "field_type": "select", "section": "display", "is_required": True, "show_in_list": True, "order": 4},
                {"field_name": "status", "field_label": "Status", "field_type": "select", "section": "display", "show_in_list": True, "order": 5,
                    "options": [
                        {"value": "draft", "label": "Draft", "color": "slate"},
                        {"value": "in_transit", "label": "In Transit", "color": "blue"},
                        {"value": "received", "label": "Received", "color": "green"},
                        {"value": "cancelled", "label": "Cancelled", "color": "red"}
                    ]
                },
                {"field_name": "total_items", "field_label": "Total Items", "field_type": "number", "section": "display", "show_in_list": True, "is_readonly": True, "order": 6},
                {"field_name": "vehicle_no", "field_label": "Vehicle No", "field_type": "text", "section": "form", "order": 7},
                {"field_name": "driver_name", "field_label": "Driver Name", "field_type": "text", "section": "form", "order": 8},
                {"field_name": "driver_phone", "field_label": "Driver Phone", "field_type": "phone", "section": "form", "order": 9},
                {"field_name": "notes", "field_label": "Notes", "field_type": "textarea", "section": "form", "order": 10}
            ],
            "list_display_fields": ["transfer_no", "transfer_date", "from_warehouse", "to_warehouse", "status", "total_items"],
            "transfer_item_fields": [
                {"field_name": "item_code", "field_label": "Item Code", "field_type": "select", "order": 1},
                {"field_name": "item_name", "field_label": "Item Name", "field_type": "text", "is_readonly": True, "order": 2},
                {"field_name": "batch_no", "field_label": "Batch No", "field_type": "select", "order": 3},
                {"field_name": "quantity", "field_label": "Quantity", "field_type": "number", "order": 4},
                {"field_name": "uom", "field_label": "UOM", "field_type": "text", "is_readonly": True, "order": 5}
            ]
        }
    
    elif module == 'inventory' and entity == 'stock_adjustments':
        return {
            "module": "inventory",
            "entity": "stock_adjustments",
            "entity_label": "Stock Adjustments",
            "fields": [
                {"field_name": "adjustment_no", "field_label": "Adjustment No", "field_type": "auto", "section": "display", "show_in_list": True, "is_readonly": True, "order": 1},
                {"field_name": "adjustment_date", "field_label": "Date", "field_type": "date", "section": "display", "show_in_list": True, "order": 2},
                {"field_name": "warehouse", "field_label": "Warehouse", "field_type": "select", "section": "display", "is_required": True, "show_in_list": True, "order": 3},
                {"field_name": "adjustment_type", "field_label": "Type", "field_type": "select", "section": "display", "is_required": True, "show_in_list": True, "order": 4,
                    "options": [
                        {"value": "opening", "label": "Opening Stock"},
                        {"value": "closing", "label": "Closing Stock"},
                        {"value": "increase", "label": "Stock Increase"},
                        {"value": "decrease", "label": "Stock Decrease"},
                        {"value": "damage", "label": "Damage/Loss"},
                        {"value": "expired", "label": "Expired"},
                        {"value": "recount", "label": "Physical Recount"}
                    ]
                },
                {"field_name": "status", "field_label": "Status", "field_type": "select", "section": "display", "show_in_list": True, "order": 5,
                    "options": [
                        {"value": "draft", "label": "Draft"},
                        {"value": "approved", "label": "Approved"},
                        {"value": "cancelled", "label": "Cancelled"}
                    ]
                },
                {"field_name": "reason", "field_label": "Reason", "field_type": "textarea", "section": "form", "order": 6},
                {"field_name": "reference", "field_label": "Reference Doc", "field_type": "text", "section": "form", "order": 7}
            ],
            "list_display_fields": ["adjustment_no", "adjustment_date", "warehouse", "adjustment_type", "status"],
            "adjustment_item_fields": [
                {"field_name": "item_code", "field_label": "Item Code", "field_type": "select", "order": 1},
                {"field_name": "item_name", "field_label": "Item Name", "field_type": "text", "is_readonly": True, "order": 2},
                {"field_name": "batch_no", "field_label": "Batch No", "field_type": "text", "order": 3},
                {"field_name": "current_qty", "field_label": "Current Qty", "field_type": "number", "is_readonly": True, "order": 4},
                {"field_name": "adjusted_qty", "field_label": "Adjusted Qty", "field_type": "number", "order": 5},
                {"field_name": "difference", "field_label": "Difference", "field_type": "number", "is_readonly": True, "order": 6},
                {"field_name": "uom", "field_label": "UOM", "field_type": "text", "is_readonly": True, "order": 7}
            ]
        }
    
    # ==================== PRODUCTION MODULE ====================
    elif module == 'production' and entity == 'machines':
        return {
            "module": "production",
            "entity": "machines",
            "entity_label": "Production Machines",
            "fields": [
                {"field_name": "machine_code", "field_label": "Machine Code", "field_type": "text", "section": "basic", "is_required": True, "show_in_list": True, "order": 1},
                {"field_name": "machine_name", "field_label": "Machine Name", "field_type": "text", "section": "basic", "is_required": True, "show_in_list": True, "order": 2},
                {"field_name": "machine_type", "field_label": "Machine Type", "field_type": "select", "section": "basic", "is_required": True, "show_in_list": True, "order": 3,
                    "options": [
                        {"value": "coating", "label": "Coating Machine"},
                        {"value": "slitting", "label": "Slitting Machine"},
                        {"value": "rewinding", "label": "Rewinding Machine"},
                        {"value": "cutting", "label": "Cutting Machine"},
                        {"value": "packing", "label": "Packing Machine"},
                        {"value": "printing", "label": "Printing Machine"},
                        {"value": "lamination", "label": "Lamination Machine"}
                    ]
                },
                {"field_name": "location", "field_label": "Location/Bay", "field_type": "text", "section": "basic", "order": 4},
                {"field_name": "status", "field_label": "Status", "field_type": "select", "section": "basic", "show_in_list": True, "order": 5,
                    "options": [
                        {"value": "active", "label": "Active", "color": "green"},
                        {"value": "maintenance", "label": "Under Maintenance", "color": "yellow"},
                        {"value": "breakdown", "label": "Breakdown", "color": "red"},
                        {"value": "inactive", "label": "Inactive", "color": "slate"}
                    ]
                },
                {"field_name": "capacity_per_hour", "field_label": "Capacity/Hour", "field_type": "number", "section": "capacity", "order": 6},
                {"field_name": "capacity_uom", "field_label": "Capacity UOM", "field_type": "select", "section": "capacity", "order": 7,
                    "options": [
                        {"value": "sqm", "label": "SQM"},
                        {"value": "mtr", "label": "Meters"},
                        {"value": "kg", "label": "KG"},
                        {"value": "rolls", "label": "Rolls"},
                        {"value": "pcs", "label": "Pieces"}
                    ]
                },
                {"field_name": "wastage_norm_percent", "field_label": "Wastage Norm %", "field_type": "number", "section": "capacity", "default_value": 5, "order": 8},
                {"field_name": "max_width", "field_label": "Max Width (mm)", "field_type": "number", "section": "specs", "order": 9},
                {"field_name": "min_width", "field_label": "Min Width (mm)", "field_type": "number", "section": "specs", "order": 10},
                {"field_name": "max_speed", "field_label": "Max Speed (m/min)", "field_type": "number", "section": "specs", "order": 11},
                {"field_name": "power_consumption", "field_label": "Power (kW)", "field_type": "number", "section": "specs", "order": 12},
                {"field_name": "manufacturer", "field_label": "Manufacturer", "field_type": "text", "section": "maintenance", "order": 13},
                {"field_name": "purchase_date", "field_label": "Purchase Date", "field_type": "date", "section": "maintenance", "order": 14},
                {"field_name": "last_service_date", "field_label": "Last Service Date", "field_type": "date", "section": "maintenance", "order": 15},
                {"field_name": "next_service_date", "field_label": "Next Service Date", "field_type": "date", "section": "maintenance", "order": 16},
                {"field_name": "notes", "field_label": "Notes", "field_type": "textarea", "section": "maintenance", "order": 17}
            ],
            "list_display_fields": ["machine_code", "machine_name", "machine_type", "status", "capacity_per_hour", "wastage_norm_percent"]
        }
    
    elif module == 'production' and entity == 'order_sheets':
        return {
            "module": "production",
            "entity": "order_sheets",
            "entity_label": "Production Order Sheets",
            "fields": [
                {"field_name": "order_sheet_no", "field_label": "Order Sheet No", "field_type": "auto", "section": "display", "show_in_list": True, "is_readonly": True, "order": 1},
                {"field_name": "sales_order_id", "field_label": "Sales Order", "field_type": "select", "section": "display", "is_required": True, "show_in_list": True, "order": 2},
                {"field_name": "customer_name", "field_label": "Customer", "field_type": "text", "section": "display", "show_in_list": True, "is_readonly": True, "order": 3},
                {"field_name": "status", "field_label": "Status", "field_type": "select", "section": "display", "show_in_list": True, "order": 4,
                    "options": [
                        {"value": "draft", "label": "Draft", "color": "slate"},
                        {"value": "in_progress", "label": "In Progress", "color": "blue"},
                        {"value": "completed", "label": "Completed", "color": "green"},
                        {"value": "on_hold", "label": "On Hold", "color": "yellow"},
                        {"value": "cancelled", "label": "Cancelled", "color": "red"}
                    ]
                },
                {"field_name": "priority", "field_label": "Priority", "field_type": "select", "section": "display", "show_in_list": True, "order": 5,
                    "options": [
                        {"value": "low", "label": "Low", "color": "slate"},
                        {"value": "normal", "label": "Normal", "color": "blue"},
                        {"value": "high", "label": "High", "color": "orange"},
                        {"value": "urgent", "label": "Urgent", "color": "red"}
                    ]
                },
                {"field_name": "planned_start", "field_label": "Planned Start", "field_type": "date", "section": "planning", "order": 6},
                {"field_name": "planned_end", "field_label": "Planned End", "field_type": "date", "section": "planning", "order": 7},
                {"field_name": "actual_start", "field_label": "Actual Start", "field_type": "date", "section": "planning", "order": 8},
                {"field_name": "actual_end", "field_label": "Actual End", "field_type": "date", "section": "planning", "order": 9},
                {"field_name": "total_work_orders", "field_label": "Work Orders", "field_type": "number", "section": "display", "show_in_list": True, "is_readonly": True, "order": 10},
                {"field_name": "progress_percent", "field_label": "Progress %", "field_type": "number", "section": "display", "show_in_list": True, "is_readonly": True, "order": 11},
                {"field_name": "notes", "field_label": "Production Notes", "field_type": "textarea", "section": "form", "order": 12}
            ],
            "list_display_fields": ["order_sheet_no", "sales_order_id", "customer_name", "status", "priority", "progress_percent"]
        }
    
    elif module == 'production' and entity == 'work_orders':
        return {
            "module": "production",
            "entity": "work_orders",
            "entity_label": "Work Orders",
            "fields": [
                {"field_name": "wo_number", "field_label": "WO Number", "field_type": "auto", "section": "display", "show_in_list": True, "is_readonly": True, "order": 1},
                {"field_name": "stage", "field_label": "Production Stage", "field_type": "select", "section": "display", "is_required": True, "show_in_list": True, "order": 2,
                    "options": [
                        {"value": "coating", "label": "Coating"},
                        {"value": "slitting", "label": "Slitting"},
                        {"value": "rewinding", "label": "Rewinding"},
                        {"value": "cutting", "label": "Cutting"},
                        {"value": "packing", "label": "Packing"},
                        {"value": "ready_to_deliver", "label": "Ready to Deliver"},
                        {"value": "delivered", "label": "Delivered"}
                    ]
                },
                {"field_name": "item_name", "field_label": "Item", "field_type": "text", "section": "display", "show_in_list": True, "is_readonly": True, "order": 3},
                {"field_name": "target_qty", "field_label": "Target Qty", "field_type": "number", "section": "display", "show_in_list": True, "order": 4},
                {"field_name": "target_uom", "field_label": "UOM", "field_type": "select", "section": "display", "order": 5,
                    "options": [
                        {"value": "pcs", "label": "PCS"},
                        {"value": "rolls", "label": "Rolls"},
                        {"value": "sqm", "label": "SQM"},
                        {"value": "kg", "label": "KG"},
                        {"value": "mtr", "label": "MTR"}
                    ]
                },
                {"field_name": "completed_qty", "field_label": "Completed Qty", "field_type": "number", "section": "display", "show_in_list": True, "is_readonly": True, "order": 6},
                {"field_name": "wastage_qty", "field_label": "Wastage Qty", "field_type": "number", "section": "display", "is_readonly": True, "order": 7},
                {"field_name": "status", "field_label": "Status", "field_type": "select", "section": "display", "show_in_list": True, "order": 8,
                    "options": [
                        {"value": "pending", "label": "Pending", "color": "slate"},
                        {"value": "in_progress", "label": "In Progress", "color": "blue"},
                        {"value": "completed", "label": "Completed", "color": "green"},
                        {"value": "on_hold", "label": "On Hold", "color": "yellow"}
                    ]
                },
                {"field_name": "machine_id", "field_label": "Assigned Machine", "field_type": "select", "section": "assignment", "order": 9},
                {"field_name": "operator_id", "field_label": "Operator", "field_type": "select", "section": "assignment", "order": 10},
                {"field_name": "priority", "field_label": "Priority", "field_type": "select", "section": "assignment", "show_in_list": True, "order": 11,
                    "options": [
                        {"value": "low", "label": "Low"},
                        {"value": "normal", "label": "Normal"},
                        {"value": "high", "label": "High"},
                        {"value": "urgent", "label": "Urgent"}
                    ]
                },
                {"field_name": "scheduled_date", "field_label": "Scheduled Date", "field_type": "date", "section": "scheduling", "order": 12},
                {"field_name": "due_date", "field_label": "Due Date", "field_type": "date", "section": "scheduling", "order": 13},
                {"field_name": "instructions", "field_label": "Special Instructions", "field_type": "textarea", "section": "form", "order": 14}
            ],
            "list_display_fields": ["wo_number", "stage", "item_name", "target_qty", "completed_qty", "status", "priority"]
        }
    
    # ==================== ACCOUNTS/FINANCE MODULE ====================
    elif module == 'accounts' and entity == 'invoices':
        return {
            "module": "accounts",
            "entity": "invoices",
            "entity_label": "Sales Invoices",
            "fields": [
                {"field_name": "invoice_no", "field_label": "Invoice No", "field_type": "auto", "section": "display", "show_in_list": True, "is_readonly": True, "order": 1},
                {"field_name": "invoice_date", "field_label": "Invoice Date", "field_type": "date", "section": "display", "is_required": True, "show_in_list": True, "order": 2},
                {"field_name": "customer_id", "field_label": "Customer", "field_type": "select", "section": "display", "is_required": True, "show_in_list": True, "order": 3},
                {"field_name": "customer_gstin", "field_label": "Customer GSTIN", "field_type": "text", "section": "display", "order": 4},
                {"field_name": "place_of_supply", "field_label": "Place of Supply", "field_type": "select", "section": "display", "is_required": True, "order": 5},
                {"field_name": "invoice_type", "field_label": "Invoice Type", "field_type": "select", "section": "display", "show_in_list": True, "order": 6,
                    "options": [
                        {"value": "regular", "label": "Regular (B2B)"},
                        {"value": "b2c_large", "label": "B2C Large"},
                        {"value": "b2c_small", "label": "B2C Small"},
                        {"value": "export", "label": "Export"},
                        {"value": "sez", "label": "SEZ Supply"}
                    ]
                },
                {"field_name": "status", "field_label": "Status", "field_type": "select", "section": "display", "show_in_list": True, "order": 7,
                    "options": [
                        {"value": "draft", "label": "Draft", "color": "slate"},
                        {"value": "pending", "label": "Pending", "color": "yellow"},
                        {"value": "sent", "label": "Sent", "color": "blue"},
                        {"value": "paid", "label": "Paid", "color": "green"},
                        {"value": "overdue", "label": "Overdue", "color": "red"},
                        {"value": "cancelled", "label": "Cancelled", "color": "slate"}
                    ]
                },
                {"field_name": "subtotal", "field_label": "Subtotal", "field_type": "currency", "section": "totals", "is_readonly": True, "order": 8},
                {"field_name": "discount_amount", "field_label": "Discount", "field_type": "currency", "section": "totals", "order": 9},
                {"field_name": "cgst", "field_label": "CGST", "field_type": "currency", "section": "totals", "is_readonly": True, "order": 10},
                {"field_name": "sgst", "field_label": "SGST", "field_type": "currency", "section": "totals", "is_readonly": True, "order": 11},
                {"field_name": "igst", "field_label": "IGST", "field_type": "currency", "section": "totals", "is_readonly": True, "order": 12},
                {"field_name": "grand_total", "field_label": "Grand Total", "field_type": "currency", "section": "totals", "show_in_list": True, "is_readonly": True, "order": 13},
                {"field_name": "amount_paid", "field_label": "Amount Paid", "field_type": "currency", "section": "totals", "is_readonly": True, "order": 14},
                {"field_name": "balance_due", "field_label": "Balance Due", "field_type": "currency", "section": "totals", "show_in_list": True, "is_readonly": True, "order": 15},
                {"field_name": "due_date", "field_label": "Due Date", "field_type": "date", "section": "payment", "order": 16},
                {"field_name": "payment_terms", "field_label": "Payment Terms", "field_type": "select", "section": "payment", "order": 17,
                    "options": [
                        {"value": "immediate", "label": "Immediate"},
                        {"value": "7_days", "label": "Net 7"},
                        {"value": "15_days", "label": "Net 15"},
                        {"value": "30_days", "label": "Net 30"},
                        {"value": "45_days", "label": "Net 45"},
                        {"value": "60_days", "label": "Net 60"}
                    ]
                },
                {"field_name": "e_invoice_status", "field_label": "E-Invoice Status", "field_type": "select", "section": "einvoice", "order": 18,
                    "options": [
                        {"value": "not_generated", "label": "Not Generated"},
                        {"value": "generated", "label": "Generated"},
                        {"value": "cancelled", "label": "Cancelled"}
                    ]
                },
                {"field_name": "irn", "field_label": "IRN", "field_type": "text", "section": "einvoice", "is_readonly": True, "order": 19},
                {"field_name": "eway_bill_no", "field_label": "E-Way Bill No", "field_type": "text", "section": "einvoice", "order": 20},
                {"field_name": "notes", "field_label": "Notes", "field_type": "textarea", "section": "form", "order": 21},
                {"field_name": "terms_conditions", "field_label": "Terms & Conditions", "field_type": "textarea", "section": "form", "order": 22}
            ],
            "list_display_fields": ["invoice_no", "invoice_date", "customer_name", "invoice_type", "grand_total", "balance_due", "status"],
            "line_item_fields": [
                {"field_name": "item_id", "field_label": "Item", "field_type": "select", "order": 1},
                {"field_name": "description", "field_label": "Description", "field_type": "text", "order": 2},
                {"field_name": "hsn_code", "field_label": "HSN", "field_type": "text", "order": 3},
                {"field_name": "quantity", "field_label": "Qty", "field_type": "number", "order": 4},
                {"field_name": "unit", "field_label": "Unit", "field_type": "select", "order": 5},
                {"field_name": "rate", "field_label": "Rate", "field_type": "currency", "order": 6},
                {"field_name": "discount_percent", "field_label": "Disc %", "field_type": "number", "order": 7},
                {"field_name": "tax_rate", "field_label": "Tax %", "field_type": "number", "order": 8},
                {"field_name": "amount", "field_label": "Amount", "field_type": "currency", "is_readonly": True, "order": 9}
            ]
        }
    
    elif module == 'accounts' and entity == 'purchase_invoices':
        return {
            "module": "accounts",
            "entity": "purchase_invoices",
            "entity_label": "Purchase Invoices",
            "fields": [
                {"field_name": "bill_no", "field_label": "Bill No", "field_type": "text", "section": "display", "is_required": True, "show_in_list": True, "order": 1},
                {"field_name": "bill_date", "field_label": "Bill Date", "field_type": "date", "section": "display", "is_required": True, "show_in_list": True, "order": 2},
                {"field_name": "supplier_id", "field_label": "Supplier", "field_type": "select", "section": "display", "is_required": True, "show_in_list": True, "order": 3},
                {"field_name": "supplier_gstin", "field_label": "Supplier GSTIN", "field_type": "text", "section": "display", "order": 4},
                {"field_name": "supplier_invoice_no", "field_label": "Supplier Invoice No", "field_type": "text", "section": "display", "order": 5},
                {"field_name": "status", "field_label": "Status", "field_type": "select", "section": "display", "show_in_list": True, "order": 6,
                    "options": [
                        {"value": "draft", "label": "Draft"},
                        {"value": "pending", "label": "Pending Payment"},
                        {"value": "partial", "label": "Partially Paid"},
                        {"value": "paid", "label": "Paid"},
                        {"value": "cancelled", "label": "Cancelled"}
                    ]
                },
                {"field_name": "grand_total", "field_label": "Grand Total", "field_type": "currency", "section": "totals", "show_in_list": True, "is_readonly": True, "order": 7},
                {"field_name": "itc_eligible", "field_label": "ITC Eligible", "field_type": "checkbox", "section": "gst", "default_value": True, "order": 8},
                {"field_name": "reverse_charge", "field_label": "Reverse Charge", "field_type": "checkbox", "section": "gst", "order": 9},
                {"field_name": "notes", "field_label": "Notes", "field_type": "textarea", "section": "form", "order": 10}
            ],
            "list_display_fields": ["bill_no", "bill_date", "supplier_name", "grand_total", "status"]
        }
    
    elif module == 'accounts' and entity == 'payments':
        return {
            "module": "accounts",
            "entity": "payments",
            "entity_label": "Payments",
            "fields": [
                {"field_name": "payment_no", "field_label": "Payment No", "field_type": "auto", "section": "display", "show_in_list": True, "is_readonly": True, "order": 1},
                {"field_name": "payment_date", "field_label": "Payment Date", "field_type": "date", "section": "display", "is_required": True, "show_in_list": True, "order": 2},
                {"field_name": "payment_type", "field_label": "Payment Type", "field_type": "select", "section": "display", "is_required": True, "show_in_list": True, "order": 3,
                    "options": [
                        {"value": "receipt", "label": "Receipt (From Customer)"},
                        {"value": "payment", "label": "Payment (To Supplier)"}
                    ]
                },
                {"field_name": "party_id", "field_label": "Party", "field_type": "select", "section": "display", "is_required": True, "show_in_list": True, "order": 4},
                {"field_name": "amount", "field_label": "Amount", "field_type": "currency", "section": "display", "is_required": True, "show_in_list": True, "order": 5},
                {"field_name": "payment_mode", "field_label": "Payment Mode", "field_type": "select", "section": "display", "is_required": True, "show_in_list": True, "order": 6,
                    "options": [
                        {"value": "cash", "label": "Cash"},
                        {"value": "cheque", "label": "Cheque"},
                        {"value": "neft", "label": "NEFT/RTGS"},
                        {"value": "upi", "label": "UPI"},
                        {"value": "card", "label": "Card"}
                    ]
                },
                {"field_name": "reference_no", "field_label": "Reference No", "field_type": "text", "section": "details", "order": 7},
                {"field_name": "bank_account", "field_label": "Bank Account", "field_type": "select", "section": "details", "order": 8},
                {"field_name": "cheque_no", "field_label": "Cheque No", "field_type": "text", "section": "details", "order": 9},
                {"field_name": "cheque_date", "field_label": "Cheque Date", "field_type": "date", "section": "details", "order": 10},
                {"field_name": "tds_amount", "field_label": "TDS Amount", "field_type": "currency", "section": "details", "order": 11},
                {"field_name": "notes", "field_label": "Notes", "field_type": "textarea", "section": "form", "order": 12}
            ],
            "list_display_fields": ["payment_no", "payment_date", "payment_type", "party_name", "amount", "payment_mode"]
        }
    
    # ==================== HRMS MODULE ====================
    elif module == 'hrms' and entity == 'employees':
        return {
            "module": "hrms",
            "entity": "employees",
            "entity_label": "Employees",
            "fields": [
                {"field_name": "emp_code", "field_label": "Employee Code", "field_type": "text", "section": "basic", "is_required": True, "show_in_list": True, "order": 1},
                {"field_name": "full_name", "field_label": "Full Name", "field_type": "text", "section": "basic", "is_required": True, "show_in_list": True, "order": 2},
                {"field_name": "email", "field_label": "Email", "field_type": "email", "section": "basic", "is_required": True, "order": 3},
                {"field_name": "phone", "field_label": "Phone", "field_type": "phone", "section": "basic", "order": 4},
                {"field_name": "department", "field_label": "Department", "field_type": "select", "section": "basic", "show_in_list": True, "order": 5,
                    "options": [
                        {"value": "production", "label": "Production"},
                        {"value": "sales", "label": "Sales"},
                        {"value": "accounts", "label": "Accounts"},
                        {"value": "hr", "label": "HR"},
                        {"value": "purchase", "label": "Purchase"},
                        {"value": "quality", "label": "Quality"},
                        {"value": "stores", "label": "Stores"},
                        {"value": "admin", "label": "Admin"},
                        {"value": "it", "label": "IT"}
                    ]
                },
                {"field_name": "designation", "field_label": "Designation", "field_type": "text", "section": "basic", "show_in_list": True, "order": 6},
                {"field_name": "reporting_to", "field_label": "Reporting To", "field_type": "select", "section": "basic", "order": 7},
                {"field_name": "employment_type", "field_label": "Employment Type", "field_type": "select", "section": "employment", "order": 8,
                    "options": [
                        {"value": "permanent", "label": "Permanent"},
                        {"value": "contract", "label": "Contract"},
                        {"value": "probation", "label": "Probation"},
                        {"value": "trainee", "label": "Trainee"},
                        {"value": "intern", "label": "Intern"}
                    ]
                },
                {"field_name": "joining_date", "field_label": "Joining Date", "field_type": "date", "section": "employment", "is_required": True, "order": 9},
                {"field_name": "status", "field_label": "Status", "field_type": "select", "section": "employment", "show_in_list": True, "order": 10,
                    "options": [
                        {"value": "active", "label": "Active", "color": "green"},
                        {"value": "on_leave", "label": "On Leave", "color": "yellow"},
                        {"value": "notice_period", "label": "Notice Period", "color": "orange"},
                        {"value": "resigned", "label": "Resigned", "color": "red"},
                        {"value": "terminated", "label": "Terminated", "color": "red"}
                    ]
                },
                {"field_name": "dob", "field_label": "Date of Birth", "field_type": "date", "section": "personal", "order": 11},
                {"field_name": "gender", "field_label": "Gender", "field_type": "select", "section": "personal", "order": 12,
                    "options": [
                        {"value": "male", "label": "Male"},
                        {"value": "female", "label": "Female"},
                        {"value": "other", "label": "Other"}
                    ]
                },
                {"field_name": "blood_group", "field_label": "Blood Group", "field_type": "select", "section": "personal", "order": 13,
                    "options": [
                        {"value": "A+", "label": "A+"},
                        {"value": "A-", "label": "A-"},
                        {"value": "B+", "label": "B+"},
                        {"value": "B-", "label": "B-"},
                        {"value": "O+", "label": "O+"},
                        {"value": "O-", "label": "O-"},
                        {"value": "AB+", "label": "AB+"},
                        {"value": "AB-", "label": "AB-"}
                    ]
                },
                {"field_name": "address", "field_label": "Address", "field_type": "textarea", "section": "personal", "order": 14},
                {"field_name": "emergency_contact", "field_label": "Emergency Contact", "field_type": "text", "section": "personal", "order": 15},
                {"field_name": "pan", "field_label": "PAN", "field_type": "text", "section": "statutory", "order": 16},
                {"field_name": "aadhar", "field_label": "Aadhar No", "field_type": "text", "section": "statutory", "order": 17},
                {"field_name": "uan", "field_label": "UAN (PF)", "field_type": "text", "section": "statutory", "order": 18},
                {"field_name": "esi_no", "field_label": "ESI No", "field_type": "text", "section": "statutory", "order": 19},
                {"field_name": "bank_name", "field_label": "Bank Name", "field_type": "text", "section": "bank", "order": 20},
                {"field_name": "bank_account", "field_label": "Account No", "field_type": "text", "section": "bank", "order": 21},
                {"field_name": "ifsc_code", "field_label": "IFSC Code", "field_type": "text", "section": "bank", "order": 22},
                {"field_name": "basic_salary", "field_label": "Basic Salary", "field_type": "currency", "section": "salary", "order": 23},
                {"field_name": "hra", "field_label": "HRA", "field_type": "currency", "section": "salary", "order": 24},
                {"field_name": "other_allowances", "field_label": "Other Allowances", "field_type": "currency", "section": "salary", "order": 25}
            ],
            "list_display_fields": ["emp_code", "full_name", "department", "designation", "status"]
        }
    
    elif module == 'hrms' and entity == 'attendance':
        return {
            "module": "hrms",
            "entity": "attendance",
            "entity_label": "Attendance",
            "fields": [
                {"field_name": "employee_id", "field_label": "Employee", "field_type": "select", "section": "display", "is_required": True, "show_in_list": True, "order": 1},
                {"field_name": "date", "field_label": "Date", "field_type": "date", "section": "display", "is_required": True, "show_in_list": True, "order": 2},
                {"field_name": "check_in", "field_label": "Check In", "field_type": "time", "section": "display", "show_in_list": True, "order": 3},
                {"field_name": "check_out", "field_label": "Check Out", "field_type": "time", "section": "display", "show_in_list": True, "order": 4},
                {"field_name": "status", "field_label": "Status", "field_type": "select", "section": "display", "show_in_list": True, "order": 5,
                    "options": [
                        {"value": "present", "label": "Present", "color": "green"},
                        {"value": "absent", "label": "Absent", "color": "red"},
                        {"value": "half_day", "label": "Half Day", "color": "yellow"},
                        {"value": "late", "label": "Late", "color": "orange"},
                        {"value": "on_leave", "label": "On Leave", "color": "blue"},
                        {"value": "holiday", "label": "Holiday", "color": "purple"},
                        {"value": "week_off", "label": "Week Off", "color": "slate"}
                    ]
                },
                {"field_name": "working_hours", "field_label": "Working Hours", "field_type": "number", "section": "display", "is_readonly": True, "order": 6},
                {"field_name": "overtime_hours", "field_label": "OT Hours", "field_type": "number", "section": "display", "order": 7},
                {"field_name": "shift", "field_label": "Shift", "field_type": "select", "section": "form", "order": 8,
                    "options": [
                        {"value": "general", "label": "General (9AM-6PM)"},
                        {"value": "morning", "label": "Morning (6AM-2PM)"},
                        {"value": "evening", "label": "Evening (2PM-10PM)"},
                        {"value": "night", "label": "Night (10PM-6AM)"}
                    ]
                },
                {"field_name": "remarks", "field_label": "Remarks", "field_type": "text", "section": "form", "order": 9}
            ],
            "list_display_fields": ["employee_name", "date", "check_in", "check_out", "status", "working_hours"]
        }
    
    elif module == 'hrms' and entity == 'leaves':
        return {
            "module": "hrms",
            "entity": "leaves",
            "entity_label": "Leave Applications",
            "fields": [
                {"field_name": "employee_id", "field_label": "Employee", "field_type": "select", "section": "display", "is_required": True, "show_in_list": True, "order": 1},
                {"field_name": "leave_type", "field_label": "Leave Type", "field_type": "select", "section": "display", "is_required": True, "show_in_list": True, "order": 2,
                    "options": [
                        {"value": "casual", "label": "Casual Leave (CL)"},
                        {"value": "sick", "label": "Sick Leave (SL)"},
                        {"value": "earned", "label": "Earned Leave (EL)"},
                        {"value": "compensatory", "label": "Compensatory Off"},
                        {"value": "maternity", "label": "Maternity Leave"},
                        {"value": "paternity", "label": "Paternity Leave"},
                        {"value": "lwp", "label": "Leave Without Pay"}
                    ]
                },
                {"field_name": "from_date", "field_label": "From Date", "field_type": "date", "section": "display", "is_required": True, "show_in_list": True, "order": 3},
                {"field_name": "to_date", "field_label": "To Date", "field_type": "date", "section": "display", "is_required": True, "show_in_list": True, "order": 4},
                {"field_name": "days", "field_label": "No. of Days", "field_type": "number", "section": "display", "show_in_list": True, "is_readonly": True, "order": 5},
                {"field_name": "status", "field_label": "Status", "field_type": "select", "section": "display", "show_in_list": True, "order": 6,
                    "options": [
                        {"value": "pending", "label": "Pending", "color": "yellow"},
                        {"value": "approved", "label": "Approved", "color": "green"},
                        {"value": "rejected", "label": "Rejected", "color": "red"},
                        {"value": "cancelled", "label": "Cancelled", "color": "slate"}
                    ]
                },
                {"field_name": "reason", "field_label": "Reason", "field_type": "textarea", "section": "form", "is_required": True, "order": 7},
                {"field_name": "approved_by", "field_label": "Approved By", "field_type": "select", "section": "form", "order": 8},
                {"field_name": "remarks", "field_label": "Remarks", "field_type": "textarea", "section": "form", "order": 9}
            ],
            "list_display_fields": ["employee_name", "leave_type", "from_date", "to_date", "days", "status"]
        }
    
    # ==================== PROCUREMENT MODULE ====================
    elif module == 'procurement' and entity == 'purchase_orders':
        return {
            "module": "procurement",
            "entity": "purchase_orders",
            "entity_label": "Purchase Orders",
            "fields": [
                {"field_name": "po_number", "field_label": "PO Number", "field_type": "auto", "section": "display", "show_in_list": True, "is_readonly": True, "order": 1},
                {"field_name": "po_date", "field_label": "PO Date", "field_type": "date", "section": "display", "is_required": True, "show_in_list": True, "order": 2},
                {"field_name": "supplier_id", "field_label": "Supplier", "field_type": "select", "section": "display", "is_required": True, "show_in_list": True, "order": 3},
                {"field_name": "delivery_date", "field_label": "Expected Delivery", "field_type": "date", "section": "display", "order": 4},
                {"field_name": "status", "field_label": "Status", "field_type": "select", "section": "display", "show_in_list": True, "order": 5,
                    "options": [
                        {"value": "draft", "label": "Draft", "color": "slate"},
                        {"value": "sent", "label": "Sent to Supplier", "color": "blue"},
                        {"value": "confirmed", "label": "Confirmed", "color": "green"},
                        {"value": "partial", "label": "Partially Received", "color": "yellow"},
                        {"value": "received", "label": "Fully Received", "color": "emerald"},
                        {"value": "cancelled", "label": "Cancelled", "color": "red"}
                    ]
                },
                {"field_name": "grand_total", "field_label": "Grand Total", "field_type": "currency", "section": "display", "show_in_list": True, "is_readonly": True, "order": 6},
                {"field_name": "payment_terms", "field_label": "Payment Terms", "field_type": "select", "section": "terms", "order": 7,
                    "options": [
                        {"value": "advance", "label": "100% Advance"},
                        {"value": "50_advance", "label": "50% Advance"},
                        {"value": "credit_30", "label": "30 Days Credit"},
                        {"value": "credit_45", "label": "45 Days Credit"},
                        {"value": "credit_60", "label": "60 Days Credit"}
                    ]
                },
                {"field_name": "delivery_terms", "field_label": "Delivery Terms", "field_type": "select", "section": "terms", "order": 8,
                    "options": [
                        {"value": "ex_works", "label": "Ex-Works"},
                        {"value": "for", "label": "FOR Destination"},
                        {"value": "fob", "label": "FOB"}
                    ]
                },
                {"field_name": "shipping_address", "field_label": "Ship To", "field_type": "select", "section": "shipping", "order": 9},
                {"field_name": "notes", "field_label": "Notes", "field_type": "textarea", "section": "form", "order": 10},
                {"field_name": "terms_conditions", "field_label": "Terms & Conditions", "field_type": "textarea", "section": "form", "order": 11}
            ],
            "list_display_fields": ["po_number", "po_date", "supplier_name", "grand_total", "status"],
            "line_item_fields": [
                {"field_name": "item_id", "field_label": "Item", "field_type": "select", "order": 1},
                {"field_name": "description", "field_label": "Description", "field_type": "text", "order": 2},
                {"field_name": "quantity", "field_label": "Qty", "field_type": "number", "order": 3},
                {"field_name": "unit", "field_label": "Unit", "field_type": "select", "order": 4},
                {"field_name": "rate", "field_label": "Rate", "field_type": "currency", "order": 5},
                {"field_name": "tax_percent", "field_label": "Tax %", "field_type": "number", "order": 6},
                {"field_name": "amount", "field_label": "Amount", "field_type": "currency", "is_readonly": True, "order": 7}
            ]
        }
    
    elif module == 'procurement' and entity == 'grn':
        return {
            "module": "procurement",
            "entity": "grn",
            "entity_label": "Goods Receipt Note (GRN)",
            "fields": [
                {"field_name": "grn_number", "field_label": "GRN Number", "field_type": "auto", "section": "display", "show_in_list": True, "is_readonly": True, "order": 1},
                {"field_name": "grn_date", "field_label": "GRN Date", "field_type": "date", "section": "display", "is_required": True, "show_in_list": True, "order": 2},
                {"field_name": "po_id", "field_label": "Purchase Order", "field_type": "select", "section": "display", "show_in_list": True, "order": 3},
                {"field_name": "supplier_id", "field_label": "Supplier", "field_type": "select", "section": "display", "is_required": True, "show_in_list": True, "order": 4},
                {"field_name": "warehouse_id", "field_label": "Receiving Warehouse", "field_type": "select", "section": "display", "is_required": True, "order": 5},
                {"field_name": "challan_no", "field_label": "Delivery Challan No", "field_type": "text", "section": "display", "order": 6},
                {"field_name": "vehicle_no", "field_label": "Vehicle No", "field_type": "text", "section": "transport", "order": 7},
                {"field_name": "transporter", "field_label": "Transporter", "field_type": "text", "section": "transport", "order": 8},
                {"field_name": "lr_no", "field_label": "LR/Bilti No", "field_type": "text", "section": "transport", "order": 9},
                {"field_name": "qc_status", "field_label": "QC Status", "field_type": "select", "section": "quality", "show_in_list": True, "order": 10,
                    "options": [
                        {"value": "pending", "label": "Pending QC"},
                        {"value": "passed", "label": "QC Passed"},
                        {"value": "failed", "label": "QC Failed"},
                        {"value": "partial", "label": "Partial Accept"}
                    ]
                },
                {"field_name": "notes", "field_label": "Notes", "field_type": "textarea", "section": "form", "order": 11}
            ],
            "list_display_fields": ["grn_number", "grn_date", "supplier_name", "po_number", "qc_status"]
        }
    
    # ==================== QUALITY MODULE ====================
    elif module == 'quality' and entity == 'inspections':
        return {
            "module": "quality",
            "entity": "inspections",
            "entity_label": "Quality Inspections",
            "fields": [
                {"field_name": "inspection_no", "field_label": "Inspection No", "field_type": "auto", "section": "display", "show_in_list": True, "is_readonly": True, "order": 1},
                {"field_name": "inspection_date", "field_label": "Date", "field_type": "date", "section": "display", "is_required": True, "show_in_list": True, "order": 2},
                {"field_name": "inspection_type", "field_label": "Type", "field_type": "select", "section": "display", "is_required": True, "show_in_list": True, "order": 3,
                    "options": [
                        {"value": "incoming", "label": "Incoming (Raw Material)"},
                        {"value": "in_process", "label": "In-Process"},
                        {"value": "final", "label": "Final Inspection"},
                        {"value": "customer_complaint", "label": "Customer Complaint"}
                    ]
                },
                {"field_name": "reference_doc", "field_label": "Reference", "field_type": "text", "section": "display", "show_in_list": True, "order": 4, "help_text": "GRN No / WO No / Complaint No"},
                {"field_name": "item_id", "field_label": "Item", "field_type": "select", "section": "display", "is_required": True, "order": 5},
                {"field_name": "batch_no", "field_label": "Batch No", "field_type": "text", "section": "display", "order": 6},
                {"field_name": "quantity_inspected", "field_label": "Qty Inspected", "field_type": "number", "section": "display", "order": 7},
                {"field_name": "quantity_accepted", "field_label": "Qty Accepted", "field_type": "number", "section": "display", "order": 8},
                {"field_name": "quantity_rejected", "field_label": "Qty Rejected", "field_type": "number", "section": "display", "order": 9},
                {"field_name": "result", "field_label": "Result", "field_type": "select", "section": "display", "show_in_list": True, "order": 10,
                    "options": [
                        {"value": "pass", "label": "Pass", "color": "green"},
                        {"value": "fail", "label": "Fail", "color": "red"},
                        {"value": "conditional", "label": "Conditional Accept", "color": "yellow"}
                    ]
                },
                {"field_name": "inspector_id", "field_label": "Inspector", "field_type": "select", "section": "form", "order": 11},
                {"field_name": "remarks", "field_label": "Remarks", "field_type": "textarea", "section": "form", "order": 12}
            ],
            "list_display_fields": ["inspection_no", "inspection_date", "inspection_type", "reference_doc", "result"],
            "parameter_fields": [
                {"field_name": "parameter", "field_label": "Parameter", "field_type": "text", "order": 1},
                {"field_name": "specification", "field_label": "Specification", "field_type": "text", "order": 2},
                {"field_name": "actual", "field_label": "Actual Value", "field_type": "text", "order": 3},
                {"field_name": "result", "field_label": "Result", "field_type": "select", "options": [
                    {"value": "ok", "label": "OK"},
                    {"value": "not_ok", "label": "Not OK"}
                ], "order": 4}
            ]
        }
    
    # ==================== SETTINGS MODULE ====================
    elif module == 'settings' and entity == 'users':
        return {
            "module": "settings",
            "entity": "users",
            "entity_label": "Users",
            "fields": [
                {"field_name": "username", "field_label": "Username", "field_type": "text", "section": "basic", "is_required": True, "show_in_list": True, "order": 1},
                {"field_name": "email", "field_label": "Email", "field_type": "email", "section": "basic", "is_required": True, "show_in_list": True, "order": 2},
                {"field_name": "full_name", "field_label": "Full Name", "field_type": "text", "section": "basic", "is_required": True, "show_in_list": True, "order": 3},
                {"field_name": "phone", "field_label": "Phone", "field_type": "phone", "section": "basic", "order": 4},
                {"field_name": "role", "field_label": "Role", "field_type": "select", "section": "access", "is_required": True, "show_in_list": True, "order": 5,
                    "options": [
                        {"value": "admin", "label": "Admin"},
                        {"value": "director", "label": "Director"},
                        {"value": "manager", "label": "Manager"},
                        {"value": "sales", "label": "Sales Executive"},
                        {"value": "accounts", "label": "Accounts"},
                        {"value": "production", "label": "Production"},
                        {"value": "stores", "label": "Stores"},
                        {"value": "operator", "label": "Operator"}
                    ]
                },
                {"field_name": "department", "field_label": "Department", "field_type": "select", "section": "access", "order": 6,
                    "options": [
                        {"value": "sales", "label": "Sales"},
                        {"value": "production", "label": "Production"},
                        {"value": "accounts", "label": "Accounts"},
                        {"value": "stores", "label": "Stores"},
                        {"value": "hr", "label": "HR"},
                        {"value": "admin", "label": "Admin"}
                    ]
                },
                {"field_name": "warehouse_access", "field_label": "Warehouse Access", "field_type": "multiselect", "section": "access", "order": 7},
                {"field_name": "status", "field_label": "Status", "field_type": "select", "section": "access", "show_in_list": True, "order": 8,
                    "options": [
                        {"value": "active", "label": "Active", "color": "green"},
                        {"value": "inactive", "label": "Inactive", "color": "red"}
                    ]
                },
                {"field_name": "last_login", "field_label": "Last Login", "field_type": "datetime", "section": "display", "is_readonly": True, "order": 9}
            ],
            "list_display_fields": ["username", "full_name", "email", "role", "status"]
        }
    
    elif module == 'settings' and entity == 'company':
        return {
            "module": "settings",
            "entity": "company",
            "entity_label": "Company Settings",
            "fields": [
                {"field_name": "company_name", "field_label": "Company Name", "field_type": "text", "section": "basic", "is_required": True, "order": 1},
                {"field_name": "legal_name", "field_label": "Legal Name", "field_type": "text", "section": "basic", "is_required": True, "order": 2},
                {"field_name": "gstin", "field_label": "GSTIN", "field_type": "text", "section": "basic", "is_required": True, "order": 3},
                {"field_name": "pan", "field_label": "PAN", "field_type": "text", "section": "basic", "order": 4},
                {"field_name": "cin", "field_label": "CIN", "field_type": "text", "section": "basic", "order": 5},
                {"field_name": "address", "field_label": "Address", "field_type": "textarea", "section": "contact", "order": 6},
                {"field_name": "city", "field_label": "City", "field_type": "text", "section": "contact", "order": 7},
                {"field_name": "state", "field_label": "State", "field_type": "text", "section": "contact", "order": 8},
                {"field_name": "pincode", "field_label": "Pincode", "field_type": "text", "section": "contact", "order": 9},
                {"field_name": "phone", "field_label": "Phone", "field_type": "phone", "section": "contact", "order": 10},
                {"field_name": "email", "field_label": "Email", "field_type": "email", "section": "contact", "order": 11},
                {"field_name": "website", "field_label": "Website", "field_type": "text", "section": "contact", "order": 12},
                {"field_name": "bank_name", "field_label": "Bank Name", "field_type": "text", "section": "bank", "order": 13},
                {"field_name": "bank_account", "field_label": "Account No", "field_type": "text", "section": "bank", "order": 14},
                {"field_name": "ifsc_code", "field_label": "IFSC Code", "field_type": "text", "section": "bank", "order": 15},
                {"field_name": "bank_branch", "field_label": "Branch", "field_type": "text", "section": "bank", "order": 16},
                {"field_name": "financial_year_start", "field_label": "FY Start Month", "field_type": "select", "section": "preferences", "order": 17,
                    "options": [
                        {"value": "1", "label": "January"},
                        {"value": "4", "label": "April"}
                    ]
                },
                {"field_name": "currency", "field_label": "Currency", "field_type": "select", "section": "preferences", "default_value": "INR", "order": 18,
                    "options": [
                        {"value": "INR", "label": "INR (₹)"},
                        {"value": "USD", "label": "USD ($)"}
                    ]
                },
                {"field_name": "date_format", "field_label": "Date Format", "field_type": "select", "section": "preferences", "order": 19,
                    "options": [
                        {"value": "DD/MM/YYYY", "label": "DD/MM/YYYY"},
                        {"value": "MM/DD/YYYY", "label": "MM/DD/YYYY"},
                        {"value": "YYYY-MM-DD", "label": "YYYY-MM-DD"}
                    ]
                }
            ],
            "list_display_fields": []
        }
    
    # Default empty config
    return {
        "module": module,
        "entity": entity,
        "entity_label": entity.replace("_", " ").title(),
        "fields": [],
        "list_display_fields": []
    }


# ==================== MASTERS CRUD ====================

@router.post("/masters/{master_type}")
async def save_master_config(master_type: str, config: MasterListConfig, current_user: dict = Depends(get_current_user)):
    """Save master list configuration"""
    if current_user.get('role') not in ['admin', 'director']:
        raise HTTPException(status_code=403, detail="Only admin or director can configure masters")
    
    config_dict = config.model_dump()
    config_dict['updated_at'] = datetime.now(timezone.utc).isoformat()
    config_dict['updated_by'] = current_user['id']
    
    await db.master_configurations.update_one(
        {'master_type': master_type},
        {'$set': config_dict},
        upsert=True
    )
    
    return {"message": "Master configuration saved", "master_type": master_type}


@router.get("/masters/{master_type}/config")
async def get_master_config(master_type: str, current_user: dict = Depends(get_current_user)):
    """Get master configuration"""
    config = await db.master_configurations.find_one(
        {'master_type': master_type},
        {'_id': 0}
    )
    
    if not config:
        return await get_default_master_config(master_type)
    
    return config


async def get_default_master_config(master_type: str):
    """Get default master configuration"""
    
    if master_type == 'customer':
        return {
            "master_type": "customer",
            "master_label": "Customer Master",
            "description": "The Revenue Base",
            "fields": [
                {"field_name": "customer_name", "field_label": "Customer Name", "field_type": "text", "is_required": True, "order": 1},
                {"field_name": "gstin", "field_label": "GSTIN", "field_type": "text", "is_required": True, "order": 2},
                {"field_name": "branch", "field_label": "Branch", "field_type": "select", "order": 3,
                    "options": [
                        {"value": "GJ", "label": "Gujarat"},
                        {"value": "MH", "label": "Maharashtra"},
                        {"value": "DL", "label": "Delhi"}
                    ]
                },
                {"field_name": "buying_dna_rhythm", "field_label": "Buying DNA Rhythm (Days)", "field_type": "number", "order": 4},
                {"field_name": "credit_limit", "field_label": "Credit Limit", "field_type": "currency", "order": 5},
                {"field_name": "distance_from_sarigam", "field_label": "Distance from Sarigam (KM)", "field_type": "number", "order": 6}
            ]
        }
    
    elif master_type == 'supplier':
        return {
            "master_type": "supplier",
            "master_label": "Supplier Master",
            "description": "The Sourcing Base",
            "fields": [
                {"field_name": "supplier_name", "field_label": "Supplier Name", "field_type": "text", "is_required": True, "order": 1},
                {"field_name": "material_category", "field_label": "Material Category", "field_type": "select", "order": 2,
                    "options": [
                        {"value": "film", "label": "Film"},
                        {"value": "adhesive", "label": "Adhesive"},
                        {"value": "core", "label": "Core"}
                    ]
                },
                {"field_name": "lead_time", "field_label": "Lead Time (Days)", "field_type": "number", "order": 3},
                {"field_name": "reliability_score", "field_label": "Reliability Score", "field_type": "number", "order": 4}
            ]
        }
    
    elif master_type == 'item':
        return {
            "master_type": "item",
            "master_label": "Item Master",
            "description": "The Physics Base",
            "fields": [
                {"field_name": "item_name", "field_label": "Item Name", "field_type": "text", "is_required": True, "order": 1},
                {"field_name": "base_category", "field_label": "Base Category", "field_type": "select", "order": 2,
                    "options": [
                        {"value": "bopp", "label": "BOPP"},
                        {"value": "pvc", "label": "PVC"},
                        {"value": "masking", "label": "Masking"},
                        {"value": "double_sided", "label": "Double Sided"},
                        {"value": "cloth", "label": "Cloth"},
                        {"value": "foam", "label": "Foam"}
                    ]
                },
                {"field_name": "uom", "field_label": "UOM", "field_type": "select", "order": 3,
                    "options": [
                        {"value": "KG", "label": "KG"},
                        {"value": "SQM", "label": "SQM"},
                        {"value": "PCS", "label": "PCS"},
                        {"value": "ROL", "label": "Roll"},
                        {"value": "MTR", "label": "Meter"}
                    ]
                },
                {"field_name": "microns", "field_label": "Thickness (Microns)", "field_type": "number", "order": 4},
                {"field_name": "gsm", "field_label": "GSM", "field_type": "number", "order": 5},
                {"field_name": "adhesive_type", "field_label": "Adhesive Type", "field_type": "select", "order": 6,
                    "options": [
                        {"value": "water_based", "label": "Water Based"},
                        {"value": "hotmelt", "label": "Hotmelt"},
                        {"value": "solvent", "label": "Solvent"}
                    ]
                }
            ]
        }
    
    # Return generic config for unknown masters
    return {
        "master_type": master_type,
        "master_label": master_type.replace("_", " ").title(),
        "fields": []
    }


# ==================== FIELD REORDER ====================

@router.put("/config/{module}/{entity}/reorder")
async def reorder_fields(
    module: str,
    entity: str,
    field_orders: List[Dict[str, Any]],  # [{"field_name": "x", "order": 1}, ...]
    current_user: dict = Depends(get_current_user)
):
    """Reorder fields for an entity"""
    if current_user.get('role') not in ['admin', 'director']:
        raise HTTPException(status_code=403, detail="Only admin or director can reorder fields")
    
    config = await db.field_configurations.find_one({'module': module, 'entity': entity})
    
    if not config:
        raise HTTPException(status_code=404, detail="Configuration not found")
    
    # Create order map
    order_map = {item['field_name']: item['order'] for item in field_orders}
    
    # Update field orders
    fields = config.get('fields', [])
    for field in fields:
        if field['field_name'] in order_map:
            field['order'] = order_map[field['field_name']]
    
    # Sort by order
    fields.sort(key=lambda x: x.get('order', 0))
    
    await db.field_configurations.update_one(
        {'module': module, 'entity': entity},
        {'$set': {'fields': fields, 'updated_at': datetime.now(timezone.utc).isoformat()}}
    )
    
    return {"message": "Fields reordered successfully"}


@router.put("/stages/{module}/{entity}/reorder")
async def reorder_stages(
    module: str,
    entity: str,
    stage_orders: List[Dict[str, Any]],  # [{"value": "x", "order": 1}, ...]
    current_user: dict = Depends(get_current_user)
):
    """Reorder Kanban stages"""
    if current_user.get('role') not in ['admin', 'director']:
        raise HTTPException(status_code=403, detail="Only admin or director can reorder stages")
    
    config = await db.field_configurations.find_one({'module': module, 'entity': entity})
    
    if not config:
        raise HTTPException(status_code=404, detail="Configuration not found")
    
    # Create order map
    order_map = {item['value']: item['order'] for item in stage_orders}
    
    # Update stage orders
    stages = config.get('kanban_stages', [])
    for stage in stages:
        if stage['value'] in order_map:
            stage['order'] = order_map[stage['value']]
    
    # Sort by order
    stages.sort(key=lambda x: x.get('order', 0))
    
    await db.field_configurations.update_one(
        {'module': module, 'entity': entity},
        {'$set': {'kanban_stages': stages, 'updated_at': datetime.now(timezone.utc).isoformat()}}
    )
    
    return {"message": "Stages reordered successfully"}
