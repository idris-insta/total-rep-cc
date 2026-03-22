"""
SQLAlchemy Entity Models - Base and Common
"""
from sqlalchemy import Column, String, DateTime, Boolean, Text, Integer, Float, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship, Mapped, mapped_column
from datetime import datetime, timezone
import uuid

from core.database import Base


class TimestampMixin:
    """Mixin for created_at and updated_at timestamps"""
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    created_by: Mapped[str] = mapped_column(String(36), nullable=True)
    updated_by: Mapped[str] = mapped_column(String(36), nullable=True)


class UUIDMixin:
    """Mixin for UUID primary key"""
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))


# ==================== USER & AUTH ====================
class User(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "users"
    
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    password: Mapped[str] = mapped_column(String(255), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(50), default="viewer")
    location: Mapped[str] = mapped_column(String(255), nullable=True)
    department: Mapped[str] = mapped_column(String(255), nullable=True)
    team: Mapped[str] = mapped_column(String(255), nullable=True)
    reports_to: Mapped[str] = mapped_column(String(36), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    permissions: Mapped[dict] = mapped_column(JSONB, nullable=True)


class Role(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "roles"
    
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    permissions: Mapped[dict] = mapped_column(JSONB, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


# ==================== CRM ====================
class Lead(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "leads"
    
    company_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    contact_person: Mapped[str] = mapped_column(String(255), nullable=True)
    email: Mapped[str] = mapped_column(String(255), nullable=True, index=True)
    phone: Mapped[str] = mapped_column(String(50), nullable=True)
    mobile: Mapped[str] = mapped_column(String(50), nullable=True)
    address: Mapped[str] = mapped_column(Text, nullable=True)
    city: Mapped[str] = mapped_column(String(100), nullable=True)
    state: Mapped[str] = mapped_column(String(100), nullable=True)
    country: Mapped[str] = mapped_column(String(100), default="India")
    pincode: Mapped[str] = mapped_column(String(20), nullable=True)
    source: Mapped[str] = mapped_column(String(100), nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="new", index=True)
    industry: Mapped[str] = mapped_column(String(100), nullable=True)
    customer_type: Mapped[str] = mapped_column(String(100), nullable=True)
    expected_value: Mapped[float] = mapped_column(Float, nullable=True)
    estimated_value: Mapped[float] = mapped_column(Float, nullable=True)
    probability: Mapped[int] = mapped_column(Integer, nullable=True)
    assigned_to: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=True, index=True)
    notes: Mapped[str] = mapped_column(Text, nullable=True)
    custom_fields: Mapped[dict] = mapped_column(JSONB, nullable=True)
    next_followup_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    next_follow_up: Mapped[str] = mapped_column(String(255), nullable=True)
    follow_up_activity: Mapped[str] = mapped_column(String(255), nullable=True)
    products_of_interest: Mapped[list] = mapped_column(JSONB, nullable=True)
    lost_reason: Mapped[str] = mapped_column(String(255), nullable=True)


class Account(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "accounts"
    
    customer_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    account_type: Mapped[str] = mapped_column(String(50), default="customer")  # customer, supplier, both
    gstin: Mapped[str] = mapped_column(String(20), nullable=True, index=True)
    pan: Mapped[str] = mapped_column(String(20), nullable=True)
    industry: Mapped[str] = mapped_column(String(100), nullable=True)
    website: Mapped[str] = mapped_column(String(255), nullable=True)
    aadhar_no: Mapped[str] = mapped_column(String(20), nullable=True)
    opening_balance: Mapped[float] = mapped_column(Float, default=0)
    bank_details: Mapped[str] = mapped_column(Text, nullable=True)
    notes: Mapped[str] = mapped_column(Text, nullable=True)
    
    email: Mapped[str] = mapped_column(String(255), nullable=True)
    phone: Mapped[str] = mapped_column(String(50), nullable=True)
    mobile: Mapped[str] = mapped_column(String(50), nullable=True)
    
    # Billing Address
    billing_address: Mapped[str] = mapped_column(Text, nullable=True)
    billing_city: Mapped[str] = mapped_column(String(100), nullable=True)
    billing_state: Mapped[str] = mapped_column(String(100), nullable=True)
    billing_pincode: Mapped[str] = mapped_column(String(20), nullable=True)
    billing_country: Mapped[str] = mapped_column(String(100), default="India")
    
    # Shipping Address
    shipping_address: Mapped[str] = mapped_column(Text, nullable=True)
    city: Mapped[str] = mapped_column(String(100), nullable=True)
    state: Mapped[str] = mapped_column(String(100), nullable=True)
    country: Mapped[str] = mapped_column(String(100), default="India")
    pincode: Mapped[str] = mapped_column(String(20), nullable=True)
    
    # Credit Terms
    credit_limit: Mapped[float] = mapped_column(Float, default=0)
    credit_days: Mapped[int] = mapped_column(Integer, default=30)
    payment_terms: Mapped[str] = mapped_column(String(255), nullable=True)
    credit_control: Mapped[str] = mapped_column(String(50), default="warning")
    
    # Balances (calculated)
    receivable_amount: Mapped[float] = mapped_column(Float, default=0)
    payable_amount: Mapped[float] = mapped_column(Float, default=0)
    
    assigned_to: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    custom_fields: Mapped[dict] = mapped_column(JSONB, nullable=True)
    contact_persons: Mapped[list] = mapped_column(JSONB, nullable=True)  # Array of contact objects


class Quotation(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "quotations"
    
    quote_number: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    account_id: Mapped[str] = mapped_column(String(36), ForeignKey("accounts.id"), nullable=True, index=True)
    lead_id: Mapped[str] = mapped_column(String(36), ForeignKey("leads.id"), nullable=True)
    quote_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    valid_until: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="draft", index=True)
    items: Mapped[list] = mapped_column(JSONB, nullable=True)  # Array of line items
    subtotal: Mapped[float] = mapped_column(Float, default=0)
    tax_amount: Mapped[float] = mapped_column(Float, default=0)
    discount_amount: Mapped[float] = mapped_column(Float, default=0)
    grand_total: Mapped[float] = mapped_column(Float, default=0)
    terms_conditions: Mapped[str] = mapped_column(Text, nullable=True)
    notes: Mapped[str] = mapped_column(Text, nullable=True)
    assigned_to: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    custom_fields: Mapped[dict] = mapped_column(JSONB, nullable=True)


class Sample(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "samples"
    
    sample_number: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    account_id: Mapped[str] = mapped_column(String(36), ForeignKey("accounts.id"), nullable=True, index=True)
    lead_id: Mapped[str] = mapped_column(String(36), ForeignKey("leads.id"), nullable=True)
    sample_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    status: Mapped[str] = mapped_column(String(50), default="pending", index=True)
    items: Mapped[list] = mapped_column(JSONB, nullable=True)
    delivery_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    feedback_due_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    feedback: Mapped[str] = mapped_column(Text, nullable=True)
    feedback_rating: Mapped[int] = mapped_column(Integer, nullable=True)
    notes: Mapped[str] = mapped_column(Text, nullable=True)
    assigned_to: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    custom_fields: Mapped[dict] = mapped_column(JSONB, nullable=True)


class Followup(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "followups"
    
    lead_id: Mapped[str] = mapped_column(String(36), ForeignKey("leads.id"), nullable=True, index=True)
    account_id: Mapped[str] = mapped_column(String(36), ForeignKey("accounts.id"), nullable=True, index=True)
    followup_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    followup_type: Mapped[str] = mapped_column(String(50), default="call")  # call, email, visit, meeting
    status: Mapped[str] = mapped_column(String(50), default="pending")
    notes: Mapped[str] = mapped_column(Text, nullable=True)
    outcome: Mapped[str] = mapped_column(Text, nullable=True)
    next_action: Mapped[str] = mapped_column(Text, nullable=True)
    assigned_to: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
