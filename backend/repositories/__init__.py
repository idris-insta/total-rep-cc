"""
Repositories Layer - Data Access
"""
from .crm import lead_repository, account_repository, quotation_repository, sample_repository
from .base import BaseRepository

__all__ = [
    "BaseRepository",
    "lead_repository",
    "account_repository",
    "quotation_repository", 
    "sample_repository"
]
