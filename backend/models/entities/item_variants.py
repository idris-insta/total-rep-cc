"""
SQLAlchemy Entity Models - SKU Variants & Multi-UOM System
Implements:
  - ItemGroup / SubGroup hierarchy with unlimited nesting
  - SKU template format: IS-51110V-045WHNANL  (width & length as variants, NOT in SKU)
  - ItemVariant: each unique width × length combination is a separate variant
  - Multi-UOM profile: Buying (Tons) / Stocking (KG) / Selling (Rolls or Boxes)
  - UOM conversion factor table with item-level overrides
  - Price Lists per branch / customer group with volume tiers
"""
from sqlalchemy import String, DateTime, Boolean, Text, Integer, Float, ForeignKey, UniqueConstraint, Index
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime, timezone

from core.database import Base
from models.entities.base import UUIDMixin, TimestampMixin


# ==================== ITEM GROUP HIERARCHY ====================

class ItemGroup(Base, UUIDMixin, TimestampMixin):
    """
    Unlimited multi-level product group hierarchy.
    Groups can be tagged to a ProductLine for dimensional reporting.
    product_lines table is created by dimensional_gl.py.
    """
    __tablename__ = "item_groups"

    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    parent_id: Mapped[str] = mapped_column(String(36), ForeignKey("item_groups.id"), nullable=True)
    is_group: Mapped[bool] = mapped_column(Boolean, default=False)
    product_line_id: Mapped[str] = mapped_column(String(36), ForeignKey("product_lines.id"), nullable=True)
    default_gst_rate: Mapped[float] = mapped_column(Float, default=18.0)
    default_hsn: Mapped[str] = mapped_column(String(20), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    custom_fields: Mapped[dict] = mapped_column(JSONB, nullable=True)


# ==================== UOM MASTER & CONVERSIONS ====================

class UOMConversion(Base, UUIDMixin, TimestampMixin):
    """
    Unit of Measure conversion factors.
    item_id=NULL  → global rule (e.g. 1 Ton = 1000 KG for all items)
    item_id=set   → item-specific override
    to_uom = from_uom × factor
    """
    __tablename__ = "uom_conversions"

    item_id: Mapped[str] = mapped_column(String(36), ForeignKey("items.id"), nullable=True, index=True)
    from_uom: Mapped[str] = mapped_column(String(50), nullable=False)
    to_uom: Mapped[str] = mapped_column(String(50), nullable=False)
    factor: Mapped[float] = mapped_column(Float, nullable=False)
    notes: Mapped[str] = mapped_column(Text, nullable=True)

    __table_args__ = (
        UniqueConstraint("item_id", "from_uom", "to_uom", name="uq_uom_conv_item_pair"),
    )


class ItemUOMProfile(Base, UUIDMixin, TimestampMixin):
    """
    Per-item UOM profile capturing the three-UOM pattern:
      buying_uom  (Tons)  → supplier invoices this unit
      stocking_uom (KG)   → warehouse tracks in this unit
      selling_uom  (Rolls / Boxes) → customer orders this unit
    """
    __tablename__ = "item_uom_profiles"

    item_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("items.id"), unique=True, nullable=False, index=True
    )

    buying_uom: Mapped[str] = mapped_column(String(50), default="Tons")
    stocking_uom: Mapped[str] = mapped_column(String(50), default="KG")
    selling_uom: Mapped[str] = mapped_column(String(50), default="Rolls")

    # buying → stocking:  1 Ton = 1000 KG
    buying_to_stocking_factor: Mapped[float] = mapped_column(Float, default=1000.0)

    # stocking → selling: KG / weight_per_roll_kg = Rolls
    weight_per_roll_kg: Mapped[float] = mapped_column(Float, nullable=True)
    rolls_per_box: Mapped[int] = mapped_column(Integer, nullable=True)
    selling_uom_alt: Mapped[str] = mapped_column(String(50), nullable=True)   # "Boxes"

    notes: Mapped[str] = mapped_column(Text, nullable=True)


# ==================== SKU TEMPLATE & VARIANTS ====================

class ItemSKUTemplate(Base, UUIDMixin, TimestampMixin):
    """
    SKU Template – the base product code without dimensional variants.
    Example: IS-51110V-045WHNANL
      IS   = brand prefix
      51110 = spec/grade code
      V     = version
      045   = thickness (microns)
      WHNANL = attribute flags (White, Non-Abrasive, Non-Adhesive, etc.)

    Width and length are NOT encoded in the template.
    They live in ItemVariant (each variant = one width × length combo).
    """
    __tablename__ = "item_sku_templates"

    sku_code: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    item_id: Mapped[str] = mapped_column(String(36), ForeignKey("items.id"), nullable=False, index=True)

    # Decoded SKU segments stored as JSONB for flexibility
    # e.g. {"brand":"IS","spec":"51110","version":"V","micron":"045","attrs":"WHNANL"}
    sku_segments: Mapped[dict] = mapped_column(JSONB, nullable=True)

    # Physical defaults for this template
    base_material: Mapped[str] = mapped_column(String(100), nullable=True)   # BOPP, PVC, PP, Foam
    adhesive_type: Mapped[str] = mapped_column(String(100), nullable=True)   # Hot melt, Solvent, Water-based
    color: Mapped[str] = mapped_column(String(50), nullable=True)
    thickness_microns: Mapped[float] = mapped_column(Float, nullable=True)
    gsm: Mapped[float] = mapped_column(Float, nullable=True)                 # coat weight g/m²
    core_diameter_mm: Mapped[float] = mapped_column(Float, nullable=True)
    density_g_cm3: Mapped[float] = mapped_column(Float, nullable=True)       # for physics engine

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    notes: Mapped[str] = mapped_column(Text, nullable=True)


class ItemVariant(Base, UUIDMixin, TimestampMixin):
    """
    Dimensional variant of a SKU template.
    Variant axes: width_mm × length_m.
    variant_code = sku_code + "-" + width_mm + "x" + length_m (auto-generated on insert).

    Physics is pre-computed here for fast lookups during production planning:
      sqm_per_roll     = (width_mm / 1000) × length_m
      weight_per_roll_kg = sqm_per_roll × (thickness_microns / 1e6) × density_kg_m3
                         = sqm_per_roll × thickness_microns × density_g_cm3 / 1000
    """
    __tablename__ = "item_variants"

    sku_template_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("item_sku_templates.id"), nullable=False, index=True
    )
    item_id: Mapped[str] = mapped_column(String(36), ForeignKey("items.id"), nullable=False, index=True)
    variant_code: Mapped[str] = mapped_column(String(150), unique=True, nullable=False, index=True)

    width_mm: Mapped[float] = mapped_column(Float, nullable=False)
    length_m: Mapped[float] = mapped_column(Float, nullable=False)

    # Pre-computed physics
    sqm_per_roll: Mapped[float] = mapped_column(Float, nullable=True)
    weight_per_roll_kg: Mapped[float] = mapped_column(Float, nullable=True)

    # Pricing per variant
    purchase_price: Mapped[float] = mapped_column(Float, default=0)
    selling_price: Mapped[float] = mapped_column(Float, default=0)
    mrp: Mapped[float] = mapped_column(Float, nullable=True)

    # Stock
    stock_rolls: Mapped[float] = mapped_column(Float, default=0)
    stock_kg: Mapped[float] = mapped_column(Float, default=0)

    barcode: Mapped[str] = mapped_column(String(100), nullable=True, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    custom_fields: Mapped[dict] = mapped_column(JSONB, nullable=True)

    __table_args__ = (
        UniqueConstraint("sku_template_id", "width_mm", "length_m", name="uq_variant_dims"),
    )


# ==================== PRICE LISTS ====================

class PriceList(Base, UUIDMixin, TimestampMixin):
    """Named price list – branch-specific or customer-group-specific"""
    __tablename__ = "price_lists"

    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    currency: Mapped[str] = mapped_column(String(10), default="INR")
    price_list_type: Mapped[str] = mapped_column(String(20), default="selling")   # selling | buying
    branch_id: Mapped[str] = mapped_column(String(36), ForeignKey("branches.id"), nullable=True)
    valid_from: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    valid_to: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    notes: Mapped[str] = mapped_column(Text, nullable=True)


class PriceListItem(Base, UUIDMixin, TimestampMixin):
    """Rate for a specific item/variant in a price list with optional min-qty tier"""
    __tablename__ = "price_list_items"

    price_list_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("price_lists.id"), nullable=False, index=True
    )
    item_id: Mapped[str] = mapped_column(String(36), ForeignKey("items.id"), nullable=True)
    variant_id: Mapped[str] = mapped_column(String(36), ForeignKey("item_variants.id"), nullable=True)
    uom: Mapped[str] = mapped_column(String(50), default="Rolls")
    rate: Mapped[float] = mapped_column(Float, nullable=False)
    min_qty: Mapped[float] = mapped_column(Float, default=0)
    discount_percent: Mapped[float] = mapped_column(Float, default=0)

    __table_args__ = (
        Index("ix_pli_list_item_variant", "price_list_id", "item_id", "variant_id"),
    )
