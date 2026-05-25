"""
SQLAlchemy Entity Models - Dimensional General Ledger
Implements Dimensional Accounting: CostCenter, Project, ProductLine dimensions
mapped to every GL transaction for P&L / Balance Sheet MIS by dimension.

Note: Branch model lives in other.py (table: branches). We FK-reference it here.
"""
from sqlalchemy import String, DateTime, Boolean, Text, Integer, Float, ForeignKey, Index
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime, timezone

from core.database import Base
from models.entities.base import UUIDMixin, TimestampMixin


# ==================== ACCOUNTING DIMENSIONS ====================

class CostCenter(Base, UUIDMixin, TimestampMixin):
    """Cost Centre – e.g. BWD Plant, SGM Plant, HO Admin"""
    __tablename__ = "cost_centers"

    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    parent_id: Mapped[str] = mapped_column(String(36), ForeignKey("cost_centers.id"), nullable=True)
    branch_id: Mapped[str] = mapped_column(String(36), ForeignKey("branches.id"), nullable=True)
    is_group: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    budget_amount: Mapped[float] = mapped_column(Float, default=0)
    custom_fields: Mapped[dict] = mapped_column(JSONB, nullable=True)


class Project(Base, UUIDMixin, TimestampMixin):
    """Project dimension for dimensional P&L tracking"""
    __tablename__ = "projects"

    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    project_type: Mapped[str] = mapped_column(String(50), nullable=True)   # capex, opex, r_and_d
    start_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    end_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    budget_amount: Mapped[float] = mapped_column(Float, default=0)
    actual_spend: Mapped[float] = mapped_column(Float, default=0)
    status: Mapped[str] = mapped_column(String(50), default="active")
    manager_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    branch_id: Mapped[str] = mapped_column(String(36), ForeignKey("branches.id"), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    custom_fields: Mapped[dict] = mapped_column(JSONB, nullable=True)


class ProductLine(Base, UUIDMixin, TimestampMixin):
    """Product Line dimension – BOPP Tape, Foam Tape, Masking Tape, etc."""
    __tablename__ = "product_lines"

    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    custom_fields: Mapped[dict] = mapped_column(JSONB, nullable=True)


# ==================== ENHANCED GENERAL LEDGER ====================

class GeneralLedger(Base, UUIDMixin, TimestampMixin):
    """
    Core GL transaction table with full dimensional mapping.
    Every financial event posts here with dimension tags (branch, cost_center,
    project, product_line) enabling P&L and Balance Sheet MIS by any dimension.
    """
    __tablename__ = "general_ledger"

    posting_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    fiscal_year: Mapped[str] = mapped_column(String(10), nullable=False, index=True)   # "2024-25"
    fiscal_period: Mapped[int] = mapped_column(Integer, nullable=False)                # 1-12

    voucher_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    # sales_invoice | purchase_invoice | payment | receipt | journal | stock | payroll | depreciation
    voucher_number: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    voucher_id: Mapped[str] = mapped_column(String(36), nullable=True, index=True)

    account_id: Mapped[str] = mapped_column(String(36), ForeignKey("chart_of_accounts.id"), nullable=False, index=True)
    account_code: Mapped[str] = mapped_column(String(50), nullable=False)
    account_name: Mapped[str] = mapped_column(String(255), nullable=False)

    debit: Mapped[float] = mapped_column(Float, default=0, nullable=False)
    credit: Mapped[float] = mapped_column(Float, default=0, nullable=False)
    balance: Mapped[float] = mapped_column(Float, default=0)   # denormalized running balance

    # ---- DIMENSION TAGS ----
    branch_id: Mapped[str] = mapped_column(String(36), ForeignKey("branches.id"), nullable=True, index=True)
    cost_center_id: Mapped[str] = mapped_column(String(36), ForeignKey("cost_centers.id"), nullable=True, index=True)
    project_id: Mapped[str] = mapped_column(String(36), ForeignKey("projects.id"), nullable=True, index=True)
    product_line_id: Mapped[str] = mapped_column(String(36), ForeignKey("product_lines.id"), nullable=True, index=True)

    party_type: Mapped[str] = mapped_column(String(50), nullable=True)     # Customer | Supplier | Employee
    party_id: Mapped[str] = mapped_column(String(36), nullable=True, index=True)
    party_name: Mapped[str] = mapped_column(String(255), nullable=True)

    narration: Mapped[str] = mapped_column(Text, nullable=True)
    is_cancelled: Mapped[bool] = mapped_column(Boolean, default=False)
    is_opening: Mapped[bool] = mapped_column(Boolean, default=False)

    maker_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    approver_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    approved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)

    dimensions: Mapped[dict] = mapped_column(JSONB, nullable=True)   # extra dimension tags

    __table_args__ = (
        Index("ix_gl_date_account", "posting_date", "account_id"),
        Index("ix_gl_voucher", "voucher_type", "voucher_number"),
        Index("ix_gl_branch_period", "branch_id", "fiscal_year", "fiscal_period"),
        Index("ix_gl_cc_period", "cost_center_id", "fiscal_year", "fiscal_period"),
    )


class FiscalYear(Base, UUIDMixin, TimestampMixin):
    """Fiscal Year master – controls period-end and carry-forward"""
    __tablename__ = "fiscal_years"

    name: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)  # "2024-25"
    start_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    end_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_closed: Mapped[bool] = mapped_column(Boolean, default=False)
    closed_by: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    closed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)


class BudgetAllocation(Base, UUIDMixin, TimestampMixin):
    """Budget by account + dimension for variance reporting"""
    __tablename__ = "budget_allocations"

    fiscal_year: Mapped[str] = mapped_column(String(10), nullable=False, index=True)
    fiscal_period: Mapped[int] = mapped_column(Integer, nullable=True)   # null = annual
    account_id: Mapped[str] = mapped_column(String(36), ForeignKey("chart_of_accounts.id"), nullable=False)
    branch_id: Mapped[str] = mapped_column(String(36), ForeignKey("branches.id"), nullable=True)
    cost_center_id: Mapped[str] = mapped_column(String(36), ForeignKey("cost_centers.id"), nullable=True)
    project_id: Mapped[str] = mapped_column(String(36), ForeignKey("projects.id"), nullable=True)
    budget_amount: Mapped[float] = mapped_column(Float, default=0)
    notes: Mapped[str] = mapped_column(Text, nullable=True)


class ApprovalWorkflow(Base, UUIDMixin, TimestampMixin):
    """
    Maker-Checker workflow log for all documents requiring approval.
    Different from ApprovalRequest (other.py) – this is a structured audit trail
    that enforces the maker != approver invariant for financial documents.
    """
    __tablename__ = "approval_workflows"

    document_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    # sales_invoice | purchase_invoice | journal_entry | payment | work_order | po
    document_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    document_number: Mapped[str] = mapped_column(String(100), nullable=True)

    status: Mapped[str] = mapped_column(String(50), default="pending_approval", index=True)
    # pending_approval | approved | rejected | cancelled

    maker_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)
    maker_name: Mapped[str] = mapped_column(String(255), nullable=True)
    submitted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    approver_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    approver_name: Mapped[str] = mapped_column(String(255), nullable=True)
    actioned_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)

    remarks: Mapped[str] = mapped_column(Text, nullable=True)
    rejection_reason: Mapped[str] = mapped_column(Text, nullable=True)
    amount: Mapped[float] = mapped_column(Float, nullable=True)   # for threshold-based routing
    metadata_json: Mapped[dict] = mapped_column(JSONB, nullable=True)

    __table_args__ = (
        Index("ix_approval_wf_doc", "document_type", "document_id"),
    )
