"""
Base Repository Pattern for PostgreSQL/SQLAlchemy
Generic repository providing common CRUD operations
"""
from typing import TypeVar, Generic, List, Optional, Dict, Any, Type
from datetime import datetime, timezone
import uuid
from sqlalchemy import select, update, delete, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import DeclarativeBase

from core.database import async_session_factory, Base
from core.exceptions import NotFoundError

T = TypeVar('T', bound=Base)


class BaseRepository(Generic[T]):
    """
    Base repository class providing common CRUD operations using SQLAlchemy
    All repositories should inherit from this class
    """
    
    model: Type[T] = None
    
    def __init__(self, session: Optional[AsyncSession] = None):
        if not self.model:
            raise ValueError("model must be defined")
        self._session = session
    
    async def _get_session(self) -> AsyncSession:
        """Get or create a session"""
        if self._session:
            return self._session
        return async_session_factory()
    
    def _to_dict(self, obj: T) -> Dict[str, Any]:
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
    def _convert_datetime_fields(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Convert datetime string fields to datetime objects"""
        from sqlalchemy import DateTime
        
        for col in self.model.__table__.columns:
            if col.name in data and isinstance(col.type, DateTime):
                val = data[col.name]
                if isinstance(val, str):
                    try:
                        if 'T' in val:
                            data[col.name] = datetime.fromisoformat(val.replace('Z', '+00:00'))
                        else:
                            data[col.name] = datetime.strptime(val, '%Y-%m-%d').replace(tzinfo=timezone.utc)
                    except ValueError:
                        pass  # Keep the original value if conversion fails
        return data
    
    # ==================== CREATE ====================
    async def create(self, data: Dict[str, Any], user_id: Optional[str] = None) -> Dict[str, Any]:
        """Create a new record"""
        async with async_session_factory() as session:
            # Generate ID if not provided
            if 'id' not in data or not data['id']:
                data['id'] = str(uuid.uuid4())
            
            # Add timestamps
            now = datetime.now(timezone.utc)
            data['created_at'] = now
            data['updated_at'] = now
            
            if user_id:
                data['created_by'] = user_id
                data['updated_by'] = user_id
            
            # Convert datetime string fields
            data = self._convert_datetime_fields(data)
            
            # Create instance
            obj = self.model(**data)
            session.add(obj)
            await session.commit()
            await session.refresh(obj)
            return self._to_dict(obj)
    
    async def create_many(self, documents: List[Dict[str, Any]], user_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Create multiple records"""
        async with async_session_factory() as session:
            now = datetime.now(timezone.utc)
            objects = []
            for data in documents:
                if 'id' not in data or not data['id']:
                    data['id'] = str(uuid.uuid4())
                data['created_at'] = now
                data['updated_at'] = now
                if user_id:
                    data['created_by'] = user_id
                obj = self.model(**data)
                objects.append(obj)
            
            session.add_all(objects)
            await session.commit()
            return [self._to_dict(obj) for obj in objects]
    
    # ==================== READ ====================
    async def get_by_id(self, id: str) -> Optional[Dict[str, Any]]:
        """Get a record by ID"""
        async with async_session_factory() as session:
            result = await session.execute(
                select(self.model).where(self.model.id == id)
            )
            obj = result.scalar_one_or_none()
            return self._to_dict(obj)
    
    async def get_by_id_or_raise(self, id: str, resource_name: str = "Resource") -> Dict[str, Any]:
        """Get a record by ID or raise NotFoundError"""
        result = await self.get_by_id(id)
        if not result:
            raise NotFoundError(resource_name, id)
        return result
    
    async def get_one(self, filters: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Get a single record matching the filters"""
        async with async_session_factory() as session:
            conditions = [getattr(self.model, k) == v for k, v in filters.items() if hasattr(self.model, k)]
            if not conditions:
                return None
            result = await session.execute(
                select(self.model).where(and_(*conditions))
            )
            obj = result.scalar_one_or_none()
            return self._to_dict(obj)
    
    async def get_all(
        self,
        filters: Optional[Dict[str, Any]] = None,
        sort_by: str = 'created_at',
        sort_order: int = -1,
        limit: int = 1000,
        skip: int = 0
    ) -> List[Dict[str, Any]]:
        """Get all records matching the filters"""
        async with async_session_factory() as session:
            query = select(self.model)
            
            # Apply filters
            if filters:
                conditions = self._build_conditions(filters)
                if conditions:
                    query = query.where(and_(*conditions))
            
            # Apply sorting
            if hasattr(self.model, sort_by):
                sort_col = getattr(self.model, sort_by)
                if sort_order == -1:
                    query = query.order_by(sort_col.desc())
                else:
                    query = query.order_by(sort_col.asc())
            
            # Apply pagination
            query = query.offset(skip).limit(limit)
            
            result = await session.execute(query)
            objects = result.scalars().all()
            return [self._to_dict(obj) for obj in objects]
    
    async def count(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """Count records matching the filters"""
        async with async_session_factory() as session:
            query = select(func.count()).select_from(self.model)
            
            if filters:
                conditions = self._build_conditions(filters)
                if conditions:
                    query = query.where(and_(*conditions))
            
            result = await session.execute(query)
            return result.scalar()
    
    def _convert_value(self, col, val):
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
    
    def _build_conditions(self, filters: Dict[str, Any]) -> List:
        """Build SQLAlchemy conditions from MongoDB-like filters"""
        conditions = []
        for key, value in filters.items():
            if hasattr(self.model, key):
                col = getattr(self.model, key)
                if isinstance(value, dict):
                    # Handle operators like $in, $ne, etc.
                    for op, val in value.items():
                        converted_val = self._convert_value(col, val)
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
                            if isinstance(value, dict) and value.get('$options', '') == 'i':
                                conditions.append(col.ilike(f'%{pattern}%'))
                            else:
                                conditions.append(col.like(f'%{pattern}%'))
                else:
                    conditions.append(col == value)
        return conditions
    
    async def exists(self, filters: Dict[str, Any]) -> bool:
        """Check if a record exists"""
        return await self.count(filters) > 0
    
    # ==================== UPDATE ====================
    async def update(
        self,
        id: str,
        data: Dict[str, Any],
        user_id: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """Update a record by ID"""
        async with async_session_factory() as session:
            # Add updated timestamp
            data['updated_at'] = datetime.now(timezone.utc)
            if user_id:
                data['updated_by'] = user_id
            
            # Remove None values and id from update
            update_data = {k: v for k, v in data.items() if v is not None and k != 'id' and hasattr(self.model, k)}
            
            if not update_data:
                return await self.get_by_id(id)
            
            await session.execute(
                update(self.model).where(self.model.id == id).values(**update_data)
            )
            await session.commit()
            
            return await self.get_by_id(id)
    
    async def update_or_raise(
        self,
        id: str,
        data: Dict[str, Any],
        user_id: Optional[str] = None,
        resource_name: str = "Resource"
    ) -> Dict[str, Any]:
        """Update a record or raise NotFoundError"""
        # Check if exists first
        existing = await self.get_by_id(id)
        if not existing:
            raise NotFoundError(resource_name, id)
        return await self.update(id, data, user_id)
    
    async def update_many(self, filters: Dict[str, Any], data: Dict[str, Any]) -> int:
        """Update multiple records"""
        async with async_session_factory() as session:
            data['updated_at'] = datetime.now(timezone.utc)
            
            conditions = [getattr(self.model, k) == v for k, v in filters.items() if hasattr(self.model, k)]
            update_data = {k: v for k, v in data.items() if hasattr(self.model, k)}
            
            if not conditions or not update_data:
                return 0
            
            result = await session.execute(
                update(self.model).where(and_(*conditions)).values(**update_data)
            )
            await session.commit()
            return result.rowcount
    
    async def upsert(self, filters: Dict[str, Any], data: Dict[str, Any], user_id: Optional[str] = None) -> Dict[str, Any]:
        """Update or insert a record"""
        existing = await self.get_one(filters)
        if existing:
            return await self.update(existing['id'], data, user_id)
        else:
            return await self.create({**filters, **data}, user_id)
    
    # ==================== DELETE ====================
    async def delete(self, id: str) -> bool:
        """Delete a record by ID"""
        async with async_session_factory() as session:
            result = await session.execute(
                delete(self.model).where(self.model.id == id)
            )
            await session.commit()
            return result.rowcount > 0
    
    async def delete_or_raise(self, id: str, resource_name: str = "Resource") -> bool:
        """Delete a record or raise NotFoundError"""
        if not await self.delete(id):
            raise NotFoundError(resource_name, id)
        return True
    
    async def delete_many(self, filters: Dict[str, Any]) -> int:
        """Delete multiple records"""
        async with async_session_factory() as session:
            conditions = [getattr(self.model, k) == v for k, v in filters.items() if hasattr(self.model, k)]
            
            if not conditions:
                return 0
            
            result = await session.execute(
                delete(self.model).where(and_(*conditions))
            )
            await session.commit()
            return result.rowcount
    
    # ==================== AGGREGATION ====================
    async def aggregate_sum(self, field: str, filters: Optional[Dict[str, Any]] = None) -> float:
        """Sum a field"""
        async with async_session_factory() as session:
            if not hasattr(self.model, field):
                return 0
            
            col = getattr(self.model, field)
            query = select(func.sum(col))
            
            if filters:
                conditions = [getattr(self.model, k) == v for k, v in filters.items() if hasattr(self.model, k)]
                if conditions:
                    query = query.where(and_(*conditions))
            
            result = await session.execute(query)
            return result.scalar() or 0
    
    async def distinct(self, field: str, filters: Optional[Dict[str, Any]] = None) -> List[Any]:
        """Get distinct values for a field"""
        async with async_session_factory() as session:
            if not hasattr(self.model, field):
                return []
            
            col = getattr(self.model, field)
            query = select(col).distinct()
            
            if filters:
                conditions = [getattr(self.model, k) == v for k, v in filters.items() if hasattr(self.model, k)]
                if conditions:
                    query = query.where(and_(*conditions))
            
            result = await session.execute(query)
            return [row[0] for row in result.fetchall()]
    
    # ==================== SEARCH ====================
    async def search(self, query: str, fields: List[str], limit: int = 50) -> List[Dict[str, Any]]:
        """Search across multiple fields (case-insensitive)"""
        async with async_session_factory() as session:
            conditions = []
            for field in fields:
                if hasattr(self.model, field):
                    col = getattr(self.model, field)
                    conditions.append(col.ilike(f'%{query}%'))
            
            if not conditions:
                return []
            
            stmt = select(self.model).where(or_(*conditions)).limit(limit)
            result = await session.execute(stmt)
            objects = result.scalars().all()
            return [self._to_dict(obj) for obj in objects]
