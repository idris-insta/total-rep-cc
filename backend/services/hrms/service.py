"""
HRMS Services - Business Logic Layer for HRMS module
"""
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone, timedelta

from repositories.hrms import (
    employee_repository,
    attendance_repository,
    leave_request_repository,
    payroll_repository
)
from core.exceptions import NotFoundError, ValidationError, BusinessRuleError, DuplicateError
from core.legacy_db import db


class EmployeeService:
    """Business logic for Employee management"""
    
    def __init__(self):
        self.repo = employee_repository
    
    async def get_all_employees(self, filters: Optional[Dict] = None) -> List[Dict[str, Any]]:
        """Get all employees with optional filters"""
        query = {}
        if filters:
            if filters.get('department'):
                query['department'] = filters['department']
            if filters.get('status'):
                query['status'] = filters['status']
            if filters.get('search'):
                return await self.repo.search(filters['search'])
        return await self.repo.get_all(query)
    
    async def get_employee(self, employee_id: str) -> Dict[str, Any]:
        """Get a single employee"""
        return await self.repo.get_by_id_or_raise(employee_id, "Employee")
    
    async def create_employee(self, data: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """Create a new employee"""
        # Check for duplicate employee code
        existing = await self.repo.get_by_code(data['employee_code'])
        if existing:
            raise DuplicateError("Employee", f"code '{data['employee_code']}'")
        
        data['status'] = 'active'
        return await self.repo.create(data, user_id)
    
    async def update_employee(self, employee_id: str, data: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """Update an existing employee"""
        return await self.repo.update_or_raise(employee_id, data, user_id, "Employee")
    
    async def terminate_employee(self, employee_id: str, termination_date: str, reason: str, user_id: str) -> Dict[str, Any]:
        """Terminate an employee"""
        return await self.repo.update_or_raise(employee_id, {
            'status': 'terminated',
            'termination_date': termination_date,
            'termination_reason': reason
        }, user_id, "Employee")


class AttendanceService:
    """Business logic for Attendance management"""
    
    def __init__(self):
        self.repo = attendance_repository
    
    async def mark_attendance(self, data: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """Mark attendance for an employee"""
        # Check for existing attendance
        existing = await self.repo.get_by_employee_and_date(data['employee_id'], data['date'])
        if existing:
            # Update existing record
            return await self.repo.update(existing['id'], data, user_id)
        
        # Create new attendance record
        return await self.repo.create(data, user_id)
    
    async def get_attendance(self, employee_id: str = None, date: str = None) -> List[Dict[str, Any]]:
        """Get attendance records"""
        if employee_id and date:
            record = await self.repo.get_by_employee_and_date(employee_id, date)
            return [record] if record else []
        elif employee_id:
            return await self.repo.get_by_employee(employee_id)
        elif date:
            return await self.repo.get_by_date(date)
        return await self.repo.get_all()
    
    async def check_in(self, employee_id: str, user_id: str) -> Dict[str, Any]:
        """Record employee check-in"""
        today = datetime.now(timezone.utc).strftime('%Y-%m-%d')
        now = datetime.now(timezone.utc).strftime('%H:%M:%S')
        
        return await self.mark_attendance({
            'employee_id': employee_id,
            'date': today,
            'check_in': now,
            'status': 'present'
        }, user_id)
    
    async def check_out(self, employee_id: str, user_id: str) -> Dict[str, Any]:
        """Record employee check-out"""
        today = datetime.now(timezone.utc).strftime('%Y-%m-%d')
        now = datetime.now(timezone.utc).strftime('%H:%M:%S')
        
        existing = await self.repo.get_by_employee_and_date(employee_id, today)
        if not existing:
            raise BusinessRuleError("Employee has not checked in today")
        
        # Calculate hours worked
        check_in_time = datetime.strptime(existing['check_in'], '%H:%M:%S')
        check_out_time = datetime.strptime(now, '%H:%M:%S')
        hours_worked = (check_out_time - check_in_time).total_seconds() / 3600
        
        return await self.repo.update(existing['id'], {
            'check_out': now,
            'hours_worked': round(hours_worked, 2)
        }, user_id)
    
    async def get_monthly_summary(self, employee_id: str, year: int, month: int) -> Dict[str, Any]:
        """Get monthly attendance summary"""
        return await self.repo.get_monthly_summary(employee_id, year, month)


class LeaveRequestService:
    """Business logic for Leave Request management"""
    
    def __init__(self):
        self.repo = leave_request_repository
    
    async def get_all_requests(self, filters: Optional[Dict] = None) -> List[Dict[str, Any]]:
        """Get all leave requests"""
        query = {}
        if filters:
            if filters.get('status'):
                query['status'] = filters['status']
            if filters.get('employee_id'):
                query['employee_id'] = filters['employee_id']
        return await self.repo.get_all(query)
    
    async def create_request(self, data: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """Create a leave request"""
        # Calculate days
        from_date = datetime.strptime(data['from_date'], '%Y-%m-%d')
        to_date = datetime.strptime(data['to_date'], '%Y-%m-%d')
        days = (to_date - from_date).days + 1
        
        data['days'] = days
        data['status'] = 'pending'
        
        return await self.repo.create(data, user_id)
    
    async def approve_request(self, request_id: str, user_id: str) -> Dict[str, Any]:
        """Approve a leave request"""
        request = await self.repo.get_by_id_or_raise(request_id, "Leave Request")
        
        if request.get('status') != 'pending':
            raise BusinessRuleError(f"Cannot approve request with status '{request.get('status')}'")
        
        return await self.repo.update(request_id, {
            'status': 'approved',
            'approved_by': user_id,
            'approved_at': datetime.now(timezone.utc).isoformat()
        }, user_id)
    
    async def reject_request(self, request_id: str, reason: str, user_id: str) -> Dict[str, Any]:
        """Reject a leave request"""
        request = await self.repo.get_by_id_or_raise(request_id, "Leave Request")
        
        if request.get('status') != 'pending':
            raise BusinessRuleError(f"Cannot reject request with status '{request.get('status')}'")
        
        return await self.repo.update(request_id, {
            'status': 'rejected',
            'rejection_reason': reason,
            'rejected_by': user_id,
            'rejected_at': datetime.now(timezone.utc).isoformat()
        }, user_id)
    
    async def get_pending_requests(self) -> List[Dict[str, Any]]:
        """Get all pending leave requests"""
        return await self.repo.get_pending()


class PayrollService:
    """Business logic for Payroll management"""
    
    def __init__(self):
        self.repo = payroll_repository
    
    async def generate_payroll(self, employee_id: str, year: int, month: int, user_id: str) -> Dict[str, Any]:
        """Generate payroll for an employee"""
        # Check if already exists
        existing = await self.repo.get_by_employee_and_month(employee_id, year, month)
        if existing:
            raise BusinessRuleError(f"Payroll already generated for {year}-{month:02d}")
        
        # Get employee details
        employee = await employee_repository.get_by_id(employee_id)
        if not employee:
            raise NotFoundError("Employee", employee_id)
        
        # Get attendance summary
        attendance = await attendance_repository.get_monthly_summary(employee_id, year, month)
        
        # Calculate salary components
        days_in_month = 30  # Simplified
        working_days = attendance.get('present', 0) + (attendance.get('half_day', 0) * 0.5)
        
        basic = employee.get('basic_salary', 0)
        hra = employee.get('hra', 0)
        
        # Pro-rate salary based on attendance
        attendance_factor = working_days / days_in_month
        gross = (basic + hra) * attendance_factor
        
        # Deductions
        pf = employee.get('pf', 0)
        esi = employee.get('esi', 0)
        pt = employee.get('pt', 0)
        total_deductions = pf + esi + pt
        
        net_salary = gross - total_deductions
        
        payroll_data = {
            'employee_id': employee_id,
            'employee_name': employee.get('name'),
            'employee_code': employee.get('employee_code'),
            'year': year,
            'month': month,
            'days_present': attendance.get('present', 0),
            'days_absent': attendance.get('absent', 0),
            'half_days': attendance.get('half_day', 0),
            'basic_salary': round(basic * attendance_factor, 2),
            'hra': round(hra * attendance_factor, 2),
            'gross_salary': round(gross, 2),
            'pf_deduction': pf,
            'esi_deduction': esi,
            'pt_deduction': pt,
            'total_deductions': total_deductions,
            'net_salary': round(net_salary, 2),
            'status': 'generated'
        }
        
        return await self.repo.create(payroll_data, user_id)
    
    async def get_payroll(self, employee_id: str = None, year: int = None, month: int = None) -> List[Dict[str, Any]]:
        """Get payroll records"""
        if employee_id and year and month:
            record = await self.repo.get_by_employee_and_month(employee_id, year, month)
            return [record] if record else []
        elif year and month:
            return await self.repo.get_by_month(year, month)
        elif employee_id:
            return await self.repo.get_by_employee(employee_id)
        return await self.repo.get_all()


# Service instances
employee_service = EmployeeService()
attendance_service = AttendanceService()
leave_request_service = LeaveRequestService()
payroll_service = PayrollService()
