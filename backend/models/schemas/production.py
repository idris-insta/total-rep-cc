"""
Production Schemas - Pydantic models for Production module
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum


# ==================== ENUMS ====================
class MachineType(str, Enum):
    COATING = "coating"
    SLITTING = "slitting"
    REWINDING = "rewinding"
    CUTTING = "cutting"
    PACKING = "packing"


class MachineStatus(str, Enum):
    ACTIVE = "active"
    MAINTENANCE = "maintenance"
    INACTIVE = "inactive"


class ProductionStage(str, Enum):
    COATING = "coating"
    SLITTING = "slitting"
    REWINDING = "rewinding"
    CUTTING = "cutting"
    PACKING = "packing"
    QUALITY_CHECK = "quality_check"
    DISPATCH_READY = "dispatch_ready"


class OrderStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


# ==================== MACHINE SCHEMAS ====================
class MachineBase(BaseModel):
    machine_name: Optional[str] = None
    machine_code: Optional[str] = None
    machine_type: Optional[str] = None
    capacity_per_hour: Optional[float] = None
    power_consumption_kw: Optional[float] = None
    maintenance_cycle_days: Optional[int] = None
    last_maintenance_date: Optional[str] = None
    notes: Optional[str] = None


class MachineCreate(MachineBase):
    machine_name: str
    machine_type: str


class MachineUpdate(MachineBase):
    status: Optional[str] = None


class MachineResponse(MachineBase):
    id: str
    status: str = "active"
    current_job: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


# ==================== ORDER SHEET SCHEMAS ====================
class OrderSheetItem(BaseModel):
    item_id: Optional[str] = None
    item_name: Optional[str] = None
    qty: float
    unit: str = "Pcs"
    specifications: Optional[str] = None


class OrderSheetBase(BaseModel):
    customer_id: Optional[str] = None
    customer_name: Optional[str] = None
    sales_order_id: Optional[str] = None
    delivery_date: Optional[str] = None
    priority: Optional[str] = "normal"
    notes: Optional[str] = None
    items: Optional[List[OrderSheetItem]] = []


class OrderSheetCreate(OrderSheetBase):
    items: List[OrderSheetItem]


class OrderSheetUpdate(OrderSheetBase):
    pass


class OrderSheetResponse(OrderSheetBase):
    id: str
    order_number: Optional[str] = None
    status: str = "pending"
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


# ==================== WORK ORDER SCHEMAS ====================
class WorkOrderBase(BaseModel):
    order_sheet_id: Optional[str] = None
    stage: Optional[str] = None
    machine_id: Optional[str] = None
    machine_name: Optional[str] = None
    target_qty: Optional[float] = None
    unit: str = "Pcs"
    scheduled_start: Optional[str] = None
    scheduled_end: Optional[str] = None
    notes: Optional[str] = None


class WorkOrderCreate(WorkOrderBase):
    order_sheet_id: str
    stage: str
    target_qty: float


class WorkOrderUpdate(WorkOrderBase):
    pass


class WorkOrderResponse(WorkOrderBase):
    id: str
    wo_number: Optional[str] = None
    status: str = "pending"
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    actual_output: Optional[float] = None
    actual_scrap: Optional[float] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


# ==================== PRODUCTION ENTRY SCHEMAS ====================
class ProductionEntryBase(BaseModel):
    work_order_id: Optional[str] = None
    machine_id: Optional[str] = None
    production_date: Optional[str] = None
    shift: Optional[str] = None
    operator_id: Optional[str] = None
    operator_name: Optional[str] = None
    input_qty: Optional[float] = None
    output_qty: Optional[float] = None
    scrap_qty: Optional[float] = None
    scrap_reason: Optional[str] = None
    downtime_minutes: Optional[int] = None
    downtime_reason: Optional[str] = None
    notes: Optional[str] = None


class ProductionEntryCreate(ProductionEntryBase):
    work_order_id: str
    output_qty: float


class ProductionEntryResponse(ProductionEntryBase):
    id: str
    scrap_percent: Optional[float] = None
    redline_alert: Optional[bool] = False
    redline_status: Optional[str] = None
    created_at: Optional[str] = None


# ==================== RM REQUISITION SCHEMAS ====================
class RequisitionItem(BaseModel):
    item_id: str
    item_name: Optional[str] = None
    qty: float
    unit: str = "Pcs"


class RMRequisitionBase(BaseModel):
    work_order_id: Optional[str] = None
    warehouse_id: Optional[str] = None
    items: Optional[List[RequisitionItem]] = []
    notes: Optional[str] = None


class RMRequisitionCreate(RMRequisitionBase):
    work_order_id: str
    warehouse_id: str
    items: List[RequisitionItem]


class RMRequisitionResponse(RMRequisitionBase):
    id: str
    requisition_number: Optional[str] = None
    status: str = "pending"
    issued_at: Optional[str] = None
    issued_by: Optional[str] = None
    created_at: Optional[str] = None
