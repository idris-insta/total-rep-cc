"""
SQLAlchemy Entity Models - Full Procurement Chain
Extends the basic procurement in procurement.py with the complete chain:
  PurchaseIndent → PurchaseEnquiry → VendorQuotation →
  (purchase_orders – existing table in procurement.py) →
  GoodsReceivedNote → PurchaseInvoice → LandedCostVoucher

Note: PurchaseOrder (table: purchase_orders) lives in procurement.py.
      We FK-reference purchase_orders.id from the new tables here.
"""
from sqlalchemy import String, DateTime, Boolean, Text, Integer, Float, ForeignKey, UniqueConstraint, Index
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime, timezone

from core.database import Base
from models.entities.base import UUIDMixin, TimestampMixin


# ==================== PURCHASE INDENT ====================

class PurchaseIndent(Base, UUIDMixin, TimestampMixin):
    """
    Internal material request raised by department / production floor.
    First link in the procurement chain.
    """
    __tablename__ = "purchase_indents"

    indent_number: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    indent_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    requested_by: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    department: Mapped[str] = mapped_column(String(100), nullable=True)
    branch_id: Mapped[str] = mapped_column(String(36), ForeignKey("branches.id"), nullable=True)
    cost_center_id: Mapped[str] = mapped_column(String(36), ForeignKey("cost_centers.id"), nullable=True)
    warehouse_id: Mapped[str] = mapped_column(String(36), ForeignKey("warehouses.id"), nullable=True)

    required_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    priority: Mapped[str] = mapped_column(String(20), default="normal")   # low | normal | high | urgent

    # [{item_id, item_name, qty, uom, purpose, available_stock, remarks}]
    items: Mapped[list] = mapped_column(JSONB, nullable=True)

    status: Mapped[str] = mapped_column(String(50), default="pending", index=True)
    # pending | approved | enquiry_raised | ordered | received | cancelled

    approved_by: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    approved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    rejection_reason: Mapped[str] = mapped_column(Text, nullable=True)

    work_order_id: Mapped[str] = mapped_column(String(36), ForeignKey("work_orders.id"), nullable=True)

    notes: Mapped[str] = mapped_column(Text, nullable=True)
    custom_fields: Mapped[dict] = mapped_column(JSONB, nullable=True)


# ==================== PURCHASE ENQUIRY ====================

class PurchaseEnquiry(Base, UUIDMixin, TimestampMixin):
    """RFQ (Request for Quotation) sent to multiple vendors simultaneously"""
    __tablename__ = "purchase_enquiries"

    enquiry_number: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    enquiry_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    indent_id: Mapped[str] = mapped_column(String(36), ForeignKey("purchase_indents.id"), nullable=True, index=True)
    branch_id: Mapped[str] = mapped_column(String(36), ForeignKey("branches.id"), nullable=True)

    # [{item_id, item_name, qty, uom, specifications, target_price}]
    items: Mapped[list] = mapped_column(JSONB, nullable=True)

    # Vendors contacted: [{account_id, vendor_name, email, sent_at, status}]
    vendors: Mapped[list] = mapped_column(JSONB, nullable=True)

    response_due_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)

    status: Mapped[str] = mapped_column(String(50), default="sent", index=True)
    # draft | sent | responses_received | compared | converted | cancelled

    created_by: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    notes: Mapped[str] = mapped_column(Text, nullable=True)


# ==================== VENDOR QUOTATION ====================

class VendorQuotation(Base, UUIDMixin, TimestampMixin):
    """
    Vendor's response to a purchase enquiry.
    Multiple VendorQuotations per PurchaseEnquiry enable comparison.
    is_selected = True marks the winning quote that becomes a PO.
    """
    __tablename__ = "vendor_quotations"

    quotation_number: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    enquiry_id: Mapped[str] = mapped_column(String(36), ForeignKey("purchase_enquiries.id"), nullable=True, index=True)
    vendor_id: Mapped[str] = mapped_column(String(36), ForeignKey("accounts.id"), nullable=False, index=True)

    quote_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    valid_until: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)

    # [{item_id, qty, uom, rate, gst_rate, total, delivery_days, remarks}]
    items: Mapped[list] = mapped_column(JSONB, nullable=True)

    subtotal: Mapped[float] = mapped_column(Float, default=0)
    tax_amount: Mapped[float] = mapped_column(Float, default=0)
    freight: Mapped[float] = mapped_column(Float, default=0)
    grand_total: Mapped[float] = mapped_column(Float, default=0)

    delivery_days: Mapped[int] = mapped_column(Integer, nullable=True)
    payment_terms: Mapped[str] = mapped_column(String(255), nullable=True)

    status: Mapped[str] = mapped_column(String(50), default="received", index=True)
    # received | shortlisted | selected | rejected

    is_selected: Mapped[bool] = mapped_column(Boolean, default=False)
    selection_reason: Mapped[str] = mapped_column(Text, nullable=True)
    attachments: Mapped[list] = mapped_column(JSONB, nullable=True)
    notes: Mapped[str] = mapped_column(Text, nullable=True)


# ==================== GOODS RECEIVED NOTE ====================

class GoodsReceivedNote(Base, UUIDMixin, TimestampMixin):
    """
    GRN – records physical receipt of goods from a vendor.
    Triggers:
      • Stock in-movement (StockLedger entry)
      • QC inspection creation
      • Purchase Invoice linkage (3-way match: PO ↔ GRN ↔ Invoice)

    References purchase_orders table (procurement.py).
    """
    __tablename__ = "goods_received_notes"

    grn_number: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    grn_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True
    )

    po_id: Mapped[str] = mapped_column(String(36), ForeignKey("purchase_orders.id"), nullable=True, index=True)
    vendor_id: Mapped[str] = mapped_column(String(36), ForeignKey("accounts.id"), nullable=False, index=True)
    warehouse_id: Mapped[str] = mapped_column(String(36), ForeignKey("warehouses.id"), nullable=False)
    branch_id: Mapped[str] = mapped_column(String(36), ForeignKey("branches.id"), nullable=True)

    # Vendor delivery documents
    vendor_invoice_number: Mapped[str] = mapped_column(String(100), nullable=True)
    lr_number: Mapped[str] = mapped_column(String(100), nullable=True)          # Lorry Receipt
    lr_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    vehicle_number: Mapped[str] = mapped_column(String(50), nullable=True)
    transporter: Mapped[str] = mapped_column(String(255), nullable=True)

    # [{item_id, item_name, po_qty, received_qty, accepted_qty, rejected_qty,
    #   uom, rate, batch_number, bin_location, qc_status, remarks}]
    items: Mapped[list] = mapped_column(JSONB, nullable=True)

    total_received_qty: Mapped[float] = mapped_column(Float, default=0)
    total_accepted_qty: Mapped[float] = mapped_column(Float, default=0)
    total_rejected_qty: Mapped[float] = mapped_column(Float, default=0)

    subtotal: Mapped[float] = mapped_column(Float, default=0)
    tax_amount: Mapped[float] = mapped_column(Float, default=0)
    grand_total: Mapped[float] = mapped_column(Float, default=0)

    status: Mapped[str] = mapped_column(String(50), default="pending_qc", index=True)
    # pending_qc | qc_done | accepted | partially_accepted | rejected | billed

    received_by: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    qc_done_by: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    qc_done_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    stock_ledger_created: Mapped[bool] = mapped_column(Boolean, default=False)

    attachments: Mapped[list] = mapped_column(JSONB, nullable=True)
    notes: Mapped[str] = mapped_column(Text, nullable=True)
    custom_fields: Mapped[dict] = mapped_column(JSONB, nullable=True)


# ==================== PURCHASE INVOICE (ACCOUNTS PAYABLE) ====================

class PurchaseInvoice(Base, UUIDMixin, TimestampMixin):
    """
    Purchase Invoice – accounts payable document.
    Supports:
      • GST (CGST / SGST / IGST) with place-of-supply logic
      • TDS on service invoices (Sec 194C, 194J, 194H, etc.)
      • 3-way match: PO ↔ GRN ↔ Invoice
      • Maker-Approver workflow
    """
    __tablename__ = "purchase_invoices"

    invoice_number: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    vendor_invoice_number: Mapped[str] = mapped_column(String(100), nullable=True, index=True)
    invoice_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True
    )
    due_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)

    vendor_id: Mapped[str] = mapped_column(String(36), ForeignKey("accounts.id"), nullable=False, index=True)
    grn_id: Mapped[str] = mapped_column(String(36), ForeignKey("goods_received_notes.id"), nullable=True)
    po_id: Mapped[str] = mapped_column(String(36), ForeignKey("purchase_orders.id"), nullable=True)
    branch_id: Mapped[str] = mapped_column(String(36), ForeignKey("branches.id"), nullable=True)
    cost_center_id: Mapped[str] = mapped_column(String(36), ForeignKey("cost_centers.id"), nullable=True)

    invoice_type: Mapped[str] = mapped_column(String(50), default="goods")   # goods | service | both | expense

    # [{item_id, qty, uom, rate, hsn, gst_rate, cgst, sgst, igst, total}]
    items: Mapped[list] = mapped_column(JSONB, nullable=True)

    # GST amounts
    subtotal: Mapped[float] = mapped_column(Float, default=0)
    cgst_amount: Mapped[float] = mapped_column(Float, default=0)
    sgst_amount: Mapped[float] = mapped_column(Float, default=0)
    igst_amount: Mapped[float] = mapped_column(Float, default=0)
    cess_amount: Mapped[float] = mapped_column(Float, default=0)
    tax_amount: Mapped[float] = mapped_column(Float, default=0)
    place_of_supply: Mapped[str] = mapped_column(String(100), nullable=True)
    reverse_charge: Mapped[bool] = mapped_column(Boolean, default=False)

    # TDS (service invoices)
    tds_applicable: Mapped[bool] = mapped_column(Boolean, default=False)
    tds_section: Mapped[str] = mapped_column(String(20), nullable=True)    # 194C | 194J | 194H
    tds_rate_percent: Mapped[float] = mapped_column(Float, default=0)
    tds_amount: Mapped[float] = mapped_column(Float, default=0)

    grand_total: Mapped[float] = mapped_column(Float, default=0)
    paid_amount: Mapped[float] = mapped_column(Float, default=0)
    balance_amount: Mapped[float] = mapped_column(Float, default=0)

    status: Mapped[str] = mapped_column(String(50), default="pending_approval", index=True)
    # draft | pending_approval | approved | partially_paid | paid | overdue | cancelled

    # Maker-Approver
    maker_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    approver_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    approved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)

    gl_posted: Mapped[bool] = mapped_column(Boolean, default=False)
    gl_posted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)

    attachments: Mapped[list] = mapped_column(JSONB, nullable=True)
    notes: Mapped[str] = mapped_column(Text, nullable=True)
    internal_notes: Mapped[str] = mapped_column(Text, nullable=True)
    custom_fields: Mapped[dict] = mapped_column(JSONB, nullable=True)


# ==================== LANDED COST VOUCHER ====================

class LandedCostVoucher(Base, UUIDMixin, TimestampMixin):
    """
    Allocates additional acquisition costs (freight, insurance, customs, handling)
    across GRN items. Updates effective item cost rate in the stock ledger.

    Distribution methods:
      by_value  – proportional to item line value
      by_weight – proportional to item weight (KG)
      by_qty    – proportional to quantity
      equal     – equal share per item line
    """
    __tablename__ = "landed_cost_vouchers"

    lcv_number: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    lcv_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    grn_ids: Mapped[list] = mapped_column(JSONB, nullable=True)   # [grn_id, ...]
    vendor_id: Mapped[str] = mapped_column(String(36), ForeignKey("accounts.id"), nullable=True)

    # [{component, amount, account_id}]
    # component: freight | insurance | customs_duty | clearing_charges | other
    cost_components: Mapped[list] = mapped_column(JSONB, nullable=True)

    total_landed_cost: Mapped[float] = mapped_column(Float, default=0)
    distribution_method: Mapped[str] = mapped_column(String(50), default="by_value")

    # [{grn_id, item_id, base_amount, allocated_cost, new_cost_rate}]
    item_allocations: Mapped[list] = mapped_column(JSONB, nullable=True)

    status: Mapped[str] = mapped_column(String(50), default="draft", index=True)
    # draft | submitted | posted | cancelled

    posted_by: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    posted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    notes: Mapped[str] = mapped_column(Text, nullable=True)
