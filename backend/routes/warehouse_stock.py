"""
Warehouse & Stock Management Module
GST-wise warehouse management with full barcoding, batch tracking, and stock operations
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
import uuid
import qrcode
from io import BytesIO
import base64
from server import db, get_current_user

router = APIRouter()

# ==================== PYDANTIC MODELS ====================

class WarehouseCreate(BaseModel):
    warehouse_code: str
    warehouse_name: str
    prefix: str  # For document serial numbers
    gstin: str
    pincode: Optional[str] = None
    state: Optional[str] = None
    city: Optional[str] = None
    address: Optional[str] = None
    bank_name: Optional[str] = None
    bank_account: Optional[str] = None
    ifsc_code: Optional[str] = None
    bank_branch: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    contact_person: Optional[str] = None
    is_active: Optional[bool] = True


class SerialNumberConfig(BaseModel):
    doc_type: str  # quotation, invoice, purchase_order, etc.
    warehouse_id: str
    prefix: Optional[str] = None
    suffix: Optional[str] = None
    separator: Optional[str] = "/"
    include_fy: Optional[bool] = True
    fy_format: Optional[str] = "2425"  # Short format
    number_length: Optional[int] = 4
    current_number: Optional[int] = 0
    reset_on_fy: Optional[bool] = True


class StockEntry(BaseModel):
    item_id: str
    warehouse_id: str
    batch_no: Optional[str] = None
    quantity: float
    uom: str
    rack_location: Optional[str] = None
    cost_price: Optional[float] = None
    expiry_date: Optional[str] = None
    barcode: Optional[str] = None


class StockTransferCreate(BaseModel):
    from_warehouse_id: str
    to_warehouse_id: str
    items: List[Dict[str, Any]]  # [{item_id, batch_no, quantity}]
    vehicle_no: Optional[str] = None
    driver_name: Optional[str] = None
    driver_phone: Optional[str] = None
    notes: Optional[str] = None


class StockAdjustmentCreate(BaseModel):
    warehouse_id: str
    adjustment_type: str  # opening, closing, increase, decrease, damage, expired, recount
    items: List[Dict[str, Any]]  # [{item_id, batch_no, current_qty, adjusted_qty}]
    reason: Optional[str] = None
    reference: Optional[str] = None


class BatchCreate(BaseModel):
    item_id: str
    warehouse_id: str
    quantity: float
    manufacturing_date: Optional[str] = None
    expiry_date: Optional[str] = None
    cost_price: Optional[float] = None
    supplier_batch: Optional[str] = None


# ==================== WAREHOUSE CRUD ====================

@router.get("/warehouses")
async def get_warehouses(
    include_inactive: bool = False,
    current_user: dict = Depends(get_current_user)
):
    """Get all warehouses with stock summary"""
    query = {} if include_inactive else {"is_active": {"$ne": False}}
    
    warehouses = await db.warehouses.find(query, {"_id": 0}).to_list(100)
    
    # Add stock summary for each warehouse
    for wh in warehouses:
        # Count total items and value
        stock_summary = await db.stock_entries.aggregate([
            {"$match": {"warehouse_id": wh.get("id")}},
            {"$group": {
                "_id": None,
                "total_items": {"$sum": 1},
                "total_quantity": {"$sum": "$quantity"},
                "total_value": {"$sum": {"$multiply": ["$quantity", {"$ifNull": ["$cost_price", 0]}]}}
            }}
        ]).to_list(1)
        
        wh["stock_summary"] = stock_summary[0] if stock_summary else {"total_items": 0, "total_quantity": 0, "total_value": 0}
    
    return warehouses


@router.post("/warehouses")
async def create_warehouse(warehouse: WarehouseCreate, current_user: dict = Depends(get_current_user)):
    """Create a new warehouse (GST-wise)"""
    if current_user.get('role') not in ['admin', 'director']:
        raise HTTPException(status_code=403, detail="Only admin or director can create warehouses")
    
    # Check for duplicate GSTIN
    existing = await db.warehouses.find_one({"gstin": warehouse.gstin})
    if existing:
        raise HTTPException(status_code=400, detail="A warehouse with this GSTIN already exists")
    
    # Check for duplicate code
    existing_code = await db.warehouses.find_one({"warehouse_code": warehouse.warehouse_code})
    if existing_code:
        raise HTTPException(status_code=400, detail="A warehouse with this code already exists")
    
    warehouse_dict = warehouse.model_dump()
    warehouse_dict["id"] = str(uuid.uuid4())
    warehouse_dict["created_at"] = datetime.now(timezone.utc).isoformat()
    warehouse_dict["created_by"] = current_user["id"]
    
    await db.warehouses.insert_one(warehouse_dict)
    
    # Create default serial number configs for this warehouse
    doc_types = ["quotation", "sales_order", "invoice", "credit_note", "purchase_order", "grn", "stock_transfer", "batch", "sample"]
    for doc_type in doc_types:
        serial_config = {
            "id": str(uuid.uuid4()),
            "doc_type": doc_type,
            "warehouse_id": warehouse_dict["id"],
            "prefix": f"{warehouse.prefix}/{doc_type[:3].upper()}",
            "separator": "/",
            "include_fy": True,
            "fy_format": "2425",
            "number_length": 4,
            "current_number": 0,
            "reset_on_fy": True,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        await db.serial_number_configs.insert_one(serial_config)
    
    return {"message": "Warehouse created successfully", "id": warehouse_dict["id"], "warehouse": warehouse_dict}


@router.get("/warehouses/{warehouse_id}")
async def get_warehouse(warehouse_id: str, current_user: dict = Depends(get_current_user)):
    """Get warehouse details with full stock register"""
    warehouse = await db.warehouses.find_one({"id": warehouse_id}, {"_id": 0})
    if not warehouse:
        raise HTTPException(status_code=404, detail="Warehouse not found")
    
    # Get stock entries
    stock = await db.stock_entries.find({"warehouse_id": warehouse_id}, {"_id": 0}).to_list(1000)
    warehouse["stock"] = stock
    
    # Get serial number configs
    serial_configs = await db.serial_number_configs.find({"warehouse_id": warehouse_id}, {"_id": 0}).to_list(20)
    warehouse["serial_configs"] = serial_configs
    
    return warehouse


@router.put("/warehouses/{warehouse_id}")
async def update_warehouse(warehouse_id: str, warehouse: WarehouseCreate, current_user: dict = Depends(get_current_user)):
    """Update warehouse details"""
    if current_user.get('role') not in ['admin', 'director']:
        raise HTTPException(status_code=403, detail="Only admin or director can update warehouses")
    
    existing = await db.warehouses.find_one({"id": warehouse_id})
    if not existing:
        raise HTTPException(status_code=404, detail="Warehouse not found")
    
    update_data = warehouse.model_dump()
    update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
    update_data["updated_by"] = current_user["id"]
    
    await db.warehouses.update_one({"id": warehouse_id}, {"$set": update_data})
    
    return {"message": "Warehouse updated successfully"}


# ==================== SERIAL NUMBER MANAGEMENT ====================

@router.get("/serial-configs")
async def get_serial_configs(
    warehouse_id: Optional[str] = None,
    doc_type: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Get serial number configurations"""
    query = {}
    if warehouse_id:
        query["warehouse_id"] = warehouse_id
    if doc_type:
        query["doc_type"] = doc_type
    
    configs = await db.serial_number_configs.find(query, {"_id": 0}).to_list(100)
    
    # Generate sample format for each
    for config in configs:
        config["sample_format"] = generate_sample_serial(config)
    
    return configs


@router.post("/serial-configs")
async def create_serial_config(config: SerialNumberConfig, current_user: dict = Depends(get_current_user)):
    """Create or update serial number configuration"""
    if current_user.get('role') not in ['admin', 'director']:
        raise HTTPException(status_code=403, detail="Only admin can configure serial numbers")
    
    # Check if config exists for this doc_type and warehouse
    existing = await db.serial_number_configs.find_one({
        "doc_type": config.doc_type,
        "warehouse_id": config.warehouse_id
    })
    
    config_dict = config.model_dump()
    config_dict["updated_at"] = datetime.now(timezone.utc).isoformat()
    
    if existing:
        await db.serial_number_configs.update_one(
            {"doc_type": config.doc_type, "warehouse_id": config.warehouse_id},
            {"$set": config_dict}
        )
    else:
        config_dict["id"] = str(uuid.uuid4())
        config_dict["created_at"] = config_dict["updated_at"]
        await db.serial_number_configs.insert_one(config_dict)
    
    return {"message": "Serial configuration saved", "sample_format": generate_sample_serial(config_dict)}


@router.get("/generate-serial/{doc_type}/{warehouse_id}")
async def generate_serial_number(doc_type: str, warehouse_id: str, current_user: dict = Depends(get_current_user)):
    """Generate next serial number for a document type"""
    config = await db.serial_number_configs.find_one({
        "doc_type": doc_type,
        "warehouse_id": warehouse_id
    })
    
    if not config:
        # Use default format
        config = {
            "prefix": doc_type[:3].upper(),
            "separator": "/",
            "include_fy": True,
            "fy_format": "2425",
            "number_length": 4,
            "current_number": 0
        }
    
    # Get current financial year
    now = datetime.now()
    fy_start_year = now.year if now.month >= 4 else now.year - 1
    fy_end_year = fy_start_year + 1
    
    if config.get("fy_format") == "2425":
        fy = f"{str(fy_start_year)[-2:]}{str(fy_end_year)[-2:]}"
    elif config.get("fy_format") == "24-25":
        fy = f"{str(fy_start_year)[-2:]}-{str(fy_end_year)[-2:]}"
    else:
        fy = f"{fy_start_year}-{str(fy_end_year)[-2:]}"
    
    # Increment number
    next_number = (config.get("current_number", 0) or 0) + 1
    
    # Build serial number
    sep = config.get("separator", "/")
    parts = []
    if config.get("prefix"):
        parts.append(config["prefix"])
    if config.get("include_fy", True):
        parts.append(fy)
    parts.append(str(next_number).zfill(config.get("number_length", 4)))
    if config.get("suffix"):
        parts.append(config["suffix"])
    
    serial_number = sep.join(parts)
    
    # Update current number
    await db.serial_number_configs.update_one(
        {"doc_type": doc_type, "warehouse_id": warehouse_id},
        {"$set": {"current_number": next_number}},
        upsert=True
    )
    
    return {"serial_number": serial_number, "next_number": next_number}


def generate_sample_serial(config: dict) -> str:
    """Generate a sample serial number format"""
    now = datetime.now()
    fy_start_year = now.year if now.month >= 4 else now.year - 1
    fy_end_year = fy_start_year + 1
    
    if config.get("fy_format") == "2425":
        fy = f"{str(fy_start_year)[-2:]}{str(fy_end_year)[-2:]}"
    elif config.get("fy_format") == "24-25":
        fy = f"{str(fy_start_year)[-2:]}-{str(fy_end_year)[-2:]}"
    else:
        fy = f"{fy_start_year}-{str(fy_end_year)[-2:]}"
    
    sep = config.get("separator", "/")
    parts = []
    if config.get("prefix"):
        parts.append(config["prefix"])
    if config.get("include_fy", True):
        parts.append(fy)
    parts.append("0001")
    if config.get("suffix"):
        parts.append(config["suffix"])
    
    return sep.join(parts)


# ==================== BATCH MANAGEMENT ====================

@router.post("/batches")
async def create_batch(batch: BatchCreate, current_user: dict = Depends(get_current_user)):
    """Create a new batch with auto-generated batch number"""
    # Get warehouse for prefix
    warehouse = await db.warehouses.find_one({"id": batch.warehouse_id})
    if not warehouse:
        raise HTTPException(status_code=404, detail="Warehouse not found")
    
    # Get item
    item = await db.items.find_one({"id": batch.item_id})
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    
    # Generate batch number
    batch_serial = await generate_serial_number("batch", batch.warehouse_id, current_user)
    batch_no = batch_serial["serial_number"]
    
    # Generate barcode
    barcode_data = f"{warehouse.get('warehouse_code', 'WH')}-{item.get('item_code', 'ITEM')}-{batch_no}"
    
    batch_dict = batch.model_dump()
    batch_dict["id"] = str(uuid.uuid4())
    batch_dict["batch_no"] = batch_no
    batch_dict["barcode"] = barcode_data
    batch_dict["item_code"] = item.get("item_code")
    batch_dict["item_name"] = item.get("item_name")
    batch_dict["warehouse_code"] = warehouse.get("warehouse_code")
    batch_dict["current_quantity"] = batch.quantity
    batch_dict["created_at"] = datetime.now(timezone.utc).isoformat()
    batch_dict["created_by"] = current_user["id"]
    
    await db.batches.insert_one(batch_dict)
    
    # Create stock entry
    stock_entry = {
        "id": str(uuid.uuid4()),
        "item_id": batch.item_id,
        "item_code": item.get("item_code"),
        "item_name": item.get("item_name"),
        "warehouse_id": batch.warehouse_id,
        "batch_id": batch_dict["id"],
        "batch_no": batch_no,
        "quantity": batch.quantity,
        "uom": item.get("primary_uom", "PCS"),
        "cost_price": batch.cost_price,
        "expiry_date": batch.expiry_date,
        "barcode": barcode_data,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.stock_entries.insert_one(stock_entry)
    
    return {"message": "Batch created", "batch_no": batch_no, "barcode": barcode_data, "batch": batch_dict}


@router.get("/batches")
async def get_batches(
    warehouse_id: Optional[str] = None,
    item_id: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Get batches with filters"""
    query = {}
    if warehouse_id:
        query["warehouse_id"] = warehouse_id
    if item_id:
        query["item_id"] = item_id
    
    batches = await db.batches.find(query, {"_id": 0}).sort("created_at", -1).to_list(500)
    return batches


# ==================== BARCODE & LABEL GENERATION ====================

@router.get("/generate-barcode/{data}")
async def generate_barcode(data: str, format: str = "qr", current_user: dict = Depends(get_current_user)):
    """Generate barcode/QR code for item/batch"""
    if format == "qr":
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(data)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        
        buffer = BytesIO()
        img.save(buffer, format="PNG")
        buffer.seek(0)
        
        img_base64 = base64.b64encode(buffer.getvalue()).decode()
        return {"format": "qr", "data": data, "image": f"data:image/png;base64,{img_base64}"}
    
    return {"format": format, "data": data, "error": "Only QR format supported currently"}


@router.get("/generate-label/{item_id}")
async def generate_label(
    item_id: str,
    batch_no: Optional[str] = None,
    warehouse_id: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Generate label data for printing"""
    item = await db.items.find_one({"id": item_id}, {"_id": 0})
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    
    label_data = {
        "item_code": item.get("item_code"),
        "item_name": item.get("item_name"),
        "category": item.get("category"),
        "specs": f"{item.get('thickness', '')}µ x {item.get('width', '')}mm x {item.get('length', '')}m",
        "color": item.get("color"),
        "uom": item.get("primary_uom"),
        "hsn": item.get("hsn_code"),
        "batch_no": batch_no,
        "barcode_data": f"{item.get('item_code')}-{batch_no or 'STOCK'}"
    }
    
    if warehouse_id:
        warehouse = await db.warehouses.find_one({"id": warehouse_id}, {"_id": 0})
        if warehouse:
            label_data["warehouse"] = warehouse.get("warehouse_name")
            label_data["warehouse_code"] = warehouse.get("warehouse_code")
    
    # Generate QR code
    qr_result = await generate_barcode(label_data["barcode_data"], "qr", current_user)
    label_data["qr_image"] = qr_result.get("image")
    
    return label_data


# ==================== STOCK TRANSFERS ====================

@router.post("/stock-transfers")
async def create_stock_transfer(transfer: StockTransferCreate, current_user: dict = Depends(get_current_user)):
    """Create a stock transfer between warehouses"""
    # Validate warehouses
    from_wh = await db.warehouses.find_one({"id": transfer.from_warehouse_id})
    to_wh = await db.warehouses.find_one({"id": transfer.to_warehouse_id})
    
    if not from_wh or not to_wh:
        raise HTTPException(status_code=404, detail="Warehouse not found")
    
    if transfer.from_warehouse_id == transfer.to_warehouse_id:
        raise HTTPException(status_code=400, detail="Cannot transfer to same warehouse")
    
    # Generate transfer number
    transfer_serial = await generate_serial_number("stock_transfer", transfer.from_warehouse_id, current_user)
    
    transfer_dict = transfer.model_dump()
    transfer_dict["id"] = str(uuid.uuid4())
    transfer_dict["transfer_no"] = transfer_serial["serial_number"]
    transfer_dict["transfer_date"] = datetime.now(timezone.utc).isoformat()
    transfer_dict["from_warehouse_name"] = from_wh.get("warehouse_name")
    transfer_dict["to_warehouse_name"] = to_wh.get("warehouse_name")
    transfer_dict["status"] = "draft"
    transfer_dict["total_items"] = len(transfer.items)
    transfer_dict["created_at"] = datetime.now(timezone.utc).isoformat()
    transfer_dict["created_by"] = current_user["id"]
    
    # Validate stock availability
    for item in transfer.items:
        stock = await db.stock_entries.find_one({
            "item_id": item.get("item_id"),
            "warehouse_id": transfer.from_warehouse_id,
            "batch_no": item.get("batch_no")
        })
        if not stock or stock.get("quantity", 0) < item.get("quantity", 0):
            raise HTTPException(status_code=400, detail=f"Insufficient stock for item {item.get('item_id')}")
    
    await db.stock_transfers.insert_one(transfer_dict)
    
    return {"message": "Stock transfer created", "transfer_no": transfer_dict["transfer_no"], "id": transfer_dict["id"]}


@router.put("/stock-transfers/{transfer_id}/dispatch")
async def dispatch_transfer(transfer_id: str, current_user: dict = Depends(get_current_user)):
    """Dispatch stock transfer - deduct from source warehouse"""
    transfer = await db.stock_transfers.find_one({"id": transfer_id})
    if not transfer:
        raise HTTPException(status_code=404, detail="Transfer not found")
    
    if transfer.get("status") != "draft":
        raise HTTPException(status_code=400, detail="Transfer already dispatched or cancelled")
    
    # Deduct stock from source warehouse
    for item in transfer.get("items", []):
        await db.stock_entries.update_one(
            {
                "item_id": item.get("item_id"),
                "warehouse_id": transfer["from_warehouse_id"],
                "batch_no": item.get("batch_no")
            },
            {"$inc": {"quantity": -item.get("quantity", 0)}}
        )
    
    await db.stock_transfers.update_one(
        {"id": transfer_id},
        {"$set": {"status": "in_transit", "dispatched_at": datetime.now(timezone.utc).isoformat(), "dispatched_by": current_user["id"]}}
    )
    
    return {"message": "Transfer dispatched", "status": "in_transit"}


@router.put("/stock-transfers/{transfer_id}/receive")
async def receive_transfer(transfer_id: str, current_user: dict = Depends(get_current_user)):
    """Receive stock transfer - add to destination warehouse"""
    transfer = await db.stock_transfers.find_one({"id": transfer_id})
    if not transfer:
        raise HTTPException(status_code=404, detail="Transfer not found")
    
    if transfer.get("status") != "in_transit":
        raise HTTPException(status_code=400, detail="Transfer not in transit")
    
    # Add stock to destination warehouse
    for item in transfer.get("items", []):
        # Check if stock entry exists
        existing = await db.stock_entries.find_one({
            "item_id": item.get("item_id"),
            "warehouse_id": transfer["to_warehouse_id"],
            "batch_no": item.get("batch_no")
        })
        
        if existing:
            await db.stock_entries.update_one(
                {"id": existing["id"]},
                {"$inc": {"quantity": item.get("quantity", 0)}}
            )
        else:
            # Create new stock entry
            stock_entry = {
                "id": str(uuid.uuid4()),
                "item_id": item.get("item_id"),
                "warehouse_id": transfer["to_warehouse_id"],
                "batch_no": item.get("batch_no"),
                "quantity": item.get("quantity", 0),
                "uom": item.get("uom", "PCS"),
                "transfer_id": transfer_id,
                "created_at": datetime.now(timezone.utc).isoformat()
            }
            await db.stock_entries.insert_one(stock_entry)
    
    await db.stock_transfers.update_one(
        {"id": transfer_id},
        {"$set": {"status": "received", "received_at": datetime.now(timezone.utc).isoformat(), "received_by": current_user["id"]}}
    )
    
    return {"message": "Transfer received", "status": "received"}


@router.get("/stock-transfers")
async def get_stock_transfers(
    warehouse_id: Optional[str] = None,
    status: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Get stock transfers"""
    query = {}
    if warehouse_id:
        query["$or"] = [{"from_warehouse_id": warehouse_id}, {"to_warehouse_id": warehouse_id}]
    if status:
        query["status"] = status
    
    transfers = await db.stock_transfers.find(query, {"_id": 0}).sort("created_at", -1).to_list(200)
    return transfers


# ==================== STOCK ADJUSTMENTS ====================

@router.post("/stock-adjustments")
async def create_stock_adjustment(adjustment: StockAdjustmentCreate, current_user: dict = Depends(get_current_user)):
    """Create stock adjustment (opening, closing, increase, decrease, damage, etc.)"""
    warehouse = await db.warehouses.find_one({"id": adjustment.warehouse_id})
    if not warehouse:
        raise HTTPException(status_code=404, detail="Warehouse not found")
    
    # Generate adjustment number
    adj_serial = await generate_serial_number("stock_adjustment", adjustment.warehouse_id, current_user)
    
    adjustment_dict = adjustment.model_dump()
    adjustment_dict["id"] = str(uuid.uuid4())
    adjustment_dict["adjustment_no"] = adj_serial.get("serial_number", f"ADJ-{datetime.now().strftime('%Y%m%d%H%M%S')}")
    adjustment_dict["adjustment_date"] = datetime.now(timezone.utc).isoformat()
    adjustment_dict["warehouse_name"] = warehouse.get("warehouse_name")
    adjustment_dict["status"] = "draft"
    adjustment_dict["created_at"] = datetime.now(timezone.utc).isoformat()
    adjustment_dict["created_by"] = current_user["id"]
    
    await db.stock_adjustments.insert_one(adjustment_dict)
    
    return {"message": "Adjustment created", "adjustment_no": adjustment_dict["adjustment_no"], "id": adjustment_dict["id"]}


@router.put("/stock-adjustments/{adjustment_id}/approve")
async def approve_stock_adjustment(adjustment_id: str, current_user: dict = Depends(get_current_user)):
    """Approve and apply stock adjustment"""
    if current_user.get('role') not in ['admin', 'director', 'manager']:
        raise HTTPException(status_code=403, detail="Only admin/director/manager can approve adjustments")
    
    adjustment = await db.stock_adjustments.find_one({"id": adjustment_id})
    if not adjustment:
        raise HTTPException(status_code=404, detail="Adjustment not found")
    
    if adjustment.get("status") != "draft":
        raise HTTPException(status_code=400, detail="Adjustment already processed")
    
    # Apply adjustments
    for item in adjustment.get("items", []):
        item_id = item.get("item_id")
        batch_no = item.get("batch_no")
        adjusted_qty = item.get("adjusted_qty", 0)
        
        # Find or create stock entry
        stock = await db.stock_entries.find_one({
            "item_id": item_id,
            "warehouse_id": adjustment["warehouse_id"],
            "batch_no": batch_no
        })
        
        if stock:
            await db.stock_entries.update_one(
                {"id": stock["id"]},
                {"$set": {"quantity": adjusted_qty, "adjusted_at": datetime.now(timezone.utc).isoformat()}}
            )
        else:
            # Create new stock entry for opening stock
            stock_entry = {
                "id": str(uuid.uuid4()),
                "item_id": item_id,
                "warehouse_id": adjustment["warehouse_id"],
                "batch_no": batch_no,
                "quantity": adjusted_qty,
                "uom": item.get("uom", "PCS"),
                "adjustment_id": adjustment_id,
                "created_at": datetime.now(timezone.utc).isoformat()
            }
            await db.stock_entries.insert_one(stock_entry)
    
    await db.stock_adjustments.update_one(
        {"id": adjustment_id},
        {"$set": {"status": "approved", "approved_at": datetime.now(timezone.utc).isoformat(), "approved_by": current_user["id"]}}
    )
    
    return {"message": "Adjustment approved and applied", "status": "approved"}


@router.get("/stock-adjustments")
async def get_stock_adjustments(
    warehouse_id: Optional[str] = None,
    adjustment_type: Optional[str] = None,
    status: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Get stock adjustments"""
    query = {}
    if warehouse_id:
        query["warehouse_id"] = warehouse_id
    if adjustment_type:
        query["adjustment_type"] = adjustment_type
    if status:
        query["status"] = status
    
    adjustments = await db.stock_adjustments.find(query, {"_id": 0}).sort("created_at", -1).to_list(200)
    return adjustments


# ==================== STOCK REGISTER & REPORTS ====================

@router.get("/stock-register")
async def get_stock_register(
    warehouse_id: Optional[str] = None,
    item_id: Optional[str] = None,
    category: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Get consolidated stock register"""
    match_stage = {}
    if warehouse_id:
        match_stage["warehouse_id"] = warehouse_id
    if item_id:
        match_stage["item_id"] = item_id
    
    pipeline = [
        {"$match": match_stage} if match_stage else {"$match": {}},
        {"$group": {
            "_id": {"item_id": "$item_id", "warehouse_id": "$warehouse_id"},
            "item_code": {"$first": "$item_code"},
            "item_name": {"$first": "$item_name"},
            "total_quantity": {"$sum": "$quantity"},
            "total_value": {"$sum": {"$multiply": ["$quantity", {"$ifNull": ["$cost_price", 0]}]}},
            "batch_count": {"$sum": 1},
            "batches": {"$push": {"batch_no": "$batch_no", "quantity": "$quantity", "expiry_date": "$expiry_date"}}
        }},
        {"$sort": {"item_code": 1}}
    ]
    
    stock = await db.stock_entries.aggregate(pipeline).to_list(1000)
    
    # Add warehouse names
    warehouses = {w["id"]: w["warehouse_name"] for w in await db.warehouses.find({}, {"_id": 0, "id": 1, "warehouse_name": 1}).to_list(100)}
    for entry in stock:
        entry["warehouse_name"] = warehouses.get(entry["_id"]["warehouse_id"], "Unknown")
    
    return stock


@router.get("/item-ledger/{item_id}")
async def get_item_ledger(
    item_id: str,
    warehouse_id: Optional[str] = None,
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Get item-wise ledger showing all movements"""
    # Get item details
    item = await db.items.find_one({"id": item_id}, {"_id": 0})
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    
    # Get all stock movements
    movements = []
    
    # Stock adjustments
    adj_query = {"items.item_id": item_id, "status": "approved"}
    if warehouse_id:
        adj_query["warehouse_id"] = warehouse_id
    
    adjustments = await db.stock_adjustments.find(adj_query, {"_id": 0}).to_list(500)
    for adj in adjustments:
        for item_adj in adj.get("items", []):
            if item_adj.get("item_id") == item_id:
                movements.append({
                    "date": adj.get("adjustment_date"),
                    "type": "Adjustment",
                    "sub_type": adj.get("adjustment_type"),
                    "doc_no": adj.get("adjustment_no"),
                    "warehouse": adj.get("warehouse_name"),
                    "in_qty": item_adj.get("adjusted_qty", 0) if adj.get("adjustment_type") in ["opening", "increase"] else 0,
                    "out_qty": item_adj.get("adjusted_qty", 0) if adj.get("adjustment_type") in ["decrease", "damage", "expired"] else 0,
                    "batch_no": item_adj.get("batch_no")
                })
    
    # Stock transfers
    transfer_query = {"items.item_id": item_id, "status": "received"}
    transfers = await db.stock_transfers.find(transfer_query, {"_id": 0}).to_list(500)
    for tr in transfers:
        for item_tr in tr.get("items", []):
            if item_tr.get("item_id") == item_id:
                movements.append({
                    "date": tr.get("transfer_date"),
                    "type": "Transfer Out",
                    "doc_no": tr.get("transfer_no"),
                    "warehouse": tr.get("from_warehouse_name"),
                    "in_qty": 0,
                    "out_qty": item_tr.get("quantity", 0),
                    "batch_no": item_tr.get("batch_no")
                })
                movements.append({
                    "date": tr.get("received_at"),
                    "type": "Transfer In",
                    "doc_no": tr.get("transfer_no"),
                    "warehouse": tr.get("to_warehouse_name"),
                    "in_qty": item_tr.get("quantity", 0),
                    "out_qty": 0,
                    "batch_no": item_tr.get("batch_no")
                })
    
    # Sort by date
    movements.sort(key=lambda x: x.get("date", ""), reverse=True)
    
    return {
        "item": item,
        "movements": movements,
        "summary": {
            "total_in": sum(m.get("in_qty", 0) for m in movements),
            "total_out": sum(m.get("out_qty", 0) for m in movements)
        }
    }


# ==================== CONSOLIDATED VIEW ====================

@router.get("/consolidated-stock")
async def get_consolidated_stock(current_user: dict = Depends(get_current_user)):
    """Get consolidated stock across all warehouses"""
    pipeline = [
        {"$group": {
            "_id": "$item_id",
            "item_code": {"$first": "$item_code"},
            "item_name": {"$first": "$item_name"},
            "total_quantity": {"$sum": "$quantity"},
            "total_value": {"$sum": {"$multiply": ["$quantity", {"$ifNull": ["$cost_price", 0]}]}},
            "warehouse_stock": {"$push": {
                "warehouse_id": "$warehouse_id",
                "quantity": "$quantity"
            }}
        }},
        {"$sort": {"item_code": 1}}
    ]
    
    stock = await db.stock_entries.aggregate(pipeline).to_list(1000)
    
    # Add warehouse names
    warehouses = {w["id"]: w for w in await db.warehouses.find({}, {"_id": 0}).to_list(100)}
    for entry in stock:
        for wh_stock in entry.get("warehouse_stock", []):
            wh = warehouses.get(wh_stock["warehouse_id"], {})
            wh_stock["warehouse_name"] = wh.get("warehouse_name", "Unknown")
            wh_stock["warehouse_code"] = wh.get("warehouse_code", "")
    
    # Calculate totals
    totals = {
        "total_items": len(stock),
        "total_quantity": sum(s.get("total_quantity", 0) for s in stock),
        "total_value": sum(s.get("total_value", 0) for s in stock)
    }
    
    return {"stock": stock, "totals": totals, "warehouses": list(warehouses.values())}
