"""
CRM Services - Business Logic Layer for CRM module
"""
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone

from repositories.crm import (
    lead_repository,
    account_repository,
    quotation_repository,
    sample_repository
)
from core.exceptions import NotFoundError, ValidationError, DuplicateError
from core.legacy_db import db


class LeadService:
    """Business logic for Lead management"""
    
    def __init__(self):
        self.repo = lead_repository
    
    async def get_all_leads(self, filters: Optional[Dict] = None) -> List[Dict[str, Any]]:
        """Get all leads with optional filters"""
        query = {}
        if filters:
            if filters.get('status'):
                query['status'] = filters['status']
            if filters.get('assigned_to'):
                query['assigned_to'] = filters['assigned_to']
            if filters.get('source'):
                query['source'] = filters['source']
        return await self.repo.get_all(query)
    
    async def get_lead(self, lead_id: str) -> Dict[str, Any]:
        """Get a single lead by ID"""
        return await self.repo.get_by_id_or_raise(lead_id, "Lead")
    
    async def create_lead(self, data: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """Create a new lead"""
        # Check for duplicate email if provided
        if data.get('email'):
            existing = await self.repo.get_one({'email': data['email']})
            if existing:
                raise DuplicateError("Lead", "email")
        
        return await self.repo.create(data, user_id)
    
    async def update_lead(self, lead_id: str, data: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """Update an existing lead"""
        return await self.repo.update_or_raise(lead_id, data, user_id, "Lead")
    
    async def delete_lead(self, lead_id: str) -> bool:
        """Delete a lead"""
        return await self.repo.delete_or_raise(lead_id, "Lead")
    
    async def move_to_stage(self, lead_id: str, new_stage: str, user_id: str) -> Dict[str, Any]:
        """Move lead to a new stage"""
        lead = await self.get_lead(lead_id)
        old_stage = lead.get('status')
        
        # Log stage change
        await db.lead_activities.insert_one({
            'lead_id': lead_id,
            'activity_type': 'stage_change',
            'old_value': old_stage,
            'new_value': new_stage,
            'user_id': user_id,
            'created_at': datetime.now(timezone.utc).isoformat()
        })
        
        return await self.repo.update(lead_id, {'status': new_stage}, user_id)
    
    async def get_kanban_view(self, stages: List[str]) -> Dict[str, List[Dict[str, Any]]]:
        """Get leads organized for Kanban view"""
        return await self.repo.get_kanban_data(stages)
    
    async def convert_to_account(self, lead_id: str, user_id: str) -> Dict[str, Any]:
        """Convert a qualified lead to a customer account"""
        lead = await self.get_lead(lead_id)
        
        # Create account from lead data
        account_data = {
            'customer_name': lead.get('company_name'),
            'account_type': 'customer',
            'billing_address': lead.get('address'),
            'billing_city': lead.get('city'),
            'billing_state': lead.get('state'),
            'billing_pincode': lead.get('pincode'),
            'industry': lead.get('industry'),
            'notes': f"Converted from Lead: {lead.get('company_name')}"
        }
        
        account = await account_repository.create(account_data, user_id)
        
        # Update lead status
        await self.repo.update(lead_id, {
            'status': 'converted',
            'converted_account_id': account['id']
        }, user_id)
        
        return account


class AccountService:
    """Business logic for Account management"""
    
    def __init__(self):
        self.repo = account_repository
    
    async def get_all_accounts(self, account_type: str = 'all') -> List[Dict[str, Any]]:
        """Get all accounts with optional type filter"""
        return await self.repo.get_by_type(account_type)
    
    async def get_account(self, account_id: str) -> Dict[str, Any]:
        """Get a single account with balance"""
        return await self.repo.get_with_balance(account_id)
    
    async def create_account(self, data: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """Create a new account"""
        # Check for duplicate GSTIN if provided
        if data.get('gstin'):
            existing = await self.repo.get_by_gstin(data['gstin'])
            if existing:
                raise DuplicateError("Account", "GSTIN")
        
        return await self.repo.create(data, user_id)
    
    async def update_account(self, account_id: str, data: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """Update an existing account"""
        return await self.repo.update_or_raise(account_id, data, user_id, "Account")
    
    async def delete_account(self, account_id: str) -> bool:
        """Delete an account"""
        # Check for dependent records
        quotes = await quotation_repository.count({'account_id': account_id})
        if quotes > 0:
            raise ValidationError(f"Cannot delete account with {quotes} quotations")
        
        return await self.repo.delete_or_raise(account_id, "Account")
    
    async def get_customer_health(self, account_id: str) -> Dict[str, Any]:
        """Get customer health metrics"""
        account = await self.get_account(account_id)
        
        # Get quote stats
        quotes = await quotation_repository.get_by_account(account_id)
        total_quotes = len(quotes)
        accepted_quotes = len([q for q in quotes if q.get('status') == 'accepted'])
        
        return {
            'account_id': account_id,
            'customer_name': account.get('customer_name'),
            'total_quotes': total_quotes,
            'conversion_rate': (accepted_quotes / total_quotes * 100) if total_quotes > 0 else 0,
            'receivable_amount': account.get('receivable_amount', 0),
            'credit_limit': account.get('credit_limit', 0),
            'credit_utilized_percent': 0  # Calculate based on outstanding
        }


class QuotationService:
    """Business logic for Quotation management"""
    
    def __init__(self):
        self.repo = quotation_repository
    
    async def get_all_quotations(self, filters: Optional[Dict] = None) -> List[Dict[str, Any]]:
        """Get all quotations with optional filters"""
        query = {}
        if filters:
            if filters.get('status'):
                query['status'] = filters['status']
            if filters.get('account_id'):
                query['account_id'] = filters['account_id']
        return await self.repo.get_all(query)
    
    async def get_quotation(self, quote_id: str) -> Dict[str, Any]:
        """Get a single quotation"""
        return await self.repo.get_by_id_or_raise(quote_id, "Quotation")
    
    async def create_quotation(self, data: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """Create a new quotation"""
        # Verify account exists
        account = await account_repository.get_by_id(data['account_id'])
        if not account:
            raise NotFoundError("Account", data['account_id'])
        
        # Generate quote number
        data['quote_number'] = await self.repo.generate_quote_number()
        data['status'] = 'draft'
        
        # Calculate totals
        data = self._calculate_totals(data)
        
        return await self.repo.create(data, user_id)
    
    async def update_quotation(self, quote_id: str, data: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """Update an existing quotation"""
        # Recalculate totals if items changed
        if 'items' in data:
            data = self._calculate_totals(data)
        
        return await self.repo.update_or_raise(quote_id, data, user_id, "Quotation")
    
    async def delete_quotation(self, quote_id: str) -> bool:
        """Delete a quotation"""
        return await self.repo.delete_or_raise(quote_id, "Quotation")
    
    def _calculate_totals(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate quotation totals from line items"""
        items = data.get('items', [])
        subtotal = 0
        tax_amount = 0
        
        for item in items:
            qty = item.get('quantity', 0)
            price = item.get('unit_price', 0)
            disc = item.get('discount_percent', 0)
            tax = item.get('tax_percent', 0)
            
            line_total = qty * price * (1 - disc / 100)
            line_tax = line_total * tax / 100
            item['amount'] = line_total + line_tax
            
            subtotal += line_total
            tax_amount += line_tax
        
        header_discount = data.get('header_discount_percent', 0)
        discount_amount = subtotal * header_discount / 100
        
        data['subtotal'] = round(subtotal, 2)
        data['tax_amount'] = round(tax_amount, 2)
        data['discount_amount'] = round(discount_amount, 2)
        data['grand_total'] = round(subtotal + tax_amount - discount_amount, 2)
        
        return data
    
    async def convert_to_sales_order(self, quote_id: str, user_id: str) -> Dict[str, Any]:
        """Convert quotation to sales order"""
        quote = await self.get_quotation(quote_id)
        
        # Create sales order
        so_data = {
            'quotation_id': quote_id,
            'account_id': quote.get('account_id'),
            'items': quote.get('items', []),
            'subtotal': quote.get('subtotal'),
            'tax_amount': quote.get('tax_amount'),
            'grand_total': quote.get('grand_total'),
            'status': 'confirmed'
        }
        
        # Generate SO number
        count = await db.sales_orders.count_documents({})
        so_data['so_number'] = f"SO-{datetime.now().strftime('%Y%m')}-{count + 1:04d}"
        so_data['created_at'] = datetime.now(timezone.utc).isoformat()
        so_data['created_by'] = user_id
        
        await db.sales_orders.insert_one(so_data)
        
        # Update quotation status
        await self.repo.update(quote_id, {'status': 'accepted'}, user_id)
        
        return so_data


class SampleService:
    """Business logic for Sample management"""
    
    def __init__(self):
        self.repo = sample_repository
    
    async def get_all_samples(self, filters: Optional[Dict] = None) -> List[Dict[str, Any]]:
        """Get all samples with optional filters"""
        query = {}
        if filters:
            if filters.get('status'):
                query['status'] = filters['status']
            if filters.get('account_id'):
                query['account_id'] = filters['account_id']
        return await self.repo.get_all(query)
    
    async def create_sample(self, data: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """Create a new sample request"""
        # Verify account exists
        account = await account_repository.get_by_id(data['account_id'])
        if not account:
            raise NotFoundError("Account", data['account_id'])
        
        # Generate sample number
        data['sample_number'] = await self.repo.generate_sample_number()
        data['status'] = 'pending'
        
        return await self.repo.create(data, user_id)
    
    async def update_status(self, sample_id: str, status: str, user_id: str) -> Dict[str, Any]:
        """Update sample status"""
        await self.repo.get_by_id_or_raise(sample_id, "Sample")
        return await self.repo.update(sample_id, {'status': status}, user_id)
    
    async def record_feedback(self, sample_id: str, feedback: str, status: str, user_id: str) -> Dict[str, Any]:
        """Record sample feedback"""
        return await self.repo.update(sample_id, {
            'feedback': feedback,
            'status': status,
            'feedback_recorded_at': datetime.now(timezone.utc).isoformat()
        }, user_id)


# Service instances
lead_service = LeadService()
account_service = AccountService()
quotation_service = QuotationService()
sample_service = SampleService()
