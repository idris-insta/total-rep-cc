"""
Expense & Financial Control Module
Handles:
- Expense Buckets (Exhibitions, Marketing, Utilities, etc.)
- Expense Claims & Reimbursements
- Budget Tracking
- Auto-calculate material weight on invoices
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from typing import List, Optional, Dict
from datetime import datetime, timezone
import uuid
from server import db, get_current_user
from utils.document_numbering import generate_document_number

router = APIRouter()


# ==================== EXPENSE BUCKET MODELS ====================
class ExpenseBucketCreate(BaseModel):
    bucket_name: str
    bucket_code: str
    category: str  # Fixed, Variable, One-time
    description: Optional[str] = None
    budget_amount: float = 0
    budget_period: str = "monthly"  # monthly, quarterly, yearly
    ledger_id: Optional[str] = None
    is_active: bool = True


class ExpenseBucket(BaseModel):
    id: str
    bucket_name: str
    bucket_code: str
    category: str
    description: Optional[str] = None
    budget_amount: float
    budget_period: str
    ledger_id: Optional[str] = None
    spent_amount: float = 0
    remaining_budget: float = 0
    is_active: bool
    created_at: str


# ==================== EXPENSE ENTRY MODELS ====================
class ExpenseEntryCreate(BaseModel):
    bucket_id: str
    expense_date: str
    amount: float
    payment_mode: str  # cash, bank, credit_card, petty_cash
    vendor_name: Optional[str] = None
    invoice_no: Optional[str] = None
    description: str
    branch_id: Optional[str] = None
    department: Optional[str] = None
    project_id: Optional[str] = None
    attachments: List[str] = []  # document IDs
    is_reimbursable: bool = False
    employee_id: Optional[str] = None  # For reimbursements


class ExpenseEntry(BaseModel):
    id: str
    expense_no: str
    bucket_id: str
    bucket_name: Optional[str] = None
    expense_date: str
    amount: float
    payment_mode: str
    vendor_name: Optional[str] = None
    invoice_no: Optional[str] = None
    description: str
    branch_id: Optional[str] = None
    department: Optional[str] = None
    project_id: Optional[str] = None
    attachments: List[str]
    is_reimbursable: bool
    employee_id: Optional[str] = None
    reimbursement_status: Optional[str] = None  # pending, approved, paid, rejected
    status: str  # draft, submitted, approved, rejected, paid
    created_at: str
    created_by: str
    approved_by: Optional[str] = None
    approved_at: Optional[str] = None


# ==================== DEFAULT EXPENSE BUCKETS ====================
DEFAULT_BUCKETS = [
    {'bucket_code': 'EXHB', 'bucket_name': 'Exhibitions & Trade Shows', 'category': 'Variable'},
    {'bucket_code': 'MKTG', 'bucket_name': 'Marketing & Advertising', 'category': 'Variable'},
    {'bucket_code': 'UTIL', 'bucket_name': 'Utilities (Electricity/Water/Gas)', 'category': 'Fixed'},
    {'bucket_code': 'RENT', 'bucket_name': 'Rent & Lease', 'category': 'Fixed'},
    {'bucket_code': 'TRVL', 'bucket_name': 'Travel & Conveyance', 'category': 'Variable'},
    {'bucket_code': 'COMM', 'bucket_name': 'Communication (Phone/Internet)', 'category': 'Fixed'},
    {'bucket_code': 'STNY', 'bucket_name': 'Stationery & Printing', 'category': 'Variable'},
    {'bucket_code': 'REPR', 'bucket_name': 'Repairs & Maintenance', 'category': 'Variable'},
    {'bucket_code': 'INSR', 'bucket_name': 'Insurance', 'category': 'Fixed'},
    {'bucket_code': 'PROF', 'bucket_name': 'Professional Fees (Legal/CA)', 'category': 'Variable'},
    {'bucket_code': 'BANK', 'bucket_name': 'Bank Charges', 'category': 'Variable'},
    {'bucket_code': 'MISC', 'bucket_name': 'Miscellaneous', 'category': 'Variable'},
]


# ==================== EXPENSE BUCKET ENDPOINTS ====================
@router.post("/buckets/bootstrap")
async def bootstrap_expense_buckets(current_user: dict = Depends(get_current_user)):
    """Initialize default expense buckets"""
    if current_user['role'] != 'admin':
        raise HTTPException(status_code=403, detail="Admin only")
    
    created = 0
    for bucket in DEFAULT_BUCKETS:
        existing = await db.expense_buckets.find_one({'bucket_code': bucket['bucket_code']}, {'_id': 0})
        if not existing:
            await db.expense_buckets.insert_one({
                'id': str(uuid.uuid4()),
                **bucket,
                'description': None,
                'budget_amount': 0,
                'budget_period': 'monthly',
                'ledger_id': None,
                'spent_amount': 0,
                'remaining_budget': 0,
                'is_active': True,
                'created_at': datetime.now(timezone.utc).isoformat(),
                'created_by': current_user['id']
            })
            created += 1
    
    return {'message': f'Created {created} expense buckets', 'total': len(DEFAULT_BUCKETS)}


@router.post("/buckets", response_model=ExpenseBucket)
async def create_expense_bucket(data: ExpenseBucketCreate, current_user: dict = Depends(get_current_user)):
    """Create a new expense bucket"""
    if current_user['role'] not in ['admin', 'accountant']:
        raise HTTPException(status_code=403, detail="Access denied")
    
    existing = await db.expense_buckets.find_one({'bucket_code': data.bucket_code}, {'_id': 0})
    if existing:
        raise HTTPException(status_code=400, detail="Bucket code already exists")
    
    bucket_id = str(uuid.uuid4())
    bucket_doc = {
        'id': bucket_id,
        **data.model_dump(),
        'spent_amount': 0,
        'remaining_budget': data.budget_amount,
        'created_at': datetime.now(timezone.utc).isoformat(),
        'created_by': current_user['id']
    }
    
    await db.expense_buckets.insert_one(bucket_doc)
    return ExpenseBucket(**{k: v for k, v in bucket_doc.items() if k != '_id'})


@router.get("/buckets", response_model=List[ExpenseBucket])
async def get_expense_buckets(
    category: Optional[str] = None,
    is_active: Optional[bool] = None,
    current_user: dict = Depends(get_current_user)
):
    """Get all expense buckets"""
    query = {}
    if category:
        query['category'] = category
    if is_active is not None:
        query['is_active'] = is_active
    
    buckets = await db.expense_buckets.find(query, {'_id': 0}).sort('bucket_name', 1).to_list(100)
    return [ExpenseBucket(**b) for b in buckets]


@router.put("/buckets/{bucket_id}/budget")
async def update_bucket_budget(
    bucket_id: str,
    budget_amount: float,
    budget_period: str = "monthly",
    current_user: dict = Depends(get_current_user)
):
    """Update expense bucket budget"""
    if current_user['role'] not in ['admin', 'accountant']:
        raise HTTPException(status_code=403, detail="Access denied")
    
    bucket = await db.expense_buckets.find_one({'id': bucket_id}, {'_id': 0})
    if not bucket:
        raise HTTPException(status_code=404, detail="Bucket not found")
    
    remaining = budget_amount - bucket.get('spent_amount', 0)
    
    await db.expense_buckets.update_one(
        {'id': bucket_id},
        {'$set': {
            'budget_amount': budget_amount,
            'budget_period': budget_period,
            'remaining_budget': remaining,
            'updated_at': datetime.now(timezone.utc).isoformat()
        }}
    )
    
    return {'message': 'Budget updated', 'remaining': remaining}


# ==================== EXPENSE ENTRY ENDPOINTS ====================
@router.post("/entries", response_model=ExpenseEntry)
async def create_expense_entry(data: ExpenseEntryCreate, current_user: dict = Depends(get_current_user)):
    """Create a new expense entry"""
    # Verify bucket exists
    bucket = await db.expense_buckets.find_one({'id': data.bucket_id}, {'_id': 0})
    if not bucket:
        raise HTTPException(status_code=404, detail="Expense bucket not found")
    
    entry_id = str(uuid.uuid4())
    branch_code = 'HO'
    if data.branch_id:
        branch = await db.branches.find_one({'id': data.branch_id}, {'_id': 0})
        branch_code = branch.get('branch_code', 'HO') if branch else 'HO'
    
    expense_no = await generate_document_number(db, 'expense', branch_code)
    
    entry_doc = {
        'id': entry_id,
        'expense_no': expense_no,
        **data.model_dump(),
        'bucket_name': bucket['bucket_name'],
        'reimbursement_status': 'pending' if data.is_reimbursable else None,
        'status': 'draft',
        'created_at': datetime.now(timezone.utc).isoformat(),
        'created_by': current_user['id'],
        'approved_by': None,
        'approved_at': None
    }
    
    await db.expense_entries.insert_one(entry_doc)
    return ExpenseEntry(**{k: v for k, v in entry_doc.items() if k != '_id'})


@router.get("/entries", response_model=List[ExpenseEntry])
async def get_expense_entries(
    bucket_id: Optional[str] = None,
    status: Optional[str] = None,
    branch_id: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Get all expense entries"""
    query = {}
    if bucket_id:
        query['bucket_id'] = bucket_id
    if status:
        query['status'] = status
    if branch_id:
        query['branch_id'] = branch_id
    if date_from:
        query['expense_date'] = {'$gte': date_from}
    if date_to:
        if 'expense_date' in query:
            query['expense_date']['$lte'] = date_to
        else:
            query['expense_date'] = {'$lte': date_to}
    
    entries = await db.expense_entries.find(query, {'_id': 0}).sort('expense_date', -1).to_list(500)
    return [ExpenseEntry(**e) for e in entries]


@router.put("/entries/{entry_id}/approve")
async def approve_expense_entry(entry_id: str, current_user: dict = Depends(get_current_user)):
    """Approve expense entry"""
    if current_user['role'] not in ['admin', 'manager', 'accountant']:
        raise HTTPException(status_code=403, detail="Access denied")
    
    entry = await db.expense_entries.find_one({'id': entry_id}, {'_id': 0})
    if not entry:
        raise HTTPException(status_code=404, detail="Expense entry not found")
    
    if entry['status'] != 'submitted':
        raise HTTPException(status_code=400, detail="Entry not in submitted status")
    
    # Update entry status
    await db.expense_entries.update_one(
        {'id': entry_id},
        {'$set': {
            'status': 'approved',
            'approved_by': current_user['id'],
            'approved_at': datetime.now(timezone.utc).isoformat()
        }}
    )
    
    # Update bucket spent amount
    await db.expense_buckets.update_one(
        {'id': entry['bucket_id']},
        {
            '$inc': {'spent_amount': entry['amount'], 'remaining_budget': -entry['amount']}
        }
    )
    
    return {'message': 'Expense approved', 'entry_id': entry_id}


@router.put("/entries/{entry_id}/submit")
async def submit_expense_entry(entry_id: str, current_user: dict = Depends(get_current_user)):
    """Submit expense entry for approval"""
    entry = await db.expense_entries.find_one({'id': entry_id}, {'_id': 0})
    if not entry:
        raise HTTPException(status_code=404, detail="Expense entry not found")
    
    if entry['status'] != 'draft':
        raise HTTPException(status_code=400, detail="Entry not in draft status")
    
    await db.expense_entries.update_one(
        {'id': entry_id},
        {'$set': {'status': 'submitted'}}
    )
    
    return {'message': 'Expense submitted for approval', 'entry_id': entry_id}


# ==================== EXPENSE ANALYTICS ====================
@router.get("/analytics/by-bucket")
async def get_expense_analytics_by_bucket(
    period: str = "month",
    branch_id: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Get expense analytics grouped by bucket"""
    match_query = {'status': 'approved'}
    if branch_id:
        match_query['branch_id'] = branch_id
    
    pipeline = [
        {'$match': match_query},
        {'$group': {
            '_id': '$bucket_id',
            'bucket_name': {'$first': '$bucket_name'},
            'total_amount': {'$sum': '$amount'},
            'count': {'$sum': 1}
        }},
        {'$sort': {'total_amount': -1}}
    ]
    
    results = await db.expense_entries.aggregate(pipeline).to_list(50)
    
    # Get budget info
    for r in results:
        bucket = await db.expense_buckets.find_one({'id': r['_id']}, {'_id': 0})
        if bucket:
            r['budget_amount'] = bucket.get('budget_amount', 0)
            r['utilization'] = round((r['total_amount'] / bucket['budget_amount'] * 100), 1) if bucket.get('budget_amount') else 0
    
    return results


@router.get("/analytics/trend")
async def get_expense_trend(
    months: int = 6,
    bucket_id: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Get expense trend over months"""
    match_query = {'status': 'approved'}
    if bucket_id:
        match_query['bucket_id'] = bucket_id
    
    pipeline = [
        {'$match': match_query},
        {'$addFields': {
            'month': {'$substr': ['$expense_date', 0, 7]}
        }},
        {'$group': {
            '_id': '$month',
            'total_amount': {'$sum': '$amount'},
            'count': {'$sum': 1}
        }},
        {'$sort': {'_id': -1}},
        {'$limit': months}
    ]
    
    results = await db.expense_entries.aggregate(pipeline).to_list(months)
    return results
