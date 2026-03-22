from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, timezone
import uuid
from server import db, get_current_user

router = APIRouter()

class WorkOrderCreate(BaseModel):
    sales_order_id: Optional[str] = None
    item_id: str
    quantity_to_make: float
    machine_id: str
    thickness: Optional[float] = None
    color: Optional[str] = None
    width: Optional[float] = None
    length: Optional[float] = None
    brand: Optional[str] = None
    priority: str = "normal"

class WorkOrder(BaseModel):
    id: str
    wo_number: str
    sales_order_id: Optional[str] = None
    item_id: str
    quantity_to_make: float
    quantity_made: float
    machine_id: str
    thickness: Optional[float] = None
    color: Optional[str] = None
    width: Optional[float] = None
    length: Optional[float] = None
    brand: Optional[str] = None
    priority: str
    status: str
    created_at: str
    started_at: Optional[str] = None
    completed_at: Optional[str] = None

class ProductionEntry(BaseModel):
    wo_id: str
    quantity_produced: float
    wastage: float
    start_time: str
    end_time: str
    operator: str
    notes: Optional[str] = None

class Machine(BaseModel):
    id: str
    machine_code: str
    machine_name: str
    machine_type: str
    capacity_per_hour: Optional[float] = None
    location: Optional[str] = None
    status: str = "active"


@router.post("/work-orders", response_model=WorkOrder)
async def create_work_order(wo_data: WorkOrderCreate, current_user: dict = Depends(get_current_user)):
    wo_id = str(uuid.uuid4())
    wo_number = f"WO-{datetime.now(timezone.utc).strftime('%Y%m%d')}-{str(uuid.uuid4())[:6].upper()}"
    
    wo_doc = {
        'id': wo_id,
        'wo_number': wo_number,
        **wo_data.model_dump(),
        'quantity_made': 0,
        'status': 'planned',
        'created_at': datetime.now(timezone.utc).isoformat(),
        'created_by': current_user['id']
    }
    
    await db.work_orders.insert_one(wo_doc)
    return WorkOrder(**{k: v for k, v in wo_doc.items() if k != '_id'})

@router.get("/work-orders", response_model=List[WorkOrder])
async def get_work_orders(status: Optional[str] = None, machine_id: Optional[str] = None, current_user: dict = Depends(get_current_user)):
    query = {}
    if status:
        query['status'] = status
    if machine_id:
        query['machine_id'] = machine_id
    
    work_orders = await db.work_orders.find(query, {'_id': 0}).sort('created_at', -1).to_list(1000)
    return [WorkOrder(**wo) for wo in work_orders]

@router.get("/work-orders/{wo_id}", response_model=WorkOrder)
async def get_work_order(wo_id: str, current_user: dict = Depends(get_current_user)):
    wo = await db.work_orders.find_one({'id': wo_id}, {'_id': 0})
    if not wo:
        raise HTTPException(status_code=404, detail="Work order not found")
    return WorkOrder(**wo)

@router.put("/work-orders/{wo_id}/start")
async def start_work_order(wo_id: str, current_user: dict = Depends(get_current_user)):
    result = await db.work_orders.update_one(
        {'id': wo_id},
        {'$set': {'status': 'in_progress', 'started_at': datetime.now(timezone.utc).isoformat()}}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Work order not found")
    
    return {'message': 'Work order started'}


@router.put("/work-orders/{wo_id}/cancel")
async def cancel_work_order(wo_id: str, current_user: dict = Depends(get_current_user)):
    # WORKBOOK APPROVAL: Cancel Production Order requires approval (admin for phase-1)
    approval = await db.approval_requests.find_one({
        "module": "Production",
        "entity_type": "WorkOrder",
        "entity_id": wo_id,
        "action": "Cancel Production Order",
        "status": "approved",
    }, {"_id": 0})
    if not approval:
        await db.approval_requests.insert_one({
            "id": str(uuid.uuid4()),
            "module": "Production",
            "entity_type": "WorkOrder",
            "entity_id": wo_id,
            "action": "Cancel Production Order",
            "condition": "Any",
            "status": "pending",
            "approver_role": "admin",
            "requested_by": current_user["id"],
            "requested_at": datetime.now(timezone.utc).isoformat(),
            "decided_by": None,
            "decided_at": None,
            "payload": {"wo_id": wo_id},
            "notes": "Workbook rule: cancel production order requires approval"
        })
        raise HTTPException(status_code=409, detail="Approval required: Cancel Production Order")

    wo = await db.work_orders.find_one({'id': wo_id}, {'_id': 0})
    if not wo:
        raise HTTPException(status_code=404, detail="Work order not found")

    await db.work_orders.update_one({'id': wo_id}, {'$set': {'status': 'cancelled', 'updated_at': datetime.now(timezone.utc).isoformat()}})
    return {'message': 'Work order cancelled'}

@router.post("/production-entries")
async def create_production_entry(entry_data: ProductionEntry, current_user: dict = Depends(get_current_user)):
    wo = await db.work_orders.find_one({'id': entry_data.wo_id}, {'_id': 0})
    if not wo:
        raise HTTPException(status_code=404, detail="Work order not found")

    # WORKBOOK APPROVAL: scrap / wastage > 7% requires approval (admin for phase-1)
    if entry_data.quantity_produced and entry_data.quantity_produced > 0:
        scrap_pct = (entry_data.wastage / entry_data.quantity_produced) * 100 if entry_data.wastage else 0
        if scrap_pct > 7:
            approval = await db.approval_requests.find_one({
                "module": "Production",
                "entity_type": "ProductionEntry",
                "entity_id": entry_data.wo_id,
                "action": "Production Scrap",
                "status": "approved",
            }, {"_id": 0})
            if not approval:
                await db.approval_requests.insert_one({
                    "id": str(uuid.uuid4()),
                    "module": "Production",
                    "entity_type": "ProductionEntry",
                    "entity_id": entry_data.wo_id,
                    "action": "Production Scrap",
                    "condition": ">7%",
                    "status": "pending",
                    "approver_role": "admin",
                    "requested_by": current_user["id"],
                    "requested_at": datetime.now(timezone.utc).isoformat(),
                    "decided_by": None,
                    "decided_at": None,
                    "payload": entry_data.model_dump(),
                    "notes": f"Workbook rule: scrap {scrap_pct:.2f}% > 7% requires approval"
                })
                raise HTTPException(status_code=409, detail="Approval required: Production Scrap > 7%")

    
    entry_id = str(uuid.uuid4())
    batch_number = f"{wo['item_id']}-{datetime.now(timezone.utc).strftime('%Y%m%d')}-{wo['machine_id']}-{wo['wo_number']}"
    
    entry_doc = {
        'id': entry_id,
        'batch_number': batch_number,
        **entry_data.model_dump(),
        'created_at': datetime.now(timezone.utc).isoformat(),
        'created_by': current_user['id']
    }
    
    await db.production_entries.insert_one(entry_doc)
    
    new_quantity_made = wo['quantity_made'] + entry_data.quantity_produced
    status = 'completed' if new_quantity_made >= wo['quantity_to_make'] else 'in_progress'
    
    update_data = {
        'quantity_made': new_quantity_made,
        'status': status
    }
    if status == 'completed':
        update_data['completed_at'] = datetime.now(timezone.utc).isoformat()
    
    await db.work_orders.update_one({'id': entry_data.wo_id}, {'$set': update_data})
    
    # Record stock movement into Inventory stock ledger/balance (uses Inventory module collections)
    machine = await db.machines.find_one({'id': wo['machine_id']}, {'_id': 0})
    warehouses = await db.warehouses.find({}, {'_id': 0}).to_list(1000)
    default_wh = next((w for w in warehouses if w.get('warehouse_type') == 'Main'), warehouses[0] if warehouses else None)

    # Update stock_balance and item current_stock similarly to Inventory /stock/entry logic
    balance = await db.stock_balance.find_one({'item_id': wo['item_id'], 'warehouse_id': (default_wh or {}).get('id', '')}, {'_id': 0})
    current_qty = balance.get('quantity', 0) if balance else 0
    new_qty = current_qty + entry_data.quantity_produced

    await db.stock_ledger.insert_one({
        'id': str(uuid.uuid4()),
        'item_id': wo['item_id'],
        'warehouse_id': (default_wh or {}).get('id', ''),
        'transaction_date': datetime.now(timezone.utc).isoformat(),
        'transaction_type': 'production_in',
        'reference_type': 'WorkOrder',
        'reference_id': wo['id'],
        'in_qty': entry_data.quantity_produced,
        'out_qty': 0,
        'balance_qty': new_qty,
        'unit_cost': 0,
        'batch_no': batch_number,
        'notes': f"Machine: {(machine or {}).get('machine_code', wo['machine_id'])}",
        'created_by': current_user['id']
    })

    if balance:
        await db.stock_balance.update_one(
            {'item_id': wo['item_id'], 'warehouse_id': (default_wh or {}).get('id', '')},
            {'$set': {'quantity': new_qty, 'available_qty': new_qty, 'last_updated': datetime.now(timezone.utc).isoformat()}}
        )
    else:
        item_doc = await db.items.find_one({'id': wo['item_id']}, {'_id': 0})
        await db.stock_balance.insert_one({
            'id': str(uuid.uuid4()),
            'item_id': wo['item_id'],
            'item_code': (item_doc or {}).get('item_code'),
            'item_name': (item_doc or {}).get('item_name'),
            'warehouse_id': (default_wh or {}).get('id', ''),
            'warehouse_name': (default_wh or {}).get('warehouse_name', ''),
            'quantity': new_qty,
            'reserved_qty': 0,
            'available_qty': new_qty,
            'uom': (item_doc or {}).get('uom', 'Rolls'),
            'avg_cost': 0,
            'total_value': 0,
            'last_updated': datetime.now(timezone.utc).isoformat()
        })

    total_stock = await db.stock_balance.aggregate([
        {'$match': {'item_id': wo['item_id']}},
        {'$group': {'_id': None, 'total': {'$sum': '$quantity'}}}
    ]).to_list(1)
    total = total_stock[0]['total'] if total_stock else 0
    await db.items.update_one({'id': wo['item_id']}, {'$set': {'current_stock': total}})
    
    return {'message': 'Production entry created', 'entry_id': entry_id, 'batch_number': batch_number}

@router.get("/production-entries")
async def get_production_entries(wo_id: Optional[str] = None, current_user: dict = Depends(get_current_user)):
    query = {}
    if wo_id:
        query['wo_id'] = wo_id
    
    entries = await db.production_entries.find(query, {'_id': 0}).sort('created_at', -1).to_list(1000)
    return entries


@router.get("/machines", response_model=List[Machine])
async def get_machines(machine_type: Optional[str] = None, current_user: dict = Depends(get_current_user)):
    query = {}
    if machine_type:
        query['machine_type'] = machine_type
    
    machines = await db.machines.find(query, {'_id': 0}).to_list(1000)
    return [Machine(**machine) for machine in machines]

@router.post("/machines", response_model=Machine)
async def create_machine(machine_data: dict, current_user: dict = Depends(get_current_user)):
    machine_id = str(uuid.uuid4())
    machine_doc = {
        'id': machine_id,
        **machine_data,
        'status': 'active'
    }
    
    await db.machines.insert_one(machine_doc)
    return Machine(**{k: v for k, v in machine_doc.items() if k != '_id'})

@router.get("/analytics/wastage")
async def get_wastage_analytics(current_user: dict = Depends(get_current_user)):
    pipeline = [
        {
            '$group': {
                '_id': '$wo_id',
                'total_produced': {'$sum': '$quantity_produced'},
                'total_wastage': {'$sum': '$wastage'}
            }
        },
        {
            '$project': {
                '_id': 0,
                'wo_id': '$_id',
                'total_produced': 1,
                'total_wastage': 1,
                'wastage_percentage': {
                    '$multiply': [
                        {'$divide': ['$total_wastage', {'$add': ['$total_produced', '$total_wastage']}]},
                        100
                    ]
                }
            }
        }
    ]
    
    analytics = await db.production_entries.aggregate(pipeline).to_list(1000)
    return analytics