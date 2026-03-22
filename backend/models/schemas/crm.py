"""
CRM Schemas - Pydantic models for CRM module
"""
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


# ==================== ENUMS ====================
class LeadStatus(str, Enum):
    NEW = "new"
    HOT_LEADS = "hot_leads"
    COLD_LEADS = "cold_leads"
    CONTACTED = "contacted"
    QUALIFIED = "qualified"
    PROPOSAL = "proposal"
    NEGOTIATION = "negotiation"
    CONVERTED = "converted"
    CUSTOMER = "customer"
    LOST = "lost"


class AccountType(str, Enum):
    CUSTOMER = "customer"
    SUPPLIER = "supplier"
    BOTH = "both"


class QuotationStatus(str, Enum):
    DRAFT = "draft"
    SENT = "sent"
    VIEWED = "viewed"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    EXPIRED = "expired"


class SampleStatus(str, Enum):
    PENDING = "pending"
    DISPATCHED = "dispatched"
    DELIVERED = "delivered"
    FEEDBACK_PENDING = "feedback_pending"
    APPROVED = "approved"
    REJECTED = "rejected"


# ==================== LEAD SCHEMAS ====================
class LeadBase(BaseModel):
    company_name: Optional[str] = None
    contact_person: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    source: Optional[str] = None
    status: Optional[str] = "new"
    assigned_to: Optional[str] = None
    estimated_value: Optional[float] = None
    notes: Optional[str] = None
    # Address
    address: Optional[str] = None
    country: Optional[str] = "India"
    state: Optional[str] = None
    city: Optional[str] = None
    pincode: Optional[str] = None
    # Classification
    industry: Optional[str] = None
    customer_type: Optional[str] = None
    products_of_interest: Optional[List[str]] = None
    # Follow-up
    next_follow_up: Optional[str] = None
    follow_up_activity: Optional[str] = None


class LeadCreate(LeadBase):
    company_name: str


class LeadUpdate(LeadBase):
    pass


class LeadResponse(LeadBase):
    id: str
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    created_by: Optional[str] = None


# ==================== ACCOUNT SCHEMAS ====================
class AccountBase(BaseModel):
    customer_name: Optional[str] = None
    account_type: Optional[str] = "customer"
    gstin: Optional[str] = None
    pan: Optional[str] = None
    industry: Optional[str] = None
    website: Optional[str] = None
    aadhar_no: Optional[str] = None
    opening_balance: Optional[float] = 0
    bank_details: Optional[str] = None
    notes: Optional[str] = None
    # Billing Address
    billing_address: Optional[str] = None
    billing_city: Optional[str] = None
    billing_state: Optional[str] = None
    billing_pincode: Optional[str] = None
    billing_country: Optional[str] = "India"
    # Credit Terms
    credit_limit: Optional[float] = 0
    credit_days: Optional[int] = 30
    payment_terms: Optional[str] = None
    credit_control: Optional[str] = "warning"


class AccountCreate(AccountBase):
    customer_name: str


class AccountUpdate(AccountBase):
    pass


class AccountResponse(AccountBase):
    id: str
    receivable_amount: Optional[float] = 0
    payable_amount: Optional[float] = 0
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


# ==================== QUOTATION SCHEMAS ====================
class QuotationLineItem(BaseModel):
    item_id: Optional[str] = None
    item_name: Optional[str] = None
    description: Optional[str] = None
    hsn_code: Optional[str] = None
    quantity: float = 1
    unit: str = "Pcs"
    unit_price: float = 0
    discount_percent: float = 0
    tax_percent: float = 18
    amount: Optional[float] = None


class QuotationBase(BaseModel):
    account_id: Optional[str] = None
    contact_person: Optional[str] = None
    reference: Optional[str] = None
    valid_until: Optional[str] = None
    transport: Optional[str] = None
    delivery_terms: Optional[str] = None
    payment_terms: Optional[str] = None
    validity_days: Optional[int] = 30
    header_discount_percent: Optional[float] = 0
    notes: Optional[str] = None
    terms_conditions: Optional[str] = None
    items: Optional[List[QuotationLineItem]] = []


class QuotationCreate(QuotationBase):
    account_id: str


class QuotationUpdate(QuotationBase):
    status: Optional[str] = None


class QuotationResponse(QuotationBase):
    id: str
    quote_number: Optional[str] = None
    status: str = "draft"
    subtotal: Optional[float] = 0
    tax_amount: Optional[float] = 0
    discount_amount: Optional[float] = 0
    grand_total: Optional[float] = 0
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


# ==================== SAMPLE SCHEMAS ====================
class SampleItem(BaseModel):
    product_name: Optional[str] = None
    product_specs: Optional[str] = None
    quantity: int = 1
    unit: str = "Pcs"


class SampleBase(BaseModel):
    account_id: Optional[str] = None
    contact_person: Optional[str] = None
    purpose: Optional[str] = None
    quotation_id: Optional[str] = None
    from_location: Optional[str] = None
    courier: Optional[str] = None
    tracking_number: Optional[str] = None
    expected_delivery: Optional[str] = None
    feedback_due_date: Optional[str] = None
    notes: Optional[str] = None
    items: Optional[List[SampleItem]] = []


class SampleCreate(SampleBase):
    account_id: str


class SampleUpdate(SampleBase):
    status: Optional[str] = None
    feedback: Optional[str] = None


class SampleResponse(SampleBase):
    id: str
    sample_number: Optional[str] = None
    status: str = "pending"
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
