"""
Settings Schemas - Pydantic models for Settings module
"""
from pydantic import BaseModel
from typing import Optional, List, Any, Dict


# ==================== FIELD CONFIGURATION SCHEMAS ====================
class FieldConfig(BaseModel):
    field_name: str
    field_type: str  # text, number, date, select, multiselect, etc.
    label: str
    required: bool = False
    visible: bool = True
    editable: bool = True
    default_value: Optional[Any] = None
    options: Optional[List[str]] = None
    validation: Optional[Dict[str, Any]] = None
    order: int = 0


class FieldConfigurationCreate(BaseModel):
    module: str
    entity: str
    sections: Optional[Dict[str, List[FieldConfig]]] = None
    kanban_stages: Optional[List[Dict[str, Any]]] = None


class FieldConfigurationResponse(BaseModel):
    id: str
    module: str
    entity: str
    sections: Optional[Dict[str, Any]] = None
    kanban_stages: Optional[List[Dict[str, Any]]] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


# ==================== SYSTEM SETTING SCHEMAS ====================
class SystemSettingCreate(BaseModel):
    key: str
    value: Any
    category: str = "general"


class SystemSettingResponse(BaseModel):
    id: str
    key: str
    value: Any
    category: str
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


# ==================== COMPANY PROFILE SCHEMAS ====================
class CompanyProfileCreate(BaseModel):
    company_name: str
    legal_name: Optional[str] = None
    gstin: Optional[str] = None
    pan: Optional[str] = None
    cin: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    pincode: Optional[str] = None
    country: str = "India"
    phone: Optional[str] = None
    email: Optional[str] = None
    website: Optional[str] = None
    logo_url: Optional[str] = None
    bank_name: Optional[str] = None
    bank_account: Optional[str] = None
    bank_ifsc: Optional[str] = None


class CompanyProfileUpdate(CompanyProfileCreate):
    company_name: Optional[str] = None


class CompanyProfileResponse(CompanyProfileCreate):
    id: str
    is_active: bool
    created_at: Optional[str] = None


# ==================== BRANCH SCHEMAS ====================
class BranchCreate(BaseModel):
    branch_name: str
    branch_code: Optional[str] = None
    gstin: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    pincode: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    is_head_office: bool = False


class BranchUpdate(BranchCreate):
    branch_name: Optional[str] = None
    is_active: Optional[bool] = None


class BranchResponse(BranchCreate):
    id: str
    is_active: bool
    created_at: Optional[str] = None


# ==================== USER SCHEMAS ====================
class UserCreate(BaseModel):
    name: str
    email: str
    password: str
    role: str  # admin, manager, user, viewer
    department: Optional[str] = None
    phone: Optional[str] = None
    branch_id: Optional[str] = None


class UserUpdate(BaseModel):
    name: Optional[str] = None
    role: Optional[str] = None
    department: Optional[str] = None
    phone: Optional[str] = None
    branch_id: Optional[str] = None
    password: Optional[str] = None
    is_active: Optional[bool] = None


class UserResponse(BaseModel):
    id: str
    name: str
    email: str
    role: str
    department: Optional[str] = None
    phone: Optional[str] = None
    branch_id: Optional[str] = None
    is_active: bool
    created_at: Optional[str] = None
