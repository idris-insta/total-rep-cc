"""
Procurement Repositories - Data Access Layer for Procurement module (PostgreSQL/SQLAlchemy)
"""
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone

from repositories.base import BaseRepository
from models.entities.procurement import Supplier, PurchaseOrder, PurchaseRequisition, GRN, LandingCost
from core.database import async_session_factory


class SupplierRepository(BaseRepository[Supplier]):
    """Repository for Supplier operations"""
    model = Supplier
    
    async def get_by_type(self, supplier_type: str) -> List[Dict[str, Any]]:
        """Get suppliers by type"""
        return await self.get_all({'supplier_type': supplier_type})
    
    async def get_by_gstin(self, gstin: str) -> Optional[Dict[str, Any]]:
        """Get supplier by GSTIN"""
        return await self.get_one({'gstin': gstin})
    
    async def search(self, query: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Search suppliers by name or code"""
        return await super().search(query, ['supplier_name', 'supplier_code'], limit)


class PurchaseOrderRepository(BaseRepository[PurchaseOrder]):
    """Repository for Purchase Order operations"""
    model = PurchaseOrder
    
    async def get_by_supplier(self, supplier_id: str) -> List[Dict[str, Any]]:
        """Get POs for a supplier"""
        return await self.get_all({'supplier_id': supplier_id})
    
    async def get_by_status(self, status: str) -> List[Dict[str, Any]]:
        """Get POs by status"""
        return await self.get_all({'status': status})
    
    async def get_pending(self) -> List[Dict[str, Any]]:
        """Get pending POs"""
        return await self.get_all({'status': {'$in': ['draft', 'sent', 'partial']}})
    
    async def generate_po_number(self) -> str:
        """Generate unique PO number"""
        count = await self.count()
        return f"PO-{datetime.now().strftime('%Y%m')}-{count + 1:04d}"


class GRNRepository(BaseRepository[GRN]):
    """Repository for Goods Receipt Note operations"""
    model = GRN
    
    async def get_by_po(self, po_id: str) -> List[Dict[str, Any]]:
        """Get GRNs for a PO"""
        return await self.get_all({'po_id': po_id})
    
    async def get_by_supplier(self, supplier_id: str) -> List[Dict[str, Any]]:
        """Get GRNs for a supplier"""
        return await self.get_all({'supplier_id': supplier_id})
    
    async def generate_grn_number(self) -> str:
        """Generate unique GRN number"""
        count = await self.count()
        return f"GRN-{datetime.now().strftime('%Y%m')}-{count + 1:04d}"


class PurchaseRequisitionRepository(BaseRepository[PurchaseRequisition]):
    """Repository for Purchase Requisition operations"""
    model = PurchaseRequisition
    
    async def get_by_status(self, status: str) -> List[Dict[str, Any]]:
        """Get requisitions by status"""
        return await self.get_all({'status': status})
    
    async def get_pending_approval(self) -> List[Dict[str, Any]]:
        """Get requisitions pending approval"""
        return await self.get_all({'status': 'pending_approval'})
    
    async def generate_pr_number(self) -> str:
        """Generate unique PR number"""
        count = await self.count()
        return f"PR-{datetime.now().strftime('%Y%m')}-{count + 1:04d}"


class LandingCostRepository(BaseRepository[LandingCost]):
    """Repository for Landing Cost operations"""
    model = LandingCost
    
    async def get_by_grn(self, grn_id: str) -> List[Dict[str, Any]]:
        """Get landing costs for a GRN"""
        return await self.get_all({'grn_id': grn_id})


# Repository instances
supplier_repository = SupplierRepository()
purchase_order_repository = PurchaseOrderRepository()
grn_repository = GRNRepository()
purchase_requisition_repository = PurchaseRequisitionRepository()
landing_cost_repository = LandingCostRepository()
