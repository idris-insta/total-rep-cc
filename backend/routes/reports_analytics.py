"""
Reports & Analytics Module - Comprehensive Business Intelligence
Features:
- Sales Analytics (Daily, Weekly, Monthly, YoY)
- Purchase Analytics
- Inventory Reports
- Financial Reports (P&L, Balance Sheet)
- Customer Analytics (Top customers, Payment behavior)
- Vendor Analytics
- Employee Performance Reports
- Custom Report Builder
- Export to Excel/PDF
- Scheduled Email Reports
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone, timedelta
from dateutil.relativedelta import relativedelta
import uuid
import io

from server import db, get_current_user

# PDF and Excel export libraries
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, mm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.pdfgen import canvas
import xlsxwriter

router = APIRouter()

# ==================== SALES ANALYTICS ====================
@router.get("/sales/summary")
async def get_sales_summary(
    period: str = Query(default="month"),  # today, week, month, quarter, year
    compare_previous: bool = True,
    current_user: dict = Depends(get_current_user)
):
    """Get sales summary with comparison to previous period"""
    now = datetime.now(timezone.utc)
    
    if period == "today":
        start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
        prev_start = start_date - timedelta(days=1)
        prev_end = start_date
    elif period == "week":
        start_date = now - timedelta(days=now.weekday())
        start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
        prev_start = start_date - timedelta(weeks=1)
        prev_end = start_date
    elif period == "month":
        start_date = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        prev_start = start_date - relativedelta(months=1)
        prev_end = start_date
    elif period == "quarter":
        quarter = (now.month - 1) // 3
        start_date = now.replace(month=quarter*3+1, day=1, hour=0, minute=0, second=0, microsecond=0)
        prev_start = start_date - relativedelta(months=3)
        prev_end = start_date
    else:  # year
        start_date = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
        prev_start = start_date - relativedelta(years=1)
        prev_end = start_date
    
    # Current period
    current_invoices = await db.invoices.find({
        "invoice_type": "Sales",
        "invoice_date": {"$gte": start_date.strftime("%Y-%m-%d")}
    }, {"_id": 0}).to_list(10000)
    
    current_total = sum(inv.get("grand_total", 0) for inv in current_invoices)
    current_count = len(current_invoices)
    current_avg = current_total / current_count if current_count > 0 else 0
    
    # Previous period
    prev_invoices = await db.invoices.find({
        "invoice_type": "Sales",
        "invoice_date": {
            "$gte": prev_start.strftime("%Y-%m-%d"),
            "$lt": prev_end.strftime("%Y-%m-%d")
        }
    }, {"_id": 0}).to_list(10000)
    
    prev_total = sum(inv.get("grand_total", 0) for inv in prev_invoices)
    prev_count = len(prev_invoices)
    
    # Calculate growth
    growth_percent = ((current_total - prev_total) / prev_total * 100) if prev_total > 0 else 0
    count_growth = ((current_count - prev_count) / prev_count * 100) if prev_count > 0 else 0
    
    return {
        "period": period,
        "current_period": {
            "start_date": start_date.strftime("%Y-%m-%d"),
            "total_sales": round(current_total, 2),
            "invoice_count": current_count,
            "average_order_value": round(current_avg, 2)
        },
        "previous_period": {
            "start_date": prev_start.strftime("%Y-%m-%d"),
            "end_date": prev_end.strftime("%Y-%m-%d"),
            "total_sales": round(prev_total, 2),
            "invoice_count": prev_count
        },
        "growth": {
            "sales_growth_percent": round(growth_percent, 2),
            "count_growth_percent": round(count_growth, 2),
            "sales_growth_amount": round(current_total - prev_total, 2)
        }
    }

@router.get("/sales/trend")
async def get_sales_trend(
    period: str = Query(default="daily"),  # daily, weekly, monthly
    months: int = Query(default=6),
    current_user: dict = Depends(get_current_user)
):
    """Get sales trend over time"""
    now = datetime.now(timezone.utc)
    start_date = now - relativedelta(months=months)
    
    invoices = await db.invoices.find({
        "invoice_type": "Sales",
        "invoice_date": {"$gte": start_date.strftime("%Y-%m-%d")}
    }, {"_id": 0, "invoice_date": 1, "grand_total": 1}).to_list(100000)
    
    # Group by period
    trend_data = {}
    for inv in invoices:
        date_str = inv.get("invoice_date", "")
        if not date_str:
            continue
            
        if period == "daily":
            key = date_str
        elif period == "weekly":
            dt = datetime.strptime(date_str, "%Y-%m-%d")
            week_start = dt - timedelta(days=dt.weekday())
            key = week_start.strftime("%Y-%m-%d")
        else:  # monthly
            key = date_str[:7]  # YYYY-MM
        
        if key not in trend_data:
            trend_data[key] = {"period": key, "total": 0, "count": 0}
        trend_data[key]["total"] += inv.get("grand_total", 0)
        trend_data[key]["count"] += 1
    
    # Sort and format
    trend_list = sorted(trend_data.values(), key=lambda x: x["period"])
    for item in trend_list:
        item["total"] = round(item["total"], 2)
        item["average"] = round(item["total"] / item["count"], 2) if item["count"] > 0 else 0
    
    return {
        "period_type": period,
        "data_points": len(trend_list),
        "trend": trend_list
    }

@router.get("/sales/top-products")
async def get_top_products(
    limit: int = Query(default=10),
    period_months: int = Query(default=3),
    current_user: dict = Depends(get_current_user)
):
    """Get top selling products"""
    start_date = (datetime.now(timezone.utc) - relativedelta(months=period_months)).strftime("%Y-%m-%d")
    
    invoices = await db.invoices.find({
        "invoice_type": "Sales",
        "invoice_date": {"$gte": start_date}
    }, {"_id": 0, "items": 1}).to_list(100000)
    
    product_sales = {}
    for inv in invoices:
        for item in inv.get("items", []):
            item_id = item.get("item_id") or item.get("description", "Unknown")
            if item_id not in product_sales:
                product_sales[item_id] = {
                    "item_id": item_id,
                    "item_name": item.get("item_name") or item.get("description", ""),
                    "quantity_sold": 0,
                    "total_revenue": 0,
                    "order_count": 0
                }
            product_sales[item_id]["quantity_sold"] += item.get("quantity", 0)
            product_sales[item_id]["total_revenue"] += item.get("line_total", 0)
            product_sales[item_id]["order_count"] += 1
    
    # Sort by revenue and take top
    top_products = sorted(product_sales.values(), key=lambda x: x["total_revenue"], reverse=True)[:limit]
    
    for p in top_products:
        p["total_revenue"] = round(p["total_revenue"], 2)
        p["avg_price"] = round(p["total_revenue"] / p["quantity_sold"], 2) if p["quantity_sold"] > 0 else 0
    
    return {
        "period_months": period_months,
        "top_products": top_products
    }

@router.get("/sales/top-customers")
async def get_top_customers(
    limit: int = Query(default=10),
    period_months: int = Query(default=12),
    current_user: dict = Depends(get_current_user)
):
    """Get top customers by sales value"""
    start_date = (datetime.now(timezone.utc) - relativedelta(months=period_months)).strftime("%Y-%m-%d")
    
    invoices = await db.invoices.find({
        "invoice_type": "Sales",
        "invoice_date": {"$gte": start_date}
    }, {"_id": 0, "account_id": 1, "account_name": 1, "grand_total": 1}).to_list(100000)
    
    customer_sales = {}
    for inv in invoices:
        acc_id = inv.get("account_id", "Unknown")
        if acc_id not in customer_sales:
            customer_sales[acc_id] = {
                "customer_id": acc_id,
                "customer_name": inv.get("account_name", "Unknown"),
                "total_purchases": 0,
                "order_count": 0
            }
        customer_sales[acc_id]["total_purchases"] += inv.get("grand_total", 0)
        customer_sales[acc_id]["order_count"] += 1
    
    top_customers = sorted(customer_sales.values(), key=lambda x: x["total_purchases"], reverse=True)[:limit]
    
    for c in top_customers:
        c["total_purchases"] = round(c["total_purchases"], 2)
        c["avg_order_value"] = round(c["total_purchases"] / c["order_count"], 2) if c["order_count"] > 0 else 0
    
    return {
        "period_months": period_months,
        "top_customers": top_customers
    }

# ==================== PURCHASE ANALYTICS ====================
@router.get("/purchases/summary")
async def get_purchase_summary(
    period_months: int = Query(default=3),
    current_user: dict = Depends(get_current_user)
):
    """Get purchase summary"""
    start_date = (datetime.now(timezone.utc) - relativedelta(months=period_months)).strftime("%Y-%m-%d")
    
    pos = await db.purchase_orders.find({
        "created_at": {"$gte": start_date}
    }, {"_id": 0}).to_list(10000)
    
    total_value = sum(po.get("grand_total", 0) for po in pos)
    received_value = sum(po.get("grand_total", 0) for po in pos if po.get("status") == "received")
    pending_value = sum(po.get("grand_total", 0) for po in pos if po.get("status") in ["draft", "sent"])
    
    by_status = {}
    for po in pos:
        status = po.get("status", "unknown")
        if status not in by_status:
            by_status[status] = {"count": 0, "value": 0}
        by_status[status]["count"] += 1
        by_status[status]["value"] += po.get("grand_total", 0)
    
    return {
        "period_months": period_months,
        "total_pos": len(pos),
        "total_value": round(total_value, 2),
        "received_value": round(received_value, 2),
        "pending_value": round(pending_value, 2),
        "by_status": by_status
    }

@router.get("/purchases/top-suppliers")
async def get_top_suppliers(
    limit: int = Query(default=10),
    period_months: int = Query(default=12),
    current_user: dict = Depends(get_current_user)
):
    """Get top suppliers by purchase value"""
    start_date = (datetime.now(timezone.utc) - relativedelta(months=period_months)).strftime("%Y-%m-%d")
    
    pos = await db.purchase_orders.find({
        "created_at": {"$gte": start_date},
        "status": {"$in": ["received", "partial"]}
    }, {"_id": 0, "supplier_id": 1, "supplier_name": 1, "grand_total": 1}).to_list(100000)
    
    supplier_purchases = {}
    for po in pos:
        sup_id = po.get("supplier_id", "Unknown")
        if sup_id not in supplier_purchases:
            supplier_purchases[sup_id] = {
                "supplier_id": sup_id,
                "supplier_name": po.get("supplier_name", "Unknown"),
                "total_purchases": 0,
                "po_count": 0
            }
        supplier_purchases[sup_id]["total_purchases"] += po.get("grand_total", 0)
        supplier_purchases[sup_id]["po_count"] += 1
    
    top_suppliers = sorted(supplier_purchases.values(), key=lambda x: x["total_purchases"], reverse=True)[:limit]
    
    for s in top_suppliers:
        s["total_purchases"] = round(s["total_purchases"], 2)
    
    return {"period_months": period_months, "top_suppliers": top_suppliers}

# ==================== INVENTORY REPORTS ====================
@router.get("/inventory/summary")
async def get_inventory_summary(current_user: dict = Depends(get_current_user)):
    """Get inventory summary"""
    items = await db.items.find({"is_active": True}, {"_id": 0}).to_list(10000)
    
    total_items = len(items)
    total_stock_value = sum((i.get("current_stock", 0) * i.get("standard_cost", 0)) for i in items)
    low_stock_count = len([i for i in items if i.get("current_stock", 0) <= i.get("reorder_level", 0) and i.get("reorder_level", 0) > 0])
    out_of_stock = len([i for i in items if i.get("current_stock", 0) <= 0])
    
    # Category breakdown
    by_category = {}
    for item in items:
        cat = item.get("category", "Uncategorized")
        if cat not in by_category:
            by_category[cat] = {"count": 0, "stock_value": 0}
        by_category[cat]["count"] += 1
        by_category[cat]["stock_value"] += item.get("current_stock", 0) * item.get("standard_cost", 0)
    
    return {
        "total_items": total_items,
        "total_stock_value": round(total_stock_value, 2),
        "low_stock_items": low_stock_count,
        "out_of_stock_items": out_of_stock,
        "by_category": by_category
    }

@router.get("/inventory/movement")
async def get_inventory_movement(
    period_days: int = Query(default=30),
    current_user: dict = Depends(get_current_user)
):
    """Get inventory movement report"""
    start_date = (datetime.now(timezone.utc) - timedelta(days=period_days)).isoformat()
    
    # Get stock ledger entries
    movements = await db.stock_ledger.find({
        "transaction_date": {"$gte": start_date}
    }, {"_id": 0}).to_list(100000)
    
    total_in = sum(m.get("in_qty", 0) for m in movements)
    total_out = sum(m.get("out_qty", 0) for m in movements)
    
    # By transaction type
    by_type = {}
    for m in movements:
        t_type = m.get("transaction_type", "unknown")
        if t_type not in by_type:
            by_type[t_type] = {"in_qty": 0, "out_qty": 0, "count": 0}
        by_type[t_type]["in_qty"] += m.get("in_qty", 0)
        by_type[t_type]["out_qty"] += m.get("out_qty", 0)
        by_type[t_type]["count"] += 1
    
    return {
        "period_days": period_days,
        "total_transactions": len(movements),
        "total_in_qty": round(total_in, 2),
        "total_out_qty": round(total_out, 2),
        "net_movement": round(total_in - total_out, 2),
        "by_transaction_type": by_type
    }

# ==================== FINANCIAL REPORTS ====================
@router.get("/financial/profit-loss")
async def get_profit_loss(
    period: str = Query(default="month"),  # month, quarter, year
    current_user: dict = Depends(get_current_user)
):
    """Get Profit & Loss summary"""
    now = datetime.now(timezone.utc)
    
    if period == "month":
        start_date = now.replace(day=1)
    elif period == "quarter":
        quarter = (now.month - 1) // 3
        start_date = now.replace(month=quarter*3+1, day=1)
    else:
        start_date = now.replace(month=1, day=1)
    
    start_str = start_date.strftime("%Y-%m-%d")
    
    # Revenue (Sales)
    sales = await db.invoices.find({
        "invoice_type": "Sales",
        "invoice_date": {"$gte": start_str}
    }, {"_id": 0, "grand_total": 1, "taxable_amount": 1}).to_list(100000)
    
    total_revenue = sum(s.get("taxable_amount", 0) for s in sales)
    
    # Cost of Goods Sold (Purchases)
    purchases = await db.invoices.find({
        "invoice_type": "Purchase",
        "invoice_date": {"$gte": start_str}
    }, {"_id": 0, "taxable_amount": 1}).to_list(100000)
    
    cogs = sum(p.get("taxable_amount", 0) for p in purchases)
    
    # Expenses
    expenses = await db.expenses.find({
        "expense_date": {"$gte": start_str}
    }, {"_id": 0, "amount": 1, "category": 1}).to_list(100000)
    
    total_expenses = sum(e.get("amount", 0) for e in expenses)
    expense_breakdown = {}
    for e in expenses:
        cat = e.get("category", "Other")
        expense_breakdown[cat] = expense_breakdown.get(cat, 0) + e.get("amount", 0)
    
    gross_profit = total_revenue - cogs
    net_profit = gross_profit - total_expenses
    gross_margin = (gross_profit / total_revenue * 100) if total_revenue > 0 else 0
    net_margin = (net_profit / total_revenue * 100) if total_revenue > 0 else 0
    
    return {
        "period": period,
        "start_date": start_str,
        "revenue": {
            "total_revenue": round(total_revenue, 2),
            "invoice_count": len(sales)
        },
        "cost_of_goods_sold": round(cogs, 2),
        "gross_profit": round(gross_profit, 2),
        "gross_margin_percent": round(gross_margin, 2),
        "operating_expenses": {
            "total": round(total_expenses, 2),
            "breakdown": expense_breakdown
        },
        "net_profit": round(net_profit, 2),
        "net_margin_percent": round(net_margin, 2)
    }

@router.get("/financial/cash-flow")
async def get_cash_flow(
    period_months: int = Query(default=3),
    current_user: dict = Depends(get_current_user)
):
    """Get cash flow summary"""
    start_date = (datetime.now(timezone.utc) - relativedelta(months=period_months)).strftime("%Y-%m-%d")
    
    # Collections (payments received)
    receipts = await db.payments.find({
        "payment_type": "receipt",
        "payment_date": {"$gte": start_date}
    }, {"_id": 0, "amount": 1}).to_list(100000)
    
    total_receipts = sum(r.get("amount", 0) for r in receipts)
    
    # Payments made
    payments = await db.payments.find({
        "payment_type": "payment",
        "payment_date": {"$gte": start_date}
    }, {"_id": 0, "amount": 1}).to_list(100000)
    
    total_payments = sum(p.get("amount", 0) for p in payments)
    
    # Outstanding receivables
    receivables = await db.invoices.find({
        "invoice_type": "Sales",
        "status": {"$in": ["sent", "partial", "overdue"]}
    }, {"_id": 0, "balance": 1}).to_list(100000)
    
    total_receivables = sum(r.get("balance", 0) for r in receivables)
    
    # Outstanding payables
    payables = await db.invoices.find({
        "invoice_type": "Purchase",
        "status": {"$in": ["sent", "partial", "overdue"]}
    }, {"_id": 0, "balance": 1}).to_list(100000)
    
    total_payables = sum(p.get("balance", 0) for p in payables)
    
    return {
        "period_months": period_months,
        "cash_inflow": round(total_receipts, 2),
        "cash_outflow": round(total_payments, 2),
        "net_cash_flow": round(total_receipts - total_payments, 2),
        "outstanding_receivables": round(total_receivables, 2),
        "outstanding_payables": round(total_payables, 2),
        "net_working_capital": round(total_receivables - total_payables, 2)
    }

# ==================== DASHBOARD KPIs ====================
@router.get("/dashboard/kpis")
async def get_dashboard_kpis(current_user: dict = Depends(get_current_user)):
    """Get all KPIs for dashboard"""
    now = datetime.now(timezone.utc)
    month_start = now.replace(day=1).strftime("%Y-%m-%d")
    today = now.strftime("%Y-%m-%d")
    
    # Today's sales
    today_sales = await db.invoices.find({
        "invoice_type": "Sales",
        "invoice_date": today
    }, {"_id": 0, "grand_total": 1}).to_list(1000)
    
    # Month's sales
    month_sales = await db.invoices.find({
        "invoice_type": "Sales",
        "invoice_date": {"$gte": month_start}
    }, {"_id": 0, "grand_total": 1}).to_list(100000)
    
    # Pending orders
    pending_orders = await db.purchase_orders.count_documents({"status": {"$in": ["draft", "sent"]}})
    
    # Low stock items
    low_stock = await db.items.count_documents({
        "is_active": True,
        "$expr": {"$lte": ["$current_stock", "$reorder_level"]},
        "reorder_level": {"$gt": 0}
    })
    
    # Overdue invoices
    overdue = await db.invoices.count_documents({
        "status": "overdue"
    })
    
    # Active customers (ordered in last 90 days)
    ninety_days_ago = (now - timedelta(days=90)).strftime("%Y-%m-%d")
    active_customers = await db.invoices.distinct("account_id", {
        "invoice_type": "Sales",
        "invoice_date": {"$gte": ninety_days_ago}
    })
    
    return {
        "today_sales": round(sum(s.get("grand_total", 0) for s in today_sales), 2),
        "today_orders": len(today_sales),
        "month_sales": round(sum(s.get("grand_total", 0) for s in month_sales), 2),
        "month_orders": len(month_sales),
        "pending_pos": pending_orders,
        "low_stock_items": low_stock,
        "overdue_invoices": overdue,
        "active_customers": len(active_customers)
    }


# ==================== PDF EXPORT ====================
@router.get("/export/pdf/{report_type}")
async def export_report_pdf(
    report_type: str,
    period: str = Query(default="month"),
    current_user: dict = Depends(get_current_user)
):
    """Export report as PDF"""
    buffer = io.BytesIO()
    
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=30,
        leftMargin=30,
        topMargin=30,
        bottomMargin=30
    )
    
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        spaceAfter=20,
        textColor=colors.HexColor('#1e293b')
    )
    subtitle_style = ParagraphStyle(
        'CustomSubtitle',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.HexColor('#64748b'),
        spaceAfter=10
    )
    
    elements = []
    
    now = datetime.now(timezone.utc)
    
    if report_type == "sales":
        # Sales Report
        elements.append(Paragraph("Sales Report", title_style))
        elements.append(Paragraph(f"Period: {period.capitalize()} | Generated: {now.strftime('%Y-%m-%d %H:%M')}", subtitle_style))
        elements.append(Spacer(1, 20))
        
        # Fetch sales data
        if period == "month":
            start_date = now.replace(day=1).strftime("%Y-%m-%d")
        elif period == "year":
            start_date = now.replace(month=1, day=1).strftime("%Y-%m-%d")
        else:
            start_date = (now - timedelta(days=7)).strftime("%Y-%m-%d")
        
        invoices = await db.invoices.find({
            "invoice_type": "Sales",
            "invoice_date": {"$gte": start_date}
        }, {"_id": 0}).to_list(1000)
        
        # Summary section
        total_sales = sum(inv.get("grand_total", 0) for inv in invoices)
        total_tax = sum(inv.get("total_tax", 0) for inv in invoices)
        
        summary_data = [
            ["Metric", "Value"],
            ["Total Invoices", str(len(invoices))],
            ["Total Sales", f"₹{total_sales:,.2f}"],
            ["Total Tax", f"₹{total_tax:,.2f}"],
            ["Average Order Value", f"₹{total_sales/len(invoices):,.2f}" if invoices else "₹0.00"]
        ]
        
        summary_table = Table(summary_data, colWidths=[200, 200])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f97316')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 11),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f8fafc')),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#e2e8f0')),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('PADDING', (0, 0), (-1, -1), 8),
        ]))
        elements.append(summary_table)
        elements.append(Spacer(1, 20))
        
        # Invoice list
        elements.append(Paragraph("Invoice Details", styles['Heading2']))
        elements.append(Spacer(1, 10))
        
        invoice_data = [["Invoice #", "Date", "Customer", "Amount", "Status"]]
        for inv in invoices[:50]:  # Limit to 50 rows
            invoice_data.append([
                inv.get("invoice_number", "N/A"),
                inv.get("invoice_date", "N/A"),
                inv.get("account_name", "N/A")[:25],
                f"₹{inv.get('grand_total', 0):,.2f}",
                inv.get("status", "N/A").capitalize()
            ])
        
        invoice_table = Table(invoice_data, colWidths=[80, 70, 150, 90, 70])
        invoice_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#334155')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('ALIGN', (3, 0), (3, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e1')),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('PADDING', (0, 0), (-1, -1), 6),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8fafc')]),
        ]))
        elements.append(invoice_table)
        
    elif report_type == "inventory":
        # Inventory Report
        elements.append(Paragraph("Inventory Report", title_style))
        elements.append(Paragraph(f"Generated: {now.strftime('%Y-%m-%d %H:%M')}", subtitle_style))
        elements.append(Spacer(1, 20))
        
        items = await db.items.find({"is_active": True}, {"_id": 0}).to_list(500)
        
        item_data = [["Item Code", "Item Name", "Category", "Stock", "Reorder Level", "Status"]]
        for item in items:
            stock = item.get("current_stock", 0)
            reorder = item.get("reorder_level", 0)
            status = "Low Stock" if stock <= reorder and reorder > 0 else "OK"
            item_data.append([
                item.get("item_code", "N/A"),
                item.get("item_name", "N/A")[:30],
                item.get("category", "N/A"),
                str(stock),
                str(reorder),
                status
            ])
        
        item_table = Table(item_data, colWidths=[70, 150, 80, 50, 70, 60])
        item_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#334155')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('ALIGN', (3, 0), (4, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e1')),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('PADDING', (0, 0), (-1, -1), 6),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8fafc')]),
        ]))
        elements.append(item_table)
        
    elif report_type == "customers":
        # Customer Report
        elements.append(Paragraph("Customer Analytics Report", title_style))
        elements.append(Paragraph(f"Generated: {now.strftime('%Y-%m-%d %H:%M')}", subtitle_style))
        elements.append(Spacer(1, 20))
        
        accounts = await db.accounts.find({"is_customer": True}, {"_id": 0}).to_list(200)
        
        acc_data = [["Account Name", "Contact", "City", "Outstanding", "Last Order"]]
        for acc in accounts:
            acc_data.append([
                acc.get("account_name", "N/A")[:25],
                acc.get("contact_person", "N/A"),
                acc.get("city", "N/A"),
                f"₹{acc.get('outstanding_balance', 0):,.2f}",
                acc.get("last_order_date", "N/A")
            ])
        
        acc_table = Table(acc_data, colWidths=[130, 100, 80, 90, 80])
        acc_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#334155')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('ALIGN', (3, 0), (3, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e1')),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('PADDING', (0, 0), (-1, -1), 6),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8fafc')]),
        ]))
        elements.append(acc_table)
    
    else:
        raise HTTPException(status_code=400, detail=f"Unknown report type: {report_type}")
    
    doc.build(elements)
    buffer.seek(0)
    
    filename = f"{report_type}_report_{now.strftime('%Y%m%d_%H%M%S')}.pdf"
    
    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


# ==================== EXCEL EXPORT ====================
@router.get("/export/excel/{report_type}")
async def export_report_excel(
    report_type: str,
    period: str = Query(default="month"),
    current_user: dict = Depends(get_current_user)
):
    """Export report as Excel"""
    buffer = io.BytesIO()
    workbook = xlsxwriter.Workbook(buffer, {'in_memory': True})
    
    # Styles
    title_format = workbook.add_format({
        'bold': True, 'font_size': 16, 'font_color': '#1e293b'
    })
    header_format = workbook.add_format({
        'bold': True, 'bg_color': '#334155', 'font_color': 'white',
        'border': 1, 'text_wrap': True, 'valign': 'vcenter'
    })
    cell_format = workbook.add_format({
        'border': 1, 'valign': 'vcenter'
    })
    money_format = workbook.add_format({
        'border': 1, 'num_format': '₹#,##0.00', 'valign': 'vcenter'
    })
    date_format = workbook.add_format({
        'border': 1, 'num_format': 'yyyy-mm-dd', 'valign': 'vcenter'
    })
    
    now = datetime.now(timezone.utc)
    
    if report_type == "sales":
        worksheet = workbook.add_worksheet("Sales Report")
        
        # Title
        worksheet.write(0, 0, "Sales Report", title_format)
        worksheet.write(1, 0, f"Period: {period.capitalize()} | Generated: {now.strftime('%Y-%m-%d %H:%M')}")
        
        # Fetch data
        if period == "month":
            start_date = now.replace(day=1).strftime("%Y-%m-%d")
        elif period == "year":
            start_date = now.replace(month=1, day=1).strftime("%Y-%m-%d")
        else:
            start_date = (now - timedelta(days=7)).strftime("%Y-%m-%d")
        
        invoices = await db.invoices.find({
            "invoice_type": "Sales",
            "invoice_date": {"$gte": start_date}
        }, {"_id": 0}).to_list(5000)
        
        # Headers
        headers = ["Invoice #", "Date", "Customer", "Subtotal", "Tax", "Grand Total", "Status"]
        for col, header in enumerate(headers):
            worksheet.write(3, col, header, header_format)
        
        # Data
        row = 4
        for inv in invoices:
            worksheet.write(row, 0, inv.get("invoice_number", ""), cell_format)
            worksheet.write(row, 1, inv.get("invoice_date", ""), cell_format)
            worksheet.write(row, 2, inv.get("account_name", ""), cell_format)
            worksheet.write(row, 3, inv.get("subtotal", 0), money_format)
            worksheet.write(row, 4, inv.get("total_tax", 0), money_format)
            worksheet.write(row, 5, inv.get("grand_total", 0), money_format)
            worksheet.write(row, 6, inv.get("status", "").capitalize(), cell_format)
            row += 1
        
        # Summary
        row += 2
        worksheet.write(row, 0, "Summary", title_format)
        worksheet.write(row + 1, 0, "Total Invoices:", cell_format)
        worksheet.write(row + 1, 1, len(invoices), cell_format)
        worksheet.write(row + 2, 0, "Total Sales:", cell_format)
        worksheet.write(row + 2, 1, sum(i.get("grand_total", 0) for i in invoices), money_format)
        
        # Column widths
        worksheet.set_column(0, 0, 15)
        worksheet.set_column(1, 1, 12)
        worksheet.set_column(2, 2, 30)
        worksheet.set_column(3, 5, 15)
        worksheet.set_column(6, 6, 12)
        
    elif report_type == "inventory":
        worksheet = workbook.add_worksheet("Inventory Report")
        
        worksheet.write(0, 0, "Inventory Report", title_format)
        worksheet.write(1, 0, f"Generated: {now.strftime('%Y-%m-%d %H:%M')}")
        
        items = await db.items.find({"is_active": True}, {"_id": 0}).to_list(2000)
        
        headers = ["Item Code", "Item Name", "Category", "UOM", "Stock", "Reorder Level", "Status"]
        for col, header in enumerate(headers):
            worksheet.write(3, col, header, header_format)
        
        row = 4
        for item in items:
            stock = item.get("current_stock", 0)
            reorder = item.get("reorder_level", 0)
            status = "Low Stock" if stock <= reorder and reorder > 0 else "OK"
            
            worksheet.write(row, 0, item.get("item_code", ""), cell_format)
            worksheet.write(row, 1, item.get("item_name", ""), cell_format)
            worksheet.write(row, 2, item.get("category", ""), cell_format)
            worksheet.write(row, 3, item.get("uom", ""), cell_format)
            worksheet.write(row, 4, stock, cell_format)
            worksheet.write(row, 5, reorder, cell_format)
            worksheet.write(row, 6, status, cell_format)
            row += 1
        
        worksheet.set_column(0, 0, 12)
        worksheet.set_column(1, 1, 35)
        worksheet.set_column(2, 2, 15)
        worksheet.set_column(3, 6, 12)
        
    elif report_type == "customers":
        worksheet = workbook.add_worksheet("Customer Report")
        
        worksheet.write(0, 0, "Customer Report", title_format)
        worksheet.write(1, 0, f"Generated: {now.strftime('%Y-%m-%d %H:%M')}")
        
        accounts = await db.accounts.find({"is_customer": True}, {"_id": 0}).to_list(1000)
        
        headers = ["Account Name", "Contact Person", "Phone", "City", "State", "Outstanding"]
        for col, header in enumerate(headers):
            worksheet.write(3, col, header, header_format)
        
        row = 4
        for acc in accounts:
            worksheet.write(row, 0, acc.get("account_name", ""), cell_format)
            worksheet.write(row, 1, acc.get("contact_person", ""), cell_format)
            worksheet.write(row, 2, acc.get("phone", ""), cell_format)
            worksheet.write(row, 3, acc.get("city", ""), cell_format)
            worksheet.write(row, 4, acc.get("state", ""), cell_format)
            worksheet.write(row, 5, acc.get("outstanding_balance", 0), money_format)
            row += 1
        
        worksheet.set_column(0, 0, 30)
        worksheet.set_column(1, 1, 20)
        worksheet.set_column(2, 2, 15)
        worksheet.set_column(3, 4, 15)
        worksheet.set_column(5, 5, 15)
    
    else:
        workbook.close()
        raise HTTPException(status_code=400, detail=f"Unknown report type: {report_type}")
    
    workbook.close()
    buffer.seek(0)
    
    filename = f"{report_type}_report_{now.strftime('%Y%m%d_%H%M%S')}.xlsx"
    
    return StreamingResponse(
        buffer,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )
