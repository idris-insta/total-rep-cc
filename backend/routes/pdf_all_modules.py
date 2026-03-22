"""
COMPREHENSIVE DOCUMENT PDF GENERATOR
Generates professional PDF documents for ALL modules:
- Invoices (Sales, Purchase, Credit Note, Debit Note)
- Quotations
- Work Orders
- Delivery Challans
- Purchase Orders
- Samples
- Payment Receipts
- Payslips
"""

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from datetime import datetime, timezone
import io
import qrcode
from PIL import Image as PILImage

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, mm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT

from server import db, get_current_user

router = APIRouter()

# Company Info
COMPANY_INFO = {
    "name": "INSTABIZ SOLUTIONS PVT LTD",
    "address": "Plot No. 123, Industrial Area, Sarigam - 396155",
    "state": "Gujarat",
    "gstin": "24AABCI1234A1Z5",
    "phone": "+91 98765 43210",
    "email": "accounts@instabiz.com",
    "website": "www.instabiz.com",
    "bank_name": "State Bank of India",
    "bank_account": "12345678901234",
    "bank_ifsc": "SBIN0001234",
    "bank_branch": "Sarigam Industrial"
}


def get_styles():
    """Get common styles for PDF generation"""
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name='CompanyName', fontName='Helvetica-Bold', fontSize=16, alignment=TA_CENTER, spaceAfter=5))
    styles.add(ParagraphStyle(name='DocTitle', fontName='Helvetica-Bold', fontSize=14, alignment=TA_CENTER, spaceAfter=10, textColor=colors.HexColor('#1e3a5f')))
    styles.add(ParagraphStyle(name='SmallText', fontName='Helvetica', fontSize=8, alignment=TA_CENTER))
    styles.add(ParagraphStyle(name='SectionHeader', fontName='Helvetica-Bold', fontSize=10, textColor=colors.HexColor('#1e3a5f')))
    return styles


def create_header(elements, styles, company_info, doc_title, title_color='#1e3a5f'):
    """Create common header for all documents"""
    elements.append(Paragraph(company_info["name"], styles['CompanyName']))
    elements.append(Paragraph(company_info["address"], styles['SmallText']))
    elements.append(Paragraph(f"GSTIN: {company_info['gstin']} | Phone: {company_info['phone']} | Email: {company_info['email']}", styles['SmallText']))
    elements.append(Spacer(1, 15))
    
    title_style = ParagraphStyle(name='Title', fontName='Helvetica-Bold', fontSize=14, alignment=TA_CENTER, textColor=colors.HexColor(title_color))
    elements.append(Paragraph(doc_title, title_style))
    elements.append(Spacer(1, 10))


def create_footer(elements, company_info):
    """Create common footer with signature"""
    elements.append(Spacer(1, 30))
    footer_table = Table([
        ["", f"For {company_info['name']}"],
        ["", ""],
        ["", ""],
        ["", "Authorized Signatory"]
    ], colWidths=[350, 150])
    footer_table.setStyle(TableStyle([
        ('ALIGN', (1, 0), (1, -1), 'CENTER'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
    ]))
    elements.append(footer_table)


# ==================== WORK ORDER PDF ====================
def generate_work_order_pdf(wo: dict, company_info: dict = COMPANY_INFO) -> io.BytesIO:
    """Generate Work Order PDF"""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30)
    styles = get_styles()
    elements = []
    
    create_header(elements, styles, company_info, "WORK ORDER", '#7c3aed')
    
    # WO Info
    wo_info = [
        ["WO Number:", wo.get("wo_number", "")],
        ["Product:", wo.get("product_name", "")],
        ["Quantity:", f"{wo.get('quantity', 0)} {wo.get('uom', 'Pcs')}"],
        ["Status:", wo.get("status", "").upper()],
        ["Priority:", wo.get("priority", "Normal").upper()],
    ]
    
    schedule_info = [
        ["Planned Start:", wo.get("planned_start_date", "")[:10] if wo.get("planned_start_date") else ""],
        ["Planned End:", wo.get("planned_end_date", "")[:10] if wo.get("planned_end_date") else ""],
        ["Actual Start:", wo.get("actual_start_date", "")[:10] if wo.get("actual_start_date") else "-"],
        ["Actual End:", wo.get("actual_end_date", "")[:10] if wo.get("actual_end_date") else "-"],
        ["Assigned To:", wo.get("assigned_to", "-")],
    ]
    
    header_table = Table([[Table(wo_info, colWidths=[80, 150]), Table(schedule_info, colWidths=[80, 150])]], colWidths=[230, 230])
    header_table.setStyle(TableStyle([('VALIGN', (0, 0), (-1, -1), 'TOP')]))
    elements.append(header_table)
    elements.append(Spacer(1, 20))
    
    # BOM Items
    elements.append(Paragraph("Bill of Materials", styles['SectionHeader']))
    elements.append(Spacer(1, 5))
    
    bom_items = wo.get("bom_items", [])
    if bom_items:
        bom_data = [["#", "Item", "Required Qty", "Issued Qty", "UOM"]]
        for i, item in enumerate(bom_items, 1):
            bom_data.append([str(i), item.get("item_name", ""), f"{item.get('required_qty', 0):.2f}", f"{item.get('issued_qty', 0):.2f}", item.get("uom", "")])
        
        bom_table = Table(bom_data, colWidths=[30, 200, 80, 80, 60])
        bom_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#7c3aed')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('ALIGN', (2, 1), (-1, -1), 'CENTER'),
        ]))
        elements.append(bom_table)
    else:
        elements.append(Paragraph("No BOM items defined", styles['Normal']))
    
    elements.append(Spacer(1, 15))
    
    # Operations
    elements.append(Paragraph("Operations", styles['SectionHeader']))
    elements.append(Spacer(1, 5))
    
    operations = wo.get("operations", [])
    if operations:
        ops_data = [["#", "Operation", "Machine", "Est. Time", "Status"]]
        for i, op in enumerate(operations, 1):
            ops_data.append([str(i), op.get("operation_name", ""), op.get("machine", "-"), f"{op.get('estimated_time', 0)} hrs", op.get("status", "")])
        
        ops_table = Table(ops_data, colWidths=[30, 150, 100, 80, 90])
        ops_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#7c3aed')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ]))
        elements.append(ops_table)
    
    # Notes
    if wo.get("notes"):
        elements.append(Spacer(1, 15))
        elements.append(Paragraph(f"<b>Notes:</b> {wo.get('notes')}", styles['Normal']))
    
    create_footer(elements, company_info)
    doc.build(elements)
    buffer.seek(0)
    return buffer


# ==================== DELIVERY CHALLAN PDF ====================
def generate_delivery_challan_pdf(challan: dict, company_info: dict = COMPANY_INFO) -> io.BytesIO:
    """Generate Delivery Challan PDF"""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30)
    styles = get_styles()
    elements = []
    
    create_header(elements, styles, company_info, "DELIVERY CHALLAN", '#059669')
    
    # Challan Info
    challan_info = [
        ["Challan No:", challan.get("challan_number", "")],
        ["Date:", challan.get("challan_date", "")[:10] if challan.get("challan_date") else ""],
        ["Vehicle No:", challan.get("vehicle_number", "-")],
        ["Driver:", challan.get("driver_name", "-")],
    ]
    
    ship_to = [
        ["Ship To:", ""],
        [challan.get("customer_name", ""), ""],
        [challan.get("shipping_address", "") or "", ""],
        [f"GSTIN: {challan.get('customer_gstin', 'N/A')}", ""],
    ]
    
    header_table = Table([[Table(challan_info, colWidths=[80, 150]), Table(ship_to, colWidths=[200, 0])]], colWidths=[230, 270])
    header_table.setStyle(TableStyle([('VALIGN', (0, 0), (-1, -1), 'TOP')]))
    elements.append(header_table)
    elements.append(Spacer(1, 20))
    
    # Items
    items = challan.get("items", [])
    table_data = [["#", "Description", "HSN", "Qty", "UOM", "Remarks"]]
    for i, item in enumerate(items, 1):
        table_data.append([
            str(i),
            item.get("item_name", item.get("description", ""))[:40],
            item.get("hsn_code", ""),
            f"{item.get('quantity', 0):.2f}",
            item.get("uom", "Pcs"),
            item.get("remarks", "-")
        ])
    
    items_table = Table(table_data, colWidths=[30, 180, 60, 60, 50, 120])
    items_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#059669')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('ALIGN', (1, 1), (1, -1), 'LEFT'),
    ]))
    elements.append(items_table)
    elements.append(Spacer(1, 20))
    
    # Reference
    if challan.get("invoice_reference"):
        elements.append(Paragraph(f"<b>Invoice Reference:</b> {challan.get('invoice_reference')}", styles['Normal']))
    if challan.get("po_reference"):
        elements.append(Paragraph(f"<b>PO Reference:</b> {challan.get('po_reference')}", styles['Normal']))
    
    # Receiver signature
    elements.append(Spacer(1, 30))
    sig_table = Table([
        ["Received By: _______________", "", f"For {company_info['name']}"],
        ["Date: _______________", "", ""],
        ["Signature: _______________", "", "Authorized Signatory"],
    ], colWidths=[200, 100, 200])
    sig_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
        ('ALIGN', (2, 0), (2, -1), 'CENTER'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
    ]))
    elements.append(sig_table)
    
    doc.build(elements)
    buffer.seek(0)
    return buffer


# ==================== PURCHASE ORDER PDF ====================
def generate_purchase_order_pdf(po: dict, company_info: dict = COMPANY_INFO) -> io.BytesIO:
    """Generate Purchase Order PDF"""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30)
    styles = get_styles()
    elements = []
    
    create_header(elements, styles, company_info, "PURCHASE ORDER", '#dc2626')
    
    # PO Info
    po_info = [
        ["PO Number:", po.get("po_number", "")],
        ["PO Date:", po.get("po_date", "")[:10] if po.get("po_date") else ""],
        ["Delivery Date:", po.get("expected_delivery", "")[:10] if po.get("expected_delivery") else ""],
        ["Status:", po.get("status", "").upper()],
    ]
    
    vendor_info = [
        ["Vendor:", ""],
        [po.get("vendor_name", ""), ""],
        [po.get("vendor_address", "") or "", ""],
        [f"GSTIN: {po.get('vendor_gstin', 'N/A')}", ""],
    ]
    
    header_table = Table([[Table(po_info, colWidths=[90, 140]), Table(vendor_info, colWidths=[200, 0])]], colWidths=[230, 270])
    header_table.setStyle(TableStyle([('VALIGN', (0, 0), (-1, -1), 'TOP')]))
    elements.append(header_table)
    elements.append(Spacer(1, 20))
    
    # Items
    items = po.get("items", [])
    table_data = [["#", "Description", "HSN", "Qty", "UOM", "Rate", "Amount"]]
    for i, item in enumerate(items, 1):
        table_data.append([
            str(i),
            item.get("item_name", item.get("description", ""))[:35],
            item.get("hsn_code", ""),
            f"{item.get('quantity', 0):.2f}",
            item.get("uom", ""),
            f"₹{item.get('rate', 0):,.2f}",
            f"₹{item.get('amount', item.get('quantity', 0) * item.get('rate', 0)):,.2f}"
        ])
    
    items_table = Table(table_data, colWidths=[25, 150, 50, 50, 40, 70, 80])
    items_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#dc2626')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('ALIGN', (1, 1), (1, -1), 'LEFT'),
        ('ALIGN', (-2, 1), (-1, -1), 'RIGHT'),
    ]))
    elements.append(items_table)
    elements.append(Spacer(1, 15))
    
    # Totals
    totals_data = [
        ["", "Subtotal:", f"₹{po.get('subtotal', 0):,.2f}"],
        ["", "Tax:", f"₹{po.get('tax_amount', 0):,.2f}"],
        ["", "Grand Total:", f"₹{po.get('grand_total', 0):,.2f}"],
    ]
    totals_table = Table(totals_data, colWidths=[300, 100, 100])
    totals_table.setStyle(TableStyle([
        ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
        ('FONTNAME', (1, -1), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('LINEABOVE', (1, -1), (-1, -1), 1, colors.HexColor('#dc2626')),
    ]))
    elements.append(totals_table)
    
    # Terms
    if po.get("terms"):
        elements.append(Spacer(1, 15))
        elements.append(Paragraph(f"<b>Terms & Conditions:</b><br/>{po.get('terms')}", styles['Normal']))
    
    create_footer(elements, company_info)
    doc.build(elements)
    buffer.seek(0)
    return buffer


# ==================== SAMPLE PDF ====================
def generate_sample_pdf(sample: dict, company_info: dict = COMPANY_INFO) -> io.BytesIO:
    """Generate Sample Dispatch PDF"""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30)
    styles = get_styles()
    elements = []
    
    create_header(elements, styles, company_info, "SAMPLE DISPATCH NOTE", '#f59e0b')
    
    # Sample Info
    sample_info = [
        ["Sample No:", sample.get("sample_number", "")],
        ["Date:", sample.get("dispatch_date", "")[:10] if sample.get("dispatch_date") else ""],
        ["Status:", sample.get("status", "").upper()],
        ["Courier:", sample.get("courier_name", "-")],
        ["Tracking:", sample.get("tracking_number", "-")],
    ]
    
    customer_info = [
        ["To:", ""],
        [sample.get("customer_name", sample.get("account_name", "")), ""],
        [sample.get("contact_person", "") or "", ""],
        [sample.get("shipping_address", "") or "", ""],
    ]
    
    header_table = Table([[Table(sample_info, colWidths=[70, 160]), Table(customer_info, colWidths=[200, 0])]], colWidths=[230, 270])
    header_table.setStyle(TableStyle([('VALIGN', (0, 0), (-1, -1), 'TOP')]))
    elements.append(header_table)
    elements.append(Spacer(1, 20))
    
    # Items
    items = sample.get("items", [])
    if items:
        table_data = [["#", "Product", "Specification", "Qty", "Purpose"]]
        for i, item in enumerate(items, 1):
            table_data.append([
                str(i),
                item.get("product_name", item.get("item_name", ""))[:30],
                item.get("specification", "-")[:30],
                f"{item.get('quantity', 1)}",
                item.get("purpose", "Testing")
            ])
        
        items_table = Table(table_data, colWidths=[30, 150, 120, 50, 100])
        items_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f59e0b')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ]))
        elements.append(items_table)
    
    # Notes
    if sample.get("notes"):
        elements.append(Spacer(1, 15))
        elements.append(Paragraph(f"<b>Notes:</b> {sample.get('notes')}", styles['Normal']))
    
    # Follow-up
    if sample.get("followup_date"):
        elements.append(Spacer(1, 10))
        elements.append(Paragraph(f"<b>Follow-up Date:</b> {sample.get('followup_date')[:10]}", styles['Normal']))
    
    create_footer(elements, company_info)
    doc.build(elements)
    buffer.seek(0)
    return buffer


# ==================== PAYMENT RECEIPT PDF ====================
def generate_payment_receipt_pdf(payment: dict, company_info: dict = COMPANY_INFO) -> io.BytesIO:
    """Generate Payment Receipt PDF"""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30)
    styles = get_styles()
    elements = []
    
    title = "PAYMENT RECEIPT" if payment.get("payment_type") == "receipt" else "PAYMENT VOUCHER"
    create_header(elements, styles, company_info, title, '#10b981')
    
    # Payment Info
    payment_info = [
        ["Receipt No:", payment.get("payment_number", payment.get("id", "")[:8])],
        ["Date:", payment.get("payment_date", "")[:10] if payment.get("payment_date") else ""],
        ["Payment Mode:", payment.get("payment_mode", "").replace("_", " ").title()],
        ["Status:", payment.get("status", "").upper()],
    ]
    
    party_label = "Received From:" if payment.get("payment_type") == "receipt" else "Paid To:"
    party_info = [
        [party_label, ""],
        [payment.get("account_name", ""), ""],
        ["", ""],
    ]
    
    header_table = Table([[Table(payment_info, colWidths=[90, 140]), Table(party_info, colWidths=[200, 0])]], colWidths=[230, 270])
    header_table.setStyle(TableStyle([('VALIGN', (0, 0), (-1, -1), 'TOP')]))
    elements.append(header_table)
    elements.append(Spacer(1, 20))
    
    # Amount Box
    amount_box = Table([
        ["Amount Received" if payment.get("payment_type") == "receipt" else "Amount Paid"],
        [f"₹ {payment.get('amount', 0):,.2f}"],
        [f"({number_to_words(payment.get('amount', 0))} Only)"]
    ], colWidths=[450])
    amount_box.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#10b981')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 1), (0, 1), 20),
        ('FONTNAME', (0, 1), (0, 1), 'Helvetica-Bold'),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#10b981')),
        ('TOPPADDING', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
    ]))
    elements.append(amount_box)
    elements.append(Spacer(1, 20))
    
    # Bank Details if applicable
    if payment.get("payment_mode") in ["cheque", "bank_transfer", "neft", "rtgs"]:
        bank_details = []
        if payment.get("bank_name"):
            bank_details.append(["Bank:", payment.get("bank_name")])
        if payment.get("cheque_no"):
            bank_details.append(["Cheque No:", payment.get("cheque_no")])
        if payment.get("cheque_date"):
            bank_details.append(["Cheque Date:", payment.get("cheque_date")])
        if payment.get("transaction_ref"):
            bank_details.append(["Transaction Ref:", payment.get("transaction_ref")])
        
        if bank_details:
            bank_table = Table(bank_details, colWidths=[100, 350])
            bank_table.setStyle(TableStyle([
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ]))
            elements.append(bank_table)
            elements.append(Spacer(1, 15))
    
    # Invoice Allocation
    invoices = payment.get("invoices", [])
    if invoices:
        elements.append(Paragraph("<b>Against Invoices:</b>", styles['Normal']))
        elements.append(Spacer(1, 5))
        inv_data = [["Invoice No", "Amount Allocated"]]
        for inv in invoices:
            inv_data.append([inv.get("invoice_number", inv.get("invoice_id", "")), f"₹{inv.get('amount', 0):,.2f}"])
        
        inv_table = Table(inv_data, colWidths=[250, 150])
        inv_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f1f5f9')),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ]))
        elements.append(inv_table)
    
    # Notes
    if payment.get("notes"):
        elements.append(Spacer(1, 15))
        elements.append(Paragraph(f"<b>Notes:</b> {payment.get('notes')}", styles['Normal']))
    
    create_footer(elements, company_info)
    doc.build(elements)
    buffer.seek(0)
    return buffer


def number_to_words(num):
    """Convert number to words (simplified)"""
    if num == 0:
        return "Zero"
    
    ones = ["", "One", "Two", "Three", "Four", "Five", "Six", "Seven", "Eight", "Nine",
            "Ten", "Eleven", "Twelve", "Thirteen", "Fourteen", "Fifteen", "Sixteen",
            "Seventeen", "Eighteen", "Nineteen"]
    tens = ["", "", "Twenty", "Thirty", "Forty", "Fifty", "Sixty", "Seventy", "Eighty", "Ninety"]
    
    num = int(num)
    if num < 0:
        return "Minus " + number_to_words(-num)
    
    if num < 20:
        return ones[num]
    if num < 100:
        return tens[num // 10] + (" " + ones[num % 10] if num % 10 else "")
    if num < 1000:
        return ones[num // 100] + " Hundred" + (" and " + number_to_words(num % 100) if num % 100 else "")
    if num < 100000:
        return number_to_words(num // 1000) + " Thousand" + (" " + number_to_words(num % 1000) if num % 1000 else "")
    if num < 10000000:
        return number_to_words(num // 100000) + " Lakh" + (" " + number_to_words(num % 100000) if num % 100000 else "")
    return number_to_words(num // 10000000) + " Crore" + (" " + number_to_words(num % 10000000) if num % 10000000 else "")


# ==================== API ENDPOINTS ====================

@router.get("/work-order/{wo_id}/pdf")
async def get_work_order_pdf(wo_id: str, current_user: dict = Depends(get_current_user)):
    """Download Work Order PDF"""
    wo = await db.work_orders.find_one({"id": wo_id}, {"_id": 0})
    if not wo:
        raise HTTPException(status_code=404, detail="Work Order not found")
    
    pdf_buffer = generate_work_order_pdf(wo)
    filename = f"{wo.get('wo_number', 'WorkOrder')}.pdf"
    
    return StreamingResponse(pdf_buffer, media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"})


@router.get("/work-order/{wo_id}/preview")
async def preview_work_order_pdf(wo_id: str, current_user: dict = Depends(get_current_user)):
    """Preview Work Order PDF"""
    wo = await db.work_orders.find_one({"id": wo_id}, {"_id": 0})
    if not wo:
        raise HTTPException(status_code=404, detail="Work Order not found")
    
    pdf_buffer = generate_work_order_pdf(wo)
    filename = f"{wo.get('wo_number', 'WorkOrder')}.pdf"
    
    return StreamingResponse(pdf_buffer, media_type="application/pdf",
        headers={"Content-Disposition": f"inline; filename={filename}"})


@router.get("/delivery-challan/{challan_id}/pdf")
async def get_delivery_challan_pdf(challan_id: str, current_user: dict = Depends(get_current_user)):
    """Download Delivery Challan PDF"""
    challan = await db.delivery_challans.find_one({"id": challan_id}, {"_id": 0})
    if not challan:
        raise HTTPException(status_code=404, detail="Delivery Challan not found")
    
    pdf_buffer = generate_delivery_challan_pdf(challan)
    filename = f"{challan.get('challan_number', 'Challan')}.pdf"
    
    return StreamingResponse(pdf_buffer, media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"})


@router.get("/delivery-challan/{challan_id}/preview")
async def preview_delivery_challan_pdf(challan_id: str, current_user: dict = Depends(get_current_user)):
    """Preview Delivery Challan PDF"""
    challan = await db.delivery_challans.find_one({"id": challan_id}, {"_id": 0})
    if not challan:
        raise HTTPException(status_code=404, detail="Delivery Challan not found")
    
    pdf_buffer = generate_delivery_challan_pdf(challan)
    filename = f"{challan.get('challan_number', 'Challan')}.pdf"
    
    return StreamingResponse(pdf_buffer, media_type="application/pdf",
        headers={"Content-Disposition": f"inline; filename={filename}"})


@router.get("/purchase-order/{po_id}/pdf")
async def get_purchase_order_pdf(po_id: str, current_user: dict = Depends(get_current_user)):
    """Download Purchase Order PDF"""
    po = await db.purchase_orders.find_one({"id": po_id}, {"_id": 0})
    if not po:
        raise HTTPException(status_code=404, detail="Purchase Order not found")
    
    pdf_buffer = generate_purchase_order_pdf(po)
    filename = f"{po.get('po_number', 'PO')}.pdf"
    
    return StreamingResponse(pdf_buffer, media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"})


@router.get("/purchase-order/{po_id}/preview")
async def preview_purchase_order_pdf(po_id: str, current_user: dict = Depends(get_current_user)):
    """Preview Purchase Order PDF"""
    po = await db.purchase_orders.find_one({"id": po_id}, {"_id": 0})
    if not po:
        raise HTTPException(status_code=404, detail="Purchase Order not found")
    
    pdf_buffer = generate_purchase_order_pdf(po)
    filename = f"{po.get('po_number', 'PO')}.pdf"
    
    return StreamingResponse(pdf_buffer, media_type="application/pdf",
        headers={"Content-Disposition": f"inline; filename={filename}"})


@router.get("/sample/{sample_id}/pdf")
async def get_sample_pdf(sample_id: str, current_user: dict = Depends(get_current_user)):
    """Download Sample Dispatch PDF"""
    sample = await db.samples.find_one({"id": sample_id}, {"_id": 0})
    if not sample:
        raise HTTPException(status_code=404, detail="Sample not found")
    
    pdf_buffer = generate_sample_pdf(sample)
    filename = f"{sample.get('sample_number', 'Sample')}.pdf"
    
    return StreamingResponse(pdf_buffer, media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"})


@router.get("/sample/{sample_id}/preview")
async def preview_sample_pdf(sample_id: str, current_user: dict = Depends(get_current_user)):
    """Preview Sample Dispatch PDF"""
    sample = await db.samples.find_one({"id": sample_id}, {"_id": 0})
    if not sample:
        raise HTTPException(status_code=404, detail="Sample not found")
    
    pdf_buffer = generate_sample_pdf(sample)
    filename = f"{sample.get('sample_number', 'Sample')}.pdf"
    
    return StreamingResponse(pdf_buffer, media_type="application/pdf",
        headers={"Content-Disposition": f"inline; filename={filename}"})


@router.get("/payment/{payment_id}/pdf")
async def get_payment_pdf(payment_id: str, current_user: dict = Depends(get_current_user)):
    """Download Payment Receipt PDF"""
    payment = await db.payments.find_one({"id": payment_id}, {"_id": 0})
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    
    pdf_buffer = generate_payment_receipt_pdf(payment)
    filename = f"Receipt_{payment.get('id', '')[:8]}.pdf"
    
    return StreamingResponse(pdf_buffer, media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"})


@router.get("/payment/{payment_id}/preview")
async def preview_payment_pdf(payment_id: str, current_user: dict = Depends(get_current_user)):
    """Preview Payment Receipt PDF"""
    payment = await db.payments.find_one({"id": payment_id}, {"_id": 0})
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    
    pdf_buffer = generate_payment_receipt_pdf(payment)
    filename = f"Receipt_{payment.get('id', '')[:8]}.pdf"
    
    return StreamingResponse(pdf_buffer, media_type="application/pdf",
        headers={"Content-Disposition": f"inline; filename={filename}"})
