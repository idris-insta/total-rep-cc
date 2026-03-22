from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
import uuid
from server import db, get_current_user
from utils.uom_converter import convert_all_uom, calculate_sqm

router = APIRouter()

# ==================== ITEM MODELS ====================
class ItemCreate(BaseModel):
    item_code: str
    item_name: str
    category: str
    item_type: str = "Finished Goods"
    hsn_code: Optional[str] = None
    uom: str = "Rolls"
    secondary_uom: Optional[str] = None
    conversion_factor: float = 1
    thickness: Optional[float] = None  # Microns
    width: Optional[float] = None  # MM
    length: Optional[float] = None  # Meters
    color: Optional[str] = None
    adhesive_type: Optional[str] = None
    base_material: Optional[str] = None
    grade: Optional[str] = None
    # Dimensional Physics Engine fields
    gsm: Optional[float] = None  # Grams per Square Meter
    density: Optional[float] = None  # g/cm3 for thickness-based calc
    standard_cost: float = 0
    selling_price: float = 0
    min_sale_price: float = 0  # MSP - updated by Import Bridge
    last_landed_rate: float = 0  # From Import Bridge
    min_order_qty: float = 1
    reorder_level: float = 0
    safety_stock: float = 0
    lead_time_days: int = 7
    shelf_life_days: Optional[int] = None
    storage_conditions: Optional[str] = None
    is_active: bool = True

class ItemUpdate(BaseModel):
    item_name: Optional[str] = None
    category: Optional[str] = None
    item_type: Optional[str] = None
    hsn_code: Optional[str] = None
    uom: Optional[str] = None
    secondary_uom: Optional[str] = None
    conversion_factor: Optional[float] = None
    thickness: Optional[float] = None
    width: Optional[float] = None
    length: Optional[float] = None
    color: Optional[str] = None
    adhesive_type: Optional[str] = None
    base_material: Optional[str] = None
    grade: Optional[str] = None
    gsm: Optional[float] = None
    density: Optional[float] = None
    standard_cost: Optional[float] = None
    selling_price: Optional[float] = None
    min_sale_price: Optional[float] = None
    last_landed_rate: Optional[float] = None
    min_order_qty: Optional[float] = None
    reorder_level: Optional[float] = None
    safety_stock: Optional[float] = None
    lead_time_days: Optional[int] = None
    shelf_life_days: Optional[int] = None
    storage_conditions: Optional[str] = None
    is_active: Optional[bool] = None

class Item(BaseModel):
    id: str
    item_code: Optional[str] = None
    item_name: Optional[str] = None
    category: Optional[str] = None
    item_type: Optional[str] = None
    sub_category: Optional[str] = None
    hsn_code: Optional[str] = None
    description: Optional[str] = None
    uom: Optional[str] = "Nos"
    primary_uom: Optional[str] = "Pcs"
    secondary_uom: Optional[str] = None
    alternate_uom: Optional[str] = None
    conversion_factor: Optional[float] = 1
    thickness: Optional[float] = None
    thickness_microns: Optional[float] = None
    width: Optional[float] = None
    width_mm: Optional[float] = None
    length: Optional[float] = None
    length_m: Optional[float] = None
    color: Optional[str] = None
    adhesive_type: Optional[str] = None
    base_material: Optional[str] = None
    grade: Optional[str] = None
    gsm: Optional[float] = None
    core_diameter: Optional[float] = None
    density: Optional[float] = None
    purchase_price: Optional[float] = 0
    cost_price: Optional[float] = None
    standard_cost: Optional[float] = 0
    selling_price: Optional[float] = 0
    min_selling_price: Optional[float] = None
    min_sale_price: Optional[float] = 0
    margin_percent: Optional[float] = None
    mrp: Optional[float] = None
    last_landed_rate: Optional[float] = 0
    min_order_qty: Optional[float] = 1
    min_qty: Optional[float] = 0
    max_qty: Optional[float] = None
    reorder_level: Optional[float] = 0
    reorder_qty: Optional[float] = 0
    safety_stock: Optional[float] = 0
    lead_time_days: Optional[int] = 7
    shelf_life_days: Optional[int] = None
    storage_conditions: Optional[str] = None
    gst_rate: Optional[float] = 18
    cess_rate: Optional[float] = 0
    barcode: Optional[str] = None
    notes: Optional[str] = None
    is_active: Optional[bool] = True
    is_batch_tracked: Optional[bool] = False
    is_serial_tracked: Optional[bool] = False
    current_stock: Optional[float] = 0
    stock_qty: Optional[float] = 0
    stock_kg: Optional[float] = 0
    stock_sqm: Optional[float] = 0
    stock_pcs: Optional[int] = 0
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

# ==================== STOCK MODELS ====================
class StockEntry(BaseModel):
    item_id: str
    warehouse_id: str
    quantity: float
    transaction_type: str  # receipt, issue, adjustment, transfer_in, transfer_out
    reference_type: Optional[str] = None  # PO, SO, Transfer, Production
    reference_id: Optional[str] = None
    batch_no: Optional[str] = None
    expiry_date: Optional[str] = None
    unit_cost: float = 0
    notes: Optional[str] = None

class StockBalance(BaseModel):
    id: str
    item_id: str
    item_code: str
    item_name: str
    warehouse_id: str
    warehouse_name: str
    quantity: float
    reserved_qty: float = 0
    available_qty: float = 0
    uom: str
    avg_cost: float = 0
    total_value: float = 0
    last_receipt_date: Optional[str] = None
    last_issue_date: Optional[str] = None

class StockLedger(BaseModel):
    id: str
    item_id: str
    warehouse_id: str
    transaction_date: str
    transaction_type: str
    reference_type: Optional[str] = None
    reference_id: Optional[str] = None
    in_qty: float = 0
    out_qty: float = 0
    balance_qty: float = 0
    unit_cost: float = 0
    batch_no: Optional[str] = None
    notes: Optional[str] = None
    created_by: str

# ==================== WAREHOUSE MODELS ====================
class WarehouseCreate(BaseModel):
    warehouse_code: str
    warehouse_name: str
    warehouse_type: str = "Main"  # Main, Branch, Transit
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    pincode: Optional[str] = None
    manager_id: Optional[str] = None
    is_active: bool = True

class Warehouse(BaseModel):
    id: str
    warehouse_code: str
    warehouse_name: str
    warehouse_type: str
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    pincode: Optional[str] = None
    manager_id: Optional[str] = None
    is_active: bool = True
    created_at: str

# ==================== TRANSFER MODELS ====================
class TransferItemCreate(BaseModel):
    item_id: str
    quantity: float
    batch_no: Optional[str] = None

class StockTransferCreate(BaseModel):
    from_warehouse: str
    to_warehouse: str
    items: List[TransferItemCreate]
    scheduled_date: Optional[str] = None
    truck_no: Optional[str] = None
    driver_name: Optional[str] = None
    driver_phone: Optional[str] = None
    notes: Optional[str] = None

class StockTransfer(BaseModel):
    id: str
    transfer_number: str
    from_warehouse: str
    from_warehouse_name: Optional[str] = None
    to_warehouse: str
    to_warehouse_name: Optional[str] = None
    items: List[dict]
    status: str  # draft, issued, in_transit, received, cancelled
    scheduled_date: Optional[str] = None
    issued_date: Optional[str] = None
    received_date: Optional[str] = None
    truck_no: Optional[str] = None
    driver_name: Optional[str] = None
    driver_phone: Optional[str] = None
    notes: Optional[str] = None
    created_by: str
    created_at: str
    updated_at: Optional[str] = None

# ==================== ITEM ENDPOINTS ====================
@router.post("/items", response_model=Item)
async def create_item(item_data: ItemCreate, current_user: dict = Depends(get_current_user)):
    item_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    
    # Check duplicate item code
    existing = await db.items.find_one({"item_code": item_data.item_code})
    if existing:
        raise HTTPException(status_code=400, detail="Item code already exists")
    
    item_doc = {
        "id": item_id,
        **item_data.model_dump(),
        "current_stock": 0,
        "stock_kg": 0,
        "stock_sqm": 0,
        "stock_pcs": 0,
        "created_at": now,
        "updated_at": now
    }
    
    await db.items.insert_one(item_doc)
    return Item(**{k: v for k, v in item_doc.items() if k != '_id'})


# ==================== UOM CONVERSION ENDPOINT ====================
@router.get("/items/{item_id}/convert-uom")
async def convert_item_uom(
    item_id: str,
    quantity: float,
    from_uom: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Convert quantity between UOMs for an item using Dimensional Physics Engine
    Supports: KG, SQM, PCS, ROLL, MTR
    """
    item = await db.items.find_one({"id": item_id}, {"_id": 0})
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    
    width_mm = item.get('width', 0)
    length_m = item.get('length', 0)
    gsm = item.get('gsm')
    item_type = item.get('item_type', 'BOPP')
    
    if not width_mm or not length_m:
        raise HTTPException(
            status_code=400, 
            detail="Item dimensions (width, length) required for UOM conversion"
        )
    
    result = convert_all_uom(quantity, from_uom, width_mm, length_m, gsm, item_type)
    
    return {
        'item_code': item['item_code'],
        'item_name': item['item_name'],
        'input': {'quantity': quantity, 'uom': from_uom},
        'converted': result,
        'dimensions': {
            'width_mm': width_mm,
            'length_m': length_m,
            'gsm': gsm or 'default'
        }
    }


@router.get("/items", response_model=List[Item])
async def get_items(
    category: Optional[str] = None,
    item_type: Optional[str] = None,
    is_active: Optional[bool] = None,
    search: Optional[str] = None,
    low_stock: Optional[bool] = None,
    current_user: dict = Depends(get_current_user)
):
    query = {}
    if category:
        query["category"] = category
    if item_type:
        query["item_type"] = item_type
    if is_active is not None:
        query["is_active"] = is_active
    if search:
        query["$or"] = [
            {"item_code": {"$regex": search, "$options": "i"}},
            {"item_name": {"$regex": search, "$options": "i"}}
        ]
    if low_stock:
        query["$expr"] = {"$lte": ["$current_stock", "$reorder_level"]}
    
    items = await db.items.find(query, {"_id": 0}).sort("item_code", 1).to_list(1000)
    return [Item(**item) for item in items]

@router.get("/items/{item_id}", response_model=Item)
async def get_item(item_id: str, current_user: dict = Depends(get_current_user)):
    item = await db.items.find_one({"id": item_id}, {"_id": 0})
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return Item(**item)

@router.put("/items/{item_id}", response_model=Item)
async def update_item(item_id: str, item_data: ItemUpdate, current_user: dict = Depends(get_current_user)):
    update_dict = {k: v for k, v in item_data.model_dump().items() if v is not None}
    update_dict["updated_at"] = datetime.now(timezone.utc).isoformat()
    
    result = await db.items.update_one({"id": item_id}, {"$set": update_dict})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Item not found")
    
    item = await db.items.find_one({"id": item_id}, {"_id": 0})
    return Item(**item)

@router.delete("/items/{item_id}")
async def delete_item(item_id: str, current_user: dict = Depends(get_current_user)):
    # Soft delete
    result = await db.items.update_one(
        {"id": item_id},
        {"$set": {"is_active": False, "updated_at": datetime.now(timezone.utc).isoformat()}}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Item not found")
    return {"message": "Item deactivated"}

# ==================== WAREHOUSE ENDPOINTS ====================
@router.post("/warehouses", response_model=Warehouse)
async def create_warehouse(wh_data: WarehouseCreate, current_user: dict = Depends(get_current_user)):
    wh_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    
    wh_doc = {
        "id": wh_id,
        **wh_data.model_dump(),
        "created_at": now
    }
    
    await db.warehouses.insert_one(wh_doc)
    return Warehouse(**{k: v for k, v in wh_doc.items() if k != '_id'})

@router.get("/warehouses", response_model=List[Warehouse])
async def get_warehouses(is_active: Optional[bool] = None, current_user: dict = Depends(get_current_user)):
    query = {}
    if is_active is not None:
        query["is_active"] = is_active
    
    warehouses = await db.warehouses.find(query, {"_id": 0}).to_list(100)
    return [Warehouse(**wh) for wh in warehouses]

@router.get("/warehouses/{wh_id}", response_model=Warehouse)
async def get_warehouse(wh_id: str, current_user: dict = Depends(get_current_user)):
    wh = await db.warehouses.find_one({"id": wh_id}, {"_id": 0})
    if not wh:
        raise HTTPException(status_code=404, detail="Warehouse not found")
    return Warehouse(**wh)

# ==================== STOCK ENDPOINTS ====================
@router.post("/stock/entry")
async def create_stock_entry(entry: StockEntry, current_user: dict = Depends(get_current_user)):
    """Record a stock transaction"""

    # WORKBOOK APPROVAL: block negative adjustments until approved
    if entry.transaction_type in ["adjustment", "adjustment_out"]:
        base_approval = await db.approval_requests.find_one({
            "module": "Inventory",
            "entity_type": "StockEntry",
            "entity_id": entry.reference_id or "",
            "action": "Stock Adjustment",
            "status": "approved",
        }, {"_id": 0})
        if not base_approval:
            raise HTTPException(status_code=409, detail="Approval required: Stock Adjustment")

    entry_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    
    # Validate item exists
    item = await db.items.find_one({"id": entry.item_id}, {"_id": 0})
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    
    # Get current balance
    balance = await db.stock_balance.find_one({
        "item_id": entry.item_id,
        "warehouse_id": entry.warehouse_id
    })
    
    current_qty = balance.get("quantity", 0) if balance else 0
    
    # Calculate new balance
    if entry.transaction_type in ["receipt", "transfer_in", "adjustment_in"]:
        new_qty = current_qty + entry.quantity
        in_qty = entry.quantity
        out_qty = 0
    else:
        if current_qty < entry.quantity:
            raise HTTPException(status_code=400, detail="Insufficient stock")
        new_qty = current_qty - entry.quantity
        in_qty = 0
        out_qty = entry.quantity
    
    # Create ledger entry
    ledger_doc = {
        "id": entry_id,
        "item_id": entry.item_id,
        "warehouse_id": entry.warehouse_id,
        "transaction_date": now,
        "transaction_type": entry.transaction_type,
        "reference_type": entry.reference_type,
        "reference_id": entry.reference_id,
        "in_qty": in_qty,
        "out_qty": out_qty,
        "balance_qty": new_qty,
        "unit_cost": entry.unit_cost,
        "batch_no": entry.batch_no,
        "notes": entry.notes,
        "created_by": current_user["id"]
    }
    await db.stock_ledger.insert_one(ledger_doc)
    
    # Update or create balance
    if balance:
        await db.stock_balance.update_one(
            {"item_id": entry.item_id, "warehouse_id": entry.warehouse_id},
            {"$set": {"quantity": new_qty, "last_updated": now}}
        )
    else:
        wh = await db.warehouses.find_one({"id": entry.warehouse_id}, {"warehouse_name": 1})
        balance_doc = {
            "id": str(uuid.uuid4()),
            "item_id": entry.item_id,
            "item_code": item.get("item_code"),
            "item_name": item.get("item_name"),
            "warehouse_id": entry.warehouse_id,
            "warehouse_name": wh.get("warehouse_name") if wh else "",
            "quantity": new_qty,
            "reserved_qty": 0,
            "available_qty": new_qty,
            "uom": item.get("uom"),
            "avg_cost": entry.unit_cost,
            "total_value": new_qty * entry.unit_cost,
            "last_updated": now
        }
        await db.stock_balance.insert_one(balance_doc)
    
    # Update item's total stock
    total_stock = await db.stock_balance.aggregate([
        {"$match": {"item_id": entry.item_id}},
        {"$group": {"_id": None, "total": {"$sum": "$quantity"}}}
    ]).to_list(1)
    total = total_stock[0]["total"] if total_stock else 0
    await db.items.update_one({"id": entry.item_id}, {"$set": {"current_stock": total}})
    
    return {"message": "Stock entry recorded", "new_balance": new_qty}

@router.get("/stock/balance")
async def get_stock_balance(
    warehouse_id: Optional[str] = None,
    item_id: Optional[str] = None,
    low_stock: Optional[bool] = None,
    current_user: dict = Depends(get_current_user)
):
    query = {}
    if warehouse_id:
        query["warehouse_id"] = warehouse_id
    if item_id:
        query["item_id"] = item_id
    
    balances = await db.stock_balance.find(query, {"_id": 0}).to_list(1000)
    
    if low_stock:
        # Filter items below reorder level
        result = []
        for bal in balances:
            item = await db.items.find_one({"id": bal["item_id"]}, {"reorder_level": 1})
            if item and bal["quantity"] <= item.get("reorder_level", 0):
                result.append(bal)
        return result
    
    return balances

@router.get("/stock/ledger/{item_id}")
async def get_stock_ledger(
    item_id: str,
    warehouse_id: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    query = {"item_id": item_id}
    if warehouse_id:
        query["warehouse_id"] = warehouse_id
    if date_from:
        query["transaction_date"] = {"$gte": date_from}
    if date_to:
        if "transaction_date" in query:
            query["transaction_date"]["$lte"] = date_to
        else:
            query["transaction_date"] = {"$lte": date_to}
    
    ledger = await db.stock_ledger.find(query, {"_id": 0}).sort("transaction_date", -1).to_list(500)
    return ledger

# ==================== TRANSFER ENDPOINTS ====================
@router.post("/transfers", response_model=StockTransfer)
async def create_transfer(transfer_data: StockTransferCreate, current_user: dict = Depends(get_current_user)):
    transfer_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc)
    transfer_number = f"TRF-{now.strftime('%Y%m%d')}-{str(uuid.uuid4())[:6].upper()}"
    
    # Get warehouse names
    from_wh = await db.warehouses.find_one({"id": transfer_data.from_warehouse}, {"warehouse_name": 1})
    to_wh = await db.warehouses.find_one({"id": transfer_data.to_warehouse}, {"warehouse_name": 1})
    
    # Enrich items with names
    items_with_details = []
    for item in transfer_data.items:
        item_doc = await db.items.find_one({"id": item.item_id}, {"item_code": 1, "item_name": 1, "uom": 1})
        if item_doc:
            items_with_details.append({
                "item_id": item.item_id,
                "item_code": item_doc.get("item_code"),
                "item_name": item_doc.get("item_name"),
                "quantity": item.quantity,
                "uom": item_doc.get("uom"),
                "batch_no": item.batch_no,
                "received_qty": 0
            })
    
    transfer_doc = {
        "id": transfer_id,
        "transfer_number": transfer_number,
        "from_warehouse": transfer_data.from_warehouse,
        "from_warehouse_name": from_wh.get("warehouse_name") if from_wh else "",
        "to_warehouse": transfer_data.to_warehouse,
        "to_warehouse_name": to_wh.get("warehouse_name") if to_wh else "",
        "items": items_with_details,
        "status": "draft",
        "scheduled_date": transfer_data.scheduled_date,
        "truck_no": transfer_data.truck_no,
        "driver_name": transfer_data.driver_name,
        "driver_phone": transfer_data.driver_phone,
        "notes": transfer_data.notes,
        "created_by": current_user["id"],
        "created_at": now.isoformat(),
        "updated_at": now.isoformat()
    }
    
    await db.stock_transfers.insert_one(transfer_doc)

    # Auto-create approval request (admin for phase-1)
    await db.approval_requests.insert_one({
        "id": str(uuid.uuid4()),
        "module": "Inventory",
        "entity_type": "StockTransfer",
        "entity_id": transfer_id,
        "action": "Stock Transfer",
        "condition": "Inter-warehouse",
        "status": "pending",
        "approver_role": "admin",
        "requested_by": current_user["id"],
        "requested_at": datetime.now(timezone.utc).isoformat(),
        "decided_by": None,
        "decided_at": None,
        "payload": {"transfer_number": transfer_number},
        "notes": "Workbook rule: Inter-warehouse transfer requires approval"
    })

    return StockTransfer(**{k: v for k, v in transfer_doc.items() if k != '_id'})

@router.get("/transfers", response_model=List[StockTransfer])
async def get_transfers(
    status: Optional[str] = None,
    from_warehouse: Optional[str] = None,
    to_warehouse: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    query = {}
    if status:
        query["status"] = status
    if from_warehouse:
        query["from_warehouse"] = from_warehouse
    if to_warehouse:
        query["to_warehouse"] = to_warehouse
    
    transfers = await db.stock_transfers.find(query, {"_id": 0}).sort("created_at", -1).to_list(500)
    return [StockTransfer(**t) for t in transfers]

@router.put("/transfers/{transfer_id}/issue")
async def issue_transfer(transfer_id: str, current_user: dict = Depends(get_current_user)):
    """Issue transfer - deduct from source warehouse"""

    # WORKBOOK APPROVAL: Inter-warehouse transfer requires approval before issue
    approval = await db.approval_requests.find_one({
        "module": "Inventory",
        "entity_type": "StockTransfer",
        "entity_id": transfer_id,
        "action": "Stock Transfer",
        "status": "approved",
    }, {"_id": 0})
    if not approval:
        raise HTTPException(status_code=409, detail="Approval required: Stock Transfer")

    transfer = await db.stock_transfers.find_one({"id": transfer_id}, {"_id": 0})
    if not transfer:
        raise HTTPException(status_code=404, detail="Transfer not found")
    
    if transfer["status"] != "draft":
        raise HTTPException(status_code=400, detail="Transfer already issued")
    
    now = datetime.now(timezone.utc).isoformat()
    
    # Deduct stock from source warehouse
    for item in transfer["items"]:
        entry = StockEntry(
            item_id=item["item_id"],
            warehouse_id=transfer["from_warehouse"],
            quantity=item["quantity"],
            transaction_type="transfer_out",
            reference_type="Transfer",
            reference_id=transfer_id,
            batch_no=item.get("batch_no")
        )
        await create_stock_entry(entry, current_user)
    
    await db.stock_transfers.update_one(
        {"id": transfer_id},
        {"$set": {"status": "in_transit", "issued_date": now, "updated_at": now}}
    )
    
    return {"message": "Transfer issued"}

@router.put("/transfers/{transfer_id}/receive")
async def receive_transfer(transfer_id: str, received_items: List[dict], current_user: dict = Depends(get_current_user)):
    """Receive transfer - add to destination warehouse"""
    transfer = await db.stock_transfers.find_one({"id": transfer_id}, {"_id": 0})
    if not transfer:
        raise HTTPException(status_code=404, detail="Transfer not found")
    
    if transfer["status"] != "in_transit":
        raise HTTPException(status_code=400, detail="Transfer not in transit")
    
    now = datetime.now(timezone.utc).isoformat()
    
    # Add stock to destination warehouse
    for recv_item in received_items:
        entry = StockEntry(
            item_id=recv_item["item_id"],
            warehouse_id=transfer["to_warehouse"],
            quantity=recv_item["received_qty"],
            transaction_type="transfer_in",
            reference_type="Transfer",
            reference_id=transfer_id,
            batch_no=recv_item.get("batch_no")
        )
        await create_stock_entry(entry, current_user)
    
    await db.stock_transfers.update_one(
        {"id": transfer_id},
        {"$set": {"status": "received", "received_date": now, "updated_at": now}}
    )
    
    return {"message": "Transfer received"}

# ==================== STATS ====================
@router.get("/stats/overview")
async def get_inventory_stats(current_user: dict = Depends(get_current_user)):
    total_items = await db.items.count_documents({"is_active": True})
    total_warehouses = await db.warehouses.count_documents({"is_active": True})
    
    # Low stock items
    low_stock_pipeline = [
        {"$match": {"is_active": True}},
        {"$match": {"$expr": {"$lte": ["$current_stock", "$reorder_level"]}}},
        {"$count": "count"}
    ]
    low_stock_result = await db.items.aggregate(low_stock_pipeline).to_list(1)
    low_stock_count = low_stock_result[0]["count"] if low_stock_result else 0
    
    # Pending transfers
    pending_transfers = await db.stock_transfers.count_documents({"status": {"$in": ["draft", "in_transit"]}})
    
    # Stock value
    value_pipeline = [
        {"$group": {"_id": None, "total": {"$sum": "$total_value"}}}
    ]
    value_result = await db.stock_balance.aggregate(value_pipeline).to_list(1)
    total_value = value_result[0]["total"] if value_result else 0
    
    # Stock by category
    category_pipeline = [
        {"$match": {"is_active": True}},
        {"$group": {"_id": "$category", "count": {"$sum": 1}, "stock": {"$sum": "$current_stock"}}}
    ]
    category_result = await db.items.aggregate(category_pipeline).to_list(100)
    by_category = {r["_id"]: {"count": r["count"], "stock": r["stock"]} for r in category_result if r["_id"]}
    
    return {
        "total_items": total_items,
        "total_warehouses": total_warehouses,
        "low_stock_items": low_stock_count,
        "pending_transfers": pending_transfers,
        "total_stock_value": round(total_value, 2),
        "by_category": by_category
    }
