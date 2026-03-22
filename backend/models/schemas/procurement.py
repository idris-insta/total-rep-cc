"""
Procurement Schemas - Pydantic models for Procurement module
"""
from pydantic import BaseModel
from typing import Optional, List


# ==================== SUPPLIER SCHEMAS ====================
class SupplierBase(BaseModel):
    supplier_code: Optional[str] = None
    supplier_name: Optional[str] = None
    supplier_type: Optional[str] = "Raw Material"
    contact_person: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    mobile: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    pincode: Optional[str] = None
    country: str = "India"
    gstin: Optional[str] = None
    pan: Optional[str] = None
    payment_terms: Optional[str] = "30 days"
    credit_limit: Optional[float] = 0
    bank_name: Optional[str] = None
    bank_account: Optional[str] = None
    ifsc_code: Optional[str] = None
    notes: Optional[str] = None


class SupplierCreate(SupplierBase):
    supplier_name: str
    contact_person: str
    email: str
    phone: str
    address: str


class SupplierUpdate(SupplierBase):
    status: Optional[str] = None


class SupplierResponse(SupplierBase):
    id: str
    status: str = "active"
    created_at: Optional[str] = None


# ==================== PURCHASE ORDER SCHEMAS ====================
class POItemCreate(BaseModel):
    item_id: str
    item_name: Optional[str] = None
    description: Optional[str] = None
    quantity: float
    unit: str = "Pcs"
    unit_price: float
    tax_percent: float = 18


class PurchaseOrderCreate(BaseModel):
    supplier_id: str
    items: List[POItemCreate]
    expected_date: Optional[str] = None
    delivery_address: Optional[str] = None
    notes: Optional[str] = None


class PurchaseOrderUpdate(BaseModel):
    expected_date: Optional[str] = None
    delivery_address: Optional[str] = None
    notes: Optional[str] = None
    status: Optional[str] = None


class PurchaseOrderResponse(BaseModel):
    id: str
    po_number: str
    supplier_id: str
    supplier_name: Optional[str] = None
    items: List[dict]
    subtotal: float
    total_tax: float
    grand_total: float
    status: str
    created_at: Optional[str] = None


# ==================== GRN SCHEMAS ====================
class GRNItemCreate(BaseModel):
    item_id: str
    item_name: Optional[str] = None
    ordered_qty: float
    received_qty: float
    unit: str = "Pcs"
    rejected_qty: float = 0
    rejection_reason: Optional[str] = None


class GRNCreate(BaseModel):
    po_id: str
    warehouse_id: str
    items: List[GRNItemCreate]
    received_date: Optional[str] = None
    challan_no: Optional[str] = None
    notes: Optional[str] = None


class GRNResponse(BaseModel):
    id: str
    grn_number: str
    po_id: str
    po_number: Optional[str] = None
    supplier_id: Optional[str] = None
    supplier_name: Optional[str] = None
    warehouse_id: str
    items: List[dict]
    received_date: str
    status: str
    created_at: Optional[str] = None


# ==================== PURCHASE REQUISITION SCHEMAS ====================
class PRItemCreate(BaseModel):
    item_id: str
    item_name: Optional[str] = None
    quantity: float
    unit: str = "Pcs"
    required_date: Optional[str] = None
    notes: Optional[str] = None


class PurchaseRequisitionCreate(BaseModel):
    department: Optional[str] = None
    items: List[PRItemCreate]
    required_date: Optional[str] = None
    priority: str = "normal"  # low, normal, high, urgent
    notes: Optional[str] = None


class PurchaseRequisitionResponse(BaseModel):
    id: str
    pr_number: str
    department: Optional[str] = None
    items: List[dict]
    status: str
    requested_by: Optional[str] = None
    approved_by: Optional[str] = None
    approved_at: Optional[str] = None
    created_at: Optional[str] = None
