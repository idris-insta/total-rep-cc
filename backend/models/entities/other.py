"""
SQLAlchemy Entity Models - Quality, Sales Incentives, Settings, and Other Modules
"""
from sqlalchemy import Column, String, DateTime, Boolean, Text, Integer, Float, ForeignKey, Date
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime, timezone, date

from core.database import Base
from models.entities.base import UUIDMixin, TimestampMixin


# ==================== QUALITY MODULE ====================
class QCInspection(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "qc_inspections"
    
    inspection_number: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    inspection_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)  # incoming, in_process, final, customer_return
    inspection_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    
    # Reference
    reference_type: Mapped[str] = mapped_column(String(50), nullable=True)  # grn, work_order, production_entry
    reference_id: Mapped[str] = mapped_column(String(36), nullable=True, index=True)
    
    item_id: Mapped[str] = mapped_column(String(36), ForeignKey("items.id"), nullable=True, index=True)
    batch_number: Mapped[str] = mapped_column(String(100), nullable=True)
    
    # Quantities
    sample_qty: Mapped[float] = mapped_column(Float, default=0)
    inspected_qty: Mapped[float] = mapped_column(Float, default=0)
    accepted_qty: Mapped[float] = mapped_column(Float, default=0)
    rejected_qty: Mapped[float] = mapped_column(Float, default=0)
    
    # Results
    result: Mapped[str] = mapped_column(String(20), default="pending", index=True)  # pending, pass, fail, conditional
    parameters: Mapped[list] = mapped_column(JSONB, nullable=True)  # Array of {name, standard, actual, result}
    
    inspector_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    remarks: Mapped[str] = mapped_column(Text, nullable=True)
    attachments: Mapped[list] = mapped_column(JSONB, nullable=True)
    custom_fields: Mapped[dict] = mapped_column(JSONB, nullable=True)


class QCParameter(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "qc_parameters"
    
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    category: Mapped[str] = mapped_column(String(100), nullable=True)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    unit: Mapped[str] = mapped_column(String(50), nullable=True)
    min_value: Mapped[float] = mapped_column(Float, nullable=True)
    max_value: Mapped[float] = mapped_column(Float, nullable=True)
    standard_value: Mapped[str] = mapped_column(String(255), nullable=True)
    is_mandatory: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class CustomerComplaint(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "customer_complaints"
    
    complaint_number: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    account_id: Mapped[str] = mapped_column(String(36), ForeignKey("accounts.id"), nullable=True, index=True)
    complaint_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    invoice_id: Mapped[str] = mapped_column(String(36), ForeignKey("invoices.id"), nullable=True)
    item_id: Mapped[str] = mapped_column(String(36), ForeignKey("items.id"), nullable=True)
    batch_number: Mapped[str] = mapped_column(String(100), nullable=True)
    
    complaint_type: Mapped[str] = mapped_column(String(100), nullable=True)
    severity: Mapped[str] = mapped_column(String(20), default="medium", index=True)  # low, medium, high, critical
    status: Mapped[str] = mapped_column(String(50), default="open", index=True)  # open, in_progress, resolved, closed
    
    description: Mapped[str] = mapped_column(Text, nullable=True)
    root_cause: Mapped[str] = mapped_column(Text, nullable=True)
    corrective_action: Mapped[str] = mapped_column(Text, nullable=True)
    preventive_action: Mapped[str] = mapped_column(Text, nullable=True)
    
    assigned_to: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    resolved_by: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    resolved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    
    attachments: Mapped[list] = mapped_column(JSONB, nullable=True)
    custom_fields: Mapped[dict] = mapped_column(JSONB, nullable=True)


class TDSDocument(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "tds_documents"
    
    item_id: Mapped[str] = mapped_column(String(36), ForeignKey("items.id"), nullable=False, index=True)
    version: Mapped[str] = mapped_column(String(20), nullable=True)
    effective_date: Mapped[date] = mapped_column(Date, nullable=True)
    specifications: Mapped[dict] = mapped_column(JSONB, nullable=True)
    test_methods: Mapped[dict] = mapped_column(JSONB, nullable=True)
    application_areas: Mapped[list] = mapped_column(JSONB, nullable=True)
    storage_conditions: Mapped[str] = mapped_column(Text, nullable=True)
    shelf_life: Mapped[str] = mapped_column(String(100), nullable=True)
    document_url: Mapped[str] = mapped_column(String(500), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


# ==================== SALES INCENTIVES ====================
class SalesTarget(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "sales_targets"
    
    employee_id: Mapped[str] = mapped_column(String(36), ForeignKey("employees.id"), nullable=False, index=True)
    period: Mapped[str] = mapped_column(String(20), nullable=False, index=True)  # YYYY-MM or YYYY-Q1, etc.
    target_type: Mapped[str] = mapped_column(String(50), default="revenue")  # revenue, collection, new_customers, orders
    target_value: Mapped[float] = mapped_column(Float, default=0)
    achieved_value: Mapped[float] = mapped_column(Float, default=0)
    achievement_percent: Mapped[float] = mapped_column(Float, default=0)
    status: Mapped[str] = mapped_column(String(50), default="active", index=True)


class IncentiveSlab(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "incentive_slabs"
    
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    min_achievement: Mapped[float] = mapped_column(Float, default=0)
    max_achievement: Mapped[float] = mapped_column(Float, default=100)
    incentive_percent: Mapped[float] = mapped_column(Float, default=0)
    fixed_amount: Mapped[float] = mapped_column(Float, default=0)
    applicable_for: Mapped[str] = mapped_column(String(50), nullable=True)  # all, designation-wise, etc.
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class IncentivePayout(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "incentive_payouts"
    
    employee_id: Mapped[str] = mapped_column(String(36), ForeignKey("employees.id"), nullable=False, index=True)
    period: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    target_id: Mapped[str] = mapped_column(String(36), ForeignKey("sales_targets.id"), nullable=True)
    achievement_percent: Mapped[float] = mapped_column(Float, default=0)
    incentive_amount: Mapped[float] = mapped_column(Float, default=0)
    status: Mapped[str] = mapped_column(String(50), default="calculated", index=True)  # calculated, approved, paid
    approved_by: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    payment_date: Mapped[date] = mapped_column(Date, nullable=True)
    transaction_ref: Mapped[str] = mapped_column(String(100), nullable=True)
    notes: Mapped[str] = mapped_column(Text, nullable=True)


class SalesAchievement(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "sales_achievements"
    
    employee_id: Mapped[str] = mapped_column(String(36), ForeignKey("employees.id"), nullable=False, index=True)
    period: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    target_type: Mapped[str] = mapped_column(String(50), default="revenue")
    target_value: Mapped[float] = mapped_column(Float, default=0)
    achieved_value: Mapped[float] = mapped_column(Float, default=0)
    achievement_percent: Mapped[float] = mapped_column(Float, default=0)
    breakdown: Mapped[dict] = mapped_column(JSONB, nullable=True)  # Details by customer, product, etc.


# ==================== SETTINGS & CONFIGURATION ====================
class FieldConfiguration(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "field_configurations"
    
    module: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    entity: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    fields: Mapped[list] = mapped_column(JSONB, nullable=True)  # Array of field configs
    layout: Mapped[dict] = mapped_column(JSONB, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class SystemSetting(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "system_settings"
    
    key: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    value: Mapped[str] = mapped_column(Text, nullable=True)
    value_json: Mapped[dict] = mapped_column(JSONB, nullable=True)
    category: Mapped[str] = mapped_column(String(50), default="general")
    description: Mapped[str] = mapped_column(Text, nullable=True)
    is_public: Mapped[bool] = mapped_column(Boolean, default=False)


class CompanyProfile(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "company_profiles"
    
    company_name: Mapped[str] = mapped_column(String(255), nullable=False)
    legal_name: Mapped[str] = mapped_column(String(255), nullable=True)
    gstin: Mapped[str] = mapped_column(String(20), nullable=True, index=True)
    pan: Mapped[str] = mapped_column(String(20), nullable=True)
    cin: Mapped[str] = mapped_column(String(30), nullable=True)
    
    address: Mapped[str] = mapped_column(Text, nullable=True)
    city: Mapped[str] = mapped_column(String(100), nullable=True)
    state: Mapped[str] = mapped_column(String(100), nullable=True)
    pincode: Mapped[str] = mapped_column(String(20), nullable=True)
    country: Mapped[str] = mapped_column(String(100), default="India")
    
    phone: Mapped[str] = mapped_column(String(50), nullable=True)
    email: Mapped[str] = mapped_column(String(255), nullable=True)
    website: Mapped[str] = mapped_column(String(255), nullable=True)
    
    logo_url: Mapped[str] = mapped_column(String(500), nullable=True)
    bank_details: Mapped[dict] = mapped_column(JSONB, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class Branch(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "branches"
    
    branch_code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)
    branch_name: Mapped[str] = mapped_column(String(255), nullable=False)
    branch_type: Mapped[str] = mapped_column(String(50), default="branch")  # head_office, branch, warehouse, factory
    
    address: Mapped[str] = mapped_column(Text, nullable=True)
    city: Mapped[str] = mapped_column(String(100), nullable=True)
    state: Mapped[str] = mapped_column(String(100), nullable=True)
    pincode: Mapped[str] = mapped_column(String(20), nullable=True)
    
    gstin: Mapped[str] = mapped_column(String(20), nullable=True)
    phone: Mapped[str] = mapped_column(String(50), nullable=True)
    email: Mapped[str] = mapped_column(String(255), nullable=True)
    
    manager_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    is_head_office: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    custom_fields: Mapped[dict] = mapped_column(JSONB, nullable=True)


class NumberSeries(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "number_series"
    
    document_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    prefix: Mapped[str] = mapped_column(String(20), nullable=True)
    suffix: Mapped[str] = mapped_column(String(20), nullable=True)
    current_number: Mapped[int] = mapped_column(Integer, default=0)
    padding: Mapped[int] = mapped_column(Integer, default=4)
    reset_on: Mapped[str] = mapped_column(String(20), nullable=True)  # monthly, yearly, never
    branch_id: Mapped[str] = mapped_column(String(36), ForeignKey("branches.id"), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


# ==================== DOCUMENTS & FILES ====================
class Document(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "documents"
    
    document_name: Mapped[str] = mapped_column(String(255), nullable=False)
    document_type: Mapped[str] = mapped_column(String(50), nullable=True)
    reference_type: Mapped[str] = mapped_column(String(50), nullable=True, index=True)
    reference_id: Mapped[str] = mapped_column(String(36), nullable=True, index=True)
    file_url: Mapped[str] = mapped_column(String(500), nullable=True)
    file_size: Mapped[int] = mapped_column(Integer, nullable=True)
    mime_type: Mapped[str] = mapped_column(String(100), nullable=True)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    tags: Mapped[list] = mapped_column(JSONB, nullable=True)


class DriveFolder(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "drive_folders"
    
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    parent_id: Mapped[str] = mapped_column(String(36), ForeignKey("drive_folders.id"), nullable=True)
    path: Mapped[str] = mapped_column(String(1000), nullable=True)
    owner_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    is_shared: Mapped[bool] = mapped_column(Boolean, default=False)
    shared_with: Mapped[list] = mapped_column(JSONB, nullable=True)


class DriveFile(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "drive_files"
    
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    folder_id: Mapped[str] = mapped_column(String(36), ForeignKey("drive_folders.id"), nullable=True, index=True)
    file_url: Mapped[str] = mapped_column(String(500), nullable=True)
    file_size: Mapped[int] = mapped_column(Integer, nullable=True)
    mime_type: Mapped[str] = mapped_column(String(100), nullable=True)
    owner_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    is_shared: Mapped[bool] = mapped_column(Boolean, default=False)
    shared_with: Mapped[list] = mapped_column(JSONB, nullable=True)


# ==================== NOTIFICATIONS & ACTIVITY ====================
class Notification(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "notifications"
    
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=True)
    notification_type: Mapped[str] = mapped_column(String(50), nullable=True)
    priority: Mapped[str] = mapped_column(String(20), default="normal")
    reference_type: Mapped[str] = mapped_column(String(50), nullable=True)
    reference_id: Mapped[str] = mapped_column(String(36), nullable=True)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False)
    read_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)


class ActivityLog(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "activity_logs"
    
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=True, index=True)
    action: Mapped[str] = mapped_column(String(50), nullable=False)
    entity_type: Mapped[str] = mapped_column(String(50), nullable=True, index=True)
    entity_id: Mapped[str] = mapped_column(String(36), nullable=True, index=True)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    old_values: Mapped[dict] = mapped_column(JSONB, nullable=True)
    new_values: Mapped[dict] = mapped_column(JSONB, nullable=True)
    ip_address: Mapped[str] = mapped_column(String(50), nullable=True)
    user_agent: Mapped[str] = mapped_column(String(500), nullable=True)


class ApprovalRequest(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "approval_requests"
    
    request_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    reference_type: Mapped[str] = mapped_column(String(50), nullable=True)
    reference_id: Mapped[str] = mapped_column(String(36), nullable=True, index=True)
    requested_by: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    approver_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="pending", index=True)
    comments: Mapped[str] = mapped_column(Text, nullable=True)
    approved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)


# ==================== CHAT & COMMUNICATION ====================
class ChatRoom(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "chat_rooms"
    
    name: Mapped[str] = mapped_column(String(255), nullable=True)
    room_type: Mapped[str] = mapped_column(String(20), default="direct")  # direct, group
    participants: Mapped[list] = mapped_column(JSONB, nullable=True)  # Array of user_ids
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class ChatMessage(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "chat_messages"
    
    room_id: Mapped[str] = mapped_column(String(36), ForeignKey("chat_rooms.id"), nullable=False, index=True)
    sender_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=True)
    message_type: Mapped[str] = mapped_column(String(20), default="text")  # text, image, file
    attachments: Mapped[list] = mapped_column(JSONB, nullable=True)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False)
    read_by: Mapped[list] = mapped_column(JSONB, nullable=True)


# ==================== E-INVOICE & GST ====================
class EInvoice(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "e_invoices"
    
    invoice_id: Mapped[str] = mapped_column(String(36), ForeignKey("invoices.id"), nullable=False, index=True)
    irn: Mapped[str] = mapped_column(String(100), nullable=True, index=True)
    ack_number: Mapped[str] = mapped_column(String(100), nullable=True)
    ack_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    signed_invoice: Mapped[str] = mapped_column(Text, nullable=True)
    signed_qr_code: Mapped[str] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="pending", index=True)
    error_message: Mapped[str] = mapped_column(Text, nullable=True)
    request_payload: Mapped[dict] = mapped_column(JSONB, nullable=True)
    response_payload: Mapped[dict] = mapped_column(JSONB, nullable=True)


class EWayBill(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "eway_bills"
    
    invoice_id: Mapped[str] = mapped_column(String(36), ForeignKey("invoices.id"), nullable=True, index=True)
    eway_bill_number: Mapped[str] = mapped_column(String(50), nullable=True, index=True)
    eway_bill_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    valid_until: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="pending", index=True)
    
    # Transport details
    transporter_id: Mapped[str] = mapped_column(String(36), ForeignKey("transporters.id"), nullable=True)
    transporter_name: Mapped[str] = mapped_column(String(255), nullable=True)
    vehicle_number: Mapped[str] = mapped_column(String(50), nullable=True)
    transport_mode: Mapped[str] = mapped_column(String(20), nullable=True)
    transport_doc_number: Mapped[str] = mapped_column(String(100), nullable=True)
    transport_doc_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    
    from_place: Mapped[str] = mapped_column(String(255), nullable=True)
    from_state: Mapped[str] = mapped_column(String(100), nullable=True)
    from_pincode: Mapped[str] = mapped_column(String(20), nullable=True)
    to_place: Mapped[str] = mapped_column(String(255), nullable=True)
    to_state: Mapped[str] = mapped_column(String(100), nullable=True)
    to_pincode: Mapped[str] = mapped_column(String(20), nullable=True)
    
    distance: Mapped[int] = mapped_column(Integer, nullable=True)
    error_message: Mapped[str] = mapped_column(Text, nullable=True)


class Transporter(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "transporters"
    
    transporter_name: Mapped[str] = mapped_column(String(255), nullable=False)
    transporter_id: Mapped[str] = mapped_column(String(20), nullable=True)  # GST Transporter ID
    gstin: Mapped[str] = mapped_column(String(20), nullable=True)
    phone: Mapped[str] = mapped_column(String(50), nullable=True)
    email: Mapped[str] = mapped_column(String(255), nullable=True)
    address: Mapped[str] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


# ==================== GATEPASS & DELIVERY ====================
class Gatepass(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "gatepasses"
    
    gatepass_number: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    gatepass_type: Mapped[str] = mapped_column(String(50), default="outward")  # inward, outward, returnable
    gatepass_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    
    # Reference
    reference_type: Mapped[str] = mapped_column(String(50), nullable=True)  # invoice, challan, transfer
    reference_id: Mapped[str] = mapped_column(String(36), nullable=True)
    
    account_id: Mapped[str] = mapped_column(String(36), ForeignKey("accounts.id"), nullable=True)
    
    # Items
    items: Mapped[list] = mapped_column(JSONB, nullable=True)
    
    # Vehicle
    vehicle_number: Mapped[str] = mapped_column(String(50), nullable=True)
    driver_name: Mapped[str] = mapped_column(String(255), nullable=True)
    driver_phone: Mapped[str] = mapped_column(String(50), nullable=True)
    
    status: Mapped[str] = mapped_column(String(50), default="pending", index=True)
    expected_return_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    actual_return_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    
    authorized_by: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    notes: Mapped[str] = mapped_column(Text, nullable=True)


class DeliveryChallan(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "delivery_challans"
    
    challan_number: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    challan_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    challan_type: Mapped[str] = mapped_column(String(50), default="delivery")  # delivery, job_work, sample
    
    account_id: Mapped[str] = mapped_column(String(36), ForeignKey("accounts.id"), nullable=True, index=True)
    invoice_id: Mapped[str] = mapped_column(String(36), ForeignKey("invoices.id"), nullable=True)
    sales_order_id: Mapped[str] = mapped_column(String(36), nullable=True)
    
    shipping_address: Mapped[str] = mapped_column(Text, nullable=True)
    items: Mapped[list] = mapped_column(JSONB, nullable=True)
    
    # Transport
    transporter_id: Mapped[str] = mapped_column(String(36), ForeignKey("transporters.id"), nullable=True)
    vehicle_number: Mapped[str] = mapped_column(String(50), nullable=True)
    lr_number: Mapped[str] = mapped_column(String(100), nullable=True)
    
    status: Mapped[str] = mapped_column(String(50), default="draft", index=True)
    delivered_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    received_by: Mapped[str] = mapped_column(String(255), nullable=True)
    
    notes: Mapped[str] = mapped_column(Text, nullable=True)
    custom_fields: Mapped[dict] = mapped_column(JSONB, nullable=True)


# ==================== AI & ANALYTICS ====================
class AIQuery(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "ai_queries"
    
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=True, index=True)
    query: Mapped[str] = mapped_column(Text, nullable=False)
    response: Mapped[str] = mapped_column(Text, nullable=True)
    context: Mapped[dict] = mapped_column(JSONB, nullable=True)
    model_used: Mapped[str] = mapped_column(String(100), nullable=True)
    tokens_used: Mapped[int] = mapped_column(Integer, nullable=True)
    response_time_ms: Mapped[int] = mapped_column(Integer, nullable=True)


class CustomReport(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "custom_reports"
    
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    module: Mapped[str] = mapped_column(String(50), nullable=True)
    report_type: Mapped[str] = mapped_column(String(50), nullable=True)
    query_config: Mapped[dict] = mapped_column(JSONB, nullable=True)
    columns: Mapped[list] = mapped_column(JSONB, nullable=True)
    filters: Mapped[list] = mapped_column(JSONB, nullable=True)
    grouping: Mapped[list] = mapped_column(JSONB, nullable=True)
    sorting: Mapped[list] = mapped_column(JSONB, nullable=True)
    owner_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    is_public: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
