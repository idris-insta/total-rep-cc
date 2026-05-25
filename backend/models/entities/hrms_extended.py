"""
SQLAlchemy Entity Models - HRMS Extended
Adds the missing HRMS depth not covered by hrms.py:
  - LeaveBalance & LeaveApplication (hrms.py has LeaveRequest – this is the enhanced version)
  - ShiftMaster & EmployeeShiftRoster
  - AttendanceRecord (extended from basic Attendance in hrms.py)
  - EmployeeSalaryAssignment – links employee to existing salary_structures
  - PayrollRun + PayslipEntry – structured payroll processing
  - EmployeeLoan – enhanced loan/advance with EMI schedule
  - AssetCategory, FixedAsset, AssetDepreciationEntry (SLM & WDV methods)

Note: LeaveType, SalaryStructure, Holiday, Employee tables are in hrms.py.
      We FK-reference them here; we do NOT redefine them.
"""
from sqlalchemy import String, DateTime, Boolean, Text, Integer, Float, ForeignKey, Date, UniqueConstraint, Index
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime, timezone, date

from core.database import Base
from models.entities.base import UUIDMixin, TimestampMixin


# ==================== LEAVE MANAGEMENT (EXTENDED) ====================

class LeaveBalance(Base, UUIDMixin, TimestampMixin):
    """Annual leave balance ledger per employee per leave type"""
    __tablename__ = "leave_balances"

    employee_id: Mapped[str] = mapped_column(String(36), ForeignKey("employees.id"), nullable=False, index=True)
    leave_type_id: Mapped[str] = mapped_column(String(36), ForeignKey("leave_types.id"), nullable=False)
    fiscal_year: Mapped[str] = mapped_column(String(10), nullable=False)   # "2024-25"
    opening_balance: Mapped[float] = mapped_column(Float, default=0)
    entitlement: Mapped[float] = mapped_column(Float, default=0)
    taken: Mapped[float] = mapped_column(Float, default=0)
    encashed: Mapped[float] = mapped_column(Float, default=0)
    closing_balance: Mapped[float] = mapped_column(Float, default=0)
    # closing = opening + entitlement - taken - encashed

    __table_args__ = (
        UniqueConstraint("employee_id", "leave_type_id", "fiscal_year", name="uq_leave_bal_emp_type_fy"),
    )


class LeaveApplication(Base, UUIDMixin, TimestampMixin):
    """
    Enhanced leave request with full Maker-Approver workflow.
    Separate from LeaveRequest in hrms.py (table: leave_requests) –
    this table (leave_applications) tracks structured approval steps.
    """
    __tablename__ = "leave_applications"

    application_number: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    employee_id: Mapped[str] = mapped_column(String(36), ForeignKey("employees.id"), nullable=False, index=True)
    leave_type_id: Mapped[str] = mapped_column(String(36), ForeignKey("leave_types.id"), nullable=False)

    from_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    to_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    total_days: Mapped[float] = mapped_column(Float, nullable=False)
    half_day: Mapped[bool] = mapped_column(Boolean, default=False)

    reason: Mapped[str] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="pending", index=True)
    # pending | approved | rejected | cancelled | withdrawn

    approver_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    approved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    rejection_reason: Mapped[str] = mapped_column(Text, nullable=True)
    attachments: Mapped[list] = mapped_column(JSONB, nullable=True)


# ==================== SHIFT MANAGEMENT ====================

class ShiftMaster(Base, UUIDMixin, TimestampMixin):
    """Shift definitions: Morning (06-14), Evening (14-22), Night (22-06)"""
    __tablename__ = "shift_masters"

    shift_code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    shift_name: Mapped[str] = mapped_column(String(100), nullable=False)
    start_time: Mapped[str] = mapped_column(String(10), nullable=False)   # "06:00"
    end_time: Mapped[str] = mapped_column(String(10), nullable=False)     # "14:00"
    grace_minutes: Mapped[int] = mapped_column(Integer, default=10)
    is_night_shift: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class EmployeeShiftRoster(Base, UUIDMixin, TimestampMixin):
    """Assigns shift to employee for a date range"""
    __tablename__ = "employee_shift_rosters"

    employee_id: Mapped[str] = mapped_column(String(36), ForeignKey("employees.id"), nullable=False, index=True)
    shift_id: Mapped[str] = mapped_column(String(36), ForeignKey("shift_masters.id"), nullable=False)
    effective_from: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    effective_to: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    notes: Mapped[str] = mapped_column(Text, nullable=True)


class AttendanceRecord(Base, UUIDMixin, TimestampMixin):
    """
    Structured daily attendance (biometric / manual).
    Extends the basic Attendance in hrms.py with shift, OT, late-minute tracking.
    """
    __tablename__ = "attendance_records"

    employee_id: Mapped[str] = mapped_column(String(36), ForeignKey("employees.id"), nullable=False, index=True)
    attendance_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    shift_id: Mapped[str] = mapped_column(String(36), ForeignKey("shift_masters.id"), nullable=True)

    in_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    out_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    working_hours: Mapped[float] = mapped_column(Float, default=0)
    overtime_hours: Mapped[float] = mapped_column(Float, default=0)

    status: Mapped[str] = mapped_column(String(50), default="present", index=True)
    # present | absent | half_day | late | holiday | week_off | on_leave

    is_late: Mapped[bool] = mapped_column(Boolean, default=False)
    late_minutes: Mapped[int] = mapped_column(Integer, default=0)
    early_exit_minutes: Mapped[int] = mapped_column(Integer, default=0)

    leave_application_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("leave_applications.id"), nullable=True
    )
    biometric_log_id: Mapped[str] = mapped_column(String(100), nullable=True)
    entry_source: Mapped[str] = mapped_column(String(20), default="manual")   # biometric | manual | system
    notes: Mapped[str] = mapped_column(Text, nullable=True)
    approved_by: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)

    __table_args__ = (
        UniqueConstraint("employee_id", "attendance_date", name="uq_att_rec_emp_date"),
    )


# ==================== PAYROLL (STRUCTURED) ====================

class EmployeeSalaryAssignment(Base, UUIDMixin, TimestampMixin):
    """
    Links an employee to their salary_structure with effective-date versioning.
    References existing salary_structures table (hrms.py).
    """
    __tablename__ = "employee_salary_assignments"

    employee_id: Mapped[str] = mapped_column(String(36), ForeignKey("employees.id"), nullable=False, index=True)
    salary_structure_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("salary_structures.id"), nullable=False
    )
    effective_from: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    effective_to: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)

    ctc_annual: Mapped[float] = mapped_column(Float, default=0)
    basic_monthly: Mapped[float] = mapped_column(Float, default=0)
    gross_monthly: Mapped[float] = mapped_column(Float, default=0)

    # Override specific salary components: {component_name: amount}
    component_overrides: Mapped[dict] = mapped_column(JSONB, nullable=True)

    # Statutory rates (can override structure defaults)
    pf_employee_percent: Mapped[float] = mapped_column(Float, default=12.0)
    pf_employer_percent: Mapped[float] = mapped_column(Float, default=12.0)
    esi_employee_percent: Mapped[float] = mapped_column(Float, default=0.75)
    esi_employer_percent: Mapped[float] = mapped_column(Float, default=3.25)
    esi_applicable: Mapped[bool] = mapped_column(Boolean, default=True)
    # ESI not applicable if gross > ₹21,000/month

    approved_by: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    notes: Mapped[str] = mapped_column(Text, nullable=True)


class PayrollRun(Base, UUIDMixin, TimestampMixin):
    """Monthly payroll processing run header"""
    __tablename__ = "payroll_runs"

    run_number: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    payroll_month: Mapped[str] = mapped_column(String(7), nullable=False, index=True)   # "2024-03"
    fiscal_year: Mapped[str] = mapped_column(String(10), nullable=False)
    branch_id: Mapped[str] = mapped_column(String(36), ForeignKey("branches.id"), nullable=True)

    status: Mapped[str] = mapped_column(String(50), default="draft", index=True)
    # draft | computed | approved | bank_file_generated | paid | locked

    total_employees: Mapped[int] = mapped_column(Integer, default=0)
    total_gross: Mapped[float] = mapped_column(Float, default=0)
    total_deductions: Mapped[float] = mapped_column(Float, default=0)
    total_net_pay: Mapped[float] = mapped_column(Float, default=0)
    total_pf_employee: Mapped[float] = mapped_column(Float, default=0)
    total_pf_employer: Mapped[float] = mapped_column(Float, default=0)
    total_esi_employee: Mapped[float] = mapped_column(Float, default=0)
    total_esi_employer: Mapped[float] = mapped_column(Float, default=0)
    total_tds: Mapped[float] = mapped_column(Float, default=0)

    processed_by: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    approved_by: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    approved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    payment_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    payment_mode: Mapped[str] = mapped_column(String(50), nullable=True)   # bank_transfer | cheque | cash
    notes: Mapped[str] = mapped_column(Text, nullable=True)


class PayslipEntry(Base, UUIDMixin, TimestampMixin):
    """
    Per-employee payslip for a payroll run.
    Captures full statutory breakdown: PF / ESI / Professional Tax / TDS.
    """
    __tablename__ = "payslip_entries"

    payroll_run_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("payroll_runs.id"), nullable=False, index=True
    )
    employee_id: Mapped[str] = mapped_column(String(36), ForeignKey("employees.id"), nullable=False, index=True)
    payroll_month: Mapped[str] = mapped_column(String(7), nullable=False)

    # Working days
    working_days: Mapped[float] = mapped_column(Float, default=0)
    present_days: Mapped[float] = mapped_column(Float, default=0)
    absent_days: Mapped[float] = mapped_column(Float, default=0)
    leave_days: Mapped[float] = mapped_column(Float, default=0)
    overtime_hours: Mapped[float] = mapped_column(Float, default=0)

    # Earnings
    basic: Mapped[float] = mapped_column(Float, default=0)
    hra: Mapped[float] = mapped_column(Float, default=0)
    ta: Mapped[float] = mapped_column(Float, default=0)
    special_allowance: Mapped[float] = mapped_column(Float, default=0)
    overtime_amount: Mapped[float] = mapped_column(Float, default=0)
    other_earnings: Mapped[float] = mapped_column(Float, default=0)
    gross_earnings: Mapped[float] = mapped_column(Float, default=0)

    # Statutory deductions
    pf_employee: Mapped[float] = mapped_column(Float, default=0)     # 12% of basic
    esi_employee: Mapped[float] = mapped_column(Float, default=0)    # 0.75% of gross
    professional_tax: Mapped[float] = mapped_column(Float, default=0)
    tds: Mapped[float] = mapped_column(Float, default=0)
    loan_emi: Mapped[float] = mapped_column(Float, default=0)
    advance_recovery: Mapped[float] = mapped_column(Float, default=0)
    other_deductions: Mapped[float] = mapped_column(Float, default=0)
    total_deductions: Mapped[float] = mapped_column(Float, default=0)

    # Employer contributions (CTC components, not deducted from employee)
    pf_employer: Mapped[float] = mapped_column(Float, default=0)     # 12% of basic
    esi_employer: Mapped[float] = mapped_column(Float, default=0)    # 3.25% of gross

    net_pay: Mapped[float] = mapped_column(Float, default=0)

    # Full detail for e-payslip PDF
    earnings_detail: Mapped[list] = mapped_column(JSONB, nullable=True)
    deductions_detail: Mapped[list] = mapped_column(JSONB, nullable=True)

    bank_account: Mapped[str] = mapped_column(String(50), nullable=True)
    payment_status: Mapped[str] = mapped_column(String(50), default="pending")
    payment_reference: Mapped[str] = mapped_column(String(100), nullable=True)
    paid_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        UniqueConstraint("payroll_run_id", "employee_id", name="uq_payslip_run_emp"),
    )


class EmployeeLoan(Base, UUIDMixin, TimestampMixin):
    """Enhanced loan/advance with EMI repayment schedule (supplements hrms.py Loan)"""
    __tablename__ = "employee_loans_ext"

    loan_number: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    employee_id: Mapped[str] = mapped_column(String(36), ForeignKey("employees.id"), nullable=False, index=True)
    loan_type: Mapped[str] = mapped_column(String(50), default="advance")
    # advance | personal_loan | vehicle_loan

    loan_amount: Mapped[float] = mapped_column(Float, nullable=False)
    outstanding_amount: Mapped[float] = mapped_column(Float, default=0)
    emi_amount: Mapped[float] = mapped_column(Float, default=0)
    disbursement_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    tenure_months: Mapped[int] = mapped_column(Integer, default=1)
    status: Mapped[str] = mapped_column(String(50), default="active")   # active | closed | written_off

    approved_by: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    # [{month, emi, principal, interest, balance}]
    repayment_schedule: Mapped[list] = mapped_column(JSONB, nullable=True)
    notes: Mapped[str] = mapped_column(Text, nullable=True)


# ==================== FIXED ASSET MANAGEMENT ====================

class AssetCategory(Base, UUIDMixin, TimestampMixin):
    """Asset category with default depreciation method and ledger accounts"""
    __tablename__ = "asset_categories"

    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    depreciation_method: Mapped[str] = mapped_column(String(50), default="straight_line")
    # straight_line (SLM) | diminishing_value (WDV)
    useful_life_years: Mapped[float] = mapped_column(Float, default=5)
    depreciation_rate_percent: Mapped[float] = mapped_column(Float, nullable=True)
    salvage_value_percent: Mapped[float] = mapped_column(Float, default=5.0)
    gl_account_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("chart_of_accounts.id"), nullable=True
    )
    depreciation_account_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("chart_of_accounts.id"), nullable=True
    )
    accumulated_dep_account_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("chart_of_accounts.id"), nullable=True
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    notes: Mapped[str] = mapped_column(Text, nullable=True)


class FixedAsset(Base, UUIDMixin, TimestampMixin):
    """
    Fixed Asset master record.

    Depreciation formulae:
      SLM  : annual_dep = (gross_block - salvage_value) / useful_life_years
      WDV  : annual_dep = net_block × depreciation_rate_percent / 100

    Non-depreciable assets:  is_depreciable = False  (land, art, etc.)
    """
    __tablename__ = "fixed_assets"

    asset_code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    asset_name: Mapped[str] = mapped_column(String(255), nullable=False)
    asset_category_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("asset_categories.id"), nullable=False
    )
    branch_id: Mapped[str] = mapped_column(String(36), ForeignKey("branches.id"), nullable=True)
    cost_center_id: Mapped[str] = mapped_column(String(36), ForeignKey("cost_centers.id"), nullable=True)

    # Acquisition
    purchase_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    installation_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    purchase_invoice_id: Mapped[str] = mapped_column(String(36), ForeignKey("invoices.id"), nullable=True)
    supplier_id: Mapped[str] = mapped_column(String(36), ForeignKey("accounts.id"), nullable=True)

    # Cost block
    gross_block: Mapped[float] = mapped_column(Float, nullable=False)
    salvage_value: Mapped[float] = mapped_column(Float, default=0)
    depreciable_amount: Mapped[float] = mapped_column(Float, default=0)
    # depreciable_amount = gross_block - salvage_value

    # Depreciation settings
    is_depreciable: Mapped[bool] = mapped_column(Boolean, default=True)
    depreciation_method: Mapped[str] = mapped_column(String(50), default="straight_line")
    useful_life_years: Mapped[float] = mapped_column(Float, default=5)
    depreciation_rate_percent: Mapped[float] = mapped_column(Float, nullable=True)

    # Running balances
    accumulated_depreciation: Mapped[float] = mapped_column(Float, default=0)
    net_block: Mapped[float] = mapped_column(Float, default=0)
    # net_block = gross_block - accumulated_depreciation

    status: Mapped[str] = mapped_column(String(50), default="active", index=True)
    # active | disposed | written_off | under_maintenance

    disposal_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    disposal_value: Mapped[float] = mapped_column(Float, nullable=True)
    disposal_reason: Mapped[str] = mapped_column(Text, nullable=True)

    location: Mapped[str] = mapped_column(String(255), nullable=True)
    custodian_id: Mapped[str] = mapped_column(String(36), ForeignKey("employees.id"), nullable=True)

    insurance_policy: Mapped[str] = mapped_column(String(100), nullable=True)
    insurance_expiry: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    insured_value: Mapped[float] = mapped_column(Float, nullable=True)

    notes: Mapped[str] = mapped_column(Text, nullable=True)
    custom_fields: Mapped[dict] = mapped_column(JSONB, nullable=True)


class AssetDepreciationEntry(Base, UUIDMixin, TimestampMixin):
    """
    Periodic depreciation journal per asset.
    Created by the monthly/annual depreciation run.

    SLM  : depreciation_amount = depreciable_amount / (useful_life_years × 12)  [monthly]
    WDV  : depreciation_amount = opening_net_block × rate / (100 × 12)           [monthly]
    """
    __tablename__ = "asset_depreciation_entries"

    asset_id: Mapped[str] = mapped_column(String(36), ForeignKey("fixed_assets.id"), nullable=False, index=True)
    fiscal_year: Mapped[str] = mapped_column(String(10), nullable=False)
    fiscal_period: Mapped[int] = mapped_column(Integer, nullable=False)   # 1-12
    depreciation_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    opening_net_block: Mapped[float] = mapped_column(Float, default=0)
    depreciation_amount: Mapped[float] = mapped_column(Float, default=0)
    closing_net_block: Mapped[float] = mapped_column(Float, default=0)

    method_used: Mapped[str] = mapped_column(String(50), nullable=True)   # straight_line | diminishing_value
    gl_entry_id: Mapped[str] = mapped_column(String(36), ForeignKey("general_ledger.id"), nullable=True)
    journal_entry_id: Mapped[str] = mapped_column(String(36), ForeignKey("journal_entries.id"), nullable=True)

    is_posted: Mapped[bool] = mapped_column(Boolean, default=False)
    posted_by: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)

    __table_args__ = (
        UniqueConstraint("asset_id", "fiscal_year", "fiscal_period", name="uq_dep_entry_period"),
    )
