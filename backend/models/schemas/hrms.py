"""
HRMS Schemas - Pydantic models for HRMS module
"""
from pydantic import BaseModel
from typing import Optional


# ==================== EMPLOYEE SCHEMAS ====================
class EmployeeBase(BaseModel):
    employee_code: Optional[str] = None
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    department: Optional[str] = None
    designation: Optional[str] = None
    location: Optional[str] = None
    date_of_joining: Optional[str] = None
    shift_timing: Optional[str] = None
    basic_salary: Optional[float] = None
    hra: Optional[float] = None
    pf: Optional[float] = None
    esi: Optional[float] = None
    pt: Optional[float] = None
    bank_name: Optional[str] = None
    bank_account: Optional[str] = None
    bank_ifsc: Optional[str] = None


class EmployeeCreate(EmployeeBase):
    employee_code: str
    name: str
    email: str
    department: str
    designation: str


class EmployeeUpdate(EmployeeBase):
    status: Optional[str] = None


class EmployeeResponse(EmployeeBase):
    id: str
    status: str = "active"
    created_at: Optional[str] = None


# ==================== ATTENDANCE SCHEMAS ====================
class AttendanceCreate(BaseModel):
    employee_id: str
    date: str
    check_in: Optional[str] = None
    check_out: Optional[str] = None
    status: str  # present, absent, half_day, leave
    hours_worked: float = 0


class AttendanceResponse(BaseModel):
    id: str
    employee_id: str
    date: str
    check_in: Optional[str] = None
    check_out: Optional[str] = None
    status: str
    hours_worked: float
    created_at: Optional[str] = None


# ==================== LEAVE REQUEST SCHEMAS ====================
class LeaveRequestCreate(BaseModel):
    employee_id: str
    leave_type: str  # casual, sick, earned, unpaid
    from_date: str
    to_date: str
    reason: str


class LeaveRequestResponse(BaseModel):
    id: str
    employee_id: str
    leave_type: str
    from_date: str
    to_date: str
    reason: str
    days: float
    status: str
    approved_by: Optional[str] = None
    approved_at: Optional[str] = None
    created_at: Optional[str] = None


# ==================== PAYROLL SCHEMAS ====================
class PayrollResponse(BaseModel):
    id: str
    employee_id: str
    employee_name: Optional[str] = None
    employee_code: Optional[str] = None
    year: int
    month: int
    days_present: float
    days_absent: float
    basic_salary: float
    hra: float
    gross_salary: float
    pf_deduction: float
    esi_deduction: float
    pt_deduction: float
    total_deductions: float
    net_salary: float
    status: str
    created_at: Optional[str] = None
