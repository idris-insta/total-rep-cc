"""
Legacy Database Compatibility Layer
Provides MongoDB-like interface for PostgreSQL to support legacy routes during migration
"""
from typing import Dict, Any, List, Optional
from sqlalchemy import select, insert, update, delete, func, and_, or_, text
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timezone
import uuid
import logging

from core.database import async_session_factory, Base
from models.entities import *

logger = logging.getLogger(__name__)


# Mapping of collection names to SQLAlchemy models
MODEL_MAP = {
    'users': User,
    'roles': Role,
    'leads': Lead,
    'accounts': Account,
    'quotations': Quotation,
    'samples': Sample,
    'followups': Followup,
    'items': Item,
    'warehouses': Warehouse,
    'stock': Stock,
    'stock_transfers': StockTransfer,
    'stock_adjustments': StockAdjustment,
    'batches': Batch,
    'bin_locations': BinLocation,
    'stock_ledger': StockLedger,
    'machines': Machine,
    'order_sheets': OrderSheet,
    'work_orders': WorkOrder,
    'production_entries': ProductionEntry,
    'rm_requisitions': RMRequisition,
    'work_order_stages': WorkOrderStage,
    'stage_entries': StageEntry,
    'invoices': Invoice,
    'payments': Payment,
    'journal_entries': JournalEntry,
    'chart_of_accounts': ChartOfAccounts,
    'ledgers': Ledger,
    'ledger_groups': LedgerGroup,
    'ledger_entries': LedgerEntry,
    'expenses': Expense,
    'suppliers': Supplier,
    'purchase_orders': PurchaseOrder,
    'purchase_requisitions': PurchaseRequisition,
    'grn': GRN,
    'landing_costs': LandingCost,
    'employees': Employee,
    'attendance': Attendance,
    'leave_requests': LeaveRequest,
    'leave_types': LeaveType,
    'salary_structures': SalaryStructure,
    'payroll': Payroll,
    'loans': Loan,
    'holidays': Holiday,
    'qc_inspections': QCInspection,
    'qc_parameters': QCParameter,
    'customer_complaints': CustomerComplaint,
    'tds_documents': TDSDocument,
    'sales_targets': SalesTarget,
    'incentive_slabs': IncentiveSlab,
    'incentive_payouts': IncentivePayout,
    'sales_achievements': SalesAchievement,
    'field_configurations': FieldConfiguration,
    'system_settings': SystemSetting,
    'company_profiles': CompanyProfile,
    'branches': Branch,
    'number_series': NumberSeries,
    'documents': Document,
    'drive_folders': DriveFolder,
    'drive_files': DriveFile,
    'notifications': Notification,
    'activity_logs': ActivityLog,
    'approval_requests': ApprovalRequest,
    'chat_rooms': ChatRoom,
    'chat_messages': ChatMessage,
    'e_invoices': EInvoice,
    'eway_bills': EWayBill,
    'transporters': Transporter,
    'gatepasses': Gatepass,
    'delivery_challans': DeliveryChallan,
    'ai_queries': AIQuery,
    'custom_reports': CustomReport,
    # Aliases for compatibility
    'customers': Account,
}


def _to_dict(obj) -> Dict[str, Any]:
    """Convert SQLAlchemy model to dictionary"""
    if obj is None:
        return None
    result = {}
    for column in obj.__table__.columns:
        value = getattr(obj, column.name)
        if isinstance(value, datetime):
            value = value.isoformat()
        result[column.name] = value
    return result


def _convert_value(col, val):
    """Convert value to appropriate type for column"""
    from sqlalchemy import DateTime
    
    # If the column is a datetime column and the value is a string, convert it
    if hasattr(col, 'type') and isinstance(col.type, DateTime):
        if isinstance(val, str):
            try:
                # Try ISO format
                if 'T' in val:
                    return datetime.fromisoformat(val.replace('Z', '+00:00'))
                # Try date-only format
                return datetime.strptime(val, '%Y-%m-%d').replace(tzinfo=timezone.utc)
            except ValueError:
                pass
    return val


def _build_filters(model, query: Dict[str, Any]):
    """Build SQLAlchemy filter conditions from MongoDB-like query"""
    conditions = []
    
    for key, value in query.items():
        if key == '$or':
            or_conditions = []
            for sub_query in value:
                sub_conds = _build_filters(model, sub_query)
                if sub_conds:
                    or_conditions.append(and_(*sub_conds) if len(sub_conds) > 1 else sub_conds[0])
            if or_conditions:
                conditions.append(or_(*or_conditions))
        elif key == '$and':
            for sub_query in value:
                conditions.extend(_build_filters(model, sub_query))
        elif hasattr(model, key):
            col = getattr(model, key)
            if isinstance(value, dict):
                for op, val in value.items():
                    converted_val = _convert_value(col, val)
                    if op == '$in':
                        conditions.append(col.in_(val))
                    elif op == '$nin':
                        conditions.append(~col.in_(val))
                    elif op == '$ne':
                        conditions.append(col != converted_val)
                    elif op == '$lt':
                        conditions.append(col < converted_val)
                    elif op == '$lte':
                        conditions.append(col <= converted_val)
                    elif op == '$gt':
                        conditions.append(col > converted_val)
                    elif op == '$gte':
                        conditions.append(col >= converted_val)
                    elif op == '$regex':
                        pattern = val
                        conditions.append(col.ilike(f'%{pattern}%'))
                    elif op == '$exists':
                        if val:
                            conditions.append(col != None)
                        else:
                            conditions.append(col == None)
            else:
                conditions.append(col == value)
    
    return conditions


class LegacyCollection:
    """MongoDB-like collection interface for PostgreSQL"""
    
    def __init__(self, model):
        self.model = model
    
    def _convert_datetime_fields(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Convert datetime string fields to datetime objects"""
        from sqlalchemy import DateTime
        
        for col in self.model.__table__.columns:
            if col.name in data:
                val = data[col.name]
                if isinstance(col.type, DateTime) and isinstance(val, str):
                    try:
                        if 'T' in val:
                            data[col.name] = datetime.fromisoformat(val.replace('Z', '+00:00'))
                        else:
                            data[col.name] = datetime.strptime(val, '%Y-%m-%d').replace(tzinfo=timezone.utc)
                    except ValueError:
                        pass  # Keep the original value if conversion fails
        return data
    
    async def find_one(self, query: Dict[str, Any] = None, projection: Dict[str, Any] = None) -> Optional[Dict[str, Any]]:
        """Find a single document"""
        async with async_session_factory() as session:
            stmt = select(self.model)
            if query:
                conditions = _build_filters(self.model, query)
                if conditions:
                    stmt = stmt.where(and_(*conditions))
            stmt = stmt.limit(1)
            result = await session.execute(stmt)
            obj = result.scalar_one_or_none()
            return _to_dict(obj)
    
    def find(self, query: Dict[str, Any] = None, projection: Dict[str, Any] = None):
        """Return a cursor-like object"""
        return LegacyCursor(self.model, query, projection)
    
    async def insert_one(self, document: Dict[str, Any]) -> Any:
        """Insert a single document"""
        async with async_session_factory() as session:
            if 'id' not in document or not document['id']:
                document['id'] = str(uuid.uuid4())
            if 'created_at' not in document:
                document['created_at'] = datetime.now(timezone.utc)
            if 'updated_at' not in document:
                document['updated_at'] = datetime.now(timezone.utc)
            
            # Filter out keys that don't exist in the model
            valid_keys = {c.name for c in self.model.__table__.columns}
            filtered_doc = {k: v for k, v in document.items() if k in valid_keys}
            
            # Convert datetime string fields
            filtered_doc = self._convert_datetime_fields(filtered_doc)
            
            obj = self.model(**filtered_doc)
            session.add(obj)
            await session.commit()
            return type('InsertResult', (), {'inserted_id': document['id']})()
    
    async def insert_many(self, documents: List[Dict[str, Any]]) -> Any:
        """Insert multiple documents"""
        async with async_session_factory() as session:
            valid_keys = {c.name for c in self.model.__table__.columns}
            for doc in documents:
                if 'id' not in doc or not doc['id']:
                    doc['id'] = str(uuid.uuid4())
                if 'created_at' not in doc:
                    doc['created_at'] = datetime.now(timezone.utc)
                if 'updated_at' not in doc:
                    doc['updated_at'] = datetime.now(timezone.utc)
                
                filtered_doc = {k: v for k, v in doc.items() if k in valid_keys}
                obj = self.model(**filtered_doc)
                session.add(obj)
            await session.commit()
            return type('InsertResult', (), {'inserted_ids': [d['id'] for d in documents]})()
    
    async def update_one(self, query: Dict[str, Any], update_data: Dict[str, Any]) -> Any:
        """Update a single document"""
        async with async_session_factory() as session:
            conditions = _build_filters(self.model, query)
            
            # Extract $set data
            if '$set' in update_data:
                data = update_data['$set']
            else:
                data = update_data
            
            data['updated_at'] = datetime.now(timezone.utc)
            valid_keys = {c.name for c in self.model.__table__.columns}
            filtered_data = {k: v for k, v in data.items() if k in valid_keys and k != 'id'}
            
            if conditions and filtered_data:
                stmt = update(self.model).where(and_(*conditions)).values(**filtered_data)
                result = await session.execute(stmt)
                await session.commit()
                return type('UpdateResult', (), {'matched_count': result.rowcount, 'modified_count': result.rowcount})()
            return type('UpdateResult', (), {'matched_count': 0, 'modified_count': 0})()
    
    async def update_many(self, query: Dict[str, Any], update_data: Dict[str, Any]) -> Any:
        """Update multiple documents"""
        return await self.update_one(query, update_data)
    
    async def delete_one(self, query: Dict[str, Any]) -> Any:
        """Delete a single document"""
        async with async_session_factory() as session:
            conditions = _build_filters(self.model, query)
            if conditions:
                stmt = delete(self.model).where(and_(*conditions))
                result = await session.execute(stmt)
                await session.commit()
                return type('DeleteResult', (), {'deleted_count': min(result.rowcount, 1)})()
            return type('DeleteResult', (), {'deleted_count': 0})()
    
    async def delete_many(self, query: Dict[str, Any]) -> Any:
        """Delete multiple documents"""
        async with async_session_factory() as session:
            conditions = _build_filters(self.model, query)
            if conditions:
                stmt = delete(self.model).where(and_(*conditions))
                result = await session.execute(stmt)
                await session.commit()
                return type('DeleteResult', (), {'deleted_count': result.rowcount})()
            return type('DeleteResult', (), {'deleted_count': 0})()
    
    async def count_documents(self, query: Dict[str, Any] = None, limit: int = None) -> int:
        """Count documents matching query"""
        async with async_session_factory() as session:
            stmt = select(func.count()).select_from(self.model)
            if query:
                conditions = _build_filters(self.model, query)
                if conditions:
                    stmt = stmt.where(and_(*conditions))
            result = await session.execute(stmt)
            return result.scalar()
    
    async def distinct(self, field: str, query: Dict[str, Any] = None) -> List[Any]:
        """Get distinct values for a field"""
        async with async_session_factory() as session:
            if not hasattr(self.model, field):
                return []
            col = getattr(self.model, field)
            stmt = select(col).distinct()
            if query:
                conditions = _build_filters(self.model, query)
                if conditions:
                    stmt = stmt.where(and_(*conditions))
            result = await session.execute(stmt)
            return [row[0] for row in result.fetchall()]
    
    def aggregate(self, pipeline: List[Dict[str, Any]]):
        """Return an aggregation cursor"""
        return LegacyAggregateCursor(self.model, pipeline)


class LegacyCursor:
    """MongoDB-like cursor for PostgreSQL"""
    
    def __init__(self, model, query: Dict[str, Any] = None, projection: Dict[str, Any] = None):
        self.model = model
        self.query = query or {}
        self.projection = projection
        self._sort_field = 'created_at'
        self._sort_order = -1
        self._skip = 0
        self._limit = 1000
    
    def sort(self, field: str, order: int = -1):
        """Set sort field and order"""
        self._sort_field = field
        self._sort_order = order
        return self
    
    def skip(self, count: int):
        """Set skip count"""
        self._skip = count
        return self
    
    def limit(self, count: int):
        """Set limit"""
        self._limit = count
        return self
    
    async def to_list(self, length: int = None) -> List[Dict[str, Any]]:
        """Execute query and return results"""
        async with async_session_factory() as session:
            stmt = select(self.model)
            
            if self.query:
                conditions = _build_filters(self.model, self.query)
                if conditions:
                    stmt = stmt.where(and_(*conditions))
            
            if hasattr(self.model, self._sort_field):
                col = getattr(self.model, self._sort_field)
                if self._sort_order == -1:
                    stmt = stmt.order_by(col.desc())
                else:
                    stmt = stmt.order_by(col.asc())
            
            stmt = stmt.offset(self._skip).limit(length or self._limit)
            
            result = await session.execute(stmt)
            return [_to_dict(obj) for obj in result.scalars().all()]


class LegacyAggregateCursor:
    """MongoDB-like aggregation cursor for PostgreSQL"""
    
    def __init__(self, model, pipeline: List[Dict[str, Any]]):
        self.model = model
        self.pipeline = pipeline
    
    async def to_list(self, length: int = None) -> List[Dict[str, Any]]:
        """Execute aggregation and return results"""
        async with async_session_factory() as session:
            stmt = select(self.model)
            
            for stage in self.pipeline:
                if '$match' in stage:
                    conditions = _build_filters(self.model, stage['$match'])
                    if conditions:
                        stmt = stmt.where(and_(*conditions))
                elif '$limit' in stage:
                    stmt = stmt.limit(stage['$limit'])
                elif '$skip' in stage:
                    stmt = stmt.offset(stage['$skip'])
                elif '$sort' in stage:
                    for field, order in stage['$sort'].items():
                        if hasattr(self.model, field):
                            col = getattr(self.model, field)
                            if order == -1:
                                stmt = stmt.order_by(col.desc())
                            else:
                                stmt = stmt.order_by(col.asc())
            
            result = await session.execute(stmt)
            return [_to_dict(obj) for obj in result.scalars().all()]


class LegacyDatabase:
    """MongoDB-like database interface for PostgreSQL"""
    
    def __getattr__(self, collection_name: str) -> LegacyCollection:
        """Get a collection by name"""
        model = MODEL_MAP.get(collection_name)
        if model is None:
            # Create a dynamic model for unknown collections
            logger.warning(f"Unknown collection: {collection_name}, returning empty collection")
            # Return a stub that returns empty results
            return LegacyStubCollection(collection_name)
        return LegacyCollection(model)
    
    def __getitem__(self, collection_name: str) -> LegacyCollection:
        """Get a collection by name using bracket notation"""
        return self.__getattr__(collection_name)


class LegacyStubCollection:
    """Stub collection for unknown/unmapped collections"""
    
    def __init__(self, name: str):
        self.name = name
        logger.warning(f"Stub collection created for: {name}")
    
    async def find_one(self, *args, **kwargs):
        return None
    
    def find(self, *args, **kwargs):
        return LegacyStubCursor()
    
    async def insert_one(self, *args, **kwargs):
        return type('InsertResult', (), {'inserted_id': str(uuid.uuid4())})()
    
    async def insert_many(self, *args, **kwargs):
        return type('InsertResult', (), {'inserted_ids': []})()
    
    async def update_one(self, *args, **kwargs):
        return type('UpdateResult', (), {'matched_count': 0, 'modified_count': 0})()
    
    async def update_many(self, *args, **kwargs):
        return type('UpdateResult', (), {'matched_count': 0, 'modified_count': 0})()
    
    async def delete_one(self, *args, **kwargs):
        return type('DeleteResult', (), {'deleted_count': 0})()
    
    async def delete_many(self, *args, **kwargs):
        return type('DeleteResult', (), {'deleted_count': 0})()
    
    async def count_documents(self, *args, **kwargs):
        return 0
    
    async def distinct(self, *args, **kwargs):
        return []
    
    def aggregate(self, *args, **kwargs):
        return LegacyStubCursor()


class LegacyStubCursor:
    """Stub cursor for unknown collections"""
    
    def sort(self, *args, **kwargs):
        return self
    
    def skip(self, *args, **kwargs):
        return self
    
    def limit(self, *args, **kwargs):
        return self
    
    async def to_list(self, *args, **kwargs):
        return []


# Create the global legacy database instance
db = LegacyDatabase()
