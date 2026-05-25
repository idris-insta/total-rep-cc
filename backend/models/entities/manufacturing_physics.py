"""
SQLAlchemy Entity Models - Manufacturing Physics Engine
Implements the 7-stage adhesive tape production flow:

  Stage 1 (Coating):    BOPP + Adhesive + Liner → Jumbo Roll (Semi-Finished WIP)
  Stage 2 (Converting): Jumbo Roll → Slitting / Rewinding → Finished Goods (Rolls)

Physics Engine:
  KG = SQM × thickness_m × density_kg_m3
     = SQM × (thickness_microns / 1e6) × (density_g_cm3 × 1000)

Redline Guard:
  scrap_percent = scrap_kg / input_kg × 100
  If scrap_percent > 7.0 → lock production → require Director-level override
"""
from sqlalchemy import String, DateTime, Boolean, Text, Integer, Float, ForeignKey, Index, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime, timezone

from core.database import Base
from models.entities.base import UUIDMixin, TimestampMixin

REDLINE_THRESHOLD_PCT = 7.0


# ==================== BILL OF MATERIALS ====================

class BillOfMaterials(Base, UUIDMixin, TimestampMixin):
    """
    BOM header linking a finished item to its raw-material recipe.
    Supports physics-driven quantity formulas alongside fixed quantities.
    """
    __tablename__ = "bom_headers"

    bom_number: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    item_id: Mapped[str] = mapped_column(String(36), ForeignKey("items.id"), nullable=False, index=True)
    variant_id: Mapped[str] = mapped_column(String(36), ForeignKey("item_variants.id"), nullable=True)

    output_qty: Mapped[float] = mapped_column(Float, default=1.0)
    output_uom: Mapped[str] = mapped_column(String(50), default="KG")

    # Physics parameters for output estimation
    thickness_microns: Mapped[float] = mapped_column(Float, nullable=True)
    density_g_cm3: Mapped[float] = mapped_column(Float, nullable=True)

    bom_type: Mapped[str] = mapped_column(String(50), default="manufacturing")   # manufacturing | sub_assembly
    stage: Mapped[str] = mapped_column(String(50), nullable=True)   # coating | slitting | rewinding
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_default: Mapped[bool] = mapped_column(Boolean, default=True)
    version: Mapped[int] = mapped_column(Integer, default=1)
    notes: Mapped[str] = mapped_column(Text, nullable=True)
    custom_fields: Mapped[dict] = mapped_column(JSONB, nullable=True)


class BOMItem(Base, UUIDMixin, TimestampMixin):
    """Raw-material / sub-assembly line in a BOM"""
    __tablename__ = "bom_items"

    bom_id: Mapped[str] = mapped_column(String(36), ForeignKey("bom_headers.id"), nullable=False, index=True)
    item_id: Mapped[str] = mapped_column(String(36), ForeignKey("items.id"), nullable=False, index=True)
    sequence: Mapped[int] = mapped_column(Integer, default=1)

    qty_per_unit: Mapped[float] = mapped_column(Float, nullable=False)
    uom: Mapped[str] = mapped_column(String(50), default="KG")

    # Optional physics formula string, e.g. "SQM * gsm / 1000"
    qty_formula: Mapped[str] = mapped_column(String(255), nullable=True)

    scrap_percent: Mapped[float] = mapped_column(Float, default=0)
    item_type: Mapped[str] = mapped_column(String(50), default="raw_material")
    # raw_material | sub_assembly | consumable | packing
    notes: Mapped[str] = mapped_column(Text, nullable=True)


# ==================== ADHESIVE MIX FORMULA ====================

class AdhesiveMixFormula(Base, UUIDMixin, TimestampMixin):
    """
    Adhesive mixing recipe. Coating Stage mixes components to a target
    viscosity / solid-content before applying to BOPP film.
    """
    __tablename__ = "adhesive_mix_formulas"

    formula_code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    formula_name: Mapped[str] = mapped_column(String(255), nullable=False)

    output_item_id: Mapped[str] = mapped_column(String(36), ForeignKey("items.id"), nullable=True)
    output_qty_kg: Mapped[float] = mapped_column(Float, default=100.0)   # per batch

    # Components: [{item_id, item_name, qty_kg, percentage, notes}]
    components: Mapped[list] = mapped_column(JSONB, nullable=True)

    # Quality targets
    viscosity_cps: Mapped[float] = mapped_column(Float, nullable=True)
    solid_content_percent: Mapped[float] = mapped_column(Float, nullable=True)
    ph_value: Mapped[float] = mapped_column(Float, nullable=True)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    version: Mapped[int] = mapped_column(Integer, default=1)
    notes: Mapped[str] = mapped_column(Text, nullable=True)


# ==================== STAGE 1 – COATING ====================

class CoatingOrder(Base, UUIDMixin, TimestampMixin):
    """
    Stage 1 production order on the Coating Line.
    Inputs : BOPP film roll + adhesive compound + release liner
    Output : Jumbo roll (semi-finished WIP)

    Physics target:
      target_output_kg = target_sqm × (thickness_microns/1e6) × (density_g_cm3 × 1000)

    Redline Guard:
      scrap_percent = scrap_kg / (bopp_input_kg) × 100
      If > 7.0 → redline_triggered = True → production locked until Director override
    """
    __tablename__ = "coating_orders"

    co_number: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    work_order_id: Mapped[str] = mapped_column(String(36), ForeignKey("work_orders.id"), nullable=True, index=True)
    machine_id: Mapped[str] = mapped_column(String(36), ForeignKey("machines.id"), nullable=True, index=True)

    planned_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="planned", index=True)
    # planned | mixing | coating | drying | inspection | completed | on_hold | cancelled

    # Input materials
    bopp_item_id: Mapped[str] = mapped_column(String(36), ForeignKey("items.id"), nullable=True)
    bopp_roll_width_mm: Mapped[float] = mapped_column(Float, nullable=True)
    bopp_input_kg: Mapped[float] = mapped_column(Float, default=0)
    bopp_input_sqm: Mapped[float] = mapped_column(Float, default=0)

    adhesive_formula_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("adhesive_mix_formulas.id"), nullable=True
    )
    adhesive_input_kg: Mapped[float] = mapped_column(Float, default=0)

    liner_item_id: Mapped[str] = mapped_column(String(36), ForeignKey("items.id"), nullable=True)
    liner_input_kg: Mapped[float] = mapped_column(Float, default=0)

    # Physics targets
    target_thickness_microns: Mapped[float] = mapped_column(Float, nullable=True)
    target_coating_gsm: Mapped[float] = mapped_column(Float, nullable=True)
    target_sqm: Mapped[float] = mapped_column(Float, nullable=True)
    target_output_kg: Mapped[float] = mapped_column(Float, nullable=True)

    # Actuals – filled as production progresses
    actual_output_kg: Mapped[float] = mapped_column(Float, default=0)
    actual_output_sqm: Mapped[float] = mapped_column(Float, default=0)
    scrap_kg: Mapped[float] = mapped_column(Float, default=0)
    scrap_percent: Mapped[float] = mapped_column(Float, default=0)

    # Redline Guard (threshold = 7%)
    redline_triggered: Mapped[bool] = mapped_column(Boolean, default=False)
    redline_override_by: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    redline_override_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    redline_override_reason: Mapped[str] = mapped_column(Text, nullable=True)

    # Output jumbo roll reference
    jumbo_roll_batch: Mapped[str] = mapped_column(String(100), nullable=True, index=True)
    jumbo_item_id: Mapped[str] = mapped_column(String(36), ForeignKey("items.id"), nullable=True)

    shift: Mapped[str] = mapped_column(String(20), nullable=True)    # morning | evening | night
    operator_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    supervisor_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)

    qc_passed: Mapped[bool] = mapped_column(Boolean, nullable=True)
    qc_params: Mapped[dict] = mapped_column(JSONB, nullable=True)
    notes: Mapped[str] = mapped_column(Text, nullable=True)
    custom_fields: Mapped[dict] = mapped_column(JSONB, nullable=True)


class JumboRoll(Base, UUIDMixin, TimestampMixin):
    """
    Jumbo Roll – semi-finished WIP output from the Coating Stage.
    This is the primary input for Stage 2 (Slitting / Converting).
    """
    __tablename__ = "jumbo_rolls"

    batch_number: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    coating_order_id: Mapped[str] = mapped_column(String(36), ForeignKey("coating_orders.id"), nullable=True)
    item_id: Mapped[str] = mapped_column(String(36), ForeignKey("items.id"), nullable=False, index=True)

    roll_width_mm: Mapped[float] = mapped_column(Float, nullable=False)
    roll_length_m: Mapped[float] = mapped_column(Float, nullable=True)
    thickness_microns: Mapped[float] = mapped_column(Float, nullable=True)
    gross_weight_kg: Mapped[float] = mapped_column(Float, default=0)
    core_weight_kg: Mapped[float] = mapped_column(Float, default=0)
    net_weight_kg: Mapped[float] = mapped_column(Float, default=0)
    sqm: Mapped[float] = mapped_column(Float, default=0)

    status: Mapped[str] = mapped_column(String(50), default="in_stock", index=True)
    # in_stock | reserved | consumed | scrapped
    warehouse_id: Mapped[str] = mapped_column(String(36), ForeignKey("warehouses.id"), nullable=True)

    manufacture_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    expiry_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)

    qc_approved: Mapped[bool] = mapped_column(Boolean, nullable=True)
    qc_inspector_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    qc_params: Mapped[dict] = mapped_column(JSONB, nullable=True)
    notes: Mapped[str] = mapped_column(Text, nullable=True)


# ==================== STAGE 2 – SLITTING / CONVERTING ====================

class SlittingOrder(Base, UUIDMixin, TimestampMixin):
    """
    Stage 2 production order – Slitting / Rewinding / Converting.
    Input : Jumbo roll(s) from Stage 1
    Output: Finished-goods rolls at target width × length

    Physics expectation:
      expected_output_kg = target_rolls × weight_per_roll_kg  (from ItemVariant)

    Redline Guard:
      scrap_percent = (scrap_kg + edge_trim_kg) / total_input_kg × 100
      If > 7.0 → redline_triggered = True → Director override required
    """
    __tablename__ = "slitting_orders"

    so_number: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    work_order_id: Mapped[str] = mapped_column(String(36), ForeignKey("work_orders.id"), nullable=True, index=True)
    machine_id: Mapped[str] = mapped_column(String(36), ForeignKey("machines.id"), nullable=True, index=True)

    planned_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="planned", index=True)
    # planned | in_progress | completed | on_hold | cancelled

    # Input jumbo rolls: [{jumbo_roll_id, batch_number, qty_kg, sqm}]
    input_jumbo_rolls: Mapped[list] = mapped_column(JSONB, nullable=True)
    total_input_kg: Mapped[float] = mapped_column(Float, default=0)
    total_input_sqm: Mapped[float] = mapped_column(Float, default=0)

    # Target finished-goods specification
    target_item_id: Mapped[str] = mapped_column(String(36), ForeignKey("items.id"), nullable=True)
    target_variant_id: Mapped[str] = mapped_column(String(36), ForeignKey("item_variants.id"), nullable=True)
    target_width_mm: Mapped[float] = mapped_column(Float, nullable=False)
    target_length_m: Mapped[float] = mapped_column(Float, nullable=False)
    target_rolls: Mapped[int] = mapped_column(Integer, nullable=True)

    expected_output_kg: Mapped[float] = mapped_column(Float, nullable=True)
    expected_output_sqm: Mapped[float] = mapped_column(Float, nullable=True)

    # Actuals
    actual_output_rolls: Mapped[int] = mapped_column(Integer, default=0)
    actual_output_kg: Mapped[float] = mapped_column(Float, default=0)
    scrap_kg: Mapped[float] = mapped_column(Float, default=0)
    edge_trim_kg: Mapped[float] = mapped_column(Float, default=0)
    scrap_percent: Mapped[float] = mapped_column(Float, default=0)

    # Redline Guard
    redline_triggered: Mapped[bool] = mapped_column(Boolean, default=False)
    redline_override_by: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    redline_override_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    redline_override_reason: Mapped[str] = mapped_column(Text, nullable=True)

    # Slitting lane plan: [{lane, width_mm, rolls_count}]
    slitting_plan: Mapped[list] = mapped_column(JSONB, nullable=True)

    output_batch: Mapped[str] = mapped_column(String(100), nullable=True, index=True)
    output_warehouse_id: Mapped[str] = mapped_column(String(36), ForeignKey("warehouses.id"), nullable=True)

    shift: Mapped[str] = mapped_column(String(20), nullable=True)
    operator_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    supervisor_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)

    qc_params: Mapped[dict] = mapped_column(JSONB, nullable=True)
    notes: Mapped[str] = mapped_column(Text, nullable=True)
    custom_fields: Mapped[dict] = mapped_column(JSONB, nullable=True)


class ProductionShiftLog(Base, UUIDMixin, TimestampMixin):
    """Shift-level production telemetry – links to a coating or slitting order"""
    __tablename__ = "production_shift_logs"

    shift_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    shift: Mapped[str] = mapped_column(String(20), nullable=False)
    machine_id: Mapped[str] = mapped_column(String(36), ForeignKey("machines.id"), nullable=True, index=True)
    stage: Mapped[str] = mapped_column(String(50), nullable=False)   # coating | slitting | rewinding

    reference_type: Mapped[str] = mapped_column(String(50), nullable=True)   # coating_order | slitting_order
    reference_id: Mapped[str] = mapped_column(String(36), nullable=True)

    operator_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    start_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    end_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)

    input_kg: Mapped[float] = mapped_column(Float, default=0)
    output_kg: Mapped[float] = mapped_column(Float, default=0)
    scrap_kg: Mapped[float] = mapped_column(Float, default=0)
    scrap_percent: Mapped[float] = mapped_column(Float, default=0)
    downtime_minutes: Mapped[int] = mapped_column(Integer, default=0)
    downtime_reason: Mapped[str] = mapped_column(Text, nullable=True)
    redline_flag: Mapped[bool] = mapped_column(Boolean, default=False)

    shift_params: Mapped[dict] = mapped_column(JSONB, nullable=True)
    notes: Mapped[str] = mapped_column(Text, nullable=True)


class ScrapEntry(Base, UUIDMixin, TimestampMixin):
    """
    Scrap/wastage capture per production event.
    Feeds the Redline Guard calculation.
    scrap_percent = scrap_kg / input_kg × 100
    threshold = 7% (REDLINE_THRESHOLD_PCT constant above)
    """
    __tablename__ = "scrap_entries"

    entry_number: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    entry_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    reference_type: Mapped[str] = mapped_column(String(50), nullable=True)
    # coating_order | slitting_order | production_entry
    reference_id: Mapped[str] = mapped_column(String(36), nullable=True, index=True)

    stage: Mapped[str] = mapped_column(String(50), nullable=True)
    scrap_type: Mapped[str] = mapped_column(String(100), nullable=True)
    # edge_trim | tail_end | startup_waste | defect | splice

    scrap_kg: Mapped[float] = mapped_column(Float, default=0)
    scrap_sqm: Mapped[float] = mapped_column(Float, default=0)
    input_kg: Mapped[float] = mapped_column(Float, default=0)
    scrap_percent: Mapped[float] = mapped_column(Float, default=0)

    exceeds_threshold: Mapped[bool] = mapped_column(Boolean, default=False)
    threshold_percent: Mapped[float] = mapped_column(Float, default=REDLINE_THRESHOLD_PCT)
    production_locked: Mapped[bool] = mapped_column(Boolean, default=False)
    override_by: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    override_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)

    disposal_method: Mapped[str] = mapped_column(String(100), nullable=True)
    disposal_value: Mapped[float] = mapped_column(Float, default=0)

    notes: Mapped[str] = mapped_column(Text, nullable=True)
    recorded_by: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
