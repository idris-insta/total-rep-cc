"""
Inventory Services - Business Logic Layer for Inventory module
"""
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone

from repositories.inventory import (
    item_repository,
    warehouse_repository,
    stock_repository,
    stock_transfer_repository,
    stock_adjustment_repository,
    batch_repository
)
from core.exceptions import NotFoundError, ValidationError, BusinessRuleError
from core.legacy_db import db


class ItemService:
    """Business logic for Item (Product) management"""
    
    def __init__(self):
        self.repo = item_repository
    
    async def get_all_items(self, filters: Optional[Dict] = None) -> List[Dict[str, Any]]:
        """Get all items with optional filters"""
        query = {}
        if filters:
            if filters.get('category'):
                query['category'] = filters['category']
            if filters.get('item_type'):
                query['item_type'] = filters['item_type']
            if filters.get('search'):
                return await self.repo.search(filters['search'])
        return await self.repo.get_all(query)
    
    async def get_item(self, item_id: str) -> Dict[str, Any]:
        """Get a single item by ID"""
        return await self.repo.get_by_id_or_raise(item_id, "Item")
    
    async def create_item(self, data: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """Create a new item"""
        # Check for duplicate item code
        if data.get('item_code'):
            existing = await self.repo.get_one({'item_code': data['item_code']})
            if existing:
                raise ValidationError(f"Item code '{data['item_code']}' already exists")
        
        # Auto-calculate MSP if not provided
        if data.get('cost_price') and data.get('margin_percent') and not data.get('min_selling_price'):
            cost = data['cost_price']
            margin = data['margin_percent']
            data['min_selling_price'] = round(cost * (1 + margin / 100), 2)
        
        return await self.repo.create(data, user_id)
    
    async def update_item(self, item_id: str, data: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """Update an existing item"""
        # Auto-recalculate MSP if cost or margin changed
        if 'cost_price' in data or 'margin_percent' in data:
            item = await self.get_item(item_id)
            cost = data.get('cost_price', item.get('cost_price', 0))
            margin = data.get('margin_percent', item.get('margin_percent', 0))
            if cost and margin:
                data['min_selling_price'] = round(cost * (1 + margin / 100), 2)
        
        return await self.repo.update_or_raise(item_id, data, user_id, "Item")
    
    async def delete_item(self, item_id: str) -> bool:
        """Delete an item"""
        # Check for stock
        stock = await stock_repository.get_by_item(item_id)
        total_qty = sum(s.get('qty', 0) for s in stock)
        if total_qty > 0:
            raise BusinessRuleError(f"Cannot delete item with existing stock ({total_qty} units)")
        
        return await self.repo.delete_or_raise(item_id, "Item")
    
    async def get_low_stock_items(self) -> List[Dict[str, Any]]:
        """Get items below reorder level"""
        return await self.repo.get_low_stock()
    
    async def get_stock_summary(self, item_id: str) -> Dict[str, Any]:
        """Get stock summary for an item across all warehouses"""
        item = await self.get_item(item_id)
        stock = await stock_repository.get_by_item(item_id)
        
        return {
            'item_id': item_id,
            'item_name': item.get('item_name'),
            'total_qty': sum(s.get('qty', 0) for s in stock),
            'by_warehouse': stock
        }


class WarehouseService:
    """Business logic for Warehouse management"""
    
    def __init__(self):
        self.repo = warehouse_repository
    
    async def get_all_warehouses(self, active_only: bool = True) -> List[Dict[str, Any]]:
        """Get all warehouses"""
        if active_only:
            return await self.repo.get_active()
        return await self.repo.get_all()
    
    async def get_warehouse(self, warehouse_id: str) -> Dict[str, Any]:
        """Get a single warehouse"""
        return await self.repo.get_by_id_or_raise(warehouse_id, "Warehouse")
    
    async def create_warehouse(self, data: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """Create a new warehouse"""
        # Check for duplicate GSTIN
        if data.get('gstin'):
            existing = await self.repo.get_by_gstin(data['gstin'])
            if existing:
                raise ValidationError(f"Warehouse with GSTIN '{data['gstin']}' already exists")
        
        data['is_active'] = True
        return await self.repo.create(data, user_id)
    
    async def update_warehouse(self, warehouse_id: str, data: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """Update an existing warehouse"""
        return await self.repo.update_or_raise(warehouse_id, data, user_id, "Warehouse")
    
    async def get_warehouse_stock(self, warehouse_id: str) -> List[Dict[str, Any]]:
        """Get all stock in a warehouse"""
        await self.get_warehouse(warehouse_id)  # Verify warehouse exists
        return await stock_repository.get_by_warehouse(warehouse_id)


class StockTransferService:
    """Business logic for Stock Transfers"""
    
    def __init__(self):
        self.repo = stock_transfer_repository
    
    async def get_all_transfers(self, filters: Optional[Dict] = None) -> List[Dict[str, Any]]:
        """Get all transfers with optional filters"""
        query = {}
        if filters:
            if filters.get('status'):
                query['status'] = filters['status']
            if filters.get('from_warehouse'):
                query['from_warehouse_id'] = filters['from_warehouse']
            if filters.get('to_warehouse'):
                query['to_warehouse_id'] = filters['to_warehouse']
        return await self.repo.get_all(query)
    
    async def create_transfer(self, data: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """Create a new stock transfer"""
        # Verify warehouses exist
        from_wh = await warehouse_repository.get_by_id(data['from_warehouse_id'])
        to_wh = await warehouse_repository.get_by_id(data['to_warehouse_id'])
        
        if not from_wh:
            raise NotFoundError("Source warehouse", data['from_warehouse_id'])
        if not to_wh:
            raise NotFoundError("Destination warehouse", data['to_warehouse_id'])
        
        if data['from_warehouse_id'] == data['to_warehouse_id']:
            raise ValidationError("Source and destination warehouse cannot be the same")
        
        # Verify stock availability
        for item in data.get('items', []):
            stock = await stock_repository.get_stock(item['item_id'], data['from_warehouse_id'])
            available = stock.get('qty', 0) if stock else 0
            if available < item['qty']:
                raise BusinessRuleError(f"Insufficient stock for item {item['item_id']}. Available: {available}")
        
        # Generate transfer number
        count = await self.repo.count()
        data['transfer_number'] = f"TRF-{datetime.now().strftime('%Y%m')}-{count + 1:04d}"
        data['status'] = 'pending'
        
        return await self.repo.create(data, user_id)
    
    async def dispatch_transfer(self, transfer_id: str, user_id: str) -> Dict[str, Any]:
        """Dispatch a transfer (mark as in transit)"""
        transfer = await self.repo.get_by_id_or_raise(transfer_id, "Stock Transfer")
        
        if transfer.get('status') != 'pending':
            raise BusinessRuleError(f"Cannot dispatch transfer with status '{transfer.get('status')}'")
        
        # Deduct stock from source warehouse
        for item in transfer.get('items', []):
            await stock_repository.update_stock(
                item['item_id'],
                transfer['from_warehouse_id'],
                -item['qty'],
                user_id
            )
        
        return await self.repo.update(transfer_id, {
            'status': 'in_transit',
            'dispatched_at': datetime.now(timezone.utc).isoformat(),
            'dispatched_by': user_id
        }, user_id)
    
    async def receive_transfer(self, transfer_id: str, user_id: str) -> Dict[str, Any]:
        """Receive a transfer at destination warehouse"""
        transfer = await self.repo.get_by_id_or_raise(transfer_id, "Stock Transfer")
        
        if transfer.get('status') != 'in_transit':
            raise BusinessRuleError(f"Cannot receive transfer with status '{transfer.get('status')}'")
        
        # Add stock to destination warehouse
        for item in transfer.get('items', []):
            await stock_repository.update_stock(
                item['item_id'],
                transfer['to_warehouse_id'],
                item['qty'],
                user_id
            )
        
        return await self.repo.update(transfer_id, {
            'status': 'received',
            'received_at': datetime.now(timezone.utc).isoformat(),
            'received_by': user_id
        }, user_id)


class StockAdjustmentService:
    """Business logic for Stock Adjustments"""
    
    def __init__(self):
        self.repo = stock_adjustment_repository
    
    async def create_adjustment(self, data: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """Create a stock adjustment"""
        # Generate adjustment number
        count = await self.repo.count()
        data['adjustment_number'] = f"ADJ-{datetime.now().strftime('%Y%m')}-{count + 1:04d}"
        data['status'] = 'pending'
        
        return await self.repo.create(data, user_id)
    
    async def approve_adjustment(self, adjustment_id: str, user_id: str) -> Dict[str, Any]:
        """Approve and apply a stock adjustment"""
        adjustment = await self.repo.get_by_id_or_raise(adjustment_id, "Stock Adjustment")
        
        if adjustment.get('status') != 'pending':
            raise BusinessRuleError(f"Cannot approve adjustment with status '{adjustment.get('status')}'")
        
        # Apply the adjustment
        qty_change = adjustment.get('qty', 0)
        if adjustment.get('adjustment_type') in ['damage', 'expired', 'decrease']:
            qty_change = -abs(qty_change)
        
        await stock_repository.update_stock(
            adjustment['item_id'],
            adjustment['warehouse_id'],
            qty_change,
            user_id
        )
        
        return await self.repo.update(adjustment_id, {
            'status': 'approved',
            'approved_at': datetime.now(timezone.utc).isoformat(),
            'approved_by': user_id
        }, user_id)


class BatchService:
    """Business logic for Batch tracking"""
    
    def __init__(self):
        self.repo = batch_repository
    
    async def get_batches_for_item(self, item_id: str) -> List[Dict[str, Any]]:
        """Get all batches for an item"""
        return await self.repo.get_by_item(item_id)
    
    async def get_expiring_batches(self, days: int = 30) -> List[Dict[str, Any]]:
        """Get batches expiring soon"""
        return await self.repo.get_expiring_soon(days)
    
    async def create_batch(self, data: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """Create a new batch"""
        # Generate batch number
        count = await self.repo.count()
        data['batch_number'] = f"BAT-{datetime.now().strftime('%Y%m%d')}-{count + 1:04d}"
        
        return await self.repo.create(data, user_id)


# Service instances
item_service = ItemService()
warehouse_service = WarehouseService()
stock_transfer_service = StockTransferService()
stock_adjustment_service = StockAdjustmentService()
batch_service = BatchService()
