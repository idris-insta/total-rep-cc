"""
Production Repositories - Data Access Layer for Production module (PostgreSQL/SQLAlchemy)
"""
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
from sqlalchemy import select, and_

from repositories.base import BaseRepository
from models.entities.production import Machine, OrderSheet, WorkOrder, ProductionEntry, RMRequisition, WorkOrderStage, StageEntry
from core.database import async_session_factory


class MachineRepository(BaseRepository[Machine]):
    """Repository for Machine Master operations"""
    model = Machine
    
    async def get_active(self) -> List[Dict[str, Any]]:
        """Get all active machines"""
        return await self.get_all({'status': 'active'})
    
    async def get_by_type(self, machine_type: str) -> List[Dict[str, Any]]:
        """Get machines by type (coating, slitting, rewinding, etc.)"""
        return await self.get_all({'machine_type': machine_type})
    
    async def get_available(self) -> List[Dict[str, Any]]:
        """Get machines available for production"""
        async with async_session_factory() as session:
            result = await session.execute(
                select(Machine).where(
                    and_(
                        Machine.status == 'active',
                        Machine.current_job == None
                    )
                )
            )
            return [self._to_dict(obj) for obj in result.scalars().all()]


class OrderSheetRepository(BaseRepository[OrderSheet]):
    """Repository for Order Sheet (Production Order) operations"""
    model = OrderSheet
    
    async def get_by_status(self, status: str) -> List[Dict[str, Any]]:
        """Get order sheets by status"""
        return await self.get_all({'status': status})
    
    async def get_pending(self) -> List[Dict[str, Any]]:
        """Get pending order sheets"""
        return await self.get_all({'status': {'$in': ['pending', 'in_progress']}})
    
    async def generate_order_number(self) -> str:
        """Generate unique order sheet number"""
        count = await self.count()
        return f"OS-{datetime.now().strftime('%Y%m')}-{count + 1:04d}"


class WorkOrderRepository(BaseRepository[WorkOrder]):
    """Repository for Work Order operations"""
    model = WorkOrder
    
    async def get_by_order_sheet(self, order_sheet_id: str) -> List[Dict[str, Any]]:
        """Get work orders for an order sheet"""
        return await self.get_all({'order_sheet_id': order_sheet_id})
    
    async def get_by_stage(self, stage: str) -> List[Dict[str, Any]]:
        """Get work orders by production stage"""
        return await self.get_all({'stage': stage})
    
    async def get_by_machine(self, machine_id: str) -> List[Dict[str, Any]]:
        """Get work orders assigned to a machine"""
        return await self.get_all({'machine_id': machine_id})
    
    async def get_in_progress(self) -> List[Dict[str, Any]]:
        """Get work orders in progress"""
        return await self.get_all({'status': 'in_progress'})
    
    async def generate_wo_number(self) -> str:
        """Generate unique work order number"""
        count = await self.count()
        return f"WO-{datetime.now().strftime('%Y%m')}-{count + 1:04d}"


class ProductionEntryRepository(BaseRepository[ProductionEntry]):
    """Repository for Production Entry (actual production log) operations"""
    model = ProductionEntry
    
    async def get_by_work_order(self, work_order_id: str) -> List[Dict[str, Any]]:
        """Get production entries for a work order"""
        return await self.get_all({'work_order_id': work_order_id})
    
    async def get_by_machine(self, machine_id: str, date: str = None) -> List[Dict[str, Any]]:
        """Get production entries for a machine"""
        filters = {'machine_id': machine_id}
        if date:
            filters['production_date'] = date
        return await self.get_all(filters)
    
    async def get_by_date_range(self, start_date: str, end_date: str) -> List[Dict[str, Any]]:
        """Get production entries within date range"""
        async with async_session_factory() as session:
            result = await session.execute(
                select(ProductionEntry).where(
                    and_(
                        ProductionEntry.production_date >= start_date,
                        ProductionEntry.production_date <= end_date
                    )
                )
            )
            return [self._to_dict(obj) for obj in result.scalars().all()]


class RMRequisitionRepository(BaseRepository[RMRequisition]):
    """Repository for Raw Material Requisition operations"""
    model = RMRequisition
    
    async def get_by_work_order(self, work_order_id: str) -> List[Dict[str, Any]]:
        """Get RM requisitions for a work order"""
        return await self.get_all({'work_order_id': work_order_id})
    
    async def get_pending(self) -> List[Dict[str, Any]]:
        """Get pending RM requisitions"""
        return await self.get_all({'status': 'pending'})
    
    async def generate_requisition_number(self) -> str:
        """Generate unique requisition number"""
        count = await self.count()
        return f"RMR-{datetime.now().strftime('%Y%m')}-{count + 1:04d}"


class WorkOrderStageRepository(BaseRepository[WorkOrderStage]):
    """Repository for Work Order Stage operations"""
    model = WorkOrderStage
    
    async def get_by_work_order(self, work_order_id: str) -> List[Dict[str, Any]]:
        """Get stages for a work order"""
        return await self.get_all({'work_order_id': work_order_id}, sort_by='stage_number', sort_order=1)
    
    async def get_by_stage_name(self, stage_name: str) -> List[Dict[str, Any]]:
        """Get all stages by name"""
        return await self.get_all({'stage_name': stage_name})


class StageEntryRepository(BaseRepository[StageEntry]):
    """Repository for Stage Entry operations"""
    model = StageEntry
    
    async def get_by_stage(self, work_order_stage_id: str) -> List[Dict[str, Any]]:
        """Get entries for a stage"""
        return await self.get_all({'work_order_stage_id': work_order_stage_id})


# Repository instances
machine_repository = MachineRepository()
order_sheet_repository = OrderSheetRepository()
work_order_repository = WorkOrderRepository()
production_entry_repository = ProductionEntryRepository()
rm_requisition_repository = RMRequisitionRepository()
work_order_stage_repository = WorkOrderStageRepository()
stage_entry_repository = StageEntryRepository()
