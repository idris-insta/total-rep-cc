"""
Internal Chat System - WhatsApp/Slack-like messaging for ERP users
Features:
- Direct messages (1-on-1)
- Group chats with admin controls
- File/image attachments
- Task assignment from chat
- Message reactions
- Read receipts (polling-based)
"""

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
import uuid
import os
import shutil

from server import db, get_current_user

router = APIRouter()

UPLOAD_DIR = "/app/uploads/chat"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# ==================== MODELS ====================
class MessageCreate(BaseModel):
    content: str
    message_type: str = "text"  # text, image, file, task
    attachment_url: Optional[str] = None
    attachment_name: Optional[str] = None
    reply_to: Optional[str] = None
    task_data: Optional[Dict[str, Any]] = None  # For task messages

class GroupCreate(BaseModel):
    name: str
    description: Optional[str] = None
    member_ids: List[str]
    avatar_url: Optional[str] = None

class GroupUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    avatar_url: Optional[str] = None

class TaskFromChat(BaseModel):
    title: str
    description: Optional[str] = None
    assigned_to: str
    due_date: Optional[str] = None
    priority: str = "medium"  # low, medium, high, urgent
    chat_id: Optional[str] = None
    message_id: Optional[str] = None


# ==================== DIRECT MESSAGES ====================
@router.get("/conversations")
async def get_conversations(current_user: dict = Depends(get_current_user)):
    """Get all conversations for current user (DMs and groups)"""
    user_id = current_user['id']
    
    # Get direct message conversations
    dm_pipeline = [
        {"$match": {
            "$or": [
                {"sender_id": user_id},
                {"receiver_id": user_id}
            ],
            "group_id": None
        }},
        {"$sort": {"created_at": -1}},
        {"$group": {
            "_id": {
                "$cond": [
                    {"$eq": ["$sender_id", user_id]},
                    "$receiver_id",
                    "$sender_id"
                ]
            },
            "last_message": {"$first": "$$ROOT"},
            "unread_count": {
                "$sum": {
                    "$cond": [
                        {"$and": [
                            {"$ne": ["$sender_id", user_id]},
                            {"$eq": ["$is_read", False]}
                        ]},
                        1, 0
                    ]
                }
            }
        }}
    ]
    
    dm_results = await db.chat_messages.aggregate(dm_pipeline).to_list(100)
    
    # Get user details for DMs
    conversations = []
    for dm in dm_results:
        other_user_id = dm['_id']
        other_user = await db.users.find_one({"id": other_user_id}, {"_id": 0, "password": 0})
        if other_user:
            last_msg = dm['last_message']
            conversations.append({
                "type": "dm",
                "id": other_user_id,
                "name": other_user.get('name', other_user.get('email', 'Unknown')),
                "avatar": other_user.get('avatar_url'),
                "last_message": last_msg.get('content', '')[:50],
                "last_message_time": last_msg.get('created_at'),
                "unread_count": dm['unread_count'],
                "is_online": other_user.get('is_online', False)
            })
    
    # Get group conversations
    groups = await db.chat_groups.find(
        {"member_ids": user_id, "is_active": True},
        {"_id": 0}
    ).to_list(50)
    
    for group in groups:
        last_msg = await db.chat_messages.find_one(
            {"group_id": group['id']},
            {"_id": 0},
            sort=[("created_at", -1)]
        )
        unread = await db.chat_messages.count_documents({
            "group_id": group['id'],
            "sender_id": {"$ne": user_id},
            "read_by": {"$nin": [user_id]}
        })
        
        conversations.append({
            "type": "group",
            "id": group['id'],
            "name": group['name'],
            "avatar": group.get('avatar_url'),
            "last_message": last_msg.get('content', '')[:50] if last_msg else '',
            "last_message_time": last_msg.get('created_at') if last_msg else None,
            "unread_count": unread,
            "member_count": len(group.get('member_ids', []))
        })
    
    # Sort by last message time
    conversations.sort(key=lambda x: x.get('last_message_time') or '', reverse=True)
    
    return conversations


@router.get("/messages/dm/{user_id}")
async def get_dm_messages(
    user_id: str,
    limit: int = Query(default=50, le=200),
    before: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Get direct messages with a specific user"""
    my_id = current_user['id']
    
    query = {
        "$or": [
            {"sender_id": my_id, "receiver_id": user_id},
            {"sender_id": user_id, "receiver_id": my_id}
        ],
        "group_id": None
    }
    
    if before:
        query["created_at"] = {"$lt": before}
    
    messages = await db.chat_messages.find(
        query,
        {"_id": 0}
    ).sort("created_at", -1).limit(limit).to_list(limit)
    
    # Mark messages as read
    await db.chat_messages.update_many(
        {"sender_id": user_id, "receiver_id": my_id, "is_read": False},
        {"$set": {"is_read": True, "read_at": datetime.now(timezone.utc).isoformat()}}
    )
    
    # Get other user info
    other_user = await db.users.find_one({"id": user_id}, {"_id": 0, "password": 0})
    
    return {
        "messages": list(reversed(messages)),
        "user": other_user,
        "has_more": len(messages) == limit
    }


@router.post("/messages/dm/{user_id}")
async def send_dm(
    user_id: str,
    message: MessageCreate,
    current_user: dict = Depends(get_current_user)
):
    """Send a direct message to a user"""
    my_id = current_user['id']
    
    # Verify recipient exists
    recipient = await db.users.find_one({"id": user_id}, {"_id": 0})
    if not recipient:
        raise HTTPException(status_code=404, detail="User not found")
    
    message_id = str(uuid.uuid4())
    message_doc = {
        "id": message_id,
        "sender_id": my_id,
        "sender_name": current_user.get('name', current_user.get('email')),
        "receiver_id": user_id,
        "group_id": None,
        "content": message.content,
        "message_type": message.message_type,
        "attachment_url": message.attachment_url,
        "attachment_name": message.attachment_name,
        "reply_to": message.reply_to,
        "task_data": message.task_data,
        "is_read": False,
        "read_at": None,
        "reactions": [],
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.chat_messages.insert_one(message_doc)
    
    # Create task if message type is task
    if message.message_type == "task" and message.task_data:
        await create_chat_task(message.task_data, message_id, my_id)
    
    return {k: v for k, v in message_doc.items() if k != '_id'}


# ==================== GROUP CHATS ====================
@router.post("/groups")
async def create_group(
    group: GroupCreate,
    current_user: dict = Depends(get_current_user)
):
    """Create a new group chat"""
    group_id = str(uuid.uuid4())
    
    # Add creator to members if not already included
    member_ids = list(set(group.member_ids + [current_user['id']]))
    
    group_doc = {
        "id": group_id,
        "name": group.name,
        "description": group.description,
        "avatar_url": group.avatar_url,
        "member_ids": member_ids,
        "admin_ids": [current_user['id']],
        "created_by": current_user['id'],
        "created_at": datetime.now(timezone.utc).isoformat(),
        "is_active": True
    }
    
    await db.chat_groups.insert_one(group_doc)
    
    # Create system message
    await db.chat_messages.insert_one({
        "id": str(uuid.uuid4()),
        "sender_id": "system",
        "sender_name": "System",
        "group_id": group_id,
        "content": f"{current_user.get('name', 'User')} created the group",
        "message_type": "system",
        "created_at": datetime.now(timezone.utc).isoformat()
    })
    
    return {k: v for k, v in group_doc.items() if k != '_id'}


@router.get("/groups/{group_id}")
async def get_group(group_id: str, current_user: dict = Depends(get_current_user)):
    """Get group details"""
    group = await db.chat_groups.find_one(
        {"id": group_id, "member_ids": current_user['id']},
        {"_id": 0}
    )
    
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    
    # Get member details
    members = await db.users.find(
        {"id": {"$in": group['member_ids']}},
        {"_id": 0, "password": 0}
    ).to_list(100)
    
    group['members'] = members
    return group


@router.get("/messages/group/{group_id}")
async def get_group_messages(
    group_id: str,
    limit: int = Query(default=50, le=200),
    before: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Get messages from a group"""
    # Verify membership
    group = await db.chat_groups.find_one(
        {"id": group_id, "member_ids": current_user['id']},
        {"_id": 0}
    )
    if not group:
        raise HTTPException(status_code=403, detail="Not a member of this group")
    
    query = {"group_id": group_id}
    if before:
        query["created_at"] = {"$lt": before}
    
    messages = await db.chat_messages.find(
        query,
        {"_id": 0}
    ).sort("created_at", -1).limit(limit).to_list(limit)
    
    # Mark as read
    await db.chat_messages.update_many(
        {"group_id": group_id, "read_by": {"$nin": [current_user['id']]}},
        {"$addToSet": {"read_by": current_user['id']}}
    )
    
    return {
        "messages": list(reversed(messages)),
        "group": group,
        "has_more": len(messages) == limit
    }


@router.post("/messages/group/{group_id}")
async def send_group_message(
    group_id: str,
    message: MessageCreate,
    current_user: dict = Depends(get_current_user)
):
    """Send a message to a group"""
    # Verify membership
    group = await db.chat_groups.find_one(
        {"id": group_id, "member_ids": current_user['id']},
        {"_id": 0}
    )
    if not group:
        raise HTTPException(status_code=403, detail="Not a member of this group")
    
    message_id = str(uuid.uuid4())
    message_doc = {
        "id": message_id,
        "sender_id": current_user['id'],
        "sender_name": current_user.get('name', current_user.get('email')),
        "group_id": group_id,
        "receiver_id": None,
        "content": message.content,
        "message_type": message.message_type,
        "attachment_url": message.attachment_url,
        "attachment_name": message.attachment_name,
        "reply_to": message.reply_to,
        "task_data": message.task_data,
        "read_by": [current_user['id']],
        "reactions": [],
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.chat_messages.insert_one(message_doc)
    
    if message.message_type == "task" and message.task_data:
        await create_chat_task(message.task_data, message_id, current_user['id'])
    
    return {k: v for k, v in message_doc.items() if k != '_id'}


@router.put("/groups/{group_id}")
async def update_group(
    group_id: str,
    updates: GroupUpdate,
    current_user: dict = Depends(get_current_user)
):
    """Update group details (admin only)"""
    group = await db.chat_groups.find_one(
        {"id": group_id, "admin_ids": current_user['id']},
        {"_id": 0}
    )
    if not group:
        raise HTTPException(status_code=403, detail="Not authorized to update this group")
    
    update_data = {k: v for k, v in updates.model_dump().items() if v is not None}
    if update_data:
        await db.chat_groups.update_one(
            {"id": group_id},
            {"$set": update_data}
        )
    
    return {"message": "Group updated successfully"}


@router.post("/groups/{group_id}/members")
async def add_group_member(
    group_id: str,
    user_ids: List[str],
    current_user: dict = Depends(get_current_user)
):
    """Add members to a group (admin only)"""
    group = await db.chat_groups.find_one(
        {"id": group_id, "admin_ids": current_user['id']},
        {"_id": 0}
    )
    if not group:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    await db.chat_groups.update_one(
        {"id": group_id},
        {"$addToSet": {"member_ids": {"$each": user_ids}}}
    )
    
    # System message
    users = await db.users.find({"id": {"$in": user_ids}}, {"name": 1}).to_list(len(user_ids))
    names = [u.get('name', 'User') for u in users]
    
    await db.chat_messages.insert_one({
        "id": str(uuid.uuid4()),
        "sender_id": "system",
        "sender_name": "System",
        "group_id": group_id,
        "content": f"{current_user.get('name')} added {', '.join(names)} to the group",
        "message_type": "system",
        "created_at": datetime.now(timezone.utc).isoformat()
    })
    
    return {"message": "Members added successfully"}


@router.delete("/groups/{group_id}/members/{user_id}")
async def remove_group_member(
    group_id: str,
    user_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Remove a member from group"""
    group = await db.chat_groups.find_one({"id": group_id}, {"_id": 0})
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    
    # User can remove themselves or admin can remove others
    if user_id != current_user['id'] and current_user['id'] not in group.get('admin_ids', []):
        raise HTTPException(status_code=403, detail="Not authorized")
    
    await db.chat_groups.update_one(
        {"id": group_id},
        {"$pull": {"member_ids": user_id, "admin_ids": user_id}}
    )
    
    return {"message": "Member removed"}


# ==================== TASKS FROM CHAT ====================
async def create_chat_task(task_data: Dict[str, Any], message_id: str, created_by: str):
    """Create a task from chat message"""
    task_id = str(uuid.uuid4())
    task_doc = {
        "id": task_id,
        "title": task_data.get('title', 'New Task'),
        "description": task_data.get('description', ''),
        "assigned_to": task_data.get('assigned_to'),
        "assigned_by": created_by,
        "due_date": task_data.get('due_date'),
        "priority": task_data.get('priority', 'medium'),
        "status": "pending",
        "chat_id": task_data.get('chat_id'),
        "message_id": message_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    await db.chat_tasks.insert_one(task_doc)
    return task_id


@router.post("/tasks")
async def create_task(task: TaskFromChat, current_user: dict = Depends(get_current_user)):
    """Create a new task"""
    task_id = str(uuid.uuid4())
    task_doc = {
        "id": task_id,
        "title": task.title,
        "description": task.description,
        "assigned_to": task.assigned_to,
        "assigned_by": current_user['id'],
        "due_date": task.due_date,
        "priority": task.priority,
        "status": "pending",
        "chat_id": task.chat_id,
        "message_id": task.message_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    await db.chat_tasks.insert_one(task_doc)
    return {k: v for k, v in task_doc.items() if k != '_id'}


@router.get("/tasks")
async def get_tasks(
    status: Optional[str] = None,
    assigned_to: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Get tasks (assigned to me or created by me)"""
    query = {
        "$or": [
            {"assigned_to": current_user['id']},
            {"assigned_by": current_user['id']}
        ]
    }
    if status:
        query["status"] = status
    if assigned_to:
        query["assigned_to"] = assigned_to
    
    tasks = await db.chat_tasks.find(query, {"_id": 0}).sort("created_at", -1).to_list(200)
    
    # Get assignee names
    user_ids = list(set([t.get('assigned_to') for t in tasks] + [t.get('assigned_by') for t in tasks]))
    users = await db.users.find({"id": {"$in": user_ids}}, {"_id": 0, "id": 1, "name": 1}).to_list(len(user_ids))
    user_map = {u['id']: u.get('name', 'Unknown') for u in users}
    
    for task in tasks:
        task['assigned_to_name'] = user_map.get(task.get('assigned_to'), 'Unknown')
        task['assigned_by_name'] = user_map.get(task.get('assigned_by'), 'Unknown')
    
    return tasks


@router.put("/tasks/{task_id}")
async def update_task(
    task_id: str,
    status: Optional[str] = None,
    priority: Optional[str] = None,
    due_date: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Update task status/priority"""
    task = await db.chat_tasks.find_one({"id": task_id}, {"_id": 0})
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    if task.get('assigned_to') != current_user['id'] and task.get('assigned_by') != current_user['id']:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    update_data = {"updated_at": datetime.now(timezone.utc).isoformat()}
    if status:
        update_data["status"] = status
        if status == "completed":
            update_data["completed_at"] = datetime.now(timezone.utc).isoformat()
    if priority:
        update_data["priority"] = priority
    if due_date:
        update_data["due_date"] = due_date
    
    await db.chat_tasks.update_one({"id": task_id}, {"$set": update_data})
    return {"message": "Task updated"}


# ==================== ATTACHMENTS ====================
@router.post("/upload")
async def upload_chat_attachment(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user)
):
    """Upload a file attachment for chat"""
    file_id = str(uuid.uuid4())
    file_ext = os.path.splitext(file.filename)[1] if file.filename else ''
    file_path = os.path.join(UPLOAD_DIR, f"{file_id}{file_ext}")
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # Determine file type
    file_type = "file"
    if file.content_type and file.content_type.startswith("image/"):
        file_type = "image"
    
    return {
        "file_id": file_id,
        "file_name": file.filename,
        "file_type": file_type,
        "file_url": f"/api/chat/files/{file_id}{file_ext}",
        "content_type": file.content_type
    }


@router.get("/files/{file_name}")
async def get_chat_file(file_name: str):
    """Get uploaded chat file"""
    from fastapi.responses import FileResponse
    file_path = os.path.join(UPLOAD_DIR, file_name)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(file_path)


# ==================== REACTIONS ====================
@router.post("/messages/{message_id}/react")
async def react_to_message(
    message_id: str,
    emoji: str,
    current_user: dict = Depends(get_current_user)
):
    """Add/remove reaction to a message"""
    message = await db.chat_messages.find_one({"id": message_id}, {"_id": 0})
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")
    
    reactions = message.get('reactions', [])
    existing = next((r for r in reactions if r['user_id'] == current_user['id'] and r['emoji'] == emoji), None)
    
    if existing:
        # Remove reaction
        await db.chat_messages.update_one(
            {"id": message_id},
            {"$pull": {"reactions": {"user_id": current_user['id'], "emoji": emoji}}}
        )
    else:
        # Add reaction
        await db.chat_messages.update_one(
            {"id": message_id},
            {"$addToSet": {"reactions": {"user_id": current_user['id'], "emoji": emoji, "user_name": current_user.get('name')}}}
        )
    
    return {"message": "Reaction updated"}


# ==================== USERS LIST ====================
@router.get("/users")
async def get_chat_users(current_user: dict = Depends(get_current_user)):
    """Get list of users for chat"""
    users = await db.users.find(
        {"is_active": {"$ne": False}},
        {"_id": 0, "password": 0}
    ).to_list(500)
    
    # Exclude current user
    users = [u for u in users if u.get('id') != current_user['id']]
    
    return users
