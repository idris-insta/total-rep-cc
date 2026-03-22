"""
Gatepass System Module
Handles:
- Inward Gatepass (linked to GRN)
- Outward Gatepass (linked to Delivery Note)
- Vehicle & Transporter tracking
- Stock movement logging
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, timezone
import uuid
from server import db, get_current_user
from utils.document_numbering import generate_document_number

router = APIRouter()


# ==================== TRANSPORTER MODELS ====================
class TransporterCreate(BaseModel):
    transporter_name: str
    contact_person: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    gstin: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    is_active: bool = True


class Transporter(BaseModel):
    id: str
    transporter_code: str
    transporter_name: str
    contact_person: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    gstin: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    is_active: bool
    created_at: str


# ==================== GATEPASS MODELS ====================
class GatepassItemCreate(BaseModel):
    item_id: str
    item_name: str
    quantity: float
    uom: str
    batch_no: Optional[str] = None
    remarks: Optional[str] = None


class GatepassCreate(BaseModel):
    gatepass_type: str  # inward, outward
    reference_type: str  # GRN, DeliveryNote, StockTransfer, Returnable, NonReturnable
    reference_id: Optional[str] = None
    transporter_id: Optional[str] = None
    vehicle_no: str
    driver_name: Optional[str] = None
    driver_phone: Optional[str] = None
    lr_no: Optional[str] = None  # Lorry Receipt Number
    lr_date: Optional[str] = None
    party_name: Optional[str] = None
    party_address: Optional[str] = None
    branch_id: Optional[str] = None
    warehouse_id: str
    items: List[GatepassItemCreate]
    purpose: Optional[str] = None
    expected_return_date: Optional[str] = None  # For returnable items
    remarks: Optional[str] = None


class Gatepass(BaseModel):
    id: str
    gatepass_no: str
    gatepass_type: str
    reference_type: str
    reference_id: Optional[str] = None
    transporter_id: Optional[str] = None
    transporter_name: Optional[str] = None
    vehicle_no: str
    driver_name: Optional[str] = None
    driver_phone: Optional[str] = None
    lr_no: Optional[str] = None
    lr_date: Optional[str] = None
    party_name: Optional[str] = None
    party_address: Optional[str] = None
    branch_id: Optional[str] = None
    warehouse_id: str
    items: List[dict]
    total_qty: float
    purpose: Optional[str] = None
    expected_return_date: Optional[str] = None
    actual_return_date: Optional[str] = None
    remarks: Optional[str] = None
    status: str  # draft, approved, in_transit, completed, returned
    in_time: Optional[str] = None
    out_time: Optional[str] = None
    created_at: str
    created_by: str
    approved_by: Optional[str] = None
    approved_at: Optional[str] = None


# ==================== TRANSPORTER ENDPOINTS ====================
@router.post("/transporters", response_model=Transporter)
async def create_transporter(data: TransporterCreate, current_user: dict = Depends(get_current_user)):
    """Create a new transporter"""
    trans_id = str(uuid.uuid4())
    
    # Generate transporter code
    count = await db.transporters.count_documents({}) + 1
    trans_code = f"TR-{str(count).zfill(4)}"
    
    trans_doc = {
        'id': trans_id,
        'transporter_code': trans_code,
        **data.model_dump(),
        'created_at': datetime.now(timezone.utc).isoformat(),
        'created_by': current_user['id']
    }
    
    await db.transporters.insert_one(trans_doc)
    return Transporter(**{k: v for k, v in trans_doc.items() if k != '_id'})


@router.get("/transporters", response_model=List[Transporter])
async def get_transporters(
    is_active: Optional[bool] = None,
    current_user: dict = Depends(get_current_user)
):
    """Get all transporters"""
    query = {}
    if is_active is not None:
        query['is_active'] = is_active
    
    transporters = await db.transporters.find(query, {'_id': 0}).sort('transporter_name', 1).to_list(500)
    return [Transporter(**t) for t in transporters]


# ==================== GATEPASS ENDPOINTS ====================
@router.post("/", response_model=Gatepass)
async def create_gatepass(data: GatepassCreate, current_user: dict = Depends(get_current_user)):
    """
    Create a new gatepass (inward or outward)
    - Inward: Stock will be added on GRN approval
    - Outward: Stock will be deducted on Delivery Note
    """
    gp_id = str(uuid.uuid4())
    
    # Generate gatepass number
    branch_code = 'HO'
    if data.branch_id:
        branch = await db.branches.find_one({'id': data.branch_id}, {'_id': 0})
        branch_code = branch.get('branch_code', 'HO') if branch else 'HO'
    
    doc_type = 'gatepass_in' if data.gatepass_type == 'inward' else 'gatepass_out'
    gp_number = await generate_document_number(db, doc_type, branch_code)
    
    # Get transporter name if provided
    transporter_name = None
    if data.transporter_id:
        transporter = await db.transporters.find_one({'id': data.transporter_id}, {'_id': 0})
        transporter_name = transporter.get('transporter_name') if transporter else None
    
    # Calculate total quantity
    total_qty = sum(item.quantity for item in data.items)
    
    gp_doc = {
        'id': gp_id,
        'gatepass_no': gp_number,
        **data.model_dump(),
        'items': [item.model_dump() for item in data.items],
        'transporter_name': transporter_name,
        'total_qty': total_qty,
        'status': 'draft',
        'in_time': datetime.now(timezone.utc).isoformat() if data.gatepass_type == 'inward' else None,
        'out_time': datetime.now(timezone.utc).isoformat() if data.gatepass_type == 'outward' else None,
        'actual_return_date': None,
        'created_at': datetime.now(timezone.utc).isoformat(),
        'created_by': current_user['id'],
        'approved_by': None,
        'approved_at': None
    }
    
    await db.gatepasses.insert_one(gp_doc)
    return Gatepass(**{k: v for k, v in gp_doc.items() if k != '_id'})


@router.get("/", response_model=List[Gatepass])
async def get_gatepasses(
    gatepass_type: Optional[str] = None,
    status: Optional[str] = None,
    warehouse_id: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Get all gatepasses with filters"""
    query = {}
    
    if gatepass_type:
        query['gatepass_type'] = gatepass_type
    if status:
        query['status'] = status
    if warehouse_id:
        query['warehouse_id'] = warehouse_id
    if date_from:
        query['created_at'] = {'$gte': date_from}
    if date_to:
        if 'created_at' in query:
            query['created_at']['$lte'] = date_to
        else:
            query['created_at'] = {'$lte': date_to}
    
    gatepasses = await db.gatepasses.find(query, {'_id': 0}).sort('created_at', -1).to_list(500)
    return [Gatepass(**gp) for gp in gatepasses]


@router.get("/{gatepass_id}", response_model=Gatepass)
async def get_gatepass(gatepass_id: str, current_user: dict = Depends(get_current_user)):
    """Get gatepass by ID"""
    gp = await db.gatepasses.find_one({'id': gatepass_id}, {'_id': 0})
    if not gp:
        raise HTTPException(status_code=404, detail="Gatepass not found")
    return Gatepass(**gp)


@router.put("/{gatepass_id}/approve")
async def approve_gatepass(gatepass_id: str, current_user: dict = Depends(get_current_user)):
    """Approve gatepass - triggers stock movement"""
    gp = await db.gatepasses.find_one({'id': gatepass_id}, {'_id': 0})
    if not gp:
        raise HTTPException(status_code=404, detail="Gatepass not found")
    
    if gp['status'] != 'draft':
        raise HTTPException(status_code=400, detail="Gatepass is not in draft status")
    
    # Update status
    await db.gatepasses.update_one(
        {'id': gatepass_id},
        {'$set': {
            'status': 'approved',
            'approved_by': current_user['id'],
            'approved_at': datetime.now(timezone.utc).isoformat()
        }}
    )
    
    return {'message': 'Gatepass approved', 'gatepass_id': gatepass_id}


@router.put("/{gatepass_id}/complete")
async def complete_gatepass(gatepass_id: str, current_user: dict = Depends(get_current_user)):
    """Mark gatepass as completed"""
    gp = await db.gatepasses.find_one({'id': gatepass_id}, {'_id': 0})
    if not gp:
        raise HTTPException(status_code=404, detail="Gatepass not found")
    
    update_data = {
        'status': 'completed',
        'updated_at': datetime.now(timezone.utc).isoformat()
    }
    
    # Set in/out time based on type
    if gp['gatepass_type'] == 'inward' and not gp.get('in_time'):
        update_data['in_time'] = datetime.now(timezone.utc).isoformat()
    elif gp['gatepass_type'] == 'outward' and not gp.get('out_time'):
        update_data['out_time'] = datetime.now(timezone.utc).isoformat()
    
    await db.gatepasses.update_one({'id': gatepass_id}, {'$set': update_data})
    
    return {'message': 'Gatepass completed', 'gatepass_id': gatepass_id}


@router.put("/{gatepass_id}/return")
async def mark_gatepass_returned(gatepass_id: str, current_user: dict = Depends(get_current_user)):
    """Mark returnable gatepass as returned"""
    gp = await db.gatepasses.find_one({'id': gatepass_id}, {'_id': 0})
    if not gp:
        raise HTTPException(status_code=404, detail="Gatepass not found")
    
    if gp['reference_type'] != 'Returnable':
        raise HTTPException(status_code=400, detail="Gatepass is not returnable type")
    
    await db.gatepasses.update_one(
        {'id': gatepass_id},
        {'$set': {
            'status': 'returned',
            'actual_return_date': datetime.now(timezone.utc).isoformat()
        }}
    )
    
    return {'message': 'Gatepass marked as returned', 'gatepass_id': gatepass_id}


# ==================== VEHICLE LOG ====================
@router.get("/vehicle-log")
async def get_vehicle_log(
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    vehicle_no: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Get vehicle movement log from gatepasses"""
    query = {}
    
    if vehicle_no:
        query['vehicle_no'] = {'$regex': vehicle_no, '$options': 'i'}
    if date_from:
        query['created_at'] = {'$gte': date_from}
    if date_to:
        if 'created_at' in query:
            query['created_at']['$lte'] = date_to
        else:
            query['created_at'] = {'$lte': date_to}
    
    gatepasses = await db.gatepasses.find(
        query,
        {
            '_id': 0,
            'gatepass_no': 1,
            'gatepass_type': 1,
            'vehicle_no': 1,
            'driver_name': 1,
            'transporter_name': 1,
            'party_name': 1,
            'in_time': 1,
            'out_time': 1,
            'status': 1,
            'created_at': 1
        }
    ).sort('created_at', -1).to_list(500)
    
    return gatepasses
