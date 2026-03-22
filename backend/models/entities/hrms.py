"""
SQLAlchemy Entity Models - HRMS Module
"""
from sqlalchemy import Column, String, DateTime, Boolean, Text, Integer, Float, ForeignKey, Date
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime, timezone, date

from core.database import Base
from models.entities.base import UUIDMixin, TimestampMixin


class Employee(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "employees"
    
    employee_code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    email: Mapped[str] = mapped_column(String(255), nullable=True, index=True)
    phone: Mapped[str] = mapped_column(String(50), nullable=True)
    mobile: Mapped[str] = mapped_column(String(50), nullable=True)
    
    # Personal
    date_of_birth: Mapped[date] = mapped_column(Date, nullable=True)
    gender: Mapped[str] = mapped_column(String(20), nullable=True)
    blood_group: Mapped[str] = mapped_column(String(10), nullable=True)
    marital_status: Mapped[str] = mapped_column(String(20), nullable=True)
    address: Mapped[str] = mapped_column(Text, nullable=True)
    city: Mapped[str] = mapped_column(String(100), nullable=True)
    state: Mapped[str] = mapped_column(String(100), nullable=True)
    pincode: Mapped[str] = mapped_column(String(20), nullable=True)
    location: Mapped[str] = mapped_column(String(255), nullable=True)
    emergency_contact: Mapped[dict] = mapped_column(JSONB, nullable=True)
    
    # Employment
    department: Mapped[str] = mapped_column(String(100), nullable=True, index=True)
    designation: Mapped[str] = mapped_column(String(100), nullable=True)
    employment_type: Mapped[str] = mapped_column(String(50), default="permanent")  # permanent, contract, trainee
    joining_date: Mapped[date] = mapped_column(Date, nullable=True)
    date_of_joining: Mapped[str] = mapped_column(String(50), nullable=True)  # String version for schema compatibility
    confirmation_date: Mapped[date] = mapped_column(Date, nullable=True)
    resignation_date: Mapped[date] = mapped_column(Date, nullable=True)
    leaving_date: Mapped[date] = mapped_column(Date, nullable=True)
    reports_to: Mapped[str] = mapped_column(String(36), ForeignKey("employees.id"), nullable=True)
    branch_id: Mapped[str] = mapped_column(String(36), ForeignKey("branches.id"), nullable=True)
    shift_timing: Mapped[str] = mapped_column(String(100), nullable=True)
    
    # Status
    status: Mapped[str] = mapped_column(String(50), default="active", index=True)  # active, inactive, terminated, resigned
    
    # Documents
    pan: Mapped[str] = mapped_column(String(20), nullable=True)
    aadhar: Mapped[str] = mapped_column(String(20), nullable=True)
    uan: Mapped[str] = mapped_column(String(20), nullable=True)  # PF UAN
    esic_number: Mapped[str] = mapped_column(String(20), nullable=True)
    
    # Bank
    bank_name: Mapped[str] = mapped_column(String(255), nullable=True)
    bank_account: Mapped[str] = mapped_column(String(50), nullable=True)
    ifsc_code: Mapped[str] = mapped_column(String(20), nullable=True)
    bank_ifsc: Mapped[str] = mapped_column(String(20), nullable=True)  # Alias for ifsc_code
    
    # Salary
    basic_salary: Mapped[float] = mapped_column(Float, default=0)
    hra: Mapped[float] = mapped_column(Float, default=0)
    pf: Mapped[float] = mapped_column(Float, default=0)
    esi: Mapped[float] = mapped_column(Float, default=0)
    pt: Mapped[float] = mapped_column(Float, default=0)
    salary_structure_id: Mapped[str] = mapped_column(String(36), ForeignKey("salary_structures.id"), nullable=True)
    
    # User link
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    
    profile_photo: Mapped[str] = mapped_column(String(500), nullable=True)
    custom_fields: Mapped[dict] = mapped_column(JSONB, nullable=True)


class Attendance(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "attendance"
    
    employee_id: Mapped[str] = mapped_column(String(36), ForeignKey("employees.id"), nullable=False, index=True)
    date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(20), default="present")  # present, absent, half_day, leave, holiday, weekend
    check_in: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    check_out: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    hours_worked: Mapped[float] = mapped_column(Float, default=0)
    overtime_hours: Mapped[float] = mapped_column(Float, default=0)
    shift: Mapped[str] = mapped_column(String(20), nullable=True)
    late_minutes: Mapped[int] = mapped_column(Integer, default=0)
    early_leaving_minutes: Mapped[int] = mapped_column(Integer, default=0)
    notes: Mapped[str] = mapped_column(Text, nullable=True)
    
    __table_args__ = (
        # Unique constraint on employee + date
        {'extend_existing': True},
    )


class LeaveRequest(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "leave_requests"
    
    employee_id: Mapped[str] = mapped_column(String(36), ForeignKey("employees.id"), nullable=False, index=True)
    leave_type: Mapped[str] = mapped_column(String(50), nullable=False)  # casual, sick, earned, maternity, etc.
    from_date: Mapped[date] = mapped_column(Date, nullable=False)
    to_date: Mapped[date] = mapped_column(Date, nullable=False)
    days: Mapped[float] = mapped_column(Float, default=1)
    is_half_day: Mapped[bool] = mapped_column(Boolean, default=False)
    half_day_type: Mapped[str] = mapped_column(String(20), nullable=True)  # first_half, second_half
    reason: Mapped[str] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="pending", index=True)  # pending, approved, rejected, cancelled
    approved_by: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    approved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    rejection_reason: Mapped[str] = mapped_column(Text, nullable=True)
    attachments: Mapped[list] = mapped_column(JSONB, nullable=True)


class LeaveType(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "leave_types"
    
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    days_allowed: Mapped[int] = mapped_column(Integer, default=0)
    is_paid: Mapped[bool] = mapped_column(Boolean, default=True)
    is_carry_forward: Mapped[bool] = mapped_column(Boolean, default=False)
    max_carry_forward: Mapped[int] = mapped_column(Integer, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class SalaryStructure(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "salary_structures"
    
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    components: Mapped[list] = mapped_column(JSONB, nullable=True)  # Array of {name, type, calculation_type, value}
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class Payroll(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "payroll"
    
    employee_id: Mapped[str] = mapped_column(String(36), ForeignKey("employees.id"), nullable=False, index=True)
    year: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    month: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    
    # Days
    working_days: Mapped[int] = mapped_column(Integer, default=0)
    present_days: Mapped[float] = mapped_column(Float, default=0)
    leave_days: Mapped[float] = mapped_column(Float, default=0)
    absent_days: Mapped[float] = mapped_column(Float, default=0)
    
    # Earnings
    basic: Mapped[float] = mapped_column(Float, default=0)
    hra: Mapped[float] = mapped_column(Float, default=0)
    da: Mapped[float] = mapped_column(Float, default=0)
    special_allowance: Mapped[float] = mapped_column(Float, default=0)
    other_allowances: Mapped[float] = mapped_column(Float, default=0)
    overtime: Mapped[float] = mapped_column(Float, default=0)
    incentives: Mapped[float] = mapped_column(Float, default=0)
    gross_salary: Mapped[float] = mapped_column(Float, default=0)
    
    # Deductions
    pf_employee: Mapped[float] = mapped_column(Float, default=0)
    pf_employer: Mapped[float] = mapped_column(Float, default=0)
    esic_employee: Mapped[float] = mapped_column(Float, default=0)
    esic_employer: Mapped[float] = mapped_column(Float, default=0)
    pt: Mapped[float] = mapped_column(Float, default=0)  # Professional Tax
    tds: Mapped[float] = mapped_column(Float, default=0)
    loan_deduction: Mapped[float] = mapped_column(Float, default=0)
    other_deductions: Mapped[float] = mapped_column(Float, default=0)
    total_deductions: Mapped[float] = mapped_column(Float, default=0)
    
    net_salary: Mapped[float] = mapped_column(Float, default=0)
    
    status: Mapped[str] = mapped_column(String(50), default="draft", index=True)  # draft, approved, paid
    payment_date: Mapped[date] = mapped_column(Date, nullable=True)
    payment_mode: Mapped[str] = mapped_column(String(50), nullable=True)
    transaction_ref: Mapped[str] = mapped_column(String(100), nullable=True)
    
    breakdown: Mapped[dict] = mapped_column(JSONB, nullable=True)  # Detailed breakdown


class Loan(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "loans"
    
    employee_id: Mapped[str] = mapped_column(String(36), ForeignKey("employees.id"), nullable=False, index=True)
    loan_type: Mapped[str] = mapped_column(String(50), nullable=True)  # salary_advance, personal, vehicle, etc.
    amount: Mapped[float] = mapped_column(Float, default=0)
    interest_rate: Mapped[float] = mapped_column(Float, default=0)
    tenure_months: Mapped[int] = mapped_column(Integer, default=0)
    emi_amount: Mapped[float] = mapped_column(Float, default=0)
    disbursement_date: Mapped[date] = mapped_column(Date, nullable=True)
    start_month: Mapped[str] = mapped_column(String(10), nullable=True)  # YYYY-MM
    paid_amount: Mapped[float] = mapped_column(Float, default=0)
    balance_amount: Mapped[float] = mapped_column(Float, default=0)
    status: Mapped[str] = mapped_column(String(50), default="pending", index=True)
    approved_by: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    notes: Mapped[str] = mapped_column(Text, nullable=True)


class Holiday(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "holidays"
    
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    year: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    holiday_type: Mapped[str] = mapped_column(String(50), default="public")  # public, restricted, optional
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    applicable_branches: Mapped[list] = mapped_column(JSONB, nullable=True)  # If specific to certain branches
