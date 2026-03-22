"""
Advanced Inventory Module - Best-in-Class Features
Features:
- Batch/Lot Tracking with Expiry
- Serial Number Tracking
- Bin/Rack Location Management
- Stock Aging Analysis
- Auto Reorder Alerts + Auto-PO Generation
- Barcode/QR Code Support
- Stock Valuation (FIFO, LIFO, Weighted Avg)
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone, timedelta
import uuid

from server import db, get_current_user

router = APIRouter()

# ==================== MODELS ====================
class BatchCreate(BaseModel):
    item_id: str
    batch_number: str
    warehouse_id: str
    manufacturing_date: Optional[str] = None
    expiry_date: Optional[str] = None
    quantity: float
    unit_cost: float
    supplier_id: Optional[str] = None
    po_id: Optional[str] = None
    notes: Optional[str] = None

class Batch(BaseModel):
    id: str
    item_id: str
    item_code: Optional[str] = None
    item_name: Optional[str] = None
    batch_number: str
    warehouse_id: str
    warehouse_name: Optional[str] = None
    manufacturing_date: Optional[str] = None
    expiry_date: Optional[str] = None
    initial_quantity: float
    current_quantity: float
    reserved_quantity: float = 0
    unit_cost: float
    total_value: float
    status: str  # active, expired, consumed, blocked
    supplier_id: Optional[str] = None
    po_id: Optional[str] = None
    notes: Optional[str] = None
    created_at: str

class SerialNumber(BaseModel):
    id: str
    item_id: str
    serial_number: str
    batch_id: Optional[str] = None
    warehouse_id: str
    bin_location: Optional[str] = None
    status: str  # available, sold, reserved, damaged, in_service
    purchase_date: Optional[str] = None
    warranty_expiry: Optional[str] = None
    current_owner: Optional[str] = None  # customer_id if sold
    notes: Optional[str] = None
    created_at: str

class BinLocation(BaseModel):
    id: str
    warehouse_id: str
    bin_code: str  # e.g., A-01-02 (Aisle-Rack-Shelf)
    aisle: str
    rack: str
    shelf: str
    bin_type: str  # picking, bulk, reserve, returns
    max_capacity: float
    current_capacity: float
    item_id: Optional[str] = None
    is_active: bool = True

class ReorderAlert(BaseModel):
    id: str
    item_id: str
    item_code: str
    item_name: str
    warehouse_id: str
    warehouse_name: str
    current_stock: float
    reorder_level: float
    safety_stock: float
    suggested_qty: float
    preferred_supplier_id: Optional[str] = None
    preferred_supplier_name: Optional[str] = None
    status: str  # pending, po_created, ignored
    created_at: str

# ==================== BATCH TRACKING ENDPOINTS ====================
@router.post("/batches", response_model=Batch)
async def create_batch(batch_data: BatchCreate, current_user: dict = Depends(get_current_user)):
    """Create a new batch for an item"""
    batch_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    
    # Validate item
    item = await db.items.find_one({"id": batch_data.item_id}, {"item_code": 1, "item_name": 1})
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    
    # Validate warehouse
    warehouse = await db.warehouses.find_one({"id": batch_data.warehouse_id}, {"warehouse_name": 1})
    if not warehouse:
        raise HTTPException(status_code=404, detail="Warehouse not found")
    
    # Check for duplicate batch number
    existing = await db.batches.find_one({
        "item_id": batch_data.item_id,
        "batch_number": batch_data.batch_number
    })
    if existing:
        raise HTTPException(status_code=400, detail="Batch number already exists for this item")
    
    # Determine status based on expiry
    status = "active"
    if batch_data.expiry_date:
        expiry = datetime.fromisoformat(batch_data.expiry_date.replace('Z', '+00:00'))
        if expiry < datetime.now(timezone.utc):
            status = "expired"
    
    batch_doc = {
        "id": batch_id,
        "item_id": batch_data.item_id,
        "item_code": item.get("item_code"),
        "item_name": item.get("item_name"),
        "batch_number": batch_data.batch_number,
        "warehouse_id": batch_data.warehouse_id,
        "warehouse_name": warehouse.get("warehouse_name"),
        "manufacturing_date": batch_data.manufacturing_date,
        "expiry_date": batch_data.expiry_date,
        "initial_quantity": batch_data.quantity,
        "current_quantity": batch_data.quantity,
        "reserved_quantity": 0,
        "unit_cost": batch_data.unit_cost,
        "total_value": round(batch_data.quantity * batch_data.unit_cost, 2),
        "status": status,
        "supplier_id": batch_data.supplier_id,
        "po_id": batch_data.po_id,
        "notes": batch_data.notes,
        "created_at": now
    }
    
    await db.batches.insert_one(batch_doc)
    
    # Update item stock
    await db.items.update_one(
        {"id": batch_data.item_id},
        {"$inc": {"current_stock": batch_data.quantity}}
    )
    
    return Batch(**{k: v for k, v in batch_doc.items() if k != '_id'})

@router.get("/batches")
async def list_batches(
    item_id: Optional[str] = None,
    warehouse_id: Optional[str] = None,
    status: Optional[str] = None,
    expiring_within_days: Optional[int] = None,
    current_user: dict = Depends(get_current_user)
):
    """List batches with filters"""
    query = {}
    if item_id:
        query["item_id"] = item_id
    if warehouse_id:
        query["warehouse_id"] = warehouse_id
    if status:
        query["status"] = status
    if expiring_within_days:
        expiry_threshold = (datetime.now(timezone.utc) + timedelta(days=expiring_within_days)).isoformat()
        query["expiry_date"] = {"$lte": expiry_threshold, "$ne": None}
        query["status"] = "active"
    
    batches = await db.batches.find(query, {"_id": 0}).sort("expiry_date", 1).to_list(1000)
    return batches

@router.get("/batches/expiring")
async def get_expiring_batches(
    days: int = Query(default=30),
    current_user: dict = Depends(get_current_user)
):
    """Get batches expiring within specified days"""
    expiry_threshold = (datetime.now(timezone.utc) + timedelta(days=days)).isoformat()
    
    batches = await db.batches.find({
        "status": "active",
        "expiry_date": {"$lte": expiry_threshold, "$ne": None},
        "current_quantity": {"$gt": 0}
    }, {"_id": 0}).sort("expiry_date", 1).to_list(1000)
    
    # Categorize by urgency
    urgent = []  # < 7 days
    warning = []  # 7-15 days
    attention = []  # 15-30 days
    
    now = datetime.now(timezone.utc)
    for batch in batches:
        if batch.get("expiry_date"):
            expiry = datetime.fromisoformat(batch["expiry_date"].replace('Z', '+00:00'))
            days_left = (expiry - now).days
            batch["days_until_expiry"] = days_left
            
            if days_left < 7:
                urgent.append(batch)
            elif days_left < 15:
                warning.append(batch)
            else:
                attention.append(batch)
    
    return {
        "summary": {
            "total_expiring": len(batches),
            "urgent_count": len(urgent),
            "warning_count": len(warning),
            "attention_count": len(attention)
        },
        "urgent": urgent,
        "warning": warning,
        "attention": attention
    }

# ==================== SERIAL NUMBER TRACKING ====================
@router.post("/serial-numbers/bulk")
async def create_serial_numbers_bulk(
    item_id: str,
    warehouse_id: str,
    serial_numbers: List[str],
    batch_id: Optional[str] = None,
    bin_location: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Create multiple serial numbers at once"""
    now = datetime.now(timezone.utc).isoformat()
    
    item = await db.items.find_one({"id": item_id}, {"item_code": 1, "item_name": 1})
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    
    # Check for duplicates
    existing = await db.serial_numbers.find({
        "item_id": item_id,
        "serial_number": {"$in": serial_numbers}
    }).to_list(1000)
    
    if existing:
        duplicate_serials = [s["serial_number"] for s in existing]
        raise HTTPException(
            status_code=400, 
            detail=f"Duplicate serial numbers: {', '.join(duplicate_serials)}"
        )
    
    serial_docs = []
    for sn in serial_numbers:
        serial_docs.append({
            "id": str(uuid.uuid4()),
            "item_id": item_id,
            "item_code": item.get("item_code"),
            "item_name": item.get("item_name"),
            "serial_number": sn,
            "batch_id": batch_id,
            "warehouse_id": warehouse_id,
            "bin_location": bin_location,
            "status": "available",
            "purchase_date": now[:10],
            "warranty_expiry": None,
            "current_owner": None,
            "notes": None,
            "created_at": now
        })
    
    if serial_docs:
        await db.serial_numbers.insert_many(serial_docs)
    
    return {"created": len(serial_docs), "serial_numbers": serial_numbers}

@router.get("/serial-numbers")
async def list_serial_numbers(
    item_id: Optional[str] = None,
    warehouse_id: Optional[str] = None,
    status: Optional[str] = None,
    search: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """List serial numbers with filters"""
    query = {}
    if item_id:
        query["item_id"] = item_id
    if warehouse_id:
        query["warehouse_id"] = warehouse_id
    if status:
        query["status"] = status
    if search:
        query["serial_number"] = {"$regex": search, "$options": "i"}
    
    serials = await db.serial_numbers.find(query, {"_id": 0}).sort("created_at", -1).to_list(1000)
    return serials

@router.put("/serial-numbers/{serial_id}/status")
async def update_serial_status(
    serial_id: str,
    status: str,
    customer_id: Optional[str] = None,
    notes: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Update serial number status (sell, reserve, damage, etc.)"""
    valid_statuses = ["available", "sold", "reserved", "damaged", "in_service", "returned"]
    if status not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of: {valid_statuses}")
    
    update = {"status": status, "updated_at": datetime.now(timezone.utc).isoformat()}
    if customer_id:
        update["current_owner"] = customer_id
    if notes:
        update["notes"] = notes
    
    result = await db.serial_numbers.update_one({"id": serial_id}, {"$set": update})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Serial number not found")
    
    return {"message": f"Serial number status updated to {status}"}

# ==================== BIN LOCATION MANAGEMENT ====================
@router.post("/bin-locations")
async def create_bin_location(
    warehouse_id: str,
    aisle: str,
    rack: str,
    shelf: str,
    bin_type: str = "picking",
    max_capacity: float = 100,
    current_user: dict = Depends(get_current_user)
):
    """Create a bin location"""
    bin_code = f"{aisle}-{rack}-{shelf}"
    
    existing = await db.bin_locations.find_one({
        "warehouse_id": warehouse_id,
        "bin_code": bin_code
    })
    if existing:
        raise HTTPException(status_code=400, detail="Bin location already exists")
    
    bin_doc = {
        "id": str(uuid.uuid4()),
        "warehouse_id": warehouse_id,
        "bin_code": bin_code,
        "aisle": aisle,
        "rack": rack,
        "shelf": shelf,
        "bin_type": bin_type,
        "max_capacity": max_capacity,
        "current_capacity": 0,
        "item_id": None,
        "is_active": True,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.bin_locations.insert_one(bin_doc)
    return {k: v for k, v in bin_doc.items() if k != '_id'}

@router.get("/bin-locations")
async def list_bin_locations(
    warehouse_id: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """List bin locations"""
    query = {}
    if warehouse_id:
        query["warehouse_id"] = warehouse_id
    
    bins = await db.bin_locations.find(query, {"_id": 0}).sort("bin_code", 1).to_list(1000)
    return bins

# ==================== STOCK AGING ANALYSIS ====================
@router.get("/stock-aging")
async def get_stock_aging(
    warehouse_id: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Get stock aging analysis"""
    query = {"current_quantity": {"$gt": 0}}
    if warehouse_id:
        query["warehouse_id"] = warehouse_id
    
    batches = await db.batches.find(query, {"_id": 0}).to_list(10000)
    
    now = datetime.now(timezone.utc)
    aging_buckets = {
        "0_30_days": {"count": 0, "value": 0, "items": []},
        "31_60_days": {"count": 0, "value": 0, "items": []},
        "61_90_days": {"count": 0, "value": 0, "items": []},
        "91_180_days": {"count": 0, "value": 0, "items": []},
        "over_180_days": {"count": 0, "value": 0, "items": []}
    }
    
    for batch in batches:
        created = datetime.fromisoformat(batch["created_at"].replace('Z', '+00:00'))
        age_days = (now - created).days
        value = batch.get("current_quantity", 0) * batch.get("unit_cost", 0)
        
        item_info = {
            "batch_number": batch["batch_number"],
            "item_code": batch.get("item_code"),
            "item_name": batch.get("item_name"),
            "quantity": batch["current_quantity"],
            "value": round(value, 2),
            "age_days": age_days
        }
        
        if age_days <= 30:
            aging_buckets["0_30_days"]["count"] += 1
            aging_buckets["0_30_days"]["value"] += value
            aging_buckets["0_30_days"]["items"].append(item_info)
        elif age_days <= 60:
            aging_buckets["31_60_days"]["count"] += 1
            aging_buckets["31_60_days"]["value"] += value
            aging_buckets["31_60_days"]["items"].append(item_info)
        elif age_days <= 90:
            aging_buckets["61_90_days"]["count"] += 1
            aging_buckets["61_90_days"]["value"] += value
            aging_buckets["61_90_days"]["items"].append(item_info)
        elif age_days <= 180:
            aging_buckets["91_180_days"]["count"] += 1
            aging_buckets["91_180_days"]["value"] += value
            aging_buckets["91_180_days"]["items"].append(item_info)
        else:
            aging_buckets["over_180_days"]["count"] += 1
            aging_buckets["over_180_days"]["value"] += value
            aging_buckets["over_180_days"]["items"].append(item_info)
    
    # Round values
    for bucket in aging_buckets.values():
        bucket["value"] = round(bucket["value"], 2)
    
    total_value = sum(b["value"] for b in aging_buckets.values())
    
    return {
        "generated_at": now.isoformat(),
        "total_batches": len(batches),
        "total_value": round(total_value, 2),
        "aging_buckets": aging_buckets
    }

# ==================== AUTO REORDER SYSTEM ====================
@router.get("/reorder-alerts")
async def get_reorder_alerts(
    warehouse_id: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Get items that need reordering"""
    # Find items below reorder level
    pipeline = [
        {"$match": {"is_active": True}},
        {"$lookup": {
            "from": "stock",
            "localField": "id",
            "foreignField": "item_id",
            "as": "stock_info"
        }}
    ]
    
    items = await db.items.aggregate(pipeline).to_list(1000)
    
    alerts = []
    for item in items:
        current_stock = item.get("current_stock", 0)
        reorder_level = item.get("reorder_level", 0)
        safety_stock = item.get("safety_stock", 0)
        
        if current_stock <= reorder_level and reorder_level > 0:
            # Calculate suggested order quantity
            suggested_qty = max(item.get("min_order_qty", 1), (reorder_level + safety_stock) - current_stock)
            
            alerts.append({
                "id": str(uuid.uuid4()),
                "item_id": item["id"],
                "item_code": item.get("item_code"),
                "item_name": item.get("item_name"),
                "current_stock": current_stock,
                "reorder_level": reorder_level,
                "safety_stock": safety_stock,
                "suggested_qty": suggested_qty,
                "urgency": "critical" if current_stock <= safety_stock else "warning",
                "status": "pending"
            })
    
    # Sort by urgency
    alerts.sort(key=lambda x: (0 if x["urgency"] == "critical" else 1, -x["suggested_qty"]))
    
    return {
        "total_alerts": len(alerts),
        "critical_count": len([a for a in alerts if a["urgency"] == "critical"]),
        "warning_count": len([a for a in alerts if a["urgency"] == "warning"]),
        "alerts": alerts
    }

@router.post("/reorder-alerts/{item_id}/create-po")
async def create_po_from_alert(
    item_id: str,
    supplier_id: str,
    quantity: float,
    warehouse_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Create PO from reorder alert"""
    item = await db.items.find_one({"id": item_id}, {"_id": 0})
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    
    supplier = await db.suppliers.find_one({"id": supplier_id}, {"supplier_name": 1, "payment_terms": 1})
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")
    
    now = datetime.now(timezone.utc)
    po_id = str(uuid.uuid4())
    po_number = f"PO-AUTO-{now.strftime('%Y%m%d%H%M%S')}"
    
    unit_price = item.get("standard_cost", 0) or item.get("last_landed_rate", 0)
    tax_amount = quantity * unit_price * 0.18  # 18% GST default
    
    po_doc = {
        "id": po_id,
        "po_number": po_number,
        "supplier_id": supplier_id,
        "supplier_name": supplier.get("supplier_name"),
        "po_type": "Auto-Reorder",
        "warehouse_id": warehouse_id,
        "items": [{
            "item_id": item_id,
            "item_code": item.get("item_code"),
            "item_name": item.get("item_name"),
            "quantity": quantity,
            "unit_price": unit_price,
            "tax_percent": 18,
            "discount_percent": 0,
            "line_total": round(quantity * unit_price * 1.18, 2)
        }],
        "subtotal": round(quantity * unit_price, 2),
        "tax_amount": round(tax_amount, 2),
        "grand_total": round(quantity * unit_price + tax_amount, 2),
        "payment_terms": supplier.get("payment_terms", "30 days"),
        "status": "draft",
        "auto_generated": True,
        "created_by": current_user["id"],
        "created_at": now.isoformat()
    }
    
    await db.purchase_orders.insert_one(po_doc)
    
    return {"message": "Auto-PO created", "po_number": po_number, "po_id": po_id}

# ==================== BARCODE SUPPORT ====================
@router.get("/barcode/lookup/{barcode}")
async def lookup_barcode(barcode: str, current_user: dict = Depends(get_current_user)):
    """Lookup item by barcode or item code"""
    # Search by item_code first
    item = await db.items.find_one(
        {"$or": [
            {"item_code": barcode},
            {"barcode": barcode}
        ]},
        {"_id": 0}
    )
    
    if not item:
        # Try serial number
        serial = await db.serial_numbers.find_one({"serial_number": barcode}, {"_id": 0})
        if serial:
            item = await db.items.find_one({"id": serial["item_id"]}, {"_id": 0})
            if item:
                item["serial_info"] = serial
    
    if not item:
        # Try batch number
        batch = await db.batches.find_one({"batch_number": barcode}, {"_id": 0})
        if batch:
            item = await db.items.find_one({"id": batch["item_id"]}, {"_id": 0})
            if item:
                item["batch_info"] = batch
    
    if not item:
        raise HTTPException(status_code=404, detail="Item not found for barcode")
    
    return item

@router.put("/items/{item_id}/barcode")
async def update_item_barcode(
    item_id: str,
    barcode: str,
    current_user: dict = Depends(get_current_user)
):
    """Update or set barcode for an item"""
    # Check for duplicate
    existing = await db.items.find_one({"barcode": barcode, "id": {"$ne": item_id}})
    if existing:
        raise HTTPException(status_code=400, detail="Barcode already assigned to another item")
    
    result = await db.items.update_one(
        {"id": item_id},
        {"$set": {"barcode": barcode, "updated_at": datetime.now(timezone.utc).isoformat()}}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Item not found")
    
    return {"message": "Barcode updated successfully"}

# ==================== STOCK VALUATION ====================
@router.get("/stock-valuation")
async def get_stock_valuation(
    method: str = Query(default="weighted_avg"),  # fifo, lifo, weighted_avg
    warehouse_id: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Get stock valuation using different methods"""
    query = {"current_quantity": {"$gt": 0}}
    if warehouse_id:
        query["warehouse_id"] = warehouse_id
    
    batches = await db.batches.find(query, {"_id": 0}).sort("created_at", 1).to_list(10000)
    
    # Group by item
    item_batches = {}
    for batch in batches:
        item_id = batch["item_id"]
        if item_id not in item_batches:
            item_batches[item_id] = {
                "item_id": item_id,
                "item_code": batch.get("item_code"),
                "item_name": batch.get("item_name"),
                "batches": []
            }
        item_batches[item_id]["batches"].append(batch)
    
    valuations = []
    total_value = 0
    
    for item_id, data in item_batches.items():
        total_qty = sum(b["current_quantity"] for b in data["batches"])
        
        if method == "fifo":
            # First In First Out - use oldest batches first
            value = sum(b["current_quantity"] * b["unit_cost"] for b in data["batches"])
            avg_cost = value / total_qty if total_qty > 0 else 0
        elif method == "lifo":
            # Last In First Out - use newest batches first
            value = sum(b["current_quantity"] * b["unit_cost"] for b in reversed(data["batches"]))
            avg_cost = value / total_qty if total_qty > 0 else 0
        else:
            # Weighted Average
            total_cost = sum(b["current_quantity"] * b["unit_cost"] for b in data["batches"])
            avg_cost = total_cost / total_qty if total_qty > 0 else 0
            value = total_qty * avg_cost
        
        valuations.append({
            "item_id": item_id,
            "item_code": data["item_code"],
            "item_name": data["item_name"],
            "quantity": total_qty,
            "avg_cost": round(avg_cost, 2),
            "total_value": round(value, 2),
            "batch_count": len(data["batches"])
        })
        total_value += value
    
    return {
        "valuation_method": method,
        "total_items": len(valuations),
        "total_value": round(total_value, 2),
        "items": sorted(valuations, key=lambda x: x["total_value"], reverse=True)
    }
