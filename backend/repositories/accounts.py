"""
Accounts Repositories - Data Access Layer for Accounts module (PostgreSQL/SQLAlchemy)
"""
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
from sqlalchemy import select, and_, func

from repositories.base import BaseRepository
from models.entities.accounts import Invoice, Payment, JournalEntry, ChartOfAccounts, Ledger, LedgerGroup, LedgerEntry, Expense
from core.database import async_session_factory


class InvoiceRepository(BaseRepository[Invoice]):
    """Repository for Invoice operations"""
    model = Invoice
    
    async def get_by_type(self, invoice_type: str) -> List[Dict[str, Any]]:
        """Get invoices by type (Sales, Purchase, Credit Note, Debit Note)"""
        return await self.get_all({'invoice_type': invoice_type})
    
    async def get_by_account(self, account_id: str) -> List[Dict[str, Any]]:
        """Get invoices for an account"""
        return await self.get_all({'account_id': account_id})
    
    async def get_by_status(self, status: str) -> List[Dict[str, Any]]:
        """Get invoices by status"""
        return await self.get_all({'status': status})
    
    async def get_overdue(self) -> List[Dict[str, Any]]:
        """Get overdue invoices"""
        today = datetime.now(timezone.utc)
        async with async_session_factory() as session:
            result = await session.execute(
                select(Invoice).where(
                    and_(
                        Invoice.status.in_(['sent', 'partial']),
                        Invoice.due_date < today
                    )
                )
            )
            return [self._to_dict(obj) for obj in result.scalars().all()]
    
    async def generate_invoice_number(self, invoice_type: str = "Sales") -> str:
        """Generate unique invoice number"""
        prefix = "INV" if invoice_type == "Sales" else "PINV" if invoice_type == "Purchase" else "CN" if invoice_type == "Credit Note" else "DN"
        count = await self.count({'invoice_type': invoice_type})
        return f"{prefix}-{datetime.now().strftime('%Y%m')}-{count + 1:04d}"
    
    async def get_pending_amount(self, account_id: str) -> float:
        """Get total pending amount for an account"""
        async with async_session_factory() as session:
            result = await session.execute(
                select(func.sum(Invoice.balance_amount)).where(
                    and_(
                        Invoice.account_id == account_id,
                        Invoice.status.in_(['sent', 'partial', 'overdue'])
                    )
                )
            )
            return result.scalar() or 0


class PaymentRepository(BaseRepository[Payment]):
    """Repository for Payment operations"""
    model = Payment
    
    async def get_by_type(self, payment_type: str) -> List[Dict[str, Any]]:
        """Get payments by type (receipt, payment)"""
        return await self.get_all({'payment_type': payment_type})
    
    async def get_by_account(self, account_id: str) -> List[Dict[str, Any]]:
        """Get payments for an account"""
        return await self.get_all({'account_id': account_id})
    
    async def generate_payment_number(self, payment_type: str = "receipt") -> str:
        """Generate unique payment number"""
        prefix = "REC" if payment_type == "receipt" else "PAY"
        count = await self.count({'payment_type': payment_type})
        return f"{prefix}-{datetime.now().strftime('%Y%m')}-{count + 1:04d}"


class JournalEntryRepository(BaseRepository[JournalEntry]):
    """Repository for Journal Entry operations"""
    model = JournalEntry
    
    async def get_by_date_range(self, start_date: str, end_date: str) -> List[Dict[str, Any]]:
        """Get journal entries within date range"""
        async with async_session_factory() as session:
            result = await session.execute(
                select(JournalEntry).where(
                    and_(
                        JournalEntry.entry_date >= start_date,
                        JournalEntry.entry_date <= end_date
                    )
                )
            )
            return [self._to_dict(obj) for obj in result.scalars().all()]
    
    async def generate_entry_number(self) -> str:
        """Generate unique journal entry number"""
        count = await self.count()
        return f"JE-{datetime.now().strftime('%Y%m')}-{count + 1:04d}"


class ChartOfAccountsRepository(BaseRepository[ChartOfAccounts]):
    """Repository for Chart of Accounts operations"""
    model = ChartOfAccounts
    
    async def get_by_type(self, account_type: str) -> List[Dict[str, Any]]:
        """Get accounts by type (Asset, Liability, Equity, Revenue, Expense)"""
        return await self.get_all({'account_type': account_type})
    
    async def get_by_parent(self, parent_id: str) -> List[Dict[str, Any]]:
        """Get child accounts"""
        return await self.get_all({'parent_id': parent_id})


class LedgerRepository(BaseRepository[Ledger]):
    """Repository for Ledger operations"""
    model = Ledger
    
    async def get_by_group(self, group_id: str) -> List[Dict[str, Any]]:
        """Get ledgers by group"""
        return await self.get_all({'ledger_group_id': group_id})
    
    async def get_by_account(self, account_id: str) -> Optional[Dict[str, Any]]:
        """Get ledger linked to an account"""
        return await self.get_one({'account_id': account_id})


class LedgerGroupRepository(BaseRepository[LedgerGroup]):
    """Repository for Ledger Group operations"""
    model = LedgerGroup
    
    async def get_by_parent(self, parent_id: str) -> List[Dict[str, Any]]:
        """Get child groups"""
        return await self.get_all({'parent_id': parent_id})
    
    async def get_primary_groups(self) -> List[Dict[str, Any]]:
        """Get primary groups"""
        return await self.get_all({'is_primary': True})


class LedgerEntryRepository(BaseRepository[LedgerEntry]):
    """Repository for Ledger Entry operations"""
    model = LedgerEntry
    
    async def get_by_ledger(self, ledger_id: str) -> List[Dict[str, Any]]:
        """Get entries for a ledger"""
        return await self.get_all({'ledger_id': ledger_id}, sort_by='entry_date')
    
    async def get_by_voucher(self, voucher_number: str) -> List[Dict[str, Any]]:
        """Get entries for a voucher"""
        return await self.get_all({'voucher_number': voucher_number})


class ExpenseRepository(BaseRepository[Expense]):
    """Repository for Expense operations"""
    model = Expense
    
    async def get_by_category(self, category: str) -> List[Dict[str, Any]]:
        """Get expenses by category"""
        return await self.get_all({'category': category})
    
    async def get_by_status(self, status: str) -> List[Dict[str, Any]]:
        """Get expenses by status"""
        return await self.get_all({'status': status})
    
    async def get_pending_approval(self) -> List[Dict[str, Any]]:
        """Get expenses pending approval"""
        return await self.get_all({'status': 'pending'})


# Repository instances
invoice_repository = InvoiceRepository()
payment_repository = PaymentRepository()
journal_entry_repository = JournalEntryRepository()
coa_repository = ChartOfAccountsRepository()
ledger_repository = LedgerRepository()
ledger_group_repository = LedgerGroupRepository()
ledger_entry_repository = LedgerEntryRepository()
expense_repository = ExpenseRepository()
