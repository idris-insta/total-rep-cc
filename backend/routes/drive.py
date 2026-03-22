"""
Drive System - Google Drive-like file storage for ERP
Features:
- File upload (docs, sheets, PDFs, images, videos)
- Folder organization with nesting
- File sharing with users (view/edit permissions)
- File preview, search, favorites
- Integration with chat and documents
"""

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, Form
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
import uuid
import os
import shutil
import mimetypes

from server import db, get_current_user

router = APIRouter()

DRIVE_DIR = "/app/uploads/drive"
os.makedirs(DRIVE_DIR, exist_ok=True)

# ==================== MODELS ====================
class FolderCreate(BaseModel):
    name: str
    parent_id: Optional[str] = None
    color: Optional[str] = None

class FolderUpdate(BaseModel):
    name: Optional[str] = None
    color: Optional[str] = None

class FileShare(BaseModel):
    user_ids: List[str]
    permission: str = "view"  # view, edit

class FileMove(BaseModel):
    folder_id: Optional[str] = None  # null for root


# ==================== FOLDERS ====================
@router.post("/folders")
async def create_folder(folder: FolderCreate, current_user: dict = Depends(get_current_user)):
    """Create a new folder"""
    folder_id = str(uuid.uuid4())
    
    # Verify parent folder exists and user has access
    if folder.parent_id:
        parent = await db.drive_folders.find_one({
            "id": folder.parent_id,
            "$or": [
                {"owner_id": current_user['id']},
                {"shared_with.user_id": current_user['id']}
            ]
        })
        if not parent:
            raise HTTPException(status_code=404, detail="Parent folder not found")
    
    folder_doc = {
        "id": folder_id,
        "name": folder.name,
        "parent_id": folder.parent_id,
        "color": folder.color or "#3b82f6",
        "owner_id": current_user['id'],
        "owner_name": current_user.get('name', current_user.get('email')),
        "shared_with": [],
        "is_favorite": False,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.drive_folders.insert_one(folder_doc)
    return {k: v for k, v in folder_doc.items() if k != '_id'}


@router.get("/folders")
async def get_folders(
    parent_id: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Get folders in a directory"""
    query = {
        "parent_id": parent_id,
        "$or": [
            {"owner_id": current_user['id']},
            {"shared_with.user_id": current_user['id']}
        ]
    }
    
    folders = await db.drive_folders.find(query, {"_id": 0}).sort("name", 1).to_list(500)
    return folders


@router.get("/folders/{folder_id}")
async def get_folder(folder_id: str, current_user: dict = Depends(get_current_user)):
    """Get folder details with breadcrumb path"""
    folder = await db.drive_folders.find_one({
        "id": folder_id,
        "$or": [
            {"owner_id": current_user['id']},
            {"shared_with.user_id": current_user['id']}
        ]
    }, {"_id": 0})
    
    if not folder:
        raise HTTPException(status_code=404, detail="Folder not found")
    
    # Build breadcrumb path
    path = [folder]
    current = folder
    while current.get('parent_id'):
        parent = await db.drive_folders.find_one({"id": current['parent_id']}, {"_id": 0})
        if parent:
            path.insert(0, parent)
            current = parent
        else:
            break
    
    folder['path'] = path
    return folder


@router.put("/folders/{folder_id}")
async def update_folder(
    folder_id: str,
    updates: FolderUpdate,
    current_user: dict = Depends(get_current_user)
):
    """Update folder"""
    folder = await db.drive_folders.find_one({
        "id": folder_id,
        "owner_id": current_user['id']
    })
    if not folder:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    update_data = {k: v for k, v in updates.model_dump().items() if v is not None}
    update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
    
    await db.drive_folders.update_one({"id": folder_id}, {"$set": update_data})
    return {"message": "Folder updated"}


@router.delete("/folders/{folder_id}")
async def delete_folder(folder_id: str, current_user: dict = Depends(get_current_user)):
    """Delete folder and all contents"""
    folder = await db.drive_folders.find_one({
        "id": folder_id,
        "owner_id": current_user['id']
    })
    if not folder:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    # Delete all files in folder
    files = await db.drive_files.find({"folder_id": folder_id}, {"file_path": 1}).to_list(1000)
    for f in files:
        if f.get('file_path') and os.path.exists(f['file_path']):
            os.remove(f['file_path'])
    
    await db.drive_files.delete_many({"folder_id": folder_id})
    
    # Delete subfolders recursively
    async def delete_subfolders(parent_id):
        subfolders = await db.drive_folders.find({"parent_id": parent_id}, {"id": 1}).to_list(100)
        for sf in subfolders:
            await delete_subfolders(sf['id'])
            # Delete files in subfolder
            sub_files = await db.drive_files.find({"folder_id": sf['id']}, {"file_path": 1}).to_list(1000)
            for f in sub_files:
                if f.get('file_path') and os.path.exists(f['file_path']):
                    os.remove(f['file_path'])
            await db.drive_files.delete_many({"folder_id": sf['id']})
            await db.drive_folders.delete_one({"id": sf['id']})
    
    await delete_subfolders(folder_id)
    await db.drive_folders.delete_one({"id": folder_id})
    
    return {"message": "Folder deleted"}


# ==================== FILES ====================
@router.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    folder_id: Optional[str] = Form(None),
    current_user: dict = Depends(get_current_user)
):
    """Upload a file to drive"""
    file_id = str(uuid.uuid4())
    original_name = file.filename or "untitled"
    file_ext = os.path.splitext(original_name)[1]
    safe_name = f"{file_id}{file_ext}"
    file_path = os.path.join(DRIVE_DIR, safe_name)
    
    # Verify folder access
    if folder_id:
        folder = await db.drive_folders.find_one({
            "id": folder_id,
            "$or": [
                {"owner_id": current_user['id']},
                {"shared_with": {"$elemMatch": {"user_id": current_user['id'], "permission": "edit"}}}
            ]
        })
        if not folder:
            raise HTTPException(status_code=403, detail="Cannot upload to this folder")
    
    # Save file
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    file_size = os.path.getsize(file_path)
    content_type = file.content_type or mimetypes.guess_type(original_name)[0] or "application/octet-stream"
    
    # Determine file category
    category = "other"
    if content_type.startswith("image/"):
        category = "image"
    elif content_type.startswith("video/"):
        category = "video"
    elif content_type.startswith("audio/"):
        category = "audio"
    elif content_type in ["application/pdf"]:
        category = "pdf"
    elif content_type in ["application/vnd.ms-excel", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"]:
        category = "spreadsheet"
    elif content_type in ["application/msword", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"]:
        category = "document"
    
    file_doc = {
        "id": file_id,
        "name": original_name,
        "file_path": file_path,
        "file_size": file_size,
        "content_type": content_type,
        "category": category,
        "folder_id": folder_id,
        "owner_id": current_user['id'],
        "owner_name": current_user.get('name', current_user.get('email')),
        "shared_with": [],
        "is_favorite": False,
        "download_count": 0,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.drive_files.insert_one(file_doc)
    
    # Update storage usage
    await db.users.update_one(
        {"id": current_user['id']},
        {"$inc": {"storage_used": file_size}}
    )
    
    return {k: v for k, v in file_doc.items() if k not in ['_id', 'file_path']}


@router.get("/files")
async def get_files(
    folder_id: Optional[str] = None,
    category: Optional[str] = None,
    search: Optional[str] = None,
    favorites_only: bool = False,
    shared_only: bool = False,
    recent: bool = False,
    current_user: dict = Depends(get_current_user)
):
    """Get files with filters"""
    query = {
        "$or": [
            {"owner_id": current_user['id']},
            {"shared_with.user_id": current_user['id']}
        ]
    }
    
    if folder_id is not None:
        query["folder_id"] = folder_id if folder_id else None
    
    if category:
        query["category"] = category
    
    if search:
        query["name"] = {"$regex": search, "$options": "i"}
    
    if favorites_only:
        query["is_favorite"] = True
    
    if shared_only:
        query["shared_with.0"] = {"$exists": True}
    
    sort_field = "updated_at" if recent else "name"
    sort_order = -1 if recent else 1
    
    files = await db.drive_files.find(
        query,
        {"_id": 0, "file_path": 0}
    ).sort(sort_field, sort_order).limit(200).to_list(200)
    
    return files


@router.get("/files/{file_id}")
async def get_file_info(file_id: str, current_user: dict = Depends(get_current_user)):
    """Get file details"""
    file = await db.drive_files.find_one({
        "id": file_id,
        "$or": [
            {"owner_id": current_user['id']},
            {"shared_with.user_id": current_user['id']}
        ]
    }, {"_id": 0, "file_path": 0})
    
    if not file:
        raise HTTPException(status_code=404, detail="File not found")
    
    return file


@router.get("/files/{file_id}/download")
async def download_file(file_id: str, current_user: dict = Depends(get_current_user)):
    """Download a file"""
    file = await db.drive_files.find_one({
        "id": file_id,
        "$or": [
            {"owner_id": current_user['id']},
            {"shared_with.user_id": current_user['id']}
        ]
    })
    
    if not file:
        raise HTTPException(status_code=404, detail="File not found")
    
    file_path = file.get('file_path')
    if not file_path or not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found on disk")
    
    # Update download count
    await db.drive_files.update_one({"id": file_id}, {"$inc": {"download_count": 1}})
    
    return FileResponse(
        file_path,
        filename=file.get('name'),
        media_type=file.get('content_type')
    )


@router.get("/files/{file_id}/preview")
async def preview_file(file_id: str, current_user: dict = Depends(get_current_user)):
    """Get file for preview (images, PDFs)"""
    file = await db.drive_files.find_one({
        "id": file_id,
        "$or": [
            {"owner_id": current_user['id']},
            {"shared_with.user_id": current_user['id']}
        ]
    })
    
    if not file:
        raise HTTPException(status_code=404, detail="File not found")
    
    file_path = file.get('file_path')
    if not file_path or not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found on disk")
    
    return FileResponse(file_path, media_type=file.get('content_type'))


@router.put("/files/{file_id}")
async def update_file(
    file_id: str,
    name: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Rename a file"""
    file = await db.drive_files.find_one({
        "id": file_id,
        "owner_id": current_user['id']
    })
    if not file:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    update_data = {"updated_at": datetime.now(timezone.utc).isoformat()}
    if name:
        update_data["name"] = name
    
    await db.drive_files.update_one({"id": file_id}, {"$set": update_data})
    return {"message": "File updated"}


@router.put("/files/{file_id}/move")
async def move_file(
    file_id: str,
    move: FileMove,
    current_user: dict = Depends(get_current_user)
):
    """Move file to another folder"""
    file = await db.drive_files.find_one({
        "id": file_id,
        "owner_id": current_user['id']
    })
    if not file:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    # Verify target folder
    if move.folder_id:
        folder = await db.drive_folders.find_one({
            "id": move.folder_id,
            "$or": [
                {"owner_id": current_user['id']},
                {"shared_with": {"$elemMatch": {"user_id": current_user['id'], "permission": "edit"}}}
            ]
        })
        if not folder:
            raise HTTPException(status_code=403, detail="Cannot move to this folder")
    
    await db.drive_files.update_one(
        {"id": file_id},
        {"$set": {"folder_id": move.folder_id, "updated_at": datetime.now(timezone.utc).isoformat()}}
    )
    
    return {"message": "File moved"}


@router.delete("/files/{file_id}")
async def delete_file(file_id: str, current_user: dict = Depends(get_current_user)):
    """Delete a file"""
    file = await db.drive_files.find_one({
        "id": file_id,
        "owner_id": current_user['id']
    })
    if not file:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    # Delete physical file
    file_path = file.get('file_path')
    if file_path and os.path.exists(file_path):
        os.remove(file_path)
    
    # Update storage usage
    await db.users.update_one(
        {"id": current_user['id']},
        {"$inc": {"storage_used": -file.get('file_size', 0)}}
    )
    
    await db.drive_files.delete_one({"id": file_id})
    return {"message": "File deleted"}


# ==================== SHARING ====================
@router.post("/files/{file_id}/share")
async def share_file(
    file_id: str,
    share: FileShare,
    current_user: dict = Depends(get_current_user)
):
    """Share file with users"""
    file = await db.drive_files.find_one({
        "id": file_id,
        "owner_id": current_user['id']
    })
    if not file:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    # Get user names
    users = await db.users.find(
        {"id": {"$in": share.user_ids}},
        {"id": 1, "name": 1, "email": 1}
    ).to_list(len(share.user_ids))
    
    share_entries = [
        {"user_id": u['id'], "user_name": u.get('name', u.get('email')), "permission": share.permission}
        for u in users
    ]
    
    await db.drive_files.update_one(
        {"id": file_id},
        {"$addToSet": {"shared_with": {"$each": share_entries}}}
    )
    
    return {"message": "File shared", "shared_with": share_entries}


@router.post("/folders/{folder_id}/share")
async def share_folder(
    folder_id: str,
    share: FileShare,
    current_user: dict = Depends(get_current_user)
):
    """Share folder with users"""
    folder = await db.drive_folders.find_one({
        "id": folder_id,
        "owner_id": current_user['id']
    })
    if not folder:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    users = await db.users.find(
        {"id": {"$in": share.user_ids}},
        {"id": 1, "name": 1, "email": 1}
    ).to_list(len(share.user_ids))
    
    share_entries = [
        {"user_id": u['id'], "user_name": u.get('name', u.get('email')), "permission": share.permission}
        for u in users
    ]
    
    await db.drive_folders.update_one(
        {"id": folder_id},
        {"$addToSet": {"shared_with": {"$each": share_entries}}}
    )
    
    return {"message": "Folder shared"}


@router.delete("/files/{file_id}/share/{user_id}")
async def unshare_file(
    file_id: str,
    user_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Remove user from file sharing"""
    file = await db.drive_files.find_one({
        "id": file_id,
        "owner_id": current_user['id']
    })
    if not file:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    await db.drive_files.update_one(
        {"id": file_id},
        {"$pull": {"shared_with": {"user_id": user_id}}}
    )
    
    return {"message": "Share removed"}


# ==================== FAVORITES ====================
@router.post("/files/{file_id}/favorite")
async def toggle_file_favorite(file_id: str, current_user: dict = Depends(get_current_user)):
    """Toggle file favorite status"""
    file = await db.drive_files.find_one({
        "id": file_id,
        "$or": [
            {"owner_id": current_user['id']},
            {"shared_with.user_id": current_user['id']}
        ]
    }, {"is_favorite": 1})
    
    if not file:
        raise HTTPException(status_code=404, detail="File not found")
    
    new_status = not file.get('is_favorite', False)
    await db.drive_files.update_one({"id": file_id}, {"$set": {"is_favorite": new_status}})
    
    return {"is_favorite": new_status}


@router.post("/folders/{folder_id}/favorite")
async def toggle_folder_favorite(folder_id: str, current_user: dict = Depends(get_current_user)):
    """Toggle folder favorite status"""
    folder = await db.drive_folders.find_one({
        "id": folder_id,
        "$or": [
            {"owner_id": current_user['id']},
            {"shared_with.user_id": current_user['id']}
        ]
    }, {"is_favorite": 1})
    
    if not folder:
        raise HTTPException(status_code=404, detail="Folder not found")
    
    new_status = not folder.get('is_favorite', False)
    await db.drive_folders.update_one({"id": folder_id}, {"$set": {"is_favorite": new_status}})
    
    return {"is_favorite": new_status}


# ==================== STORAGE STATS ====================
@router.get("/storage")
async def get_storage_stats(current_user: dict = Depends(get_current_user)):
    """Get user's storage statistics"""
    # Total file size
    pipeline = [
        {"$match": {"owner_id": current_user['id']}},
        {"$group": {"_id": None, "total_size": {"$sum": "$file_size"}, "file_count": {"$sum": 1}}}
    ]
    
    result = await db.drive_files.aggregate(pipeline).to_list(1)
    stats = result[0] if result else {"total_size": 0, "file_count": 0}
    
    # By category
    category_pipeline = [
        {"$match": {"owner_id": current_user['id']}},
        {"$group": {"_id": "$category", "size": {"$sum": "$file_size"}, "count": {"$sum": 1}}}
    ]
    categories = await db.drive_files.aggregate(category_pipeline).to_list(20)
    
    # Folder count
    folder_count = await db.drive_folders.count_documents({"owner_id": current_user['id']})
    
    return {
        "total_size": stats.get('total_size', 0),
        "file_count": stats.get('file_count', 0),
        "folder_count": folder_count,
        "by_category": {c['_id']: {"size": c['size'], "count": c['count']} for c in categories if c['_id']},
        "storage_limit": 5 * 1024 * 1024 * 1024  # 5GB limit
    }
