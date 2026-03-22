"""
Two-Stage Production Engine
Stage 1: Coating (Chemical transformation)
  - Water-Based (BOPP)
  - Hotmelt (Single/Double Side)
  - PVC Coating

Stage 2: Converting (Physical transformation)
  - Process A: Direct Slitting (Jumbo → Finished Boxes)
  - Process B: Rewinding & Cutting (Jumbo → Log Roll → PCS)

Includes:
- RM Requisition (Film + Adhesive + Pigment + Liner)
- 7% Scrap Redline Guard
- Batch tracking
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict
from datetime import datetime, timezone
import uuid
from server import db, get_current_user
from utils.document_numbering import generate_document_number
from utils.uom_converter import convert_all_uom, calculate_jumbo_to_slits

router = APIRouter()

SCRAP_REDLINE_PERCENT = 7.0  # Auto-lock if scrap exceeds this


# ==================== RM REQUISITION MODELS ====================
class RMRequisitionItem(BaseModel):
    item_id: str
    item_name: str
    item_type: str  # Film, Adhesive, Pigment, Liner, Solvent
    required_qty: float
    uom: str
    warehouse_id: str
    batch_no: Optional[str] = None


class RMRequisitionCreate(BaseModel):
    work_order_id: str
    items: List[RMRequisitionItem]
    required_date: str
    priority: str = "normal"  # urgent, high, normal, low
    notes: Optional[str] = None


class RMRequisition(BaseModel):
    id: str
    requisition_no: str
    work_order_id: str
    wo_number: Optional[str] = None
    items: List[dict]
    required_date: str
    priority: str
    status: str  # draft, submitted, partial_issued, issued, cancelled
    notes: Optional[str] = None
    created_at: str
    created_by: str
    issued_at: Optional[str] = None
    issued_by: Optional[str] = None


# ==================== COATING (STAGE 1) MODELS ====================
class CoatingBatchCreate(BaseModel):
    work_order_id: str
    coating_type: str  # water_based, hotmelt_single, hotmelt_double, pvc
    machine_id: str
    input_film_item_id: str
    input_film_qty_kg: float
    input_film_batch: Optional[str] = None
    adhesive_item_id: str
    adhesive_qty_kg: float
    adhesive_batch: Optional[str] = None
    pigment_item_id: Optional[str] = None
    pigment_qty_kg: float = 0
    liner_item_id: Optional[str] = None
    liner_qty_sqm: float = 0
    target_gsm: float
    target_width_mm: float
    target_length_m: float
    operator_id: str
    notes: Optional[str] = None


class CoatingBatch(BaseModel):
    id: str
    batch_no: str
    work_order_id: str
    coating_type: str
    machine_id: str
    input_materials: List[dict]
    target_specs: dict
    output_jumbo_qty_sqm: float = 0
    output_jumbo_qty_kg: float = 0
    scrap_qty_kg: float = 0
    scrap_percent: float = 0
    status: str  # in_progress, completed, on_hold, rejected
    qc_status: Optional[str] = None  # pending, passed, failed
    operator_id: str
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    notes: Optional[str] = None
    created_at: str


# ==================== CONVERTING (STAGE 2) MODELS ====================
class ConvertingJobCreate(BaseModel):
    work_order_id: str
    process_type: str  # direct_slitting, rewinding_cutting
    coating_batch_id: str  # Input jumbo from coating
    machine_id: str
    input_jumbo_sqm: float
    slit_width_mm: float
    slit_length_m: float
    target_pcs: int
    operator_id: str
    notes: Optional[str] = None


class ConvertingJob(BaseModel):
    id: str
    job_no: str
    work_order_id: str
    process_type: str
    coating_batch_id: str
    machine_id: str
    input_specs: dict
    output_specs: dict
    actual_output_pcs: int = 0
    scrap_qty: float = 0
    scrap_percent: float = 0
    status: str  # in_progress, completed, on_hold
    operator_id: str
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    notes: Optional[str] = None
    created_at: str


# ==================== RM REQUISITION ENDPOINTS ====================
@router.post("/rm-requisitions", response_model=RMRequisition)
async def create_rm_requisition(data: RMRequisitionCreate, current_user: dict = Depends(get_current_user)):
    """Create RM Requisition for production"""
    req_id = str(uuid.uuid4())
    req_no = await generate_document_number(db, 'rm_requisition', 'HO')
    
    # Get work order details
    wo = await db.work_orders.find_one({'id': data.work_order_id}, {'_id': 0})
    wo_number = wo.get('wo_number') if wo else None
    
    req_doc = {
        'id': req_id,
        'requisition_no': req_no,
        **data.model_dump(),
        'items': [item.model_dump() for item in data.items],
        'wo_number': wo_number,
        'status': 'draft',
        'created_at': datetime.now(timezone.utc).isoformat(),
        'created_by': current_user['id'],
        'issued_at': None,
        'issued_by': None
    }
    
    await db.rm_requisitions.insert_one(req_doc)
    return RMRequisition(**{k: v for k, v in req_doc.items() if k != '_id'})


@router.get("/rm-requisitions", response_model=List[RMRequisition])
async def get_rm_requisitions(
    work_order_id: Optional[str] = None,
    status: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Get all RM requisitions"""
    query = {}
    if work_order_id:
        query['work_order_id'] = work_order_id
    if status:
        query['status'] = status
    
    reqs = await db.rm_requisitions.find(query, {'_id': 0}).sort('created_at', -1).to_list(500)
    return [RMRequisition(**r) for r in reqs]


@router.put("/rm-requisitions/{req_id}/issue")
async def issue_rm_requisition(req_id: str, current_user: dict = Depends(get_current_user)):
    """Issue materials against requisition - deducts from inventory"""
    req = await db.rm_requisitions.find_one({'id': req_id}, {'_id': 0})
    if not req:
        raise HTTPException(status_code=404, detail="Requisition not found")
    
    if req['status'] not in ['draft', 'submitted']:
        raise HTTPException(status_code=400, detail="Requisition already processed")
    
    # Deduct stock for each item
    for item in req['items']:
        # Update stock balance
        await db.stock_balance.update_one(
            {'item_id': item['item_id'], 'warehouse_id': item['warehouse_id']},
            {'$inc': {'quantity': -item['required_qty'], 'available_qty': -item['required_qty']}}
        )
        
        # Create stock ledger entry
        await db.stock_ledger.insert_one({
            'id': str(uuid.uuid4()),
            'item_id': item['item_id'],
            'warehouse_id': item['warehouse_id'],
            'transaction_date': datetime.now(timezone.utc).isoformat(),
            'transaction_type': 'issue',
            'reference_type': 'RM_Requisition',
            'reference_id': req_id,
            'in_qty': 0,
            'out_qty': item['required_qty'],
            'unit_cost': 0,
            'batch_no': item.get('batch_no'),
            'notes': f"RM Issue for WO: {req.get('wo_number')}",
            'created_by': current_user['id']
        })
    
    # Update requisition status
    await db.rm_requisitions.update_one(
        {'id': req_id},
        {'$set': {
            'status': 'issued',
            'issued_at': datetime.now(timezone.utc).isoformat(),
            'issued_by': current_user['id']
        }}
    )
    
    return {'message': 'Materials issued successfully', 'requisition_id': req_id}


# ==================== COATING (STAGE 1) ENDPOINTS ====================
@router.post("/coating-batches", response_model=CoatingBatch)
async def create_coating_batch(data: CoatingBatchCreate, current_user: dict = Depends(get_current_user)):
    """Create a coating batch (Stage 1 production)"""
    batch_id = str(uuid.uuid4())
    batch_no = f"CB-{datetime.now(timezone.utc).strftime('%Y%m%d')}-{str(uuid.uuid4())[:6].upper()}"
    
    # Prepare input materials list
    input_materials = [
        {'type': 'Film', 'item_id': data.input_film_item_id, 'qty_kg': data.input_film_qty_kg, 'batch': data.input_film_batch},
        {'type': 'Adhesive', 'item_id': data.adhesive_item_id, 'qty_kg': data.adhesive_qty_kg, 'batch': data.adhesive_batch}
    ]
    if data.pigment_item_id:
        input_materials.append({'type': 'Pigment', 'item_id': data.pigment_item_id, 'qty_kg': data.pigment_qty_kg})
    if data.liner_item_id:
        input_materials.append({'type': 'Liner', 'item_id': data.liner_item_id, 'qty_sqm': data.liner_qty_sqm})
    
    target_specs = {
        'gsm': data.target_gsm,
        'width_mm': data.target_width_mm,
        'length_m': data.target_length_m
    }
    
    batch_doc = {
        'id': batch_id,
        'batch_no': batch_no,
        'work_order_id': data.work_order_id,
        'coating_type': data.coating_type,
        'machine_id': data.machine_id,
        'input_materials': input_materials,
        'target_specs': target_specs,
        'output_jumbo_qty_sqm': 0,
        'output_jumbo_qty_kg': 0,
        'scrap_qty_kg': 0,
        'scrap_percent': 0,
        'status': 'in_progress',
        'qc_status': 'pending',
        'operator_id': data.operator_id,
        'start_time': datetime.now(timezone.utc).isoformat(),
        'end_time': None,
        'notes': data.notes,
        'created_at': datetime.now(timezone.utc).isoformat(),
        'created_by': current_user['id']
    }
    
    await db.coating_batches.insert_one(batch_doc)
    return CoatingBatch(**{k: v for k, v in batch_doc.items() if k != '_id'})


@router.get("/coating-batches", response_model=List[CoatingBatch])
async def get_coating_batches(
    work_order_id: Optional[str] = None,
    status: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Get all coating batches"""
    query = {}
    if work_order_id:
        query['work_order_id'] = work_order_id
    if status:
        query['status'] = status
    
    batches = await db.coating_batches.find(query, {'_id': 0}).sort('created_at', -1).to_list(500)
    return [CoatingBatch(**b) for b in batches]


@router.put("/coating-batches/{batch_id}/complete")
async def complete_coating_batch(
    batch_id: str,
    output_sqm: float,
    scrap_kg: float,
    qc_status: str = "passed",
    current_user: dict = Depends(get_current_user)
):
    """
    Complete coating batch with output and scrap data
    Applies 7% Redline Guard
    """
    batch = await db.coating_batches.find_one({'id': batch_id}, {'_id': 0})
    if not batch:
        raise HTTPException(status_code=404, detail="Coating batch not found")
    
    # Calculate total input weight
    total_input_kg = sum(m.get('qty_kg', 0) for m in batch['input_materials'])
    
    # Calculate scrap percentage
    scrap_percent = (scrap_kg / total_input_kg * 100) if total_input_kg > 0 else 0
    
    # Calculate output weight from SQM
    gsm = batch['target_specs'].get('gsm', 50)
    output_kg = (output_sqm * gsm) / 1000
    
    # REDLINE GUARD: Check if scrap exceeds 7%
    if scrap_percent > SCRAP_REDLINE_PERCENT:
        # Create approval request
        await db.approval_requests.insert_one({
            'id': str(uuid.uuid4()),
            'module': 'Production',
            'entity_type': 'CoatingBatch',
            'entity_id': batch_id,
            'action': 'Complete with High Scrap',
            'condition': f'Scrap {scrap_percent:.2f}% exceeds {SCRAP_REDLINE_PERCENT}% limit',
            'status': 'pending',
            'approver_role': 'director',
            'requested_by': current_user['id'],
            'requested_at': datetime.now(timezone.utc).isoformat(),
            'payload': {
                'batch_id': batch_id,
                'scrap_percent': scrap_percent,
                'output_sqm': output_sqm,
                'scrap_kg': scrap_kg
            },
            'notes': f'Redline Guard triggered: Scrap {scrap_percent:.2f}%'
        })
        
        # Update batch status to on_hold
        await db.coating_batches.update_one(
            {'id': batch_id},
            {'$set': {
                'status': 'on_hold',
                'scrap_qty_kg': scrap_kg,
                'scrap_percent': scrap_percent,
                'output_jumbo_qty_sqm': output_sqm,
                'output_jumbo_qty_kg': output_kg
            }}
        )
        
        raise HTTPException(
            status_code=409,
            detail=f"REDLINE: Scrap {scrap_percent:.2f}% exceeds {SCRAP_REDLINE_PERCENT}% limit. Director approval required."
        )
    
    # Normal completion
    await db.coating_batches.update_one(
        {'id': batch_id},
        {'$set': {
            'status': 'completed',
            'qc_status': qc_status,
            'output_jumbo_qty_sqm': output_sqm,
            'output_jumbo_qty_kg': output_kg,
            'scrap_qty_kg': scrap_kg,
            'scrap_percent': scrap_percent,
            'end_time': datetime.now(timezone.utc).isoformat()
        }}
    )
    
    # Add jumbo to inventory as semi-finished goods
    # (In real implementation, create inventory entry for jumbo roll)
    
    return {
        'message': 'Coating batch completed',
        'batch_id': batch_id,
        'output_sqm': output_sqm,
        'output_kg': output_kg,
        'scrap_percent': round(scrap_percent, 2)
    }


# ==================== CONVERTING (STAGE 2) ENDPOINTS ====================
@router.post("/converting-jobs", response_model=ConvertingJob)
async def create_converting_job(data: ConvertingJobCreate, current_user: dict = Depends(get_current_user)):
    """Create a converting job (Stage 2 production)"""
    job_id = str(uuid.uuid4())
    job_no = f"CJ-{datetime.now(timezone.utc).strftime('%Y%m%d')}-{str(uuid.uuid4())[:6].upper()}"
    
    # Get coating batch to verify input
    coating_batch = await db.coating_batches.find_one({'id': data.coating_batch_id}, {'_id': 0})
    if not coating_batch:
        raise HTTPException(status_code=404, detail="Coating batch not found")
    
    if coating_batch['status'] != 'completed' or coating_batch.get('qc_status') != 'passed':
        raise HTTPException(status_code=400, detail="Coating batch not ready for converting")
    
    # Calculate expected output using jumbo-to-slits formula
    jumbo_specs = coating_batch['target_specs']
    slit_calc = calculate_jumbo_to_slits(
        jumbo_specs.get('width_mm', 0),
        data.input_jumbo_sqm / (jumbo_specs.get('width_mm', 1000) / 1000),  # Calculate length from sqm
        data.slit_width_mm,
        data.slit_length_m
    )
    
    input_specs = {
        'coating_batch': data.coating_batch_id,
        'jumbo_sqm': data.input_jumbo_sqm,
        'jumbo_width_mm': jumbo_specs.get('width_mm'),
        'jumbo_gsm': jumbo_specs.get('gsm')
    }
    
    output_specs = {
        'slit_width_mm': data.slit_width_mm,
        'slit_length_m': data.slit_length_m,
        'target_pcs': data.target_pcs,
        'theoretical_pcs': slit_calc['total_theoretical'],
        'effective_pcs': slit_calc['total_effective']
    }
    
    job_doc = {
        'id': job_id,
        'job_no': job_no,
        'work_order_id': data.work_order_id,
        'process_type': data.process_type,
        'coating_batch_id': data.coating_batch_id,
        'machine_id': data.machine_id,
        'input_specs': input_specs,
        'output_specs': output_specs,
        'actual_output_pcs': 0,
        'scrap_qty': 0,
        'scrap_percent': 0,
        'status': 'in_progress',
        'operator_id': data.operator_id,
        'start_time': datetime.now(timezone.utc).isoformat(),
        'end_time': None,
        'notes': data.notes,
        'created_at': datetime.now(timezone.utc).isoformat(),
        'created_by': current_user['id']
    }
    
    await db.converting_jobs.insert_one(job_doc)
    return ConvertingJob(**{k: v for k, v in job_doc.items() if k != '_id'})


@router.get("/converting-jobs", response_model=List[ConvertingJob])
async def get_converting_jobs(
    work_order_id: Optional[str] = None,
    status: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Get all converting jobs"""
    query = {}
    if work_order_id:
        query['work_order_id'] = work_order_id
    if status:
        query['status'] = status
    
    jobs = await db.converting_jobs.find(query, {'_id': 0}).sort('created_at', -1).to_list(500)
    return [ConvertingJob(**j) for j in jobs]


@router.put("/converting-jobs/{job_id}/complete")
async def complete_converting_job(
    job_id: str,
    actual_pcs: int,
    scrap_pcs: int = 0,
    current_user: dict = Depends(get_current_user)
):
    """Complete converting job with output"""
    job = await db.converting_jobs.find_one({'id': job_id}, {'_id': 0})
    if not job:
        raise HTTPException(status_code=404, detail="Converting job not found")
    
    target_pcs = job['output_specs'].get('target_pcs', 1)
    scrap_percent = (scrap_pcs / (actual_pcs + scrap_pcs) * 100) if (actual_pcs + scrap_pcs) > 0 else 0
    
    await db.converting_jobs.update_one(
        {'id': job_id},
        {'$set': {
            'status': 'completed',
            'actual_output_pcs': actual_pcs,
            'scrap_qty': scrap_pcs,
            'scrap_percent': scrap_percent,
            'end_time': datetime.now(timezone.utc).isoformat()
        }}
    )
    
    # Update work order quantity made
    wo = await db.work_orders.find_one({'id': job['work_order_id']}, {'_id': 0})
    if wo:
        new_qty = wo.get('quantity_made', 0) + actual_pcs
        await db.work_orders.update_one(
            {'id': job['work_order_id']},
            {'$set': {'quantity_made': new_qty}}
        )
    
    # Add finished goods to inventory
    # (Implementation depends on item master configuration)
    
    return {
        'message': 'Converting job completed',
        'job_id': job_id,
        'actual_pcs': actual_pcs,
        'scrap_percent': round(scrap_percent, 2)
    }


# ==================== PRODUCTION SUMMARY ====================
@router.get("/summary/{work_order_id}")
async def get_production_summary(work_order_id: str, current_user: dict = Depends(get_current_user)):
    """Get complete production summary for a work order"""
    wo = await db.work_orders.find_one({'id': work_order_id}, {'_id': 0})
    if not wo:
        raise HTTPException(status_code=404, detail="Work order not found")
    
    # Get requisitions
    requisitions = await db.rm_requisitions.find(
        {'work_order_id': work_order_id}, {'_id': 0}
    ).to_list(50)
    
    # Get coating batches
    coating_batches = await db.coating_batches.find(
        {'work_order_id': work_order_id}, {'_id': 0}
    ).to_list(50)
    
    # Get converting jobs
    converting_jobs = await db.converting_jobs.find(
        {'work_order_id': work_order_id}, {'_id': 0}
    ).to_list(50)
    
    # Calculate totals
    total_output_sqm = sum(b.get('output_jumbo_qty_sqm', 0) for b in coating_batches)
    total_output_pcs = sum(j.get('actual_output_pcs', 0) for j in converting_jobs)
    total_scrap_kg = sum(b.get('scrap_qty_kg', 0) for b in coating_batches)
    
    return {
        'work_order': wo,
        'rm_requisitions': requisitions,
        'coating_batches': coating_batches,
        'converting_jobs': converting_jobs,
        'totals': {
            'output_sqm': total_output_sqm,
            'output_pcs': total_output_pcs,
            'scrap_kg': total_scrap_kg,
            'target_qty': wo.get('quantity_to_make', 0),
            'completed_qty': wo.get('quantity_made', 0),
            'completion_percent': round((wo.get('quantity_made', 0) / wo.get('quantity_to_make', 1)) * 100, 1)
        }
    }
