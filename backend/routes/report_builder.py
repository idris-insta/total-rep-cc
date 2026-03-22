"""
Advanced Report Builder Module
Features:
- Custom report creation with drag-drop columns
- Multiple data sources (CRM, Inventory, Accounts, HRMS, Production)
- Flexible filtering and grouping
- Save and share reports
- Export to PDF/Excel
- Schedule email reports
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
import uuid
import io

from server import db, get_current_user
from models.schemas import ReportCreate, ReportUpdate, ReportColumnDef, ReportFilterDef

# PDF and Excel
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
import xlsxwriter

router = APIRouter()

# Module configurations
MODULE_CONFIGS = {
    "crm_leads": {
        "collection": "leads",
        "fields": {
            "company_name": {"label": "Company Name", "type": "text"},
            "contact_person": {"label": "Contact Person", "type": "text"},
            "email": {"label": "Email", "type": "text"},
            "phone": {"label": "Phone", "type": "text"},
            "city": {"label": "City", "type": "text"},
            "state": {"label": "State", "type": "text"},
            "status": {"label": "Status", "type": "text"},
            "source": {"label": "Source", "type": "text"},
            "assigned_to": {"label": "Assigned To", "type": "text"},
            "estimated_value": {"label": "Estimated Value", "type": "currency"},
            "created_at": {"label": "Created Date", "type": "date"},
        }
    },
    "crm_accounts": {
        "collection": "accounts",
        "fields": {
            "account_name": {"label": "Account Name", "type": "text"},
            "account_type": {"label": "Type", "type": "text"},
            "contact_person": {"label": "Contact Person", "type": "text"},
            "city": {"label": "City", "type": "text"},
            "state": {"label": "State", "type": "text"},
            "gstin": {"label": "GSTIN", "type": "text"},
            "credit_limit": {"label": "Credit Limit", "type": "currency"},
            "outstanding_balance": {"label": "Outstanding", "type": "currency"},
            "is_customer": {"label": "Is Customer", "type": "boolean"},
            "is_vendor": {"label": "Is Vendor", "type": "boolean"},
        }
    },
    "inventory_items": {
        "collection": "items",
        "fields": {
            "item_code": {"label": "Item Code", "type": "text"},
            "item_name": {"label": "Item Name", "type": "text"},
            "category": {"label": "Category", "type": "text"},
            "item_type": {"label": "Type", "type": "text"},
            "hsn_code": {"label": "HSN Code", "type": "text"},
            "uom": {"label": "UOM", "type": "text"},
            "current_stock": {"label": "Current Stock", "type": "number"},
            "standard_cost": {"label": "Cost", "type": "currency"},
            "selling_price": {"label": "Selling Price", "type": "currency"},
            "reorder_level": {"label": "Reorder Level", "type": "number"},
        }
    },
    "sales_invoices": {
        "collection": "invoices",
        "fields": {
            "invoice_number": {"label": "Invoice #", "type": "text"},
            "invoice_date": {"label": "Date", "type": "date"},
            "account_name": {"label": "Customer", "type": "text"},
            "subtotal": {"label": "Subtotal", "type": "currency"},
            "total_tax": {"label": "Tax", "type": "currency"},
            "grand_total": {"label": "Grand Total", "type": "currency"},
            "status": {"label": "Status", "type": "text"},
            "payment_status": {"label": "Payment Status", "type": "text"},
        },
        "filter": {"invoice_type": "Sales"}
    },
    "purchase_orders": {
        "collection": "purchase_orders",
        "fields": {
            "po_number": {"label": "PO #", "type": "text"},
            "order_date": {"label": "Date", "type": "date"},
            "vendor_name": {"label": "Vendor", "type": "text"},
            "subtotal": {"label": "Subtotal", "type": "currency"},
            "total_tax": {"label": "Tax", "type": "currency"},
            "grand_total": {"label": "Grand Total", "type": "currency"},
            "status": {"label": "Status", "type": "text"},
        }
    },
    "hrms_employees": {
        "collection": "employees",
        "fields": {
            "employee_code": {"label": "Emp Code", "type": "text"},
            "name": {"label": "Name", "type": "text"},
            "department": {"label": "Department", "type": "text"},
            "designation": {"label": "Designation", "type": "text"},
            "location": {"label": "Location", "type": "text"},
            "date_of_joining": {"label": "Joining Date", "type": "date"},
            "basic_salary": {"label": "Basic Salary", "type": "currency"},
        }
    },
    "production_orders": {
        "collection": "production_orders",
        "fields": {
            "order_number": {"label": "Order #", "type": "text"},
            "product_name": {"label": "Product", "type": "text"},
            "quantity": {"label": "Quantity", "type": "number"},
            "status": {"label": "Status", "type": "text"},
            "planned_start_date": {"label": "Start Date", "type": "date"},
            "planned_end_date": {"label": "End Date", "type": "date"},
            "produced_quantity": {"label": "Produced", "type": "number"},
        }
    }
}


# ==================== REPORT CRUD ====================
@router.get("/modules")
async def get_available_modules(current_user: dict = Depends(get_current_user)):
    """Get available modules and their fields for report building"""
    modules = []
    for key, config in MODULE_CONFIGS.items():
        modules.append({
            "id": key,
            "name": key.replace("_", " ").title(),
            "fields": [
                {"field": f, "label": v["label"], "type": v["type"]}
                for f, v in config["fields"].items()
            ]
        })
    return modules


@router.post("/reports")
async def create_report(report: ReportCreate, current_user: dict = Depends(get_current_user)):
    """Create a new custom report"""
    report_id = str(uuid.uuid4())
    
    report_doc = {
        "id": report_id,
        "name": report.name,
        "description": report.description,
        "module": report.module,
        "columns": [col.model_dump() for col in report.columns],
        "filters": [f.model_dump() for f in report.filters] if report.filters else [],
        "group_by": report.group_by,
        "order_by": report.order_by,
        "order_direction": report.order_direction,
        "is_public": report.is_public,
        "is_active": True,
        "created_by": current_user['id'],
        "created_by_name": current_user.get('name', current_user.get('email')),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "run_count": 0
    }
    
    await db.custom_reports.insert_one(report_doc)
    return {k: v for k, v in report_doc.items() if k != '_id'}


@router.get("/reports")
async def get_reports(current_user: dict = Depends(get_current_user)):
    """Get all reports (user's own + public)"""
    query = {
        "$or": [
            {"created_by": current_user['id']},
            {"is_public": True}
        ],
        "is_active": True
    }
    
    reports = await db.custom_reports.find(query, {"_id": 0}).sort("updated_at", -1).to_list(100)
    return reports


@router.get("/reports/{report_id}")
async def get_report(report_id: str, current_user: dict = Depends(get_current_user)):
    """Get report details"""
    report = await db.custom_reports.find_one({
        "id": report_id,
        "$or": [
            {"created_by": current_user['id']},
            {"is_public": True}
        ]
    }, {"_id": 0})
    
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    
    return report


@router.put("/reports/{report_id}")
async def update_report(
    report_id: str,
    updates: ReportUpdate,
    current_user: dict = Depends(get_current_user)
):
    """Update a report"""
    report = await db.custom_reports.find_one({
        "id": report_id,
        "created_by": current_user['id']
    })
    
    if not report:
        raise HTTPException(status_code=403, detail="Not authorized to update this report")
    
    update_data = {k: v for k, v in updates.model_dump().items() if v is not None}
    if 'columns' in update_data:
        update_data['columns'] = [c.model_dump() if hasattr(c, 'model_dump') else c for c in update_data['columns']]
    if 'filters' in update_data:
        update_data['filters'] = [f.model_dump() if hasattr(f, 'model_dump') else f for f in update_data['filters']]
    
    update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
    
    await db.custom_reports.update_one({"id": report_id}, {"$set": update_data})
    return {"message": "Report updated"}


@router.delete("/reports/{report_id}")
async def delete_report(report_id: str, current_user: dict = Depends(get_current_user)):
    """Delete a report"""
    report = await db.custom_reports.find_one({
        "id": report_id,
        "created_by": current_user['id']
    })
    
    if not report:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    await db.custom_reports.update_one(
        {"id": report_id},
        {"$set": {"is_active": False, "deleted_at": datetime.now(timezone.utc).isoformat()}}
    )
    return {"message": "Report deleted"}


# ==================== REPORT EXECUTION ====================
@router.post("/reports/{report_id}/run")
async def run_report(
    report_id: str,
    limit: int = Query(default=500, le=5000),
    current_user: dict = Depends(get_current_user)
):
    """Execute a report and return data"""
    report = await db.custom_reports.find_one({
        "id": report_id,
        "$or": [
            {"created_by": current_user['id']},
            {"is_public": True}
        ]
    }, {"_id": 0})
    
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    
    module_config = MODULE_CONFIGS.get(report['module'])
    if not module_config:
        raise HTTPException(status_code=400, detail=f"Unknown module: {report['module']}")
    
    collection = db[module_config['collection']]
    
    # Build query from filters
    query = module_config.get('filter', {}).copy()
    
    for filter_def in report.get('filters', []):
        field = filter_def['field']
        op = filter_def['operator']
        value = filter_def['value']
        
        if op == 'eq':
            query[field] = value
        elif op == 'ne':
            query[field] = {"$ne": value}
        elif op == 'gt':
            query[field] = {"$gt": value}
        elif op == 'gte':
            query[field] = {"$gte": value}
        elif op == 'lt':
            query[field] = {"$lt": value}
        elif op == 'lte':
            query[field] = {"$lte": value}
        elif op == 'contains':
            query[field] = {"$regex": value, "$options": "i"}
        elif op == 'in':
            query[field] = {"$in": value if isinstance(value, list) else [value]}
        elif op == 'between':
            query[field] = {"$gte": value, "$lte": filter_def.get('value2', value)}
    
    # Build projection
    projection = {"_id": 0}
    for col in report.get('columns', []):
        projection[col['field']] = 1
    
    # Build sort
    sort_field = report.get('order_by') or 'created_at'
    sort_dir = 1 if report.get('order_direction') == 'asc' else -1
    
    # Execute query
    data = await collection.find(query, projection).sort(sort_field, sort_dir).limit(limit).to_list(limit)
    
    # Update run count
    await db.custom_reports.update_one(
        {"id": report_id},
        {"$inc": {"run_count": 1}, "$set": {"last_run_at": datetime.now(timezone.utc).isoformat()}}
    )
    
    # Calculate aggregations if needed
    aggregations = {}
    for col in report.get('columns', []):
        if col.get('aggregation'):
            field = col['field']
            agg = col['aggregation']
            values = [d.get(field, 0) for d in data if d.get(field) is not None]
            
            if agg == 'sum':
                aggregations[field] = sum(values)
            elif agg == 'avg':
                aggregations[field] = sum(values) / len(values) if values else 0
            elif agg == 'count':
                aggregations[field] = len(values)
            elif agg == 'min':
                aggregations[field] = min(values) if values else 0
            elif agg == 'max':
                aggregations[field] = max(values) if values else 0
    
    return {
        "report": report,
        "data": data,
        "total_rows": len(data),
        "aggregations": aggregations
    }


# ==================== EXPORT ====================
@router.get("/reports/{report_id}/export/excel")
async def export_report_excel(
    report_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Export report to Excel"""
    result = await run_report(report_id, limit=5000, current_user=current_user)
    report = result['report']
    data = result['data']
    
    buffer = io.BytesIO()
    workbook = xlsxwriter.Workbook(buffer, {'in_memory': True})
    worksheet = workbook.add_worksheet(report['name'][:31])
    
    header_format = workbook.add_format({
        'bold': True, 'bg_color': '#334155', 'font_color': 'white', 'border': 1
    })
    cell_format = workbook.add_format({'border': 1})
    money_format = workbook.add_format({'border': 1, 'num_format': '₹#,##0.00'})
    
    # Headers
    columns = report.get('columns', [])
    for col_idx, col in enumerate(columns):
        worksheet.write(0, col_idx, col.get('label', col['field']), header_format)
        worksheet.set_column(col_idx, col_idx, 15)
    
    # Data
    for row_idx, row in enumerate(data, 1):
        for col_idx, col in enumerate(columns):
            field = col['field']
            value = row.get(field, '')
            
            field_type = MODULE_CONFIGS.get(report['module'], {}).get('fields', {}).get(field, {}).get('type', 'text')
            
            if field_type == 'currency':
                worksheet.write_number(row_idx, col_idx, float(value) if value else 0, money_format)
            else:
                worksheet.write(row_idx, col_idx, str(value) if value else '', cell_format)
    
    workbook.close()
    buffer.seek(0)
    
    filename = f"{report['name'].replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.xlsx"
    
    return StreamingResponse(
        buffer,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.get("/reports/{report_id}/export/pdf")
async def export_report_pdf(
    report_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Export report to PDF"""
    result = await run_report(report_id, limit=500, current_user=current_user)
    report = result['report']
    data = result['data']
    
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=landscape(A4), rightMargin=20, leftMargin=20, topMargin=20, bottomMargin=20)
    
    styles = getSampleStyleSheet()
    elements = []
    
    elements.append(Paragraph(report['name'], styles['Heading1']))
    elements.append(Paragraph(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')} | Rows: {len(data)}", styles['Normal']))
    elements.append(Spacer(1, 20))
    
    columns = report.get('columns', [])
    table_data = [[col.get('label', col['field']) for col in columns]]
    
    for row in data[:200]:  # Limit for PDF
        table_data.append([str(row.get(col['field'], ''))[:30] for col in columns])
    
    col_widths = [80] * len(columns)
    table = Table(table_data, colWidths=col_widths)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#334155')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 8),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e1')),
        ('FONTSIZE', (0, 1), (-1, -1), 7),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    
    elements.append(table)
    doc.build(elements)
    buffer.seek(0)
    
    filename = f"{report['name'].replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.pdf"
    
    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )
