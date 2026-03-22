"""
SQLAlchemy Entity Models - Production Module
"""
from sqlalchemy import Column, String, DateTime, Boolean, Text, Integer, Float, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime, timezone

from core.database import Base
from models.entities.base import UUIDMixin, TimestampMixin


class Machine(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "machines"
    
    machine_code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    machine_name: Mapped[str] = mapped_column(String(255), nullable=False)
    machine_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)  # coating, slitting, rewinding, cutting, packing
    description: Mapped[str] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="active", index=True)  # active, maintenance, inactive
    current_job: Mapped[str] = mapped_column(String(36), nullable=True)  # current work_order_id
    capacity_per_hour: Mapped[float] = mapped_column(Float, nullable=True)
    capacity_uom: Mapped[str] = mapped_column(String(50), nullable=True)
    power_consumption_kw: Mapped[float] = mapped_column(Float, nullable=True)
    maintenance_cycle_days: Mapped[int] = mapped_column(Integer, nullable=True)
    last_maintenance_date: Mapped[str] = mapped_column(String(50), nullable=True)
    location: Mapped[str] = mapped_column(String(255), nullable=True)
    operator_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    maintenance_schedule: Mapped[dict] = mapped_column(JSONB, nullable=True)
    last_maintenance: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    next_maintenance: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    notes: Mapped[str] = mapped_column(Text, nullable=True)
    specifications: Mapped[dict] = mapped_column(JSONB, nullable=True)
    custom_fields: Mapped[dict] = mapped_column(JSONB, nullable=True)


class OrderSheet(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "order_sheets"
    
    order_number: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    order_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    account_id: Mapped[str] = mapped_column(String(36), ForeignKey("accounts.id"), nullable=True, index=True)
    sales_order_id: Mapped[str] = mapped_column(String(36), nullable=True, index=True)
    status: Mapped[str] = mapped_column(String(50), default="pending", index=True)  # pending, in_progress, completed, cancelled
    priority: Mapped[str] = mapped_column(String(20), default="normal")  # low, normal, high, urgent
    required_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    items: Mapped[list] = mapped_column(JSONB, nullable=True)  # Array of order items
    total_qty: Mapped[float] = mapped_column(Float, default=0)
    completed_qty: Mapped[float] = mapped_column(Float, default=0)
    notes: Mapped[str] = mapped_column(Text, nullable=True)
    custom_fields: Mapped[dict] = mapped_column(JSONB, nullable=True)


class WorkOrder(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "work_orders"
    
    wo_number: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    order_sheet_id: Mapped[str] = mapped_column(String(36), ForeignKey("order_sheets.id"), nullable=True, index=True)
    item_id: Mapped[str] = mapped_column(String(36), ForeignKey("items.id"), nullable=True, index=True)
    machine_id: Mapped[str] = mapped_column(String(36), ForeignKey("machines.id"), nullable=True, index=True)
    stage: Mapped[str] = mapped_column(String(50), nullable=False, index=True)  # coating, drying, slitting, rewinding, cutting, packing, dispatch
    status: Mapped[str] = mapped_column(String(50), default="pending", index=True)  # pending, in_progress, completed, on_hold
    priority: Mapped[str] = mapped_column(String(20), default="normal")
    planned_qty: Mapped[float] = mapped_column(Float, default=0)
    completed_qty: Mapped[float] = mapped_column(Float, default=0)
    rejected_qty: Mapped[float] = mapped_column(Float, default=0)
    planned_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    planned_end: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    actual_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    actual_end: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    operator_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    specifications: Mapped[dict] = mapped_column(JSONB, nullable=True)  # Width, length, thickness, etc.
    bom: Mapped[list] = mapped_column(JSONB, nullable=True)  # Bill of Materials
    notes: Mapped[str] = mapped_column(Text, nullable=True)
    custom_fields: Mapped[dict] = mapped_column(JSONB, nullable=True)


class ProductionEntry(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "production_entries"
    
    entry_number: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    work_order_id: Mapped[str] = mapped_column(String(36), ForeignKey("work_orders.id"), nullable=False, index=True)
    machine_id: Mapped[str] = mapped_column(String(36), ForeignKey("machines.id"), nullable=True, index=True)
    production_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)
    shift: Mapped[str] = mapped_column(String(20), nullable=True)  # morning, evening, night
    operator_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    good_qty: Mapped[float] = mapped_column(Float, default=0)
    rejected_qty: Mapped[float] = mapped_column(Float, default=0)
    wastage_qty: Mapped[float] = mapped_column(Float, default=0)
    start_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    end_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    downtime_minutes: Mapped[int] = mapped_column(Integer, default=0)
    downtime_reason: Mapped[str] = mapped_column(Text, nullable=True)
    batch_number: Mapped[str] = mapped_column(String(100), nullable=True)
    quality_params: Mapped[dict] = mapped_column(JSONB, nullable=True)
    notes: Mapped[str] = mapped_column(Text, nullable=True)


class RMRequisition(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "rm_requisitions"
    
    requisition_number: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    work_order_id: Mapped[str] = mapped_column(String(36), ForeignKey("work_orders.id"), nullable=True, index=True)
    requisition_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    status: Mapped[str] = mapped_column(String(50), default="pending", index=True)  # pending, approved, issued, completed
    items: Mapped[list] = mapped_column(JSONB, nullable=True)  # Array of requisition items
    warehouse_id: Mapped[str] = mapped_column(String(36), ForeignKey("warehouses.id"), nullable=True)
    requested_by: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    approved_by: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    issued_by: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    notes: Mapped[str] = mapped_column(Text, nullable=True)


class WorkOrderStage(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "work_order_stages"
    
    work_order_id: Mapped[str] = mapped_column(String(36), ForeignKey("work_orders.id"), nullable=False, index=True)
    stage_number: Mapped[int] = mapped_column(Integer, nullable=False)
    stage_name: Mapped[str] = mapped_column(String(50), nullable=False)  # coating, drying, slitting, etc.
    status: Mapped[str] = mapped_column(String(50), default="pending")
    machine_id: Mapped[str] = mapped_column(String(36), ForeignKey("machines.id"), nullable=True)
    operator_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    input_qty: Mapped[float] = mapped_column(Float, default=0)
    output_qty: Mapped[float] = mapped_column(Float, default=0)
    rejected_qty: Mapped[float] = mapped_column(Float, default=0)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    parameters: Mapped[dict] = mapped_column(JSONB, nullable=True)  # Stage-specific parameters
    quality_check: Mapped[dict] = mapped_column(JSONB, nullable=True)
    notes: Mapped[str] = mapped_column(Text, nullable=True)


class StageEntry(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "stage_entries"
    
    work_order_stage_id: Mapped[str] = mapped_column(String(36), ForeignKey("work_order_stages.id"), nullable=False, index=True)
    entry_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    shift: Mapped[str] = mapped_column(String(20), nullable=True)
    operator_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    input_qty: Mapped[float] = mapped_column(Float, default=0)
    output_qty: Mapped[float] = mapped_column(Float, default=0)
    rejected_qty: Mapped[float] = mapped_column(Float, default=0)
    wastage_qty: Mapped[float] = mapped_column(Float, default=0)
    parameters: Mapped[dict] = mapped_column(JSONB, nullable=True)
    notes: Mapped[str] = mapped_column(Text, nullable=True)
