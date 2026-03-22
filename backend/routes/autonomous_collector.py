"""
AUTONOMOUS COLLECTOR MODULE - The Revenue Hunter
Inspired by Recordant and AlignBooks

Features:
1. Debtor Segmentation (Good, Moderate, Bad payers)
2. Auto-Block for Bad Payers
3. Smart Payment Reminders
4. Collection Analytics
5. Emergency Business Controls (The "Nuke Button")
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone, timedelta
import uuid
from server import db, get_current_user

router = APIRouter()


# ==================== DEBTOR SEGMENTATION ====================
class DebtorProfile(BaseModel):
    account_id: str
    account_name: str
    segment: str  # GOLD, SILVER, BRONZE, BLOCKED
    total_outstanding: float
    overdue_amount: float
    avg_payment_days: float
    payment_score: int  # 0-100
    last_payment_date: Optional[str]
    invoices_overdue: int
    credit_limit: float
    credit_used_percent: float
    auto_block: bool
    block_reason: Optional[str]


@router.get("/debtors/segmentation")
async def get_debtor_segmentation(current_user: dict = Depends(get_current_user)):
    """
    Segment all debtors based on payment behavior
    - GOLD: Pays within terms, score 80-100
    - SILVER: Occasional delays, score 50-79
    - BRONZE: Frequent delays, score 20-49
    - BLOCKED: Auto-blocked for non-payment, score 0-19
    """
    accounts = await db.accounts.find({"is_active": True}, {"_id": 0}).to_list(1000)
    
    segments = {"GOLD": [], "SILVER": [], "BRONZE": [], "BLOCKED": []}
    summary = {"total_outstanding": 0, "total_overdue": 0, "blocked_count": 0}
    
    for acc in accounts:
        # Calculate payment metrics
        total_outstanding = acc.get("receivable_amount", 0)
        credit_limit = acc.get("credit_limit", 0)
        avg_payment_days = acc.get("avg_payment_days", 0)
        credit_days = acc.get("credit_days", 30)
        
        # Get overdue invoices
        overdue_invoices = await db.invoices.find({
            "account_id": acc["id"],
            "status": {"$in": ["sent", "partial", "overdue"]},
            "due_date": {"$lt": datetime.now(timezone.utc).isoformat()}
        }, {"_id": 0}).to_list(100)
        
        overdue_amount = sum(inv.get("balance_amount", 0) for inv in overdue_invoices)
        invoices_overdue = len(overdue_invoices)
        
        # Calculate payment score
        payment_score = 100
        if avg_payment_days > credit_days:
            delay_days = avg_payment_days - credit_days
            payment_score -= min(50, delay_days)  # Max 50 points deduction for delays
        if invoices_overdue > 0:
            payment_score -= min(30, invoices_overdue * 10)  # 10 points per overdue invoice
        if credit_limit > 0 and total_outstanding > credit_limit:
            payment_score -= 20  # Over credit limit
        
        payment_score = max(0, payment_score)
        
        # Determine segment
        if payment_score >= 80:
            segment = "GOLD"
        elif payment_score >= 50:
            segment = "SILVER"
        elif payment_score >= 20:
            segment = "BRONZE"
        else:
            segment = "BLOCKED"
        
        # Check for auto-block
        auto_block = False
        block_reason = None
        if invoices_overdue >= 3 and overdue_amount > 50000:
            auto_block = True
            block_reason = f"{invoices_overdue} invoices overdue, ₹{overdue_amount:,.0f} outstanding"
        
        profile = DebtorProfile(
            account_id=acc["id"],
            account_name=acc.get("customer_name", "Unknown"),
            segment=segment,
            total_outstanding=total_outstanding,
            overdue_amount=overdue_amount,
            avg_payment_days=avg_payment_days,
            payment_score=payment_score,
            last_payment_date=acc.get("last_payment_date"),
            invoices_overdue=invoices_overdue,
            credit_limit=credit_limit,
            credit_used_percent=(total_outstanding / credit_limit * 100) if credit_limit > 0 else 0,
            auto_block=auto_block,
            block_reason=block_reason
        )
        
        segments[segment].append(profile.model_dump())
        summary["total_outstanding"] += total_outstanding
        summary["total_overdue"] += overdue_amount
        if auto_block:
            summary["blocked_count"] += 1
    
    return {
        "segments": segments,
        "summary": summary,
        "segment_counts": {k: len(v) for k, v in segments.items()}
    }


@router.post("/debtors/{account_id}/block")
async def block_debtor(account_id: str, reason: str = "Manual block", current_user: dict = Depends(get_current_user)):
    """Block a debtor from placing new orders"""
    if current_user.get("role") not in ["admin", "director"]:
        raise HTTPException(status_code=403, detail="Only admin/director can block accounts")
    
    await db.accounts.update_one(
        {"id": account_id},
        {"$set": {
            "is_blocked": True,
            "block_reason": reason,
            "blocked_at": datetime.now(timezone.utc).isoformat(),
            "blocked_by": current_user["id"]
        }}
    )
    
    # Log the action
    await db.audit_trail.insert_one({
        "id": str(uuid.uuid4()),
        "action": "DEBTOR_BLOCKED",
        "entity_type": "account",
        "entity_id": account_id,
        "reason": reason,
        "user_id": current_user["id"],
        "timestamp": datetime.now(timezone.utc).isoformat()
    })
    
    return {"message": "Account blocked successfully", "account_id": account_id}


@router.post("/debtors/{account_id}/unblock")
async def unblock_debtor(account_id: str, current_user: dict = Depends(get_current_user)):
    """Unblock a debtor"""
    if current_user.get("role") not in ["admin", "director"]:
        raise HTTPException(status_code=403, detail="Only admin/director can unblock accounts")
    
    await db.accounts.update_one(
        {"id": account_id},
        {"$set": {"is_blocked": False, "block_reason": None, "blocked_at": None}}
    )
    
    return {"message": "Account unblocked successfully"}


# ==================== SMART REMINDERS ====================
@router.get("/reminders/pending")
async def get_pending_reminders(current_user: dict = Depends(get_current_user)):
    """Get all pending payment reminders to be sent"""
    now = datetime.now(timezone.utc)
    
    # Find invoices due within 3 days
    upcoming_due = await db.invoices.find({
        "status": {"$in": ["sent", "partial"]},
        "due_date": {
            "$gte": now.isoformat(),
            "$lte": (now + timedelta(days=3)).isoformat()
        }
    }, {"_id": 0}).to_list(100)
    
    # Find overdue invoices
    overdue = await db.invoices.find({
        "status": {"$in": ["sent", "partial", "overdue"]},
        "due_date": {"$lt": now.isoformat()}
    }, {"_id": 0}).to_list(100)
    
    reminders = []
    
    for inv in upcoming_due:
        account = await db.accounts.find_one({"id": inv["account_id"]}, {"_id": 0})
        reminders.append({
            "type": "GENTLE_REMINDER",
            "priority": "MEDIUM",
            "invoice_number": inv["invoice_number"],
            "account_name": account.get("customer_name", "Unknown") if account else "Unknown",
            "phone": account.get("phone") if account else None,
            "email": account.get("email") if account else None,
            "amount": inv["balance_amount"],
            "due_date": inv["due_date"],
            "days_until_due": (datetime.fromisoformat(inv["due_date"].replace("Z", "+00:00")) - now).days,
            "message_template": f"Gentle reminder: Invoice #{inv['invoice_number']} for ₹{inv['balance_amount']:,.0f} is due on {inv['due_date'][:10]}. Please arrange payment."
        })
    
    for inv in overdue:
        account = await db.accounts.find_one({"id": inv["account_id"]}, {"_id": 0})
        days_overdue = (now - datetime.fromisoformat(inv["due_date"].replace("Z", "+00:00"))).days
        
        priority = "HIGH" if days_overdue > 15 else "MEDIUM"
        reminder_type = "URGENT_REMINDER" if days_overdue > 30 else "OVERDUE_NOTICE"
        
        reminders.append({
            "type": reminder_type,
            "priority": priority,
            "invoice_number": inv["invoice_number"],
            "account_name": account.get("customer_name", "Unknown") if account else "Unknown",
            "phone": account.get("phone") if account else None,
            "email": account.get("email") if account else None,
            "amount": inv["balance_amount"],
            "due_date": inv["due_date"],
            "days_overdue": days_overdue,
            "message_template": f"OVERDUE: Invoice #{inv['invoice_number']} for ₹{inv['balance_amount']:,.0f} was due {days_overdue} days ago. Please clear immediately to avoid service disruption."
        })
    
    return {
        "reminders": sorted(reminders, key=lambda x: x.get("days_overdue", -x.get("days_until_due", 0)), reverse=True),
        "total_count": len(reminders),
        "urgent_count": len([r for r in reminders if r["priority"] == "HIGH"])
    }


# ==================== EMERGENCY CONTROLS (THE "NUKE BUTTON") ====================
class EmergencyAction(BaseModel):
    action: str  # HALT_PRODUCTION, FREEZE_ORDERS, BLOCK_SHIPPING, LOCKDOWN
    scope: str  # ALL, BRANCH, DEPARTMENT
    branch_id: Optional[str] = None
    reason: str
    duration_hours: Optional[int] = None


@router.post("/emergency/activate")
async def activate_emergency_control(action: EmergencyAction, current_user: dict = Depends(get_current_user)):
    """
    THE NUKE BUTTON - Emergency business controls
    Only Director can activate these
    """
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Only director/admin can activate emergency controls")
    
    emergency_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc)
    
    emergency_doc = {
        "id": emergency_id,
        "action": action.action,
        "scope": action.scope,
        "branch_id": action.branch_id,
        "reason": action.reason,
        "activated_by": current_user["id"],
        "activated_at": now.isoformat(),
        "expires_at": (now + timedelta(hours=action.duration_hours)).isoformat() if action.duration_hours else None,
        "is_active": True
    }
    
    await db.emergency_controls.insert_one(emergency_doc)
    
    # Set system-wide flag
    await db.system_settings.update_one(
        {"key": "emergency_mode"},
        {"$set": {
            "value": True,
            "emergency_id": emergency_id,
            "action": action.action,
            "updated_at": now.isoformat()
        }},
        upsert=True
    )
    
    return {
        "message": f"Emergency control '{action.action}' activated",
        "emergency_id": emergency_id,
        "action": action.action,
        "reason": action.reason,
        "activated_at": now.isoformat()
    }


@router.post("/emergency/deactivate/{emergency_id}")
async def deactivate_emergency_control(emergency_id: str, current_user: dict = Depends(get_current_user)):
    """Deactivate an emergency control"""
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Only director/admin can deactivate emergency controls")
    
    await db.emergency_controls.update_one(
        {"id": emergency_id},
        {"$set": {
            "is_active": False,
            "deactivated_by": current_user["id"],
            "deactivated_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    # Clear system-wide flag
    await db.system_settings.update_one(
        {"key": "emergency_mode"},
        {"$set": {"value": False, "emergency_id": None, "action": None}}
    )
    
    return {"message": "Emergency control deactivated", "emergency_id": emergency_id}


@router.get("/emergency/status")
async def get_emergency_status(current_user: dict = Depends(get_current_user)):
    """Check if any emergency controls are active"""
    active_controls = await db.emergency_controls.find(
        {"is_active": True},
        {"_id": 0}
    ).to_list(10)
    
    return {
        "emergency_active": len(active_controls) > 0,
        "active_controls": active_controls
    }


# ==================== COLLECTION ANALYTICS ====================
@router.get("/analytics/collection")
async def get_collection_analytics(period: str = "month", current_user: dict = Depends(get_current_user)):
    """Get collection analytics and trends"""
    now = datetime.now(timezone.utc)
    
    if period == "week":
        start_date = now - timedelta(days=7)
    elif period == "month":
        start_date = now - timedelta(days=30)
    elif period == "quarter":
        start_date = now - timedelta(days=90)
    else:
        start_date = now - timedelta(days=365)
    
    # Get payments in period
    payments = await db.payments.find({
        "payment_type": "receipt",
        "payment_date": {"$gte": start_date.isoformat()}
    }, {"_id": 0}).to_list(1000)
    
    total_collected = sum(p.get("amount", 0) for p in payments)
    
    # Get invoices raised in period
    invoices = await db.invoices.find({
        "invoice_type": "Sales",
        "invoice_date": {"$gte": start_date.isoformat()}
    }, {"_id": 0}).to_list(1000)
    
    total_invoiced = sum(inv.get("grand_total", 0) for inv in invoices)
    
    # Collection efficiency
    collection_efficiency = (total_collected / total_invoiced * 100) if total_invoiced > 0 else 0
    
    # Average collection days
    collection_days = []
    for payment in payments:
        if payment.get("invoices"):
            for inv_alloc in payment["invoices"]:
                inv = await db.invoices.find_one({"id": inv_alloc.get("invoice_id")}, {"_id": 0})
                if inv:
                    inv_date = datetime.fromisoformat(inv["invoice_date"].replace("Z", "+00:00"))
                    pay_date = datetime.fromisoformat(payment["payment_date"].replace("Z", "+00:00"))
                    days = (pay_date - inv_date).days
                    collection_days.append(days)
    
    avg_collection_days = sum(collection_days) / len(collection_days) if collection_days else 0
    
    # Daily trend
    daily_collections = {}
    for payment in payments:
        date = payment["payment_date"][:10]
        daily_collections[date] = daily_collections.get(date, 0) + payment.get("amount", 0)
    
    return {
        "period": period,
        "total_invoiced": total_invoiced,
        "total_collected": total_collected,
        "collection_efficiency": round(collection_efficiency, 1),
        "avg_collection_days": round(avg_collection_days, 1),
        "pending_collection": total_invoiced - total_collected,
        "daily_trend": [{"date": k, "amount": v} for k, v in sorted(daily_collections.items())],
        "payment_count": len(payments)
    }


# ==================== QUICK ACTIONS ====================
@router.get("/quick-actions")
async def get_quick_actions(current_user: dict = Depends(get_current_user)):
    """Get quick action items for dashboard"""
    now = datetime.now(timezone.utc)
    
    # Overdue invoices count
    overdue_invoices = await db.invoices.count_documents({
        "status": {"$in": ["sent", "partial"]},
        "due_date": {"$lt": now.isoformat()}
    })
    
    # Pending approvals
    pending_approvals = await db.approvals.count_documents({"status": "pending"})
    
    # Low stock items
    low_stock = await db.items.count_documents({
        "stock_quantity": {"$lte": "$reorder_level"}
    })
    
    # Work orders needing attention
    stalled_wos = await db.work_orders.count_documents({
        "status": "in_progress",
        "updated_at": {"$lt": (now - timedelta(hours=24)).isoformat()}
    })
    
    # Late customers (from Buying DNA)
    late_customers = await db.leads.count_documents({
        "status": "converted",
        "last_order_date": {"$lt": (now - timedelta(days=30)).isoformat()}
    })
    
    # Custom fields that need attention
    custom_fields = await db.custom_fields.count_documents({})
    
    actions = [
        {
            "id": "overdue_invoices",
            "label": "Overdue Invoices",
            "count": overdue_invoices,
            "color": "red",
            "link": "/accounts",
            "icon": "DollarSign",
            "priority": "high" if overdue_invoices > 5 else "medium"
        },
        {
            "id": "pending_approvals",
            "label": "Pending Approvals",
            "count": pending_approvals,
            "color": "orange",
            "link": "/approvals",
            "icon": "CheckCircle",
            "priority": "high" if pending_approvals > 0 else "low"
        },
        {
            "id": "low_stock",
            "label": "Low Stock Items",
            "count": low_stock,
            "color": "amber",
            "link": "/advanced-inventory",
            "icon": "Package",
            "priority": "medium"
        },
        {
            "id": "stalled_wos",
            "label": "Stalled Work Orders",
            "count": stalled_wos,
            "color": "purple",
            "link": "/production",
            "icon": "Factory",
            "priority": "high" if stalled_wos > 0 else "low"
        },
        {
            "id": "late_customers",
            "label": "Customers Due for Follow-up",
            "count": late_customers,
            "color": "blue",
            "link": "/crm/leads",
            "icon": "Users",
            "priority": "medium"
        }
    ]
    
    # Filter only actions with count > 0 or important ones
    return {
        "actions": [a for a in actions if a["count"] > 0 or a["priority"] == "high"],
        "total_actions": sum(a["count"] for a in actions)
    }
