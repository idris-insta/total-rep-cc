"""
Sales Incentives Module
Handles:
- Target Setting (Monthly/Quarterly/Yearly)
- Achievement Tracking
- Auto-bonus calculation for exceeding targets
- Commission calculation
- Incentive payout tracking
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict
from datetime import datetime, timezone
import uuid
from server import db, get_current_user

router = APIRouter()


# ==================== TARGET MODELS ====================
class SalesTargetCreate(BaseModel):
    employee_id: str
    target_type: str  # monthly, quarterly, yearly
    period: str  # YYYY-MM for monthly, YYYY-Q1/Q2/Q3/Q4 for quarterly, YYYY for yearly
    target_amount: float
    target_quantity: int = 0
    product_category: Optional[str] = None  # Specific category or 'all'
    branch_id: Optional[str] = None
    notes: Optional[str] = None


class SalesTarget(BaseModel):
    id: str
    employee_id: str
    employee_name: Optional[str] = None
    target_type: str
    period: str
    target_amount: float
    target_quantity: int
    achieved_amount: float = 0
    achieved_quantity: int = 0
    achievement_percent: float = 0
    product_category: Optional[str] = None
    branch_id: Optional[str] = None
    status: str  # active, achieved, not_achieved, exceeded
    notes: Optional[str] = None
    created_at: str
    updated_at: Optional[str] = None


# ==================== INCENTIVE SLAB MODELS ====================
class IncentiveSlabCreate(BaseModel):
    slab_name: str
    min_achievement: float  # Minimum achievement % for this slab
    max_achievement: float  # Maximum achievement % for this slab
    incentive_type: str  # percentage, fixed, per_unit
    incentive_value: float  # Percentage or fixed amount
    is_cumulative: bool = False  # If true, adds to previous slabs
    applies_to: str = "all"  # all, sales, support, manager
    is_active: bool = True


class IncentiveSlab(BaseModel):
    id: str
    slab_name: str
    min_achievement: float
    max_achievement: float
    incentive_type: str
    incentive_value: float
    is_cumulative: bool
    applies_to: str
    is_active: bool
    created_at: str


# ==================== INCENTIVE PAYOUT MODELS ====================
class IncentivePayout(BaseModel):
    id: str
    employee_id: str
    employee_name: Optional[str] = None
    period: str
    target_id: str
    target_amount: float
    achieved_amount: float
    achievement_percent: float
    slab_applied: str
    calculated_incentive: float
    bonus_amount: float = 0  # Extra bonus for exceeding target
    total_payout: float
    status: str  # calculated, approved, paid
    approved_by: Optional[str] = None
    approved_at: Optional[str] = None
    paid_at: Optional[str] = None
    payroll_id: Optional[str] = None  # Linked payroll if paid through payroll
    created_at: str


# ==================== DEFAULT INCENTIVE SLABS ====================
DEFAULT_SLABS = [
    {'slab_name': 'Below Target', 'min_achievement': 0, 'max_achievement': 80, 'incentive_type': 'percentage', 'incentive_value': 0},
    {'slab_name': '80-100% Achievement', 'min_achievement': 80, 'max_achievement': 100, 'incentive_type': 'percentage', 'incentive_value': 1.0},
    {'slab_name': '100-120% Achievement', 'min_achievement': 100, 'max_achievement': 120, 'incentive_type': 'percentage', 'incentive_value': 2.0},
    {'slab_name': '120-150% Achievement', 'min_achievement': 120, 'max_achievement': 150, 'incentive_type': 'percentage', 'incentive_value': 3.0},
    {'slab_name': 'Super Achiever (150%+)', 'min_achievement': 150, 'max_achievement': 999, 'incentive_type': 'percentage', 'incentive_value': 5.0},
]


# ==================== INCENTIVE SLAB ENDPOINTS ====================
@router.post("/slabs/bootstrap")
async def bootstrap_incentive_slabs(current_user: dict = Depends(get_current_user)):
    """Initialize default incentive slabs"""
    if current_user['role'] != 'admin':
        raise HTTPException(status_code=403, detail="Admin only")
    
    created = 0
    for slab in DEFAULT_SLABS:
        existing = await db.incentive_slabs.find_one({'slab_name': slab['slab_name']}, {'_id': 0})
        if not existing:
            await db.incentive_slabs.insert_one({
                'id': str(uuid.uuid4()),
                **slab,
                'is_cumulative': False,
                'applies_to': 'all',
                'is_active': True,
                'created_at': datetime.now(timezone.utc).isoformat()
            })
            created += 1
    
    return {'message': f'Created {created} incentive slabs', 'total': len(DEFAULT_SLABS)}


@router.post("/slabs", response_model=IncentiveSlab)
async def create_incentive_slab(data: IncentiveSlabCreate, current_user: dict = Depends(get_current_user)):
    """Create a new incentive slab"""
    if current_user['role'] not in ['admin', 'hr']:
        raise HTTPException(status_code=403, detail="Access denied")
    
    slab_id = str(uuid.uuid4())
    slab_doc = {
        'id': slab_id,
        **data.model_dump(),
        'created_at': datetime.now(timezone.utc).isoformat()
    }
    
    await db.incentive_slabs.insert_one(slab_doc)
    return IncentiveSlab(**{k: v for k, v in slab_doc.items() if k != '_id'})


@router.get("/slabs", response_model=List[IncentiveSlab])
async def get_incentive_slabs(current_user: dict = Depends(get_current_user)):
    """Get all incentive slabs"""
    slabs = await db.incentive_slabs.find({'is_active': True}, {'_id': 0}).sort('min_achievement', 1).to_list(50)
    return [IncentiveSlab(**s) for s in slabs]


# ==================== TARGET ENDPOINTS ====================
@router.post("/targets", response_model=SalesTarget)
async def create_sales_target(data: SalesTargetCreate, current_user: dict = Depends(get_current_user)):
    """Create sales target for an employee"""
    if current_user['role'] not in ['admin', 'manager', 'hr']:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Verify employee exists
    employee = await db.employees.find_one({'id': data.employee_id}, {'_id': 0})
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    # Check for existing target
    existing = await db.sales_targets.find_one({
        'employee_id': data.employee_id,
        'period': data.period,
        'target_type': data.target_type
    }, {'_id': 0})
    
    if existing:
        raise HTTPException(status_code=400, detail="Target already exists for this period")
    
    target_id = str(uuid.uuid4())
    target_doc = {
        'id': target_id,
        **data.model_dump(),
        'employee_name': employee.get('name'),
        'achieved_amount': 0,
        'achieved_quantity': 0,
        'achievement_percent': 0,
        'status': 'active',
        'created_at': datetime.now(timezone.utc).isoformat(),
        'updated_at': None
    }
    
    await db.sales_targets.insert_one(target_doc)
    return SalesTarget(**{k: v for k, v in target_doc.items() if k != '_id'})


@router.get("/targets", response_model=List[SalesTarget])
async def get_sales_targets(
    employee_id: Optional[str] = None,
    period: Optional[str] = None,
    status: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Get sales targets"""
    query = {}
    if employee_id:
        query['employee_id'] = employee_id
    if period:
        query['period'] = period
    if status:
        query['status'] = status
    
    targets = await db.sales_targets.find(query, {'_id': 0}).sort('created_at', -1).to_list(500)
    return [SalesTarget(**t) for t in targets]


@router.put("/targets/{target_id}/update-achievement")
async def update_target_achievement(
    target_id: str,
    achieved_amount: float,
    achieved_quantity: int = 0,
    current_user: dict = Depends(get_current_user)
):
    """Update target achievement (called when sales are recorded)"""
    target = await db.sales_targets.find_one({'id': target_id}, {'_id': 0})
    if not target:
        raise HTTPException(status_code=404, detail="Target not found")
    
    achievement_percent = (achieved_amount / target['target_amount'] * 100) if target['target_amount'] > 0 else 0
    
    # Determine status
    if achievement_percent >= 100:
        status = 'exceeded' if achievement_percent > 100 else 'achieved'
    else:
        status = 'active'
    
    await db.sales_targets.update_one(
        {'id': target_id},
        {'$set': {
            'achieved_amount': achieved_amount,
            'achieved_quantity': achieved_quantity,
            'achievement_percent': round(achievement_percent, 2),
            'status': status,
            'updated_at': datetime.now(timezone.utc).isoformat()
        }}
    )
    
    return {
        'message': 'Achievement updated',
        'target_id': target_id,
        'achievement_percent': round(achievement_percent, 2),
        'status': status
    }


# ==================== INCENTIVE CALCULATION ====================
@router.post("/calculate/{target_id}")
async def calculate_incentive(target_id: str, current_user: dict = Depends(get_current_user)):
    """
    Calculate incentive for a target period
    Auto-bonus for exceeding 100% achievement
    """
    target = await db.sales_targets.find_one({'id': target_id}, {'_id': 0})
    if not target:
        raise HTTPException(status_code=404, detail="Target not found")
    
    achievement_percent = target['achievement_percent']
    achieved_amount = target['achieved_amount']
    
    # Find applicable slab
    slabs = await db.incentive_slabs.find(
        {'is_active': True},
        {'_id': 0}
    ).sort('min_achievement', 1).to_list(50)
    
    applicable_slab = None
    for slab in slabs:
        if slab['min_achievement'] <= achievement_percent < slab['max_achievement']:
            applicable_slab = slab
            break
    
    if not applicable_slab:
        # Use highest slab if exceeded all
        applicable_slab = slabs[-1] if slabs else {'slab_name': 'No Slab', 'incentive_type': 'percentage', 'incentive_value': 0}
    
    # Calculate incentive based on slab
    if applicable_slab['incentive_type'] == 'percentage':
        calculated_incentive = achieved_amount * (applicable_slab['incentive_value'] / 100)
    elif applicable_slab['incentive_type'] == 'fixed':
        calculated_incentive = applicable_slab['incentive_value']
    else:  # per_unit
        calculated_incentive = target['achieved_quantity'] * applicable_slab['incentive_value']
    
    # Auto-bonus for exceeding target
    bonus_amount = 0
    if achievement_percent > 100:
        # Bonus: 5% of amount exceeding target
        excess_amount = achieved_amount - target['target_amount']
        bonus_amount = excess_amount * 0.05
    
    total_payout = calculated_incentive + bonus_amount
    
    # Create payout record
    payout_id = str(uuid.uuid4())
    payout_doc = {
        'id': payout_id,
        'employee_id': target['employee_id'],
        'employee_name': target.get('employee_name'),
        'period': target['period'],
        'target_id': target_id,
        'target_amount': target['target_amount'],
        'achieved_amount': achieved_amount,
        'achievement_percent': achievement_percent,
        'slab_applied': applicable_slab['slab_name'],
        'calculated_incentive': round(calculated_incentive, 2),
        'bonus_amount': round(bonus_amount, 2),
        'total_payout': round(total_payout, 2),
        'status': 'calculated',
        'approved_by': None,
        'approved_at': None,
        'paid_at': None,
        'payroll_id': None,
        'created_at': datetime.now(timezone.utc).isoformat()
    }
    
    await db.incentive_payouts.insert_one(payout_doc)
    
    return IncentivePayout(**{k: v for k, v in payout_doc.items() if k != '_id'})


@router.get("/payouts", response_model=List[IncentivePayout])
async def get_incentive_payouts(
    employee_id: Optional[str] = None,
    period: Optional[str] = None,
    status: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Get incentive payouts"""
    query = {}
    if employee_id:
        query['employee_id'] = employee_id
    if period:
        query['period'] = period
    if status:
        query['status'] = status
    
    payouts = await db.incentive_payouts.find(query, {'_id': 0}).sort('created_at', -1).to_list(500)
    return [IncentivePayout(**p) for p in payouts]


@router.put("/payouts/{payout_id}/approve")
async def approve_incentive_payout(payout_id: str, current_user: dict = Depends(get_current_user)):
    """Approve incentive payout"""
    if current_user['role'] not in ['admin', 'director']:
        raise HTTPException(status_code=403, detail="Only admin/director can approve")
    
    await db.incentive_payouts.update_one(
        {'id': payout_id},
        {'$set': {
            'status': 'approved',
            'approved_by': current_user['id'],
            'approved_at': datetime.now(timezone.utc).isoformat()
        }}
    )
    
    return {'message': 'Payout approved', 'payout_id': payout_id}


@router.put("/payouts/{payout_id}/mark-paid")
async def mark_payout_paid(
    payout_id: str,
    payroll_id: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Mark payout as paid"""
    payout = await db.incentive_payouts.find_one({'id': payout_id}, {'_id': 0})
    if not payout:
        raise HTTPException(status_code=404, detail="Payout not found")
    
    if payout['status'] != 'approved':
        raise HTTPException(status_code=400, detail="Payout not approved yet")
    
    await db.incentive_payouts.update_one(
        {'id': payout_id},
        {'$set': {
            'status': 'paid',
            'paid_at': datetime.now(timezone.utc).isoformat(),
            'payroll_id': payroll_id
        }}
    )
    
    return {'message': 'Payout marked as paid', 'payout_id': payout_id}


# ==================== LEADERBOARD ====================
@router.get("/leaderboard")
async def get_sales_leaderboard(
    period: str,
    limit: int = 10,
    current_user: dict = Depends(get_current_user)
):
    """Get sales leaderboard for a period"""
    pipeline = [
        {'$match': {'period': period}},
        {'$sort': {'achievement_percent': -1}},
        {'$limit': limit},
        {'$project': {
            '_id': 0,
            'employee_id': 1,
            'employee_name': 1,
            'target_amount': 1,
            'achieved_amount': 1,
            'achievement_percent': 1,
            'status': 1
        }}
    ]
    
    leaderboard = await db.sales_targets.aggregate(pipeline).to_list(limit)
    
    # Add rank
    for i, entry in enumerate(leaderboard):
        entry['rank'] = i + 1
    
    return leaderboard
