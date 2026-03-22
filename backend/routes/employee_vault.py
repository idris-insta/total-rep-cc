"""
Employee Document Vault Module
Secure storage for employee documents:
- Aadhaar Card
- PAN Card
- Passport
- Driving License
- Educational Certificates
- Experience Letters
- Bank Documents
- Bio-data/Resume

Also handles:
- Asset Assignment tracking
- Document expiry alerts
"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, timezone
import uuid
import os
from server import db, get_current_user

router = APIRouter()

UPLOAD_DIR = "/app/backend/uploads/employee_docs"
os.makedirs(UPLOAD_DIR, exist_ok=True)


# ==================== DOCUMENT TYPES ====================
DOCUMENT_TYPES = [
    'aadhaar',
    'pan',
    'passport',
    'driving_license',
    'voter_id',
    'educational_certificate',
    'experience_letter',
    'offer_letter',
    'appointment_letter',
    'bank_statement',
    'cancelled_cheque',
    'address_proof',
    'photo',
    'resume',
    'bio_data',
    'medical_certificate',
    'police_verification',
    'other'
]


# ==================== EMPLOYEE DOCUMENT MODELS ====================
class EmployeeDocumentCreate(BaseModel):
    employee_id: str
    document_type: str
    document_number: Optional[str] = None
    issue_date: Optional[str] = None
    expiry_date: Optional[str] = None
    issuing_authority: Optional[str] = None
    notes: Optional[str] = None


class EmployeeDocument(BaseModel):
    id: str
    employee_id: str
    document_type: str
    document_number: Optional[str] = None
    file_name: Optional[str] = None
    file_path: Optional[str] = None
    file_size: int = 0
    mime_type: Optional[str] = None
    issue_date: Optional[str] = None
    expiry_date: Optional[str] = None
    issuing_authority: Optional[str] = None
    is_verified: bool = False
    verified_by: Optional[str] = None
    verified_at: Optional[str] = None
    notes: Optional[str] = None
    created_at: str
    created_by: str


# ==================== ASSET ASSIGNMENT MODELS ====================
class AssetAssignmentCreate(BaseModel):
    employee_id: str
    asset_type: str  # laptop, mobile, vehicle, id_card, key, uniform, etc.
    asset_code: str
    asset_name: str
    serial_number: Optional[str] = None
    assigned_date: str
    condition_at_assignment: str = "good"  # new, good, fair, damaged
    value: float = 0
    notes: Optional[str] = None


class AssetAssignment(BaseModel):
    id: str
    employee_id: str
    employee_name: Optional[str] = None
    asset_type: str
    asset_code: str
    asset_name: str
    serial_number: Optional[str] = None
    assigned_date: str
    returned_date: Optional[str] = None
    condition_at_assignment: str
    condition_at_return: Optional[str] = None
    value: float
    status: str  # assigned, returned, lost, damaged
    notes: Optional[str] = None
    created_at: str
    created_by: str


# ==================== DOCUMENT ENDPOINTS ====================
@router.get("/document-types")
async def get_document_types():
    """Get list of allowed document types"""
    return {'document_types': DOCUMENT_TYPES}


@router.post("/documents", response_model=EmployeeDocument)
async def create_employee_document(
    employee_id: str = Form(...),
    document_type: str = Form(...),
    document_number: Optional[str] = Form(None),
    issue_date: Optional[str] = Form(None),
    expiry_date: Optional[str] = Form(None),
    issuing_authority: Optional[str] = Form(None),
    notes: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None),
    current_user: dict = Depends(get_current_user)
):
    """Upload and create employee document record"""
    # Verify employee exists
    employee = await db.employees.find_one({'id': employee_id}, {'_id': 0})
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    if document_type not in DOCUMENT_TYPES:
        raise HTTPException(status_code=400, detail=f"Invalid document type. Must be one of: {DOCUMENT_TYPES}")
    
    doc_id = str(uuid.uuid4())
    file_name = None
    file_path = None
    file_size = 0
    mime_type = None
    
    # Handle file upload
    if file:
        # Create employee folder
        emp_folder = os.path.join(UPLOAD_DIR, employee_id)
        os.makedirs(emp_folder, exist_ok=True)
        
        # Generate unique filename
        ext = os.path.splitext(file.filename)[1]
        file_name = f"{document_type}_{doc_id[:8]}{ext}"
        file_path = os.path.join(emp_folder, file_name)
        
        # Save file
        contents = await file.read()
        with open(file_path, 'wb') as f:
            f.write(contents)
        
        file_size = len(contents)
        mime_type = file.content_type
    
    doc_record = {
        'id': doc_id,
        'employee_id': employee_id,
        'document_type': document_type,
        'document_number': document_number,
        'file_name': file_name,
        'file_path': file_path,
        'file_size': file_size,
        'mime_type': mime_type,
        'issue_date': issue_date,
        'expiry_date': expiry_date,
        'issuing_authority': issuing_authority,
        'is_verified': False,
        'verified_by': None,
        'verified_at': None,
        'notes': notes,
        'created_at': datetime.now(timezone.utc).isoformat(),
        'created_by': current_user['id']
    }
    
    await db.employee_documents.insert_one(doc_record)
    return EmployeeDocument(**{k: v for k, v in doc_record.items() if k != '_id'})


@router.get("/documents", response_model=List[EmployeeDocument])
async def get_employee_documents(
    employee_id: str,
    document_type: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Get all documents for an employee"""
    query = {'employee_id': employee_id}
    if document_type:
        query['document_type'] = document_type
    
    docs = await db.employee_documents.find(query, {'_id': 0}).sort('created_at', -1).to_list(100)
    return [EmployeeDocument(**d) for d in docs]


@router.put("/documents/{doc_id}/verify")
async def verify_document(doc_id: str, current_user: dict = Depends(get_current_user)):
    """Mark document as verified"""
    if current_user['role'] not in ['admin', 'hr']:
        raise HTTPException(status_code=403, detail="Access denied")
    
    result = await db.employee_documents.update_one(
        {'id': doc_id},
        {'$set': {
            'is_verified': True,
            'verified_by': current_user['id'],
            'verified_at': datetime.now(timezone.utc).isoformat()
        }}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Document not found")
    
    return {'message': 'Document verified', 'doc_id': doc_id}


@router.delete("/documents/{doc_id}")
async def delete_document(doc_id: str, current_user: dict = Depends(get_current_user)):
    """Delete employee document"""
    if current_user['role'] not in ['admin', 'hr']:
        raise HTTPException(status_code=403, detail="Access denied")
    
    doc = await db.employee_documents.find_one({'id': doc_id}, {'_id': 0})
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # Delete file if exists
    if doc.get('file_path') and os.path.exists(doc['file_path']):
        os.remove(doc['file_path'])
    
    await db.employee_documents.delete_one({'id': doc_id})
    
    return {'message': 'Document deleted', 'doc_id': doc_id}


@router.get("/documents/expiring")
async def get_expiring_documents(
    days: int = 30,
    current_user: dict = Depends(get_current_user)
):
    """Get documents expiring within specified days"""
    from datetime import timedelta
    
    cutoff_date = (datetime.now(timezone.utc) + timedelta(days=days)).isoformat()[:10]
    today = datetime.now(timezone.utc).isoformat()[:10]
    
    docs = await db.employee_documents.find({
        'expiry_date': {'$gte': today, '$lte': cutoff_date}
    }, {'_id': 0}).to_list(100)
    
    # Enrich with employee names
    for doc in docs:
        emp = await db.employees.find_one({'id': doc['employee_id']}, {'_id': 0, 'name': 1})
        doc['employee_name'] = emp.get('name') if emp else None
    
    return docs


# ==================== ASSET ASSIGNMENT ENDPOINTS ====================
@router.post("/assets", response_model=AssetAssignment)
async def assign_asset(data: AssetAssignmentCreate, current_user: dict = Depends(get_current_user)):
    """Assign asset to employee"""
    # Verify employee exists
    employee = await db.employees.find_one({'id': data.employee_id}, {'_id': 0})
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    # Check if asset code is already assigned
    existing = await db.asset_assignments.find_one({
        'asset_code': data.asset_code,
        'status': 'assigned'
    }, {'_id': 0})
    
    if existing:
        raise HTTPException(status_code=400, detail="Asset is already assigned to another employee")
    
    asset_id = str(uuid.uuid4())
    
    asset_doc = {
        'id': asset_id,
        **data.model_dump(),
        'employee_name': employee.get('name'),
        'returned_date': None,
        'condition_at_return': None,
        'status': 'assigned',
        'created_at': datetime.now(timezone.utc).isoformat(),
        'created_by': current_user['id']
    }
    
    await db.asset_assignments.insert_one(asset_doc)
    return AssetAssignment(**{k: v for k, v in asset_doc.items() if k != '_id'})


@router.get("/assets", response_model=List[AssetAssignment])
async def get_asset_assignments(
    employee_id: Optional[str] = None,
    status: Optional[str] = None,
    asset_type: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Get asset assignments"""
    query = {}
    if employee_id:
        query['employee_id'] = employee_id
    if status:
        query['status'] = status
    if asset_type:
        query['asset_type'] = asset_type
    
    assets = await db.asset_assignments.find(query, {'_id': 0}).sort('assigned_date', -1).to_list(500)
    return [AssetAssignment(**a) for a in assets]


@router.put("/assets/{asset_id}/return")
async def return_asset(
    asset_id: str,
    condition: str = "good",
    notes: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Mark asset as returned"""
    asset = await db.asset_assignments.find_one({'id': asset_id}, {'_id': 0})
    if not asset:
        raise HTTPException(status_code=404, detail="Asset assignment not found")
    
    if asset['status'] != 'assigned':
        raise HTTPException(status_code=400, detail="Asset is not currently assigned")
    
    await db.asset_assignments.update_one(
        {'id': asset_id},
        {'$set': {
            'status': 'returned',
            'returned_date': datetime.now(timezone.utc).isoformat()[:10],
            'condition_at_return': condition,
            'notes': notes or asset.get('notes')
        }}
    )
    
    return {'message': 'Asset returned', 'asset_id': asset_id}


@router.put("/assets/{asset_id}/report-lost")
async def report_asset_lost(asset_id: str, notes: str, current_user: dict = Depends(get_current_user)):
    """Report asset as lost"""
    asset = await db.asset_assignments.find_one({'id': asset_id}, {'_id': 0})
    if not asset:
        raise HTTPException(status_code=404, detail="Asset assignment not found")
    
    await db.asset_assignments.update_one(
        {'id': asset_id},
        {'$set': {
            'status': 'lost',
            'notes': notes
        }}
    )
    
    return {'message': 'Asset reported as lost', 'asset_id': asset_id}


# ==================== EMPLOYEE VAULT SUMMARY ====================
@router.get("/{employee_id}/vault-summary")
async def get_employee_vault_summary(employee_id: str, current_user: dict = Depends(get_current_user)):
    """Get complete vault summary for an employee"""
    employee = await db.employees.find_one({'id': employee_id}, {'_id': 0})
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    # Get all documents
    documents = await db.employee_documents.find(
        {'employee_id': employee_id},
        {'_id': 0}
    ).to_list(50)
    
    # Get all assets
    assets = await db.asset_assignments.find(
        {'employee_id': employee_id, 'status': 'assigned'},
        {'_id': 0}
    ).to_list(50)
    
    # Document checklist
    doc_types_uploaded = set(d['document_type'] for d in documents)
    required_docs = ['aadhaar', 'pan', 'photo', 'address_proof', 'bank_statement']
    
    checklist = []
    for doc_type in required_docs:
        checklist.append({
            'document_type': doc_type,
            'uploaded': doc_type in doc_types_uploaded,
            'verified': any(d['is_verified'] for d in documents if d['document_type'] == doc_type)
        })
    
    # Calculate total asset value
    total_asset_value = sum(a.get('value', 0) for a in assets)
    
    return {
        'employee': {
            'id': employee['id'],
            'name': employee.get('name'),
            'employee_code': employee.get('employee_code')
        },
        'documents': {
            'total': len(documents),
            'verified': sum(1 for d in documents if d.get('is_verified')),
            'checklist': checklist,
            'list': documents
        },
        'assets': {
            'total': len(assets),
            'total_value': total_asset_value,
            'list': assets
        }
    }
