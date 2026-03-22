"""
Custom Exception Classes
Centralized exception handling for the application
"""
from fastapi import HTTPException, status
from typing import Optional, Any, Dict


class AppException(HTTPException):
    """Base application exception"""
    def __init__(
        self,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail: str = "An error occurred",
        headers: Optional[Dict[str, Any]] = None
    ):
        super().__init__(status_code=status_code, detail=detail, headers=headers)


class NotFoundError(AppException):
    """Resource not found exception"""
    def __init__(self, resource: str = "Resource", identifier: str = ""):
        detail = f"{resource} not found" + (f": {identifier}" if identifier else "")
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail=detail)


class ValidationError(AppException):
    """Validation error exception"""
    def __init__(self, detail: str = "Validation failed"):
        super().__init__(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=detail)


class AuthenticationError(AppException):
    """Authentication error exception"""
    def __init__(self, detail: str = "Authentication failed"):
        super().__init__(status_code=status.HTTP_401_UNAUTHORIZED, detail=detail)


class AuthorizationError(AppException):
    """Authorization error exception"""
    def __init__(self, detail: str = "Access denied"):
        super().__init__(status_code=status.HTTP_403_FORBIDDEN, detail=detail)


class DuplicateError(AppException):
    """Duplicate resource exception"""
    def __init__(self, resource: str = "Resource", field: str = ""):
        detail = f"{resource} already exists" + (f" with this {field}" if field else "")
        super().__init__(status_code=status.HTTP_409_CONFLICT, detail=detail)


class BusinessRuleError(AppException):
    """Business rule violation exception"""
    def __init__(self, detail: str = "Business rule violation"):
        super().__init__(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)


class ExternalServiceError(AppException):
    """External service error exception"""
    def __init__(self, service: str = "External service", detail: str = ""):
        message = f"{service} error" + (f": {detail}" if detail else "")
        super().__init__(status_code=status.HTTP_502_BAD_GATEWAY, detail=message)
