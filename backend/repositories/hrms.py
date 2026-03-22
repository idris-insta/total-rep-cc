"""
HRMS Repositories - Data Access Layer for HRMS module (PostgreSQL/SQLAlchemy)
"""
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
from sqlalchemy import select, and_

from repositories.base import BaseRepository
from models.entities.hrms import Employee, Attendance, LeaveRequest, LeaveType, SalaryStructure, Payroll, Loan, Holiday
from core.database import async_session_factory


class EmployeeRepository(BaseRepository[Employee]):
    """Repository for Employee operations"""
    model = Employee
    
    async def get_by_department(self, department: str) -> List[Dict[str, Any]]:
        """Get employees by department"""
        return await self.get_all({'department': department})
    
    async def get_by_status(self, status: str) -> List[Dict[str, Any]]:
        """Get employees by status (active, inactive, terminated)"""
        return await self.get_all({'status': status})
    
    async def get_by_code(self, employee_code: str) -> Optional[Dict[str, Any]]:
        """Get employee by code"""
        return await self.get_one({'employee_code': employee_code})
    
    async def search(self, query: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Search employees by name, code, or email"""
        return await super().search(query, ['name', 'employee_code', 'email'], limit)


class AttendanceRepository(BaseRepository[Attendance]):
    """Repository for Attendance operations"""
    model = Attendance
    
    async def get_by_employee(self, employee_id: str) -> List[Dict[str, Any]]:
        """Get attendance records for an employee"""
        return await self.get_all({'employee_id': employee_id})
    
    async def get_by_date(self, date: str) -> List[Dict[str, Any]]:
        """Get all attendance records for a date"""
        return await self.get_all({'date': date})
    
    async def get_by_employee_and_date(self, employee_id: str, date: str) -> Optional[Dict[str, Any]]:
        """Get attendance record for an employee on a specific date"""
        return await self.get_one({'employee_id': employee_id, 'date': date})
    
    async def get_monthly_summary(self, employee_id: str, year: int, month: int) -> Dict[str, Any]:
        """Get monthly attendance summary for an employee"""
        async with async_session_factory() as session:
            month_str = f"{year}-{month:02d}"
            result = await session.execute(
                select(Attendance).where(
                    and_(
                        Attendance.employee_id == employee_id,
                        Attendance.date.cast(str).like(f'{month_str}%')
                    )
                )
            )
            records = [self._to_dict(obj) for obj in result.scalars().all()]
        
        present = len([r for r in records if r.get('status') == 'present'])
        absent = len([r for r in records if r.get('status') == 'absent'])
        half_day = len([r for r in records if r.get('status') == 'half_day'])
        total_hours = sum(r.get('hours_worked', 0) for r in records)
        
        return {
            'employee_id': employee_id,
            'year': year,
            'month': month,
            'present': present,
            'absent': absent,
            'half_day': half_day,
            'total_days': present + absent + half_day,
            'total_hours': total_hours
        }


class LeaveRequestRepository(BaseRepository[LeaveRequest]):
    """Repository for Leave Request operations"""
    model = LeaveRequest
    
    async def get_by_employee(self, employee_id: str) -> List[Dict[str, Any]]:
        """Get leave requests for an employee"""
        return await self.get_all({'employee_id': employee_id})
    
    async def get_by_status(self, status: str) -> List[Dict[str, Any]]:
        """Get leave requests by status"""
        return await self.get_all({'status': status})
    
    async def get_pending(self) -> List[Dict[str, Any]]:
        """Get pending leave requests"""
        return await self.get_by_status('pending')


class LeaveTypeRepository(BaseRepository[LeaveType]):
    """Repository for Leave Type operations"""
    model = LeaveType
    
    async def get_active(self) -> List[Dict[str, Any]]:
        """Get active leave types"""
        return await self.get_all({'is_active': True})


class SalaryStructureRepository(BaseRepository[SalaryStructure]):
    """Repository for Salary Structure operations"""
    model = SalaryStructure
    
    async def get_active(self) -> List[Dict[str, Any]]:
        """Get active salary structures"""
        return await self.get_all({'is_active': True})


class PayrollRepository(BaseRepository[Payroll]):
    """Repository for Payroll operations"""
    model = Payroll
    
    async def get_by_employee(self, employee_id: str) -> List[Dict[str, Any]]:
        """Get payroll records for an employee"""
        return await self.get_all({'employee_id': employee_id})
    
    async def get_by_month(self, year: int, month: int) -> List[Dict[str, Any]]:
        """Get payroll records for a specific month"""
        return await self.get_all({'year': year, 'month': month})
    
    async def get_by_employee_and_month(self, employee_id: str, year: int, month: int) -> Optional[Dict[str, Any]]:
        """Get payroll record for an employee for a specific month"""
        return await self.get_one({'employee_id': employee_id, 'year': year, 'month': month})


class LoanRepository(BaseRepository[Loan]):
    """Repository for Loan operations"""
    model = Loan
    
    async def get_by_employee(self, employee_id: str) -> List[Dict[str, Any]]:
        """Get loans for an employee"""
        return await self.get_all({'employee_id': employee_id})
    
    async def get_active_loans(self) -> List[Dict[str, Any]]:
        """Get all active loans"""
        return await self.get_all({'status': 'active'})


class HolidayRepository(BaseRepository[Holiday]):
    """Repository for Holiday operations"""
    model = Holiday
    
    async def get_by_year(self, year: int) -> List[Dict[str, Any]]:
        """Get holidays for a year"""
        return await self.get_all({'year': year})


# Repository instances
employee_repository = EmployeeRepository()
attendance_repository = AttendanceRepository()
leave_request_repository = LeaveRequestRepository()
leave_type_repository = LeaveTypeRepository()
salary_structure_repository = SalaryStructureRepository()
payroll_repository = PayrollRepository()
loan_repository = LoanRepository()
holiday_repository = HolidayRepository()
