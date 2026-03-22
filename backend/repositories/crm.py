"""
CRM Repositories - Data Access Layer for CRM module (PostgreSQL/SQLAlchemy)
"""
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
from sqlalchemy import select, and_, or_, func
from sqlalchemy.ext.asyncio import AsyncSession

from repositories.base import BaseRepository
from models.entities.base import Lead, Account, Quotation, Sample, Followup
from core.database import async_session_factory


class LeadRepository(BaseRepository[Lead]):
    """Repository for Lead operations"""
    model = Lead
    
    async def get_by_status(self, status: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Get leads by status"""
        return await self.get_all({'status': status}, limit=limit)
    
    async def get_kanban_data(self, stages: List[str]) -> Dict[str, List[Dict[str, Any]]]:
        """Get leads grouped by status for Kanban view"""
        result = {}
        for stage in stages:
            result[stage] = await self.get_by_status(stage)
        return result
    
    async def update_status(self, lead_id: str, new_status: str, user_id: str) -> Optional[Dict[str, Any]]:
        """Update lead status"""
        return await self.update(lead_id, {'status': new_status}, user_id)
    
    async def get_by_assigned_user(self, user_id: str) -> List[Dict[str, Any]]:
        """Get leads assigned to a specific user"""
        return await self.get_all({'assigned_to': user_id})
    
    async def search(self, query: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Search leads by company name, contact person, or email"""
        return await super().search(query, ['company_name', 'contact_person', 'email'], limit)


class AccountRepository(BaseRepository[Account]):
    """Repository for Account (Customer/Supplier) operations"""
    model = Account
    
    async def get_by_type(self, account_type: str) -> List[Dict[str, Any]]:
        """Get accounts by type (customer/supplier/both)"""
        if account_type == 'all':
            return await self.get_all()
        return await self.get_all({'account_type': {'$in': [account_type, 'both']}})
    
    async def get_customers(self) -> List[Dict[str, Any]]:
        """Get all customer accounts"""
        async with async_session_factory() as session:
            result = await session.execute(
                select(Account).where(
                    or_(Account.account_type == 'customer', Account.account_type == 'both')
                )
            )
            return [self._to_dict(obj) for obj in result.scalars().all()]
    
    async def get_suppliers(self) -> List[Dict[str, Any]]:
        """Get all supplier accounts"""
        async with async_session_factory() as session:
            result = await session.execute(
                select(Account).where(
                    or_(Account.account_type == 'supplier', Account.account_type == 'both')
                )
            )
            return [self._to_dict(obj) for obj in result.scalars().all()]
    
    async def get_by_gstin(self, gstin: str) -> Optional[Dict[str, Any]]:
        """Get account by GSTIN"""
        return await self.get_one({'gstin': gstin})
    
    async def search(self, query: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Search accounts by name or GSTIN"""
        return await super().search(query, ['customer_name', 'gstin'], limit)
    
    async def get_with_balance(self, account_id: str) -> Optional[Dict[str, Any]]:
        """Get account with calculated receivable/payable balance"""
        account = await self.get_by_id(account_id)
        if not account:
            return None
        
        # Calculate receivable from invoices - will need Invoice repository
        from repositories.accounts import invoice_repository
        balance = await invoice_repository.get_pending_amount(account_id)
        account['receivable_amount'] = balance
        
        return account


class QuotationRepository(BaseRepository[Quotation]):
    """Repository for Quotation operations"""
    model = Quotation
    
    async def get_by_account(self, account_id: str) -> List[Dict[str, Any]]:
        """Get quotations for an account"""
        return await self.get_all({'account_id': account_id})
    
    async def get_by_status(self, status: str) -> List[Dict[str, Any]]:
        """Get quotations by status"""
        return await self.get_all({'status': status})
    
    async def generate_quote_number(self) -> str:
        """Generate unique quote number"""
        count = await self.count()
        return f"QT-{datetime.now().strftime('%Y%m')}-{count + 1:04d}"
    
    async def update_status(self, quote_id: str, status: str, user_id: str) -> Optional[Dict[str, Any]]:
        """Update quotation status"""
        return await self.update(quote_id, {'status': status}, user_id)
    
    async def get_total_value(self, status: Optional[str] = None) -> float:
        """Get total value of quotations"""
        filters = {} if not status else {'status': status}
        return await self.aggregate_sum('grand_total', filters)


class SampleRepository(BaseRepository[Sample]):
    """Repository for Sample operations"""
    model = Sample
    
    async def get_by_account(self, account_id: str) -> List[Dict[str, Any]]:
        """Get samples for an account"""
        return await self.get_all({'account_id': account_id})
    
    async def get_by_status(self, status: str) -> List[Dict[str, Any]]:
        """Get samples by status"""
        return await self.get_all({'status': status})
    
    async def generate_sample_number(self) -> str:
        """Generate unique sample number"""
        count = await self.count()
        return f"SMP-{datetime.now().strftime('%Y%m')}-{count + 1:04d}"
    
    async def get_pending_feedback(self) -> List[Dict[str, Any]]:
        """Get samples pending feedback"""
        async with async_session_factory() as session:
            result = await session.execute(
                select(Sample).where(
                    and_(
                        Sample.status == 'feedback_pending',
                        Sample.feedback_due_date <= datetime.now(timezone.utc)
                    )
                )
            )
            return [self._to_dict(obj) for obj in result.scalars().all()]


class FollowupRepository(BaseRepository[Followup]):
    """Repository for Followup operations"""
    model = Followup
    
    async def get_by_lead(self, lead_id: str) -> List[Dict[str, Any]]:
        """Get followups for a lead"""
        return await self.get_all({'lead_id': lead_id})
    
    async def get_by_account(self, account_id: str) -> List[Dict[str, Any]]:
        """Get followups for an account"""
        return await self.get_all({'account_id': account_id})
    
    async def get_pending(self) -> List[Dict[str, Any]]:
        """Get pending followups"""
        return await self.get_all({'status': 'pending'})


# Repository instances
lead_repository = LeadRepository()
account_repository = AccountRepository()
quotation_repository = QuotationRepository()
sample_repository = SampleRepository()
followup_repository = FollowupRepository()
