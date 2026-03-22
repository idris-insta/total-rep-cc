"""
Accounts Services - Business Logic Layer for Accounts module
"""
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone

from repositories.accounts import (
    invoice_repository,
    payment_repository,
    journal_entry_repository,
    coa_repository
)
from repositories.crm import account_repository
from core.exceptions import NotFoundError, ValidationError, BusinessRuleError
from core.legacy_db import db


class InvoiceService:
    """Business logic for Invoice management"""
    
    def __init__(self):
        self.repo = invoice_repository
    
    async def get_all_invoices(self, filters: Optional[Dict] = None) -> List[Dict[str, Any]]:
        """Get all invoices with optional filters"""
        query = {}
        if filters:
            if filters.get('invoice_type'):
                query['invoice_type'] = filters['invoice_type']
            if filters.get('status'):
                query['status'] = filters['status']
            if filters.get('account_id'):
                query['account_id'] = filters['account_id']
        return await self.repo.get_all(query)
    
    async def get_invoice(self, invoice_id: str) -> Dict[str, Any]:
        """Get a single invoice"""
        return await self.repo.get_by_id_or_raise(invoice_id, "Invoice")
    
    async def create_invoice(self, data: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """Create a new invoice with tax calculations"""
        # Get account details
        account = await account_repository.get_by_id(data['account_id'])
        if not account:
            raise NotFoundError("Account", data['account_id'])
        
        # Calculate item totals
        items = []
        subtotal = 0
        total_discount = 0
        total_cgst = 0
        total_sgst = 0
        total_igst = 0
        
        for item in data.get('items', []):
            qty = item.get('quantity', 0)
            unit_price = item.get('unit_price', 0)
            discount_percent = item.get('discount_percent', 0)
            tax_percent = item.get('tax_percent', 18)
            
            line_total = qty * unit_price
            discount_amount = line_total * discount_percent / 100
            taxable = line_total - discount_amount
            
            # GST calculation (assume intra-state for now)
            cgst = taxable * (tax_percent / 2) / 100
            sgst = taxable * (tax_percent / 2) / 100
            
            items.append({
                **item,
                'line_total': line_total,
                'discount_amount': discount_amount,
                'taxable_amount': taxable,
                'cgst': cgst,
                'sgst': sgst,
                'igst': 0,
                'total': taxable + cgst + sgst
            })
            
            subtotal += line_total
            total_discount += discount_amount
            total_cgst += cgst
            total_sgst += sgst
        
        # Generate invoice number
        invoice_number = await self.repo.generate_invoice_number(data.get('invoice_type', 'Sales'))
        
        invoice_data = {
            **data,
            'invoice_number': invoice_number,
            'account_name': account.get('company_name') or account.get('name'),
            'account_gstin': account.get('gstin'),
            'items': items,
            'subtotal': round(subtotal, 2),
            'discount_amount': round(total_discount, 2),
            'taxable_amount': round(subtotal - total_discount, 2),
            'cgst_amount': round(total_cgst, 2),
            'sgst_amount': round(total_sgst, 2),
            'igst_amount': round(total_igst, 2),
            'total_tax': round(total_cgst + total_sgst + total_igst, 2),
            'grand_total': round(subtotal - total_discount + total_cgst + total_sgst + total_igst, 2),
            'status': 'draft',
            'paid_amount': 0,
            'balance_amount': round(subtotal - total_discount + total_cgst + total_sgst + total_igst, 2)
        }
        
        return await self.repo.create(invoice_data, user_id)
    
    async def update_invoice_status(self, invoice_id: str, status: str, user_id: str) -> Dict[str, Any]:
        """Update invoice status"""
        valid_statuses = ['draft', 'sent', 'partial', 'paid', 'overdue', 'cancelled']
        if status not in valid_statuses:
            raise ValidationError(f"Invalid status. Must be one of: {valid_statuses}")
        
        return await self.repo.update_or_raise(invoice_id, {'status': status}, user_id, "Invoice")
    
    async def record_payment(self, invoice_id: str, amount: float, user_id: str) -> Dict[str, Any]:
        """Record payment against an invoice"""
        invoice = await self.get_invoice(invoice_id)
        
        new_paid = invoice.get('paid_amount', 0) + amount
        new_balance = invoice.get('grand_total', 0) - new_paid
        
        status = 'paid' if new_balance <= 0 else 'partial'
        
        return await self.repo.update(invoice_id, {
            'paid_amount': new_paid,
            'balance_amount': max(0, new_balance),
            'status': status
        }, user_id)
    
    async def get_overdue_invoices(self) -> List[Dict[str, Any]]:
        """Get all overdue invoices"""
        return await self.repo.get_overdue()
    
    async def get_invoice_aging(self) -> Dict[str, Any]:
        """Get invoice aging summary"""
        today = datetime.now(timezone.utc).strftime('%Y-%m-%d')
        invoices = await self.repo.get_all({'status': {'$in': ['sent', 'partial', 'overdue']}})
        
        aging = {
            'current': 0,
            '1_30_days': 0,
            '31_60_days': 0,
            '61_90_days': 0,
            'over_90_days': 0
        }
        
        for inv in invoices:
            due_date = inv.get('due_date', today)
            balance = inv.get('balance_amount', 0)
            days_overdue = (datetime.strptime(today, '%Y-%m-%d') - datetime.strptime(due_date, '%Y-%m-%d')).days
            
            if days_overdue <= 0:
                aging['current'] += balance
            elif days_overdue <= 30:
                aging['1_30_days'] += balance
            elif days_overdue <= 60:
                aging['31_60_days'] += balance
            elif days_overdue <= 90:
                aging['61_90_days'] += balance
            else:
                aging['over_90_days'] += balance
        
        return aging


class PaymentService:
    """Business logic for Payment management"""
    
    def __init__(self):
        self.repo = payment_repository
    
    async def get_all_payments(self, filters: Optional[Dict] = None) -> List[Dict[str, Any]]:
        """Get all payments with optional filters"""
        query = {}
        if filters:
            if filters.get('payment_type'):
                query['payment_type'] = filters['payment_type']
            if filters.get('account_id'):
                query['account_id'] = filters['account_id']
        return await self.repo.get_all(query)
    
    async def create_payment(self, data: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """Create a payment and apply to invoices"""
        # Get account details
        account = await account_repository.get_by_id(data['account_id'])
        if not account:
            raise NotFoundError("Account", data['account_id'])
        
        # Generate payment number
        payment_number = await self.repo.generate_payment_number(data.get('payment_type', 'receipt'))
        
        payment_data = {
            **data,
            'payment_number': payment_number,
            'account_name': account.get('company_name') or account.get('name'),
            'status': 'completed'
        }
        
        payment = await self.repo.create(payment_data, user_id)
        
        # Apply to invoices if specified
        for inv_payment in data.get('invoices', []):
            await invoice_service.record_payment(
                inv_payment['invoice_id'],
                inv_payment['amount'],
                user_id
            )
        
        return payment


class JournalEntryService:
    """Business logic for Journal Entry management"""
    
    def __init__(self):
        self.repo = journal_entry_repository
    
    async def get_all_entries(self, filters: Optional[Dict] = None) -> List[Dict[str, Any]]:
        """Get all journal entries"""
        query = {}
        if filters:
            if filters.get('start_date') and filters.get('end_date'):
                query['entry_date'] = {
                    '$gte': filters['start_date'],
                    '$lte': filters['end_date']
                }
        return await self.repo.get_all(query)
    
    async def create_entry(self, data: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """Create a journal entry"""
        # Validate debit = credit
        total_debit = sum(line.get('debit', 0) for line in data.get('lines', []))
        total_credit = sum(line.get('credit', 0) for line in data.get('lines', []))
        
        if round(total_debit, 2) != round(total_credit, 2):
            raise ValidationError(f"Debit ({total_debit}) must equal Credit ({total_credit})")
        
        entry_number = await self.repo.generate_entry_number()
        
        entry_data = {
            **data,
            'entry_number': entry_number,
            'total_debit': total_debit,
            'total_credit': total_credit,
            'status': 'posted'
        }
        
        return await self.repo.create(entry_data, user_id)


# Service instances
invoice_service = InvoiceService()
payment_service = PaymentService()
journal_entry_service = JournalEntryService()
