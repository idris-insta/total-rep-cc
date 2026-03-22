from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, timezone
import uuid
from server import db, get_current_user

router = APIRouter()

class EmployeeCreate(BaseModel):
    employee_code: str
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    department: Optional[str] = None
    designation: Optional[str] = None
    location: Optional[str] = None
    date_of_joining: Optional[str] = None
    shift_timing: Optional[str] = None
    basic_salary: Optional[float] = 0
    hra: Optional[float] = 0
    pf: Optional[float] = 0
    esi: Optional[float] = 0
    pt: Optional[float] = 0

class Employee(BaseModel):
    id: str
    employee_code: Optional[str] = None
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    department: Optional[str] = None
    designation: Optional[str] = None
    location: Optional[str] = None
    date_of_joining: Optional[str] = None
    shift_timing: Optional[str] = None
    basic_salary: Optional[float] = 0
    hra: Optional[float] = 0
    pf: Optional[float] = 0
    esi: Optional[float] = 0
    pt: Optional[float] = 0
    status: Optional[str] = "active"
    created_at: Optional[str] = None
    employment_type: Optional[str] = None

class AttendanceCreate(BaseModel):
    employee_id: str
    date: str
    check_in: Optional[str] = None
    check_out: Optional[str] = None
    status: str
    hours_worked: float = 0

class Attendance(BaseModel):
    id: str
    employee_id: str
    date: str
    check_in: Optional[str] = None
    check_out: Optional[str] = None
    status: str
    hours_worked: float
    created_at: str

class LeaveRequestCreate(BaseModel):
    employee_id: str
    leave_type: str
    from_date: str
    to_date: str
    reason: str

class LeaveRequest(BaseModel):
    id: str
    employee_id: str
    leave_type: str
    from_date: str
    to_date: str
    reason: str
    status: str
    days: float
    created_at: str
    approved_by: Optional[str] = None
    approved_at: Optional[str] = None

class PayrollCreate(BaseModel):
    employee_id: str
    month: str
    year: int
    days_present: float
    days_absent: float
    overtime_hours: float = 0


@router.post("/employees", response_model=Employee)
async def create_employee(emp_data: EmployeeCreate, current_user: dict = Depends(get_current_user)):
    existing = await db.employees.find_one({'employee_code': emp_data.employee_code}, {'_id': 0})
    if existing:
        raise HTTPException(status_code=400, detail="Employee code already exists")
    
    emp_id = str(uuid.uuid4())
    emp_doc = {
        'id': emp_id,
        **emp_data.model_dump(),
        'status': 'active',
        'created_at': datetime.now(timezone.utc).isoformat()
    }
    
    await db.employees.insert_one(emp_doc)
    return Employee(**{k: v for k, v in emp_doc.items() if k != '_id'})

@router.get("/employees", response_model=List[Employee])
async def get_employees(department: Optional[str] = None, location: Optional[str] = None, current_user: dict = Depends(get_current_user)):
    query = {'status': 'active'}
    if department:
        query['department'] = department
    if location:
        query['location'] = location
    
    employees = await db.employees.find(query, {'_id': 0}).to_list(1000)
    return [Employee(**emp) for emp in employees]

@router.get("/employees/{emp_id}", response_model=Employee)
async def get_employee(emp_id: str, current_user: dict = Depends(get_current_user)):
    emp = await db.employees.find_one({'id': emp_id}, {'_id': 0})
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")
    return Employee(**emp)


@router.post("/attendance", response_model=Attendance)
async def mark_attendance(att_data: AttendanceCreate, current_user: dict = Depends(get_current_user)):
    existing = await db.attendance.find_one({'employee_id': att_data.employee_id, 'date': att_data.date}, {'_id': 0})
    if existing:
        raise HTTPException(status_code=400, detail="Attendance already marked for this date")
    
    att_id = str(uuid.uuid4())
    att_doc = {
        'id': att_id,
        **att_data.model_dump(),
        'created_at': datetime.now(timezone.utc).isoformat()
    }
    
    await db.attendance.insert_one(att_doc)
    return Attendance(**{k: v for k, v in att_doc.items() if k != '_id'})

@router.get("/attendance", response_model=List[Attendance])
async def get_attendance(employee_id: Optional[str] = None, date: Optional[str] = None, month: Optional[str] = None, current_user: dict = Depends(get_current_user)):
    query = {}
    if employee_id:
        query['employee_id'] = employee_id
    if date:
        query['date'] = date
    if month:
        query['date'] = {'$regex': f'^{month}'}
    
    attendance = await db.attendance.find(query, {'_id': 0}).sort('date', -1).to_list(1000)
    return [Attendance(**att) for att in attendance]


@router.post("/leave-requests", response_model=LeaveRequest)
async def create_leave_request(leave_data: LeaveRequestCreate, current_user: dict = Depends(get_current_user)):
    leave_id = str(uuid.uuid4())
    
    from_date = datetime.fromisoformat(leave_data.from_date)
    to_date = datetime.fromisoformat(leave_data.to_date)
    days = (to_date - from_date).days + 1
    
    leave_doc = {
        'id': leave_id,
        **leave_data.model_dump(),
        'days': days,
        'status': 'pending',
        'created_at': datetime.now(timezone.utc).isoformat()
    }
    
    await db.leave_requests.insert_one(leave_doc)
    return LeaveRequest(**{k: v for k, v in leave_doc.items() if k != '_id'})

@router.get("/leave-requests", response_model=List[LeaveRequest])
async def get_leave_requests(employee_id: Optional[str] = None, status: Optional[str] = None, current_user: dict = Depends(get_current_user)):
    query = {}
    if employee_id:
        query['employee_id'] = employee_id
    if status:
        query['status'] = status
    
    leaves = await db.leave_requests.find(query, {'_id': 0}).sort('created_at', -1).to_list(1000)
    return [LeaveRequest(**leave) for leave in leaves]

@router.put("/leave-requests/{leave_id}/approve")
async def approve_leave(leave_id: str, current_user: dict = Depends(get_current_user)):
    result = await db.leave_requests.update_one(
        {'id': leave_id},
        {'$set': {
            'status': 'approved',
            'approved_by': current_user['id'],
            'approved_at': datetime.now(timezone.utc).isoformat()
        }}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Leave request not found")
    
    return {'message': 'Leave approved'}

@router.put("/leave-requests/{leave_id}/reject")
async def reject_leave(leave_id: str, reason: str, current_user: dict = Depends(get_current_user)):
    result = await db.leave_requests.update_one(
        {'id': leave_id},
        {'$set': {
            'status': 'rejected',
            'rejected_by': current_user['id'],
            'rejected_at': datetime.now(timezone.utc).isoformat(),
            'rejection_reason': reason
        }}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Leave request not found")
    
    return {'message': 'Leave rejected'}


@router.post("/payroll")
async def generate_payroll(payroll_data: PayrollCreate, current_user: dict = Depends(get_current_user)):
    # WORKBOOK APPROVAL: Payroll run requires approval (admin for phase-1)
    approval = await db.approval_requests.find_one({
        "module": "HRMS",
        "entity_type": "Payroll",
        "entity_id": f"{payroll_data.employee_id}:{payroll_data.month}:{payroll_data.year}",
        "action": "Payroll Run",
        "status": "approved",
    }, {"_id": 0})
    if not approval:
        # create pending request and block
        await db.approval_requests.insert_one({
            "id": str(uuid.uuid4()),
            "module": "HRMS",
            "entity_type": "Payroll",
            "entity_id": f"{payroll_data.employee_id}:{payroll_data.month}:{payroll_data.year}",
            "action": "Payroll Run",
            "condition": "Any",
            "status": "pending",
            "approver_role": "admin",
            "requested_by": current_user["id"],
            "requested_at": datetime.now(timezone.utc).isoformat(),
            "decided_by": None,
            "decided_at": None,
            "payload": payroll_data.model_dump(),
            "notes": "Workbook rule: Payroll run requires approval"
        })
        raise HTTPException(status_code=409, detail="Approval required: Payroll Run")

    employee = await db.employees.find_one({'id': payroll_data.employee_id}, {'_id': 0})
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    payroll_id = str(uuid.uuid4())
    
    daily_rate = employee['basic_salary'] / 30
    earned_basic = daily_rate * payroll_data.days_present
    earned_hra = (employee['hra'] / 30) * payroll_data.days_present
    
    gross_salary = earned_basic + earned_hra
    
    pf_deduction = (employee['pf'] / 100) * earned_basic
    esi_deduction = (employee['esi'] / 100) * gross_salary if gross_salary <= 21000 else 0
    pt_deduction = employee['pt']
    
    total_deductions = pf_deduction + esi_deduction + pt_deduction
    net_salary = gross_salary - total_deductions
    
    payroll_doc = {
        'id': payroll_id,
        'employee_id': payroll_data.employee_id,
        'month': payroll_data.month,
        'year': payroll_data.year,
        'days_present': payroll_data.days_present,
        'days_absent': payroll_data.days_absent,
        'earned_basic': earned_basic,
        'earned_hra': earned_hra,
        'gross_salary': gross_salary,
        'pf_deduction': pf_deduction,
        'esi_deduction': esi_deduction,
        'pt_deduction': pt_deduction,
        'total_deductions': total_deductions,
        'net_salary': net_salary,
        'status': 'generated',
        'created_at': datetime.now(timezone.utc).isoformat(),
        'created_by': current_user['id']
    }
    
    await db.payroll.insert_one(payroll_doc)
    return {'message': 'Payroll generated', 'payroll_id': payroll_id, 'net_salary': net_salary}

@router.get("/payroll")
async def get_payroll(employee_id: Optional[str] = None, month: Optional[str] = None, year: Optional[int] = None, current_user: dict = Depends(get_current_user)):
    query = {}
    if employee_id:
        query['employee_id'] = employee_id
    if month:
        query['month'] = month
    if year:
        query['year'] = year
    
    payroll = await db.payroll.find(query, {'_id': 0}).sort('created_at', -1).to_list(1000)
    return payroll

@router.get("/reports/attendance-summary")
async def get_attendance_summary(month: str, current_user: dict = Depends(get_current_user)):
    attendance = await db.attendance.find({'date': {'$regex': f'^{month}'}}, {'_id': 0}).to_list(10000)
    
    summary = {}
    for att in attendance:
        emp_id = att['employee_id']
        if emp_id not in summary:
            summary[emp_id] = {'present': 0, 'absent': 0, 'leave': 0, 'total_hours': 0}
        
        if att['status'] == 'present':
            summary[emp_id]['present'] += 1
            summary[emp_id]['total_hours'] += att.get('hours_worked', 0)
        elif att['status'] == 'absent':
            summary[emp_id]['absent'] += 1
        elif att['status'] == 'leave':
            summary[emp_id]['leave'] += 1
    
    return summary