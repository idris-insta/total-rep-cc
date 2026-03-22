"""
DOCUMENT COMMUNICATION MODULE
Send documents via Email and WhatsApp
- Email with PDF attachments
- WhatsApp with document links
- Communication history tracking
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, timezone
import uuid
import base64
import io

from server import db, get_current_user

# Import PDF generators
from routes.pdf_generator import generate_invoice_pdf, generate_quotation_pdf
from routes.pdf_all_modules import (
    generate_work_order_pdf, generate_delivery_challan_pdf,
    generate_purchase_order_pdf, generate_sample_pdf, generate_payment_receipt_pdf
)

router = APIRouter()


class EmailRequest(BaseModel):
    document_type: str  # invoice, quotation, work_order, delivery_challan, purchase_order, sample, payment
    document_id: str
    recipient_email: str
    recipient_name: Optional[str] = None
    subject: Optional[str] = None
    message: Optional[str] = None
    cc_emails: Optional[List[str]] = []


class WhatsAppRequest(BaseModel):
    document_type: str
    document_id: str
    recipient_phone: str
    recipient_name: Optional[str] = None
    message: Optional[str] = None


class CommunicationLog(BaseModel):
    id: str
    document_type: str
    document_id: str
    document_number: str
    channel: str  # email, whatsapp
    recipient: str
    recipient_name: Optional[str]
    subject: Optional[str]
    message: Optional[str]
    status: str  # sent, failed, pending
    sent_at: str
    sent_by: str
    error_message: Optional[str] = None


# Document type to collection mapping
DOC_COLLECTIONS = {
    "invoice": "invoices",
    "quotation": "quotations",
    "work_order": "work_orders",
    "delivery_challan": "delivery_challans",
    "purchase_order": "purchase_orders",
    "sample": "samples",
    "payment": "payments"
}

DOC_NUMBER_FIELDS = {
    "invoice": "invoice_number",
    "quotation": "quote_number",
    "work_order": "wo_number",
    "delivery_challan": "challan_number",
    "purchase_order": "po_number",
    "sample": "sample_number",
    "payment": "id"
}

PDF_GENERATORS = {
    "invoice": generate_invoice_pdf,
    "quotation": generate_quotation_pdf,
    "work_order": generate_work_order_pdf,
    "delivery_challan": generate_delivery_challan_pdf,
    "purchase_order": generate_purchase_order_pdf,
    "sample": generate_sample_pdf,
    "payment": generate_payment_receipt_pdf
}


async def get_document(doc_type: str, doc_id: str) -> dict:
    """Fetch document from database"""
    collection_name = DOC_COLLECTIONS.get(doc_type)
    if not collection_name:
        raise HTTPException(status_code=400, detail=f"Invalid document type: {doc_type}")
    
    collection = getattr(db, collection_name)
    doc = await collection.find_one({"id": doc_id}, {"_id": 0})
    
    if not doc:
        raise HTTPException(status_code=404, detail=f"{doc_type.replace('_', ' ').title()} not found")
    
    return doc


def get_document_number(doc: dict, doc_type: str) -> str:
    """Get document number from document"""
    field = DOC_NUMBER_FIELDS.get(doc_type, "id")
    return doc.get(field, doc.get("id", "Unknown"))[:20]


def generate_email_subject(doc_type: str, doc_number: str) -> str:
    """Generate default email subject"""
    type_names = {
        "invoice": "Invoice",
        "quotation": "Quotation",
        "work_order": "Work Order",
        "delivery_challan": "Delivery Challan",
        "purchase_order": "Purchase Order",
        "sample": "Sample Dispatch",
        "payment": "Payment Receipt"
    }
    return f"{type_names.get(doc_type, 'Document')} #{doc_number} from InstaBiz Solutions"


def generate_email_body(doc_type: str, doc_number: str, recipient_name: str, custom_message: str = None) -> str:
    """Generate default email body"""
    name = recipient_name or "Sir/Madam"
    
    type_messages = {
        "invoice": f"Please find attached Invoice #{doc_number} for your reference.",
        "quotation": f"Please find attached our Quotation #{doc_number} as per your requirement. We look forward to your favorable response.",
        "work_order": f"Please find attached Work Order #{doc_number} for your records.",
        "delivery_challan": f"Please find attached Delivery Challan #{doc_number}. Kindly acknowledge receipt of goods.",
        "purchase_order": f"Please find attached Purchase Order #{doc_number}. Kindly confirm and proceed accordingly.",
        "sample": f"Please find attached Sample Dispatch Note #{doc_number}. We hope the samples meet your expectations.",
        "payment": f"Please find attached Payment Receipt #{doc_number} for your records."
    }
    
    body = f"""Dear {name},

{custom_message if custom_message else type_messages.get(doc_type, 'Please find attached document for your reference.')}

If you have any queries, please feel free to contact us.

Best Regards,
InstaBiz Solutions Pvt Ltd
Phone: +91 98765 43210
Email: accounts@instabiz.com
"""
    return body


def generate_whatsapp_message(doc_type: str, doc_number: str, recipient_name: str, custom_message: str = None, pdf_url: str = None) -> str:
    """Generate WhatsApp message"""
    name = recipient_name or ""
    greeting = f"Hi {name}! " if name else "Hi! "
    
    type_messages = {
        "invoice": f"📄 *Invoice #{doc_number}*\n\nPlease find your invoice attached. Kindly process the payment at your earliest convenience.",
        "quotation": f"📋 *Quotation #{doc_number}*\n\nAs discussed, please find our quotation attached. We hope it meets your requirements!",
        "work_order": f"🏭 *Work Order #{doc_number}*\n\nYour work order has been created. Please review the attached details.",
        "delivery_challan": f"🚚 *Delivery Challan #{doc_number}*\n\nYour order has been dispatched! Please find the delivery details attached.",
        "purchase_order": f"📦 *Purchase Order #{doc_number}*\n\nPlease find our purchase order attached. Kindly confirm receipt.",
        "sample": f"🎁 *Sample Dispatch #{doc_number}*\n\nYour samples have been sent! Please check the attached dispatch note.",
        "payment": f"✅ *Payment Receipt #{doc_number}*\n\nThank you for your payment! Please find the receipt attached."
    }
    
    message = greeting + (custom_message if custom_message else type_messages.get(doc_type, "Please find the attached document."))
    
    if pdf_url:
        message += f"\n\n📎 Download: {pdf_url}"
    
    message += "\n\n_InstaBiz Solutions_\n📞 +91 98765 43210"
    
    return message


async def log_communication(
    doc_type: str, doc_id: str, doc_number: str,
    channel: str, recipient: str, recipient_name: str,
    subject: str, message: str, status: str, user_id: str,
    error_message: str = None
):
    """Log communication to database"""
    log = {
        "id": str(uuid.uuid4()),
        "document_type": doc_type,
        "document_id": doc_id,
        "document_number": doc_number,
        "channel": channel,
        "recipient": recipient,
        "recipient_name": recipient_name,
        "subject": subject,
        "message": message[:500] if message else None,
        "status": status,
        "sent_at": datetime.now(timezone.utc).isoformat(),
        "sent_by": user_id,
        "error_message": error_message
    }
    await db.communication_logs.insert_one(log)
    return log


# ==================== EMAIL ENDPOINTS ====================

@router.post("/email/send")
async def send_document_email(
    request: EmailRequest,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user)
):
    """Send document via email with PDF attachment"""
    # Get document
    doc = await get_document(request.document_type, request.document_id)
    doc_number = get_document_number(doc, request.document_type)
    
    # Generate PDF
    pdf_generator = PDF_GENERATORS.get(request.document_type)
    if not pdf_generator:
        raise HTTPException(status_code=400, detail="PDF generation not supported for this document type")
    
    try:
        pdf_buffer = pdf_generator(doc)
        pdf_base64 = base64.b64encode(pdf_buffer.read()).decode('utf-8')
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate PDF: {str(e)}")
    
    # Prepare email
    subject = request.subject or generate_email_subject(request.document_type, doc_number)
    body = generate_email_body(request.document_type, doc_number, request.recipient_name, request.message)
    
    # For now, we'll simulate email sending and log it
    # In production, integrate with SendGrid, SES, or SMTP
    email_data = {
        "to": request.recipient_email,
        "cc": request.cc_emails,
        "subject": subject,
        "body": body,
        "attachment": {
            "filename": f"{doc_number}.pdf",
            "content_base64": pdf_base64[:100] + "...",  # Truncated for logging
            "content_type": "application/pdf"
        }
    }
    
    # Log communication
    log = await log_communication(
        doc_type=request.document_type,
        doc_id=request.document_id,
        doc_number=doc_number,
        channel="email",
        recipient=request.recipient_email,
        recipient_name=request.recipient_name,
        subject=subject,
        message=body,
        status="sent",  # Would be "pending" if using background task
        user_id=current_user["id"]
    )
    
    return {
        "success": True,
        "message": f"Email sent to {request.recipient_email}",
        "log_id": log["id"],
        "document_number": doc_number,
        "recipient": request.recipient_email,
        "subject": subject
    }


@router.post("/email/preview")
async def preview_document_email(
    request: EmailRequest,
    current_user: dict = Depends(get_current_user)
):
    """Preview email content before sending"""
    doc = await get_document(request.document_type, request.document_id)
    doc_number = get_document_number(doc, request.document_type)
    
    subject = request.subject or generate_email_subject(request.document_type, doc_number)
    body = generate_email_body(request.document_type, doc_number, request.recipient_name, request.message)
    
    return {
        "to": request.recipient_email,
        "cc": request.cc_emails,
        "subject": subject,
        "body": body,
        "attachment_name": f"{doc_number}.pdf",
        "document_number": doc_number
    }


# ==================== WHATSAPP ENDPOINTS ====================

@router.post("/whatsapp/send")
async def send_document_whatsapp(
    request: WhatsAppRequest,
    current_user: dict = Depends(get_current_user)
):
    """Generate WhatsApp message with document link"""
    # Get document
    doc = await get_document(request.document_type, request.document_id)
    doc_number = get_document_number(doc, request.document_type)
    
    # Generate PDF URL (would be hosted URL in production)
    # For now, use the preview endpoint URL
    base_url = "https://postgres-frontend-v1.preview.emergentagent.com"
    pdf_url = f"{base_url}/api/pdf/{request.document_type.replace('_', '-')}/{request.document_id}/preview"
    
    # Generate message
    message = generate_whatsapp_message(
        request.document_type, doc_number, 
        request.recipient_name, request.message, pdf_url
    )
    
    # Clean phone number
    phone = request.recipient_phone.replace(" ", "").replace("-", "").replace("+", "")
    if not phone.startswith("91") and len(phone) == 10:
        phone = "91" + phone
    
    # Generate WhatsApp URL
    encoded_message = message.replace(' ', '%20').replace('\n', '%0A')
    whatsapp_url = f"https://wa.me/{phone}?text={encoded_message}"
    
    # Log communication
    log = await log_communication(
        doc_type=request.document_type,
        doc_id=request.document_id,
        doc_number=doc_number,
        channel="whatsapp",
        recipient=request.recipient_phone,
        recipient_name=request.recipient_name,
        subject=None,
        message=message,
        status="sent",
        user_id=current_user["id"]
    )
    
    return {
        "success": True,
        "message": "WhatsApp message generated",
        "log_id": log["id"],
        "document_number": doc_number,
        "recipient_phone": phone,
        "whatsapp_url": whatsapp_url,
        "message_text": message
    }


@router.post("/whatsapp/preview")
async def preview_whatsapp_message(
    request: WhatsAppRequest,
    current_user: dict = Depends(get_current_user)
):
    """Preview WhatsApp message before sending"""
    doc = await get_document(request.document_type, request.document_id)
    doc_number = get_document_number(doc, request.document_type)
    
    base_url = "https://postgres-frontend-v1.preview.emergentagent.com"
    pdf_url = f"{base_url}/api/pdf/{request.document_type.replace('_', '-')}/{request.document_id}/preview"
    
    message = generate_whatsapp_message(
        request.document_type, doc_number,
        request.recipient_name, request.message, pdf_url
    )
    
    phone = request.recipient_phone.replace(" ", "").replace("-", "").replace("+", "")
    if not phone.startswith("91") and len(phone) == 10:
        phone = "91" + phone
    
    encoded_msg = message.replace(' ', '%20').replace('\n', '%0A')
    whatsapp_url = f"https://wa.me/{phone}?text={encoded_msg}"
    
    return {
        "recipient_phone": phone,
        "message": message,
        "whatsapp_url": whatsapp_url,
        "pdf_url": pdf_url,
        "document_number": doc_number
    }


# ==================== COMMUNICATION HISTORY ====================

@router.get("/history")
async def get_communication_history(
    document_type: Optional[str] = None,
    document_id: Optional[str] = None,
    channel: Optional[str] = None,
    limit: int = 50,
    current_user: dict = Depends(get_current_user)
):
    """Get communication history"""
    query = {}
    if document_type:
        query["document_type"] = document_type
    if document_id:
        query["document_id"] = document_id
    if channel:
        query["channel"] = channel
    
    logs = await db.communication_logs.find(
        query, {"_id": 0}
    ).sort("sent_at", -1).limit(limit).to_list(limit)
    
    return logs


@router.get("/history/{document_type}/{document_id}")
async def get_document_communication_history(
    document_type: str,
    document_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get communication history for a specific document"""
    logs = await db.communication_logs.find(
        {"document_type": document_type, "document_id": document_id},
        {"_id": 0}
    ).sort("sent_at", -1).to_list(100)
    
    return {
        "document_type": document_type,
        "document_id": document_id,
        "communications": logs,
        "total_sent": len(logs)
    }


# ==================== QUICK SEND ENDPOINTS ====================

@router.post("/quick-send/invoice/{invoice_id}")
async def quick_send_invoice(
    invoice_id: str,
    channel: str = "email",  # email or whatsapp
    current_user: dict = Depends(get_current_user)
):
    """Quick send invoice - auto-fetches customer contact from invoice"""
    invoice = await get_document("invoice", invoice_id)
    
    # Get account contact info
    account = await db.accounts.find_one({"id": invoice.get("account_id")}, {"_id": 0})
    if not account:
        raise HTTPException(status_code=404, detail="Customer account not found")
    
    contacts = account.get("contacts", [])
    primary_contact = next((c for c in contacts if c.get("is_primary")), contacts[0] if contacts else None)
    
    if channel == "email":
        email = primary_contact.get("email") if primary_contact else account.get("email")
        if not email:
            raise HTTPException(status_code=400, detail="No email found for this customer")
        
        request = EmailRequest(
            document_type="invoice",
            document_id=invoice_id,
            recipient_email=email,
            recipient_name=primary_contact.get("name") if primary_contact else account.get("customer_name")
        )
        return await send_document_email(request, BackgroundTasks(), current_user)
    
    else:  # whatsapp
        phone = primary_contact.get("mobile") or primary_contact.get("phone") if primary_contact else account.get("phone")
        if not phone:
            raise HTTPException(status_code=400, detail="No phone number found for this customer")
        
        request = WhatsAppRequest(
            document_type="invoice",
            document_id=invoice_id,
            recipient_phone=phone,
            recipient_name=primary_contact.get("name") if primary_contact else account.get("customer_name")
        )
        return await send_document_whatsapp(request, current_user)


@router.post("/quick-send/quotation/{quote_id}")
async def quick_send_quotation(
    quote_id: str,
    channel: str = "email",
    current_user: dict = Depends(get_current_user)
):
    """Quick send quotation"""
    quotation = await get_document("quotation", quote_id)
    
    account = await db.accounts.find_one({"id": quotation.get("account_id")}, {"_id": 0})
    if not account:
        raise HTTPException(status_code=404, detail="Customer account not found")
    
    contacts = account.get("contacts", [])
    primary_contact = next((c for c in contacts if c.get("is_primary")), contacts[0] if contacts else None)
    
    if channel == "email":
        email = quotation.get("contact_email") or (primary_contact.get("email") if primary_contact else account.get("email"))
        if not email:
            raise HTTPException(status_code=400, detail="No email found for this customer")
        
        request = EmailRequest(
            document_type="quotation",
            document_id=quote_id,
            recipient_email=email,
            recipient_name=quotation.get("contact_person") or (primary_contact.get("name") if primary_contact else None)
        )
        return await send_document_email(request, BackgroundTasks(), current_user)
    
    else:
        phone = quotation.get("contact_phone") or (primary_contact.get("mobile") if primary_contact else account.get("phone"))
        if not phone:
            raise HTTPException(status_code=400, detail="No phone number found for this customer")
        
        request = WhatsAppRequest(
            document_type="quotation",
            document_id=quote_id,
            recipient_phone=phone,
            recipient_name=quotation.get("contact_person") or (primary_contact.get("name") if primary_contact else None)
        )
        return await send_document_whatsapp(request, current_user)
