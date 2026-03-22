"""
Multi-Branch Management Module
Supports:
- Individual branch dashboards for GST filings
- Consolidated Director Dashboard
- Branch-Bridge Ledger System
- Tax numbering per branch
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
import uuid
from server import db, get_current_user

router = APIRouter()


# ==================== BRANCH MODELS ====================
class BranchCreate(BaseModel):
    branch_code: str  # MH, GJ, DL
    branch_name: str
    state: str
    gstin: str
    address: str
    city: str
    pincode: str
    contact_person: Optional[str] = None
    contact_phone: Optional[str] = None
    contact_email: Optional[str] = None
    is_head_office: bool = False
    is_active: bool = True


class BranchUpdate(BaseModel):
    branch_name: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    pincode: Optional[str] = None
    contact_person: Optional[str] = None
    contact_phone: Optional[str] = None
    contact_email: Optional[str] = None
    is_active: Optional[bool] = None


class Branch(BaseModel):
    id: str
    branch_code: str
    branch_name: str
    state: str
    gstin: str
    address: str
    city: str
    pincode: str
    contact_person: Optional[str] = None
    contact_phone: Optional[str] = None
    contact_email: Optional[str] = None
    is_head_office: bool
    is_active: bool
    created_at: str
    updated_at: Optional[str] = None


# ==================== BRANCH LEDGER BRIDGE ====================
class BranchLedgerEntry(BaseModel):
    """For inter-branch transactions and consolidated view"""
    from_branch_id: str
    to_branch_id: str
    transaction_type: str  # stock_transfer, inter_branch_sale, expense_allocation
    amount: float
    reference_type: str
    reference_id: str
    narration: Optional[str] = None


# ==================== BRANCH ENDPOINTS ====================
@router.post("/", response_model=Branch)
async def create_branch(branch_data: BranchCreate, current_user: dict = Depends(get_current_user)):
    """Create a new branch"""
    if current_user['role'] != 'admin':
        raise HTTPException(status_code=403, detail="Only admins can create branches")
    
    # Check for duplicate branch code or GSTIN
    existing = await db.branches.find_one({
        '$or': [
            {'branch_code': branch_data.branch_code},
            {'gstin': branch_data.gstin}
        ]
    }, {'_id': 0})
    
    if existing:
        raise HTTPException(status_code=400, detail="Branch code or GSTIN already exists")
    
    branch_id = str(uuid.uuid4())
    branch_doc = {
        'id': branch_id,
        **branch_data.model_dump(),
        'created_at': datetime.now(timezone.utc).isoformat(),
        'created_by': current_user['id']
    }
    
    await db.branches.insert_one(branch_doc)
    return Branch(**{k: v for k, v in branch_doc.items() if k != '_id'})


@router.get("/", response_model=List[Branch])
async def get_branches(
    is_active: Optional[bool] = None,
    current_user: dict = Depends(get_current_user)
):
    """Get all branches"""
    query = {}
    if is_active is not None:
        query['is_active'] = is_active
    
    branches = await db.branches.find(query, {'_id': 0}).sort('branch_code', 1).to_list(100)
    return [Branch(**b) for b in branches]


@router.get("/{branch_id}", response_model=Branch)
async def get_branch(branch_id: str, current_user: dict = Depends(get_current_user)):
    """Get branch by ID"""
    branch = await db.branches.find_one({'id': branch_id}, {'_id': 0})
    if not branch:
        raise HTTPException(status_code=404, detail="Branch not found")
    return Branch(**branch)


@router.put("/{branch_id}", response_model=Branch)
async def update_branch(
    branch_id: str,
    update_data: BranchUpdate,
    current_user: dict = Depends(get_current_user)
):
    """Update branch details"""
    if current_user['role'] != 'admin':
        raise HTTPException(status_code=403, detail="Only admins can update branches")
    
    update_dict = {k: v for k, v in update_data.model_dump().items() if v is not None}
    update_dict['updated_at'] = datetime.now(timezone.utc).isoformat()
    
    result = await db.branches.update_one(
        {'id': branch_id},
        {'$set': update_dict}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Branch not found")
    
    branch = await db.branches.find_one({'id': branch_id}, {'_id': 0})
    return Branch(**branch)


# ==================== BRANCH DASHBOARD ====================
@router.get("/{branch_id}/dashboard")
async def get_branch_dashboard(
    branch_id: str,
    period: str = "month",
    current_user: dict = Depends(get_current_user)
):
    """
    Get branch-specific dashboard for GST filings
    Includes: Sales, Purchases, AR/AP, GST Summary
    """
    branch = await db.branches.find_one({'id': branch_id}, {'_id': 0})
    if not branch:
        raise HTTPException(status_code=404, detail="Branch not found")
    
    # Calculate date range based on period
    now = datetime.now(timezone.utc)
    if period == "month":
        from datetime import timedelta
        start_date = now.replace(day=1).isoformat()
    elif period == "quarter":
        quarter_start_month = ((now.month - 1) // 3) * 3 + 1
        start_date = now.replace(month=quarter_start_month, day=1).isoformat()
    else:  # year
        start_date = now.replace(month=4 if now.month >= 4 else 4, day=1).isoformat()
        if now.month < 4:
            start_date = (now.replace(year=now.year-1, month=4, day=1)).isoformat()
    
    # Sales summary
    sales_pipeline = [
        {'$match': {'branch_id': branch_id, 'invoice_type': 'Sales', 'created_at': {'$gte': start_date}}},
        {'$group': {
            '_id': None,
            'total_sales': {'$sum': '$grand_total'},
            'total_tax': {'$sum': '$total_tax'},
            'invoice_count': {'$sum': 1}
        }}
    ]
    sales_result = await db.invoices.aggregate(sales_pipeline).to_list(1)
    sales = sales_result[0] if sales_result else {'total_sales': 0, 'total_tax': 0, 'invoice_count': 0}
    
    # Purchase summary
    purchase_pipeline = [
        {'$match': {'branch_id': branch_id, 'invoice_type': 'Purchase', 'created_at': {'$gte': start_date}}},
        {'$group': {
            '_id': None,
            'total_purchases': {'$sum': '$grand_total'},
            'total_tax': {'$sum': '$total_tax'},
            'invoice_count': {'$sum': 1}
        }}
    ]
    purchase_result = await db.invoices.aggregate(purchase_pipeline).to_list(1)
    purchases = purchase_result[0] if purchase_result else {'total_purchases': 0, 'total_tax': 0, 'invoice_count': 0}
    
    # AR/AP summary
    ar_pipeline = [
        {'$match': {'branch_id': branch_id, 'invoice_type': 'Sales', 'status': {'$nin': ['paid', 'cancelled']}}},
        {'$group': {'_id': None, 'total_ar': {'$sum': '$balance_amount'}}}
    ]
    ar_result = await db.invoices.aggregate(ar_pipeline).to_list(1)
    ar = ar_result[0].get('total_ar', 0) if ar_result else 0
    
    ap_pipeline = [
        {'$match': {'branch_id': branch_id, 'invoice_type': 'Purchase', 'status': {'$nin': ['paid', 'cancelled']}}},
        {'$group': {'_id': None, 'total_ap': {'$sum': '$balance_amount'}}}
    ]
    ap_result = await db.invoices.aggregate(ap_pipeline).to_list(1)
    ap = ap_result[0].get('total_ap', 0) if ap_result else 0
    
    # GST Summary
    gst_summary = {
        'output_cgst': sales.get('total_tax', 0) / 2,
        'output_sgst': sales.get('total_tax', 0) / 2,
        'output_igst': 0,  # Calculate based on interstate sales
        'input_cgst': purchases.get('total_tax', 0) / 2,
        'input_sgst': purchases.get('total_tax', 0) / 2,
        'input_igst': 0,
        'net_payable': (sales.get('total_tax', 0) - purchases.get('total_tax', 0))
    }
    
    return {
        'branch': branch,
        'period': period,
        'sales': {
            'total': sales.get('total_sales', 0),
            'tax': sales.get('total_tax', 0),
            'count': sales.get('invoice_count', 0)
        },
        'purchases': {
            'total': purchases.get('total_purchases', 0),
            'tax': purchases.get('total_tax', 0),
            'count': purchases.get('invoice_count', 0)
        },
        'receivables': ar,
        'payables': ap,
        'gst_summary': gst_summary
    }


# ==================== CONSOLIDATED DIRECTOR DASHBOARD ====================
@router.get("/consolidated/dashboard")
async def get_consolidated_dashboard(
    period: str = "month",
    current_user: dict = Depends(get_current_user)
):
    """
    Consolidated Director Dashboard - Global business health
    Aggregates all branches
    """
    if current_user['role'] not in ['admin', 'director']:
        raise HTTPException(status_code=403, detail="Access denied. Directors only.")
    
    branches = await db.branches.find({'is_active': True}, {'_id': 0}).to_list(100)
    
    consolidated = {
        'total_sales': 0,
        'total_purchases': 0,
        'total_ar': 0,
        'total_ap': 0,
        'cash_position': 0,
        'branch_breakdown': []
    }
    
    for branch in branches:
        # Get each branch's data (simplified - in production, optimize with aggregation)
        sales = await db.invoices.aggregate([
            {'$match': {'branch_id': branch['id'], 'invoice_type': 'Sales'}},
            {'$group': {'_id': None, 'total': {'$sum': '$grand_total'}}}
        ]).to_list(1)
        
        branch_sales = sales[0].get('total', 0) if sales else 0
        
        consolidated['total_sales'] += branch_sales
        consolidated['branch_breakdown'].append({
            'branch_code': branch['branch_code'],
            'branch_name': branch['branch_name'],
            'sales': branch_sales
        })
    
    # Cash position (simplified)
    cash_ledger = await db.ledgers.find_one({'name': {'$regex': 'cash', '$options': 'i'}}, {'_id': 0})
    consolidated['cash_position'] = cash_ledger.get('current_balance', 0) if cash_ledger else 0
    
    return consolidated


# ==================== INTER-BRANCH TRANSACTIONS ====================
@router.post("/ledger-bridge")
async def create_branch_ledger_entry(
    entry: BranchLedgerEntry,
    current_user: dict = Depends(get_current_user)
):
    """
    Create inter-branch ledger entry
    Used for stock transfers, expense allocations, etc.
    """
    entry_id = str(uuid.uuid4())
    
    # Get branch details
    from_branch = await db.branches.find_one({'id': entry.from_branch_id}, {'_id': 0})
    to_branch = await db.branches.find_one({'id': entry.to_branch_id}, {'_id': 0})
    
    if not from_branch or not to_branch:
        raise HTTPException(status_code=404, detail="One or both branches not found")
    
    entry_doc = {
        'id': entry_id,
        **entry.model_dump(),
        'from_branch_code': from_branch['branch_code'],
        'to_branch_code': to_branch['branch_code'],
        'status': 'pending',
        'created_at': datetime.now(timezone.utc).isoformat(),
        'created_by': current_user['id']
    }
    
    await db.branch_ledger.insert_one(entry_doc)
    
    return {'id': entry_id, 'message': 'Inter-branch entry created'}


@router.get("/ledger-bridge/entries")
async def get_branch_ledger_entries(
    branch_id: Optional[str] = None,
    status: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Get inter-branch ledger entries"""
    query = {}
    if branch_id:
        query['$or'] = [{'from_branch_id': branch_id}, {'to_branch_id': branch_id}]
    if status:
        query['status'] = status
    
    entries = await db.branch_ledger.find(query, {'_id': 0}).sort('created_at', -1).to_list(500)
    return entries
