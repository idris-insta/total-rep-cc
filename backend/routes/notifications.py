"""
Notification & Alert System
Features:
- Payment Reminders
- Low Stock Alerts
- Approval Notifications
- Due Date Reminders
- System Notifications
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone, timedelta
import uuid

from server import db, get_current_user

router = APIRouter()

# ==================== MODELS ====================
class NotificationCreate(BaseModel):
    title: str
    message: str
    type: str  # payment, stock, approval, system, reminder
    priority: str = "normal"  # low, normal, high, urgent
    target_user_id: Optional[str] = None  # None = all users
    reference_type: Optional[str] = None  # invoice, po, leave, etc.
    reference_id: Optional[str] = None
    action_url: Optional[str] = None

class Notification(BaseModel):
    id: str
    title: str
    message: str
    type: str
    priority: str
    target_user_id: Optional[str]
    reference_type: Optional[str]
    reference_id: Optional[str]
    action_url: Optional[str]
    is_read: bool = False
    read_at: Optional[str] = None
    created_at: str

# ==================== NOTIFICATION ENDPOINTS ====================
@router.post("/notifications")
async def create_notification(data: NotificationCreate, current_user: dict = Depends(get_current_user)):
    """Create a new notification"""
    now = datetime.now(timezone.utc).isoformat()
    
    notif_doc = {
        "id": str(uuid.uuid4()),
        **data.model_dump(),
        "is_read": False,
        "read_at": None,
        "created_by": current_user["id"],
        "created_at": now
    }
    
    await db.notifications.insert_one(notif_doc)
    return {k: v for k, v in notif_doc.items() if k != '_id'}

@router.get("/notifications")
async def list_notifications(
    unread_only: bool = False,
    type: Optional[str] = None,
    limit: int = 50,
    current_user: dict = Depends(get_current_user)
):
    """List notifications for current user"""
    query = {
        "$or": [
            {"target_user_id": current_user["id"]},
            {"target_user_id": None}
        ]
    }
    if unread_only:
        query["is_read"] = False
    if type:
        query["type"] = type
    
    notifs = await db.notifications.find(query, {"_id": 0}).sort("created_at", -1).limit(limit).to_list(limit)
    return notifs

@router.put("/notifications/{notif_id}/read")
async def mark_notification_read(notif_id: str, current_user: dict = Depends(get_current_user)):
    """Mark notification as read"""
    await db.notifications.update_one(
        {"id": notif_id},
        {"$set": {"is_read": True, "read_at": datetime.now(timezone.utc).isoformat()}}
    )
    return {"message": "Notification marked as read"}

@router.put("/notifications/read-all")
async def mark_all_read(current_user: dict = Depends(get_current_user)):
    """Mark all notifications as read"""
    await db.notifications.update_many(
        {"$or": [{"target_user_id": current_user["id"]}, {"target_user_id": None}], "is_read": False},
        {"$set": {"is_read": True, "read_at": datetime.now(timezone.utc).isoformat()}}
    )
    return {"message": "All notifications marked as read"}

@router.get("/notifications/count")
async def get_unread_count(current_user: dict = Depends(get_current_user)):
    """Get unread notification count"""
    count = await db.notifications.count_documents({
        "$or": [{"target_user_id": current_user["id"]}, {"target_user_id": None}],
        "is_read": False
    })
    return {"unread_count": count}

# ==================== AUTO-GENERATE ALERTS ====================
@router.post("/alerts/generate")
async def generate_system_alerts(current_user: dict = Depends(get_current_user)):
    """Generate system alerts (payment dues, low stock, etc.)"""
    alerts_created = []
    now = datetime.now(timezone.utc)
    today = now.strftime("%Y-%m-%d")
    
    # 1. Payment Due Reminders (invoices due in 3 days or overdue)
    due_threshold = (now + timedelta(days=3)).strftime("%Y-%m-%d")
    overdue_invoices = await db.invoices.find({
        "status": {"$in": ["sent", "partial"]},
        "due_date": {"$lte": due_threshold}
    }, {"_id": 0, "id": 1, "invoice_number": 1, "account_name": 1, "due_date": 1, "balance": 1}).to_list(100)
    
    for inv in overdue_invoices:
        is_overdue = inv["due_date"] < today
        existing = await db.notifications.find_one({
            "reference_type": "invoice",
            "reference_id": inv["id"],
            "created_at": {"$gte": (now - timedelta(days=1)).isoformat()}
        })
        if not existing:
            notif = {
                "id": str(uuid.uuid4()),
                "title": "Payment Overdue" if is_overdue else "Payment Due Soon",
                "message": f"Invoice {inv['invoice_number']} for {inv['account_name']} - ₹{inv['balance']:,.0f} {'is overdue' if is_overdue else 'due on ' + inv['due_date']}",
                "type": "payment",
                "priority": "urgent" if is_overdue else "high",
                "target_user_id": None,
                "reference_type": "invoice",
                "reference_id": inv["id"],
                "action_url": f"/accounts/invoices",
                "is_read": False,
                "created_at": now.isoformat()
            }
            await db.notifications.insert_one(notif)
            alerts_created.append(notif["title"])
    
    # 2. Low Stock Alerts
    low_stock_items = await db.items.find({
        "is_active": True,
        "$expr": {"$lte": ["$current_stock", "$reorder_level"]},
        "reorder_level": {"$gt": 0}
    }, {"_id": 0, "id": 1, "item_code": 1, "item_name": 1, "current_stock": 1, "reorder_level": 1}).to_list(50)
    
    for item in low_stock_items:
        existing = await db.notifications.find_one({
            "reference_type": "item",
            "reference_id": item["id"],
            "created_at": {"$gte": (now - timedelta(days=1)).isoformat()}
        })
        if not existing:
            is_critical = item["current_stock"] <= 0
            notif = {
                "id": str(uuid.uuid4()),
                "title": "Out of Stock" if is_critical else "Low Stock Alert",
                "message": f"{item['item_code']} - {item['item_name']}: Stock {item['current_stock']} (Reorder: {item['reorder_level']})",
                "type": "stock",
                "priority": "urgent" if is_critical else "high",
                "target_user_id": None,
                "reference_type": "item",
                "reference_id": item["id"],
                "action_url": "/inventory",
                "is_read": False,
                "created_at": now.isoformat()
            }
            await db.notifications.insert_one(notif)
            alerts_created.append(notif["title"])
    
    # 3. Pending Approvals
    pending_leaves = await db.leave_applications.count_documents({"status": "pending"})
    pending_pos = await db.purchase_orders.count_documents({"status": "draft"})
    
    if pending_leaves > 0:
        existing = await db.notifications.find_one({
            "type": "approval",
            "title": {"$regex": "Leave"},
            "created_at": {"$gte": (now - timedelta(hours=12)).isoformat()}
        })
        if not existing:
            notif = {
                "id": str(uuid.uuid4()),
                "title": "Pending Leave Approvals",
                "message": f"{pending_leaves} leave application(s) awaiting approval",
                "type": "approval",
                "priority": "normal",
                "target_user_id": None,
                "reference_type": "leave",
                "action_url": "/hrms",
                "is_read": False,
                "created_at": now.isoformat()
            }
            await db.notifications.insert_one(notif)
            alerts_created.append(notif["title"])
    
    # 4. Expiring Batches
    expiry_threshold = (now + timedelta(days=30)).isoformat()
    expiring_batches = await db.batches.find({
        "status": "active",
        "expiry_date": {"$lte": expiry_threshold, "$ne": None},
        "current_quantity": {"$gt": 0}
    }, {"_id": 0, "id": 1, "batch_number": 1, "item_name": 1, "expiry_date": 1}).to_list(20)
    
    for batch in expiring_batches:
        existing = await db.notifications.find_one({
            "reference_type": "batch",
            "reference_id": batch["id"],
            "created_at": {"$gte": (now - timedelta(days=7)).isoformat()}
        })
        if not existing:
            notif = {
                "id": str(uuid.uuid4()),
                "title": "Batch Expiring Soon",
                "message": f"Batch {batch['batch_number']} ({batch['item_name']}) expires on {batch['expiry_date'][:10]}",
                "type": "stock",
                "priority": "high",
                "target_user_id": None,
                "reference_type": "batch",
                "reference_id": batch["id"],
                "action_url": "/inventory",
                "is_read": False,
                "created_at": now.isoformat()
            }
            await db.notifications.insert_one(notif)
            alerts_created.append(notif["title"])
    
    return {
        "message": f"Generated {len(alerts_created)} alerts",
        "alerts": alerts_created
    }

# ==================== SCHEDULED REMINDERS ====================
@router.get("/reminders/payment-due")
async def get_payment_due_reminders(days_ahead: int = 7, current_user: dict = Depends(get_current_user)):
    """Get payment due reminders for the next N days"""
    now = datetime.now(timezone.utc)
    threshold = (now + timedelta(days=days_ahead)).strftime("%Y-%m-%d")
    
    invoices = await db.invoices.find({
        "status": {"$in": ["sent", "partial"]},
        "due_date": {"$lte": threshold}
    }, {"_id": 0}).sort("due_date", 1).to_list(100)
    
    overdue = [i for i in invoices if i["due_date"] < now.strftime("%Y-%m-%d")]
    upcoming = [i for i in invoices if i["due_date"] >= now.strftime("%Y-%m-%d")]
    
    total_overdue = sum(i.get("balance", 0) for i in overdue)
    total_upcoming = sum(i.get("balance", 0) for i in upcoming)
    
    return {
        "overdue": {
            "count": len(overdue),
            "total_amount": round(total_overdue, 2),
            "invoices": overdue[:10]
        },
        "upcoming": {
            "count": len(upcoming),
            "total_amount": round(total_upcoming, 2),
            "invoices": upcoming[:10]
        }
    }

# ==================== ACTIVITY LOG ====================
@router.post("/activity-log")
async def log_activity(
    action: str,
    entity_type: str,
    entity_id: str,
    details: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Log user activity"""
    log_doc = {
        "id": str(uuid.uuid4()),
        "user_id": current_user["id"],
        "user_name": current_user.get("name", "Unknown"),
        "action": action,
        "entity_type": entity_type,
        "entity_id": entity_id,
        "details": details,
        "ip_address": None,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.activity_logs.insert_one(log_doc)
    return {k: v for k, v in log_doc.items() if k != '_id'}

@router.get("/activity-log")
async def get_activity_log(
    entity_type: Optional[str] = None,
    user_id: Optional[str] = None,
    limit: int = 100,
    current_user: dict = Depends(get_current_user)
):
    """Get activity log"""
    query = {}
    if entity_type:
        query["entity_type"] = entity_type
    if user_id:
        query["user_id"] = user_id
    
    logs = await db.activity_logs.find(query, {"_id": 0}).sort("created_at", -1).limit(limit).to_list(limit)
    return logs
