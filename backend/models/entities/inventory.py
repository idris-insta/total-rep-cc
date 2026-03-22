"""
SQLAlchemy Entity Models - Inventory Module
"""
from sqlalchemy import Column, String, DateTime, Boolean, Text, Integer, Float, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime, timezone

from core.database import Base
from models.entities.base import UUIDMixin, TimestampMixin


class Item(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "items"
    
    item_code: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    item_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    item_type: Mapped[str] = mapped_column(String(50), default="finished_goods")  # raw_material, wip, finished_goods, consumable
    category: Mapped[str] = mapped_column(String(100), nullable=True, index=True)
    sub_category: Mapped[str] = mapped_column(String(100), nullable=True)
    hsn_code: Mapped[str] = mapped_column(String(20), nullable=True, index=True)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    
    # UOM
    uom: Mapped[str] = mapped_column(String(50), default="Nos")
    primary_uom: Mapped[str] = mapped_column(String(50), default="Pcs")
    secondary_uom: Mapped[str] = mapped_column(String(50), nullable=True)
    alternate_uom: Mapped[str] = mapped_column(String(50), nullable=True)
    conversion_factor: Mapped[float] = mapped_column(Float, default=1)
    
    # Pricing
    purchase_price: Mapped[float] = mapped_column(Float, default=0)
    cost_price: Mapped[float] = mapped_column(Float, nullable=True)
    selling_price: Mapped[float] = mapped_column(Float, default=0)
    min_selling_price: Mapped[float] = mapped_column(Float, nullable=True)
    margin_percent: Mapped[float] = mapped_column(Float, nullable=True)
    mrp: Mapped[float] = mapped_column(Float, nullable=True)
    
    # Stock
    stock_qty: Mapped[float] = mapped_column(Float, default=0)
    stock_kg: Mapped[float] = mapped_column(Float, default=0)
    stock_sqm: Mapped[float] = mapped_column(Float, default=0)
    reorder_level: Mapped[float] = mapped_column(Float, default=0)
    reorder_qty: Mapped[float] = mapped_column(Float, default=0)
    safety_stock: Mapped[float] = mapped_column(Float, nullable=True)
    min_qty: Mapped[float] = mapped_column(Float, default=0)
    max_qty: Mapped[float] = mapped_column(Float, nullable=True)
    lead_time_days: Mapped[int] = mapped_column(Integer, nullable=True)
    shelf_life_days: Mapped[int] = mapped_column(Integer, nullable=True)
    
    # Tax
    gst_rate: Mapped[float] = mapped_column(Float, default=18)
    cess_rate: Mapped[float] = mapped_column(Float, default=0)
    
    # Physical attributes (for adhesive tapes)
    base_material: Mapped[str] = mapped_column(String(100), nullable=True)
    adhesive_type: Mapped[str] = mapped_column(String(100), nullable=True)
    color: Mapped[str] = mapped_column(String(50), nullable=True)
    width: Mapped[float] = mapped_column(Float, nullable=True)
    width_mm: Mapped[float] = mapped_column(Float, nullable=True)
    length: Mapped[float] = mapped_column(Float, nullable=True)
    length_m: Mapped[float] = mapped_column(Float, nullable=True)
    thickness: Mapped[float] = mapped_column(Float, nullable=True)
    thickness_microns: Mapped[float] = mapped_column(Float, nullable=True)
    gsm: Mapped[float] = mapped_column(Float, nullable=True)
    core_diameter: Mapped[float] = mapped_column(Float, nullable=True)
    
    # Other
    barcode: Mapped[str] = mapped_column(String(100), nullable=True)
    notes: Mapped[str] = mapped_column(Text, nullable=True)
    
    # Flags
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_batch_tracked: Mapped[bool] = mapped_column(Boolean, default=False)
    is_serial_tracked: Mapped[bool] = mapped_column(Boolean, default=False)
    
    custom_fields: Mapped[dict] = mapped_column(JSONB, nullable=True)
    specifications: Mapped[dict] = mapped_column(JSONB, nullable=True)


class Warehouse(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "warehouses"
    
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    warehouse_type: Mapped[str] = mapped_column(String(50), default="storage")  # storage, production, transit
    address: Mapped[str] = mapped_column(Text, nullable=True)
    city: Mapped[str] = mapped_column(String(100), nullable=True)
    state: Mapped[str] = mapped_column(String(100), nullable=True)
    pincode: Mapped[str] = mapped_column(String(20), nullable=True)
    gstin: Mapped[str] = mapped_column(String(20), nullable=True)
    manager_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False)
    custom_fields: Mapped[dict] = mapped_column(JSONB, nullable=True)


class Stock(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "stock"
    
    item_id: Mapped[str] = mapped_column(String(36), ForeignKey("items.id"), nullable=False, index=True)
    warehouse_id: Mapped[str] = mapped_column(String(36), ForeignKey("warehouses.id"), nullable=False, index=True)
    qty: Mapped[float] = mapped_column(Float, default=0)
    reserved_qty: Mapped[float] = mapped_column(Float, default=0)
    available_qty: Mapped[float] = mapped_column(Float, default=0)
    batch_number: Mapped[str] = mapped_column(String(100), nullable=True)
    bin_location: Mapped[str] = mapped_column(String(100), nullable=True)
    
    __table_args__ = (
        # Composite unique constraint
        {'extend_existing': True},
    )


class StockTransfer(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "stock_transfers"
    
    transfer_number: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    from_warehouse_id: Mapped[str] = mapped_column(String(36), ForeignKey("warehouses.id"), nullable=False)
    to_warehouse_id: Mapped[str] = mapped_column(String(36), ForeignKey("warehouses.id"), nullable=False)
    transfer_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    status: Mapped[str] = mapped_column(String(50), default="pending", index=True)  # pending, in_transit, completed, cancelled
    items: Mapped[list] = mapped_column(JSONB, nullable=True)  # Array of transfer items
    notes: Mapped[str] = mapped_column(Text, nullable=True)
    approved_by: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    received_by: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    received_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)


class StockAdjustment(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "stock_adjustments"
    
    adjustment_number: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    warehouse_id: Mapped[str] = mapped_column(String(36), ForeignKey("warehouses.id"), nullable=False)
    adjustment_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    adjustment_type: Mapped[str] = mapped_column(String(50), default="physical_count")  # physical_count, damage, loss, write_off
    status: Mapped[str] = mapped_column(String(50), default="pending", index=True)
    items: Mapped[list] = mapped_column(JSONB, nullable=True)  # Array of adjustment items
    reason: Mapped[str] = mapped_column(Text, nullable=True)
    approved_by: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)


class Batch(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "batches"
    
    batch_number: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    item_id: Mapped[str] = mapped_column(String(36), ForeignKey("items.id"), nullable=False, index=True)
    warehouse_id: Mapped[str] = mapped_column(String(36), ForeignKey("warehouses.id"), nullable=True)
    manufacture_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    expiry_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    qty: Mapped[float] = mapped_column(Float, default=0)
    status: Mapped[str] = mapped_column(String(50), default="active")
    supplier_batch: Mapped[str] = mapped_column(String(100), nullable=True)
    attributes: Mapped[dict] = mapped_column(JSONB, nullable=True)


class BinLocation(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "bin_locations"
    
    warehouse_id: Mapped[str] = mapped_column(String(36), ForeignKey("warehouses.id"), nullable=False, index=True)
    bin_code: Mapped[str] = mapped_column(String(50), nullable=False)
    bin_name: Mapped[str] = mapped_column(String(100), nullable=True)
    zone: Mapped[str] = mapped_column(String(50), nullable=True)
    rack: Mapped[str] = mapped_column(String(50), nullable=True)
    level: Mapped[str] = mapped_column(String(50), nullable=True)
    position: Mapped[str] = mapped_column(String(50), nullable=True)
    capacity: Mapped[float] = mapped_column(Float, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class StockLedger(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "stock_ledger"
    
    item_id: Mapped[str] = mapped_column(String(36), ForeignKey("items.id"), nullable=False, index=True)
    warehouse_id: Mapped[str] = mapped_column(String(36), ForeignKey("warehouses.id"), nullable=False, index=True)
    transaction_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)
    transaction_type: Mapped[str] = mapped_column(String(50), nullable=False)  # purchase, sale, transfer_in, transfer_out, adjustment, production
    reference_type: Mapped[str] = mapped_column(String(50), nullable=True)  # grn, invoice, transfer, adjustment, work_order
    reference_id: Mapped[str] = mapped_column(String(36), nullable=True, index=True)
    qty_in: Mapped[float] = mapped_column(Float, default=0)
    qty_out: Mapped[float] = mapped_column(Float, default=0)
    balance_qty: Mapped[float] = mapped_column(Float, default=0)
    rate: Mapped[float] = mapped_column(Float, default=0)
    value: Mapped[float] = mapped_column(Float, default=0)
    batch_number: Mapped[str] = mapped_column(String(100), nullable=True)
    notes: Mapped[str] = mapped_column(Text, nullable=True)
