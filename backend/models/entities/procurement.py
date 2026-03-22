"""
SQLAlchemy Entity Models - Procurement Module
"""
from sqlalchemy import Column, String, DateTime, Boolean, Text, Integer, Float, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime, timezone

from core.database import Base
from models.entities.base import UUIDMixin, TimestampMixin


class Supplier(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "suppliers"
    
    supplier_code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    supplier_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    supplier_type: Mapped[str] = mapped_column(String(50), nullable=True)  # raw_material, consumable, service, etc.
    gstin: Mapped[str] = mapped_column(String(20), nullable=True, index=True)
    pan: Mapped[str] = mapped_column(String(20), nullable=True)
    email: Mapped[str] = mapped_column(String(255), nullable=True)
    phone: Mapped[str] = mapped_column(String(50), nullable=True)
    mobile: Mapped[str] = mapped_column(String(50), nullable=True)
    address: Mapped[str] = mapped_column(Text, nullable=True)
    city: Mapped[str] = mapped_column(String(100), nullable=True)
    state: Mapped[str] = mapped_column(String(100), nullable=True)
    country: Mapped[str] = mapped_column(String(100), default="India")
    pincode: Mapped[str] = mapped_column(String(20), nullable=True)
    payment_terms: Mapped[str] = mapped_column(String(255), nullable=True)
    credit_days: Mapped[int] = mapped_column(Integer, default=30)
    bank_details: Mapped[dict] = mapped_column(JSONB, nullable=True)
    contact_persons: Mapped[list] = mapped_column(JSONB, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    rating: Mapped[int] = mapped_column(Integer, nullable=True)
    custom_fields: Mapped[dict] = mapped_column(JSONB, nullable=True)


class PurchaseOrder(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "purchase_orders"
    
    po_number: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    supplier_id: Mapped[str] = mapped_column(String(36), ForeignKey("suppliers.id"), nullable=True, index=True)
    po_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)
    expected_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="draft", index=True)  # draft, sent, partial, completed, cancelled
    
    # Addresses
    billing_address: Mapped[str] = mapped_column(Text, nullable=True)
    shipping_address: Mapped[str] = mapped_column(Text, nullable=True)
    
    # Line items
    items: Mapped[list] = mapped_column(JSONB, nullable=True)
    
    # Amounts
    subtotal: Mapped[float] = mapped_column(Float, default=0)
    discount_amount: Mapped[float] = mapped_column(Float, default=0)
    tax_amount: Mapped[float] = mapped_column(Float, default=0)
    freight_amount: Mapped[float] = mapped_column(Float, default=0)
    total_amount: Mapped[float] = mapped_column(Float, default=0)
    
    # References
    requisition_id: Mapped[str] = mapped_column(String(36), ForeignKey("purchase_requisitions.id"), nullable=True)
    
    terms_conditions: Mapped[str] = mapped_column(Text, nullable=True)
    notes: Mapped[str] = mapped_column(Text, nullable=True)
    approved_by: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    custom_fields: Mapped[dict] = mapped_column(JSONB, nullable=True)


class PurchaseRequisition(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "purchase_requisitions"
    
    pr_number: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    requisition_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    required_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="draft", index=True)  # draft, pending_approval, approved, converted, rejected
    department: Mapped[str] = mapped_column(String(100), nullable=True)
    items: Mapped[list] = mapped_column(JSONB, nullable=True)
    total_amount: Mapped[float] = mapped_column(Float, default=0)
    requested_by: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    approved_by: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    reason: Mapped[str] = mapped_column(Text, nullable=True)
    notes: Mapped[str] = mapped_column(Text, nullable=True)
    custom_fields: Mapped[dict] = mapped_column(JSONB, nullable=True)


class GRN(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "grn"
    
    grn_number: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    po_id: Mapped[str] = mapped_column(String(36), ForeignKey("purchase_orders.id"), nullable=True, index=True)
    supplier_id: Mapped[str] = mapped_column(String(36), ForeignKey("suppliers.id"), nullable=True, index=True)
    grn_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)
    warehouse_id: Mapped[str] = mapped_column(String(36), ForeignKey("warehouses.id"), nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="draft", index=True)  # draft, pending_qc, completed, rejected
    
    # Items
    items: Mapped[list] = mapped_column(JSONB, nullable=True)  # Array with received_qty, accepted_qty, rejected_qty
    
    # Challan/Invoice reference
    challan_number: Mapped[str] = mapped_column(String(100), nullable=True)
    challan_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    invoice_number: Mapped[str] = mapped_column(String(100), nullable=True)
    invoice_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Vehicle/Transport
    vehicle_number: Mapped[str] = mapped_column(String(50), nullable=True)
    transporter: Mapped[str] = mapped_column(String(255), nullable=True)
    lr_number: Mapped[str] = mapped_column(String(100), nullable=True)
    
    received_by: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    inspected_by: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    notes: Mapped[str] = mapped_column(Text, nullable=True)
    custom_fields: Mapped[dict] = mapped_column(JSONB, nullable=True)


class LandingCost(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "landing_costs"
    
    grn_id: Mapped[str] = mapped_column(String(36), ForeignKey("grn.id"), nullable=False, index=True)
    cost_type: Mapped[str] = mapped_column(String(50), nullable=False)  # freight, insurance, customs, handling, etc.
    description: Mapped[str] = mapped_column(Text, nullable=True)
    amount: Mapped[float] = mapped_column(Float, default=0)
    allocation_method: Mapped[str] = mapped_column(String(50), default="value")  # value, qty, weight
    vendor_name: Mapped[str] = mapped_column(String(255), nullable=True)
    invoice_number: Mapped[str] = mapped_column(String(100), nullable=True)
