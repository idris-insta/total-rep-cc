from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
import uuid
from server import db, get_current_user

router = APIRouter()

# ==================== MODELS ====================
class MasterDataItem(BaseModel):
    id: str
    category: str
    value: str
    label: str
    is_active: bool = True
    sort_order: int = 0
    metadata: Optional[Dict[str, Any]] = None
    created_at: str
    updated_at: Optional[str] = None

class MasterDataCreate(BaseModel):
    category: str
    value: str
    label: str
    sort_order: int = 0
    metadata: Optional[Dict[str, Any]] = None

class MasterDataUpdate(BaseModel):
    value: Optional[str] = None
    label: Optional[str] = None
    is_active: Optional[bool] = None
    sort_order: Optional[int] = None
    metadata: Optional[Dict[str, Any]] = None

class NumberSeriesConfig(BaseModel):
    id: str
    document_type: str  # quotation, sales_order, invoice, sample, lead, etc.
    prefix: str
    suffix: Optional[str] = None
    separator: str = "-"
    year_format: str = "YYYY"  # YYYY, YY, YYMM, YYYYMM
    padding: int = 6
    current_number: int = 0
    reset_yearly: bool = True
    reset_monthly: bool = False
    is_active: bool = True
    created_at: str
    updated_at: Optional[str] = None

class NumberSeriesCreate(BaseModel):
    document_type: str
    prefix: str
    suffix: Optional[str] = None
    separator: str = "-"
    year_format: str = "YYYY"
    padding: int = 6
    current_number: int = 0
    reset_yearly: bool = True
    reset_monthly: bool = False

# ==================== MASTER DATA CATEGORIES ====================
DEFAULT_CATEGORIES = {
    "lead_source": [
        {"value": "IndiaMART", "label": "IndiaMART"},
        {"value": "TradeIndia", "label": "TradeIndia"},
        {"value": "Alibaba", "label": "Alibaba"},
        {"value": "Google", "label": "Google Search"},
        {"value": "Exhibition", "label": "Exhibition"},
        {"value": "Cold Call", "label": "Cold Call"},
        {"value": "Referral", "label": "Referral"},
        {"value": "Website", "label": "Website"},
        {"value": "LinkedIn", "label": "LinkedIn"},
        {"value": "Other", "label": "Other"}
    ],
    "lead_status": [
        {"value": "new", "label": "New"},
        {"value": "contacted", "label": "Contacted"},
        {"value": "qualified", "label": "Qualified"},
        {"value": "proposal", "label": "Proposal Sent"},
        {"value": "negotiation", "label": "Negotiation"},
        {"value": "converted", "label": "Converted"},
        {"value": "lost", "label": "Lost"}
    ],
    "industry": [
        {"value": "Manufacturing", "label": "Manufacturing"},
        {"value": "Packaging", "label": "Packaging"},
        {"value": "Construction", "label": "Construction"},
        {"value": "Automotive", "label": "Automotive"},
        {"value": "Electronics", "label": "Electronics"},
        {"value": "FMCG", "label": "FMCG"},
        {"value": "Pharmaceutical", "label": "Pharmaceutical"},
        {"value": "Textile", "label": "Textile"},
        {"value": "Food Processing", "label": "Food Processing"},
        {"value": "Logistics", "label": "Logistics"},
        {"value": "Other", "label": "Other"}
    ],
    "payment_terms": [
        {"value": "Advance", "label": "Advance"},
        {"value": "Cash", "label": "Cash"},
        {"value": "7 days", "label": "7 Days"},
        {"value": "15 days", "label": "15 Days"},
        {"value": "30 days", "label": "30 Days"},
        {"value": "45 days", "label": "45 Days"},
        {"value": "60 days", "label": "60 Days"},
        {"value": "90 days", "label": "90 Days"}
    ],
    "credit_control": [
        {"value": "Ignore", "label": "Ignore (No Check)"},
        {"value": "Warn", "label": "Warn (Show Alert)"},
        {"value": "Block", "label": "Block (Prevent Order)"}
    ],
    "transport_terms": [
        {"value": "Ex-Works", "label": "Ex-Works"},
        {"value": "FOR Destination", "label": "FOR Destination"},
        {"value": "CIF", "label": "CIF"},
        {"value": "To Pay", "label": "To Pay"},
        {"value": "Paid", "label": "Paid"}
    ],
    "unit_of_measure": [
        {"value": "Pcs", "label": "Pieces"},
        {"value": "Rolls", "label": "Rolls"},
        {"value": "Box", "label": "Box"},
        {"value": "Kg", "label": "Kilograms"},
        {"value": "Mtr", "label": "Meters"},
        {"value": "Sqm", "label": "Square Meters"},
        {"value": "Ltr", "label": "Liters"},
        {"value": "Nos", "label": "Numbers"}
    ],
    "tax_rate": [
        {"value": "0", "label": "0% (Exempt)"},
        {"value": "5", "label": "5%"},
        {"value": "12", "label": "12%"},
        {"value": "18", "label": "18%"},
        {"value": "28", "label": "28%"}
    ],
    "courier": [
        {"value": "DTDC", "label": "DTDC"},
        {"value": "BlueDart", "label": "BlueDart"},
        {"value": "Delhivery", "label": "Delhivery"},
        {"value": "FedEx", "label": "FedEx"},
        {"value": "DHL", "label": "DHL"},
        {"value": "Self", "label": "Self Delivery"},
        {"value": "Transport", "label": "Transport"}
    ],
    "sample_purpose": [
        {"value": "Trial", "label": "Trial"},
        {"value": "Evaluation", "label": "Evaluation"},
        {"value": "Quality Check", "label": "Quality Check"},
        {"value": "New Development", "label": "New Development"},
        {"value": "Replacement", "label": "Replacement"}
    ],
    "feedback_status": [
        {"value": "pending", "label": "Pending"},
        {"value": "positive", "label": "Positive"},
        {"value": "negative", "label": "Negative"},
        {"value": "needs_revision", "label": "Needs Revision"},
        {"value": "no_response", "label": "No Response"}
    ],
    "quotation_status": [
        {"value": "draft", "label": "Draft"},
        {"value": "sent", "label": "Sent"},
        {"value": "accepted", "label": "Accepted"},
        {"value": "rejected", "label": "Rejected"},
        {"value": "expired", "label": "Expired"},
        {"value": "revised", "label": "Revised"}
    ],
    "followup_type": [
        {"value": "Call", "label": "Phone Call"},
        {"value": "Email", "label": "Email"},
        {"value": "Meeting", "label": "Meeting"},
        {"value": "Visit", "label": "Site Visit"},
        {"value": "Sample", "label": "Send Sample"},
        {"value": "Quote", "label": "Send Quote"}
    ],
    "account_type": [
        {"value": "Customer", "label": "Customer"},
        {"value": "Prospect", "label": "Prospect"},
        {"value": "Partner", "label": "Partner"},
        {"value": "Vendor", "label": "Vendor"}
    ],
    "designation": [
        {"value": "Owner", "label": "Owner"},
        {"value": "Director", "label": "Director"},
        {"value": "CEO", "label": "CEO"},
        {"value": "Manager", "label": "Manager"},
        {"value": "Purchase Manager", "label": "Purchase Manager"},
        {"value": "Sales Manager", "label": "Sales Manager"},
        {"value": "Accounts Manager", "label": "Accounts Manager"},
        {"value": "Executive", "label": "Executive"},
        {"value": "Other", "label": "Other"}
    ]
}

# Indian States with GST codes
INDIAN_STATES = {
    "01": {"code": "JK", "name": "Jammu & Kashmir"},
    "02": {"code": "HP", "name": "Himachal Pradesh"},
    "03": {"code": "PB", "name": "Punjab"},
    "04": {"code": "CH", "name": "Chandigarh"},
    "05": {"code": "UK", "name": "Uttarakhand"},
    "06": {"code": "HR", "name": "Haryana"},
    "07": {"code": "DL", "name": "Delhi"},
    "08": {"code": "RJ", "name": "Rajasthan"},
    "09": {"code": "UP", "name": "Uttar Pradesh"},
    "10": {"code": "BR", "name": "Bihar"},
    "11": {"code": "SK", "name": "Sikkim"},
    "12": {"code": "AR", "name": "Arunachal Pradesh"},
    "13": {"code": "NL", "name": "Nagaland"},
    "14": {"code": "MN", "name": "Manipur"},
    "15": {"code": "MZ", "name": "Mizoram"},
    "16": {"code": "TR", "name": "Tripura"},
    "17": {"code": "ML", "name": "Meghalaya"},
    "18": {"code": "AS", "name": "Assam"},
    "19": {"code": "WB", "name": "West Bengal"},
    "20": {"code": "JH", "name": "Jharkhand"},
    "21": {"code": "OR", "name": "Odisha"},
    "22": {"code": "CT", "name": "Chhattisgarh"},
    "23": {"code": "MP", "name": "Madhya Pradesh"},
    "24": {"code": "GJ", "name": "Gujarat"},
    "25": {"code": "DD", "name": "Daman & Diu"},
    "26": {"code": "DN", "name": "Dadra & Nagar Haveli"},
    "27": {"code": "MH", "name": "Maharashtra"},
    "28": {"code": "AP", "name": "Andhra Pradesh"},
    "29": {"code": "KA", "name": "Karnataka"},
    "30": {"code": "GA", "name": "Goa"},
    "31": {"code": "LD", "name": "Lakshadweep"},
    "32": {"code": "KL", "name": "Kerala"},
    "33": {"code": "TN", "name": "Tamil Nadu"},
    "34": {"code": "PY", "name": "Puducherry"},
    "35": {"code": "AN", "name": "Andaman & Nicobar"},
    "36": {"code": "TG", "name": "Telangana"},
    "37": {"code": "AP", "name": "Andhra Pradesh (New)"},
    "38": {"code": "LA", "name": "Ladakh"}
}

# ==================== MASTER DATA ENDPOINTS ====================
@router.get("/categories")
async def get_all_categories(current_user: dict = Depends(get_current_user)):
    """Get list of all available master data categories"""
    return list(DEFAULT_CATEGORIES.keys())

@router.get("/category/{category}")
async def get_category_items(category: str, include_inactive: bool = False, current_user: dict = Depends(get_current_user)):
    """Get all items for a specific category"""
    query = {"category": category}
    if not include_inactive:
        query["is_active"] = True
    
    items = await db.master_data.find(query, {"_id": 0}).sort("sort_order", 1).to_list(1000)
    
    # If no custom items exist, return defaults
    if not items and category in DEFAULT_CATEGORIES:
        return DEFAULT_CATEGORIES[category]
    
    return items

@router.post("/category/{category}", response_model=MasterDataItem)
async def add_category_item(category: str, item_data: MasterDataCreate, current_user: dict = Depends(get_current_user)):
    """Add a new item to a category"""
    if current_user.get('role') not in ['admin', 'manager']:
        raise HTTPException(status_code=403, detail="Only admins and managers can modify master data")
    
    item_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    
    item_doc = {
        "id": item_id,
        "category": category,
        "value": item_data.value,
        "label": item_data.label,
        "is_active": True,
        "sort_order": item_data.sort_order,
        "metadata": item_data.metadata,
        "created_at": now,
        "updated_at": now
    }
    
    await db.master_data.insert_one(item_doc)
    return MasterDataItem(**{k: v for k, v in item_doc.items() if k != '_id'})

@router.put("/item/{item_id}", response_model=MasterDataItem)
async def update_category_item(item_id: str, item_data: MasterDataUpdate, current_user: dict = Depends(get_current_user)):
    """Update a master data item"""
    if current_user.get('role') not in ['admin', 'manager']:
        raise HTTPException(status_code=403, detail="Only admins and managers can modify master data")
    
    update_dict = {k: v for k, v in item_data.model_dump().items() if v is not None}
    update_dict["updated_at"] = datetime.now(timezone.utc).isoformat()
    
    result = await db.master_data.update_one({"id": item_id}, {"$set": update_dict})
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Item not found")
    
    item = await db.master_data.find_one({"id": item_id}, {"_id": 0})
    return MasterDataItem(**item)

@router.delete("/item/{item_id}")
async def delete_category_item(item_id: str, current_user: dict = Depends(get_current_user)):
    """Soft delete a master data item"""
    if current_user.get('role') not in ['admin', 'manager']:
        raise HTTPException(status_code=403, detail="Only admins and managers can modify master data")
    
    result = await db.master_data.update_one(
        {"id": item_id},
        {"$set": {"is_active": False, "updated_at": datetime.now(timezone.utc).isoformat()}}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Item not found")
    
    return {"message": "Item deactivated"}

@router.post("/initialize-defaults")
async def initialize_default_data(current_user: dict = Depends(get_current_user)):
    """Initialize default master data for all categories"""
    if current_user.get('role') != 'admin':
        raise HTTPException(status_code=403, detail="Only admins can initialize master data")
    
    now = datetime.now(timezone.utc).isoformat()
    inserted_count = 0
    
    for category, items in DEFAULT_CATEGORIES.items():
        # Check if category already has items
        existing = await db.master_data.count_documents({"category": category})
        if existing > 0:
            continue
        
        for idx, item in enumerate(items):
            item_doc = {
                "id": str(uuid.uuid4()),
                "category": category,
                "value": item["value"],
                "label": item["label"],
                "is_active": True,
                "sort_order": idx,
                "metadata": None,
                "created_at": now,
                "updated_at": now
            }
            await db.master_data.insert_one(item_doc)
            inserted_count += 1
    
    return {"message": f"Initialized {inserted_count} master data items"}

# ==================== NUMBER SERIES ENDPOINTS ====================
DEFAULT_NUMBER_SERIES = [
    {"document_type": "quotation", "prefix": "QT", "year_format": "YYYYMMDD", "padding": 6},
    {"document_type": "sales_order", "prefix": "SO", "year_format": "YYYYMMDD", "padding": 6},
    {"document_type": "invoice", "prefix": "INV", "year_format": "YYYYMM", "padding": 6},
    {"document_type": "sample", "prefix": "SMP", "year_format": "YYYYMMDD", "padding": 6},
    {"document_type": "lead", "prefix": "LD", "year_format": "YYYYMM", "padding": 6},
    {"document_type": "purchase_order", "prefix": "PO", "year_format": "YYYYMMDD", "padding": 6},
    {"document_type": "grn", "prefix": "GRN", "year_format": "YYYYMMDD", "padding": 6},
]

@router.get("/number-series")
async def get_all_number_series(current_user: dict = Depends(get_current_user)):
    """Get all number series configurations"""
    series = await db.number_series.find({}, {"_id": 0}).to_list(100)
    return series

@router.get("/number-series/{document_type}")
async def get_number_series(document_type: str, current_user: dict = Depends(get_current_user)):
    """Get number series for a specific document type"""
    series = await db.number_series.find_one({"document_type": document_type}, {"_id": 0})
    if not series:
        # Return default if not configured
        default = next((s for s in DEFAULT_NUMBER_SERIES if s["document_type"] == document_type), None)
        if default:
            return default
        raise HTTPException(status_code=404, detail="Number series not found")
    return series

@router.post("/number-series", response_model=NumberSeriesConfig)
async def create_number_series(series_data: NumberSeriesCreate, current_user: dict = Depends(get_current_user)):
    """Create or update a number series configuration"""
    if current_user.get('role') != 'admin':
        raise HTTPException(status_code=403, detail="Only admins can configure number series")
    
    now = datetime.now(timezone.utc).isoformat()
    
    # Check if exists
    existing = await db.number_series.find_one({"document_type": series_data.document_type})
    
    if existing:
        # Update existing
        update_data = series_data.model_dump()
        update_data["updated_at"] = now
        await db.number_series.update_one(
            {"document_type": series_data.document_type},
            {"$set": update_data}
        )
        series = await db.number_series.find_one({"document_type": series_data.document_type}, {"_id": 0})
    else:
        # Create new
        series_id = str(uuid.uuid4())
        series_doc = {
            "id": series_id,
            **series_data.model_dump(),
            "is_active": True,
            "created_at": now,
            "updated_at": now
        }
        await db.number_series.insert_one(series_doc)
        series = {k: v for k, v in series_doc.items() if k != '_id'}
    
    return NumberSeriesConfig(**series)

@router.post("/number-series/generate/{document_type}")
async def generate_next_number(document_type: str, current_user: dict = Depends(get_current_user)):
    """Generate the next number in a series"""
    series = await db.number_series.find_one({"document_type": document_type})
    
    if not series:
        # Use default config
        default = next((s for s in DEFAULT_NUMBER_SERIES if s["document_type"] == document_type), None)
        if not default:
            raise HTTPException(status_code=404, detail="Number series not configured")
        
        # Create the series
        now = datetime.now(timezone.utc).isoformat()
        series = {
            "id": str(uuid.uuid4()),
            **default,
            "separator": "-",
            "suffix": None,
            "current_number": 0,
            "reset_yearly": True,
            "reset_monthly": False,
            "is_active": True,
            "created_at": now,
            "updated_at": now
        }
        await db.number_series.insert_one(series)
    
    # Generate number
    now = datetime.now(timezone.utc)
    prefix = series.get("prefix", "")
    separator = series.get("separator", "-")
    suffix = series.get("suffix", "")
    padding = series.get("padding", 6)
    year_format = series.get("year_format", "YYYY")
    
    # Format date part
    date_formats = {
        "YYYY": now.strftime("%Y"),
        "YY": now.strftime("%y"),
        "YYYYMM": now.strftime("%Y%m"),
        "YYMM": now.strftime("%y%m"),
        "YYYYMMDD": now.strftime("%Y%m%d")
    }
    date_part = date_formats.get(year_format, now.strftime("%Y%m%d"))
    
    # Increment number
    new_number = series.get("current_number", 0) + 1
    
    # Update series
    await db.number_series.update_one(
        {"document_type": document_type},
        {"$set": {"current_number": new_number, "updated_at": now.isoformat()}}
    )
    
    # Build final number
    number_part = str(new_number).zfill(padding) if padding > 0 else str(uuid.uuid4())[:6].upper()
    
    parts = [prefix, date_part, number_part]
    if suffix:
        parts.append(suffix)
    
    generated_number = separator.join(filter(None, parts))
    
    return {"number": generated_number, "sequence": new_number}

@router.post("/number-series/initialize")
async def initialize_number_series(current_user: dict = Depends(get_current_user)):
    """Initialize default number series configurations"""
    if current_user.get('role') != 'admin':
        raise HTTPException(status_code=403, detail="Only admins can initialize number series")
    
    now = datetime.now(timezone.utc).isoformat()
    inserted_count = 0
    
    for series in DEFAULT_NUMBER_SERIES:
        existing = await db.number_series.find_one({"document_type": series["document_type"]})
        if existing:
            continue
        
        series_doc = {
            "id": str(uuid.uuid4()),
            **series,
            "separator": "-",
            "suffix": None,
            "current_number": 0,
            "reset_yearly": True,
            "reset_monthly": False,
            "is_active": True,
            "created_at": now,
            "updated_at": now
        }
        await db.number_series.insert_one(series_doc)
        inserted_count += 1
    
    return {"message": f"Initialized {inserted_count} number series"}

# ==================== GST UTILITIES ====================
@router.get("/states")
async def get_indian_states(current_user: dict = Depends(get_current_user)):
    """Get list of Indian states with GST codes"""
    return INDIAN_STATES

@router.get("/gst/validate/{gstin}")
async def validate_gstin(gstin: str, current_user: dict = Depends(get_current_user)):
    """Validate GSTIN format and extract information"""
    gstin = gstin.upper().strip()
    
    # GSTIN format: 2 digits state code + 10 char PAN + 1 entity code + 1 check digit + Z
    if len(gstin) != 15:
        return {"valid": False, "error": "GSTIN must be 15 characters"}
    
    # Extract state code
    state_code = gstin[:2]
    if state_code not in INDIAN_STATES:
        return {"valid": False, "error": "Invalid state code"}
    
    # Extract PAN
    pan = gstin[2:12]
    
    # Basic PAN format validation (5 letters + 4 digits + 1 letter)
    import re
    pan_pattern = r'^[A-Z]{5}[0-9]{4}[A-Z]{1}$'
    if not re.match(pan_pattern, pan):
        return {"valid": False, "error": "Invalid PAN format in GSTIN"}
    
    # Entity code (13th character)
    entity_code = gstin[12]
    entity_types = {
        "1": "Proprietorship",
        "2": "Partnership",
        "3": "Company",
        "4": "Trust",
        "5": "Society",
        "6": "Government",
        "7": "Local Authority",
        "9": "Foreign Company",
        "Z": "Default"
    }
    entity_type = entity_types.get(entity_code, "Unknown")
    
    # Get state info
    state_info = INDIAN_STATES.get(state_code, {})
    
    return {
        "valid": True,
        "gstin": gstin,
        "state_code": state_code,
        "state_name": state_info.get("name", "Unknown"),
        "state_abbr": state_info.get("code", ""),
        "pan": pan,
        "entity_code": entity_code,
        "entity_type": entity_type,
        "message": "GSTIN format is valid. For full verification, integrate with GST portal API."
    }

@router.get("/gst/lookup/{gstin}")
async def lookup_gstin(gstin: str, current_user: dict = Depends(get_current_user)):
    """
    Lookup GSTIN details. 
    Currently returns validated format info + state details.
    Can be extended to integrate with paid GST APIs (Cashfree, ClearTax, etc.)
    """
    # First validate
    validation = await validate_gstin(gstin, current_user)
    if not validation.get("valid"):
        raise HTTPException(status_code=400, detail=validation.get("error", "Invalid GSTIN"))
    
    # For now, return extracted information
    # TODO: Integrate with paid GST API for full details
    return {
        "gstin": validation["gstin"],
        "state": validation["state_name"],
        "state_code": validation["state_code"],
        "pan": validation["pan"],
        "entity_type": validation["entity_type"],
        "registration_status": "Active",  # Would come from API
        "business_name": None,  # Would come from API
        "trade_name": None,  # Would come from API
        "address": None,  # Would come from API
        "note": "Full business details require GST portal API integration. Contact admin to enable."
    }
