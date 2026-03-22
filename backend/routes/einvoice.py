"""
GST E-Invoicing & E-Way Bill System
Features:
- IRN (Invoice Reference Number) generation via NIC API
- QR Code generation for GST invoices
- E-Way Bill generation for goods transport
- Cancel/Amend IRN
- Bulk E-Invoice generation
- Integration status tracking
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone, timedelta
import uuid
import json
import hashlib
import base64
import qrcode
import io

from server import db, get_current_user

router = APIRouter()

# NIC API Configuration (Sandbox/Production)
NIC_CONFIG = {
    "sandbox": {
        "auth_url": "https://einv-apisandbox.nic.in/eivital/v1.04/auth",
        "einvoice_url": "https://einv-apisandbox.nic.in/eivital/v1.04/Invoice",
        "eway_url": "https://einv-apisandbox.nic.in/ewaybill/v1.03",
    },
    "production": {
        "auth_url": "https://einvoice1.gst.gov.in/eivital/v1.04/auth",
        "einvoice_url": "https://einvoice1.gst.gov.in/eivital/v1.04/Invoice",
        "eway_url": "https://ewaybillgst.gov.in/api",
    }
}


# ==================== MODELS ====================
class EInvoiceCredentials(BaseModel):
    gstin: str
    username: str
    password: str
    client_id: str
    client_secret: str
    environment: str = "sandbox"  # sandbox or production


class EInvoiceRequest(BaseModel):
    invoice_id: str


class BulkEInvoiceRequest(BaseModel):
    invoice_ids: List[str]


class EWayBillRequest(BaseModel):
    invoice_id: str
    transporter_id: Optional[str] = None
    transporter_name: Optional[str] = None
    trans_doc_no: Optional[str] = None
    trans_doc_date: Optional[str] = None
    vehicle_no: Optional[str] = None
    vehicle_type: str = "R"  # R=Regular, O=Over Dimensional Cargo
    trans_mode: str = "1"  # 1=Road, 2=Rail, 3=Air, 4=Ship


class CancelIRNRequest(BaseModel):
    irn: str
    cancel_reason: str  # 1=Duplicate, 2=Data Entry Mistake, 3=Order Cancelled, 4=Others
    cancel_remarks: Optional[str] = None


# ==================== CREDENTIAL MANAGEMENT ====================
@router.post("/credentials")
async def save_einvoice_credentials(
    credentials: EInvoiceCredentials,
    current_user: dict = Depends(get_current_user)
):
    """Save GST E-Invoice API credentials"""
    if current_user['role'] != 'admin':
        raise HTTPException(status_code=403, detail="Only admin can manage credentials")
    
    # Encrypt sensitive data (in production, use proper encryption)
    cred_doc = {
        "gstin": credentials.gstin,
        "username": credentials.username,
        "password": base64.b64encode(credentials.password.encode()).decode(),
        "client_id": credentials.client_id,
        "client_secret": base64.b64encode(credentials.client_secret.encode()).decode(),
        "environment": credentials.environment,
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "updated_by": current_user['id']
    }
    
    await db.einvoice_credentials.update_one(
        {"gstin": credentials.gstin},
        {"$set": cred_doc},
        upsert=True
    )
    
    return {"message": "Credentials saved successfully"}


@router.get("/credentials")
async def get_einvoice_credentials(current_user: dict = Depends(get_current_user)):
    """Get saved E-Invoice credentials (masked)"""
    if current_user['role'] != 'admin':
        raise HTTPException(status_code=403, detail="Only admin can view credentials")
    
    creds = await db.einvoice_credentials.find({}, {"_id": 0}).to_list(10)
    
    # Mask sensitive data
    for cred in creds:
        cred['password'] = "********"
        cred['client_secret'] = "********"
    
    return creds


# ==================== E-INVOICE GENERATION ====================
@router.post("/generate-irn")
async def generate_irn(
    request: EInvoiceRequest,
    current_user: dict = Depends(get_current_user)
):
    """Generate IRN for an invoice (Mock/Sandbox implementation)"""
    
    # Fetch invoice
    invoice = await db.invoices.find_one({"id": request.invoice_id}, {"_id": 0})
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    if invoice.get('irn'):
        raise HTTPException(status_code=400, detail="IRN already generated for this invoice")
    
    # Fetch customer details
    customer = await db.accounts.find_one({"id": invoice.get('account_id')}, {"_id": 0})
    if not customer:
        raise HTTPException(status_code=400, detail="Customer not found")
    
    # Validate required fields
    if not customer.get('gstin'):
        raise HTTPException(status_code=400, detail="Customer GSTIN is required for E-Invoice")
    
    # Get company settings for seller details
    settings = await db.settings.find_one({"type": "company"}, {"_id": 0})
    company = settings or {}
    
    # Build E-Invoice JSON payload (simplified GST schema)
    einvoice_payload = build_einvoice_payload(invoice, customer, company)
    
    # MOCK: Generate IRN (In production, call NIC API)
    irn = generate_mock_irn(invoice)
    ack_no = str(uuid.uuid4().int)[:15]
    ack_date = datetime.now(timezone.utc).isoformat()
    
    # Generate signed QR code data
    qr_data = generate_qr_data(irn, invoice, customer, company)
    qr_image = generate_qr_code(qr_data)
    
    # Update invoice with IRN details
    irn_details = {
        "irn": irn,
        "ack_no": ack_no,
        "ack_date": ack_date,
        "signed_qr_code": qr_data,
        "qr_code_image": qr_image,
        "einvoice_status": "generated",
        "einvoice_generated_at": datetime.now(timezone.utc).isoformat(),
        "einvoice_generated_by": current_user['id']
    }
    
    await db.invoices.update_one(
        {"id": request.invoice_id},
        {"$set": irn_details}
    )
    
    # Log the transaction
    await db.einvoice_logs.insert_one({
        "id": str(uuid.uuid4()),
        "invoice_id": request.invoice_id,
        "invoice_number": invoice.get('invoice_number'),
        "action": "generate_irn",
        "irn": irn,
        "status": "success",
        "request_payload": einvoice_payload,
        "response": {"irn": irn, "ack_no": ack_no, "ack_date": ack_date},
        "created_at": datetime.now(timezone.utc).isoformat(),
        "created_by": current_user['id']
    })
    
    return {
        "success": True,
        "irn": irn,
        "ack_no": ack_no,
        "ack_date": ack_date,
        "qr_code": qr_image,
        "message": "IRN generated successfully (Mock)"
    }


@router.post("/generate-irn/bulk")
async def generate_irn_bulk(
    request: BulkEInvoiceRequest,
    current_user: dict = Depends(get_current_user)
):
    """Generate IRN for multiple invoices"""
    results = {"success": [], "failed": []}
    
    for invoice_id in request.invoice_ids:
        try:
            result = await generate_irn(
                EInvoiceRequest(invoice_id=invoice_id),
                current_user
            )
            results['success'].append({
                "invoice_id": invoice_id,
                "irn": result['irn']
            })
        except HTTPException as e:
            results['failed'].append({
                "invoice_id": invoice_id,
                "error": e.detail
            })
        except Exception as e:
            results['failed'].append({
                "invoice_id": invoice_id,
                "error": str(e)
            })
    
    return {
        "message": f"Processed {len(request.invoice_ids)} invoices",
        "success_count": len(results['success']),
        "failed_count": len(results['failed']),
        "results": results
    }


@router.post("/cancel-irn")
async def cancel_irn(
    request: CancelIRNRequest,
    current_user: dict = Depends(get_current_user)
):
    """Cancel an IRN"""
    invoice = await db.invoices.find_one({"irn": request.irn}, {"_id": 0})
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice with this IRN not found")
    
    # Check if within 24 hours
    generated_at = invoice.get('einvoice_generated_at')
    if generated_at:
        gen_time = datetime.fromisoformat(generated_at.replace('Z', '+00:00'))
        if datetime.now(timezone.utc) - gen_time > timedelta(hours=24):
            raise HTTPException(status_code=400, detail="IRN can only be cancelled within 24 hours of generation")
    
    # MOCK: Cancel IRN
    cancel_date = datetime.now(timezone.utc).isoformat()
    
    await db.invoices.update_one(
        {"irn": request.irn},
        {
            "$set": {
                "einvoice_status": "cancelled",
                "irn_cancelled_at": cancel_date,
                "irn_cancel_reason": request.cancel_reason,
                "irn_cancel_remarks": request.cancel_remarks
            }
        }
    )
    
    await db.einvoice_logs.insert_one({
        "id": str(uuid.uuid4()),
        "invoice_id": invoice.get('id'),
        "invoice_number": invoice.get('invoice_number'),
        "action": "cancel_irn",
        "irn": request.irn,
        "status": "success",
        "cancel_reason": request.cancel_reason,
        "created_at": cancel_date,
        "created_by": current_user['id']
    })
    
    return {
        "success": True,
        "message": "IRN cancelled successfully",
        "cancelled_at": cancel_date
    }


@router.get("/invoice/{invoice_id}/irn-status")
async def get_irn_status(invoice_id: str, current_user: dict = Depends(get_current_user)):
    """Get IRN status for an invoice"""
    invoice = await db.invoices.find_one(
        {"id": invoice_id},
        {"_id": 0, "irn": 1, "ack_no": 1, "ack_date": 1, "einvoice_status": 1, 
         "signed_qr_code": 1, "qr_code_image": 1, "einvoice_generated_at": 1}
    )
    
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    return invoice


# ==================== E-WAY BILL ====================
@router.post("/generate-eway-bill")
async def generate_eway_bill(
    request: EWayBillRequest,
    current_user: dict = Depends(get_current_user)
):
    """Generate E-Way Bill for an invoice"""
    
    invoice = await db.invoices.find_one({"id": request.invoice_id}, {"_id": 0})
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    # Check if invoice value > 50,000 (E-Way Bill threshold)
    grand_total = invoice.get('grand_total', 0)
    if grand_total < 50000:
        raise HTTPException(status_code=400, detail="E-Way Bill not required for invoice value less than ₹50,000")
    
    if invoice.get('eway_bill_no'):
        raise HTTPException(status_code=400, detail="E-Way Bill already generated")
    
    customer = await db.accounts.find_one({"id": invoice.get('account_id')}, {"_id": 0})
    
    # MOCK: Generate E-Way Bill
    eway_bill_no = f"EWB{datetime.now().strftime('%Y%m%d')}{str(uuid.uuid4().int)[:10]}"
    eway_bill_date = datetime.now(timezone.utc).isoformat()
    valid_upto = (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()  # 1 day validity for <100km
    
    eway_details = {
        "eway_bill_no": eway_bill_no,
        "eway_bill_date": eway_bill_date,
        "eway_bill_valid_upto": valid_upto,
        "transporter_id": request.transporter_id,
        "transporter_name": request.transporter_name,
        "trans_doc_no": request.trans_doc_no,
        "trans_doc_date": request.trans_doc_date,
        "vehicle_no": request.vehicle_no,
        "vehicle_type": request.vehicle_type,
        "trans_mode": request.trans_mode,
        "eway_bill_status": "active",
        "eway_bill_generated_at": datetime.now(timezone.utc).isoformat(),
        "eway_bill_generated_by": current_user['id']
    }
    
    await db.invoices.update_one(
        {"id": request.invoice_id},
        {"$set": eway_details}
    )
    
    await db.eway_bill_logs.insert_one({
        "id": str(uuid.uuid4()),
        "invoice_id": request.invoice_id,
        "invoice_number": invoice.get('invoice_number'),
        "action": "generate",
        "eway_bill_no": eway_bill_no,
        "status": "success",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "created_by": current_user['id']
    })
    
    return {
        "success": True,
        "eway_bill_no": eway_bill_no,
        "eway_bill_date": eway_bill_date,
        "valid_upto": valid_upto,
        "message": "E-Way Bill generated successfully (Mock)"
    }


@router.put("/eway-bill/{eway_bill_no}/update-vehicle")
async def update_eway_bill_vehicle(
    eway_bill_no: str,
    vehicle_no: str,
    trans_doc_no: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Update vehicle details in E-Way Bill"""
    invoice = await db.invoices.find_one({"eway_bill_no": eway_bill_no}, {"_id": 0})
    if not invoice:
        raise HTTPException(status_code=404, detail="E-Way Bill not found")
    
    update_data = {
        "vehicle_no": vehicle_no,
        "vehicle_updated_at": datetime.now(timezone.utc).isoformat()
    }
    if trans_doc_no:
        update_data["trans_doc_no"] = trans_doc_no
    
    await db.invoices.update_one(
        {"eway_bill_no": eway_bill_no},
        {"$set": update_data}
    )
    
    return {"success": True, "message": "Vehicle details updated"}


@router.post("/eway-bill/{eway_bill_no}/cancel")
async def cancel_eway_bill(
    eway_bill_no: str,
    cancel_reason: str,
    current_user: dict = Depends(get_current_user)
):
    """Cancel E-Way Bill"""
    invoice = await db.invoices.find_one({"eway_bill_no": eway_bill_no}, {"_id": 0})
    if not invoice:
        raise HTTPException(status_code=404, detail="E-Way Bill not found")
    
    await db.invoices.update_one(
        {"eway_bill_no": eway_bill_no},
        {
            "$set": {
                "eway_bill_status": "cancelled",
                "eway_bill_cancelled_at": datetime.now(timezone.utc).isoformat(),
                "eway_bill_cancel_reason": cancel_reason
            }
        }
    )
    
    return {"success": True, "message": "E-Way Bill cancelled"}


# ==================== REPORTS & LOGS ====================
@router.get("/logs")
async def get_einvoice_logs(
    invoice_id: Optional[str] = None,
    action: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    limit: int = Query(default=50, le=200),
    current_user: dict = Depends(get_current_user)
):
    """Get E-Invoice/E-Way Bill logs"""
    query = {}
    if invoice_id:
        query["invoice_id"] = invoice_id
    if action:
        query["action"] = action
    if start_date:
        query["created_at"] = {"$gte": start_date}
    if end_date:
        if "created_at" in query:
            query["created_at"]["$lte"] = end_date
        else:
            query["created_at"] = {"$lte": end_date}
    
    logs = await db.einvoice_logs.find(query, {"_id": 0}).sort("created_at", -1).limit(limit).to_list(limit)
    return logs


@router.get("/pending-invoices")
async def get_pending_einvoices(current_user: dict = Depends(get_current_user)):
    """Get invoices pending E-Invoice generation"""
    invoices = await db.invoices.find(
        {
            "invoice_type": "Sales",
            "irn": {"$exists": False},
            "status": {"$nin": ["draft", "cancelled"]}
        },
        {"_id": 0, "id": 1, "invoice_number": 1, "invoice_date": 1, 
         "account_name": 1, "grand_total": 1}
    ).sort("invoice_date", -1).limit(100).to_list(100)
    
    return invoices


@router.get("/summary")
async def get_einvoice_summary(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Get E-Invoice summary statistics"""
    date_filter = {}
    if start_date:
        date_filter["$gte"] = start_date
    if end_date:
        date_filter["$lte"] = end_date
    
    query = {"invoice_type": "Sales"}
    if date_filter:
        query["invoice_date"] = date_filter
    
    total_invoices = await db.invoices.count_documents(query)
    
    irn_generated = await db.invoices.count_documents({**query, "irn": {"$exists": True, "$ne": None}})
    irn_cancelled = await db.invoices.count_documents({**query, "einvoice_status": "cancelled"})
    
    eway_generated = await db.invoices.count_documents({**query, "eway_bill_no": {"$exists": True, "$ne": None}})
    eway_cancelled = await db.invoices.count_documents({**query, "eway_bill_status": "cancelled"})
    
    return {
        "total_invoices": total_invoices,
        "irn_generated": irn_generated,
        "irn_pending": total_invoices - irn_generated,
        "irn_cancelled": irn_cancelled,
        "eway_generated": eway_generated,
        "eway_cancelled": eway_cancelled,
        "date_range": {"start": start_date, "end": end_date}
    }


# ==================== HELPER FUNCTIONS ====================
def build_einvoice_payload(invoice: dict, customer: dict, company: dict) -> dict:
    """Build E-Invoice JSON payload as per GST schema"""
    
    # Simplified payload structure
    payload = {
        "Version": "1.1",
        "TranDtls": {
            "TaxSch": "GST",
            "SupTyp": "B2B",
            "RegRev": "N",
            "EcmGstin": None,
            "IgstOnIntra": "N"
        },
        "DocDtls": {
            "Typ": "INV",
            "No": invoice.get('invoice_number'),
            "Dt": invoice.get('invoice_date')
        },
        "SellerDtls": {
            "Gstin": company.get('gstin', ''),
            "LglNm": company.get('company_name', ''),
            "Addr1": company.get('address_line1', ''),
            "Loc": company.get('city', ''),
            "Pin": company.get('pincode', ''),
            "Stcd": company.get('state_code', '33')
        },
        "BuyerDtls": {
            "Gstin": customer.get('gstin', ''),
            "LglNm": customer.get('account_name', ''),
            "Addr1": customer.get('address_line1', ''),
            "Loc": customer.get('city', ''),
            "Pin": customer.get('pincode', ''),
            "Stcd": customer.get('state_code', '33')
        },
        "ValDtls": {
            "AssVal": invoice.get('subtotal', 0),
            "CgstVal": invoice.get('cgst', 0),
            "SgstVal": invoice.get('sgst', 0),
            "IgstVal": invoice.get('igst', 0),
            "TotInvVal": invoice.get('grand_total', 0)
        },
        "ItemList": []
    }
    
    # Add items
    for idx, item in enumerate(invoice.get('items', []), 1):
        payload["ItemList"].append({
            "SlNo": str(idx),
            "IsServc": "N",
            "HsnCd": item.get('hsn_code', ''),
            "Qty": item.get('quantity', 0),
            "Unit": item.get('uom', 'NOS'),
            "UnitPrice": item.get('rate', 0),
            "TotAmt": item.get('amount', 0),
            "AssAmt": item.get('taxable_value', 0),
            "GstRt": item.get('gst_rate', 18),
            "CgstAmt": item.get('cgst', 0),
            "SgstAmt": item.get('sgst', 0),
            "IgstAmt": item.get('igst', 0),
            "TotItemVal": item.get('total', 0)
        })
    
    return payload


def generate_mock_irn(invoice: dict) -> str:
    """Generate mock IRN (64 character hex string)"""
    data = f"{invoice.get('invoice_number')}:{invoice.get('invoice_date')}:{datetime.now().isoformat()}"
    return hashlib.sha256(data.encode()).hexdigest()


def generate_qr_data(irn: str, invoice: dict, customer: dict, company: dict) -> str:
    """Generate QR code data string"""
    qr_data = {
        "SellerGstin": company.get('gstin', ''),
        "BuyerGstin": customer.get('gstin', ''),
        "DocNo": invoice.get('invoice_number'),
        "DocTyp": "INV",
        "DocDt": invoice.get('invoice_date'),
        "TotInvVal": invoice.get('grand_total', 0),
        "ItemCnt": len(invoice.get('items', [])),
        "MainHsnCode": invoice.get('items', [{}])[0].get('hsn_code', '') if invoice.get('items') else '',
        "Irn": irn
    }
    return json.dumps(qr_data)


def generate_qr_code(data: str) -> str:
    """Generate QR code image as base64"""
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(data)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)
    
    return f"data:image/png;base64,{base64.b64encode(buffer.read()).decode()}"
