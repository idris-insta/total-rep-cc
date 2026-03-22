"""
Production Stages Module - Comprehensive Work Order Management
7 Production Stages:
1. Coating - Base material + Adhesive + Release paper → Jumbo Roll
2. Slitting - Jumbo roll → Cut rolls
3. Rewinding - Jumbo roll → Log rolls  
4. Cutting - Log rolls → Cut width rolls
5. Packing - Cut rolls → Packed products (with QC video upload)
6. Ready to Deliver - Dispatch preparation
7. Delivered - Final status (stock auto-deduct after invoice)

Features:
- Machine Master with configurable wastage norms
- Auto-suggest machine assignment based on history
- Stock hold/deduct integration with Inventory
- Order Sheet views: Order-wise, Product-wise, Machine-wise
"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
import uuid
from server import db, get_current_user

router = APIRouter()

# ==================== PYDANTIC MODELS ====================

class MachineCreate(BaseModel):
    machine_code: str
    machine_name: str
    machine_type: str  # coating, slitting, rewinding, cutting, packing, quality_control, despatch
    capacity: float
    capacity_uom: str = "pcs/hour"
    location: str  # BWD, SGM
    wastage_norm_percent: float = 2.0  # Configurable per machine
    notes: Optional[str] = None

class MachineUpdate(BaseModel):
    machine_name: Optional[str] = None
    capacity: Optional[float] = None
    capacity_uom: Optional[str] = None
    location: Optional[str] = None
    wastage_norm_percent: Optional[float] = None
    status: Optional[str] = None
    notes: Optional[str] = None

class WorkOrderStageCreate(BaseModel):
    sales_order_id: str
    stage: str  # coating, slitting, rewinding, cutting, packing, ready_to_deliver, delivered
    item_id: str
    item_name: str
    item_code: Optional[str] = None
    machine_id: Optional[str] = None
    priority: str = "normal"  # urgent, high, normal, low
    # Common fields
    color: Optional[str] = None
    thickness: Optional[float] = None
    width: Optional[float] = None
    length: Optional[float] = None
    brand: Optional[str] = None
    # Coating specific
    base_material_id: Optional[str] = None
    adhesive_type: Optional[str] = None
    liner_color: Optional[str] = None
    gsm: Optional[float] = None
    density: Optional[float] = None
    sqm_per_roll: Optional[float] = None
    sqm_in_production: Optional[float] = None
    sqm_estimated_target: Optional[float] = None
    # Slitting/Cutting specific
    qty_per_ctn: Optional[int] = None
    total_ctn: Optional[int] = None
    core_brand: Optional[str] = None
    packing_brand: Optional[str] = None
    # Rewinding specific
    no_of_rolls: Optional[int] = None
    core_id: Optional[str] = None
    logs_per_roll: Optional[int] = None
    # Packing specific
    packing_type: Optional[str] = None
    # Target quantities
    target_qty: float
    target_uom: str = "pcs"
    notes: Optional[str] = None

class StageEntryCreate(BaseModel):
    work_order_stage_id: str
    operator_id: str
    start_time: str
    end_time: str
    # Input quantities
    input_qty: float
    input_uom: str
    # Output quantities
    output_qty: float
    output_uom: str
    # Wastage
    wastage_qty: float
    wastage_reason: Optional[str] = None
    # For packing stage - QC video
    qc_video_url: Optional[str] = None
    notes: Optional[str] = None
    
    # ===== Stage-Specific Fields =====
    # Coating Stage
    jumbo_roll_width: Optional[float] = None  # mm
    jumbo_roll_length: Optional[float] = None  # meters
    jumbo_roll_weight: Optional[float] = None  # kg
    sqm_produced: Optional[float] = None
    adhesive_consumption: Optional[float] = None  # kg
    base_film_consumption: Optional[float] = None  # kg
    liner_consumption: Optional[float] = None  # kg
    coating_speed: Optional[float] = None  # m/min
    drying_temp: Optional[float] = None  # celsius
    
    # Slitting Stage
    no_of_slits: Optional[int] = None
    slit_widths: Optional[List[float]] = None  # list of slit widths in mm
    parent_roll_id: Optional[str] = None
    edge_trim_width: Optional[float] = None  # mm
    sqm_input: Optional[float] = None
    sqm_output: Optional[float] = None
    
    # Rewinding Stage  
    no_of_logs: Optional[int] = None
    log_length: Optional[float] = None  # meters
    core_size: Optional[str] = None  # 1", 1.5", 2", 3"
    tension_setting: Optional[float] = None
    
    # Cutting Stage
    cut_length: Optional[float] = None  # meters
    pieces_per_log: Optional[int] = None
    total_pieces: Optional[int] = None
    
    # Packing Stage
    packing_type: Optional[str] = None  # shrink, carton, pallet
    pieces_per_carton: Optional[int] = None
    cartons_packed: Optional[int] = None
    gross_weight: Optional[float] = None  # kg
    net_weight: Optional[float] = None  # kg
    qc_status: Optional[str] = None  # pass, fail, conditional

class OrderSheetCreate(BaseModel):
    sales_order_id: str
    customer_id: str
    customer_name: str
    order_date: str
    delivery_date: Optional[str] = None
    priority: str = "normal"
    items: List[Dict[str, Any]]  # List of items with product details
    notes: Optional[str] = None


# ==================== MACHINE MASTER ENDPOINTS ====================

@router.get("/machines")
async def get_machines(
    machine_type: Optional[str] = None,
    location: Optional[str] = None,
    status: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Get all machines with optional filters"""
    query = {}
    if machine_type:
        query['machine_type'] = machine_type
    if location:
        query['location'] = location
    if status:
        query['status'] = status
    
    machines = await db.production_machines.find(query, {'_id': 0}).sort('machine_code', 1).to_list(500)
    return machines

@router.get("/machines/{machine_id}")
async def get_machine(machine_id: str, current_user: dict = Depends(get_current_user)):
    """Get single machine details"""
    machine = await db.production_machines.find_one({'id': machine_id}, {'_id': 0})
    if not machine:
        raise HTTPException(status_code=404, detail="Machine not found")
    return machine

@router.post("/machines")
async def create_machine(data: MachineCreate, current_user: dict = Depends(get_current_user)):
    """Create new machine"""
    machine_id = str(uuid.uuid4())
    
    # Check for duplicate code
    existing = await db.production_machines.find_one({'machine_code': data.machine_code})
    if existing:
        raise HTTPException(status_code=400, detail="Machine code already exists")
    
    machine_doc = {
        'id': machine_id,
        **data.model_dump(),
        'status': 'active',
        'total_production_hours': 0,
        'total_output': 0,
        'avg_wastage_percent': 0,
        'created_at': datetime.now(timezone.utc).isoformat(),
        'created_by': current_user['id']
    }
    
    await db.production_machines.insert_one(machine_doc)
    return {k: v for k, v in machine_doc.items() if k != '_id'}

@router.put("/machines/{machine_id}")
async def update_machine(machine_id: str, data: MachineUpdate, current_user: dict = Depends(get_current_user)):
    """Update machine"""
    update_data = {k: v for k, v in data.model_dump().items() if v is not None}
    update_data['updated_at'] = datetime.now(timezone.utc).isoformat()
    update_data['updated_by'] = current_user['id']
    
    result = await db.production_machines.update_one(
        {'id': machine_id},
        {'$set': update_data}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Machine not found")
    
    return {'message': 'Machine updated successfully'}

@router.delete("/machines/{machine_id}")
async def delete_machine(machine_id: str, current_user: dict = Depends(get_current_user)):
    """Deactivate machine (soft delete)"""
    result = await db.production_machines.update_one(
        {'id': machine_id},
        {'$set': {'status': 'inactive', 'deactivated_at': datetime.now(timezone.utc).isoformat()}}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Machine not found")
    
    return {'message': 'Machine deactivated'}

@router.get("/machines/suggest/{product_id}")
async def suggest_machine(product_id: str, stage: str, current_user: dict = Depends(get_current_user)):
    """Auto-suggest machine based on production history"""
    # Find most frequently used machine for this product and stage
    pipeline = [
        {'$match': {'item_id': product_id, 'stage': stage, 'status': {'$in': ['completed', 'in_progress']}}},
        {'$group': {'_id': '$machine_id', 'count': {'$sum': 1}, 'avg_wastage': {'$avg': '$actual_wastage_percent'}}},
        {'$sort': {'count': -1}},
        {'$limit': 3}
    ]
    
    suggestions = await db.work_order_stages.aggregate(pipeline).to_list(3)
    
    if not suggestions:
        # Return machines of the required type if no history
        machines = await db.production_machines.find(
            {'machine_type': stage, 'status': 'active'},
            {'_id': 0}
        ).to_list(5)
        return {'suggestions': machines, 'based_on': 'machine_type'}
    
    # Get machine details for suggestions
    machine_ids = [s['_id'] for s in suggestions]
    machines = await db.production_machines.find(
        {'id': {'$in': machine_ids}},
        {'_id': 0}
    ).to_list(10)
    
    # Enrich with usage stats
    result = []
    for m in machines:
        stats = next((s for s in suggestions if s['_id'] == m['id']), {})
        result.append({
            **m,
            'usage_count': stats.get('count', 0),
            'avg_wastage': round(stats.get('avg_wastage', 0), 2)
        })
    
    return {'suggestions': result, 'based_on': 'history'}


# ==================== SALES ORDERS LOOKUP ====================

@router.get("/sales-orders/available")
async def get_available_sales_orders(current_user: dict = Depends(get_current_user)):
    """Get sales orders that haven't been converted to order sheets yet"""
    # Get existing order sheet sales_order_ids
    existing_os = await db.order_sheets.distinct('sales_order_id')
    
    # Get sales orders not yet in production
    sales_orders = await db.sales_orders.find(
        {'id': {'$nin': existing_os}, 'status': {'$in': ['pending', 'confirmed']}},
        {'_id': 0}
    ).sort('created_at', -1).to_list(500)
    
    return sales_orders

@router.get("/sales-orders/{order_id}")
async def get_sales_order_detail(order_id: str, current_user: dict = Depends(get_current_user)):
    """Get single sales order details"""
    order = await db.sales_orders.find_one({'id': order_id}, {'_id': 0})
    if not order:
        raise HTTPException(status_code=404, detail="Sales order not found")
    return order


# ==================== ORDER SHEET ENDPOINTS ====================

@router.post("/order-sheets")
async def create_order_sheet(data: OrderSheetCreate, current_user: dict = Depends(get_current_user)):
    """Create order sheet from sales order - auto-generates work orders for all stages"""
    order_sheet_id = str(uuid.uuid4())
    order_sheet_no = f"OS-{datetime.now(timezone.utc).strftime('%Y%m%d')}-{str(uuid.uuid4())[:6].upper()}"
    
    order_sheet_doc = {
        'id': order_sheet_id,
        'order_sheet_no': order_sheet_no,
        **data.model_dump(),
        'status': 'active',
        'total_items': len(data.items),
        'completed_items': 0,
        'created_at': datetime.now(timezone.utc).isoformat(),
        'created_by': current_user['id']
    }
    
    await db.order_sheets.insert_one(order_sheet_doc)
    
    # Auto-generate work orders for each item
    work_orders_created = []
    for item in data.items:
        # Determine which stages this item needs based on product type
        stages_needed = determine_stages_for_product(item)
        
        for stage in stages_needed:
            wo_id = str(uuid.uuid4())
            wo_number = f"WO-{stage[:3].upper()}-{datetime.now(timezone.utc).strftime('%Y%m%d')}-{str(uuid.uuid4())[:4].upper()}"
            
            wo_doc = {
                'id': wo_id,
                'wo_number': wo_number,
                'order_sheet_id': order_sheet_id,
                'sales_order_id': data.sales_order_id,
                'customer_id': data.customer_id,
                'customer_name': data.customer_name,
                'stage': stage,
                'item_id': item.get('item_id'),
                'item_name': item.get('item_name'),
                'item_code': item.get('item_code'),
                'target_qty': item.get('quantity', 0),
                'target_uom': item.get('uom', 'pcs'),
                'completed_qty': 0,
                'wastage_qty': 0,
                'actual_wastage_percent': 0,
                'machine_id': None,
                'machine_name': None,
                'priority': data.priority,
                'status': 'pending',
                'color': item.get('color'),
                'thickness': item.get('thickness'),
                'width': item.get('width'),
                'length': item.get('length'),
                'brand': item.get('brand'),
                'specs': item,  # Store all specs
                'comments': [],
                'created_at': datetime.now(timezone.utc).isoformat(),
                'created_by': current_user['id']
            }
            
            await db.work_order_stages.insert_one(wo_doc)
            work_orders_created.append(wo_doc)
    
    # Mark stock as "hold" in inventory
    await hold_stock_for_order(data.sales_order_id, data.items, current_user['id'])
    
    return {
        'order_sheet': {k: v for k, v in order_sheet_doc.items() if k != '_id'},
        'work_orders_created': len(work_orders_created),
        'message': 'Order sheet created with work orders for all stages'
    }

@router.get("/order-sheets")
async def get_order_sheets(
    status: Optional[str] = None,
    customer_id: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Get all order sheets"""
    query = {}
    if status:
        query['status'] = status
    if customer_id:
        query['customer_id'] = customer_id
    
    order_sheets = await db.order_sheets.find(query, {'_id': 0}).sort('created_at', -1).to_list(500)
    
    # Enrich with progress stats
    for os in order_sheets:
        stages = await db.work_order_stages.find(
            {'order_sheet_id': os['id']},
            {'_id': 0, 'status': 1, 'stage': 1}
        ).to_list(1000)
        
        os['total_stages'] = len(stages)
        os['completed_stages'] = len([s for s in stages if s['status'] == 'completed'])
        os['in_progress_stages'] = len([s for s in stages if s['status'] == 'in_progress'])
        os['progress_percent'] = round((os['completed_stages'] / max(os['total_stages'], 1)) * 100, 1)
    
    return order_sheets

@router.get("/order-sheets/{order_sheet_id}")
async def get_order_sheet_detail(order_sheet_id: str, current_user: dict = Depends(get_current_user)):
    """Get order sheet with all work orders"""
    order_sheet = await db.order_sheets.find_one({'id': order_sheet_id}, {'_id': 0})
    if not order_sheet:
        raise HTTPException(status_code=404, detail="Order sheet not found")
    
    work_orders = await db.work_order_stages.find(
        {'order_sheet_id': order_sheet_id},
        {'_id': 0}
    ).sort([('stage', 1), ('created_at', 1)]).to_list(1000)
    
    # Group by different views
    order_wise = {}
    product_wise = {}
    machine_wise = {}
    
    for wo in work_orders:
        # Order-wise grouping
        order_id = wo.get('sales_order_id', 'unknown')
        if order_id not in order_wise:
            order_wise[order_id] = {
                'sales_order_id': order_id,
                'customer_name': wo.get('customer_name'),
                'work_orders': [],
                'total_target': 0,
                'total_completed': 0
            }
        order_wise[order_id]['work_orders'].append(wo)
        order_wise[order_id]['total_target'] += wo.get('target_qty', 0)
        order_wise[order_id]['total_completed'] += wo.get('completed_qty', 0)
        
        # Product-wise grouping
        item_id = wo.get('item_id', 'unknown')
        if item_id not in product_wise:
            product_wise[item_id] = {
                'item_id': item_id,
                'item_name': wo.get('item_name'),
                'item_code': wo.get('item_code'),
                'stages': {}
            }
        stage = wo.get('stage')
        if stage not in product_wise[item_id]['stages']:
            product_wise[item_id]['stages'][stage] = []
        product_wise[item_id]['stages'][stage].append(wo)
        
        # Machine-wise grouping
        machine_id = wo.get('machine_id')
        if machine_id:
            if machine_id not in machine_wise:
                machine_wise[machine_id] = {
                    'machine_id': machine_id,
                    'machine_name': wo.get('machine_name'),
                    'work_orders': [],
                    'total_target': 0,
                    'total_completed': 0
                }
            machine_wise[machine_id]['work_orders'].append(wo)
            machine_wise[machine_id]['total_target'] += wo.get('target_qty', 0)
            machine_wise[machine_id]['total_completed'] += wo.get('completed_qty', 0)
    
    return {
        'order_sheet': order_sheet,
        'work_orders': work_orders,
        'views': {
            'order_wise': list(order_wise.values()),
            'product_wise': list(product_wise.values()),
            'machine_wise': list(machine_wise.values())
        }
    }


# ==================== WORK ORDER STAGE ENDPOINTS ====================

@router.get("/work-order-stages")
async def get_work_order_stages(
    stage: Optional[str] = None,
    status: Optional[str] = None,
    machine_id: Optional[str] = None,
    sales_order_id: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Get work order stages with filters"""
    query = {}
    if stage:
        query['stage'] = stage
    if status:
        query['status'] = status
    if machine_id:
        query['machine_id'] = machine_id
    if sales_order_id:
        query['sales_order_id'] = sales_order_id
    
    stages = await db.work_order_stages.find(query, {'_id': 0}).sort('created_at', -1).to_list(1000)
    return stages

@router.get("/work-order-stages/{wo_id}")
async def get_work_order_stage(wo_id: str, current_user: dict = Depends(get_current_user)):
    """Get single work order stage with entries"""
    wo = await db.work_order_stages.find_one({'id': wo_id}, {'_id': 0})
    if not wo:
        raise HTTPException(status_code=404, detail="Work order not found")
    
    entries = await db.stage_entries.find(
        {'work_order_stage_id': wo_id},
        {'_id': 0}
    ).sort('created_at', -1).to_list(100)
    
    return {**wo, 'entries': entries}

@router.put("/work-order-stages/{wo_id}/assign-machine")
async def assign_machine_to_stage(
    wo_id: str,
    machine_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Assign machine to work order stage"""
    machine = await db.production_machines.find_one({'id': machine_id}, {'_id': 0})
    if not machine:
        raise HTTPException(status_code=404, detail="Machine not found")
    
    result = await db.work_order_stages.update_one(
        {'id': wo_id},
        {'$set': {
            'machine_id': machine_id,
            'machine_name': machine.get('machine_name'),
            'machine_code': machine.get('machine_code'),
            'assigned_at': datetime.now(timezone.utc).isoformat(),
            'assigned_by': current_user['id']
        }}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Work order not found")
    
    return {'message': 'Machine assigned successfully'}

@router.put("/work-order-stages/{wo_id}/start")
async def start_work_order_stage(wo_id: str, current_user: dict = Depends(get_current_user)):
    """Start work order stage"""
    wo = await db.work_order_stages.find_one({'id': wo_id}, {'_id': 0})
    if not wo:
        raise HTTPException(status_code=404, detail="Work order not found")
    
    if not wo.get('machine_id'):
        raise HTTPException(status_code=400, detail="Assign a machine before starting")
    
    await db.work_order_stages.update_one(
        {'id': wo_id},
        {'$set': {
            'status': 'in_progress',
            'started_at': datetime.now(timezone.utc).isoformat(),
            'started_by': current_user['id']
        }}
    )
    
    return {'message': 'Work order started'}

@router.post("/work-order-stages/{wo_id}/entry")
async def create_stage_entry(wo_id: str, data: StageEntryCreate, current_user: dict = Depends(get_current_user)):
    """Create production entry for a work order stage"""
    wo = await db.work_order_stages.find_one({'id': wo_id}, {'_id': 0})
    if not wo:
        raise HTTPException(status_code=404, detail="Work order not found")
    
    entry_id = str(uuid.uuid4())
    batch_no = f"{wo.get('item_code', 'ITM')}-{datetime.now(timezone.utc).strftime('%Y%m%d')}-{wo.get('machine_code', 'M')}-{str(uuid.uuid4())[:4].upper()}"
    
    # Calculate wastage percentage
    total_input = data.input_qty
    wastage_percent = (data.wastage_qty / total_input * 100) if total_input > 0 else 0
    
    # Get machine wastage norm
    machine = await db.production_machines.find_one({'id': wo.get('machine_id')}, {'_id': 0})
    wastage_norm = machine.get('wastage_norm_percent', 2.0) if machine else 2.0
    
    # Check if wastage exceeds norm
    wastage_exceeded = wastage_percent > wastage_norm
    
    entry_doc = {
        'id': entry_id,
        'batch_no': batch_no,
        **data.model_dump(),
        'wastage_percent': round(wastage_percent, 2),
        'wastage_norm': wastage_norm,
        'wastage_exceeded': wastage_exceeded,
        'stage': wo.get('stage'),
        'machine_id': wo.get('machine_id'),
        'item_id': wo.get('item_id'),
        'created_at': datetime.now(timezone.utc).isoformat(),
        'created_by': current_user['id']
    }
    
    await db.stage_entries.insert_one(entry_doc)
    
    # Update work order totals
    new_completed = wo.get('completed_qty', 0) + data.output_qty
    new_wastage = wo.get('wastage_qty', 0) + data.wastage_qty
    total_produced = new_completed + new_wastage
    avg_wastage = (new_wastage / total_produced * 100) if total_produced > 0 else 0
    
    status = 'completed' if new_completed >= wo.get('target_qty', 0) else 'in_progress'
    
    await db.work_order_stages.update_one(
        {'id': wo_id},
        {'$set': {
            'completed_qty': new_completed,
            'wastage_qty': new_wastage,
            'actual_wastage_percent': round(avg_wastage, 2),
            'status': status,
            'last_entry_at': datetime.now(timezone.utc).isoformat()
        }}
    )
    
    # If completed, check if we should move to next stage
    if status == 'completed':
        await db.work_order_stages.update_one(
            {'id': wo_id},
            {'$set': {'completed_at': datetime.now(timezone.utc).isoformat()}}
        )
    
    return {
        'entry': {k: v for k, v in entry_doc.items() if k != '_id'},
        'wastage_exceeded': wastage_exceeded,
        'wastage_norm': wastage_norm,
        'message': 'Production entry recorded'
    }

@router.post("/work-order-stages/{wo_id}/comment")
async def add_comment(wo_id: str, comment: str, current_user: dict = Depends(get_current_user)):
    """Add comment to work order"""
    comment_doc = {
        'id': str(uuid.uuid4()),
        'comment': comment,
        'user_id': current_user['id'],
        'user_name': current_user.get('name', 'Unknown'),
        'created_at': datetime.now(timezone.utc).isoformat()
    }
    
    result = await db.work_order_stages.update_one(
        {'id': wo_id},
        {'$push': {'comments': comment_doc}}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Work order not found")
    
    return {'message': 'Comment added', 'comment': comment_doc}

@router.put("/work-order-stages/{wo_id}/priority")
async def update_priority(wo_id: str, priority: str, current_user: dict = Depends(get_current_user)):
    """Update work order priority"""
    if priority not in ['urgent', 'high', 'normal', 'low']:
        raise HTTPException(status_code=400, detail="Invalid priority")
    
    result = await db.work_order_stages.update_one(
        {'id': wo_id},
        {'$set': {'priority': priority, 'updated_at': datetime.now(timezone.utc).isoformat()}}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Work order not found")
    
    return {'message': 'Priority updated'}


@router.put("/work-order-stages/{wo_id}/status")
async def update_work_order_status(wo_id: str, status: str, current_user: dict = Depends(get_current_user)):
    """Update work order status - with inventory integration for 'delivered' status"""
    valid_statuses = ['pending', 'in_progress', 'completed', 'on_hold', 'delivered']
    if status not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"Invalid status. Valid: {valid_statuses}")
    
    wo = await db.work_order_stages.find_one({'id': wo_id}, {'_id': 0})
    if not wo:
        raise HTTPException(status_code=404, detail="Work order not found")
    
    update_data = {
        'status': status,
        'updated_at': datetime.now(timezone.utc).isoformat()
    }
    
    # Handle delivered status - release stock
    if status == 'delivered' and wo.get('status') != 'delivered':
        update_data['delivered_at'] = datetime.now(timezone.utc).isoformat()
        update_data['delivered_by'] = current_user['id']
        
        # Check if all work orders for this order sheet are delivered
        order_sheet_id = wo.get('order_sheet_id')
        if order_sheet_id:
            all_wos = await db.work_order_stages.find(
                {'order_sheet_id': order_sheet_id},
                {'_id': 0, 'status': 1}
            ).to_list(1000)
            
            # Count non-delivered (excluding current one being updated)
            non_delivered = len([w for w in all_wos if w.get('status') != 'delivered' and w.get('id') != wo_id])
            
            # If this is the last one, release stock for the entire order
            if non_delivered == 0:
                sales_order_id = wo.get('sales_order_id')
                if sales_order_id:
                    await release_stock_on_delivery(sales_order_id, current_user['id'])
                    
                    # Update order sheet status
                    await db.order_sheets.update_one(
                        {'id': order_sheet_id},
                        {'$set': {
                            'status': 'completed',
                            'completed_at': datetime.now(timezone.utc).isoformat()
                        }}
                    )
    
    result = await db.work_order_stages.update_one(
        {'id': wo_id},
        {'$set': update_data}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Work order not found")
    
    return {
        'message': f'Status updated to {status}',
        'stock_released': status == 'delivered'
    }


@router.post("/order-sheets/{order_sheet_id}/mark-delivered")
async def mark_order_delivered(order_sheet_id: str, current_user: dict = Depends(get_current_user)):
    """Mark entire order sheet as delivered and release inventory"""
    order_sheet = await db.order_sheets.find_one({'id': order_sheet_id}, {'_id': 0})
    if not order_sheet:
        raise HTTPException(status_code=404, detail="Order sheet not found")
    
    sales_order_id = order_sheet.get('sales_order_id')
    
    # Update all work orders to delivered
    await db.work_order_stages.update_many(
        {'order_sheet_id': order_sheet_id},
        {'$set': {
            'status': 'delivered',
            'delivered_at': datetime.now(timezone.utc).isoformat(),
            'delivered_by': current_user['id']
        }}
    )
    
    # Update order sheet status
    await db.order_sheets.update_one(
        {'id': order_sheet_id},
        {'$set': {
            'status': 'completed',
            'completed_at': datetime.now(timezone.utc).isoformat()
        }}
    )
    
    # Release stock
    if sales_order_id:
        await release_stock_on_delivery(sales_order_id, current_user['id'])
    
    return {
        'message': 'Order marked as delivered',
        'stock_released': True,
        'sales_order_id': sales_order_id
    }


@router.get("/inventory/holds")
async def get_stock_holds(
    status: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Get all stock holds with status filter"""
    query = {}
    if status:
        query['status'] = status
    
    holds = await db.stock_holds.find(query, {'_id': 0}).sort('created_at', -1).to_list(500)
    
    # Enrich with item details
    for hold in holds:
        item = await db.stock_items.find_one({'id': hold.get('item_id')}, {'_id': 0, 'item_name': 1, 'item_code': 1})
        if item:
            hold['item_name'] = item.get('item_name')
            hold['item_code'] = item.get('item_code')
    
    return holds


@router.get("/inventory/stock-status")
async def get_production_stock_status(current_user: dict = Depends(get_current_user)):
    """Get stock status showing available, reserved, and total quantities"""
    # Get all stock balances
    balances = await db.stock_balance.find({}, {'_id': 0}).to_list(500)
    
    # Enrich with item details
    result = []
    for bal in balances:
        item = await db.stock_items.find_one({'id': bal.get('item_id')}, {'_id': 0, 'item_name': 1, 'item_code': 1, 'category': 1})
        if item:
            result.append({
                'item_id': bal.get('item_id'),
                'item_name': item.get('item_name'),
                'item_code': item.get('item_code'),
                'category': item.get('category'),
                'total_qty': bal.get('quantity', 0),
                'reserved_qty': bal.get('reserved_qty', 0),
                'available_qty': bal.get('available_qty', bal.get('quantity', 0)),
                'warehouse_id': bal.get('warehouse_id')
            })
    
    return result


# ==================== STAGE-SPECIFIC DASHBOARDS ====================

@router.get("/stages/{stage}/dashboard")
async def get_stage_dashboard(stage: str, current_user: dict = Depends(get_current_user)):
    """Get dashboard stats for a specific production stage"""
    valid_stages = ['coating', 'slitting', 'rewinding', 'cutting', 'packing', 'ready_to_deliver', 'delivered']
    if stage not in valid_stages:
        raise HTTPException(status_code=400, detail=f"Invalid stage. Valid stages: {valid_stages}")
    
    # Get work orders for this stage
    work_orders = await db.work_order_stages.find(
        {'stage': stage},
        {'_id': 0}
    ).sort('created_at', -1).to_list(500)
    
    # Get entries for calculations
    entries = await db.stage_entries.find(
        {'stage': stage},
        {'_id': 0}
    ).to_list(1000)
    
    # Calculate stats
    pending = [wo for wo in work_orders if wo.get('status') == 'pending']
    in_progress = [wo for wo in work_orders if wo.get('status') == 'in_progress']
    completed = [wo for wo in work_orders if wo.get('status') == 'completed']
    
    total_target = sum(wo.get('target_qty', 0) for wo in work_orders)
    total_completed = sum(wo.get('completed_qty', 0) for wo in work_orders)
    total_wastage = sum(wo.get('wastage_qty', 0) for wo in work_orders)
    
    # Calculate hourly production average
    total_hours = 0
    total_output = 0
    for entry in entries:
        try:
            start = datetime.fromisoformat(entry.get('start_time', ''))
            end = datetime.fromisoformat(entry.get('end_time', ''))
            hours = (end - start).total_seconds() / 3600
            total_hours += hours
            total_output += entry.get('output_qty', 0)
        except:
            pass
    
    hourly_avg = round(total_output / max(total_hours, 1), 2)
    
    # Get stage-specific metrics based on UOM
    stage_metrics = get_stage_specific_metrics(stage, work_orders, entries)
    
    return {
        'stage': stage,
        'summary': {
            'pending': len(pending),
            'in_progress': len(in_progress),
            'completed': len(completed),
            'total': len(work_orders)
        },
        'quantities': {
            'total_target': total_target,
            'total_completed': total_completed,
            'total_wastage': total_wastage,
            'completion_percent': round((total_completed / max(total_target, 1)) * 100, 1),
            'wastage_percent': round((total_wastage / max(total_completed + total_wastage, 1)) * 100, 2)
        },
        'hourly_production': {
            'total_hours': round(total_hours, 1),
            'total_output': total_output,
            'hourly_avg': hourly_avg
        },
        'stage_metrics': stage_metrics,
        'work_orders': work_orders[:20]  # Recent 20
    }


# ==================== MAIN PRODUCTION DASHBOARD ====================

@router.get("/dashboard")
async def get_production_dashboard(current_user: dict = Depends(get_current_user)):
    """Get main production dashboard"""
    # Get all order sheets
    order_sheets = await db.order_sheets.find({'status': 'active'}, {'_id': 0}).to_list(500)
    
    # Get all work order stages
    work_orders = await db.work_order_stages.find({}, {'_id': 0}).to_list(5000)
    
    # Get all items in production
    items_in_production = await db.work_order_stages.distinct('item_id', {'status': {'$in': ['pending', 'in_progress']}})
    
    # Calculate totals
    total_pcs = sum(wo.get('target_qty', 0) for wo in work_orders if wo.get('target_uom') == 'pcs')
    completed_pcs = sum(wo.get('completed_qty', 0) for wo in work_orders if wo.get('target_uom') == 'pcs')
    
    # SQM calculations
    sqm_work_orders = [wo for wo in work_orders if wo.get('target_uom') == 'sqm' or wo.get('stage') in ['coating', 'slitting']]
    total_sqm = sum(wo.get('target_qty', 0) for wo in sqm_work_orders)
    
    # Stage-wise summary
    stages_summary = {}
    for stage in ['coating', 'slitting', 'rewinding', 'cutting', 'packing', 'ready_to_deliver', 'delivered']:
        stage_wos = [wo for wo in work_orders if wo.get('stage') == stage]
        stages_summary[stage] = {
            'pending': len([w for w in stage_wos if w.get('status') == 'pending']),
            'in_progress': len([w for w in stage_wos if w.get('status') == 'in_progress']),
            'completed': len([w for w in stage_wos if w.get('status') == 'completed']),
            'total': len(stage_wos)
        }
    
    # Priority breakdown
    priority_count = {
        'urgent': len([wo for wo in work_orders if wo.get('priority') == 'urgent' and wo.get('status') != 'completed']),
        'high': len([wo for wo in work_orders if wo.get('priority') == 'high' and wo.get('status') != 'completed']),
        'normal': len([wo for wo in work_orders if wo.get('priority') == 'normal' and wo.get('status') != 'completed']),
        'low': len([wo for wo in work_orders if wo.get('priority') == 'low' and wo.get('status') != 'completed'])
    }
    
    # Get machines
    machines = await db.production_machines.find({'status': 'active'}, {'_id': 0}).to_list(100)
    
    # Calculate overall progress
    total_work_orders = len(work_orders)
    completed_work_orders = len([wo for wo in work_orders if wo.get('status') == 'completed'])
    overall_progress = round((completed_work_orders / max(total_work_orders, 1)) * 100, 1)
    
    return {
        'summary': {
            'total_sku': len(set(wo.get('item_id') for wo in work_orders)),
            'sku_in_process': len(items_in_production),
            'total_pcs_in_process': total_pcs - completed_pcs,
            'total_sqm_in_process': total_sqm,
            'overall_progress': overall_progress
        },
        'order_sheets': {
            'active': len([os for os in order_sheets if os.get('status') == 'active']),
            'total': len(order_sheets)
        },
        'work_orders': {
            'pending': len([wo for wo in work_orders if wo.get('status') == 'pending']),
            'in_progress': len([wo for wo in work_orders if wo.get('status') == 'in_progress']),
            'completed': completed_work_orders,
            'total': total_work_orders
        },
        'stages': stages_summary,
        'priority': priority_count,
        'machines': {
            'total': len(machines),
            'by_type': {}
        }
    }


# ==================== HELPER FUNCTIONS ====================

def determine_stages_for_product(item: dict) -> List[str]:
    """Determine which production stages are needed for a product"""
    # Default all stages
    stages = ['coating', 'slitting', 'rewinding', 'cutting', 'packing', 'ready_to_deliver']
    
    # If product is imported/pre-coated jumbo, skip coating
    if item.get('is_imported') or item.get('skip_coating'):
        stages = [s for s in stages if s != 'coating']
    
    # If direct slitting (no rewinding needed)
    if item.get('process_type') == 'direct_slitting':
        stages = [s for s in stages if s != 'rewinding']
    
    # If no cutting needed
    if item.get('skip_cutting'):
        stages = [s for s in stages if s != 'cutting']
    
    return stages

def get_stage_specific_metrics(stage: str, work_orders: List[dict], entries: List[dict]) -> dict:
    """Get stage-specific metrics"""
    metrics = {}
    
    if stage == 'coating':
        # KGs in/out, Rolls, Weight
        total_kgs_in = sum(e.get('input_qty', 0) for e in entries if e.get('input_uom') == 'kg')
        total_kgs_out = sum(e.get('output_qty', 0) for e in entries if e.get('output_uom') == 'kg')
        metrics = {
            'total_kgs_in': total_kgs_in,
            'total_kgs_out': total_kgs_out,
            'total_rolls': sum(wo.get('completed_qty', 0) for wo in work_orders),
            'total_sqm': sum(wo.get('sqm_in_production', 0) or 0 for wo in work_orders)
        }
    
    elif stage == 'slitting':
        # SQM in/out, Pcs, Ctns
        total_sqm_in = sum(e.get('input_qty', 0) for e in entries if e.get('input_uom') == 'sqm')
        total_sqm_out = sum(e.get('output_qty', 0) for e in entries)
        metrics = {
            'total_sqm_in': total_sqm_in,
            'total_sqm_out': total_sqm_out,
            'total_pcs': sum(wo.get('completed_qty', 0) for wo in work_orders),
            'total_ctn': sum(wo.get('total_ctn', 0) or 0 for wo in work_orders)
        }
    
    elif stage == 'rewinding':
        # Length in/out, Logs/roll
        metrics = {
            'total_length_in': sum(e.get('input_qty', 0) for e in entries if e.get('input_uom') in ['m', 'mtr']),
            'total_length_out': sum(e.get('output_qty', 0) for e in entries if e.get('output_uom') in ['m', 'mtr']),
            'total_pcs': sum(wo.get('completed_qty', 0) for wo in work_orders),
            'total_logs': sum(wo.get('logs_per_roll', 0) or 0 for wo in work_orders)
        }
    
    elif stage == 'cutting':
        # Width in/out
        metrics = {
            'total_width_in': sum(e.get('input_qty', 0) for e in entries if e.get('input_uom') == 'mm'),
            'total_width_out': sum(e.get('output_qty', 0) for e in entries if e.get('output_uom') == 'mm'),
            'total_pcs': sum(wo.get('completed_qty', 0) for wo in work_orders)
        }
    
    elif stage == 'packing':
        # Pcs in/out, Ctns
        metrics = {
            'total_pcs_in': sum(e.get('input_qty', 0) for e in entries if e.get('input_uom') == 'pcs'),
            'total_pcs_out': sum(e.get('output_qty', 0) for e in entries if e.get('output_uom') == 'pcs'),
            'total_ctn': sum(wo.get('total_ctn', 0) or 0 for wo in work_orders),
            'total_sqm': sum(wo.get('sqm_in_production', 0) or 0 for wo in work_orders)
        }
    
    return metrics

async def hold_stock_for_order(sales_order_id: str, items: List[dict], user_id: str):
    """Mark stock as 'hold' for order in inventory"""
    for item in items:
        item_id = item.get('item_id')
        qty = item.get('quantity', 0)
        
        if not item_id:
            continue
        
        # Update stock_balance to reserve/hold quantity
        await db.stock_balance.update_one(
            {'item_id': item_id},
            {'$inc': {'reserved_qty': qty, 'available_qty': -qty}}
        )
        
        # Create stock hold record
        await db.stock_holds.insert_one({
            'id': str(uuid.uuid4()),
            'item_id': item_id,
            'sales_order_id': sales_order_id,
            'quantity': qty,
            'status': 'held',
            'created_at': datetime.now(timezone.utc).isoformat(),
            'created_by': user_id
        })

async def release_stock_on_delivery(sales_order_id: str, user_id: str):
    """Release held stock and deduct from inventory after delivery"""
    holds = await db.stock_holds.find(
        {'sales_order_id': sales_order_id, 'status': 'held'},
        {'_id': 0}
    ).to_list(500)
    
    for hold in holds:
        # Update stock balance - deduct from physical stock
        await db.stock_balance.update_one(
            {'item_id': hold['item_id']},
            {'$inc': {
                'quantity': -hold['quantity'],
                'reserved_qty': -hold['quantity']
            }}
        )
        
        # Create stock ledger entry
        await db.stock_ledger.insert_one({
            'id': str(uuid.uuid4()),
            'item_id': hold['item_id'],
            'transaction_date': datetime.now(timezone.utc).isoformat(),
            'transaction_type': 'sales_delivery',
            'reference_type': 'SalesOrder',
            'reference_id': sales_order_id,
            'in_qty': 0,
            'out_qty': hold['quantity'],
            'notes': f"Delivered against SO: {sales_order_id}",
            'created_by': user_id
        })
        
        # Update hold status
        await db.stock_holds.update_one(
            {'id': hold['id']},
            {'$set': {'status': 'released', 'released_at': datetime.now(timezone.utc).isoformat()}}
        )


# ==================== REPORTS ====================

@router.get("/reports/stage-wise")
async def get_stage_wise_report(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Get stage-wise production report"""
    query = {}
    if start_date:
        query['created_at'] = {'$gte': start_date}
    if end_date:
        if 'created_at' in query:
            query['created_at']['$lte'] = end_date
        else:
            query['created_at'] = {'$lte': end_date}
    
    entries = await db.stage_entries.find(query, {'_id': 0}).to_list(10000)
    
    # Group by stage
    stage_data = {}
    for entry in entries:
        stage = entry.get('stage', 'unknown')
        if stage not in stage_data:
            stage_data[stage] = {
                'total_entries': 0,
                'total_input': 0,
                'total_output': 0,
                'total_wastage': 0,
                'total_hours': 0
            }
        
        stage_data[stage]['total_entries'] += 1
        stage_data[stage]['total_input'] += entry.get('input_qty', 0)
        stage_data[stage]['total_output'] += entry.get('output_qty', 0)
        stage_data[stage]['total_wastage'] += entry.get('wastage_qty', 0)
        
        try:
            start = datetime.fromisoformat(entry.get('start_time', ''))
            end = datetime.fromisoformat(entry.get('end_time', ''))
            hours = (end - start).total_seconds() / 3600
            stage_data[stage]['total_hours'] += hours
        except:
            pass
    
    # Calculate percentages and averages
    for stage, data in stage_data.items():
        total_produced = data['total_output'] + data['total_wastage']
        data['wastage_percent'] = round((data['total_wastage'] / max(total_produced, 1)) * 100, 2)
        data['hourly_avg'] = round(data['total_output'] / max(data['total_hours'], 1), 2)
    
    return stage_data

@router.get("/reports/machine-wise")
async def get_machine_wise_report(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Get machine-wise production report"""
    query = {}
    if start_date:
        query['created_at'] = {'$gte': start_date}
    if end_date:
        if 'created_at' in query:
            query['created_at']['$lte'] = end_date
        else:
            query['created_at'] = {'$lte': end_date}
    
    entries = await db.stage_entries.find(query, {'_id': 0}).to_list(10000)
    
    # Get machines
    machines = await db.production_machines.find({}, {'_id': 0}).to_list(500)
    machine_map = {m['id']: m for m in machines}
    
    # Group by machine
    machine_data = {}
    for entry in entries:
        machine_id = entry.get('machine_id', 'unknown')
        if machine_id not in machine_data:
            machine_info = machine_map.get(machine_id, {})
            machine_data[machine_id] = {
                'machine_name': machine_info.get('machine_name', 'Unknown'),
                'machine_code': machine_info.get('machine_code', ''),
                'machine_type': machine_info.get('machine_type', ''),
                'total_entries': 0,
                'total_output': 0,
                'total_wastage': 0,
                'total_hours': 0,
                'wastage_norm': machine_info.get('wastage_norm_percent', 2.0)
            }
        
        machine_data[machine_id]['total_entries'] += 1
        machine_data[machine_id]['total_output'] += entry.get('output_qty', 0)
        machine_data[machine_id]['total_wastage'] += entry.get('wastage_qty', 0)
        
        try:
            start = datetime.fromisoformat(entry.get('start_time', ''))
            end = datetime.fromisoformat(entry.get('end_time', ''))
            hours = (end - start).total_seconds() / 3600
            machine_data[machine_id]['total_hours'] += hours
        except:
            pass
    
    # Calculate stats
    for machine_id, data in machine_data.items():
        total_produced = data['total_output'] + data['total_wastage']
        data['wastage_percent'] = round((data['total_wastage'] / max(total_produced, 1)) * 100, 2)
        data['hourly_avg'] = round(data['total_output'] / max(data['total_hours'], 1), 2)
        data['above_norm'] = data['wastage_percent'] > data['wastage_norm']
    
    return machine_data


# ==================== DPR (DAILY PRODUCTION REPORT) ====================

@router.get("/dpr/{report_date}")
async def get_daily_production_report(
    report_date: str,
    current_user: dict = Depends(get_current_user)
):
    """Get comprehensive Daily Production Report (DPR) for a specific date"""
    # Parse date range for the day
    start_of_day = f"{report_date}T00:00:00"
    end_of_day = f"{report_date}T23:59:59"
    
    # Get all entries for the day
    entries = await db.stage_entries.find({
        'created_at': {'$gte': start_of_day, '$lte': end_of_day}
    }, {'_id': 0}).to_list(5000)
    
    # Get work orders updated on this day
    work_orders = await db.work_order_stages.find({
        '$or': [
            {'last_entry_at': {'$gte': start_of_day, '$lte': end_of_day}},
            {'started_at': {'$gte': start_of_day, '$lte': end_of_day}}
        ]
    }, {'_id': 0}).to_list(1000)
    
    # Get machines for reference
    machines = await db.production_machines.find({}, {'_id': 0}).to_list(100)
    machine_map = {m['id']: m for m in machines}
    
    # Build stage-wise DPR
    dpr_data = {
        'report_date': report_date,
        'generated_at': datetime.now(timezone.utc).isoformat(),
        'summary': {
            'total_entries': len(entries),
            'total_work_orders_active': len(work_orders),
            'total_output': sum(e.get('output_qty', 0) for e in entries),
            'total_wastage': sum(e.get('wastage_qty', 0) for e in entries),
            'total_hours_worked': 0
        },
        'stages': {}
    }
    
    # Calculate total hours
    for entry in entries:
        try:
            start = datetime.fromisoformat(entry.get('start_time', ''))
            end = datetime.fromisoformat(entry.get('end_time', ''))
            hours = (end - start).total_seconds() / 3600
            dpr_data['summary']['total_hours_worked'] += hours
        except:
            pass
    
    dpr_data['summary']['total_hours_worked'] = round(dpr_data['summary']['total_hours_worked'], 2)
    
    # Build per-stage reports
    stages = ['coating', 'slitting', 'rewinding', 'cutting', 'packing']
    
    for stage in stages:
        stage_entries = [e for e in entries if e.get('stage') == stage]
        stage_wos = [wo for wo in work_orders if wo.get('stage') == stage]
        
        if not stage_entries and not stage_wos:
            continue
        
        stage_report = build_stage_dpr(stage, stage_entries, stage_wos, machine_map)
        dpr_data['stages'][stage] = stage_report
    
    return dpr_data


@router.get("/dpr/{report_date}/stage/{stage}")
async def get_stage_dpr(
    report_date: str,
    stage: str,
    current_user: dict = Depends(get_current_user)
):
    """Get detailed DPR for a specific stage"""
    valid_stages = ['coating', 'slitting', 'rewinding', 'cutting', 'packing']
    if stage not in valid_stages:
        raise HTTPException(status_code=400, detail=f"Invalid stage. Valid stages: {valid_stages}")
    
    start_of_day = f"{report_date}T00:00:00"
    end_of_day = f"{report_date}T23:59:59"
    
    # Get entries for this stage on this day
    entries = await db.stage_entries.find({
        'stage': stage,
        'created_at': {'$gte': start_of_day, '$lte': end_of_day}
    }, {'_id': 0}).to_list(1000)
    
    # Get work orders for this stage
    work_orders = await db.work_order_stages.find({
        'stage': stage,
        '$or': [
            {'last_entry_at': {'$gte': start_of_day, '$lte': end_of_day}},
            {'started_at': {'$gte': start_of_day, '$lte': end_of_day}},
            {'status': 'in_progress'}
        ]
    }, {'_id': 0}).to_list(500)
    
    machines = await db.production_machines.find({'machine_type': stage}, {'_id': 0}).to_list(50)
    machine_map = {m['id']: m for m in machines}
    
    return {
        'report_date': report_date,
        'stage': stage,
        'generated_at': datetime.now(timezone.utc).isoformat(),
        **build_stage_dpr(stage, entries, work_orders, machine_map),
        'entries': entries,
        'work_orders': work_orders
    }


def build_stage_dpr(stage: str, entries: List[dict], work_orders: List[dict], machine_map: dict) -> dict:
    """Build stage-specific DPR data"""
    
    # Common calculations
    total_input = sum(e.get('input_qty', 0) for e in entries)
    total_output = sum(e.get('output_qty', 0) for e in entries)
    total_wastage = sum(e.get('wastage_qty', 0) for e in entries)
    total_hours = 0
    
    for entry in entries:
        try:
            start = datetime.fromisoformat(entry.get('start_time', ''))
            end = datetime.fromisoformat(entry.get('end_time', ''))
            hours = (end - start).total_seconds() / 3600
            total_hours += hours
        except:
            pass
    
    hourly_avg = round(total_output / max(total_hours, 1), 2)
    wastage_percent = round((total_wastage / max(total_input, 1)) * 100, 2)
    
    # Group by machine
    machine_production = {}
    for entry in entries:
        machine_id = entry.get('machine_id')
        if machine_id:
            if machine_id not in machine_production:
                machine_info = machine_map.get(machine_id, {})
                machine_production[machine_id] = {
                    'machine_name': machine_info.get('machine_name', 'Unknown'),
                    'machine_code': machine_info.get('machine_code', ''),
                    'wastage_norm': machine_info.get('wastage_norm_percent', 2.0),
                    'entries': 0,
                    'input': 0,
                    'output': 0,
                    'wastage': 0,
                    'hours': 0
                }
            machine_production[machine_id]['entries'] += 1
            machine_production[machine_id]['input'] += entry.get('input_qty', 0)
            machine_production[machine_id]['output'] += entry.get('output_qty', 0)
            machine_production[machine_id]['wastage'] += entry.get('wastage_qty', 0)
            try:
                start = datetime.fromisoformat(entry.get('start_time', ''))
                end = datetime.fromisoformat(entry.get('end_time', ''))
                machine_production[machine_id]['hours'] += (end - start).total_seconds() / 3600
            except:
                pass
    
    # Calculate machine-wise stats
    for machine_id, data in machine_production.items():
        data['wastage_percent'] = round((data['wastage'] / max(data['input'], 1)) * 100, 2)
        data['hourly_avg'] = round(data['output'] / max(data['hours'], 1), 2)
        data['above_norm'] = data['wastage_percent'] > data['wastage_norm']
    
    # Stage-specific metrics
    stage_metrics = {}
    
    if stage == 'coating':
        # Coating specific: KGs in/out, Rolls, Weight, SQM
        stage_metrics = {
            'total_kgs_in': sum(e.get('input_qty', 0) for e in entries if e.get('input_uom') == 'kg'),
            'total_kgs_out': sum(e.get('output_qty', 0) for e in entries if e.get('output_uom') == 'kg'),
            'total_rolls': sum(e.get('output_qty', 0) for e in entries if e.get('output_uom') == 'rolls'),
            'total_sqm': sum(wo.get('sqm_in_production', 0) or 0 for wo in work_orders),
            'total_sqm_estimated': sum(wo.get('sqm_estimated_target', 0) or 0 for wo in work_orders),
            'time_per_roll': round(total_hours / max(sum(e.get('output_qty', 0) for e in entries if e.get('output_uom') == 'rolls'), 1), 2)
        }
    
    elif stage == 'slitting':
        # Slitting specific: SQM in/out, PCS, CTN
        total_pcs = sum(e.get('output_qty', 0) for e in entries if e.get('output_uom') == 'pcs')
        stage_metrics = {
            'total_sqm_in': sum(e.get('input_qty', 0) for e in entries if e.get('input_uom') == 'sqm'),
            'total_sqm_out': sum(e.get('output_qty', 0) for e in entries if e.get('output_uom') == 'sqm'),
            'total_pcs': total_pcs,
            'total_ctn': sum(wo.get('total_ctn', 0) or 0 for wo in work_orders),
            'hourly_avg_pcs': round(total_pcs / max(total_hours, 1), 2),
            'hourly_avg_sqm': round(sum(e.get('output_qty', 0) for e in entries if e.get('output_uom') == 'sqm') / max(total_hours, 1), 2)
        }
    
    elif stage == 'rewinding':
        # Rewinding specific: Length in/out, Logs/roll
        stage_metrics = {
            'total_length_in': sum(e.get('input_qty', 0) for e in entries if e.get('input_uom') in ['m', 'mtr']),
            'total_length_out': sum(e.get('output_qty', 0) for e in entries if e.get('output_uom') in ['m', 'mtr']),
            'total_pcs': sum(e.get('output_qty', 0) for e in entries if e.get('output_uom') == 'pcs'),
            'total_logs': sum(wo.get('logs_per_roll', 0) or 0 for wo in work_orders),
            'balance_jumbo': sum(wo.get('target_qty', 0) - wo.get('completed_qty', 0) for wo in work_orders)
        }
    
    elif stage == 'cutting':
        # Cutting specific: Width in/out
        stage_metrics = {
            'total_width_in': sum(e.get('input_qty', 0) for e in entries if e.get('input_uom') == 'mm'),
            'total_width_out': sum(e.get('output_qty', 0) for e in entries if e.get('output_uom') == 'mm'),
            'total_pcs': sum(e.get('output_qty', 0) for e in entries if e.get('output_uom') == 'pcs'),
            'calculated_vs_actual': {
                'calculated': sum(wo.get('target_qty', 0) for wo in work_orders),
                'actual': sum(wo.get('completed_qty', 0) for wo in work_orders)
            }
        }
    
    elif stage == 'packing':
        # Packing specific: PCS in/out, CTN, QC videos
        stage_metrics = {
            'total_pcs_in': sum(e.get('input_qty', 0) for e in entries if e.get('input_uom') == 'pcs'),
            'total_pcs_out': sum(e.get('output_qty', 0) for e in entries if e.get('output_uom') == 'pcs'),
            'total_ctn': sum(wo.get('total_ctn', 0) or 0 for wo in work_orders),
            'total_sqm': sum(wo.get('sqm_in_production', 0) or 0 for wo in work_orders),
            'qc_videos_count': len([e for e in entries if e.get('qc_video_url')])
        }
    
    return {
        'summary': {
            'total_entries': len(entries),
            'total_work_orders': len(work_orders),
            'pending': len([wo for wo in work_orders if wo.get('status') == 'pending']),
            'in_progress': len([wo for wo in work_orders if wo.get('status') == 'in_progress']),
            'completed': len([wo for wo in work_orders if wo.get('status') == 'completed'])
        },
        'production': {
            'total_input': total_input,
            'total_output': total_output,
            'total_wastage': total_wastage,
            'wastage_percent': wastage_percent,
            'total_hours': round(total_hours, 2),
            'hourly_avg': hourly_avg
        },
        'stage_metrics': stage_metrics,
        'machine_production': list(machine_production.values())
    }


@router.get("/dpr/summary/weekly")
async def get_weekly_dpr_summary(
    start_date: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Get weekly DPR summary for trend analysis"""
    if not start_date:
        # Default to last 7 days
        end = datetime.now(timezone.utc)
        start = end - timedelta(days=7)
        start_date = start.strftime('%Y-%m-%d')
    else:
        start = datetime.fromisoformat(start_date)
        end = start + timedelta(days=7)
    
    end_date = end.strftime('%Y-%m-%d')
    
    entries = await db.stage_entries.find({
        'created_at': {'$gte': f"{start_date}T00:00:00", '$lte': f"{end_date}T23:59:59"}
    }, {'_id': 0}).to_list(10000)
    
    # Group by date
    daily_data = {}
    for entry in entries:
        date = entry.get('created_at', '')[:10]
        if date not in daily_data:
            daily_data[date] = {
                'date': date,
                'entries': 0,
                'output': 0,
                'wastage': 0,
                'hours': 0
            }
        daily_data[date]['entries'] += 1
        daily_data[date]['output'] += entry.get('output_qty', 0)
        daily_data[date]['wastage'] += entry.get('wastage_qty', 0)
        try:
            start_t = datetime.fromisoformat(entry.get('start_time', ''))
            end_t = datetime.fromisoformat(entry.get('end_time', ''))
            daily_data[date]['hours'] += (end_t - start_t).total_seconds() / 3600
        except:
            pass
    
    # Calculate daily stats
    for date, data in daily_data.items():
        data['wastage_percent'] = round((data['wastage'] / max(data['output'] + data['wastage'], 1)) * 100, 2)
        data['hourly_avg'] = round(data['output'] / max(data['hours'], 1), 2)
        data['hours'] = round(data['hours'], 2)
    
    # Sort by date
    daily_list = sorted(daily_data.values(), key=lambda x: x['date'])
    
    return {
        'start_date': start_date,
        'end_date': end_date,
        'total_days': len(daily_list),
        'daily_data': daily_list,
        'totals': {
            'total_output': sum(d['output'] for d in daily_list),
            'total_wastage': sum(d['wastage'] for d in daily_list),
            'total_hours': round(sum(d['hours'] for d in daily_list), 2),
            'avg_daily_output': round(sum(d['output'] for d in daily_list) / max(len(daily_list), 1), 2),
            'avg_wastage_percent': round(sum(d['wastage_percent'] for d in daily_list) / max(len(daily_list), 1), 2)
        }
    }


# Import timedelta for weekly summary
from datetime import timedelta
