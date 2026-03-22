"""
HRMS Enhancement Module - Complete HR Management
Features:
- Attendance Tracking (Check-in/Check-out)
- Leave Management (Apply, Approve, Balance)
- PF/ESI/PT Statutory Compliance
- Loan & Advance Management
- Employee Self-Service
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone, timedelta, date
from dateutil.relativedelta import relativedelta
import uuid

from server import db, get_current_user

router = APIRouter()

# ==================== ATTENDANCE MODELS ====================
class AttendanceCreate(BaseModel):
    employee_id: str
    date: str  # YYYY-MM-DD
    check_in: Optional[str] = None  # HH:MM
    check_out: Optional[str] = None
    status: str = "present"  # present, absent, half_day, late, on_leave, holiday, week_off
    overtime_hours: float = 0
    notes: Optional[str] = None

class Attendance(BaseModel):
    id: str
    employee_id: str
    employee_name: Optional[str] = None
    date: str
    check_in: Optional[str] = None
    check_out: Optional[str] = None
    working_hours: float = 0
    overtime_hours: float = 0
    status: str
    notes: Optional[str] = None
    created_at: str

# ==================== LEAVE MODELS ====================
class LeaveTypeCreate(BaseModel):
    name: str  # Casual Leave, Sick Leave, Earned Leave, etc.
    code: str  # CL, SL, EL
    annual_quota: int
    carry_forward: bool = False
    max_carry_forward: int = 0
    is_paid: bool = True
    requires_approval: bool = True

class LeaveApplicationCreate(BaseModel):
    employee_id: str
    leave_type_id: str
    from_date: str
    to_date: str
    reason: str
    half_day: bool = False
    half_day_type: Optional[str] = None  # first_half, second_half

class LeaveApplication(BaseModel):
    id: str
    employee_id: str
    employee_name: Optional[str] = None
    leave_type_id: str
    leave_type_name: Optional[str] = None
    from_date: str
    to_date: str
    days: float
    reason: str
    status: str  # pending, approved, rejected, cancelled
    approved_by: Optional[str] = None
    approved_at: Optional[str] = None
    rejection_reason: Optional[str] = None
    created_at: str

# ==================== STATUTORY MODELS ====================
class StatutoryConfig(BaseModel):
    id: str
    financial_year: str  # 2024-25
    pf_employee_percent: float = 12.0
    pf_employer_percent: float = 12.0
    pf_admin_charges: float = 0.5
    pf_wage_ceiling: float = 15000
    esi_employee_percent: float = 0.75
    esi_employer_percent: float = 3.25
    esi_wage_ceiling: float = 21000
    pt_slabs: List[Dict] = []  # Professional Tax slabs
    lwf_employee: float = 0
    lwf_employer: float = 0
    is_active: bool = True

class LoanCreate(BaseModel):
    employee_id: str
    loan_type: str  # salary_advance, personal_loan, emergency_loan
    amount: float
    interest_rate: float = 0
    tenure_months: int
    emi_amount: float
    start_date: str
    reason: str

# ==================== ATTENDANCE ENDPOINTS ====================
@router.post("/attendance", response_model=Attendance)
async def mark_attendance(data: AttendanceCreate, current_user: dict = Depends(get_current_user)):
    """Mark attendance for an employee"""
    # Check if already marked
    existing = await db.attendance.find_one({
        "employee_id": data.employee_id,
        "date": data.date
    })
    if existing:
        raise HTTPException(status_code=400, detail="Attendance already marked for this date")
    
    employee = await db.employees.find_one({"id": data.employee_id}, {"first_name": 1, "last_name": 1})
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    # Calculate working hours
    working_hours = 0
    if data.check_in and data.check_out:
        try:
            ci = datetime.strptime(data.check_in, "%H:%M")
            co = datetime.strptime(data.check_out, "%H:%M")
            working_hours = (co - ci).seconds / 3600
        except:
            pass
    
    now = datetime.now(timezone.utc).isoformat()
    att_doc = {
        "id": str(uuid.uuid4()),
        "employee_id": data.employee_id,
        "employee_name": f"{employee.get('first_name', '')} {employee.get('last_name', '')}".strip(),
        "date": data.date,
        "check_in": data.check_in,
        "check_out": data.check_out,
        "working_hours": round(working_hours, 2),
        "overtime_hours": data.overtime_hours,
        "status": data.status,
        "notes": data.notes,
        "created_at": now
    }
    
    await db.attendance.insert_one(att_doc)
    return Attendance(**{k: v for k, v in att_doc.items() if k != '_id'})

@router.post("/attendance/check-in")
async def employee_check_in(employee_id: str, current_user: dict = Depends(get_current_user)):
    """Employee self check-in"""
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    current_time = datetime.now(timezone.utc).strftime("%H:%M")
    
    existing = await db.attendance.find_one({"employee_id": employee_id, "date": today})
    if existing and existing.get("check_in"):
        raise HTTPException(status_code=400, detail="Already checked in today")
    
    employee = await db.employees.find_one({"id": employee_id}, {"first_name": 1, "last_name": 1})
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    # Determine status (late if after 9:30 AM)
    status = "present"
    if current_time > "09:30":
        status = "late"
    
    if existing:
        await db.attendance.update_one(
            {"id": existing["id"]},
            {"$set": {"check_in": current_time, "status": status}}
        )
    else:
        att_doc = {
            "id": str(uuid.uuid4()),
            "employee_id": employee_id,
            "employee_name": f"{employee.get('first_name', '')} {employee.get('last_name', '')}".strip(),
            "date": today,
            "check_in": current_time,
            "check_out": None,
            "working_hours": 0,
            "overtime_hours": 0,
            "status": status,
            "notes": None,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        await db.attendance.insert_one(att_doc)
    
    return {"message": f"Checked in at {current_time}", "status": status}

@router.post("/attendance/check-out")
async def employee_check_out(employee_id: str, current_user: dict = Depends(get_current_user)):
    """Employee self check-out"""
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    current_time = datetime.now(timezone.utc).strftime("%H:%M")
    
    existing = await db.attendance.find_one({"employee_id": employee_id, "date": today})
    if not existing:
        raise HTTPException(status_code=400, detail="Please check-in first")
    if existing.get("check_out"):
        raise HTTPException(status_code=400, detail="Already checked out today")
    
    # Calculate working hours
    working_hours = 0
    overtime = 0
    if existing.get("check_in"):
        try:
            ci = datetime.strptime(existing["check_in"], "%H:%M")
            co = datetime.strptime(current_time, "%H:%M")
            working_hours = (co - ci).seconds / 3600
            if working_hours > 9:
                overtime = working_hours - 9
        except:
            pass
    
    await db.attendance.update_one(
        {"id": existing["id"]},
        {"$set": {
            "check_out": current_time,
            "working_hours": round(working_hours, 2),
            "overtime_hours": round(overtime, 2)
        }}
    )
    
    return {"message": f"Checked out at {current_time}", "working_hours": round(working_hours, 2)}

@router.get("/attendance")
async def list_attendance(
    employee_id: Optional[str] = None,
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
    status: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """List attendance records"""
    query = {}
    if employee_id:
        query["employee_id"] = employee_id
    if from_date:
        query["date"] = {"$gte": from_date}
    if to_date:
        if "date" in query:
            query["date"]["$lte"] = to_date
        else:
            query["date"] = {"$lte": to_date}
    if status:
        query["status"] = status
    
    records = await db.attendance.find(query, {"_id": 0}).sort("date", -1).to_list(1000)
    return records

@router.get("/attendance/summary/{employee_id}/{month}")
async def get_attendance_summary(employee_id: str, month: str, current_user: dict = Depends(get_current_user)):
    """Get monthly attendance summary for an employee"""
    # month format: YYYY-MM
    try:
        year, mon = map(int, month.split("-"))
        start_date = date(year, mon, 1)
        end_date = (start_date + relativedelta(months=1)) - timedelta(days=1)
    except:
        raise HTTPException(status_code=400, detail="Invalid month format. Use YYYY-MM")
    
    records = await db.attendance.find({
        "employee_id": employee_id,
        "date": {"$gte": start_date.isoformat(), "$lte": end_date.isoformat()}
    }, {"_id": 0}).to_list(100)
    
    summary = {
        "present": 0, "absent": 0, "half_day": 0, "late": 0,
        "on_leave": 0, "holiday": 0, "week_off": 0,
        "total_working_hours": 0, "total_overtime": 0
    }
    
    for rec in records:
        status = rec.get("status", "present")
        summary[status] = summary.get(status, 0) + 1
        summary["total_working_hours"] += rec.get("working_hours", 0)
        summary["total_overtime"] += rec.get("overtime_hours", 0)
    
    # Calculate working days in month (excluding Sundays)
    total_days = (end_date - start_date).days + 1
    working_days = sum(1 for d in range(total_days) if (start_date + timedelta(days=d)).weekday() != 6)
    
    return {
        "employee_id": employee_id,
        "month": month,
        "total_days": total_days,
        "working_days": working_days,
        "summary": summary,
        "attendance_percentage": round((summary["present"] + summary["half_day"]*0.5) / working_days * 100, 1) if working_days > 0 else 0
    }

# ==================== LEAVE MANAGEMENT ENDPOINTS ====================
@router.post("/leave-types")
async def create_leave_type(data: LeaveTypeCreate, current_user: dict = Depends(get_current_user)):
    """Create a new leave type"""
    existing = await db.leave_types.find_one({"code": data.code.upper()})
    if existing:
        raise HTTPException(status_code=400, detail="Leave type code already exists")
    
    doc = {
        "id": str(uuid.uuid4()),
        **data.model_dump(),
        "code": data.code.upper(),
        "is_active": True,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.leave_types.insert_one(doc)
    return {k: v for k, v in doc.items() if k != '_id'}

@router.get("/leave-types")
async def list_leave_types(current_user: dict = Depends(get_current_user)):
    """List all leave types"""
    types = await db.leave_types.find({"is_active": True}, {"_id": 0}).to_list(100)
    if not types:
        # Create default leave types
        defaults = [
            {"name": "Casual Leave", "code": "CL", "annual_quota": 12, "carry_forward": False, "is_paid": True, "max_carry_forward": 0, "requires_approval": True},
            {"name": "Sick Leave", "code": "SL", "annual_quota": 12, "carry_forward": False, "is_paid": True, "max_carry_forward": 0, "requires_approval": True},
            {"name": "Earned Leave", "code": "EL", "annual_quota": 15, "carry_forward": True, "max_carry_forward": 30, "is_paid": True, "requires_approval": True},
            {"name": "Loss of Pay", "code": "LOP", "annual_quota": 0, "carry_forward": False, "is_paid": False, "max_carry_forward": 0, "requires_approval": True},
            {"name": "Maternity Leave", "code": "ML", "annual_quota": 182, "carry_forward": False, "is_paid": True, "max_carry_forward": 0, "requires_approval": True},
            {"name": "Paternity Leave", "code": "PL", "annual_quota": 15, "carry_forward": False, "is_paid": True, "max_carry_forward": 0, "requires_approval": True}
        ]
        for d in defaults:
            d["id"] = str(uuid.uuid4())
            d["is_active"] = True
            d["created_at"] = datetime.now(timezone.utc).isoformat()
        await db.leave_types.insert_many(defaults)
        # Re-fetch to get clean data without _id
        types = await db.leave_types.find({"is_active": True}, {"_id": 0}).to_list(100)
    return types

@router.post("/leave-applications", response_model=LeaveApplication)
async def apply_leave(data: LeaveApplicationCreate, current_user: dict = Depends(get_current_user)):
    """Apply for leave"""
    employee = await db.employees.find_one({"id": data.employee_id}, {"first_name": 1, "last_name": 1})
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    leave_type = await db.leave_types.find_one({"id": data.leave_type_id}, {"name": 1, "annual_quota": 1})
    if not leave_type:
        raise HTTPException(status_code=404, detail="Leave type not found")
    
    # Calculate days
    from_dt = datetime.strptime(data.from_date, "%Y-%m-%d")
    to_dt = datetime.strptime(data.to_date, "%Y-%m-%d")
    days = (to_dt - from_dt).days + 1
    if data.half_day:
        days = 0.5
    
    # Check leave balance
    year = datetime.now().year
    used = await db.leave_applications.aggregate([
        {"$match": {
            "employee_id": data.employee_id,
            "leave_type_id": data.leave_type_id,
            "status": "approved",
            "from_date": {"$regex": f"^{year}"}
        }},
        {"$group": {"_id": None, "total": {"$sum": "$days"}}}
    ]).to_list(1)
    
    used_days = used[0]["total"] if used else 0
    balance = leave_type.get("annual_quota", 0) - used_days
    
    if days > balance and leave_type.get("annual_quota", 0) > 0:
        raise HTTPException(status_code=400, detail=f"Insufficient leave balance. Available: {balance} days")
    
    now = datetime.now(timezone.utc).isoformat()
    app_doc = {
        "id": str(uuid.uuid4()),
        "employee_id": data.employee_id,
        "employee_name": f"{employee.get('first_name', '')} {employee.get('last_name', '')}".strip(),
        "leave_type_id": data.leave_type_id,
        "leave_type_name": leave_type.get("name"),
        "from_date": data.from_date,
        "to_date": data.to_date,
        "days": days,
        "reason": data.reason,
        "half_day": data.half_day,
        "half_day_type": data.half_day_type,
        "status": "pending",
        "approved_by": None,
        "approved_at": None,
        "rejection_reason": None,
        "created_at": now
    }
    
    await db.leave_applications.insert_one(app_doc)
    return LeaveApplication(**{k: v for k, v in app_doc.items() if k != '_id'})

@router.get("/leave-applications")
async def list_leave_applications(
    employee_id: Optional[str] = None,
    status: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """List leave applications"""
    query = {}
    if employee_id:
        query["employee_id"] = employee_id
    if status:
        query["status"] = status
    
    apps = await db.leave_applications.find(query, {"_id": 0}).sort("created_at", -1).to_list(1000)
    return apps

@router.put("/leave-applications/{app_id}/approve")
async def approve_leave(app_id: str, current_user: dict = Depends(get_current_user)):
    """Approve leave application"""
    result = await db.leave_applications.update_one(
        {"id": app_id, "status": "pending"},
        {"$set": {
            "status": "approved",
            "approved_by": current_user["id"],
            "approved_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Leave application not found or already processed")
    
    # Mark attendance as on_leave
    app = await db.leave_applications.find_one({"id": app_id}, {"_id": 0})
    if app:
        from_dt = datetime.strptime(app["from_date"], "%Y-%m-%d")
        to_dt = datetime.strptime(app["to_date"], "%Y-%m-%d")
        current = from_dt
        while current <= to_dt:
            await db.attendance.update_one(
                {"employee_id": app["employee_id"], "date": current.strftime("%Y-%m-%d")},
                {"$set": {"status": "on_leave"}},
                upsert=True
            )
            current += timedelta(days=1)
    
    return {"message": "Leave approved"}

@router.put("/leave-applications/{app_id}/reject")
async def reject_leave(app_id: str, reason: str = "", current_user: dict = Depends(get_current_user)):
    """Reject leave application"""
    result = await db.leave_applications.update_one(
        {"id": app_id, "status": "pending"},
        {"$set": {
            "status": "rejected",
            "approved_by": current_user["id"],
            "approved_at": datetime.now(timezone.utc).isoformat(),
            "rejection_reason": reason
        }}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Leave application not found or already processed")
    return {"message": "Leave rejected"}

@router.get("/leave-balance/{employee_id}")
async def get_leave_balance(employee_id: str, current_user: dict = Depends(get_current_user)):
    """Get leave balance for an employee"""
    year = datetime.now().year
    leave_types = await db.leave_types.find({"is_active": True}, {"_id": 0}).to_list(100)
    
    balances = []
    for lt in leave_types:
        used = await db.leave_applications.aggregate([
            {"$match": {
                "employee_id": employee_id,
                "leave_type_id": lt["id"],
                "status": "approved",
                "from_date": {"$regex": f"^{year}"}
            }},
            {"$group": {"_id": None, "total": {"$sum": "$days"}}}
        ]).to_list(1)
        
        used_days = used[0]["total"] if used else 0
        balance = lt.get("annual_quota", 0) - used_days
        
        balances.append({
            "leave_type_id": lt["id"],
            "leave_type": lt.get("name"),
            "code": lt.get("code"),
            "annual_quota": lt.get("annual_quota", 0),
            "used": used_days,
            "balance": max(0, balance)
        })
    
    return {"employee_id": employee_id, "year": year, "balances": balances}

# ==================== STATUTORY COMPLIANCE ENDPOINTS ====================
@router.get("/statutory/config")
async def get_statutory_config(current_user: dict = Depends(get_current_user)):
    """Get current statutory configuration"""
    fy = f"{datetime.now().year}-{str(datetime.now().year + 1)[2:]}" if datetime.now().month >= 4 else f"{datetime.now().year - 1}-{str(datetime.now().year)[2:]}"
    
    config = await db.statutory_config.find_one({"financial_year": fy, "is_active": True}, {"_id": 0})
    if not config:
        # Create default config
        config = {
            "id": str(uuid.uuid4()),
            "financial_year": fy,
            "pf_employee_percent": 12.0,
            "pf_employer_percent": 12.0,
            "pf_admin_charges": 0.5,
            "pf_wage_ceiling": 15000,
            "esi_employee_percent": 0.75,
            "esi_employer_percent": 3.25,
            "esi_wage_ceiling": 21000,
            "pt_slabs": [
                {"from_amt": 0, "to_amt": 10000, "amount": 0},
                {"from_amt": 10001, "to_amt": 15000, "amount": 150},
                {"from_amt": 15001, "to_amt": 999999999, "amount": 200}
            ],
            "lwf_employee": 20,
            "lwf_employer": 40,
            "is_active": True,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        await db.statutory_config.insert_one(config)
        # Re-fetch to get clean data without _id
        config = await db.statutory_config.find_one({"financial_year": fy, "is_active": True}, {"_id": 0})
    return config

@router.post("/statutory/config")
async def update_statutory_config(config: Dict[str, Any], current_user: dict = Depends(get_current_user)):
    """Update statutory configuration"""
    fy = config.get("financial_year") or f"{datetime.now().year}-{str(datetime.now().year + 1)[2:]}"
    
    config["updated_at"] = datetime.now(timezone.utc).isoformat()
    
    await db.statutory_config.update_one(
        {"financial_year": fy},
        {"$set": config},
        upsert=True
    )
    return {"message": "Configuration updated"}

@router.get("/statutory/calculate/{employee_id}")
async def calculate_statutory(employee_id: str, gross_salary: float, current_user: dict = Depends(get_current_user)):
    """Calculate statutory deductions for an employee"""
    config = await get_statutory_config(current_user)
    
    # PF Calculation
    pf_wage = min(gross_salary, config["pf_wage_ceiling"])
    pf_employee = round(pf_wage * config["pf_employee_percent"] / 100, 0)
    pf_employer = round(pf_wage * config["pf_employer_percent"] / 100, 0)
    
    # ESI Calculation (only if salary <= ceiling)
    esi_employee = 0
    esi_employer = 0
    if gross_salary <= config["esi_wage_ceiling"]:
        esi_employee = round(gross_salary * config["esi_employee_percent"] / 100, 0)
        esi_employer = round(gross_salary * config["esi_employer_percent"] / 100, 0)
    
    # PT Calculation
    pt = 0
    for slab in config.get("pt_slabs", []):
        if slab["from"] <= gross_salary <= slab["to"]:
            pt = slab["amount"]
            break
    
    # LWF
    lwf_employee = config.get("lwf_employee", 0)
    lwf_employer = config.get("lwf_employer", 0)
    
    total_employee = pf_employee + esi_employee + pt + lwf_employee
    total_employer = pf_employer + esi_employer + lwf_employer
    
    return {
        "gross_salary": gross_salary,
        "deductions": {
            "pf_employee": pf_employee,
            "esi_employee": esi_employee,
            "pt": pt,
            "lwf_employee": lwf_employee,
            "total_employee": total_employee
        },
        "employer_contribution": {
            "pf_employer": pf_employer,
            "esi_employer": esi_employer,
            "lwf_employer": lwf_employer,
            "total_employer": total_employer
        },
        "net_salary": gross_salary - total_employee,
        "ctc_components": total_employer
    }

# ==================== LOAN & ADVANCE MANAGEMENT ====================
@router.post("/loans")
async def create_loan(data: LoanCreate, current_user: dict = Depends(get_current_user)):
    """Create a loan/advance for an employee"""
    employee = await db.employees.find_one({"id": data.employee_id}, {"first_name": 1, "last_name": 1})
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    now = datetime.now(timezone.utc)
    loan_doc = {
        "id": str(uuid.uuid4()),
        **data.model_dump(),
        "employee_name": f"{employee.get('first_name', '')} {employee.get('last_name', '')}".strip(),
        "outstanding_amount": data.amount,
        "paid_emis": 0,
        "status": "active",
        "created_at": now.isoformat()
    }
    
    # Create EMI schedule
    emi_schedule = []
    emi_date = datetime.strptime(data.start_date, "%Y-%m-%d")
    for i in range(data.tenure_months):
        emi_schedule.append({
            "emi_no": i + 1,
            "due_date": emi_date.strftime("%Y-%m-%d"),
            "amount": data.emi_amount,
            "status": "pending"
        })
        emi_date += relativedelta(months=1)
    
    loan_doc["emi_schedule"] = emi_schedule
    
    await db.loans.insert_one(loan_doc)
    return {k: v for k, v in loan_doc.items() if k != '_id'}

@router.get("/loans")
async def list_loans(
    employee_id: Optional[str] = None,
    status: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """List all loans"""
    query = {}
    if employee_id:
        query["employee_id"] = employee_id
    if status:
        query["status"] = status
    
    loans = await db.loans.find(query, {"_id": 0}).sort("created_at", -1).to_list(1000)
    return loans

@router.put("/loans/{loan_id}/pay-emi")
async def pay_loan_emi(loan_id: str, emi_no: int, current_user: dict = Depends(get_current_user)):
    """Mark EMI as paid"""
    loan = await db.loans.find_one({"id": loan_id})
    if not loan:
        raise HTTPException(status_code=404, detail="Loan not found")
    
    emi_schedule = loan.get("emi_schedule", [])
    for emi in emi_schedule:
        if emi["emi_no"] == emi_no:
            emi["status"] = "paid"
            emi["paid_date"] = datetime.now(timezone.utc).strftime("%Y-%m-%d")
            break
    
    paid_count = len([e for e in emi_schedule if e["status"] == "paid"])
    outstanding = loan["amount"] - (paid_count * loan["emi_amount"])
    status = "closed" if paid_count >= loan["tenure_months"] else "active"
    
    await db.loans.update_one(
        {"id": loan_id},
        {"$set": {
            "emi_schedule": emi_schedule,
            "paid_emis": paid_count,
            "outstanding_amount": max(0, outstanding),
            "status": status
        }}
    )
    
    return {"message": f"EMI {emi_no} marked as paid", "outstanding": max(0, outstanding)}

# ==================== HOLIDAY CALENDAR ====================
@router.get("/holidays/{year}")
async def get_holidays(year: int, current_user: dict = Depends(get_current_user)):
    """Get holidays for a year"""
    holidays = await db.holidays.find({"year": year}, {"_id": 0}).to_list(100)
    if not holidays:
        # Create default Indian holidays
        defaults = [
            {"date": f"{year}-01-26", "name": "Republic Day", "type": "national"},
            {"date": f"{year}-03-29", "name": "Holi", "type": "restricted"},
            {"date": f"{year}-04-14", "name": "Ambedkar Jayanti", "type": "restricted"},
            {"date": f"{year}-05-01", "name": "May Day", "type": "national"},
            {"date": f"{year}-08-15", "name": "Independence Day", "type": "national"},
            {"date": f"{year}-10-02", "name": "Gandhi Jayanti", "type": "national"},
            {"date": f"{year}-10-31", "name": "Diwali", "type": "national"},
            {"date": f"{year}-11-01", "name": "Diwali Holiday", "type": "national"},
            {"date": f"{year}-12-25", "name": "Christmas", "type": "national"}
        ]
        for h in defaults:
            h["id"] = str(uuid.uuid4())
            h["year"] = year
        await db.holidays.insert_many(defaults)
        # Re-fetch to get clean data without _id
        holidays = await db.holidays.find({"year": year}, {"_id": 0}).to_list(100)
    return holidays

@router.post("/holidays")
async def add_holiday(
    date: str,
    name: str,
    holiday_type: str = "national",
    current_user: dict = Depends(get_current_user)
):
    """Add a holiday"""
    year = int(date[:4])
    doc = {
        "id": str(uuid.uuid4()),
        "date": date,
        "name": name,
        "type": holiday_type,
        "year": year,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.holidays.insert_one(doc)
    return {k: v for k, v in doc.items() if k != '_id'}
