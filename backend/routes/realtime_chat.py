"""
REAL-TIME CHAT MODULE - WebSocket Implementation
Provides instant messaging between users using WebSockets
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict
from datetime import datetime, timezone
import uuid
import json
from server import db, get_current_user

router = APIRouter()

# Store active WebSocket connections
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}  # user_id -> [websockets]
    
    async def connect(self, websocket: WebSocket, user_id: str):
        await websocket.accept()
        if user_id not in self.active_connections:
            self.active_connections[user_id] = []
        self.active_connections[user_id].append(websocket)
    
    def disconnect(self, websocket: WebSocket, user_id: str):
        if user_id in self.active_connections:
            if websocket in self.active_connections[user_id]:
                self.active_connections[user_id].remove(websocket)
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]
    
    async def send_personal_message(self, message: dict, user_id: str):
        if user_id in self.active_connections:
            for connection in self.active_connections[user_id]:
                try:
                    await connection.send_json(message)
                except:
                    pass
    
    async def broadcast_to_room(self, message: dict, room_id: str, exclude_user: str = None):
        # Get room members
        room = await db.chat_rooms.find_one({"id": room_id}, {"_id": 0})
        if room:
            for member_id in room.get("members", []):
                if member_id != exclude_user:
                    await self.send_personal_message(message, member_id)
    
    def get_online_users(self) -> List[str]:
        return list(self.active_connections.keys())


manager = ConnectionManager()


# Models
class MessageCreate(BaseModel):
    room_id: str
    content: str
    message_type: str = "text"  # text, file, image, task
    metadata: Optional[dict] = None


class RoomCreate(BaseModel):
    name: str
    room_type: str = "direct"  # direct, group, channel
    members: List[str]
    description: Optional[str] = None


# WebSocket endpoint
@router.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    """WebSocket connection for real-time messaging"""
    await manager.connect(websocket, user_id)
    
    # Notify others user is online
    await db.users.update_one(
        {"id": user_id},
        {"$set": {"is_online": True, "last_seen": datetime.now(timezone.utc).isoformat()}}
    )
    
    try:
        while True:
            data = await websocket.receive_json()
            
            if data.get("type") == "message":
                # Handle new message
                message = {
                    "id": str(uuid.uuid4()),
                    "room_id": data["room_id"],
                    "sender_id": user_id,
                    "content": data["content"],
                    "message_type": data.get("message_type", "text"),
                    "metadata": data.get("metadata"),
                    "created_at": datetime.now(timezone.utc).isoformat(),
                    "read_by": [user_id]
                }
                
                # Save to database
                msg_to_save = {**message}
                await db.chat_messages.insert_one(msg_to_save)
                
                # Update room's last message
                await db.chat_rooms.update_one(
                    {"id": data["room_id"]},
                    {"$set": {
                        "last_message": message["content"][:100],
                        "last_message_at": message["created_at"],
                        "last_message_by": user_id
                    }}
                )
                
                # Broadcast to room members
                await manager.broadcast_to_room(
                    {"type": "new_message", "message": message},
                    data["room_id"],
                    exclude_user=user_id
                )
                
                # Send confirmation back
                await websocket.send_json({"type": "message_sent", "message": message})
            
            elif data.get("type") == "typing":
                # Broadcast typing indicator
                await manager.broadcast_to_room(
                    {"type": "typing", "user_id": user_id, "room_id": data["room_id"]},
                    data["room_id"],
                    exclude_user=user_id
                )
            
            elif data.get("type") == "read":
                # Mark messages as read
                await db.chat_messages.update_many(
                    {"room_id": data["room_id"], "read_by": {"$ne": user_id}},
                    {"$addToSet": {"read_by": user_id}}
                )
                
    except WebSocketDisconnect:
        manager.disconnect(websocket, user_id)
        await db.users.update_one(
            {"id": user_id},
            {"$set": {"is_online": False, "last_seen": datetime.now(timezone.utc).isoformat()}}
        )


# REST endpoints (for initial data load)
@router.get("/rooms")
async def get_rooms(current_user: dict = Depends(get_current_user)):
    """Get all chat rooms for the current user"""
    rooms = await db.chat_rooms.find(
        {"members": current_user["id"]},
        {"_id": 0}
    ).sort("last_message_at", -1).to_list(100)
    
    # Enrich with member info and unread counts
    for room in rooms:
        # Get member details
        members = await db.users.find(
            {"id": {"$in": room.get("members", [])}},
            {"_id": 0, "id": 1, "name": 1, "email": 1, "is_online": 1}
        ).to_list(50)
        room["member_details"] = members
        
        # Count unread
        unread = await db.chat_messages.count_documents({
            "room_id": room["id"],
            "read_by": {"$ne": current_user["id"]}
        })
        room["unread_count"] = unread
    
    return rooms


@router.post("/rooms")
async def create_room(room: RoomCreate, current_user: dict = Depends(get_current_user)):
    """Create a new chat room"""
    # Ensure creator is in members
    members = list(set(room.members + [current_user["id"]]))
    
    # Check if direct room already exists
    if room.room_type == "direct" and len(members) == 2:
        existing = await db.chat_rooms.find_one({
            "room_type": "direct",
            "members": {"$all": members, "$size": 2}
        }, {"_id": 0})
        if existing:
            return existing
    
    room_doc = {
        "id": str(uuid.uuid4()),
        "name": room.name,
        "room_type": room.room_type,
        "members": members,
        "description": room.description,
        "created_by": current_user["id"],
        "created_at": datetime.now(timezone.utc).isoformat(),
        "last_message": None,
        "last_message_at": None
    }
    
    await db.chat_rooms.insert_one(room_doc)
    del room_doc["_id"]
    
    return room_doc


@router.get("/rooms/{room_id}/messages")
async def get_messages(room_id: str, limit: int = 50, before: Optional[str] = None, current_user: dict = Depends(get_current_user)):
    """Get messages for a room"""
    # Verify user is member
    room = await db.chat_rooms.find_one({"id": room_id, "members": current_user["id"]}, {"_id": 0})
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    
    query = {"room_id": room_id}
    if before:
        query["created_at"] = {"$lt": before}
    
    messages = await db.chat_messages.find(
        query,
        {"_id": 0}
    ).sort("created_at", -1).limit(limit).to_list(limit)
    
    # Mark as read
    await db.chat_messages.update_many(
        {"room_id": room_id, "read_by": {"$ne": current_user["id"]}},
        {"$addToSet": {"read_by": current_user["id"]}}
    )
    
    # Enrich with sender info
    for msg in messages:
        sender = await db.users.find_one({"id": msg["sender_id"]}, {"_id": 0, "name": 1, "email": 1})
        msg["sender"] = sender
    
    return messages[::-1]  # Return in chronological order


@router.post("/rooms/{room_id}/messages")
async def send_message(room_id: str, message: MessageCreate, current_user: dict = Depends(get_current_user)):
    """Send a message (REST fallback for non-WebSocket clients)"""
    # Verify user is member
    room = await db.chat_rooms.find_one({"id": room_id, "members": current_user["id"]}, {"_id": 0})
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    
    msg = {
        "id": str(uuid.uuid4()),
        "room_id": room_id,
        "sender_id": current_user["id"],
        "content": message.content,
        "message_type": message.message_type,
        "metadata": message.metadata,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "read_by": [current_user["id"]]
    }
    
    await db.chat_messages.insert_one({**msg})
    
    # Update room
    await db.chat_rooms.update_one(
        {"id": room_id},
        {"$set": {
            "last_message": msg["content"][:100],
            "last_message_at": msg["created_at"],
            "last_message_by": current_user["id"]
        }}
    )
    
    # Broadcast via WebSocket
    await manager.broadcast_to_room(
        {"type": "new_message", "message": msg},
        room_id,
        exclude_user=current_user["id"]
    )
    
    return msg


@router.get("/online-users")
async def get_online_users(current_user: dict = Depends(get_current_user)):
    """Get list of online users"""
    online_ids = manager.get_online_users()
    users = await db.users.find(
        {"id": {"$in": online_ids}},
        {"_id": 0, "id": 1, "name": 1, "email": 1}
    ).to_list(100)
    return users
