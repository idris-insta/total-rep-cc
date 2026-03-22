"""
Inventory Schemas - Pydantic models for Inventory module
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum


# ==================== ENUMS ====================
class ItemCategory(str, Enum):
    RAW_MATERIAL = "raw_material"
    SEMI_FINISHED = "semi_finished"
    FINISHED_GOODS = "finished_goods"
    PACKAGING = "packaging"


class ItemType(str, Enum):
    BOPP = "BOPP"
    MASKING = "Masking"
    DOUBLE_SIDED = "Double-Sided"
    CLOTH = "Cloth"
    PVC = "PVC"
    FOAM = "Foam"
    OTHER = "Other"


class AdjustmentType(str, Enum):
    OPENING = "opening"
    CLOSING = "closing"
    INCREASE = "increase"
    DECREASE = "decrease"
    DAMAGE = "damage"
    EXPIRED = "expired"
    RECOUNT = "recount"


class TransferStatus(str, Enum):
    PENDING = "pending"
    IN_TRANSIT = "in_transit"
    RECEIVED = "received"
    CANCELLED = "cancelled"


# ==================== ITEM SCHEMAS ====================
class ItemBase(BaseModel):
    item_code: Optional[str] = None
    item_name: Optional[str] = None
    category: Optional[str] = None
    item_type: Optional[str] = None
    hsn_code: Optional[str] = None
    # Specifications
    base_material: Optional[str] = None
    adhesive_type: Optional[str] = None
    thickness_microns: Optional[float] = None
    color: Optional[str] = None
    width_mm: Optional[float] = None
    length_m: Optional[float] = None
    gsm: Optional[float] = None
    # UOM
    primary_uom: Optional[str] = "Pcs"
    secondary_uom: Optional[str] = None
    conversion_factor: Optional[float] = None
    # Pricing
    cost_price: Optional[float] = None
    margin_percent: Optional[float] = None
    min_selling_price: Optional[float] = None
    mrp: Optional[float] = None
    # Inventory
    reorder_level: Optional[int] = None
    safety_stock: Optional[int] = None
    lead_time_days: Optional[int] = None
    shelf_life_days: Optional[int] = None
    # Other
    barcode: Optional[str] = None
    notes: Optional[str] = None


class ItemCreate(ItemBase):
    item_name: str


class ItemUpdate(ItemBase):
    pass


class ItemResponse(ItemBase):
    id: str
    stock_qty: Optional[float] = 0
    stock_kg: Optional[float] = 0
    stock_sqm: Optional[float] = 0
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


# ==================== WAREHOUSE SCHEMAS ====================
class WarehouseBase(BaseModel):
    code: Optional[str] = None
    name: Optional[str] = None
    prefix: Optional[str] = None
    gstin: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    pincode: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    bank_name: Optional[str] = None
    bank_account: Optional[str] = None
    bank_ifsc: Optional[str] = None


class WarehouseCreate(WarehouseBase):
    name: str


class WarehouseUpdate(WarehouseBase):
    is_active: Optional[bool] = None


class WarehouseResponse(WarehouseBase):
    id: str
    is_active: bool = True
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


# ==================== STOCK TRANSFER SCHEMAS ====================
class TransferItem(BaseModel):
    item_id: str
    item_name: Optional[str] = None
    qty: float
    unit: str = "Pcs"
    notes: Optional[str] = None


class StockTransferBase(BaseModel):
    from_warehouse_id: Optional[str] = None
    to_warehouse_id: Optional[str] = None
    reference: Optional[str] = None
    transport_mode: Optional[str] = None
    vehicle_number: Optional[str] = None
    driver_name: Optional[str] = None
    notes: Optional[str] = None
    items: Optional[List[TransferItem]] = []


class StockTransferCreate(StockTransferBase):
    from_warehouse_id: str
    to_warehouse_id: str
    items: List[TransferItem]


class StockTransferUpdate(StockTransferBase):
    pass


class StockTransferResponse(StockTransferBase):
    id: str
    transfer_number: Optional[str] = None
    status: str = "pending"
    dispatched_at: Optional[str] = None
    dispatched_by: Optional[str] = None
    received_at: Optional[str] = None
    received_by: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


# ==================== STOCK ADJUSTMENT SCHEMAS ====================
class StockAdjustmentBase(BaseModel):
    warehouse_id: Optional[str] = None
    item_id: Optional[str] = None
    adjustment_type: Optional[str] = None
    qty: Optional[float] = None
    reason: Optional[str] = None
    reference: Optional[str] = None
    notes: Optional[str] = None


class StockAdjustmentCreate(StockAdjustmentBase):
    warehouse_id: str
    item_id: str
    adjustment_type: str
    qty: float


class StockAdjustmentUpdate(StockAdjustmentBase):
    pass


class StockAdjustmentResponse(StockAdjustmentBase):
    id: str
    adjustment_number: Optional[str] = None
    status: str = "pending"
    approved_at: Optional[str] = None
    approved_by: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


# ==================== BATCH SCHEMAS ====================
class BatchBase(BaseModel):
    item_id: Optional[str] = None
    warehouse_id: Optional[str] = None
    manufacturing_date: Optional[str] = None
    expiry_date: Optional[str] = None
    supplier_batch: Optional[str] = None
    qty: Optional[float] = None
    unit: str = "Pcs"
    notes: Optional[str] = None


class BatchCreate(BatchBase):
    item_id: str


class BatchResponse(BatchBase):
    id: str
    batch_number: Optional[str] = None
    created_at: Optional[str] = None
