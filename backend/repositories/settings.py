"""
Settings Repositories - Data Access Layer for Settings module (PostgreSQL/SQLAlchemy)
"""
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone

from repositories.base import BaseRepository
from models.entities.other import FieldConfiguration, SystemSetting, CompanyProfile, Branch, NumberSeries
from models.entities.base import User
from core.database import async_session_factory


class FieldConfigurationRepository(BaseRepository[FieldConfiguration]):
    """Repository for Field Configuration operations (Field Registry)"""
    model = FieldConfiguration
    
    async def get_by_module(self, module: str) -> List[Dict[str, Any]]:
        """Get configurations for a module"""
        return await self.get_all({'module': module})
    
    async def get_by_module_and_entity(self, module: str, entity: str) -> Optional[Dict[str, Any]]:
        """Get configuration for specific module and entity"""
        return await self.get_one({'module': module, 'entity': entity})
    
    async def get_all_modules(self) -> List[str]:
        """Get list of all modules"""
        return await self.distinct('module')
    
    async def upsert_config(self, module: str, entity: str, config: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """Create or update a field configuration"""
        existing = await self.get_by_module_and_entity(module, entity)
        if existing:
            return await self.update(existing['id'], config, user_id)
        else:
            config['module'] = module
            config['entity'] = entity
            return await self.create(config, user_id)


class SystemSettingRepository(BaseRepository[SystemSetting]):
    """Repository for System Settings operations"""
    model = SystemSetting
    
    async def get_by_category(self, category: str) -> List[Dict[str, Any]]:
        """Get settings by category"""
        return await self.get_all({'category': category})
    
    async def get_setting(self, key: str) -> Optional[Dict[str, Any]]:
        """Get a specific setting by key"""
        return await self.get_one({'key': key})
    
    async def set_setting(self, key: str, value: Any, user_id: str, category: str = "general") -> Dict[str, Any]:
        """Set a system setting"""
        existing = await self.get_setting(key)
        if existing:
            return await self.update(existing['id'], {'value': str(value) if not isinstance(value, dict) else None, 'value_json': value if isinstance(value, dict) else None}, user_id)
        else:
            return await self.create({
                'key': key,
                'value': str(value) if not isinstance(value, dict) else None,
                'value_json': value if isinstance(value, dict) else None,
                'category': category
            }, user_id)


class CompanyProfileRepository(BaseRepository[CompanyProfile]):
    """Repository for Company Profile operations"""
    model = CompanyProfile
    
    async def get_active_profile(self) -> Optional[Dict[str, Any]]:
        """Get the active company profile"""
        return await self.get_one({'is_active': True})
    
    async def get_by_gstin(self, gstin: str) -> Optional[Dict[str, Any]]:
        """Get company by GSTIN"""
        return await self.get_one({'gstin': gstin})


class BranchRepository(BaseRepository[Branch]):
    """Repository for Branch operations"""
    model = Branch
    
    async def get_active_branches(self) -> List[Dict[str, Any]]:
        """Get all active branches"""
        return await self.get_all({'is_active': True})
    
    async def get_by_state(self, state: str) -> List[Dict[str, Any]]:
        """Get branches by state"""
        return await self.get_all({'state': state})
    
    async def get_head_office(self) -> Optional[Dict[str, Any]]:
        """Get the head office branch"""
        return await self.get_one({'is_head_office': True})


class UserRepository(BaseRepository[User]):
    """Repository for User operations"""
    model = User
    
    async def get_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Get user by email"""
        return await self.get_one({'email': email})
    
    async def get_by_role(self, role: str) -> List[Dict[str, Any]]:
        """Get users by role"""
        return await self.get_all({'role': role})
    
    async def get_active_users(self) -> List[Dict[str, Any]]:
        """Get all active users"""
        return await self.get_all({'is_active': True})


class NumberSeriesRepository(BaseRepository[NumberSeries]):
    """Repository for Number Series operations"""
    model = NumberSeries
    
    async def get_by_document_type(self, document_type: str, branch_id: str = None) -> Optional[Dict[str, Any]]:
        """Get number series for a document type"""
        filters = {'document_type': document_type}
        if branch_id:
            filters['branch_id'] = branch_id
        return await self.get_one(filters)
    
    async def get_next_number(self, document_type: str, branch_id: str = None) -> str:
        """Get next number in the series"""
        series = await self.get_by_document_type(document_type, branch_id)
        if not series:
            return f"{document_type}-0001"
        
        current = series.get('current_number', 0) + 1
        prefix = series.get('prefix', '')
        suffix = series.get('suffix', '')
        padding = series.get('padding', 4)
        
        # Update the series
        await self.update(series['id'], {'current_number': current})
        
        return f"{prefix}{str(current).zfill(padding)}{suffix}"


# Repository instances
field_configuration_repository = FieldConfigurationRepository()
system_setting_repository = SystemSettingRepository()
company_profile_repository = CompanyProfileRepository()
branch_repository = BranchRepository()
user_repository = UserRepository()
number_series_repository = NumberSeriesRepository()
