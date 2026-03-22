"""
Settings Services - Business Logic Layer for Settings module
"""
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone

from repositories.settings import (
    field_configuration_repository,
    system_setting_repository,
    company_profile_repository,
    branch_repository,
    user_repository
)
from core.exceptions import NotFoundError, ValidationError, DuplicateError
from core.legacy_db import db


class FieldConfigurationService:
    """Business logic for Field Configuration (Field Registry) management"""
    
    def __init__(self):
        self.repo = field_configuration_repository
    
    async def get_all_configurations(self, module: str = None) -> List[Dict[str, Any]]:
        """Get all field configurations"""
        if module:
            return await self.repo.get_by_module(module)
        return await self.repo.get_all()
    
    async def get_configuration(self, module: str, entity: str) -> Optional[Dict[str, Any]]:
        """Get configuration for a specific module and entity"""
        return await self.repo.get_by_module_and_entity(module, entity)
    
    async def save_configuration(self, module: str, entity: str, config: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """Save (create or update) a field configuration"""
        return await self.repo.upsert_config(module, entity, config, user_id)
    
    async def get_available_modules(self) -> List[str]:
        """Get list of all available modules"""
        return await self.repo.get_all_modules()


class SystemSettingService:
    """Business logic for System Settings management"""
    
    def __init__(self):
        self.repo = system_setting_repository
    
    async def get_all_settings(self, category: str = None) -> List[Dict[str, Any]]:
        """Get all system settings"""
        if category:
            return await self.repo.get_by_category(category)
        return await self.repo.get_all()
    
    async def get_setting(self, key: str) -> Any:
        """Get a specific setting value"""
        setting = await self.repo.get_setting(key)
        return setting.get('value') if setting else None
    
    async def set_setting(self, key: str, value: Any, user_id: str, category: str = "general") -> Dict[str, Any]:
        """Set a system setting"""
        return await self.repo.set_setting(key, value, user_id, category)
    
    async def get_settings_by_keys(self, keys: List[str]) -> Dict[str, Any]:
        """Get multiple settings by keys"""
        result = {}
        for key in keys:
            setting = await self.repo.get_setting(key)
            result[key] = setting.get('value') if setting else None
        return result


class CompanyProfileService:
    """Business logic for Company Profile management"""
    
    def __init__(self):
        self.repo = company_profile_repository
    
    async def get_active_profile(self) -> Optional[Dict[str, Any]]:
        """Get the active company profile"""
        return await self.repo.get_active_profile()
    
    async def create_profile(self, data: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """Create a new company profile"""
        # Deactivate existing profiles
        existing = await self.repo.get_all()
        for profile in existing:
            await self.repo.update(profile['id'], {'is_active': False}, user_id)
        
        data['is_active'] = True
        return await self.repo.create(data, user_id)
    
    async def update_profile(self, profile_id: str, data: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """Update company profile"""
        return await self.repo.update_or_raise(profile_id, data, user_id, "Company Profile")


class BranchService:
    """Business logic for Branch management"""
    
    def __init__(self):
        self.repo = branch_repository
    
    async def get_all_branches(self, active_only: bool = True) -> List[Dict[str, Any]]:
        """Get all branches"""
        if active_only:
            return await self.repo.get_active_branches()
        return await self.repo.get_all()
    
    async def get_branch(self, branch_id: str) -> Dict[str, Any]:
        """Get a single branch"""
        return await self.repo.get_by_id_or_raise(branch_id, "Branch")
    
    async def create_branch(self, data: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """Create a new branch"""
        data['is_active'] = True
        return await self.repo.create(data, user_id)
    
    async def update_branch(self, branch_id: str, data: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """Update a branch"""
        return await self.repo.update_or_raise(branch_id, data, user_id, "Branch")
    
    async def get_head_office(self) -> Optional[Dict[str, Any]]:
        """Get the head office branch"""
        return await self.repo.get_head_office()


class UserService:
    """Business logic for User management"""
    
    def __init__(self):
        self.repo = user_repository
    
    async def get_all_users(self, filters: Optional[Dict] = None) -> List[Dict[str, Any]]:
        """Get all users with optional filters"""
        query = {}
        if filters:
            if filters.get('role'):
                query['role'] = filters['role']
            if filters.get('is_active') is not None:
                query['is_active'] = filters['is_active']
        return await self.repo.get_all(query)
    
    async def get_user(self, user_id: str) -> Dict[str, Any]:
        """Get a single user"""
        return await self.repo.get_by_id_or_raise(user_id, "User")
    
    async def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Get user by email"""
        return await self.repo.get_by_email(email)
    
    async def create_user(self, data: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """Create a new user"""
        # Check for duplicate email
        existing = await self.repo.get_by_email(data['email'])
        if existing:
            raise DuplicateError("User", f"email '{data['email']}'")
        
        # Hash password
        import bcrypt
        if data.get('password'):
            data['hashed_password'] = bcrypt.hashpw(data['password'].encode(), bcrypt.gensalt()).decode()
            del data['password']
        
        data['is_active'] = True
        return await self.repo.create(data, user_id)
    
    async def update_user(self, user_id: str, data: Dict[str, Any], current_user_id: str) -> Dict[str, Any]:
        """Update a user"""
        # Hash password if provided
        import bcrypt
        if data.get('password'):
            data['hashed_password'] = bcrypt.hashpw(data['password'].encode(), bcrypt.gensalt()).decode()
            del data['password']
        
        return await self.repo.update_or_raise(user_id, data, current_user_id, "User")
    
    async def deactivate_user(self, user_id: str, current_user_id: str) -> Dict[str, Any]:
        """Deactivate a user"""
        return await self.repo.update_or_raise(user_id, {'is_active': False}, current_user_id, "User")


# Service instances
field_configuration_service = FieldConfigurationService()
system_setting_service = SystemSettingService()
company_profile_service = CompanyProfileService()
branch_service = BranchService()
user_service = UserService()
