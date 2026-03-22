from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
import uuid
from server import db, get_current_user

router = APIRouter()

# ==================== PERMISSION MODELS ====================
class ModulePermission(BaseModel):
    module: str
    can_view: bool = False
    can_create: bool = False
    can_edit: bool = False
    can_delete: bool = False
    can_export: bool = False
    can_approve: bool = False
    view_all_data: bool = False  # If False, user sees only their assigned data
    custom_filters: Optional[Dict[str, Any]] = None  # Additional data filters

class RolePermissions(BaseModel):
    id: str
    role_name: str
    description: Optional[str] = None
    is_system_role: bool = False
    permissions: List[ModulePermission]
    created_at: str
    updated_at: Optional[str] = None

class RoleCreate(BaseModel):
    role_name: str
    description: Optional[str] = None
    permissions: List[ModulePermission]

class RoleUpdate(BaseModel):
    role_name: Optional[str] = None
    description: Optional[str] = None
    permissions: Optional[List[ModulePermission]] = None

class UserPermissionOverride(BaseModel):
    user_id: str
    module: str
    permission_overrides: Dict[str, bool]  # e.g., {"view_all_data": True}

class UserAccessConfig(BaseModel):
    id: str
    user_id: str
    role_id: str
    custom_permissions: Optional[List[ModulePermission]] = None  # Override role permissions
    assigned_locations: List[str] = []  # Can view data from these locations
    assigned_teams: List[str] = []  # Can view data from team members
    data_access_level: str = "own"  # own, team, location, all
    created_at: str
    updated_at: Optional[str] = None

# ==================== DEFAULT ROLES ====================
DEFAULT_MODULES = [
    "crm_leads", "crm_accounts", "crm_quotations", "crm_samples",
    "inventory_items", "inventory_stock", "inventory_transfers",
    "production_work_orders", "production_bom", "production_schedule",
    "procurement_suppliers", "procurement_po", "procurement_grn",
    "accounts_invoices", "accounts_payments", "accounts_reports",
    "hrms_employees", "hrms_attendance", "hrms_payroll",
    "quality_inspections", "quality_complaints",
    "settings", "master_data", "user_management", "reports"
]

DEFAULT_ROLES = {
    "admin": {
        "description": "Full system access with all permissions",
        "is_system_role": True,
        "permissions": [
            {
                "module": module,
                "can_view": True,
                "can_create": True,
                "can_edit": True,
                "can_delete": True,
                "can_export": True,
                "can_approve": True,
                "view_all_data": True
            } for module in DEFAULT_MODULES
        ]
    },
    "manager": {
        "description": "Department manager with team data access",
        "is_system_role": True,
        "permissions": [
            {
                "module": module,
                "can_view": True,
                "can_create": True,
                "can_edit": True,
                "can_delete": module not in ["user_management", "settings"],
                "can_export": True,
                "can_approve": True,
                "view_all_data": module not in ["user_management", "settings"]  # Managers see team data
            } for module in DEFAULT_MODULES
        ]
    },
    "salesperson": {
        "description": "Sales team member with own data access",
        "is_system_role": True,
        "permissions": [
            {
                "module": "crm_leads",
                "can_view": True, "can_create": True, "can_edit": True, "can_delete": False,
                "can_export": True, "can_approve": False, "view_all_data": False
            },
            {
                "module": "crm_accounts",
                "can_view": True, "can_create": True, "can_edit": True, "can_delete": False,
                "can_export": True, "can_approve": False, "view_all_data": False
            },
            {
                "module": "crm_quotations",
                "can_view": True, "can_create": True, "can_edit": True, "can_delete": False,
                "can_export": True, "can_approve": False, "view_all_data": False
            },
            {
                "module": "crm_samples",
                "can_view": True, "can_create": True, "can_edit": True, "can_delete": False,
                "can_export": True, "can_approve": False, "view_all_data": False
            },
            {
                "module": "inventory_items",
                "can_view": True, "can_create": False, "can_edit": False, "can_delete": False,
                "can_export": True, "can_approve": False, "view_all_data": True
            },
            {
                "module": "inventory_stock",
                "can_view": True, "can_create": False, "can_edit": False, "can_delete": False,
                "can_export": True, "can_approve": False, "view_all_data": True
            },
            {
                "module": "reports",
                "can_view": True, "can_create": False, "can_edit": False, "can_delete": False,
                "can_export": True, "can_approve": False, "view_all_data": False
            }
        ]
    },
    "viewer": {
        "description": "Read-only access to assigned data",
        "is_system_role": True,
        "permissions": [
            {
                "module": module,
                "can_view": True,
                "can_create": False,
                "can_edit": False,
                "can_delete": False,
                "can_export": module in ["reports"],
                "can_approve": False,
                "view_all_data": False
            } for module in ["crm_leads", "crm_accounts", "crm_quotations", "crm_samples", 
                            "inventory_items", "inventory_stock", "reports"]
        ]
    },
    "accountant": {
        "description": "Accounts and finance access",
        "is_system_role": True,
        "permissions": [
            {
                "module": "accounts_invoices",
                "can_view": True, "can_create": True, "can_edit": True, "can_delete": False,
                "can_export": True, "can_approve": True, "view_all_data": True
            },
            {
                "module": "accounts_payments",
                "can_view": True, "can_create": True, "can_edit": True, "can_delete": False,
                "can_export": True, "can_approve": True, "view_all_data": True
            },
            {
                "module": "accounts_reports",
                "can_view": True, "can_create": False, "can_edit": False, "can_delete": False,
                "can_export": True, "can_approve": False, "view_all_data": True
            },
            {
                "module": "crm_accounts",
                "can_view": True, "can_create": False, "can_edit": False, "can_delete": False,
                "can_export": True, "can_approve": False, "view_all_data": True
            },
            {
                "module": "crm_quotations",
                "can_view": True, "can_create": False, "can_edit": False, "can_delete": False,
                "can_export": True, "can_approve": False, "view_all_data": True
            },
            {
                "module": "reports",
                "can_view": True, "can_create": False, "can_edit": False, "can_delete": False,
                "can_export": True, "can_approve": False, "view_all_data": True
            }
        ]
    }
}

# ==================== ROLE ENDPOINTS ====================
@router.get("/roles")
async def get_all_roles(current_user: dict = Depends(get_current_user)):
    """Get all defined roles"""
    roles = await db.roles.find({}, {"_id": 0}).to_list(100)
    
    # If no custom roles, return defaults
    if not roles:
        return [
            {
                "id": role_name,
                "role_name": role_name,
                **role_data
            } for role_name, role_data in DEFAULT_ROLES.items()
        ]
    
    return roles

@router.get("/roles/{role_name}")
async def get_role(role_name: str, current_user: dict = Depends(get_current_user)):
    """Get a specific role with its permissions"""
    role = await db.roles.find_one({"role_name": role_name}, {"_id": 0})
    
    if not role and role_name in DEFAULT_ROLES:
        return {
            "id": role_name,
            "role_name": role_name,
            **DEFAULT_ROLES[role_name]
        }
    
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    
    return role

@router.post("/roles", response_model=RolePermissions)
async def create_role(role_data: RoleCreate, current_user: dict = Depends(get_current_user)):
    """Create a new role"""
    if current_user.get('role') != 'admin':
        raise HTTPException(status_code=403, detail="Only admins can create roles")
    
    # Check if role exists
    existing = await db.roles.find_one({"role_name": role_data.role_name})
    if existing or role_data.role_name in DEFAULT_ROLES:
        raise HTTPException(status_code=400, detail="Role already exists")
    
    role_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    
    role_doc = {
        "id": role_id,
        "role_name": role_data.role_name,
        "description": role_data.description,
        "is_system_role": False,
        "permissions": [p.model_dump() for p in role_data.permissions],
        "created_at": now,
        "updated_at": now
    }
    
    await db.roles.insert_one(role_doc)
    return RolePermissions(**{k: v for k, v in role_doc.items() if k != '_id'})

@router.put("/roles/{role_name}", response_model=RolePermissions)
async def update_role(role_name: str, role_data: RoleUpdate, current_user: dict = Depends(get_current_user)):
    """Update a role's permissions"""
    if current_user.get('role') != 'admin':
        raise HTTPException(status_code=403, detail="Only admins can update roles")
    
    # Check if it's a system role
    existing = await db.roles.find_one({"role_name": role_name})
    if existing and existing.get("is_system_role"):
        raise HTTPException(status_code=400, detail="Cannot modify system roles. Create a custom role instead.")
    
    # If role doesn't exist in DB but is a default, create it first
    if not existing and role_name in DEFAULT_ROLES:
        role_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        existing = {
            "id": role_id,
            "role_name": role_name,
            **DEFAULT_ROLES[role_name],
            "created_at": now,
            "updated_at": now
        }
        await db.roles.insert_one(existing)
    
    if not existing:
        raise HTTPException(status_code=404, detail="Role not found")
    
    update_dict = {k: v for k, v in role_data.model_dump().items() if v is not None}
    if "permissions" in update_dict:
        update_dict["permissions"] = [p.model_dump() if hasattr(p, 'model_dump') else p for p in update_dict["permissions"]]
    update_dict["updated_at"] = datetime.now(timezone.utc).isoformat()
    
    await db.roles.update_one({"role_name": role_name}, {"$set": update_dict})
    
    role = await db.roles.find_one({"role_name": role_name}, {"_id": 0})
    return RolePermissions(**role)

@router.delete("/roles/{role_name}")
async def delete_role(role_name: str, current_user: dict = Depends(get_current_user)):
    """Delete a custom role"""
    if current_user.get('role') != 'admin':
        raise HTTPException(status_code=403, detail="Only admins can delete roles")
    
    if role_name in DEFAULT_ROLES:
        raise HTTPException(status_code=400, detail="Cannot delete system roles")
    
    result = await db.roles.delete_one({"role_name": role_name})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Role not found")
    
    return {"message": "Role deleted"}

# ==================== USER ACCESS ENDPOINTS ====================
@router.get("/users/{user_id}/access")
async def get_user_access(user_id: str, current_user: dict = Depends(get_current_user)):
    """Get a user's access configuration"""
    if current_user.get('role') != 'admin' and current_user.get('id') != user_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Get user's custom access config
    access = await db.user_access.find_one({"user_id": user_id}, {"_id": 0})
    
    # Get user's role
    user = await db.users.find_one({"id": user_id}, {"_id": 0, "role": 1, "email": 1, "name": 1})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    role_name = user.get("role", "viewer")
    
    # Get role permissions
    role = await db.roles.find_one({"role_name": role_name}, {"_id": 0})
    if not role and role_name in DEFAULT_ROLES:
        role = {"role_name": role_name, **DEFAULT_ROLES[role_name]}
    
    return {
        "user_id": user_id,
        "user_email": user.get("email"),
        "user_name": user.get("name"),
        "role": role_name,
        "role_permissions": role.get("permissions", []) if role else [],
        "custom_access": access,
        "effective_data_access": access.get("data_access_level", "own") if access else ("all" if role_name == "admin" else "own")
    }

@router.put("/users/{user_id}/access")
async def update_user_access(user_id: str, access_level: str, assigned_locations: List[str] = [], assigned_teams: List[str] = [], current_user: dict = Depends(get_current_user)):
    """Update a user's data access level"""
    if current_user.get('role') != 'admin':
        raise HTTPException(status_code=403, detail="Only admins can update user access")
    
    valid_levels = ["own", "team", "location", "all"]
    if access_level not in valid_levels:
        raise HTTPException(status_code=400, detail=f"Invalid access level. Must be one of: {valid_levels}")
    
    now = datetime.now(timezone.utc).isoformat()
    
    # Get user's role
    user = await db.users.find_one({"id": user_id}, {"_id": 0, "role": 1})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    access_doc = {
        "user_id": user_id,
        "role_id": user.get("role", "viewer"),
        "data_access_level": access_level,
        "assigned_locations": assigned_locations,
        "assigned_teams": assigned_teams,
        "updated_at": now
    }
    
    existing = await db.user_access.find_one({"user_id": user_id})
    if existing:
        await db.user_access.update_one({"user_id": user_id}, {"$set": access_doc})
    else:
        access_doc["id"] = str(uuid.uuid4())
        access_doc["created_at"] = now
        access_doc["custom_permissions"] = None
        await db.user_access.insert_one(access_doc)
    
    return {"message": "User access updated", "data_access_level": access_level}

@router.put("/users/{user_id}/permissions")
async def update_user_permissions(user_id: str, permissions: List[ModulePermission], current_user: dict = Depends(get_current_user)):
    """Set custom permission overrides for a user"""
    if current_user.get('role') != 'admin':
        raise HTTPException(status_code=403, detail="Only admins can update user permissions")
    
    now = datetime.now(timezone.utc).isoformat()
    
    access = await db.user_access.find_one({"user_id": user_id})
    
    if access:
        await db.user_access.update_one(
            {"user_id": user_id},
            {"$set": {
                "custom_permissions": [p.model_dump() for p in permissions],
                "updated_at": now
            }}
        )
    else:
        # Get user's role first
        user = await db.users.find_one({"id": user_id}, {"_id": 0, "role": 1})
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        access_doc = {
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "role_id": user.get("role", "viewer"),
            "custom_permissions": [p.model_dump() for p in permissions],
            "data_access_level": "own",
            "assigned_locations": [],
            "assigned_teams": [],
            "created_at": now,
            "updated_at": now
        }
        await db.user_access.insert_one(access_doc)
    
    return {"message": "User permissions updated"}

# ==================== PERMISSION CHECK HELPER ====================
@router.get("/check/{module}/{action}")
async def check_permission(module: str, action: str, current_user: dict = Depends(get_current_user)):
    """Check if current user has permission for an action on a module"""
    user_id = current_user.get('id')
    role_name = current_user.get('role', 'viewer')
    
    # Admin always has access
    if role_name == 'admin':
        return {"allowed": True, "view_all_data": True}
    
    # Get user's custom access config
    access = await db.user_access.find_one({"user_id": user_id}, {"_id": 0})
    
    # Check custom permissions first
    if access and access.get("custom_permissions"):
        for perm in access["custom_permissions"]:
            if perm.get("module") == module:
                action_map = {
                    "view": "can_view",
                    "create": "can_create",
                    "edit": "can_edit",
                    "delete": "can_delete",
                    "export": "can_export",
                    "approve": "can_approve"
                }
                permission_key = action_map.get(action, f"can_{action}")
                return {
                    "allowed": perm.get(permission_key, False),
                    "view_all_data": perm.get("view_all_data", False)
                }
    
    # Fall back to role permissions
    role = await db.roles.find_one({"role_name": role_name}, {"_id": 0})
    if not role and role_name in DEFAULT_ROLES:
        role = DEFAULT_ROLES[role_name]
    
    if role and role.get("permissions"):
        for perm in role["permissions"]:
            if perm.get("module") == module:
                action_map = {
                    "view": "can_view",
                    "create": "can_create",
                    "edit": "can_edit",
                    "delete": "can_delete",
                    "export": "can_export",
                    "approve": "can_approve"
                }
                permission_key = action_map.get(action, f"can_{action}")
                return {
                    "allowed": perm.get(permission_key, False),
                    "view_all_data": perm.get("view_all_data", False)
                }
    
    return {"allowed": False, "view_all_data": False}

@router.get("/modules")
async def get_all_modules(current_user: dict = Depends(get_current_user)):
    """Get list of all modules for permission configuration"""
    module_info = {
        "crm_leads": {"name": "CRM - Leads", "category": "CRM"},
        "crm_accounts": {"name": "CRM - Accounts", "category": "CRM"},
        "crm_quotations": {"name": "CRM - Quotations", "category": "CRM"},
        "crm_samples": {"name": "CRM - Samples", "category": "CRM"},
        "inventory_items": {"name": "Inventory - Items", "category": "Inventory"},
        "inventory_stock": {"name": "Inventory - Stock", "category": "Inventory"},
        "inventory_transfers": {"name": "Inventory - Transfers", "category": "Inventory"},
        "production_work_orders": {"name": "Production - Work Orders", "category": "Production"},
        "production_bom": {"name": "Production - BOM", "category": "Production"},
        "production_schedule": {"name": "Production - Schedule", "category": "Production"},
        "procurement_suppliers": {"name": "Procurement - Suppliers", "category": "Procurement"},
        "procurement_po": {"name": "Procurement - Purchase Orders", "category": "Procurement"},
        "procurement_grn": {"name": "Procurement - GRN", "category": "Procurement"},
        "accounts_invoices": {"name": "Accounts - Invoices", "category": "Accounts"},
        "accounts_payments": {"name": "Accounts - Payments", "category": "Accounts"},
        "accounts_reports": {"name": "Accounts - Reports", "category": "Accounts"},
        "hrms_employees": {"name": "HRMS - Employees", "category": "HRMS"},
        "hrms_attendance": {"name": "HRMS - Attendance", "category": "HRMS"},
        "hrms_payroll": {"name": "HRMS - Payroll", "category": "HRMS"},
        "quality_inspections": {"name": "Quality - Inspections", "category": "Quality"},
        "quality_complaints": {"name": "Quality - Complaints", "category": "Quality"},
        "settings": {"name": "Settings", "category": "System"},
        "master_data": {"name": "Master Data", "category": "System"},
        "user_management": {"name": "User Management", "category": "System"},
        "reports": {"name": "Reports", "category": "System"}
    }
    return module_info

# ==================== INITIALIZE DEFAULTS ====================
@router.post("/initialize")
async def initialize_permissions(current_user: dict = Depends(get_current_user)):
    """Initialize default roles and permissions"""
    if current_user.get('role') != 'admin':
        raise HTTPException(status_code=403, detail="Only admins can initialize permissions")
    
    now = datetime.now(timezone.utc).isoformat()
    inserted_count = 0
    
    for role_name, role_data in DEFAULT_ROLES.items():
        existing = await db.roles.find_one({"role_name": role_name})
        if existing:
            continue
        
        role_doc = {
            "id": str(uuid.uuid4()),
            "role_name": role_name,
            **role_data,
            "created_at": now,
            "updated_at": now
        }
        await db.roles.insert_one(role_doc)
        inserted_count += 1
    
    return {"message": f"Initialized {inserted_count} roles with permissions"}
