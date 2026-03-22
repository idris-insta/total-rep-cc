"""
Production Services - Business Logic Layer for Production module
"""
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone

from repositories.production import (
    machine_repository,
    order_sheet_repository,
    work_order_repository,
    production_entry_repository,
    rm_requisition_repository
)
from repositories.inventory import stock_repository, item_repository
from core.exceptions import NotFoundError, ValidationError, BusinessRuleError
from core.legacy_db import db


# Production stage constants
PRODUCTION_STAGES = [
    'coating',
    'slitting', 
    'rewinding',
    'cutting',
    'packing',
    'quality_check',
    'dispatch_ready'
]

# Scrap threshold (7% redline)
SCRAP_REDLINE_PERCENT = 7.0


class MachineService:
    """Business logic for Machine management"""
    
    def __init__(self):
        self.repo = machine_repository
    
    async def get_all_machines(self, filters: Optional[Dict] = None) -> List[Dict[str, Any]]:
        """Get all machines with optional filters"""
        query = {}
        if filters:
            if filters.get('machine_type'):
                query['machine_type'] = filters['machine_type']
            if filters.get('status'):
                query['status'] = filters['status']
        return await self.repo.get_all(query)
    
    async def get_machine(self, machine_id: str) -> Dict[str, Any]:
        """Get a single machine"""
        return await self.repo.get_by_id_or_raise(machine_id, "Machine")
    
    async def create_machine(self, data: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """Create a new machine"""
        data['status'] = data.get('status', 'active')
        return await self.repo.create(data, user_id)
    
    async def update_machine(self, machine_id: str, data: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """Update an existing machine"""
        return await self.repo.update_or_raise(machine_id, data, user_id, "Machine")
    
    async def get_machine_utilization(self, machine_id: str, start_date: str, end_date: str) -> Dict[str, Any]:
        """Get machine utilization metrics"""
        machine = await self.get_machine(machine_id)
        entries = await production_entry_repository.get_by_machine(machine_id)
        
        # Filter by date range
        entries = [e for e in entries if start_date <= e.get('production_date', '') <= end_date]
        
        total_output = sum(e.get('output_qty', 0) for e in entries)
        total_scrap = sum(e.get('scrap_qty', 0) for e in entries)
        
        return {
            'machine_id': machine_id,
            'machine_name': machine.get('machine_name'),
            'total_entries': len(entries),
            'total_output': total_output,
            'total_scrap': total_scrap,
            'scrap_percent': (total_scrap / (total_output + total_scrap) * 100) if (total_output + total_scrap) > 0 else 0
        }


class OrderSheetService:
    """Business logic for Order Sheet (Production Order) management"""
    
    def __init__(self):
        self.repo = order_sheet_repository
    
    async def get_all_order_sheets(self, filters: Optional[Dict] = None) -> List[Dict[str, Any]]:
        """Get all order sheets with optional filters"""
        query = {}
        if filters:
            if filters.get('status'):
                query['status'] = filters['status']
            if filters.get('customer_id'):
                query['customer_id'] = filters['customer_id']
        return await self.repo.get_all(query)
    
    async def get_order_sheet(self, order_sheet_id: str) -> Dict[str, Any]:
        """Get a single order sheet with work orders"""
        order_sheet = await self.repo.get_by_id_or_raise(order_sheet_id, "Order Sheet")
        order_sheet['work_orders'] = await work_order_repository.get_by_order_sheet(order_sheet_id)
        return order_sheet
    
    async def create_order_sheet(self, data: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """Create a new order sheet"""
        data['order_number'] = await self.repo.generate_order_number()
        data['status'] = 'pending'
        return await self.repo.create(data, user_id)
    
    async def update_order_sheet(self, order_sheet_id: str, data: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """Update an existing order sheet"""
        return await self.repo.update_or_raise(order_sheet_id, data, user_id, "Order Sheet")
    
    async def start_production(self, order_sheet_id: str, user_id: str) -> Dict[str, Any]:
        """Start production for an order sheet"""
        order_sheet = await self.get_order_sheet(order_sheet_id)
        
        if order_sheet.get('status') != 'pending':
            raise BusinessRuleError(f"Cannot start production for order with status '{order_sheet.get('status')}'")
        
        return await self.repo.update(order_sheet_id, {
            'status': 'in_progress',
            'started_at': datetime.now(timezone.utc).isoformat(),
            'started_by': user_id
        }, user_id)
    
    async def complete_order_sheet(self, order_sheet_id: str, user_id: str) -> Dict[str, Any]:
        """Complete an order sheet"""
        order_sheet = await self.get_order_sheet(order_sheet_id)
        
        # Check all work orders are complete
        work_orders = order_sheet.get('work_orders', [])
        incomplete = [wo for wo in work_orders if wo.get('status') != 'completed']
        
        if incomplete:
            raise BusinessRuleError(f"Cannot complete order sheet. {len(incomplete)} work orders are not completed.")
        
        return await self.repo.update(order_sheet_id, {
            'status': 'completed',
            'completed_at': datetime.now(timezone.utc).isoformat(),
            'completed_by': user_id
        }, user_id)


class WorkOrderService:
    """Business logic for Work Order management"""
    
    def __init__(self):
        self.repo = work_order_repository
    
    async def get_all_work_orders(self, filters: Optional[Dict] = None) -> List[Dict[str, Any]]:
        """Get all work orders with optional filters"""
        query = {}
        if filters:
            if filters.get('stage'):
                query['stage'] = filters['stage']
            if filters.get('status'):
                query['status'] = filters['status']
            if filters.get('order_sheet_id'):
                query['order_sheet_id'] = filters['order_sheet_id']
            if filters.get('machine_id'):
                query['machine_id'] = filters['machine_id']
        return await self.repo.get_all(query)
    
    async def get_work_order(self, work_order_id: str) -> Dict[str, Any]:
        """Get a single work order with production entries"""
        work_order = await self.repo.get_by_id_or_raise(work_order_id, "Work Order")
        work_order['production_entries'] = await production_entry_repository.get_by_work_order(work_order_id)
        return work_order
    
    async def create_work_order(self, data: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """Create a new work order"""
        # Verify order sheet exists
        order_sheet = await order_sheet_repository.get_by_id(data['order_sheet_id'])
        if not order_sheet:
            raise NotFoundError("Order Sheet", data['order_sheet_id'])
        
        data['wo_number'] = await self.repo.generate_wo_number()
        data['status'] = 'pending'
        
        return await self.repo.create(data, user_id)
    
    async def assign_machine(self, work_order_id: str, machine_id: str, user_id: str) -> Dict[str, Any]:
        """Assign a machine to a work order"""
        # Verify machine exists and is available
        machine = await machine_repository.get_by_id(machine_id)
        if not machine:
            raise NotFoundError("Machine", machine_id)
        
        if machine.get('current_job'):
            raise BusinessRuleError(f"Machine '{machine.get('machine_name')}' is currently busy")
        
        # Update work order
        work_order = await self.repo.update_or_raise(work_order_id, {
            'machine_id': machine_id,
            'machine_name': machine.get('machine_name')
        }, user_id, "Work Order")
        
        # Update machine
        await machine_repository.update(machine_id, {'current_job': work_order_id}, user_id)
        
        return work_order
    
    async def start_work_order(self, work_order_id: str, user_id: str) -> Dict[str, Any]:
        """Start a work order"""
        work_order = await self.repo.get_by_id_or_raise(work_order_id, "Work Order")
        
        if work_order.get('status') != 'pending':
            raise BusinessRuleError(f"Cannot start work order with status '{work_order.get('status')}'")
        
        if not work_order.get('machine_id'):
            raise BusinessRuleError("Work order must have a machine assigned before starting")
        
        return await self.repo.update(work_order_id, {
            'status': 'in_progress',
            'started_at': datetime.now(timezone.utc).isoformat()
        }, user_id)
    
    async def complete_work_order(self, work_order_id: str, user_id: str) -> Dict[str, Any]:
        """Complete a work order"""
        work_order = await self.get_work_order(work_order_id)
        
        if work_order.get('status') != 'in_progress':
            raise BusinessRuleError(f"Cannot complete work order with status '{work_order.get('status')}'")
        
        # Calculate totals from production entries
        entries = work_order.get('production_entries', [])
        total_output = sum(e.get('output_qty', 0) for e in entries)
        total_scrap = sum(e.get('scrap_qty', 0) for e in entries)
        
        # Release machine
        if work_order.get('machine_id'):
            await machine_repository.update(work_order['machine_id'], {'current_job': None}, user_id)
        
        return await self.repo.update(work_order_id, {
            'status': 'completed',
            'completed_at': datetime.now(timezone.utc).isoformat(),
            'actual_output': total_output,
            'actual_scrap': total_scrap
        }, user_id)


class ProductionEntryService:
    """Business logic for Production Entry management"""
    
    def __init__(self):
        self.repo = production_entry_repository
    
    async def create_entry(self, data: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """Create a production entry"""
        # Verify work order exists and is in progress
        work_order = await work_order_repository.get_by_id(data['work_order_id'])
        if not work_order:
            raise NotFoundError("Work Order", data['work_order_id'])
        
        if work_order.get('status') != 'in_progress':
            raise BusinessRuleError(f"Cannot add entry to work order with status '{work_order.get('status')}'")
        
        # Calculate scrap percentage
        output_qty = data.get('output_qty', 0)
        scrap_qty = data.get('scrap_qty', 0)
        total_qty = output_qty + scrap_qty
        scrap_percent = (scrap_qty / total_qty * 100) if total_qty > 0 else 0
        
        data['scrap_percent'] = round(scrap_percent, 2)
        data['production_date'] = data.get('production_date', datetime.now(timezone.utc).strftime('%Y-%m-%d'))
        
        # Check redline
        if scrap_percent > SCRAP_REDLINE_PERCENT:
            data['redline_alert'] = True
            data['redline_status'] = 'pending_approval'
        
        return await self.repo.create(data, user_id)
    
    async def get_entries_for_work_order(self, work_order_id: str) -> List[Dict[str, Any]]:
        """Get all entries for a work order"""
        return await self.repo.get_by_work_order(work_order_id)
    
    async def get_daily_production_summary(self, date: str) -> Dict[str, Any]:
        """Get daily production summary"""
        entries = await self.repo.get_all({'production_date': date})
        
        total_output = sum(e.get('output_qty', 0) for e in entries)
        total_scrap = sum(e.get('scrap_qty', 0) for e in entries)
        redline_alerts = len([e for e in entries if e.get('redline_alert')])
        
        return {
            'date': date,
            'total_entries': len(entries),
            'total_output': total_output,
            'total_scrap': total_scrap,
            'overall_scrap_percent': (total_scrap / (total_output + total_scrap) * 100) if (total_output + total_scrap) > 0 else 0,
            'redline_alerts': redline_alerts
        }


class RMRequisitionService:
    """Business logic for Raw Material Requisition management"""
    
    def __init__(self):
        self.repo = rm_requisition_repository
    
    async def create_requisition(self, data: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """Create a RM requisition"""
        data['requisition_number'] = await self.repo.generate_requisition_number()
        data['status'] = 'pending'
        return await self.repo.create(data, user_id)
    
    async def issue_materials(self, requisition_id: str, user_id: str) -> Dict[str, Any]:
        """Issue materials for a requisition (deduct from inventory)"""
        requisition = await self.repo.get_by_id_or_raise(requisition_id, "RM Requisition")
        
        if requisition.get('status') != 'pending':
            raise BusinessRuleError(f"Cannot issue materials for requisition with status '{requisition.get('status')}'")
        
        # Deduct from inventory
        for item in requisition.get('items', []):
            item_id = item.get('item_id')
            qty = item.get('qty', 0)
            warehouse_id = requisition.get('warehouse_id')
            
            # Check stock availability
            stock = await stock_repository.get_stock(item_id, warehouse_id)
            available = stock.get('qty', 0) if stock else 0
            
            if available < qty:
                raise BusinessRuleError(f"Insufficient stock for item {item_id}. Required: {qty}, Available: {available}")
            
            # Deduct stock
            await stock_repository.update_stock(item_id, warehouse_id, -qty, user_id)
        
        return await self.repo.update(requisition_id, {
            'status': 'issued',
            'issued_at': datetime.now(timezone.utc).isoformat(),
            'issued_by': user_id
        }, user_id)


# Service instances
machine_service = MachineService()
order_sheet_service = OrderSheetService()
work_order_service = WorkOrderService()
production_entry_service = ProductionEntryService()
rm_requisition_service = RMRequisitionService()
