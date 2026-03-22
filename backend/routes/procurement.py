from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
import uuid
import re
import httpx
from server import db, get_current_user

router = APIRouter()

# ==================== PINCODE & GSTIN HELPERS ====================
PINCODE_API_BASE = "https://api.postalpincode.in/pincode/"

async def lookup_india_pincode(pincode: str) -> Optional[dict]:
    """Fetch city/state/district from Indian pincode API."""
    if not pincode or len(pincode) != 6 or not pincode.isdigit():
        return None
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(f"{PINCODE_API_BASE}{pincode}")
            data = resp.json()
            if data and data[0].get("Status") == "Success":
                po = data[0]["PostOffice"][0]
                return {
                    "city": po.get("Block") or po.get("Name"),
                    "district": po.get("District"),
                    "state": po.get("State"),
                    "country": "India"
                }
    except Exception:
        pass
    return None

# Indian state code mapping (first 2 digits of GSTIN)
GSTIN_STATE_CODES = {
    "01": "Jammu & Kashmir", "02": "Himachal Pradesh", "03": "Punjab",
    "04": "Chandigarh", "05": "Uttarakhand", "06": "Haryana",
    "07": "Delhi", "08": "Rajasthan", "09": "Uttar Pradesh",
    "10": "Bihar", "11": "Sikkim", "12": "Arunachal Pradesh",
    "13": "Nagaland", "14": "Manipur", "15": "Mizoram",
    "16": "Tripura", "17": "Meghalaya", "18": "Assam",
    "19": "West Bengal", "20": "Jharkhand", "21": "Odisha",
    "22": "Chhattisgarh", "23": "Madhya Pradesh", "24": "Gujarat",
    "26": "Dadra & Nagar Haveli", "27": "Maharashtra", "29": "Karnataka",
    "30": "Goa", "31": "Lakshadweep", "32": "Kerala",
    "33": "Tamil Nadu", "34": "Puducherry", "35": "Andaman & Nicobar",
    "36": "Telangana", "37": "Andhra Pradesh"
}

def validate_gstin(gstin: str) -> dict:
    """Validate GSTIN format and extract state code."""
    gstin = gstin.upper().strip()
    result = {"valid": False, "gstin": gstin, "state": None, "pan": None, "error": None}
    
    if len(gstin) != 15:
        result["error"] = "GSTIN must be 15 characters"
        return result
    
    # GSTIN format: 22AAAAA0000A1Z5
    pattern = r'^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[A-Z0-9]{1}[Z]{1}[A-Z0-9]{1}$'
    if not re.match(pattern, gstin):
        result["error"] = "Invalid GSTIN format"
        return result
    
    state_code = gstin[:2]
    if state_code not in GSTIN_STATE_CODES:
        result["error"] = "Invalid state code in GSTIN"
        return result
    
    result["valid"] = True
    result["state"] = GSTIN_STATE_CODES[state_code]
    result["pan"] = gstin[2:12]
    return result

# ==================== SUPPLIER MODELS ====================
class SupplierCreate(BaseModel):
    supplier_code: Optional[str] = None
    supplier_name: str
    supplier_type: str = "Raw Material"
    contact_person: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    mobile: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    pincode: Optional[str] = None
    country: str = "India"
    gstin: Optional[str] = None
    pan: Optional[str] = None
    payment_terms: str = "30 days"
    credit_limit: float = 0
    bank_name: Optional[str] = None
    bank_account: Optional[str] = None
    ifsc_code: Optional[str] = None
    notes: Optional[str] = None

class SupplierUpdate(BaseModel):
    supplier_name: Optional[str] = None
    supplier_type: Optional[str] = None
    contact_person: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    mobile: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    pincode: Optional[str] = None
    gstin: Optional[str] = None
    pan: Optional[str] = None
    payment_terms: Optional[str] = None
    credit_limit: Optional[float] = None
    bank_name: Optional[str] = None
    bank_account: Optional[str] = None
    ifsc_code: Optional[str] = None
    notes: Optional[str] = None
    is_active: Optional[bool] = None

class Supplier(BaseModel):
    id: str
    supplier_code: Optional[str] = None
    supplier_name: Optional[str] = None
    supplier_type: Optional[str] = None
    contact_person: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    mobile: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    pincode: Optional[str] = None
    country: Optional[str] = "India"
    gstin: Optional[str] = None
    pan: Optional[str] = None
    payment_terms: Optional[str] = None
    credit_limit: Optional[float] = 0
    credit_days: Optional[int] = 30
    bank_name: Optional[str] = None
    bank_account: Optional[str] = None
    ifsc_code: Optional[str] = None
    notes: Optional[str] = None
    quality_rating: Optional[float] = 0
    delivery_rating: Optional[float] = 0
    total_orders: Optional[int] = 0
    total_value: Optional[float] = 0
    cumulative_purchase_value: Optional[float] = 0
    is_active: Optional[bool] = True
    rating: Optional[int] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

# ==================== PURCHASE ORDER MODELS ====================
class POItemCreate(BaseModel):
    item_id: str
    quantity: float
    unit_price: float
    tax_percent: float = 18
    discount_percent: float = 0
    delivery_date: Optional[str] = None
    notes: Optional[str] = None

class PurchaseOrderCreate(BaseModel):
    supplier_id: str
    po_type: str = "Standard"
    warehouse_id: str
    items: List[POItemCreate]
    currency: str = "INR"
    payment_terms: Optional[str] = None
    delivery_terms: Optional[str] = None
    shipping_address: Optional[str] = None
    notes: Optional[str] = None
    expected_date: Optional[str] = None

class PurchaseOrderUpdate(BaseModel):
    items: Optional[List[POItemCreate]] = None
    payment_terms: Optional[str] = None
    delivery_terms: Optional[str] = None
    shipping_address: Optional[str] = None
    notes: Optional[str] = None
    expected_date: Optional[str] = None
    status: Optional[str] = None

class PurchaseOrder(BaseModel):
    id: str
    po_number: str
    supplier_id: str
    supplier_name: Optional[str] = None
    po_type: str
    warehouse_id: str
    warehouse_name: Optional[str] = None
    items: List[dict]
    subtotal: float
    discount_amount: float
    taxable_amount: float
    cgst_amount: float
    sgst_amount: float
    igst_amount: float
    total_tax: float
    grand_total: float
    currency: str
    payment_terms: Optional[str] = None
    delivery_terms: Optional[str] = None
    shipping_address: Optional[str] = None
    expected_date: Optional[str] = None
    notes: Optional[str] = None
    status: str  # draft, sent, partial, received, cancelled
    received_value: float = 0
    created_by: str
    created_at: str
    updated_at: Optional[str] = None

# ==================== GRN MODELS ====================
class GRNItemCreate(BaseModel):
    po_item_index: int
    item_id: str
    received_qty: float
    accepted_qty: float
    rejected_qty: float = 0
    rejection_reason: Optional[str] = None
    batch_no: Optional[str] = None
    expiry_date: Optional[str] = None
    unit_price: float

class GRNCreate(BaseModel):
    po_id: str
    items: List[GRNItemCreate]
    invoice_no: Optional[str] = None
    invoice_date: Optional[str] = None
    invoice_amount: Optional[float] = None
    lr_no: Optional[str] = None
    vehicle_no: Optional[str] = None
    notes: Optional[str] = None

class GRN(BaseModel):
    id: str
    grn_number: str
    po_id: str
    po_number: Optional[str] = None
    supplier_id: str
    supplier_name: Optional[str] = None
    warehouse_id: str
    items: List[dict]
    total_qty: float
    accepted_qty: float
    rejected_qty: float
    total_value: float
    invoice_no: Optional[str] = None
    invoice_date: Optional[str] = None
    invoice_amount: Optional[float] = None
    lr_no: Optional[str] = None
    vehicle_no: Optional[str] = None
    notes: Optional[str] = None
    status: str  # pending_qc, approved, partial
    qc_status: Optional[str] = None
    created_by: str
    created_at: str

# ==================== SUPPLIER ENDPOINTS ====================
@router.post("/suppliers", response_model=Supplier)
async def create_supplier(supplier_data: SupplierCreate, current_user: dict = Depends(get_current_user)):
    supplier_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    
    # Generate supplier code
    count = await db.suppliers.count_documents({})
    supplier_code = supplier_data.supplier_code or f"SUP-{str(count + 1).zfill(4)}"
    
    supplier_doc = {
        "id": supplier_id,
        "supplier_code": supplier_code,
        **supplier_data.model_dump(),
        "quality_rating": 0,
        "delivery_rating": 0,
        "total_orders": 0,
        "total_value": 0,
        "cumulative_purchase_value": 0,  # For TDS/TCS tracking
        "is_active": True,
        "created_at": now,
        "updated_at": now
    }
    
    # Auto-fill geo fields from pincode (India)
    if supplier_doc.get("pincode") and len(supplier_doc.get("pincode", "")) == 6:
        geo = await lookup_india_pincode(supplier_doc["pincode"])
        if geo:
            if not supplier_doc.get("city"):
                supplier_doc["city"] = geo.get("city")
            if not supplier_doc.get("state"):
                supplier_doc["state"] = geo.get("state")
    
    # Validate and extract state from GSTIN
    if supplier_doc.get("gstin"):
        gstin_info = validate_gstin(supplier_doc["gstin"])
        if gstin_info["valid"]:
            # Auto-fill state from GSTIN if not already set
            if not supplier_doc.get("state"):
                supplier_doc["state"] = gstin_info["state"]
            # Auto-fill PAN from GSTIN
            if not supplier_doc.get("pan") and gstin_info.get("pan"):
                supplier_doc["pan"] = gstin_info["pan"]
    
    await db.suppliers.insert_one(supplier_doc)
    return Supplier(**{k: v for k, v in supplier_doc.items() if k != '_id'})

@router.get("/suppliers", response_model=List[Supplier])
async def get_suppliers(
    supplier_type: Optional[str] = None,
    is_active: Optional[bool] = None,
    search: Optional[str] = None,
    city: Optional[str] = None,
    state: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    query = {}
    if supplier_type:
        query["supplier_type"] = supplier_type
    if is_active is not None:
        query["is_active"] = is_active
    if search:
        query["$or"] = [
            {"supplier_name": {"$regex": search, "$options": "i"}},
            {"supplier_code": {"$regex": search, "$options": "i"}},
            {"gstin": {"$regex": search, "$options": "i"}}
        ]
    if city:
        query["city"] = {"$regex": city, "$options": "i"}
    if state:
        query["state"] = {"$regex": state, "$options": "i"}
    
    suppliers = await db.suppliers.find(query, {"_id": 0}).sort("supplier_name", 1).to_list(1000)
    return [Supplier(**s) for s in suppliers]

@router.get("/suppliers/{supplier_id}", response_model=Supplier)
async def get_supplier(supplier_id: str, current_user: dict = Depends(get_current_user)):
    supplier = await db.suppliers.find_one({"id": supplier_id}, {"_id": 0})
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")
    return Supplier(**supplier)

@router.put("/suppliers/{supplier_id}", response_model=Supplier)
async def update_supplier(supplier_id: str, supplier_data: SupplierUpdate, current_user: dict = Depends(get_current_user)):
    update_dict = {k: v for k, v in supplier_data.model_dump().items() if v is not None}
    update_dict["updated_at"] = datetime.now(timezone.utc).isoformat()
    
    # Auto-fill geo fields from pincode (India)
    if update_dict.get("pincode") and len(update_dict.get("pincode", "")) == 6:
        geo = await lookup_india_pincode(update_dict["pincode"])
        if geo:
            if not update_dict.get("city"):
                update_dict["city"] = geo.get("city")
            if not update_dict.get("state"):
                update_dict["state"] = geo.get("state")
    
    # Validate and extract state from GSTIN
    if update_dict.get("gstin"):
        gstin_info = validate_gstin(update_dict["gstin"])
        if gstin_info["valid"]:
            if not update_dict.get("state"):
                update_dict["state"] = gstin_info["state"]
            if not update_dict.get("pan") and gstin_info.get("pan"):
                update_dict["pan"] = gstin_info["pan"]
    
    result = await db.suppliers.update_one({"id": supplier_id}, {"$set": update_dict})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Supplier not found")
    
    supplier = await db.suppliers.find_one({"id": supplier_id}, {"_id": 0})
    return Supplier(**supplier)

@router.delete("/suppliers/{supplier_id}")
async def delete_supplier(supplier_id: str, current_user: dict = Depends(get_current_user)):
    result = await db.suppliers.update_one(
        {"id": supplier_id},
        {"$set": {"is_active": False, "updated_at": datetime.now(timezone.utc).isoformat()}}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Supplier not found")
    return {"message": "Supplier deactivated"}

# ==================== PURCHASE ORDER ENDPOINTS ====================
def calculate_po_totals(items: List[dict]) -> dict:
    subtotal = 0
    total_discount = 0
    total_tax = 0
    
    calculated_items = []
    for item in items:
        qty = item.get("quantity", 0)
        price = item.get("unit_price", 0)
        discount_pct = item.get("discount_percent", 0)
        tax_pct = item.get("tax_percent", 18)
        
        line_subtotal = qty * price
        line_discount = line_subtotal * (discount_pct / 100)
        line_taxable = line_subtotal - line_discount
        line_tax = line_taxable * (tax_pct / 100)
        line_total = line_taxable + line_tax
        
        calculated_items.append({
            **item,
            "line_subtotal": round(line_subtotal, 2),
            "line_discount": round(line_discount, 2),
            "line_taxable": round(line_taxable, 2),
            "line_tax": round(line_tax, 2),
            "line_total": round(line_total, 2),
            "received_qty": 0
        })
        
        subtotal += line_subtotal
        total_discount += line_discount
        total_tax += line_tax
    
    taxable_amount = subtotal - total_discount
    cgst = total_tax / 2
    sgst = total_tax / 2
    
    return {
        "items": calculated_items,
        "subtotal": round(subtotal, 2),
        "discount_amount": round(total_discount, 2),
        "taxable_amount": round(taxable_amount, 2),
        "cgst_amount": round(cgst, 2),
        "sgst_amount": round(sgst, 2),
        "igst_amount": 0,
        "total_tax": round(total_tax, 2),
        "grand_total": round(taxable_amount + total_tax, 2)
    }

@router.post("/purchase-orders", response_model=PurchaseOrder)
async def create_purchase_order(po_data: PurchaseOrderCreate, current_user: dict = Depends(get_current_user)):
    po_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc)
    po_number = f"PO-{now.strftime('%Y%m%d')}-{str(uuid.uuid4())[:6].upper()}"
    
    # Get supplier details
    supplier = await db.suppliers.find_one({"id": po_data.supplier_id}, {"supplier_name": 1, "payment_terms": 1})
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")
    
    # Get warehouse details
    warehouse = await db.warehouses.find_one({"id": po_data.warehouse_id}, {"warehouse_name": 1})
    
    # Enrich items with item details
    items_with_details = []
    for item in po_data.items:
        item_doc = await db.items.find_one({"id": item.item_id}, {"item_code": 1, "item_name": 1, "uom": 1, "hsn_code": 1})
        if item_doc:
            items_with_details.append({
                **item.model_dump(),
                "item_code": item_doc.get("item_code"),
                "item_name": item_doc.get("item_name"),
                "uom": item_doc.get("uom"),
                "hsn_code": item_doc.get("hsn_code")
            })
    
    # Calculate totals
    totals = calculate_po_totals(items_with_details)
    
    po_doc = {
        "id": po_id,
        "po_number": po_number,
        "supplier_id": po_data.supplier_id,
        "supplier_name": supplier.get("supplier_name"),
        "po_type": po_data.po_type,
        "warehouse_id": po_data.warehouse_id,
        "warehouse_name": warehouse.get("warehouse_name") if warehouse else "",
        **totals,
        "currency": po_data.currency,
        "payment_terms": po_data.payment_terms or supplier.get("payment_terms"),
        "delivery_terms": po_data.delivery_terms,
        "shipping_address": po_data.shipping_address,
        "expected_date": po_data.expected_date,
        "notes": po_data.notes,
        "status": "draft",
        "received_value": 0,
        "created_by": current_user["id"],
        "created_at": now.isoformat(),
        "updated_at": now.isoformat()
    }
    
    await db.purchase_orders.insert_one(po_doc)
    return PurchaseOrder(**{k: v for k, v in po_doc.items() if k != '_id'})

@router.get("/purchase-orders", response_model=List[PurchaseOrder])
async def get_purchase_orders(
    supplier_id: Optional[str] = None,
    status: Optional[str] = None,
    warehouse_id: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    query = {}
    if supplier_id:
        query["supplier_id"] = supplier_id
    if status:
        query["status"] = status
    if warehouse_id:
        query["warehouse_id"] = warehouse_id
    if date_from:
        query["created_at"] = {"$gte": date_from}
    if date_to:
        if "created_at" in query:
            query["created_at"]["$lte"] = date_to
        else:
            query["created_at"] = {"$lte": date_to}
    
    pos = await db.purchase_orders.find(query, {"_id": 0}).sort("created_at", -1).to_list(1000)
    return [PurchaseOrder(**po) for po in pos]

@router.get("/purchase-orders/{po_id}", response_model=PurchaseOrder)
async def get_purchase_order(po_id: str, current_user: dict = Depends(get_current_user)):
    po = await db.purchase_orders.find_one({"id": po_id}, {"_id": 0})
    if not po:
        raise HTTPException(status_code=404, detail="Purchase Order not found")
    return PurchaseOrder(**po)

@router.put("/purchase-orders/{po_id}/status")
async def update_po_status(po_id: str, status: str, current_user: dict = Depends(get_current_user)):
    valid_statuses = ["draft", "sent", "partial", "received", "cancelled"]
    if status not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of: {valid_statuses}")
    
    result = await db.purchase_orders.update_one(
        {"id": po_id},
        {"$set": {"status": status, "updated_at": datetime.now(timezone.utc).isoformat()}}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Purchase Order not found")
    
    return {"message": f"Status updated to {status}"}

@router.delete("/purchase-orders/{po_id}")
async def delete_purchase_order(po_id: str, current_user: dict = Depends(get_current_user)):
    po = await db.purchase_orders.find_one({"id": po_id}, {"status": 1})
    if not po:
        raise HTTPException(status_code=404, detail="Purchase Order not found")
    
    if po.get("status") not in ["draft"]:
        raise HTTPException(status_code=400, detail="Can only delete draft POs")
    
    await db.purchase_orders.delete_one({"id": po_id})
    return {"message": "Purchase Order deleted"}

@router.put("/purchase-orders/{po_id}", response_model=PurchaseOrder)
async def update_purchase_order(po_id: str, po_data: PurchaseOrderUpdate, current_user: dict = Depends(get_current_user)):
    """Edit/Update a Purchase Order (only draft or sent status)"""
    po = await db.purchase_orders.find_one({"id": po_id}, {"_id": 0})
    if not po:
        raise HTTPException(status_code=404, detail="Purchase Order not found")
    
    if po.get("status") not in ["draft", "sent"]:
        raise HTTPException(status_code=400, detail="Can only edit POs in draft or sent status")
    
    now = datetime.now(timezone.utc).isoformat()
    update_dict = {"updated_at": now}
    
    # Update items if provided
    if po_data.items:
        items_with_details = []
        for item in po_data.items:
            item_doc = await db.items.find_one({"id": item.item_id}, {"item_code": 1, "item_name": 1, "uom": 1, "hsn_code": 1})
            if item_doc:
                items_with_details.append({
                    **item.model_dump(),
                    "item_code": item_doc.get("item_code"),
                    "item_name": item_doc.get("item_name"),
                    "uom": item_doc.get("uom"),
                    "hsn_code": item_doc.get("hsn_code")
                })
        
        # Recalculate totals
        totals = calculate_po_totals(items_with_details)
        update_dict.update(totals)
    
    # Update other fields
    if po_data.payment_terms is not None:
        update_dict["payment_terms"] = po_data.payment_terms
    if po_data.delivery_terms is not None:
        update_dict["delivery_terms"] = po_data.delivery_terms
    if po_data.shipping_address is not None:
        update_dict["shipping_address"] = po_data.shipping_address
    if po_data.notes is not None:
        update_dict["notes"] = po_data.notes
    if po_data.expected_date is not None:
        update_dict["expected_date"] = po_data.expected_date
    if po_data.status is not None and po_data.status in ["draft", "sent", "cancelled"]:
        update_dict["status"] = po_data.status
    
    await db.purchase_orders.update_one({"id": po_id}, {"$set": update_dict})
    
    updated_po = await db.purchase_orders.find_one({"id": po_id}, {"_id": 0})
    return PurchaseOrder(**updated_po)

# ==================== GEO & GSTIN LOOKUP ENDPOINTS ====================
@router.get("/geo/pincode/{pincode}")
async def get_pincode_details(pincode: str, current_user: dict = Depends(get_current_user)):
    """Lookup city, district, state from Indian pincode"""
    details = await lookup_india_pincode(pincode)
    if not details:
        raise HTTPException(status_code=404, detail="Pincode not found or invalid")
    return details

@router.get("/gstin/validate/{gstin}")
async def validate_gstin_endpoint(gstin: str, current_user: dict = Depends(get_current_user)):
    """Validate GSTIN format and extract state/PAN"""
    result = validate_gstin(gstin)
    if not result["valid"]:
        raise HTTPException(status_code=400, detail=result["error"])
    return result

# ==================== TDS/TCS COMPLIANCE ENDPOINT ====================
TDS_THRESHOLD = 5000000  # 50 Lakh INR

@router.get("/suppliers/{supplier_id}/tds-info")
async def get_supplier_tds_info(supplier_id: str, current_user: dict = Depends(get_current_user)):
    """
    Get TDS/TCS information for a supplier.
    Returns cumulative purchase value and whether TDS/TCS is applicable.
    Indian Tax Rules:
    - Section 194Q (TDS): Buyer deducts 0.1% (if PAN) or 5% (no PAN) on purchases > 50 lakh
    - Section 206C(1H) (TCS): Seller collects 0.1% on sales > 50 lakh
    """
    supplier = await db.suppliers.find_one({"id": supplier_id}, {"_id": 0})
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")
    
    # Calculate cumulative purchase value from POs in current financial year
    now = datetime.now(timezone.utc)
    fy_start = f"{now.year}-04-01" if now.month >= 4 else f"{now.year - 1}-04-01"
    
    pipeline = [
        {"$match": {
            "supplier_id": supplier_id,
            "status": {"$in": ["received", "partial"]},
            "created_at": {"$gte": fy_start}
        }},
        {"$group": {
            "_id": None,
            "total_purchase_value": {"$sum": "$grand_total"}
        }}
    ]
    
    result = await db.purchase_orders.aggregate(pipeline).to_list(1)
    cumulative_value = result[0]["total_purchase_value"] if result else 0
    
    # Also add cumulative from supplier record if tracked
    cumulative_value += supplier.get("cumulative_purchase_value", 0)
    
    has_pan = bool(supplier.get("pan"))
    has_gstin = bool(supplier.get("gstin"))
    is_gst_registered = has_gstin
    threshold_exceeded = cumulative_value >= TDS_THRESHOLD
    
    # TDS Rate: 0.1% if PAN available, 5% otherwise (Section 194Q)
    tds_rate = 0.1 if has_pan else 5.0
    
    return {
        "supplier_id": supplier_id,
        "supplier_name": supplier.get("supplier_name"),
        "gstin": supplier.get("gstin"),
        "pan": supplier.get("pan"),
        "is_gst_registered": is_gst_registered,
        "cumulative_purchase_value": round(cumulative_value, 2),
        "threshold": TDS_THRESHOLD,
        "threshold_exceeded": threshold_exceeded,
        "tds_applicable": threshold_exceeded and is_gst_registered,
        "tds_rate": tds_rate if threshold_exceeded else 0,
        "tds_rate_description": f"TDS @ {tds_rate}% {'(with PAN)' if has_pan else '(without PAN)'}" if threshold_exceeded else "Not applicable",
        "remaining_before_threshold": max(0, TDS_THRESHOLD - cumulative_value),
        "message": f"{'⚠️ TDS/TCS applicable - purchases exceed ₹50 Lakh' if threshold_exceeded else f'₹{(TDS_THRESHOLD - cumulative_value):,.0f} remaining before TDS threshold'}"
    }

# ==================== GRN ENDPOINTS ====================
@router.post("/grn", response_model=GRN)
async def create_grn(grn_data: GRNCreate, current_user: dict = Depends(get_current_user)):
    grn_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc)
    grn_number = f"GRN-{now.strftime('%Y%m%d')}-{str(uuid.uuid4())[:6].upper()}"
    
    # Get PO details
    po = await db.purchase_orders.find_one({"id": grn_data.po_id}, {"_id": 0})
    if not po:
        raise HTTPException(status_code=404, detail="Purchase Order not found")
    
    # Process items
    total_qty = 0
    accepted_qty = 0
    rejected_qty = 0
    total_value = 0
    
    items_with_details = []
    for item in grn_data.items:
        po_item = po["items"][item.po_item_index] if item.po_item_index < len(po["items"]) else None
        
        items_with_details.append({
            **item.model_dump(),
            "item_code": po_item.get("item_code") if po_item else "",
            "item_name": po_item.get("item_name") if po_item else "",
            "uom": po_item.get("uom") if po_item else "",
            "line_value": item.accepted_qty * item.unit_price
        })
        
        total_qty += item.received_qty
        accepted_qty += item.accepted_qty
        rejected_qty += item.rejected_qty
        total_value += item.accepted_qty * item.unit_price
    
    grn_doc = {
        "id": grn_id,
        "grn_number": grn_number,
        "po_id": grn_data.po_id,
        "po_number": po.get("po_number"),
        "supplier_id": po.get("supplier_id"),
        "supplier_name": po.get("supplier_name"),
        "warehouse_id": po.get("warehouse_id"),
        "items": items_with_details,
        "total_qty": total_qty,
        "accepted_qty": accepted_qty,
        "rejected_qty": rejected_qty,
        "total_value": round(total_value, 2),
        "invoice_no": grn_data.invoice_no,
        "invoice_date": grn_data.invoice_date,
        "invoice_amount": grn_data.invoice_amount,
        "lr_no": grn_data.lr_no,
        "vehicle_no": grn_data.vehicle_no,
        "notes": grn_data.notes,
        "status": "pending_qc",
        "qc_status": None,
        "created_by": current_user["id"],
        "created_at": now.isoformat()
    }
    
    await db.grn.insert_one(grn_doc)
    
    # Update PO received quantities
    po_items = po["items"]
    for item in grn_data.items:
        if item.po_item_index < len(po_items):
            po_items[item.po_item_index]["received_qty"] = po_items[item.po_item_index].get("received_qty", 0) + item.accepted_qty
    
    # Check if PO is fully received
    all_received = all(
        item.get("received_qty", 0) >= item.get("quantity", 0)
        for item in po_items
    )
    new_status = "received" if all_received else "partial"
    
    await db.purchase_orders.update_one(
        {"id": grn_data.po_id},
        {"$set": {
            "items": po_items,
            "status": new_status,
            "received_value": po.get("received_value", 0) + total_value,
            "updated_at": now.isoformat()
        }}
    )
    
    return GRN(**{k: v for k, v in grn_doc.items() if k != '_id'})

@router.get("/grn", response_model=List[GRN])
async def get_grns(
    po_id: Optional[str] = None,
    supplier_id: Optional[str] = None,
    status: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    query = {}
    if po_id:
        query["po_id"] = po_id
    if supplier_id:
        query["supplier_id"] = supplier_id
    if status:
        query["status"] = status
    
    grns = await db.grn.find(query, {"_id": 0}).sort("created_at", -1).to_list(500)
    return [GRN(**g) for g in grns]

@router.put("/grn/{grn_id}/approve")
async def approve_grn(grn_id: str, current_user: dict = Depends(get_current_user)):
    """Approve GRN and update stock"""
    grn = await db.grn.find_one({"id": grn_id}, {"_id": 0})
    if not grn:
        raise HTTPException(status_code=404, detail="GRN not found")
    
    if grn["status"] != "pending_qc":
        raise HTTPException(status_code=400, detail="GRN already processed")
    
    now = datetime.now(timezone.utc).isoformat()
    
    # Add stock for each accepted item
    for item in grn["items"]:
        if item["accepted_qty"] > 0:
            # Create stock entry
            from routes.inventory import StockEntry, create_stock_entry
            entry = StockEntry(
                item_id=item["item_id"],
                warehouse_id=grn["warehouse_id"],
                quantity=item["accepted_qty"],
                transaction_type="receipt",
                reference_type="GRN",
                reference_id=grn_id,
                batch_no=item.get("batch_no"),
                expiry_date=item.get("expiry_date"),
                unit_cost=item["unit_price"]
            )
            await create_stock_entry(entry, current_user)
    
    await db.grn.update_one(
        {"id": grn_id},
        {"$set": {"status": "approved", "qc_status": "passed", "approved_at": now}}
    )
    
    return {"message": "GRN approved and stock updated"}

# ==================== STATS ====================
@router.get("/stats/overview")
async def get_procurement_stats(current_user: dict = Depends(get_current_user)):
    total_suppliers = await db.suppliers.count_documents({"is_active": True})
    
    # PO stats
    total_pos = await db.purchase_orders.count_documents({})
    pending_pos = await db.purchase_orders.count_documents({"status": {"$in": ["draft", "sent"]}})
    
    # PO value
    po_value_pipeline = [
        {"$match": {"status": {"$nin": ["cancelled"]}}},
        {"$group": {"_id": None, "total": {"$sum": "$grand_total"}}}
    ]
    po_value = await db.purchase_orders.aggregate(po_value_pipeline).to_list(1)
    total_po_value = po_value[0]["total"] if po_value else 0
    
    # Pending GRNs
    pending_grns = await db.grn.count_documents({"status": "pending_qc"})
    
    # This month's purchases
    now = datetime.now(timezone.utc)
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0).isoformat()
    monthly_pipeline = [
        {"$match": {"created_at": {"$gte": month_start}, "status": {"$nin": ["cancelled"]}}},
        {"$group": {"_id": None, "total": {"$sum": "$grand_total"}, "count": {"$sum": 1}}}
    ]
    monthly_result = await db.purchase_orders.aggregate(monthly_pipeline).to_list(1)
    
    # Top suppliers
    top_suppliers_pipeline = [
        {"$match": {"is_active": True}},
        {"$sort": {"total_value": -1}},
        {"$limit": 5},
        {"$project": {"supplier_name": 1, "total_value": 1, "total_orders": 1}}
    ]
    top_suppliers = await db.suppliers.aggregate(top_suppliers_pipeline).to_list(5)
    
    return {
        "total_suppliers": total_suppliers,
        "total_pos": total_pos,
        "pending_pos": pending_pos,
        "total_po_value": round(total_po_value, 2),
        "pending_grns": pending_grns,
        "monthly_purchases": monthly_result[0]["total"] if monthly_result else 0,
        "monthly_po_count": monthly_result[0]["count"] if monthly_result else 0,
        "top_suppliers": [{k: v for k, v in s.items() if k != '_id'} for s in top_suppliers]
    }
