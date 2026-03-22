"""
BUYING DNA SALES HUNTER - AI-Powered Purchase Rhythm Tracker
The system tracks the "rhythm" of your distributors. If a distributor usually buys every 15 days 
and hasn't ordered by Day 17, the AI drafts a WhatsApp message for them.
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, timezone, timedelta
import uuid
from server import db, get_current_user

router = APIRouter()


class BuyingPattern(BaseModel):
    account_id: str
    account_name: str
    avg_order_interval_days: float
    last_order_date: Optional[str]
    days_since_last_order: int
    expected_order_date: str
    is_overdue: bool
    overdue_days: int
    total_orders: int
    total_order_value: float
    avg_order_value: float
    suggested_action: str
    whatsapp_draft: Optional[str]
    contact_phone: Optional[str]
    contact_name: Optional[str]


@router.get("/patterns")
async def get_buying_patterns(current_user: dict = Depends(get_current_user)):
    """
    Analyze buying patterns for all accounts
    Returns accounts sorted by urgency (most overdue first)
    """
    accounts = await db.accounts.find({"is_active": True}, {"_id": 0}).to_list(1000)
    patterns = []
    now = datetime.now(timezone.utc)
    
    for account in accounts:
        account_id = account["id"]
        
        # Get all orders/invoices for this account
        invoices = await db.invoices.find({
            "account_id": account_id,
            "invoice_type": "Sales"
        }, {"_id": 0}).sort("invoice_date", -1).to_list(100)
        
        if len(invoices) < 2:
            # Not enough data to calculate pattern
            continue
        
        # Calculate order intervals
        order_dates = [datetime.fromisoformat(inv["invoice_date"].replace("Z", "+00:00")) for inv in invoices]
        intervals = []
        for i in range(len(order_dates) - 1):
            interval = (order_dates[i] - order_dates[i+1]).days
            if interval > 0:
                intervals.append(interval)
        
        if not intervals:
            continue
            
        avg_interval = sum(intervals) / len(intervals)
        last_order_date = order_dates[0]
        days_since_last = (now - last_order_date).days
        expected_order_date = last_order_date + timedelta(days=avg_interval)
        is_overdue = now > expected_order_date
        overdue_days = max(0, (now - expected_order_date).days)
        
        # Calculate order values
        total_value = sum(inv.get("grand_total", 0) for inv in invoices)
        avg_value = total_value / len(invoices) if invoices else 0
        
        # Get primary contact
        contacts = account.get("contacts", [])
        primary_contact = next((c for c in contacts if c.get("is_primary")), contacts[0] if contacts else {})
        contact_phone = primary_contact.get("mobile") or primary_contact.get("phone")
        contact_name = primary_contact.get("name", account.get("customer_name", "Customer"))
        
        # Determine suggested action
        if overdue_days > avg_interval * 0.5:
            suggested_action = "URGENT_FOLLOWUP"
        elif overdue_days > 0:
            suggested_action = "GENTLE_REMINDER"
        elif days_since_last > avg_interval * 0.8:
            suggested_action = "PRE_EMPTIVE_CHECK"
        else:
            suggested_action = "NO_ACTION"
        
        # Generate WhatsApp draft
        whatsapp_draft = None
        if suggested_action != "NO_ACTION":
            company_name = account.get("customer_name", "")
            if suggested_action == "URGENT_FOLLOWUP":
                whatsapp_draft = f"""Hi {contact_name}! 👋

Hope business is going well at {company_name}! 

We noticed it's been {days_since_last} days since your last order. Your usual reorder cycle is around {int(avg_interval)} days.

Is everything alright? Would love to help if you need anything!

🎁 Special: Order this week and get priority dispatch + 2% extra discount!

Reply to confirm your next order. 📦"""
            elif suggested_action == "GENTLE_REMINDER":
                whatsapp_draft = f"""Hi {contact_name}! 🙂

Just checking in from InstaBiz! Your last order was {days_since_last} days ago.

Based on your usual pattern, you might be running low on stock soon. Want me to prepare your regular order?

Let me know if you need any changes to your usual items!"""
            else:
                whatsapp_draft = f"""Hi {contact_name}! 

Quick heads up - based on your ordering pattern, your next restock might be due soon.

Want me to send you a quote for your regular items? Would help you plan ahead! 📋"""
        
        patterns.append(BuyingPattern(
            account_id=account_id,
            account_name=account.get("customer_name", "Unknown"),
            avg_order_interval_days=round(avg_interval, 1),
            last_order_date=last_order_date.isoformat(),
            days_since_last_order=days_since_last,
            expected_order_date=expected_order_date.isoformat(),
            is_overdue=is_overdue,
            overdue_days=overdue_days,
            total_orders=len(invoices),
            total_order_value=total_value,
            avg_order_value=round(avg_value, 2),
            suggested_action=suggested_action,
            whatsapp_draft=whatsapp_draft,
            contact_phone=contact_phone,
            contact_name=contact_name
        ).model_dump())
    
    # Sort by urgency
    patterns.sort(key=lambda x: (-x["overdue_days"], -x["days_since_last_order"]))
    
    # Summary stats
    urgent_count = len([p for p in patterns if p["suggested_action"] == "URGENT_FOLLOWUP"])
    reminder_count = len([p for p in patterns if p["suggested_action"] == "GENTLE_REMINDER"])
    preemptive_count = len([p for p in patterns if p["suggested_action"] == "PRE_EMPTIVE_CHECK"])
    
    return {
        "patterns": patterns,
        "summary": {
            "total_tracked": len(patterns),
            "urgent_followup": urgent_count,
            "gentle_reminder": reminder_count,
            "preemptive_check": preemptive_count,
            "no_action": len(patterns) - urgent_count - reminder_count - preemptive_count
        }
    }


@router.get("/patterns/{account_id}")
async def get_account_buying_pattern(account_id: str, current_user: dict = Depends(get_current_user)):
    """Get detailed buying pattern for a specific account"""
    account = await db.accounts.find_one({"id": account_id}, {"_id": 0})
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    
    invoices = await db.invoices.find({
        "account_id": account_id,
        "invoice_type": "Sales"
    }, {"_id": 0}).sort("invoice_date", -1).to_list(100)
    
    # Build order history
    order_history = []
    for inv in invoices[:20]:
        order_history.append({
            "invoice_number": inv["invoice_number"],
            "date": inv["invoice_date"],
            "amount": inv.get("grand_total", 0),
            "items_count": len(inv.get("items", []))
        })
    
    # Calculate pattern
    if len(invoices) >= 2:
        order_dates = [datetime.fromisoformat(inv["invoice_date"].replace("Z", "+00:00")) for inv in invoices]
        intervals = [(order_dates[i] - order_dates[i+1]).days for i in range(len(order_dates) - 1)]
        avg_interval = sum(intervals) / len(intervals) if intervals else 0
    else:
        avg_interval = 0
    
    # Top products ordered
    product_counts = {}
    for inv in invoices:
        for item in inv.get("items", []):
            name = item.get("item_name", "Unknown")
            product_counts[name] = product_counts.get(name, 0) + item.get("quantity", 1)
    
    top_products = sorted(product_counts.items(), key=lambda x: x[1], reverse=True)[:5]
    
    return {
        "account": {
            "id": account_id,
            "name": account.get("customer_name"),
            "contacts": account.get("contacts", [])
        },
        "pattern": {
            "avg_order_interval_days": round(avg_interval, 1),
            "total_orders": len(invoices),
            "total_value": sum(inv.get("grand_total", 0) for inv in invoices)
        },
        "order_history": order_history,
        "top_products": [{"name": p[0], "quantity": p[1]} for p in top_products]
    }


@router.post("/followup-log")
async def log_followup(
    account_id: str,
    action_type: str,  # whatsapp_sent, call_made, email_sent
    notes: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Log a follow-up action taken based on buying DNA suggestion"""
    log_entry = {
        "id": str(uuid.uuid4()),
        "account_id": account_id,
        "action_type": action_type,
        "notes": notes,
        "performed_by": current_user["id"],
        "performed_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.buying_dna_logs.insert_one(log_entry)
    
    return {"message": "Follow-up logged successfully", "log_id": log_entry["id"]}


@router.get("/dashboard")
async def get_buying_dna_dashboard(current_user: dict = Depends(get_current_user)):
    """Get dashboard summary for Buying DNA"""
    patterns_result = await get_buying_patterns(current_user)
    
    # Get recent follow-up logs
    recent_logs = await db.buying_dna_logs.find(
        {}, {"_id": 0}
    ).sort("performed_at", -1).limit(10).to_list(10)
    
    # Calculate conversion metrics
    total_followups = await db.buying_dna_logs.count_documents({})
    
    return {
        "summary": patterns_result["summary"],
        "top_urgent": patterns_result["patterns"][:5],
        "recent_followups": recent_logs,
        "metrics": {
            "total_followups_logged": total_followups,
            "accounts_tracked": patterns_result["summary"]["total_tracked"]
        }
    }
