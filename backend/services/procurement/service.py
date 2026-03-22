"""
Procurement Services - Business Logic Layer for Procurement module
"""
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone

from repositories.procurement import (
    supplier_repository,
    purchase_order_repository,
    grn_repository,
    purchase_requisition_repository
)
from repositories.inventory import stock_repository
from core.exceptions import NotFoundError, ValidationError, BusinessRuleError, DuplicateError
from core.legacy_db import db


class SupplierService:
    """Business logic for Supplier management"""
    
    def __init__(self):
        self.repo = supplier_repository
    
    async def get_all_suppliers(self, filters: Optional[Dict] = None) -> List[Dict[str, Any]]:
        """Get all suppliers with optional filters"""
        query = {}
        if filters:
            if filters.get('supplier_type'):
                query['supplier_type'] = filters['supplier_type']
            if filters.get('search'):
                return await self.repo.search(filters['search'])
        return await self.repo.get_all(query)
    
    async def get_supplier(self, supplier_id: str) -> Dict[str, Any]:
        """Get a single supplier"""
        return await self.repo.get_by_id_or_raise(supplier_id, "Supplier")
    
    async def create_supplier(self, data: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """Create a new supplier"""
        # Check for duplicate GSTIN
        if data.get('gstin'):
            existing = await self.repo.get_by_gstin(data['gstin'])
            if existing:
                raise DuplicateError("Supplier", f"GSTIN '{data['gstin']}'")
        
        # Auto-generate supplier code if not provided
        if not data.get('supplier_code'):
            count = await self.repo.count()
            data['supplier_code'] = f"SUP-{count + 1:04d}"
        
        data['status'] = 'active'
        return await self.repo.create(data, user_id)
    
    async def update_supplier(self, supplier_id: str, data: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """Update an existing supplier"""
        return await self.repo.update_or_raise(supplier_id, data, user_id, "Supplier")


class PurchaseOrderService:
    """Business logic for Purchase Order management"""
    
    def __init__(self):
        self.repo = purchase_order_repository
    
    async def get_all_orders(self, filters: Optional[Dict] = None) -> List[Dict[str, Any]]:
        """Get all purchase orders with optional filters"""
        query = {}
        if filters:
            if filters.get('status'):
                query['status'] = filters['status']
            if filters.get('supplier_id'):
                query['supplier_id'] = filters['supplier_id']
        return await self.repo.get_all(query)
    
    async def get_order(self, order_id: str) -> Dict[str, Any]:
        """Get a single purchase order"""
        return await self.repo.get_by_id_or_raise(order_id, "Purchase Order")
    
    async def create_order(self, data: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """Create a new purchase order"""
        # Verify supplier exists
        supplier = await supplier_repository.get_by_id(data['supplier_id'])
        if not supplier:
            raise NotFoundError("Supplier", data['supplier_id'])
        
        # Calculate totals
        items = []
        subtotal = 0
        total_tax = 0
        
        for item in data.get('items', []):
            qty = item.get('quantity', 0)
            unit_price = item.get('unit_price', 0)
            tax_percent = item.get('tax_percent', 18)
            
            line_total = qty * unit_price
            tax = line_total * tax_percent / 100
            
            items.append({
                **item,
                'line_total': line_total,
                'tax_amount': tax,
                'total': line_total + tax
            })
            
            subtotal += line_total
            total_tax += tax
        
        # Generate PO number
        po_number = await self.repo.generate_po_number()
        
        po_data = {
            **data,
            'po_number': po_number,
            'supplier_name': supplier.get('supplier_name'),
            'supplier_gstin': supplier.get('gstin'),
            'items': items,
            'subtotal': round(subtotal, 2),
            'total_tax': round(total_tax, 2),
            'grand_total': round(subtotal + total_tax, 2),
            'status': 'draft',
            'received_qty': 0
        }
        
        return await self.repo.create(po_data, user_id)
    
    async def send_order(self, order_id: str, user_id: str) -> Dict[str, Any]:
        """Mark PO as sent to supplier"""
        order = await self.get_order(order_id)
        
        if order.get('status') != 'draft':
            raise BusinessRuleError(f"Cannot send PO with status '{order.get('status')}'")
        
        return await self.repo.update(order_id, {
            'status': 'sent',
            'sent_at': datetime.now(timezone.utc).isoformat()
        }, user_id)
    
    async def cancel_order(self, order_id: str, reason: str, user_id: str) -> Dict[str, Any]:
        """Cancel a purchase order"""
        order = await self.get_order(order_id)
        
        if order.get('status') in ['received', 'cancelled']:
            raise BusinessRuleError(f"Cannot cancel PO with status '{order.get('status')}'")
        
        return await self.repo.update(order_id, {
            'status': 'cancelled',
            'cancellation_reason': reason,
            'cancelled_at': datetime.now(timezone.utc).isoformat()
        }, user_id)


class GRNService:
    """Business logic for Goods Receipt Note management"""
    
    def __init__(self):
        self.repo = grn_repository
    
    async def get_all_grns(self, filters: Optional[Dict] = None) -> List[Dict[str, Any]]:
        """Get all GRNs"""
        query = {}
        if filters:
            if filters.get('po_id'):
                query['po_id'] = filters['po_id']
            if filters.get('supplier_id'):
                query['supplier_id'] = filters['supplier_id']
        return await self.repo.get_all(query)
    
    async def create_grn(self, data: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """Create a GRN and update inventory"""
        # Verify PO exists
        po = await purchase_order_repository.get_by_id(data['po_id'])
        if not po:
            raise NotFoundError("Purchase Order", data['po_id'])
        
        if po.get('status') not in ['sent', 'partial']:
            raise BusinessRuleError(f"Cannot create GRN for PO with status '{po.get('status')}'")
        
        # Generate GRN number
        grn_number = await self.repo.generate_grn_number()
        
        grn_data = {
            **data,
            'grn_number': grn_number,
            'supplier_id': po.get('supplier_id'),
            'supplier_name': po.get('supplier_name'),
            'po_number': po.get('po_number'),
            'received_date': data.get('received_date', datetime.now(timezone.utc).strftime('%Y-%m-%d')),
            'status': 'received'
        }
        
        grn = await self.repo.create(grn_data, user_id)
        
        # Update inventory stock
        warehouse_id = data.get('warehouse_id')
        if warehouse_id:
            for item in data.get('items', []):
                await stock_repository.update_stock(
                    item['item_id'],
                    warehouse_id,
                    item.get('received_qty', 0),
                    user_id
                )
        
        # Update PO status
        received_qty = sum(item.get('received_qty', 0) for item in data.get('items', []))
        po_items_qty = sum(item.get('quantity', 0) for item in po.get('items', []))
        
        if received_qty >= po_items_qty:
            await purchase_order_repository.update(data['po_id'], {'status': 'received'}, user_id)
        else:
            await purchase_order_repository.update(data['po_id'], {'status': 'partial'}, user_id)
        
        return grn


class PurchaseRequisitionService:
    """Business logic for Purchase Requisition management"""
    
    def __init__(self):
        self.repo = purchase_requisition_repository
    
    async def get_all_requisitions(self, filters: Optional[Dict] = None) -> List[Dict[str, Any]]:
        """Get all purchase requisitions"""
        query = {}
        if filters:
            if filters.get('status'):
                query['status'] = filters['status']
        return await self.repo.get_all(query)
    
    async def create_requisition(self, data: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """Create a purchase requisition"""
        pr_number = await self.repo.generate_pr_number()
        
        data['pr_number'] = pr_number
        data['status'] = 'draft'
        data['requested_by'] = user_id
        
        return await self.repo.create(data, user_id)
    
    async def submit_for_approval(self, requisition_id: str, user_id: str) -> Dict[str, Any]:
        """Submit requisition for approval"""
        return await self.repo.update_or_raise(requisition_id, {
            'status': 'pending_approval',
            'submitted_at': datetime.now(timezone.utc).isoformat()
        }, user_id, "Purchase Requisition")
    
    async def approve_requisition(self, requisition_id: str, user_id: str) -> Dict[str, Any]:
        """Approve a purchase requisition"""
        req = await self.repo.get_by_id_or_raise(requisition_id, "Purchase Requisition")
        
        if req.get('status') != 'pending_approval':
            raise BusinessRuleError(f"Cannot approve requisition with status '{req.get('status')}'")
        
        return await self.repo.update(requisition_id, {
            'status': 'approved',
            'approved_by': user_id,
            'approved_at': datetime.now(timezone.utc).isoformat()
        }, user_id)
    
    async def convert_to_po(self, requisition_id: str, supplier_id: str, user_id: str) -> Dict[str, Any]:
        """Convert requisition to purchase order"""
        req = await self.repo.get_by_id_or_raise(requisition_id, "Purchase Requisition")
        
        if req.get('status') != 'approved':
            raise BusinessRuleError("Only approved requisitions can be converted to PO")
        
        # Create PO from requisition
        po = await purchase_order_service.create_order({
            'supplier_id': supplier_id,
            'items': req.get('items', []),
            'notes': f"Created from PR: {req.get('pr_number')}",
            'pr_id': requisition_id
        }, user_id)
        
        # Update requisition status
        await self.repo.update(requisition_id, {
            'status': 'converted',
            'po_id': po['id']
        }, user_id)
        
        return po


# Service instances
supplier_service = SupplierService()
purchase_order_service = PurchaseOrderService()
grn_service = GRNService()
purchase_requisition_service = PurchaseRequisitionService()
