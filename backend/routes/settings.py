from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, timezone
import uuid
from server import db, get_current_user

router = APIRouter()

class UserUpdate(BaseModel):
    role: Optional[str] = None
    location: Optional[str] = None
    department: Optional[str] = None
    team: Optional[str] = None
    reports_to: Optional[str] = None
    status: Optional[str] = None

class UserResponse(BaseModel):
    id: str
    email: str
    name: str
    role: str
    location: Optional[str] = None
    department: Optional[str] = None
    team: Optional[str] = None
    reports_to: Optional[str] = None
    created_at: str


@router.get("/users", response_model=List[UserResponse])
async def get_all_users(current_user: dict = Depends(get_current_user)):
    if current_user['role'] != 'admin':
        raise HTTPException(status_code=403, detail="Access denied. Admin only.")
    
    users = await db.users.find({}, {'_id': 0, 'password': 0}).to_list(1000)
    return [UserResponse(**user) for user in users]

@router.put("/users/{user_id}")
async def update_user(user_id: str, update_data: UserUpdate, current_user: dict = Depends(get_current_user)):
    if current_user['role'] != 'admin':
        raise HTTPException(status_code=403, detail="Access denied. Admin only.")
    
    update_dict = {k: v for k, v in update_data.model_dump().items() if v is not None}
    update_dict['updated_at'] = datetime.now(timezone.utc).isoformat()
    
    result = await db.users.update_one(
        {'id': user_id},
        {'$set': update_dict}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {'message': 'User updated successfully'}

@router.delete("/users/{user_id}")
async def delete_user(user_id: str, current_user: dict = Depends(get_current_user)):
    if current_user['role'] != 'admin':
        raise HTTPException(status_code=403, detail="Access denied. Admin only.")
    
    if user_id == current_user['id']:
        raise HTTPException(status_code=400, detail="Cannot delete your own account")
    
    result = await db.users.delete_one({'id': user_id})
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {'message': 'User deleted successfully'}