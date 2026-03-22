from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
import uuid

from server import db, get_current_user

router = APIRouter()


class ApprovalRequestCreate(BaseModel):
    module: str
    entity_type: str
    entity_id: str
    action: str
    condition: Optional[str] = None
    approver_role: str
    payload: Optional[Dict[str, Any]] = None
    notes: Optional[str] = None


class ApprovalRequest(BaseModel):
    id: str
    module: str
    entity_type: str
    entity_id: str
    action: str
    condition: Optional[str] = None
    status: str  # pending, approved, rejected
    approver_role: str
    requested_by: str
    requested_at: str
    decided_by: Optional[str] = None
    decided_at: Optional[str] = None
    payload: Optional[Dict[str, Any]] = None
    notes: Optional[str] = None


@router.post("/requests", response_model=ApprovalRequest)
async def create_approval_request(req: ApprovalRequestCreate, current_user: dict = Depends(get_current_user)):
    req_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()

    doc = {
        "id": req_id,
        **req.model_dump(),
        "status": "pending",
        "requested_by": current_user["id"],
        "requested_at": now,
        "decided_by": None,
        "decided_at": None,
    }
    await db.approval_requests.insert_one(doc)
    return ApprovalRequest(**{k: v for k, v in doc.items() if k != "_id"})


@router.get("/requests", response_model=List[ApprovalRequest])
async def list_approval_requests(
    status: Optional[str] = None,
    module: Optional[str] = None,
    approver_role: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
):
    query: Dict[str, Any] = {}
    if status:
        query["status"] = status
    if module:
        query["module"] = module
    if approver_role:
        query["approver_role"] = approver_role

    # Basic visibility: admin sees all; others only requests matching their role
    if current_user.get("role") != "admin":
        query["approver_role"] = current_user.get("role")

    reqs = await db.approval_requests.find(query, {"_id": 0}).sort("requested_at", -1).to_list(1000)
    return [ApprovalRequest(**r) for r in reqs]


@router.put("/requests/{request_id}/approve")
async def approve_request(request_id: str, notes: Optional[str] = None, current_user: dict = Depends(get_current_user)):
    req = await db.approval_requests.find_one({"id": request_id}, {"_id": 0})
    if not req:
        raise HTTPException(status_code=404, detail="Approval request not found")

    if current_user.get("role") not in ["admin", req.get("approver_role")]:
        raise HTTPException(status_code=403, detail="Not allowed to approve")

    if req.get("status") != "pending":
        raise HTTPException(status_code=400, detail="Request already decided")

    now = datetime.now(timezone.utc).isoformat()
    update = {
        "status": "approved",
        "decided_by": current_user["id"],
        "decided_at": now,
    }
    if notes is not None:
        update["notes"] = notes

    await db.approval_requests.update_one({"id": request_id}, {"$set": update})
    return {"message": "Approved"}


@router.put("/requests/{request_id}/reject")
async def reject_request(request_id: str, notes: Optional[str] = None, current_user: dict = Depends(get_current_user)):
    req = await db.approval_requests.find_one({"id": request_id}, {"_id": 0})
    if not req:
        raise HTTPException(status_code=404, detail="Approval request not found")

    if current_user.get("role") not in ["admin", req.get("approver_role")]:
        raise HTTPException(status_code=403, detail="Not allowed to reject")

    if req.get("status") != "pending":
        raise HTTPException(status_code=400, detail="Request already decided")

    now = datetime.now(timezone.utc).isoformat()
    update = {
        "status": "rejected",
        "decided_by": current_user["id"],
        "decided_at": now,
    }
    if notes is not None:
        update["notes"] = notes

    await db.approval_requests.update_one({"id": request_id}, {"$set": update})
    return {"message": "Rejected"}
