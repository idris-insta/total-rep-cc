"""
AI-Powered Business Intelligence Module
Features:
1. Natural Language Queries - Ask questions about your data
2. AI-Generated Insights - Auto-analyze trends and anomalies
3. Predictive Analytics - Forecast sales, inventory, cash flow
4. Smart Alerts - AI detects unusual patterns
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone, timedelta
import uuid
import os
import json
from dotenv import load_dotenv

load_dotenv()

from server import db, get_current_user
from emergentintegrations.llm.chat import LlmChat, UserMessage

router = APIRouter()

EMERGENT_LLM_KEY = os.environ.get('EMERGENT_LLM_KEY')

# ==================== MODELS ====================
class NLQueryRequest(BaseModel):
    query: str
    context: Optional[str] = None

class InsightRequest(BaseModel):
    focus_area: str = "all"  # sales, inventory, production, finance, all
    time_period: str = "month"  # week, month, quarter, year

class PredictionRequest(BaseModel):
    metric: str  # sales, inventory, cash_flow
    horizon_days: int = 30

class AlertCheckRequest(BaseModel):
    check_type: str = "all"  # sales, inventory, production, payments, all


# ==================== HELPER FUNCTIONS ====================
async def get_business_context():
    """Gather current business data for AI context"""
    today = datetime.now(timezone.utc)
    month_start = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    
    # Sales data
    sales_invoices = await db.invoices.find({
        "invoice_type": "Sales",
        "status": {"$ne": "cancelled"}
    }, {"_id": 0}).to_list(500)
    
    mtd_sales = sum(inv.get("total_amount", 0) for inv in sales_invoices 
                   if inv.get("invoice_date", "").startswith(month_start.strftime("%Y-%m")))
    total_sales = sum(inv.get("total_amount", 0) for inv in sales_invoices)
    
    # Customer data
    customers = await db.customers.count_documents({})
    
    # Inventory data
    items = await db.items.find({}, {"_id": 0, "item_name": 1, "current_stock": 1, "reorder_level": 1}).to_list(500)
    low_stock_items = [i for i in items if (i.get("current_stock", 0) or 0) < (i.get("reorder_level", 10) or 10)]
    
    # Production data
    work_orders = await db.work_orders.find({"status": "in_progress"}, {"_id": 0}).to_list(100)
    production_entries = await db.production_entries.find({}, {"_id": 0}).to_list(1000)
    total_produced = sum(e.get("quantity_produced", 0) for e in production_entries)
    total_wastage = sum(e.get("wastage", 0) for e in production_entries)
    avg_scrap = (total_wastage / (total_produced + total_wastage) * 100) if (total_produced + total_wastage) > 0 else 0
    
    # AR/AP
    ar = sum(inv.get("balance_amount", 0) for inv in sales_invoices if inv.get("status") not in ["paid", "cancelled"])
    
    purchase_invoices = await db.invoices.find({
        "invoice_type": "Purchase",
        "status": {"$nin": ["paid", "cancelled"]}
    }, {"_id": 0}).to_list(500)
    ap = sum(inv.get("balance_amount", 0) for inv in purchase_invoices)
    
    # Top products
    product_sales = {}
    for inv in sales_invoices:
        for item in inv.get("items", []):
            name = item.get("item_name", "Unknown")
            if name not in product_sales:
                product_sales[name] = 0
            product_sales[name] += item.get("amount", 0)
    top_products = sorted(product_sales.items(), key=lambda x: x[1], reverse=True)[:5]
    
    return {
        "date": today.strftime("%Y-%m-%d"),
        "mtd_sales": mtd_sales,
        "total_sales_all_time": total_sales,
        "total_customers": customers,
        "total_invoices": len(sales_invoices),
        "accounts_receivable": ar,
        "accounts_payable": ap,
        "net_position": ar - ap,
        "active_work_orders": len(work_orders),
        "avg_scrap_percent": round(avg_scrap, 2),
        "low_stock_items_count": len(low_stock_items),
        "low_stock_items": [i.get("item_name") for i in low_stock_items[:5]],
        "top_products": [{"name": p[0], "revenue": p[1]} for p in top_products],
        "total_items_in_inventory": len(items)
    }


async def get_llm_chat(session_id: str, system_message: str):
    """Initialize LLM chat with Gemini"""
    chat = LlmChat(
        api_key=EMERGENT_LLM_KEY,
        session_id=session_id,
        system_message=system_message
    ).with_model("gemini", "gemini-3-flash-preview")
    return chat


# ==================== 1. NATURAL LANGUAGE QUERIES ====================
@router.post("/nl-query")
async def natural_language_query(data: NLQueryRequest, current_user: dict = Depends(get_current_user)):
    """
    Ask questions about your business data in natural language
    Examples: "What were our top 5 products last month?", "How much do we owe suppliers?"
    """
    if not EMERGENT_LLM_KEY:
        raise HTTPException(status_code=500, detail="AI service not configured")
    
    # Get business context
    context = await get_business_context()
    
    system_message = """You are an AI business analyst for AdhesiveFlow ERP, an industrial ERP system for the adhesive tapes industry.
You have access to real-time business data and should provide accurate, data-driven answers.
Keep responses concise and actionable. Use bullet points for lists.
If asked about something not in the data, say so clearly.
Format currency in Indian Rupees (₹) with proper formatting.
Current business context will be provided with each query."""

    user_prompt = f"""CURRENT BUSINESS DATA:
{json.dumps(context, indent=2)}

USER QUESTION: {data.query}

Please answer based on the data provided. If the exact data isn't available, provide relevant insights from what is available."""

    try:
        chat = await get_llm_chat(
            session_id=f"nl-query-{current_user.get('id', 'default')}-{datetime.now().timestamp()}",
            system_message=system_message
        )
        
        response = await chat.send_message(UserMessage(text=user_prompt))
        
        # Log the query
        await db.ai_queries.insert_one({
            "id": str(uuid.uuid4()),
            "user_id": current_user.get("id"),
            "query": data.query,
            "response": response,
            "context_snapshot": context,
            "created_at": datetime.now(timezone.utc).isoformat()
        })
        
        return {
            "query": data.query,
            "answer": response,
            "data_snapshot": {
                "mtd_sales": context["mtd_sales"],
                "ar": context["accounts_receivable"],
                "ap": context["accounts_payable"]
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI query failed: {str(e)}")


# ==================== 2. AI-GENERATED INSIGHTS ====================
@router.post("/generate-insights")
async def generate_ai_insights(data: InsightRequest, current_user: dict = Depends(get_current_user)):
    """
    Generate AI-powered insights about business performance
    Focus areas: sales, inventory, production, finance, all
    """
    if not EMERGENT_LLM_KEY:
        raise HTTPException(status_code=500, detail="AI service not configured")
    
    context = await get_business_context()
    
    system_message = """You are a senior business analyst AI for AdhesiveFlow ERP (adhesive tapes industry).
Generate actionable business insights based on the data provided.
Structure your response as:
1. KEY FINDINGS (3-4 bullet points)
2. OPPORTUNITIES (2-3 actionable items)
3. RISKS/CONCERNS (2-3 items to watch)
4. RECOMMENDED ACTIONS (prioritized list)

Be specific with numbers and percentages. Focus on actionable insights, not generic advice."""

    focus_prompts = {
        "sales": "Focus on sales performance, customer trends, top products, and revenue opportunities.",
        "inventory": "Focus on stock levels, reorder needs, slow-moving items, and inventory optimization.",
        "production": "Focus on production efficiency, scrap rates, work order status, and capacity utilization.",
        "finance": "Focus on cash position, AR/AP, payment trends, and financial health.",
        "all": "Provide a comprehensive overview of all business areas."
    }

    user_prompt = f"""BUSINESS DATA SNAPSHOT:
{json.dumps(context, indent=2)}

ANALYSIS FOCUS: {data.focus_area.upper()}
TIME PERIOD: {data.time_period}

{focus_prompts.get(data.focus_area, focus_prompts['all'])}

Generate detailed, actionable insights based on this data."""

    try:
        chat = await get_llm_chat(
            session_id=f"insights-{current_user.get('id', 'default')}-{datetime.now().timestamp()}",
            system_message=system_message
        )
        
        response = await chat.send_message(UserMessage(text=user_prompt))
        
        return {
            "focus_area": data.focus_area,
            "time_period": data.time_period,
            "insights": response,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "data_basis": {
                "total_sales": context["total_sales_all_time"],
                "mtd_sales": context["mtd_sales"],
                "customers": context["total_customers"],
                "low_stock_count": context["low_stock_items_count"],
                "scrap_rate": context["avg_scrap_percent"]
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Insight generation failed: {str(e)}")


# ==================== 3. PREDICTIVE ANALYTICS ====================
@router.post("/predict")
async def predictive_analytics(data: PredictionRequest, current_user: dict = Depends(get_current_user)):
    """
    AI-powered predictions for sales, inventory needs, cash flow
    """
    if not EMERGENT_LLM_KEY:
        raise HTTPException(status_code=500, detail="AI service not configured")
    
    context = await get_business_context()
    
    # Get historical data for trends
    invoices = await db.invoices.find({
        "invoice_type": "Sales",
        "status": {"$ne": "cancelled"}
    }, {"_id": 0, "invoice_date": 1, "total_amount": 1}).sort("invoice_date", -1).to_list(500)
    
    # Group by month
    monthly_sales = {}
    for inv in invoices:
        month = inv.get("invoice_date", "")[:7]
        if month:
            if month not in monthly_sales:
                monthly_sales[month] = 0
            monthly_sales[month] += inv.get("total_amount", 0)
    
    historical_data = [{"month": k, "sales": v} for k, v in sorted(monthly_sales.items())[-6:]]
    
    system_message = """You are a predictive analytics AI for AdhesiveFlow ERP (adhesive tapes industry).
Based on historical data and current trends, provide predictions with:
1. PREDICTION VALUE (specific number/range)
2. CONFIDENCE LEVEL (High/Medium/Low with %)
3. KEY FACTORS (what's driving this prediction)
4. SCENARIOS (best case, expected, worst case)
5. RECOMMENDATIONS (how to improve the outcome)

Be specific with numbers. Explain your reasoning briefly."""

    metric_prompts = {
        "sales": f"Predict total sales for the next {data.horizon_days} days based on the historical trend.",
        "inventory": f"Predict which items will need reordering in the next {data.horizon_days} days and estimated quantities.",
        "cash_flow": f"Predict net cash position in {data.horizon_days} days considering AR collection and AP payments."
    }

    user_prompt = f"""CURRENT BUSINESS STATE:
{json.dumps(context, indent=2)}

HISTORICAL MONTHLY SALES (last 6 months):
{json.dumps(historical_data, indent=2)}

PREDICTION REQUEST: {data.metric.upper()}
FORECAST HORIZON: {data.horizon_days} days

{metric_prompts.get(data.metric, metric_prompts['sales'])}

Provide a detailed prediction with confidence intervals."""

    try:
        chat = await get_llm_chat(
            session_id=f"predict-{current_user.get('id', 'default')}-{datetime.now().timestamp()}",
            system_message=system_message
        )
        
        response = await chat.send_message(UserMessage(text=user_prompt))
        
        return {
            "metric": data.metric,
            "horizon_days": data.horizon_days,
            "prediction": response,
            "historical_data": historical_data,
            "current_state": {
                "mtd_sales": context["mtd_sales"],
                "ar": context["accounts_receivable"],
                "ap": context["accounts_payable"],
                "low_stock_count": context["low_stock_items_count"]
            },
            "generated_at": datetime.now(timezone.utc).isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")


# ==================== 4. SMART ALERTS ====================
@router.post("/smart-alerts")
async def generate_smart_alerts(data: AlertCheckRequest, current_user: dict = Depends(get_current_user)):
    """
    AI detects unusual patterns and generates smart alerts
    """
    if not EMERGENT_LLM_KEY:
        raise HTTPException(status_code=500, detail="AI service not configured")
    
    context = await get_business_context()
    
    # Additional anomaly data
    # Check for overdue invoices
    overdue_invoices = await db.invoices.find({
        "invoice_type": "Sales",
        "status": {"$nin": ["paid", "cancelled"]},
        "due_date": {"$lt": datetime.now(timezone.utc).strftime("%Y-%m-%d")}
    }, {"_id": 0}).to_list(100)
    overdue_amount = sum(inv.get("balance_amount", 0) for inv in overdue_invoices)
    
    # Check production issues
    production_issues = []
    if context["avg_scrap_percent"] > 7:
        production_issues.append(f"Scrap rate {context['avg_scrap_percent']}% exceeds 7% limit")
    
    system_message = """You are a smart alert AI for AdhesiveFlow ERP (adhesive tapes industry).
Analyze the business data for anomalies, risks, and urgent issues.
For each alert, provide:
- ALERT TYPE: [CRITICAL/WARNING/INFO]
- CATEGORY: [Sales/Inventory/Production/Finance/Customer]
- TITLE: Brief description
- DETAILS: What's happening and why it matters
- IMPACT: Potential business impact
- ACTION: Recommended immediate action

Prioritize by urgency. Only flag genuinely concerning patterns, not normal variations."""

    user_prompt = f"""CURRENT BUSINESS STATE:
{json.dumps(context, indent=2)}

ADDITIONAL DATA:
- Overdue invoices count: {len(overdue_invoices)}
- Overdue amount: ₹{overdue_amount:,.0f}
- Production issues: {production_issues if production_issues else "None detected"}

CHECK TYPE: {data.check_type.upper()}

Analyze this data and generate smart alerts for any concerning patterns, anomalies, or issues that need attention. If everything looks normal, say so."""

    try:
        chat = await get_llm_chat(
            session_id=f"alerts-{current_user.get('id', 'default')}-{datetime.now().timestamp()}",
            system_message=system_message
        )
        
        response = await chat.send_message(UserMessage(text=user_prompt))
        
        # Store alerts
        alert_doc = {
            "id": str(uuid.uuid4()),
            "type": "ai_generated",
            "check_type": data.check_type,
            "alerts_text": response,
            "data_snapshot": context,
            "overdue_amount": overdue_amount,
            "generated_at": datetime.now(timezone.utc).isoformat()
        }
        await db.smart_alerts.insert_one(alert_doc)
        
        return {
            "check_type": data.check_type,
            "alerts": response,
            "summary": {
                "overdue_invoices": len(overdue_invoices),
                "overdue_amount": overdue_amount,
                "low_stock_items": context["low_stock_items_count"],
                "scrap_rate": context["avg_scrap_percent"],
                "ar_ap_gap": context["net_position"]
            },
            "generated_at": datetime.now(timezone.utc).isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Alert generation failed: {str(e)}")


# ==================== QUERY HISTORY ====================
@router.get("/query-history")
async def get_query_history(limit: int = 20, current_user: dict = Depends(get_current_user)):
    """Get history of AI queries"""
    queries = await db.ai_queries.find(
        {"user_id": current_user.get("id")},
        {"_id": 0}
    ).sort("created_at", -1).to_list(limit)
    return queries


@router.get("/alerts-history")
async def get_alerts_history(limit: int = 10, current_user: dict = Depends(get_current_user)):
    """Get history of smart alerts"""
    alerts = await db.smart_alerts.find({}, {"_id": 0}).sort("generated_at", -1).to_list(limit)
    return alerts
