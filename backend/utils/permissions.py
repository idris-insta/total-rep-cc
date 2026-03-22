from functools import wraps
from fastapi import HTTPException

ROLE_PERMISSIONS = {
    'admin': {'all': ['*']},
    'sales_manager': {
        'crm': ['*'],
        'accounts': ['read'],
        'dashboard': ['read']
    },
    'production_manager': {
        'production': ['*'],
        'inventory': ['read'],
        'quality': ['*'],
        'dashboard': ['read']
    },
    'purchase_manager': {
        'procurement': ['*'],
        'inventory': ['read'],
        'dashboard': ['read']
    },
    'accounts_manager': {
        'accounts': ['*'],
        'dashboard': ['read']
    },
    'hr_manager': {
        'hrms': ['*'],
        'dashboard': ['read']
    },
    'quality_manager': {
        'quality': ['*'],
        'production': ['read'],
        'dashboard': ['read']
    },
    'warehouse_user': {
        'inventory': ['read', 'update']
    },
    'factory_operator': {
        'production': ['read', 'create']
    },
    'viewer': {
        'dashboard': ['read'],
        'all': ['read']
    }
}

def has_permission(user_role: str, module: str, action: str) -> bool:
    """
    Check if a user role has permission for a specific module and action.
    
    Args:
        user_role: The role of the user
        module: The module being accessed (e.g., 'crm', 'production')
        action: The action being performed (e.g., 'read', 'create', 'update', 'delete')
    
    Returns:
        bool: True if permission is granted, False otherwise
    """
    if user_role == 'admin':
        return True
    
    permissions = ROLE_PERMISSIONS.get(user_role, {})
    
    if 'all' in permissions and '*' in permissions['all']:
        return True
    
    if module in permissions:
        module_permissions = permissions[module]
        if '*' in module_permissions or action in module_permissions:
            return True
    
    if 'all' in permissions and action in permissions['all']:
        return True
    
    return False

def check_permission(module: str, action: str):
    """
    Decorator to check permissions for API endpoints.
    
    Usage:
        @check_permission('crm', 'create')
        async def create_lead(...):
            ...
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, current_user: dict = None, **kwargs):
            if current_user is None:
                raise HTTPException(status_code=401, detail="Authentication required")
            
            if not has_permission(current_user['role'], module, action):
                raise HTTPException(
                    status_code=403,
                    detail=f"Access denied. You don't have permission to {action} in {module} module."
                )
            
            return await func(*args, current_user=current_user, **kwargs)
        return wrapper
    return decorator

def filter_data_by_role(user_role: str, user_location: str, data: list, data_type: str) -> list:
    """
    Filter data based on user role and location.
    
    Args:
        user_role: The role of the user
        user_location: The location assigned to the user
        data: List of data items to filter
        data_type: Type of data ('inventory', 'production', etc.)
    
    Returns:
        Filtered list of data items
    """
    if user_role == 'admin':
        return data
    
    if user_role == 'warehouse_user' and user_location:
        if data_type == 'inventory':
            return [item for item in data if item.get('location') == user_location]
    
    if user_role == 'factory_operator' and user_location:
        if data_type == 'production':
            return [item for item in data if item.get('location') == user_location]
    
    return data