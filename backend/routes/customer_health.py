"""
CUSTOMER HEALTH SCORE MODULE
Combines Buying DNA patterns with Debtor Segmentation to provide a unified customer health view
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, timezone, timedelta
from server import db, get_current_user

router = APIRouter()


class CustomerHealthScore(BaseModel):
    account_id: str
    account_name: str
    health_score: int  # 0-100
    health_status: str  # CRITICAL, AT_RISK, HEALTHY, EXCELLENT
    
    # Buying DNA metrics
    buying_status: str  # URGENT_FOLLOWUP, GENTLE_REMINDER, PRE_EMPTIVE_CHECK, NO_ACTION, NO_DATA
    days_since_last_order: Optional[int]
    avg_order_interval: Optional[float]
    is_order_overdue: bool
    
    # Debtor metrics
    debtor_segment: str  # GOLD, SILVER, BRONZE, BLOCKED, NEW
    payment_score: int
    total_outstanding: float
    overdue_amount: float
    invoices_overdue: int
    
    # Combined insights
    risk_factors: List[str]
    recommended_actions: List[str]
    priority_rank: int
    
    # Contact info
    contact_name: Optional[str]
    contact_phone: Optional[str]


@router.get("/scores")
async def get_customer_health_scores(
    limit: int = 50,
    filter_status: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """
    Get unified customer health scores combining buying patterns and payment behavior
    """
    accounts = await db.accounts.find({"is_active": True}, {"_id": 0}).to_list(500)
    now = datetime.now(timezone.utc)
    
    health_scores = []
    
    for account in accounts:
        account_id = account["id"]
        
        # ========== BUYING DNA ANALYSIS ==========
        invoices = await db.invoices.find({
            "account_id": account_id,
            "invoice_type": "Sales"
        }, {"_id": 0}).sort("invoice_date", -1).to_list(50)
        
        buying_status = "NO_DATA"
        days_since_last_order = None
        avg_order_interval = None
        is_order_overdue = False
        buying_score = 50  # Neutral if no data
        
        if len(invoices) >= 2:
            order_dates = [datetime.fromisoformat(inv["invoice_date"].replace("Z", "+00:00")) for inv in invoices]
            intervals = [(order_dates[i] - order_dates[i+1]).days for i in range(len(order_dates) - 1) if (order_dates[i] - order_dates[i+1]).days > 0]
            
            if intervals:
                avg_order_interval = sum(intervals) / len(intervals)
                last_order_date = order_dates[0]
                days_since_last_order = (now - last_order_date).days
                expected_order_date = last_order_date + timedelta(days=avg_order_interval)
                is_order_overdue = now > expected_order_date
                overdue_days = max(0, (now - expected_order_date).days)
                
                # Calculate buying score
                if overdue_days > avg_order_interval * 0.5:
                    buying_status = "URGENT_FOLLOWUP"
                    buying_score = 20
                elif overdue_days > 0:
                    buying_status = "GENTLE_REMINDER"
                    buying_score = 50
                elif days_since_last_order > avg_order_interval * 0.8:
                    buying_status = "PRE_EMPTIVE_CHECK"
                    buying_score = 70
                else:
                    buying_status = "NO_ACTION"
                    buying_score = 100
        elif len(invoices) == 1:
            order_date = datetime.fromisoformat(invoices[0]["invoice_date"].replace("Z", "+00:00"))
            days_since_last_order = (now - order_date).days
            buying_score = 60 if days_since_last_order < 30 else 40
        
        # ========== DEBTOR SEGMENTATION ANALYSIS ==========
        total_outstanding = account.get("receivable_amount", 0)
        credit_limit = account.get("credit_limit", 0)
        credit_days = account.get("credit_days", 30)
        avg_payment_days = account.get("avg_payment_days", 0)
        
        # Get overdue invoices
        overdue_invoices = await db.invoices.find({
            "account_id": account_id,
            "status": {"$in": ["sent", "partial", "overdue"]},
            "due_date": {"$lt": now.isoformat()}
        }, {"_id": 0}).to_list(50)
        
        overdue_amount = sum(inv.get("balance_amount", 0) for inv in overdue_invoices)
        invoices_overdue = len(overdue_invoices)
        
        # Calculate payment score
        payment_score = 100
        if avg_payment_days > credit_days:
            delay_days = avg_payment_days - credit_days
            payment_score -= min(50, delay_days)
        if invoices_overdue > 0:
            payment_score -= min(30, invoices_overdue * 10)
        if credit_limit > 0 and total_outstanding > credit_limit:
            payment_score -= 20
        payment_score = max(0, payment_score)
        
        # Determine debtor segment
        if payment_score >= 80:
            debtor_segment = "GOLD"
        elif payment_score >= 50:
            debtor_segment = "SILVER"
        elif payment_score >= 20:
            debtor_segment = "BRONZE"
        else:
            debtor_segment = "BLOCKED"
        
        if len(invoices) == 0:
            debtor_segment = "NEW"
        
        # ========== COMBINED HEALTH SCORE ==========
        # Weight: 40% buying behavior, 60% payment behavior
        health_score = int(buying_score * 0.4 + payment_score * 0.6)
        
        # Determine health status
        if health_score >= 80:
            health_status = "EXCELLENT"
        elif health_score >= 60:
            health_status = "HEALTHY"
        elif health_score >= 40:
            health_status = "AT_RISK"
        else:
            health_status = "CRITICAL"
        
        # ========== RISK FACTORS & RECOMMENDATIONS ==========
        risk_factors = []
        recommended_actions = []
        
        if is_order_overdue:
            risk_factors.append(f"Order overdue by {max(0, days_since_last_order - int(avg_order_interval or 30))} days")
            recommended_actions.append("Send follow-up WhatsApp/call")
        
        if invoices_overdue > 0:
            risk_factors.append(f"{invoices_overdue} overdue invoice(s) worth ₹{overdue_amount:,.0f}")
            recommended_actions.append("Initiate payment collection")
        
        if credit_limit > 0 and total_outstanding > credit_limit * 0.9:
            risk_factors.append(f"Near credit limit ({int(total_outstanding/credit_limit*100)}% used)")
            recommended_actions.append("Review credit limit")
        
        if avg_payment_days > credit_days:
            risk_factors.append(f"Pays {int(avg_payment_days - credit_days)} days late on average")
        
        if buying_status == "NO_DATA" and len(invoices) == 0:
            risk_factors.append("No purchase history")
            recommended_actions.append("Schedule introductory call")
        
        if not risk_factors:
            risk_factors.append("No concerns")
        
        if not recommended_actions:
            recommended_actions.append("Maintain relationship")
        
        # Get contact info
        contacts = account.get("contacts", [])
        primary_contact = next((c for c in contacts if c.get("is_primary")), contacts[0] if contacts else {})
        
        health_scores.append(CustomerHealthScore(
            account_id=account_id,
            account_name=account.get("customer_name", "Unknown"),
            health_score=health_score,
            health_status=health_status,
            buying_status=buying_status,
            days_since_last_order=days_since_last_order,
            avg_order_interval=round(avg_order_interval, 1) if avg_order_interval else None,
            is_order_overdue=is_order_overdue,
            debtor_segment=debtor_segment,
            payment_score=payment_score,
            total_outstanding=total_outstanding,
            overdue_amount=overdue_amount,
            invoices_overdue=invoices_overdue,
            risk_factors=risk_factors,
            recommended_actions=recommended_actions,
            priority_rank=0,  # Will be set after sorting
            contact_name=primary_contact.get("name"),
            contact_phone=primary_contact.get("mobile") or primary_contact.get("phone")
        ).model_dump())
    
    # Sort by health score (worst first) and assign priority rank
    health_scores.sort(key=lambda x: x["health_score"])
    for i, score in enumerate(health_scores):
        score["priority_rank"] = i + 1
    
    # Apply filter
    if filter_status:
        health_scores = [s for s in health_scores if s["health_status"] == filter_status]
    
    # Calculate summary
    summary = {
        "total_customers": len(health_scores),
        "critical": len([s for s in health_scores if s["health_status"] == "CRITICAL"]),
        "at_risk": len([s for s in health_scores if s["health_status"] == "AT_RISK"]),
        "healthy": len([s for s in health_scores if s["health_status"] == "HEALTHY"]),
        "excellent": len([s for s in health_scores if s["health_status"] == "EXCELLENT"]),
        "avg_health_score": round(sum(s["health_score"] for s in health_scores) / len(health_scores), 1) if health_scores else 0,
        "total_at_risk_outstanding": sum(s["total_outstanding"] for s in health_scores if s["health_status"] in ["CRITICAL", "AT_RISK"])
    }
    
    return {
        "scores": health_scores[:limit],
        "summary": summary
    }


@router.get("/scores/{account_id}")
async def get_single_customer_health(account_id: str, current_user: dict = Depends(get_current_user)):
    """Get detailed health score for a single customer"""
    result = await get_customer_health_scores(limit=500, current_user=current_user)
    
    for score in result["scores"]:
        if score["account_id"] == account_id:
            return score
    
    raise HTTPException(status_code=404, detail="Customer not found")


@router.get("/widget")
async def get_health_widget_data(current_user: dict = Depends(get_current_user)):
    """Get summarized data for CRM dashboard widget"""
    result = await get_customer_health_scores(limit=100, current_user=current_user)
    
    # Get top 5 critical/at-risk customers
    attention_needed = [s for s in result["scores"] if s["health_status"] in ["CRITICAL", "AT_RISK"]][:5]
    
    return {
        "summary": result["summary"],
        "attention_needed": attention_needed,
        "health_distribution": {
            "CRITICAL": result["summary"]["critical"],
            "AT_RISK": result["summary"]["at_risk"],
            "HEALTHY": result["summary"]["healthy"],
            "EXCELLENT": result["summary"]["excellent"]
        }
    }
