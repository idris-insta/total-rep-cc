"""
Quality Services - Business Logic Layer for Quality module
"""
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone

from repositories.quality import (
    qc_inspection_repository,
    customer_complaint_repository,
    tds_repository,
    qc_parameter_repository
)
from core.exceptions import NotFoundError, ValidationError, BusinessRuleError
from core.legacy_db import db


class QCInspectionService:
    """Business logic for QC Inspection management"""
    
    def __init__(self):
        self.repo = qc_inspection_repository
    
    async def get_all_inspections(self, filters: Optional[Dict] = None) -> List[Dict[str, Any]]:
        """Get all inspections with optional filters"""
        query = {}
        if filters:
            if filters.get('inspection_type'):
                query['inspection_type'] = filters['inspection_type']
            if filters.get('result'):
                query['result'] = filters['result']
            if filters.get('reference_type'):
                query['reference_type'] = filters['reference_type']
            if filters.get('item_id'):
                query['item_id'] = filters['item_id']
        return await self.repo.get_all(query)
    
    async def get_inspection(self, inspection_id: str) -> Dict[str, Any]:
        """Get a single inspection"""
        return await self.repo.get_by_id_or_raise(inspection_id, "QC Inspection")
    
    async def create_inspection(self, data: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """Create a new QC inspection"""
        # Calculate pass/fail result
        test_parameters = data.get('test_parameters', [])
        passed_tests = sum(1 for test in test_parameters if test.get('result') == 'pass')
        total_tests = len(test_parameters)
        result = 'pass' if passed_tests == total_tests else 'fail'
        
        data['inspection_number'] = await self.repo.generate_inspection_number()
        data['result'] = result
        data['passed_tests'] = passed_tests
        data['total_tests'] = total_tests
        data['pass_rate'] = round((passed_tests / total_tests * 100) if total_tests > 0 else 0, 2)
        
        return await self.repo.create(data, user_id)
    
    async def get_inspection_stats(self, start_date: str = None, end_date: str = None) -> Dict[str, Any]:
        """Get inspection statistics"""
        query = {}
        if start_date and end_date:
            query['created_at'] = {'$gte': start_date, '$lte': end_date}
        
        inspections = await self.repo.get_all(query)
        
        total = len(inspections)
        passed = len([i for i in inspections if i.get('result') == 'pass'])
        failed = total - passed
        
        return {
            'total_inspections': total,
            'passed': passed,
            'failed': failed,
            'pass_rate': round((passed / total * 100) if total > 0 else 0, 2),
            'by_type': self._group_by_type(inspections)
        }
    
    def _group_by_type(self, inspections: List[Dict]) -> Dict[str, int]:
        """Group inspections by type"""
        by_type = {}
        for i in inspections:
            t = i.get('inspection_type', 'unknown')
            by_type[t] = by_type.get(t, 0) + 1
        return by_type


class CustomerComplaintService:
    """Business logic for Customer Complaint management"""
    
    def __init__(self):
        self.repo = customer_complaint_repository
    
    async def get_all_complaints(self, filters: Optional[Dict] = None) -> List[Dict[str, Any]]:
        """Get all complaints with optional filters"""
        query = {}
        if filters:
            if filters.get('status'):
                query['status'] = filters['status']
            if filters.get('severity'):
                query['severity'] = filters['severity']
            if filters.get('account_id'):
                query['account_id'] = filters['account_id']
        return await self.repo.get_all(query)
    
    async def get_complaint(self, complaint_id: str) -> Dict[str, Any]:
        """Get a single complaint"""
        return await self.repo.get_by_id_or_raise(complaint_id, "Customer Complaint")
    
    async def create_complaint(self, data: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """Create a new complaint"""
        data['complaint_number'] = await self.repo.generate_complaint_number()
        data['status'] = 'open'
        return await self.repo.create(data, user_id)
    
    async def update_status(self, complaint_id: str, status: str, resolution: str = None, user_id: str = None) -> Dict[str, Any]:
        """Update complaint status"""
        update_data = {'status': status}
        if status == 'resolved' and resolution:
            update_data['resolution'] = resolution
            update_data['resolved_at'] = datetime.now(timezone.utc).isoformat()
        
        return await self.repo.update_or_raise(complaint_id, update_data, user_id, "Customer Complaint")
    
    async def get_open_complaints(self) -> List[Dict[str, Any]]:
        """Get all open complaints"""
        return await self.repo.get_open_complaints()
    
    async def get_complaint_stats(self) -> Dict[str, Any]:
        """Get complaint statistics"""
        complaints = await self.repo.get_all()
        
        open_count = len([c for c in complaints if c.get('status') in ['open', 'in_progress']])
        resolved_count = len([c for c in complaints if c.get('status') == 'resolved'])
        
        by_severity = {}
        for c in complaints:
            sev = c.get('severity', 'unknown')
            by_severity[sev] = by_severity.get(sev, 0) + 1
        
        return {
            'total': len(complaints),
            'open': open_count,
            'resolved': resolved_count,
            'by_severity': by_severity
        }


class TDSService:
    """Business logic for Technical Data Sheet management"""
    
    def __init__(self):
        self.repo = tds_repository
    
    async def get_all_tds(self, filters: Optional[Dict] = None) -> List[Dict[str, Any]]:
        """Get all TDS documents"""
        query = {}
        if filters:
            if filters.get('item_id'):
                query['item_id'] = filters['item_id']
        return await self.repo.get_all(query)
    
    async def get_tds_for_item(self, item_id: str) -> List[Dict[str, Any]]:
        """Get all TDS documents for an item"""
        return await self.repo.get_by_item(item_id)
    
    async def get_latest_tds(self, item_id: str) -> Optional[Dict[str, Any]]:
        """Get the latest TDS for an item"""
        return await self.repo.get_latest_by_item(item_id)
    
    async def create_tds(self, data: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """Create a new TDS document"""
        return await self.repo.create(data, user_id)


class QCParameterService:
    """Business logic for QC Parameter management"""
    
    def __init__(self):
        self.repo = qc_parameter_repository
    
    async def get_all_parameters(self, filters: Optional[Dict] = None) -> List[Dict[str, Any]]:
        """Get all QC parameters"""
        query = {}
        if filters:
            if filters.get('category'):
                query['category'] = filters['category']
            if filters.get('is_active') is not None:
                query['is_active'] = filters['is_active']
        return await self.repo.get_all(query)
    
    async def create_parameter(self, data: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """Create a new QC parameter"""
        data['is_active'] = True
        return await self.repo.create(data, user_id)
    
    async def update_parameter(self, param_id: str, data: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """Update a QC parameter"""
        return await self.repo.update_or_raise(param_id, data, user_id, "QC Parameter")


# Service instances
qc_inspection_service = QCInspectionService()
customer_complaint_service = CustomerComplaintService()
tds_service = TDSService()
qc_parameter_service = QCParameterService()
