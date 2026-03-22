from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone, timedelta
import uuid
import os
from server import db, get_current_user
from emergentintegrations.llm.chat import LlmChat, UserMessage

router = APIRouter()

EMERGENT_LLM_KEY = os.getenv('EMERGENT_LLM_KEY')


@router.get("/overview")
async def get_dashboard_overview(current_user: dict = Depends(get_current_user)):
    now = datetime.now(timezone.utc)
    start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    
    leads_count = await db.leads.count_documents({'created_at': {'$gte': start_of_month.isoformat()}})
    quotes_count = await db.quotations.count_documents({'created_at': {'$gte': start_of_month.isoformat()}})
    samples_count = await db.samples.count_documents({'created_at': {'$gte': start_of_month.isoformat()}})
    
    invoices = await db.invoices.find({'created_at': {'$gte': start_of_month.isoformat()}}, {'_id': 0}).to_list(10000)
    total_revenue = sum(inv.get('total_amount', 0) for inv in invoices)
    
    paid_invoices = [inv for inv in invoices if inv.get('status') == 'paid']
    revenue_received = sum(inv.get('total_amount', 0) for inv in paid_invoices)
    
    low_stock = await db.stock.aggregate([
        {
            '$lookup': {
                'from': 'items',
                'localField': 'item_id',
                'foreignField': 'id',
                'as': 'item_details'
            }
        },
        {'$unwind': '$item_details'},
        {
            '$match': {
                '$expr': {'$lt': ['$quantity', '$item_details.reorder_level']}
            }
        },
        {'$count': 'count'}
    ]).to_list(1)
    
    low_stock_count = low_stock[0]['count'] if low_stock else 0
    
    work_orders = await db.work_orders.find({}, {'_id': 0}).to_list(10000)
    wo_in_progress = sum(1 for wo in work_orders if wo.get('status') == 'in_progress')
    wo_completed = sum(1 for wo in work_orders if wo.get('status') == 'completed')
    
    production_entries = await db.production_entries.find({}, {'_id': 0}).to_list(10000)
    total_wastage = sum(entry.get('wastage', 0) for entry in production_entries)
    total_produced = sum(entry.get('quantity_produced', 0) for entry in production_entries)
    wastage_percentage = (total_wastage / (total_produced + total_wastage) * 100) if (total_produced + total_wastage) > 0 else 0
    
    employees = await db.employees.count_documents({'status': 'active'})
    
    qc_inspections = await db.qc_inspections.find({}, {'_id': 0}).to_list(10000)
    qc_pass_rate = (sum(1 for insp in qc_inspections if insp.get('result') == 'pass') / len(qc_inspections) * 100) if qc_inspections else 0
    
    open_complaints = await db.customer_complaints.count_documents({'status': 'open'})
    
    return {
        'crm': {
            'leads': leads_count,
            'quotations': quotes_count,
            'samples': samples_count
        },
        'revenue': {
            'total_billed': total_revenue,
            'received': revenue_received,
            'pending': total_revenue - revenue_received
        },
        'inventory': {
            'low_stock_items': low_stock_count
        },
        'production': {
            'wo_in_progress': wo_in_progress,
            'wo_completed': wo_completed,
            'wastage_percentage': round(wastage_percentage, 2)
        },
        'hrms': {
            'active_employees': employees
        },
        'quality': {
            'qc_pass_rate': round(qc_pass_rate, 2),
            'open_complaints': open_complaints
        }
    }


@router.get("/revenue-analytics")
async def get_revenue_analytics(period: str = "month", current_user: dict = Depends(get_current_user)):
    now = datetime.now(timezone.utc)
    
    if period == "month":
        start_date = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    elif period == "quarter":
        quarter_month = ((now.month - 1) // 3) * 3 + 1
        start_date = now.replace(month=quarter_month, day=1, hour=0, minute=0, second=0, microsecond=0)
    else:
        start_date = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
    
    invoices = await db.invoices.find({'created_at': {'$gte': start_date.isoformat()}}, {'_id': 0}).to_list(10000)
    
    daily_revenue = {}
    for inv in invoices:
        date = inv.get('created_at', '')[:10]
        if date:
            if date not in daily_revenue:
                daily_revenue[date] = 0
            daily_revenue[date] += inv.get('total_amount', 0)
    
    by_location = {}
    for inv in invoices:
        loc = inv.get('location', 'Unknown')
        if loc not in by_location:
            by_location[loc] = 0
        by_location[loc] += inv.get('total_amount', 0)
    
    return {
        'period': period,
        'total_revenue': sum(inv.get('total_amount', 0) for inv in invoices),
        'daily_revenue': daily_revenue,
        'by_location': by_location,
        'invoice_count': len(invoices)
    }


@router.get("/production-analytics")
async def get_production_analytics(current_user: dict = Depends(get_current_user)):
    now = datetime.now(timezone.utc)
    start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    
    production_entries = await db.production_entries.find({'created_at': {'$gte': start_of_month.isoformat()}}, {'_id': 0}).to_list(10000)
    
    by_machine = {}
    for entry in production_entries:
        wo = await db.work_orders.find_one({'id': entry.get('wo_id')}, {'_id': 0})
        if wo:
            machine_id = wo.get('machine_id', 'unknown')
            if machine_id not in by_machine:
                by_machine[machine_id] = {'produced': 0, 'wastage': 0}
            by_machine[machine_id]['produced'] += entry.get('quantity_produced', 0)
            by_machine[machine_id]['wastage'] += entry.get('wastage', 0)
    
    total_produced = sum(entry.get('quantity_produced', 0) for entry in production_entries)
    total_wastage = sum(entry.get('wastage', 0) for entry in production_entries)
    wastage_percentage = (total_wastage / (total_produced + total_wastage) * 100) if (total_produced + total_wastage) > 0 else 0
    
    return {
        'total_produced': total_produced,
        'total_wastage': total_wastage,
        'wastage_percentage': round(wastage_percentage, 2),
        'by_machine': by_machine
    }


@router.get("/ai-insights")
async def get_ai_insights(current_user: dict = Depends(get_current_user)):
    overview = await get_dashboard_overview(current_user)
    revenue_data = await get_revenue_analytics("month", current_user)
    production_data = await get_production_analytics(current_user)
    
    context = f"""
You are an AI business analyst for an adhesive tapes manufacturing company. Analyze the following data and provide 3-5 actionable insights:

CRM Metrics:
- Leads this month: {overview['crm']['leads']}
- Quotations: {overview['crm']['quotations']}
- Samples sent: {overview['crm']['samples']}

Revenue:
- Total billed: ₹{overview['revenue']['total_billed']:,.2f}
- Received: ₹{overview['revenue']['received']:,.2f}
- Pending: ₹{overview['revenue']['pending']:,.2f}

Production:
- Work orders in progress: {overview['production']['wo_in_progress']}
- Completed: {overview['production']['wo_completed']}
- Wastage: {overview['production']['wastage_percentage']}%

Inventory:
- Low stock items: {overview['inventory']['low_stock_items']}

Quality:
- QC pass rate: {overview['quality']['qc_pass_rate']}%
- Open complaints: {overview['quality']['open_complaints']}

Provide insights in this format:
1. [Insight category]: [Brief actionable insight]
2. ...
"""
    
    try:
        chat = LlmChat(
            api_key=EMERGENT_LLM_KEY,
            session_id=f"dashboard-insights-{current_user['id']}",
            system_message="You are an expert business analyst for manufacturing companies. Provide concise, actionable insights."
        ).with_model("openai", "gpt-5.2")
        
        response = await chat.send_message(UserMessage(text=context))
        
        return {
            'insights': response,
            'generated_at': datetime.now(timezone.utc).isoformat()
        }
    except Exception as e:
        return {
            'insights': "AI insights temporarily unavailable. Please check your API key configuration.",
            'error': str(e)
        }


@router.get("/forecast")
async def get_forecast(metric: str, current_user: dict = Depends(get_current_user)):
    """
    AI-powered forecasting for various metrics
    metric: 'revenue', 'demand', 'inventory'
    """
    now = datetime.now(timezone.utc)
    start_date = now - timedelta(days=90)
    
    if metric == "revenue":
        invoices = await db.invoices.find({'created_at': {'$gte': start_date.isoformat()}}, {'_id': 0}).to_list(10000)
        
        daily_data = {}
        for inv in invoices:
            date = inv.get('created_at', '')[:10]
            if date:
                if date not in daily_data:
                    daily_data[date] = 0
                daily_data[date] += inv.get('total_amount', 0)
        
        context = f"""
Based on the last 90 days of revenue data:
{daily_data}

Provide a forecast for the next 30 days revenue. Consider:
- Historical trends
- Seasonality
- Current month performance

Format: Provide estimated revenue range and key factors affecting it.
"""
    
    elif metric == "demand":
        work_orders = await db.work_orders.find({'created_at': {'$gte': start_date.isoformat()}}, {'_id': 0}).to_list(10000)
        
        item_demand = {}
        for wo in work_orders:
            item_id = wo.get('item_id', 'unknown')
            if item_id not in item_demand:
                item_demand[item_id] = 0
            item_demand[item_id] += wo.get('quantity_to_make', 0)
        
        context = f"""
Based on the last 90 days of production demand:
{item_demand}

Forecast the demand for the next 30 days. Identify:
- Top items in demand
- Recommended production levels
- Inventory planning suggestions
"""
    
    else:
        context = "Invalid metric specified"
    
    try:
        chat = LlmChat(
            api_key=EMERGENT_LLM_KEY,
            session_id=f"forecast-{metric}-{current_user['id']}",
            system_message="You are an expert forecasting analyst for manufacturing. Provide data-driven predictions."
        ).with_model("openai", "gpt-5.2")
        
        response = await chat.send_message(UserMessage(text=context))
        
        return {
            'metric': metric,
            'forecast': response,
            'generated_at': datetime.now(timezone.utc).isoformat()
        }
    except Exception as e:
        return {
            'metric': metric,
            'forecast': "Forecast temporarily unavailable",
            'error': str(e)
        }


@router.get("/recommendations")
async def get_recommendations(area: str, current_user: dict = Depends(get_current_user)):
    """
    Get AI-powered recommendations for specific areas
    area: 'inventory', 'production', 'sales', 'quality'
    """
    
    if area == "inventory":
        low_stock = await db.stock.aggregate([
            {
                '$lookup': {
                    'from': 'items',
                    'localField': 'item_id',
                    'foreignField': 'id',
                    'as': 'item_details'
                }
            },
            {'$unwind': '$item_details'},
            {
                '$match': {
                    '$expr': {'$lt': ['$quantity', '$item_details.reorder_level']}
                }
            },
            {'$project': {'_id': 0}}
        ]).to_list(1000)
        
        context = f"""
Low stock items: {len(low_stock)}
Analyze and provide recommendations for:
1. Priority items to reorder
2. Optimal order quantities
3. Safety stock adjustments
"""
    
    elif area == "production":
        production_data = await get_production_analytics(current_user)
        
        context = f"""
Production metrics:
- Wastage: {production_data['wastage_percentage']}%
- Total produced: {production_data['total_produced']}

Provide recommendations to:
1. Reduce wastage
2. Improve production efficiency
3. Optimize machine utilization
"""
    
    elif area == "sales":
        overview = await get_dashboard_overview(current_user)
        
        conversion_rate = (overview['crm']['quotations'] / overview['crm']['leads'] * 100) if overview['crm']['leads'] > 0 else 0
        
        context = f"""
Sales funnel:
- Leads: {overview['crm']['leads']}
- Quotations: {overview['crm']['quotations']}
- Conversion rate: {conversion_rate:.1f}%

Recommend strategies to:
1. Improve lead conversion
2. Optimize quotation follow-up
3. Enhance customer engagement
"""
    
    else:
        context = "Invalid area specified"
    
    try:
        chat = LlmChat(
            api_key=EMERGENT_LLM_KEY,
            session_id=f"recommendations-{area}-{current_user['id']}",
            system_message="You are a manufacturing operations consultant. Provide specific, actionable recommendations."
        ).with_model("openai", "gpt-5.2")
        
        response = await chat.send_message(UserMessage(text=context))
        
        return {
            'area': area,
            'recommendations': response,
            'generated_at': datetime.now(timezone.utc).isoformat()
        }
    except Exception as e:
        return {
            'area': area,
            'recommendations': "Recommendations temporarily unavailable",
            'error': str(e)
        }