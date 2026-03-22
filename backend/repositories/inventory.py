"""
Inventory Repositories - Data Access Layer for Inventory module (PostgreSQL/SQLAlchemy)
"""
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone, timedelta
from sqlalchemy import select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from repositories.base import BaseRepository
from models.entities.inventory import Item, Warehouse, Stock, StockTransfer, StockAdjustment, Batch, BinLocation, StockLedger
from core.database import async_session_factory


class ItemRepository(BaseRepository[Item]):
    """Repository for Item (Product) operations"""
    model = Item
    
    async def get_by_category(self, category: str) -> List[Dict[str, Any]]:
        """Get items by category"""
        return await self.get_all({'category': category})
    
    async def get_by_type(self, item_type: str) -> List[Dict[str, Any]]:
        """Get items by type"""
        return await self.get_all({'item_type': item_type})
    
    async def get_by_hsn(self, hsn_code: str) -> Optional[Dict[str, Any]]:
        """Get item by HSN code"""
        return await self.get_one({'hsn_code': hsn_code})
    
    async def search(self, query: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Search items by name, code, or HSN"""
        return await super().search(query, ['item_name', 'item_code', 'hsn_code'], limit)
    
    async def get_low_stock(self, threshold: int = None) -> List[Dict[str, Any]]:
        """Get items with stock below reorder level"""
        async with async_session_factory() as session:
            if threshold:
                result = await session.execute(
                    select(Item).where(Item.stock_qty < threshold)
                )
            else:
                result = await session.execute(
                    select(Item).where(Item.stock_qty < Item.reorder_level)
                )
            return [self._to_dict(obj) for obj in result.scalars().all()]
    
    async def update_stock(self, item_id: str, qty_change: float, user_id: str) -> Optional[Dict[str, Any]]:
        """Update item stock quantity"""
        item = await self.get_by_id(item_id)
        if not item:
            return None
        new_qty = item.get('stock_qty', 0) + qty_change
        return await self.update(item_id, {'stock_qty': new_qty}, user_id)


class WarehouseRepository(BaseRepository[Warehouse]):
    """Repository for Warehouse operations"""
    model = Warehouse
    
    async def get_by_gstin(self, gstin: str) -> Optional[Dict[str, Any]]:
        """Get warehouse by GSTIN"""
        return await self.get_one({'gstin': gstin})
    
    async def get_active(self) -> List[Dict[str, Any]]:
        """Get all active warehouses"""
        return await self.get_all({'is_active': True})


class StockRepository(BaseRepository[Stock]):
    """Repository for Stock operations (item stock per warehouse)"""
    model = Stock
    
    async def get_by_warehouse(self, warehouse_id: str) -> List[Dict[str, Any]]:
        """Get all stock for a warehouse"""
        return await self.get_all({'warehouse_id': warehouse_id})
    
    async def get_by_item(self, item_id: str) -> List[Dict[str, Any]]:
        """Get stock across all warehouses for an item"""
        return await self.get_all({'item_id': item_id})
    
    async def get_stock(self, item_id: str, warehouse_id: str) -> Optional[Dict[str, Any]]:
        """Get stock for specific item in specific warehouse"""
        return await self.get_one({'item_id': item_id, 'warehouse_id': warehouse_id})
    
    async def update_stock(self, item_id: str, warehouse_id: str, qty_change: float, user_id: str) -> Dict[str, Any]:
        """Update stock quantity for an item in a warehouse"""
        existing = await self.get_stock(item_id, warehouse_id)
        if existing:
            new_qty = existing.get('qty', 0) + qty_change
            return await self.update(existing['id'], {'qty': new_qty}, user_id)
        else:
            return await self.create({
                'item_id': item_id,
                'warehouse_id': warehouse_id,
                'qty': qty_change
            }, user_id)


class StockTransferRepository(BaseRepository[StockTransfer]):
    """Repository for Stock Transfer operations"""
    model = StockTransfer
    
    async def get_by_status(self, status: str) -> List[Dict[str, Any]]:
        """Get transfers by status"""
        return await self.get_all({'status': status})
    
    async def get_pending(self) -> List[Dict[str, Any]]:
        """Get pending transfers"""
        return await self.get_by_status('pending')
    
    async def get_in_transit(self) -> List[Dict[str, Any]]:
        """Get transfers in transit"""
        return await self.get_by_status('in_transit')


class StockAdjustmentRepository(BaseRepository[StockAdjustment]):
    """Repository for Stock Adjustment operations"""
    model = StockAdjustment
    
    async def get_by_type(self, adjustment_type: str) -> List[Dict[str, Any]]:
        """Get adjustments by type"""
        return await self.get_all({'adjustment_type': adjustment_type})
    
    async def get_pending_approval(self) -> List[Dict[str, Any]]:
        """Get adjustments pending approval"""
        return await self.get_all({'status': 'pending'})


class BatchRepository(BaseRepository[Batch]):
    """Repository for Batch tracking operations"""
    model = Batch
    
    async def get_by_item(self, item_id: str) -> List[Dict[str, Any]]:
        """Get all batches for an item"""
        return await self.get_all({'item_id': item_id})
    
    async def get_expiring_soon(self, days: int = 30) -> List[Dict[str, Any]]:
        """Get batches expiring within specified days"""
        async with async_session_factory() as session:
            now = datetime.now(timezone.utc)
            future_date = now + timedelta(days=days)
            result = await session.execute(
                select(Batch).where(
                    and_(
                        Batch.expiry_date <= future_date,
                        Batch.expiry_date >= now
                    )
                )
            )
            return [self._to_dict(obj) for obj in result.scalars().all()]


class BinLocationRepository(BaseRepository[BinLocation]):
    """Repository for Bin Location operations"""
    model = BinLocation
    
    async def get_by_warehouse(self, warehouse_id: str) -> List[Dict[str, Any]]:
        """Get all bins for a warehouse"""
        return await self.get_all({'warehouse_id': warehouse_id})


class StockLedgerRepository(BaseRepository[StockLedger]):
    """Repository for Stock Ledger operations"""
    model = StockLedger
    
    async def get_by_item(self, item_id: str) -> List[Dict[str, Any]]:
        """Get ledger entries for an item"""
        return await self.get_all({'item_id': item_id}, sort_by='transaction_date')
    
    async def get_by_warehouse(self, warehouse_id: str) -> List[Dict[str, Any]]:
        """Get ledger entries for a warehouse"""
        return await self.get_all({'warehouse_id': warehouse_id}, sort_by='transaction_date')


# Repository instances
item_repository = ItemRepository()
warehouse_repository = WarehouseRepository()
stock_repository = StockRepository()
stock_transfer_repository = StockTransferRepository()
stock_adjustment_repository = StockAdjustmentRepository()
batch_repository = BatchRepository()
bin_location_repository = BinLocationRepository()
stock_ledger_repository = StockLedgerRepository()
