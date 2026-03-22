"""
Payroll Module
Handles:
- Dual Salary (Daily/Monthly wage types)
- Attendance-to-Payroll linking
- Statutory Deductions (PF, ESI, PT, TDS)
- Sales Incentives & Bonuses
- Payslip Generation
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from typing import List, Optional, Dict
from datetime import datetime, timezone, date
from dateutil.relativedelta import relativedelta
import uuid
import calendar
from server import db, get_current_user
from utils.document_numbering import generate_document_number

router = APIRouter()


# ==================== SALARY STRUCTURE MODELS ====================
class SalaryComponentCreate(BaseModel):
    component_name: str
    component_type: str  # earning, deduction, reimbursement
    calculation_type: str  # fixed, percentage, formula
    percentage_of: Optional[str] = None  # basic, gross, etc.
    percentage_value: float = 0
    fixed_amount: float = 0
    is_taxable: bool = True
    is_statutory: bool = False
    statutory_type: Optional[str] = None  # PF, ESI, PT, TDS
    max_limit: float = 0  # For PF/ESI capping
    is_active: bool = True


class SalaryComponent(BaseModel):
    id: str
    component_name: str
    component_type: str
    calculation_type: str
    percentage_of: Optional[str] = None
    percentage_value: float
    fixed_amount: float
    is_taxable: bool
    is_statutory: bool
    statutory_type: Optional[str] = None
    max_limit: float
    is_active: bool
    created_at: str


class EmployeeSalaryStructure(BaseModel):
    employee_id: str
    wage_type: str  # monthly, daily
    basic_salary: float
    hra: float = 0
    conveyance: float = 0
    special_allowance: float = 0
    other_allowances: float = 0
    pf_applicable: bool = True
    esi_applicable: bool = True
    pt_applicable: bool = True
    tds_applicable: bool = False
    tds_percent: float = 0
    effective_from: str


# ==================== PAYROLL MODELS ====================
class PayrollCreate(BaseModel):
    payroll_month: str  # YYYY-MM format
    employee_id: str
    working_days: int
    present_days: float
    leaves_taken: float = 0
    overtime_hours: float = 0
    overtime_rate: float = 0
    incentive_amount: float = 0
    bonus_amount: float = 0
    advance_deduction: float = 0
    loan_deduction: float = 0
    other_deductions: float = 0
    remarks: Optional[str] = None


class Payroll(BaseModel):
    id: str
    payroll_no: Optional[str] = None
    payroll_month: Optional[str] = None
    employee_id: Optional[str] = None
    employee_name: Optional[str] = None
    employee_code: Optional[str] = None
    department: Optional[str] = None
    branch_id: Optional[str] = None
    
    # Attendance
    working_days: int = 0
    present_days: float = 0
    leaves_taken: float = 0
    lop_days: float = 0  # Loss of Pay days
    
    # Earnings
    basic_salary: float = 0
    basic_earned: float = 0
    hra: float = 0
    conveyance: float = 0
    special_allowance: float = 0
    other_allowances: float = 0
    overtime_amount: float = 0
    incentive_amount: float = 0
    bonus_amount: float = 0
    gross_salary: float = 0
    
    # Deductions
    pf_employee: float = 0
    pf_employer: float = 0
    esi_employee: float = 0
    esi_employer: float = 0
    professional_tax: float = 0
    tds: float = 0
    advance_deduction: float = 0
    loan_deduction: float = 0
    other_deductions: float = 0
    total_deductions: float = 0
    
    # Net
    net_salary: float = 0
    ctc: float = 0  # Cost to Company (including employer contributions)
    
    status: Optional[str] = None  # draft, pending_approval, approved, paid
    remarks: Optional[str] = None
    created_at: Optional[str] = None
    created_by: Optional[str] = None
    approved_by: Optional[str] = None
    approved_at: Optional[str] = None
    paid_at: Optional[str] = None


# ==================== STATUTORY RATES ====================
STATUTORY_RATES = {
    'PF': {
        'employee': 12.0,  # 12% of basic
        'employer': 12.0,  # 12% of basic (3.67% EPF + 8.33% EPS)
        'wage_ceiling': 15000  # PF applicable on basic up to 15000
    },
    'ESI': {
        'employee': 0.75,  # 0.75% of gross
        'employer': 3.25,  # 3.25% of gross
        'wage_ceiling': 21000  # ESI applicable if gross <= 21000
    },
    'PT': {  # Professional Tax (varies by state, using Maharashtra rates)
        'slabs': [
            {'min': 0, 'max': 7500, 'tax': 0},
            {'min': 7501, 'max': 10000, 'tax': 175},
            {'min': 10001, 'max': float('inf'), 'tax': 200},  # 200 for 11 months, 300 for Feb
        ]
    }
}


def calculate_professional_tax(gross_salary: float, month: int = 1) -> float:
    """Calculate professional tax based on salary slab"""
    for slab in STATUTORY_RATES['PT']['slabs']:
        if slab['min'] <= gross_salary <= slab['max']:
            tax = slab['tax']
            # February has higher PT in some states
            if month == 2 and tax == 200:
                return 300
            return tax
    return 200  # Default


def calculate_pf(basic: float) -> Dict[str, float]:
    """Calculate PF contributions"""
    pf_basic = min(basic, STATUTORY_RATES['PF']['wage_ceiling'])
    return {
        'employee': round(pf_basic * STATUTORY_RATES['PF']['employee'] / 100, 0),
        'employer': round(pf_basic * STATUTORY_RATES['PF']['employer'] / 100, 0)
    }


def calculate_esi(gross: float) -> Dict[str, float]:
    """Calculate ESI contributions if applicable"""
    if gross > STATUTORY_RATES['ESI']['wage_ceiling']:
        return {'employee': 0, 'employer': 0}
    return {
        'employee': round(gross * STATUTORY_RATES['ESI']['employee'] / 100, 0),
        'employer': round(gross * STATUTORY_RATES['ESI']['employer'] / 100, 0)
    }


# ==================== SALARY STRUCTURE ENDPOINTS ====================
@router.post("/salary-structures")
async def create_salary_structure(
    data: EmployeeSalaryStructure,
    current_user: dict = Depends(get_current_user)
):
    """Create/update employee salary structure"""
    if current_user['role'] not in ['admin', 'hr']:
        raise HTTPException(status_code=403, detail="Access denied")
    
    struct_id = str(uuid.uuid4())
    
    # Deactivate previous structure
    await db.salary_structures.update_many(
        {'employee_id': data.employee_id, 'is_active': True},
        {'$set': {'is_active': False}}
    )
    
    struct_doc = {
        'id': struct_id,
        **data.model_dump(),
        'is_active': True,
        'created_at': datetime.now(timezone.utc).isoformat(),
        'created_by': current_user['id']
    }
    
    await db.salary_structures.insert_one(struct_doc)
    return {'message': 'Salary structure created', 'id': struct_id}


@router.get("/salary-structures/{employee_id}")
async def get_salary_structure(employee_id: str, current_user: dict = Depends(get_current_user)):
    """Get employee's current salary structure"""
    structure = await db.salary_structures.find_one(
        {'employee_id': employee_id, 'is_active': True},
        {'_id': 0}
    )
    if not structure:
        raise HTTPException(status_code=404, detail="Salary structure not found")
    return structure


# ==================== PAYROLL ENDPOINTS ====================
@router.post("/process", response_model=Payroll)
async def process_payroll(data: PayrollCreate, current_user: dict = Depends(get_current_user)):
    """Process payroll for an employee"""
    # Get employee details
    employee = await db.employees.find_one({'id': data.employee_id}, {'_id': 0})
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    # Get salary structure
    structure = await db.salary_structures.find_one(
        {'employee_id': data.employee_id, 'is_active': True},
        {'_id': 0}
    )
    if not structure:
        raise HTTPException(status_code=404, detail="Salary structure not found")
    
    payroll_id = str(uuid.uuid4())
    payroll_no = await generate_document_number(db, 'payroll', 'HO')
    
    # Parse month for PT calculation
    payroll_month_date = datetime.strptime(data.payroll_month + '-01', '%Y-%m-%d')
    month_num = payroll_month_date.month
    
    # Calculate based on wage type
    if structure['wage_type'] == 'daily':
        daily_rate = structure['basic_salary']
        basic_earned = daily_rate * data.present_days
        hra = 0
        conveyance = 0
        special_allowance = 0
        other_allowances = 0
    else:  # monthly
        lop_days = max(0, data.working_days - data.present_days - data.leaves_taken)
        per_day = structure['basic_salary'] / data.working_days
        basic_earned = structure['basic_salary'] - (per_day * lop_days)
        hra = structure.get('hra', 0) * (data.present_days / data.working_days)
        conveyance = structure.get('conveyance', 0)
        special_allowance = structure.get('special_allowance', 0) * (data.present_days / data.working_days)
        other_allowances = structure.get('other_allowances', 0)
    
    # Overtime
    overtime_amount = data.overtime_hours * data.overtime_rate
    
    # Gross salary
    gross_salary = (
        basic_earned + hra + conveyance + special_allowance + 
        other_allowances + overtime_amount + 
        data.incentive_amount + data.bonus_amount
    )
    
    # Statutory deductions
    pf = {'employee': 0, 'employer': 0}
    esi = {'employee': 0, 'employer': 0}
    pt = 0
    tds = 0
    
    if structure.get('pf_applicable', True):
        pf = calculate_pf(basic_earned)
    
    if structure.get('esi_applicable', True):
        esi = calculate_esi(gross_salary)
    
    if structure.get('pt_applicable', True):
        pt = calculate_professional_tax(gross_salary, month_num)
    
    if structure.get('tds_applicable', False):
        tds = round(gross_salary * structure.get('tds_percent', 0) / 100, 0)
    
    # Total deductions
    total_deductions = (
        pf['employee'] + esi['employee'] + pt + tds +
        data.advance_deduction + data.loan_deduction + data.other_deductions
    )
    
    # Net salary
    net_salary = gross_salary - total_deductions
    
    # CTC (Cost to Company)
    ctc = gross_salary + pf['employer'] + esi['employer']
    
    # LOP days
    lop_days = max(0, data.working_days - data.present_days - data.leaves_taken) if structure['wage_type'] == 'monthly' else 0
    
    payroll_doc = {
        'id': payroll_id,
        'payroll_no': payroll_no,
        'payroll_month': data.payroll_month,
        'employee_id': data.employee_id,
        'employee_name': employee.get('name'),
        'employee_code': employee.get('employee_code'),
        'department': employee.get('department'),
        'branch_id': employee.get('branch_id'),
        
        'working_days': data.working_days,
        'present_days': data.present_days,
        'leaves_taken': data.leaves_taken,
        'lop_days': lop_days,
        
        'basic_salary': structure['basic_salary'],
        'basic_earned': round(basic_earned, 0),
        'hra': round(hra, 0),
        'conveyance': round(conveyance, 0),
        'special_allowance': round(special_allowance, 0),
        'other_allowances': round(other_allowances, 0),
        'overtime_amount': round(overtime_amount, 0),
        'incentive_amount': data.incentive_amount,
        'bonus_amount': data.bonus_amount,
        'gross_salary': round(gross_salary, 0),
        
        'pf_employee': pf['employee'],
        'pf_employer': pf['employer'],
        'esi_employee': esi['employee'],
        'esi_employer': esi['employer'],
        'professional_tax': pt,
        'tds': tds,
        'advance_deduction': data.advance_deduction,
        'loan_deduction': data.loan_deduction,
        'other_deductions': data.other_deductions,
        'total_deductions': round(total_deductions, 0),
        
        'net_salary': round(net_salary, 0),
        'ctc': round(ctc, 0),
        
        'status': 'draft',
        'remarks': data.remarks,
        'created_at': datetime.now(timezone.utc).isoformat(),
        'created_by': current_user['id'],
        'approved_by': None,
        'approved_at': None,
        'paid_at': None
    }
    
    await db.payroll.insert_one(payroll_doc)
    return Payroll(**{k: v for k, v in payroll_doc.items() if k != '_id'})


@router.get("/", response_model=List[Payroll])
async def get_payrolls(
    payroll_month: Optional[str] = None,
    employee_id: Optional[str] = None,
    status: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Get all payroll records"""
    query = {}
    if payroll_month:
        query['payroll_month'] = payroll_month
    if employee_id:
        query['employee_id'] = employee_id
    if status:
        query['status'] = status
    
    payrolls = await db.payroll.find(query, {'_id': 0}).sort('created_at', -1).to_list(500)
    return [Payroll(**p) for p in payrolls]


@router.get("/{payroll_id}", response_model=Payroll)
async def get_payroll(payroll_id: str, current_user: dict = Depends(get_current_user)):
    """Get payroll by ID"""
    payroll = await db.payroll.find_one({'id': payroll_id}, {'_id': 0})
    if not payroll:
        raise HTTPException(status_code=404, detail="Payroll not found")
    return Payroll(**payroll)


@router.put("/{payroll_id}/approve")
async def approve_payroll(payroll_id: str, current_user: dict = Depends(get_current_user)):
    """Approve payroll - requires director approval"""
    # Check for approval
    approval = await db.approval_requests.find_one({
        'module': 'HRMS',
        'entity_type': 'Payroll',
        'entity_id': payroll_id,
        'action': 'Generate Payroll',
        'status': 'approved'
    }, {'_id': 0})
    
    if not approval and current_user['role'] != 'admin':
        # Create approval request
        await db.approval_requests.insert_one({
            'id': str(uuid.uuid4()),
            'module': 'HRMS',
            'entity_type': 'Payroll',
            'entity_id': payroll_id,
            'action': 'Generate Payroll',
            'condition': 'Payroll requires approval',
            'status': 'pending',
            'approver_role': 'admin',
            'requested_by': current_user['id'],
            'requested_at': datetime.now(timezone.utc).isoformat(),
            'payload': {'payroll_id': payroll_id},
            'notes': 'Payroll approval request'
        })
        raise HTTPException(status_code=409, detail="Approval required: Generate Payroll")
    
    await db.payroll.update_one(
        {'id': payroll_id},
        {'$set': {
            'status': 'approved',
            'approved_by': current_user['id'],
            'approved_at': datetime.now(timezone.utc).isoformat()
        }}
    )
    
    return {'message': 'Payroll approved', 'payroll_id': payroll_id}


@router.put("/{payroll_id}/mark-paid")
async def mark_payroll_paid(payroll_id: str, current_user: dict = Depends(get_current_user)):
    """Mark payroll as paid"""
    payroll = await db.payroll.find_one({'id': payroll_id}, {'_id': 0})
    if not payroll:
        raise HTTPException(status_code=404, detail="Payroll not found")
    
    if payroll['status'] != 'approved':
        raise HTTPException(status_code=400, detail="Payroll not approved")
    
    await db.payroll.update_one(
        {'id': payroll_id},
        {'$set': {
            'status': 'paid',
            'paid_at': datetime.now(timezone.utc).isoformat()
        }}
    )
    
    return {'message': 'Payroll marked as paid', 'payroll_id': payroll_id}


# ==================== PAYSLIP GENERATION ====================
@router.get("/{payroll_id}/payslip")
async def get_payslip(payroll_id: str, current_user: dict = Depends(get_current_user)):
    """Generate payslip data for printing"""
    payroll = await db.payroll.find_one({'id': payroll_id}, {'_id': 0})
    if not payroll:
        raise HTTPException(status_code=404, detail="Payroll not found")
    
    # Get employee details
    employee = await db.employees.find_one({'id': payroll['employee_id']}, {'_id': 0})
    
    # Get company details
    company = await db.company_settings.find_one({}, {'_id': 0})
    
    payslip = {
        'company': company or {'name': 'InstaBiz Industrial ERP'},
        'employee': {
            'name': payroll['employee_name'],
            'code': payroll['employee_code'],
            'department': payroll['department'],
            'designation': employee.get('designation') if employee else None,
            'bank_name': employee.get('bank_name') if employee else None,
            'bank_account': employee.get('bank_account') if employee else None,
            'pan': employee.get('pan') if employee else None,
            'uan': employee.get('uan') if employee else None,
            'esi_no': employee.get('esi_no') if employee else None,
        },
        'payroll_month': payroll['payroll_month'],
        'attendance': {
            'working_days': payroll['working_days'],
            'present_days': payroll['present_days'],
            'leaves_taken': payroll['leaves_taken'],
            'lop_days': payroll['lop_days']
        },
        'earnings': {
            'Basic Salary': payroll['basic_earned'],
            'HRA': payroll['hra'],
            'Conveyance': payroll['conveyance'],
            'Special Allowance': payroll['special_allowance'],
            'Other Allowances': payroll['other_allowances'],
            'Overtime': payroll['overtime_amount'],
            'Incentive': payroll['incentive_amount'],
            'Bonus': payroll['bonus_amount'],
        },
        'deductions': {
            'PF (Employee)': payroll['pf_employee'],
            'ESI (Employee)': payroll['esi_employee'],
            'Professional Tax': payroll['professional_tax'],
            'TDS': payroll['tds'],
            'Advance': payroll['advance_deduction'],
            'Loan': payroll['loan_deduction'],
            'Other': payroll['other_deductions'],
        },
        'gross_salary': payroll['gross_salary'],
        'total_deductions': payroll['total_deductions'],
        'net_salary': payroll['net_salary'],
        'employer_contributions': {
            'PF (Employer)': payroll['pf_employer'],
            'ESI (Employer)': payroll['esi_employer'],
        },
        'ctc': payroll['ctc']
    }
    
    return payslip


# ==================== BULK PAYROLL PROCESSING ====================
@router.post("/process-bulk")
async def process_bulk_payroll(
    payroll_month: str,
    branch_id: Optional[str] = None,
    department: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Process payroll for multiple employees based on attendance"""
    if current_user['role'] not in ['admin', 'hr']:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Get employees with active salary structure
    emp_query = {}
    if branch_id:
        emp_query['branch_id'] = branch_id
    if department:
        emp_query['department'] = department
    
    employees = await db.employees.find(emp_query, {'_id': 0}).to_list(1000)
    
    # Parse month for working days calculation
    year, month = map(int, payroll_month.split('-'))
    working_days = calendar.monthrange(year, month)[1]  # Total days in month
    
    processed = []
    errors = []
    
    for emp in employees:
        try:
            # Check if already processed
            existing = await db.payroll.find_one({
                'employee_id': emp['id'],
                'payroll_month': payroll_month
            }, {'_id': 0})
            
            if existing:
                continue
            
            # Get attendance for the month
            attendance_records = await db.attendance.find({
                'employee_id': emp['id'],
                'date': {'$regex': f'^{payroll_month}'}
            }, {'_id': 0}).to_list(31)
            
            present_days = sum(1 for a in attendance_records if a.get('status') in ['present', 'half_day'])
            half_days = sum(0.5 for a in attendance_records if a.get('status') == 'half_day')
            present_days = present_days - half_days + (half_days * 0.5)
            
            # Get leaves
            leaves = await db.leave_requests.find({
                'employee_id': emp['id'],
                'status': 'approved',
                'from_date': {'$lte': f'{payroll_month}-31'},
                'to_date': {'$gte': f'{payroll_month}-01'}
            }, {'_id': 0}).to_list(50)
            
            leaves_taken = sum(l.get('days', 0) for l in leaves)
            
            # Process payroll
            payroll_data = PayrollCreate(
                payroll_month=payroll_month,
                employee_id=emp['id'],
                working_days=working_days,
                present_days=present_days,
                leaves_taken=leaves_taken
            )
            
            result = await process_payroll(payroll_data, current_user)
            processed.append({'employee_id': emp['id'], 'payroll_id': result.id})
            
        except Exception as e:
            errors.append({'employee_id': emp['id'], 'error': str(e)})
    
    return {
        'message': f'Processed {len(processed)} payrolls',
        'processed': processed,
        'errors': errors,
        'total_employees': len(employees)
    }
