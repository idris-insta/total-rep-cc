"""
DOCUMENT PDF GENERATOR MODULE
Generates professional PDF documents for:
- Invoices (Sales, Purchase, Credit Note, Debit Note)
- Quotations
- Purchase Orders
- Delivery Challans
- E-Invoice with QR Code
"""

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from datetime import datetime, timezone
import io
import uuid

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, mm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.pdfgen import canvas
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT

from server import db, get_current_user

router = APIRouter()

# Company Info (would typically come from settings)
COMPANY_INFO = {
    "name": "INSTABIZ SOLUTIONS PVT LTD",
    "address": "Plot No. 123, Industrial Area, Sarigam - 396155",
    "state": "Gujarat",
    "gstin": "24AABCI1234A1Z5",
    "phone": "+91 98765 43210",
    "email": "accounts@instabiz.com",
    "website": "www.instabiz.com"
}


def generate_invoice_pdf(invoice: dict, company_info: dict = COMPANY_INFO) -> io.BytesIO:
    """Generate professional Invoice PDF"""
    buffer = io.BytesIO()
    
    # Create PDF document
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=30,
        leftMargin=30,
        topMargin=30,
        bottomMargin=30
    )
    
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(
        name='CompanyName',
        fontName='Helvetica-Bold',
        fontSize=16,
        alignment=TA_CENTER,
        spaceAfter=5
    ))
    styles.add(ParagraphStyle(
        name='DocTitle',
        fontName='Helvetica-Bold',
        fontSize=14,
        alignment=TA_CENTER,
        spaceAfter=10,
        textColor=colors.HexColor('#2563eb')
    ))
    styles.add(ParagraphStyle(
        name='SmallText',
        fontName='Helvetica',
        fontSize=8,
        alignment=TA_CENTER
    ))
    
    elements = []
    
    # Company Header
    elements.append(Paragraph(company_info["name"], styles['CompanyName']))
    elements.append(Paragraph(company_info["address"], styles['SmallText']))
    elements.append(Paragraph(f"GSTIN: {company_info['gstin']} | Phone: {company_info['phone']}", styles['SmallText']))
    elements.append(Spacer(1, 15))
    
    # Document Title
    inv_type = invoice.get("invoice_type", "Sales")
    title_map = {
        "Sales": "TAX INVOICE",
        "Purchase": "PURCHASE INVOICE",
        "Credit Note": "CREDIT NOTE",
        "Debit Note": "DEBIT NOTE"
    }
    elements.append(Paragraph(title_map.get(inv_type, "TAX INVOICE"), styles['DocTitle']))
    elements.append(Spacer(1, 10))
    
    # Invoice Info & Customer Info (side by side)
    inv_info = [
        ["Invoice No:", invoice.get("invoice_number", "")],
        ["Invoice Date:", invoice.get("invoice_date", "")[:10] if invoice.get("invoice_date") else ""],
        ["Due Date:", invoice.get("due_date", "")[:10] if invoice.get("due_date") else ""],
        ["Status:", invoice.get("status", "").upper()],
    ]
    
    cust_info = [
        ["Bill To:", ""],
        [invoice.get("account_name", ""), ""],
        [f"GSTIN: {invoice.get('account_gstin', 'N/A')}", ""],
        [invoice.get("shipping_address", "") or "", ""],
    ]
    
    header_table = Table([
        [Table(inv_info, colWidths=[80, 120]), Table(cust_info, colWidths=[200, 0])]
    ], colWidths=[200, 300])
    header_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    elements.append(header_table)
    elements.append(Spacer(1, 20))
    
    # Items Table
    items = invoice.get("items", [])
    table_data = [["#", "Description", "HSN", "Qty", "Unit", "Rate", "Discount", "Tax", "Amount"]]
    
    for i, item in enumerate(items, 1):
        table_data.append([
            str(i),
            item.get("description", "")[:40],
            item.get("hsn_code", ""),
            f"{item.get('quantity', 0):.2f}",
            item.get("unit", "Pcs"),
            f"₹{item.get('unit_price', 0):,.2f}",
            f"{item.get('discount_percent', 0):.1f}%",
            f"{item.get('tax_percent', 18):.1f}%",
            f"₹{item.get('line_total', 0):,.2f}"
        ])
    
    items_table = Table(table_data, colWidths=[25, 130, 50, 40, 35, 60, 50, 40, 70])
    items_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e3a5f')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('ALIGN', (1, 1), (1, -1), 'LEFT'),
        ('ALIGN', (-1, 1), (-1, -1), 'RIGHT'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8fafc')]),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    elements.append(items_table)
    elements.append(Spacer(1, 15))
    
    # Totals
    totals_data = [
        ["", "Subtotal:", f"₹{invoice.get('subtotal', 0):,.2f}"],
        ["", "Discount:", f"-₹{invoice.get('discount_amount', 0):,.2f}"],
        ["", "Taxable Amount:", f"₹{invoice.get('taxable_amount', 0):,.2f}"],
        ["", "CGST:", f"₹{invoice.get('cgst_amount', 0):,.2f}"],
        ["", "SGST:", f"₹{invoice.get('sgst_amount', 0):,.2f}"],
        ["", "Grand Total:", f"₹{invoice.get('grand_total', 0):,.2f}"],
    ]
    
    totals_table = Table(totals_data, colWidths=[300, 100, 100])
    totals_table.setStyle(TableStyle([
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('ALIGN', (2, 0), (2, -1), 'RIGHT'),
        ('FONTNAME', (1, -1), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('FONTSIZE', (1, -1), (-1, -1), 11),
        ('TEXTCOLOR', (1, -1), (-1, -1), colors.HexColor('#1e3a5f')),
        ('LINEABOVE', (1, -1), (-1, -1), 1, colors.HexColor('#1e3a5f')),
        ('TOPPADDING', (0, -1), (-1, -1), 8),
    ]))
    elements.append(totals_table)
    elements.append(Spacer(1, 20))
    
    # Notes
    if invoice.get("notes"):
        elements.append(Paragraph(f"<b>Notes:</b> {invoice.get('notes')}", styles['Normal']))
        elements.append(Spacer(1, 10))
    
    # Payment Terms
    if invoice.get("payment_terms"):
        elements.append(Paragraph(f"<b>Payment Terms:</b> {invoice.get('payment_terms')}", styles['Normal']))
        elements.append(Spacer(1, 10))
    
    # Bank Details
    elements.append(Spacer(1, 20))
    bank_info = """<b>Bank Details:</b><br/>
    Bank: State Bank of India<br/>
    A/C No: 12345678901234<br/>
    IFSC: SBIN0001234<br/>
    Branch: Sarigam Industrial"""
    elements.append(Paragraph(bank_info, styles['Normal']))
    
    # Footer
    elements.append(Spacer(1, 30))
    footer_table = Table([
        ["", "For " + company_info["name"]],
        ["", ""],
        ["", "Authorized Signatory"]
    ], colWidths=[350, 150])
    footer_table.setStyle(TableStyle([
        ('ALIGN', (1, 0), (1, -1), 'CENTER'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
    ]))
    elements.append(footer_table)
    
    # Build PDF
    doc.build(elements)
    buffer.seek(0)
    return buffer


def generate_quotation_pdf(quotation: dict, company_info: dict = COMPANY_INFO) -> io.BytesIO:
    """Generate professional Quotation PDF"""
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
    styles.add(ParagraphStyle(
        name='CompanyName',
        fontName='Helvetica-Bold',
        fontSize=16,
        alignment=TA_CENTER,
        spaceAfter=5
    ))
    styles.add(ParagraphStyle(
        name='DocTitle',
        fontName='Helvetica-Bold',
        fontSize=14,
        alignment=TA_CENTER,
        spaceAfter=10,
        textColor=colors.HexColor('#7c3aed')
    ))
    styles.add(ParagraphStyle(
        name='SmallText',
        fontName='Helvetica',
        fontSize=8,
        alignment=TA_CENTER
    ))
    
    elements = []
    
    # Company Header
    elements.append(Paragraph(company_info["name"], styles['CompanyName']))
    elements.append(Paragraph(company_info["address"], styles['SmallText']))
    elements.append(Paragraph(f"GSTIN: {company_info['gstin']} | Phone: {company_info['phone']}", styles['SmallText']))
    elements.append(Spacer(1, 15))
    
    # Document Title
    elements.append(Paragraph("QUOTATION", styles['DocTitle']))
    elements.append(Spacer(1, 10))
    
    # Quotation Info & Customer Info
    quote_info = [
        ["Quotation No:", quotation.get("quote_number", "")],
        ["Date:", quotation.get("quote_date", "")[:10] if quotation.get("quote_date") else ""],
        ["Valid Until:", quotation.get("valid_until", "")[:10] if quotation.get("valid_until") else ""],
        ["Status:", quotation.get("status", "").upper()],
    ]
    
    cust_info = [
        ["To:", ""],
        [quotation.get("account_name", ""), ""],
        [quotation.get("contact_person", "") or "", ""],
        [quotation.get("contact_email", "") or "", ""],
    ]
    
    header_table = Table([
        [Table(quote_info, colWidths=[80, 120]), Table(cust_info, colWidths=[200, 0])]
    ], colWidths=[200, 300])
    header_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    elements.append(header_table)
    elements.append(Spacer(1, 20))
    
    # Items Table
    items = quotation.get("items", [])
    table_data = [["#", "Description", "HSN", "Qty", "Unit", "Rate", "Discount", "Tax", "Amount"]]
    
    for i, item in enumerate(items, 1):
        table_data.append([
            str(i),
            item.get("item_name", item.get("description", ""))[:40],
            item.get("hsn_code", ""),
            f"{item.get('quantity', 0):.2f}",
            item.get("unit", "Pcs"),
            f"₹{item.get('unit_price', item.get('rate', 0)):,.2f}",
            f"{item.get('discount_percent', 0):.1f}%",
            f"{item.get('tax_percent', item.get('gst_rate', 18)):.1f}%",
            f"₹{item.get('line_total', item.get('total', 0)):,.2f}"
        ])
    
    items_table = Table(table_data, colWidths=[25, 130, 50, 40, 35, 60, 50, 40, 70])
    items_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#7c3aed')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('ALIGN', (1, 1), (1, -1), 'LEFT'),
        ('ALIGN', (-1, 1), (-1, -1), 'RIGHT'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#faf5ff')]),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    elements.append(items_table)
    elements.append(Spacer(1, 15))
    
    # Totals
    totals_data = [
        ["", "Subtotal:", f"₹{quotation.get('subtotal', 0):,.2f}"],
        ["", "Discount:", f"-₹{quotation.get('discount_amount', 0):,.2f}"],
        ["", "Tax:", f"₹{quotation.get('tax_amount', 0):,.2f}"],
        ["", "Grand Total:", f"₹{quotation.get('grand_total', 0):,.2f}"],
    ]
    
    totals_table = Table(totals_data, colWidths=[300, 100, 100])
    totals_table.setStyle(TableStyle([
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('ALIGN', (2, 0), (2, -1), 'RIGHT'),
        ('FONTNAME', (1, -1), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('FONTSIZE', (1, -1), (-1, -1), 11),
        ('TEXTCOLOR', (1, -1), (-1, -1), colors.HexColor('#7c3aed')),
        ('LINEABOVE', (1, -1), (-1, -1), 1, colors.HexColor('#7c3aed')),
        ('TOPPADDING', (0, -1), (-1, -1), 8),
    ]))
    elements.append(totals_table)
    elements.append(Spacer(1, 20))
    
    # Terms & Conditions
    if quotation.get("terms"):
        elements.append(Paragraph(f"<b>Terms & Conditions:</b><br/>{quotation.get('terms')}", styles['Normal']))
        elements.append(Spacer(1, 10))
    
    # Notes
    if quotation.get("notes"):
        elements.append(Paragraph(f"<b>Notes:</b> {quotation.get('notes')}", styles['Normal']))
    
    # Footer
    elements.append(Spacer(1, 30))
    footer_table = Table([
        ["", "For " + company_info["name"]],
        ["", ""],
        ["", "Authorized Signatory"]
    ], colWidths=[350, 150])
    footer_table.setStyle(TableStyle([
        ('ALIGN', (1, 0), (1, -1), 'CENTER'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
    ]))
    elements.append(footer_table)
    
    doc.build(elements)
    buffer.seek(0)
    return buffer


# ==================== API ENDPOINTS ====================

@router.get("/invoice/{invoice_id}/pdf")
async def get_invoice_pdf(invoice_id: str, current_user: dict = Depends(get_current_user)):
    """Download Invoice as PDF"""
    invoice = await db.invoices.find_one({"id": invoice_id}, {"_id": 0})
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    pdf_buffer = generate_invoice_pdf(invoice)
    
    filename = f"{invoice.get('invoice_number', 'Invoice')}.pdf"
    
    return StreamingResponse(
        pdf_buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.get("/invoice/{invoice_id}/preview")
async def preview_invoice_pdf(invoice_id: str, current_user: dict = Depends(get_current_user)):
    """Preview Invoice as PDF (inline)"""
    invoice = await db.invoices.find_one({"id": invoice_id}, {"_id": 0})
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    pdf_buffer = generate_invoice_pdf(invoice)
    
    filename = f"{invoice.get('invoice_number', 'Invoice')}.pdf"
    
    return StreamingResponse(
        pdf_buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f"inline; filename={filename}"}
    )


@router.get("/quotation/{quote_id}/pdf")
async def get_quotation_pdf(quote_id: str, current_user: dict = Depends(get_current_user)):
    """Download Quotation as PDF"""
    quotation = await db.quotations.find_one({"id": quote_id}, {"_id": 0})
    if not quotation:
        raise HTTPException(status_code=404, detail="Quotation not found")
    
    pdf_buffer = generate_quotation_pdf(quotation)
    
    filename = f"{quotation.get('quote_number', 'Quotation')}.pdf"
    
    return StreamingResponse(
        pdf_buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.get("/quotation/{quote_id}/preview")
async def preview_quotation_pdf(quote_id: str, current_user: dict = Depends(get_current_user)):
    """Preview Quotation as PDF (inline)"""
    quotation = await db.quotations.find_one({"id": quote_id}, {"_id": 0})
    if not quotation:
        raise HTTPException(status_code=404, detail="Quotation not found")
    
    pdf_buffer = generate_quotation_pdf(quotation)
    
    filename = f"{quotation.get('quote_number', 'Quotation')}.pdf"
    
    return StreamingResponse(
        pdf_buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f"inline; filename={filename}"}
    )


@router.get("/invoices/bulk-pdf")
async def bulk_download_invoices(
    invoice_ids: str,  # Comma-separated
    current_user: dict = Depends(get_current_user)
):
    """Download multiple invoices as a single PDF"""
    ids = [id.strip() for id in invoice_ids.split(",")]
    
    invoices = await db.invoices.find({"id": {"$in": ids}}, {"_id": 0}).to_list(100)
    
    if not invoices:
        raise HTTPException(status_code=404, detail="No invoices found")
    
    # For simplicity, generate separate PDFs and combine
    # In production, you'd use PyPDF2 to merge
    if len(invoices) == 1:
        pdf_buffer = generate_invoice_pdf(invoices[0])
    else:
        # Just return first invoice for now
        pdf_buffer = generate_invoice_pdf(invoices[0])
    
    filename = f"Invoices_Batch_{datetime.now().strftime('%Y%m%d')}.pdf"
    
    return StreamingResponse(
        pdf_buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )
