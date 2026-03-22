from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, timezone
import uuid
from server import db, get_current_user

router = APIRouter()

class QCInspectionCreate(BaseModel):
    inspection_type: str
    reference_type: str
    reference_id: str
    item_id: str
    batch_number: Optional[str] = None
    test_parameters: List[dict]
    inspector: str
    notes: Optional[str] = None

class QCInspection(BaseModel):
    id: str
    inspection_number: str
    inspection_type: str
    reference_type: str
    reference_id: str
    item_id: str
    batch_number: Optional[str] = None
    test_parameters: List[dict]
    result: str
    inspector: str
    notes: Optional[str] = None
    created_at: str

class CustomerComplaintCreate(BaseModel):
    account_id: str
    invoice_id: Optional[str] = None
    batch_number: Optional[str] = None
    complaint_type: str
    description: str
    severity: str

class CustomerComplaint(BaseModel):
    id: str
    complaint_number: str
    account_id: str
    invoice_id: Optional[str] = None
    batch_number: Optional[str] = None
    complaint_type: str
    description: str
    severity: str
    status: str
    resolution: Optional[str] = None
    created_at: str
    resolved_at: Optional[str] = None

class TDSCreate(BaseModel):
    item_id: str
    document_type: str
    document_url: str
    version: str
    notes: Optional[str] = None

class TDS(BaseModel):
    id: str
    item_id: str
    document_type: str
    document_url: str
    version: str
    notes: Optional[str] = None
    created_at: str


@router.post("/inspections", response_model=QCInspection)
async def create_qc_inspection(inspection_data: QCInspectionCreate, current_user: dict = Depends(get_current_user)):
    inspection_id = str(uuid.uuid4())
    inspection_number = f"QC-{datetime.now(timezone.utc).strftime('%Y%m%d')}-{str(uuid.uuid4())[:6].upper()}"
    
    passed_tests = sum(1 for test in inspection_data.test_parameters if test.get('result') == 'pass')
    total_tests = len(inspection_data.test_parameters)
    result = 'pass' if passed_tests == total_tests else 'fail'
    
    inspection_doc = {
        'id': inspection_id,
        'inspection_number': inspection_number,
        **inspection_data.model_dump(),
        'result': result,
        'passed_tests': passed_tests,
        'total_tests': total_tests,
        'created_at': datetime.now(timezone.utc).isoformat(),
        'created_by': current_user['id']
    }
    
    await db.qc_inspections.insert_one(inspection_doc)
    return QCInspection(**{k: v for k, v in inspection_doc.items() if k != '_id' and k not in ['passed_tests', 'total_tests', 'created_by']})

@router.get("/inspections", response_model=List[QCInspection])
async def get_qc_inspections(inspection_type: Optional[str] = None, result: Optional[str] = None, current_user: dict = Depends(get_current_user)):
    query = {}
    if inspection_type:
        query['inspection_type'] = inspection_type
    if result:
        query['result'] = result
    
    inspections = await db.qc_inspections.find(query, {'_id': 0, 'passed_tests': 0, 'total_tests': 0, 'created_by': 0}).sort('created_at', -1).to_list(1000)
    return [QCInspection(**inspection) for inspection in inspections]

@router.get("/inspections/{inspection_id}", response_model=QCInspection)
async def get_qc_inspection(inspection_id: str, current_user: dict = Depends(get_current_user)):
    inspection = await db.qc_inspections.find_one({'id': inspection_id}, {'_id': 0, 'passed_tests': 0, 'total_tests': 0, 'created_by': 0})
    if not inspection:
        raise HTTPException(status_code=404, detail="Inspection not found")
    return QCInspection(**inspection)


@router.post("/complaints", response_model=CustomerComplaint)
async def create_complaint(complaint_data: CustomerComplaintCreate, current_user: dict = Depends(get_current_user)):
    complaint_id = str(uuid.uuid4())
    complaint_number = f"CMPL-{datetime.now(timezone.utc).strftime('%Y%m%d')}-{str(uuid.uuid4())[:6].upper()}"
    
    complaint_doc = {
        'id': complaint_id,
        'complaint_number': complaint_number,
        **complaint_data.model_dump(),
        'status': 'open',
        'created_at': datetime.now(timezone.utc).isoformat(),
        'created_by': current_user['id']
    }
    
    await db.customer_complaints.insert_one(complaint_doc)
    return CustomerComplaint(**{k: v for k, v in complaint_doc.items() if k != '_id' and k != 'created_by'})

@router.get("/complaints", response_model=List[CustomerComplaint])
async def get_complaints(status: Optional[str] = None, severity: Optional[str] = None, current_user: dict = Depends(get_current_user)):
    query = {}
    if status:
        query['status'] = status
    if severity:
        query['severity'] = severity
    
    complaints = await db.customer_complaints.find(query, {'_id': 0, 'created_by': 0}).sort('created_at', -1).to_list(1000)
    return [CustomerComplaint(**complaint) for complaint in complaints]

@router.put("/complaints/{complaint_id}/resolve")
async def resolve_complaint(complaint_id: str, resolution: str, current_user: dict = Depends(get_current_user)):
    result = await db.customer_complaints.update_one(
        {'id': complaint_id},
        {'$set': {
            'status': 'resolved',
            'resolution': resolution,
            'resolved_at': datetime.now(timezone.utc).isoformat(),
            'resolved_by': current_user['id']
        }}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Complaint not found")
    
    return {'message': 'Complaint resolved'}


@router.post("/tds", response_model=TDS)
async def create_tds(tds_data: TDSCreate, current_user: dict = Depends(get_current_user)):
    tds_id = str(uuid.uuid4())
    
    tds_doc = {
        'id': tds_id,
        **tds_data.model_dump(),
        'created_at': datetime.now(timezone.utc).isoformat(),
        'created_by': current_user['id']
    }
    
    await db.tds_documents.insert_one(tds_doc)
    return TDS(**{k: v for k, v in tds_doc.items() if k != '_id' and k != 'created_by'})

@router.get("/tds", response_model=List[TDS])
async def get_tds(item_id: Optional[str] = None, current_user: dict = Depends(get_current_user)):
    query = {}
    if item_id:
        query['item_id'] = item_id
    
    tds_docs = await db.tds_documents.find(query, {'_id': 0, 'created_by': 0}).sort('created_at', -1).to_list(1000)
    return [TDS(**tds) for tds in tds_docs]


@router.get("/reports/quality-summary")
async def get_quality_summary(current_user: dict = Depends(get_current_user)):
    inspections = await db.qc_inspections.find({}, {'_id': 0}).to_list(10000)
    
    total_inspections = len(inspections)
    passed = sum(1 for insp in inspections if insp['result'] == 'pass')
    failed = total_inspections - passed
    pass_rate = (passed / total_inspections * 100) if total_inspections > 0 else 0
    
    by_type = {}
    for insp in inspections:
        insp_type = insp['inspection_type']
        if insp_type not in by_type:
            by_type[insp_type] = {'total': 0, 'passed': 0, 'failed': 0}
        by_type[insp_type]['total'] += 1
        if insp['result'] == 'pass':
            by_type[insp_type]['passed'] += 1
        else:
            by_type[insp_type]['failed'] += 1
    
    complaints = await db.customer_complaints.find({}, {'_id': 0}).to_list(10000)
    open_complaints = sum(1 for c in complaints if c['status'] == 'open')
    resolved_complaints = sum(1 for c in complaints if c['status'] == 'resolved')
    
    return {
        'inspections': {
            'total': total_inspections,
            'passed': passed,
            'failed': failed,
            'pass_rate': round(pass_rate, 2),
            'by_type': by_type
        },
        'complaints': {
            'total': len(complaints),
            'open': open_complaints,
            'resolved': resolved_complaints
        }
    }

@router.get("/batch-trace/{batch_number}")
async def trace_batch(batch_number: str, current_user: dict = Depends(get_current_user)):
    production_entry = await db.production_entries.find_one({'batch_number': batch_number}, {'_id': 0})
    if not production_entry:
        raise HTTPException(status_code=404, detail="Batch not found")
    
    wo = await db.work_orders.find_one({'id': production_entry['wo_id']}, {'_id': 0})
    
    qc_inspections = await db.qc_inspections.find({'batch_number': batch_number}, {'_id': 0}).to_list(100)
    
    complaints = await db.customer_complaints.find({'batch_number': batch_number}, {'_id': 0}).to_list(100)
    
    return {
        'batch_number': batch_number,
        'production': production_entry,
        'work_order': wo,
        'qc_inspections': qc_inspections,
        'complaints': complaints
    }