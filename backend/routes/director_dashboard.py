"""
Director Command Center Module (The 10th Screen)
Consolidated Pulse View with:
- Global Cash Pulse (AR/AP)
- Production Yield vs Standard
- Sales Velocity KPIs
- Redline Approval Alerts
- Branch-wise Performance
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict
from datetime import datetime, timezone, timedelta
from server import db, get_current_user

router = APIRouter()


# ==================== KPI MODELS ====================
class CashPulse(BaseModel):
    total_receivables: float
    total_payables: float
    net_position: float
    overdue_receivables: float
    overdue_payables: float
    cash_in_hand: float
    bank_balance: float
    receivables_aging: Dict[str, float]  # 0-30, 31-60, 61-90, 90+ days
    payables_aging: Dict[str, float]


class ProductionPulse(BaseModel):
    work_orders_in_progress: int
    total_target_qty: float
    total_completed_qty: float
    completion_percent: float
    avg_scrap_percent: float
    scrap_vs_standard: float  # Actual vs 7% standard
    machines_running: int
    machines_idle: int
    pending_approvals: int  # Redline alerts


class SalesPulse(BaseModel):
    mtd_sales: float  # Month to Date
    mtd_target: float
    mtd_achievement: float
    ytd_sales: float  # Year to Date
    ytd_target: float
    ytd_achievement: float
    avg_order_value: float
    orders_today: int
    top_products: List[dict]
    top_customers: List[dict]


# ==================== COMMAND CENTER ENDPOINTS ====================
@router.get("/cash-pulse")
async def get_cash_pulse(current_user: dict = Depends(get_current_user)):
    """
    Global Cash Pulse - AR/AP Overview
    """
    if current_user['role'] not in ['admin', 'director', 'accountant']:
        raise HTTPException(status_code=403, detail="Access denied")
    
    today = datetime.now(timezone.utc)
    today_str = today.isoformat()[:10]
    
    # Total Receivables (unpaid sales invoices)
    ar_pipeline = [
        {'$match': {'invoice_type': 'Sales', 'status': {'$nin': ['paid', 'cancelled']}}},
        {'$group': {'_id': None, 'total': {'$sum': '$balance_amount'}}}
    ]
    ar_result = await db.invoices.aggregate(ar_pipeline).to_list(1)
    total_ar = ar_result[0]['total'] if ar_result else 0
    
    # Total Payables (unpaid purchase invoices)
    ap_pipeline = [
        {'$match': {'invoice_type': 'Purchase', 'status': {'$nin': ['paid', 'cancelled']}}},
        {'$group': {'_id': None, 'total': {'$sum': '$balance_amount'}}}
    ]
    ap_result = await db.invoices.aggregate(ap_pipeline).to_list(1)
    total_ap = ap_result[0]['total'] if ap_result else 0
    
    # Overdue calculations (past due_date)
    overdue_ar_pipeline = [
        {'$match': {
            'invoice_type': 'Sales',
            'status': {'$nin': ['paid', 'cancelled']},
            'due_date': {'$lt': today_str}
        }},
        {'$group': {'_id': None, 'total': {'$sum': '$balance_amount'}}}
    ]
    overdue_ar_result = await db.invoices.aggregate(overdue_ar_pipeline).to_list(1)
    overdue_ar = overdue_ar_result[0]['total'] if overdue_ar_result else 0
    
    overdue_ap_pipeline = [
        {'$match': {
            'invoice_type': 'Purchase',
            'status': {'$nin': ['paid', 'cancelled']},
            'due_date': {'$lt': today_str}
        }},
        {'$group': {'_id': None, 'total': {'$sum': '$balance_amount'}}}
    ]
    overdue_ap_result = await db.invoices.aggregate(overdue_ap_pipeline).to_list(1)
    overdue_ap = overdue_ap_result[0]['total'] if overdue_ap_result else 0
    
    # Cash/Bank from ledgers
    cash_ledger = await db.ledgers.find_one(
        {'name': {'$regex': 'cash', '$options': 'i'}},
        {'_id': 0}
    )
    cash_balance = cash_ledger.get('current_balance', 0) if cash_ledger else 0
    
    bank_pipeline = [
        {'$match': {'name': {'$regex': 'bank', '$options': 'i'}}},
        {'$group': {'_id': None, 'total': {'$sum': '$current_balance'}}}
    ]
    bank_result = await db.ledgers.aggregate(bank_pipeline).to_list(1)
    bank_balance = bank_result[0]['total'] if bank_result else 0
    
    # Aging analysis (simplified)
    def get_aging_bucket(due_date_str):
        if not due_date_str:
            return '90+'
        try:
            due_date = datetime.fromisoformat(due_date_str.replace('Z', '+00:00'))
            days = (today - due_date).days
            if days <= 30:
                return '0-30'
            elif days <= 60:
                return '31-60'
            elif days <= 90:
                return '61-90'
            else:
                return '90+'
        except:
            return '90+'
    
    # Get detailed invoices for aging
    ar_invoices = await db.invoices.find(
        {'invoice_type': 'Sales', 'status': {'$nin': ['paid', 'cancelled']}},
        {'_id': 0, 'balance_amount': 1, 'due_date': 1}
    ).to_list(1000)
    
    ar_aging = {'0-30': 0, '31-60': 0, '61-90': 0, '90+': 0}
    for inv in ar_invoices:
        bucket = get_aging_bucket(inv.get('due_date'))
        ar_aging[bucket] += inv.get('balance_amount', 0)
    
    ap_invoices = await db.invoices.find(
        {'invoice_type': 'Purchase', 'status': {'$nin': ['paid', 'cancelled']}},
        {'_id': 0, 'balance_amount': 1, 'due_date': 1}
    ).to_list(1000)
    
    ap_aging = {'0-30': 0, '31-60': 0, '61-90': 0, '90+': 0}
    for inv in ap_invoices:
        bucket = get_aging_bucket(inv.get('due_date'))
        ap_aging[bucket] += inv.get('balance_amount', 0)
    
    return {
        'total_receivables': total_ar,
        'total_payables': total_ap,
        'net_position': total_ar - total_ap,
        'overdue_receivables': overdue_ar,
        'overdue_payables': overdue_ap,
        'cash_in_hand': cash_balance,
        'bank_balance': bank_balance,
        'receivables_aging': ar_aging,
        'payables_aging': ap_aging,
        'as_of': today_str
    }


@router.get("/production-pulse")
async def get_production_pulse(current_user: dict = Depends(get_current_user)):
    """
    Production Yield vs Standard
    """
    if current_user['role'] not in ['admin', 'director', 'production_manager']:
        raise HTTPException(status_code=403, detail="Access denied")
    
    SCRAP_STANDARD = 7.0  # 7% is the benchmark
    
    # Work orders in progress
    wo_in_progress = await db.work_orders.count_documents({'status': 'in_progress'})
    
    # Totals from active work orders
    wo_pipeline = [
        {'$match': {'status': {'$in': ['planned', 'in_progress']}}},
        {'$group': {
            '_id': None,
            'total_target': {'$sum': '$quantity_to_make'},
            'total_completed': {'$sum': '$quantity_made'}
        }}
    ]
    wo_result = await db.work_orders.aggregate(wo_pipeline).to_list(1)
    
    total_target = wo_result[0]['total_target'] if wo_result else 0
    total_completed = wo_result[0]['total_completed'] if wo_result else 0
    completion_percent = (total_completed / total_target * 100) if total_target > 0 else 0
    
    # Average scrap from coating batches (last 30 days)
    thirty_days_ago = (datetime.now(timezone.utc) - timedelta(days=30)).isoformat()
    scrap_pipeline = [
        {'$match': {'created_at': {'$gte': thirty_days_ago}, 'status': 'completed'}},
        {'$group': {'_id': None, 'avg_scrap': {'$avg': '$scrap_percent'}}}
    ]
    scrap_result = await db.coating_batches.aggregate(scrap_pipeline).to_list(1)
    avg_scrap = scrap_result[0]['avg_scrap'] if scrap_result else 0
    
    # Machines status
    total_machines = await db.machines.count_documents({'status': {'$ne': 'inactive'}})
    machines_running = await db.machines.count_documents({'status': 'running'})
    machines_idle = total_machines - machines_running
    
    # Pending approvals (Redline alerts)
    pending_approvals = await db.approval_requests.count_documents({
        'module': 'Production',
        'status': 'pending'
    })
    
    return {
        'work_orders_in_progress': wo_in_progress,
        'total_target_qty': total_target,
        'total_completed_qty': total_completed,
        'completion_percent': round(completion_percent, 1),
        'avg_scrap_percent': round(avg_scrap, 2),
        'scrap_vs_standard': round(avg_scrap - SCRAP_STANDARD, 2),
        'scrap_standard': SCRAP_STANDARD,
        'machines_running': machines_running,
        'machines_idle': machines_idle,
        'pending_approvals': pending_approvals,
        'scrap_alert': avg_scrap > SCRAP_STANDARD
    }


@router.get("/sales-pulse")
async def get_sales_pulse(current_user: dict = Depends(get_current_user)):
    """
    Sales Velocity KPIs
    """
    if current_user['role'] not in ['admin', 'director', 'sales_manager']:
        raise HTTPException(status_code=403, detail="Access denied")
    
    today = datetime.now(timezone.utc)
    month_start = today.replace(day=1).isoformat()[:10]
    
    # Determine FY start (April)
    if today.month >= 4:
        fy_start = today.replace(month=4, day=1).isoformat()[:10]
    else:
        fy_start = today.replace(year=today.year - 1, month=4, day=1).isoformat()[:10]
    
    today_str = today.isoformat()[:10]
    
    # MTD Sales
    mtd_pipeline = [
        {'$match': {
            'invoice_type': 'Sales',
            'status': {'$nin': ['cancelled', 'draft']},
            'invoice_date': {'$gte': month_start, '$lte': today_str}
        }},
        {'$group': {'_id': None, 'total': {'$sum': '$grand_total'}, 'count': {'$sum': 1}}}
    ]
    mtd_result = await db.invoices.aggregate(mtd_pipeline).to_list(1)
    mtd_sales = mtd_result[0]['total'] if mtd_result else 0
    mtd_count = mtd_result[0]['count'] if mtd_result else 0
    
    # YTD Sales
    ytd_pipeline = [
        {'$match': {
            'invoice_type': 'Sales',
            'status': {'$nin': ['cancelled', 'draft']},
            'invoice_date': {'$gte': fy_start, '$lte': today_str}
        }},
        {'$group': {'_id': None, 'total': {'$sum': '$grand_total'}}}
    ]
    ytd_result = await db.invoices.aggregate(ytd_pipeline).to_list(1)
    ytd_sales = ytd_result[0]['total'] if ytd_result else 0
    
    # Today's orders
    orders_today = await db.invoices.count_documents({
        'invoice_type': 'Sales',
        'invoice_date': today_str
    })
    
    # Average order value
    avg_order_value = mtd_sales / mtd_count if mtd_count > 0 else 0
    
    # Top products (by revenue, this month)
    top_products_pipeline = [
        {'$match': {
            'invoice_type': 'Sales',
            'invoice_date': {'$gte': month_start}
        }},
        {'$unwind': '$items'},
        {'$group': {
            '_id': '$items.description',
            'total_revenue': {'$sum': {'$multiply': ['$items.quantity', '$items.unit_price']}},
            'total_qty': {'$sum': '$items.quantity'}
        }},
        {'$sort': {'total_revenue': -1}},
        {'$limit': 5}
    ]
    top_products = await db.invoices.aggregate(top_products_pipeline).to_list(5)
    
    # Top customers (by revenue, this month)
    top_customers_pipeline = [
        {'$match': {
            'invoice_type': 'Sales',
            'invoice_date': {'$gte': month_start}
        }},
        {'$group': {
            '_id': '$account_id',
            'account_name': {'$first': '$account_name'},
            'total_revenue': {'$sum': '$grand_total'},
            'order_count': {'$sum': 1}
        }},
        {'$sort': {'total_revenue': -1}},
        {'$limit': 5}
    ]
    top_customers = await db.invoices.aggregate(top_customers_pipeline).to_list(5)
    
    # Get MTD target (sum of all sales targets for current month)
    current_month = today.strftime('%Y-%m')
    target_pipeline = [
        {'$match': {'period': current_month, 'target_type': 'monthly'}},
        {'$group': {'_id': None, 'total_target': {'$sum': '$target_amount'}}}
    ]
    target_result = await db.sales_targets.aggregate(target_pipeline).to_list(1)
    mtd_target = target_result[0]['total_target'] if target_result else mtd_sales * 1.2  # Default to 120% of actual
    
    # YTD target (estimate based on monthly)
    months_in_fy = ((today.month - 4) % 12) + 1
    ytd_target = mtd_target * months_in_fy
    
    return {
        'mtd_sales': round(mtd_sales, 2),
        'mtd_target': round(mtd_target, 2),
        'mtd_achievement': round((mtd_sales / mtd_target * 100) if mtd_target > 0 else 0, 1),
        'ytd_sales': round(ytd_sales, 2),
        'ytd_target': round(ytd_target, 2),
        'ytd_achievement': round((ytd_sales / ytd_target * 100) if ytd_target > 0 else 0, 1),
        'avg_order_value': round(avg_order_value, 2),
        'orders_today': orders_today,
        'orders_this_month': mtd_count,
        'top_products': top_products,
        'top_customers': top_customers
    }


@router.get("/alerts")
async def get_director_alerts(current_user: dict = Depends(get_current_user)):
    """
    Get all pending alerts requiring director attention
    """
    if current_user['role'] not in ['admin', 'director']:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Pending approvals
    pending_approvals = await db.approval_requests.find(
        {'status': 'pending'},
        {'_id': 0}
    ).sort('requested_at', -1).to_list(50)
    
    # Overdue invoices (AR > 30 days)
    thirty_days_ago = (datetime.now(timezone.utc) - timedelta(days=30)).isoformat()[:10]
    overdue_invoices = await db.invoices.find(
        {
            'invoice_type': 'Sales',
            'status': {'$nin': ['paid', 'cancelled']},
            'due_date': {'$lt': thirty_days_ago}
        },
        {'_id': 0, 'invoice_number': 1, 'account_name': 1, 'balance_amount': 1, 'due_date': 1}
    ).sort('due_date', 1).to_list(20)
    
    # Low stock items
    low_stock_items = await db.items.find(
        {'$expr': {'$lt': ['$current_stock', '$reorder_level']}},
        {'_id': 0, 'item_code': 1, 'item_name': 1, 'current_stock': 1, 'reorder_level': 1}
    ).to_list(20)
    
    # Expiring documents
    thirty_days_later = (datetime.now(timezone.utc) + timedelta(days=30)).isoformat()[:10]
    today_str = datetime.now(timezone.utc).isoformat()[:10]
    expiring_docs = await db.employee_documents.find(
        {'expiry_date': {'$gte': today_str, '$lte': thirty_days_later}},
        {'_id': 0}
    ).to_list(20)
    
    return {
        'pending_approvals': {
            'count': len(pending_approvals),
            'items': pending_approvals
        },
        'overdue_invoices': {
            'count': len(overdue_invoices),
            'items': overdue_invoices
        },
        'low_stock_alerts': {
            'count': len(low_stock_items),
            'items': low_stock_items
        },
        'expiring_documents': {
            'count': len(expiring_docs),
            'items': expiring_docs
        },
        'generated_at': datetime.now(timezone.utc).isoformat()
    }


@router.get("/summary")
async def get_director_summary(current_user: dict = Depends(get_current_user)):
    """
    Complete Director Command Center Summary
    """
    if current_user['role'] not in ['admin', 'director']:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Get all pulses
    cash_pulse = await get_cash_pulse(current_user)
    production_pulse = await get_production_pulse(current_user)
    sales_pulse = await get_sales_pulse(current_user)
    alerts = await get_director_alerts(current_user)
    
    # Branch-wise summary
    branches = await db.branches.find({'is_active': True}, {'_id': 0}).to_list(20)
    
    branch_performance = []
    for branch in branches:
        branch_sales = await db.invoices.aggregate([
            {'$match': {'branch_id': branch['id'], 'invoice_type': 'Sales'}},
            {'$group': {'_id': None, 'total': {'$sum': '$grand_total'}}}
        ]).to_list(1)
        
        branch_performance.append({
            'branch_code': branch['branch_code'],
            'branch_name': branch['branch_name'],
            'total_sales': branch_sales[0]['total'] if branch_sales else 0
        })
    
    return {
        'cash_pulse': cash_pulse,
        'production_pulse': production_pulse,
        'sales_pulse': sales_pulse,
        'alerts': alerts,
        'branch_performance': branch_performance,
        'generated_at': datetime.now(timezone.utc).isoformat()
    }
