"""
Centralized Pydantic Models for AdhesiveFlow ERP
All data models are defined here and imported into route files
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime


# ==================== CRM MODELS ====================
class LeadCreate(BaseModel):
    company_name: str
    contact_person: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    mobile: Optional[str] = None
    address: Optional[str] = None
    country: str = "India"
    state: Optional[str] = None
    district: Optional[str] = None
    city: Optional[str] = None
    pincode: Optional[str] = None
    customer_type: Optional[str] = None
    pipeline: str = "main"
    assigned_to: Optional[str] = None
    source: Optional[str] = None
    industry: Optional[str] = None
    product_interest: Optional[str] = None
    estimated_value: Optional[float] = None
    notes: Optional[str] = None
    next_followup_date: Optional[str] = None
    followup_activity: Optional[str] = None
    custom_fields: Optional[Dict[str, Any]] = None


class LeadUpdate(BaseModel):
    company_name: Optional[str] = None
    contact_person: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    mobile: Optional[str] = None
    address: Optional[str] = None
    country: Optional[str] = None
    state: Optional[str] = None
    district: Optional[str] = None
    city: Optional[str] = None
    pincode: Optional[str] = None
    customer_type: Optional[str] = None
    status: Optional[str] = None
    pipeline: Optional[str] = None
    assigned_to: Optional[str] = None
    source: Optional[str] = None
    industry: Optional[str] = None
    product_interest: Optional[str] = None
    estimated_value: Optional[float] = None
    notes: Optional[str] = None
    next_followup_date: Optional[str] = None
    followup_activity: Optional[str] = None
    custom_fields: Optional[Dict[str, Any]] = None


class ContactPerson(BaseModel):
    name: str
    designation: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    mobile: Optional[str] = None
    is_primary: bool = False


class ShippingAddress(BaseModel):
    address_label: str
    address_line1: str
    address_line2: Optional[str] = None
    city: str
    state: str
    pincode: str
    country: str = "India"


class AccountCreate(BaseModel):
    account_name: str
    account_type: str = "Customer"
    contact_person: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    mobile: Optional[str] = None
    address_line1: Optional[str] = None
    address_line2: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    pincode: Optional[str] = None
    country: str = "India"
    gstin: Optional[str] = None
    pan: Optional[str] = None
    credit_limit: float = 0
    payment_terms: int = 30
    is_customer: bool = True
    is_vendor: bool = False
    contact_persons: Optional[List[ContactPerson]] = None
    shipping_addresses: Optional[List[ShippingAddress]] = None
    notes: Optional[str] = None
    custom_fields: Optional[Dict[str, Any]] = None


class AccountUpdate(BaseModel):
    account_name: Optional[str] = None
    account_type: Optional[str] = None
    contact_person: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    mobile: Optional[str] = None
    address_line1: Optional[str] = None
    address_line2: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    pincode: Optional[str] = None
    country: Optional[str] = None
    gstin: Optional[str] = None
    pan: Optional[str] = None
    credit_limit: Optional[float] = None
    payment_terms: Optional[int] = None
    is_customer: Optional[bool] = None
    is_vendor: Optional[bool] = None
    is_active: Optional[bool] = None
    contact_persons: Optional[List[ContactPerson]] = None
    shipping_addresses: Optional[List[ShippingAddress]] = None
    notes: Optional[str] = None
    custom_fields: Optional[Dict[str, Any]] = None


class QuotationItem(BaseModel):
    item_id: str
    item_code: str
    item_name: str
    quantity: float
    uom: str
    rate: float
    discount_percent: float = 0
    gst_rate: float = 18
    amount: float
    hsn_code: Optional[str] = None


class QuotationCreate(BaseModel):
    account_id: str
    account_name: str
    quotation_date: str
    valid_until: str
    items: List[QuotationItem]
    terms_conditions: Optional[str] = None
    notes: Optional[str] = None
    payment_terms: Optional[str] = None
    delivery_terms: Optional[str] = None


class QuotationUpdate(BaseModel):
    valid_until: Optional[str] = None
    items: Optional[List[QuotationItem]] = None
    terms_conditions: Optional[str] = None
    notes: Optional[str] = None
    payment_terms: Optional[str] = None
    delivery_terms: Optional[str] = None
    status: Optional[str] = None


class SampleItem(BaseModel):
    item_id: str
    item_code: str
    item_name: str
    quantity: float
    uom: str


class SampleCreate(BaseModel):
    account_id: str
    account_name: str
    lead_id: Optional[str] = None
    request_date: str
    required_by: Optional[str] = None
    items: List[SampleItem]
    purpose: Optional[str] = None
    notes: Optional[str] = None
    shipping_address: Optional[str] = None
    contact_person: Optional[str] = None
    contact_phone: Optional[str] = None


class SampleUpdate(BaseModel):
    required_by: Optional[str] = None
    items: Optional[List[SampleItem]] = None
    purpose: Optional[str] = None
    notes: Optional[str] = None
    status: Optional[str] = None
    dispatch_date: Optional[str] = None
    courier_name: Optional[str] = None
    tracking_number: Optional[str] = None
    feedback: Optional[str] = None
    feedback_date: Optional[str] = None
    feedback_rating: Optional[int] = None
    outcome: Optional[str] = None


class FollowupCreate(BaseModel):
    lead_id: Optional[str] = None
    account_id: Optional[str] = None
    followup_type: str
    followup_date: str
    notes: Optional[str] = None
    next_followup_date: Optional[str] = None


# ==================== INVENTORY MODELS ====================
class ItemCreate(BaseModel):
    item_code: str
    item_name: str
    category: str
    item_type: Optional[str] = None
    hsn_code: Optional[str] = None
    uom: str = "Rolls"
    secondary_uom: Optional[str] = None
    conversion_factor: float = 1
    thickness: Optional[float] = None
    width: Optional[float] = None
    length: Optional[float] = None
    color: Optional[str] = None
    adhesive_type: Optional[str] = None
    base_material: Optional[str] = None
    grade: Optional[str] = None
    standard_cost: float = 0
    selling_price: float = 0
    min_order_qty: float = 1
    reorder_level: float = 0
    safety_stock: float = 0
    lead_time_days: int = 7
    shelf_life_days: Optional[int] = None
    storage_conditions: Optional[str] = None
    custom_fields: Optional[Dict[str, Any]] = None


class ItemUpdate(BaseModel):
    item_name: Optional[str] = None
    category: Optional[str] = None
    item_type: Optional[str] = None
    hsn_code: Optional[str] = None
    uom: Optional[str] = None
    secondary_uom: Optional[str] = None
    conversion_factor: Optional[float] = None
    thickness: Optional[float] = None
    width: Optional[float] = None
    length: Optional[float] = None
    color: Optional[str] = None
    adhesive_type: Optional[str] = None
    base_material: Optional[str] = None
    grade: Optional[str] = None
    standard_cost: Optional[float] = None
    selling_price: Optional[float] = None
    min_order_qty: Optional[float] = None
    reorder_level: Optional[float] = None
    safety_stock: Optional[float] = None
    lead_time_days: Optional[int] = None
    shelf_life_days: Optional[int] = None
    storage_conditions: Optional[str] = None
    is_active: Optional[bool] = None
    custom_fields: Optional[Dict[str, Any]] = None


# ==================== HRMS MODELS ====================
class EmployeeCreate(BaseModel):
    employee_code: str
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    department: str
    designation: Optional[str] = None
    location: str = "BWD"
    date_of_joining: Optional[str] = None
    shift_timing: str = "General"
    basic_salary: float = 0
    hra: float = 0
    pf: float = 12
    esi: float = 0.75
    pt: float = 200
    custom_fields: Optional[Dict[str, Any]] = None


class EmployeeUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    department: Optional[str] = None
    designation: Optional[str] = None
    location: Optional[str] = None
    shift_timing: Optional[str] = None
    basic_salary: Optional[float] = None
    hra: Optional[float] = None
    pf: Optional[float] = None
    esi: Optional[float] = None
    pt: Optional[float] = None
    is_active: Optional[bool] = None
    custom_fields: Optional[Dict[str, Any]] = None


# ==================== PRODUCTION MODELS ====================
class ProductionOrderCreate(BaseModel):
    order_number: Optional[str] = None
    sales_order_id: Optional[str] = None
    product_id: str
    product_name: str
    quantity: float
    uom: str
    planned_start_date: str
    planned_end_date: str
    priority: str = "normal"
    notes: Optional[str] = None


class ProductionOrderUpdate(BaseModel):
    planned_start_date: Optional[str] = None
    planned_end_date: Optional[str] = None
    actual_start_date: Optional[str] = None
    actual_end_date: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[str] = None
    produced_quantity: Optional[float] = None
    rejected_quantity: Optional[float] = None
    notes: Optional[str] = None


# ==================== PROCUREMENT MODELS ====================
class PurchaseOrderItem(BaseModel):
    item_id: str
    item_code: str
    item_name: str
    quantity: float
    uom: str
    rate: float
    gst_rate: float = 18
    discount_percent: float = 0
    hsn_code: Optional[str] = None


class PurchaseOrderCreate(BaseModel):
    vendor_id: str
    vendor_name: str
    order_date: str
    expected_delivery: Optional[str] = None
    items: List[PurchaseOrderItem]
    payment_terms: Optional[str] = None
    delivery_terms: Optional[str] = None
    notes: Optional[str] = None
    branch: str = "BWD"


class PurchaseOrderUpdate(BaseModel):
    expected_delivery: Optional[str] = None
    items: Optional[List[PurchaseOrderItem]] = None
    payment_terms: Optional[str] = None
    delivery_terms: Optional[str] = None
    notes: Optional[str] = None
    status: Optional[str] = None


# ==================== CUSTOM FIELDS MODELS ====================
class CustomFieldCreate(BaseModel):
    module: str
    field_name: str
    field_label: str
    field_type: str
    options: Optional[List[str]] = None
    default_value: Optional[str] = None
    is_required: bool = False
    is_unique: bool = False
    display_order: int = 0
    section: Optional[str] = None
    placeholder: Optional[str] = None
    help_text: Optional[str] = None
    validation_rules: Optional[Dict[str, Any]] = None


class CustomFieldUpdate(BaseModel):
    field_label: Optional[str] = None
    field_type: Optional[str] = None
    options: Optional[List[str]] = None
    default_value: Optional[str] = None
    is_required: Optional[bool] = None
    is_unique: Optional[bool] = None
    display_order: Optional[int] = None
    section: Optional[str] = None
    placeholder: Optional[str] = None
    help_text: Optional[str] = None
    validation_rules: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None


# ==================== REPORT BUILDER MODELS ====================
class ReportColumnDef(BaseModel):
    field: str
    label: str
    width: Optional[int] = None
    format: Optional[str] = None  # text, number, currency, date, percent
    aggregation: Optional[str] = None  # sum, avg, count, min, max


class ReportFilterDef(BaseModel):
    field: str
    operator: str  # eq, ne, gt, gte, lt, lte, contains, in, between
    value: Any
    value2: Optional[Any] = None  # For between operator


class ReportCreate(BaseModel):
    name: str
    description: Optional[str] = None
    module: str  # crm, inventory, accounts, hrms, production
    columns: List[ReportColumnDef]
    filters: Optional[List[ReportFilterDef]] = None
    group_by: Optional[List[str]] = None
    order_by: Optional[str] = None
    order_direction: str = "asc"
    is_public: bool = False


class ReportUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    columns: Optional[List[ReportColumnDef]] = None
    filters: Optional[List[ReportFilterDef]] = None
    group_by: Optional[List[str]] = None
    order_by: Optional[str] = None
    order_direction: Optional[str] = None
    is_public: Optional[bool] = None
    is_active: Optional[bool] = None
