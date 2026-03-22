from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone, timedelta
import uuid
import re
from server import db, get_current_user

router = APIRouter()

import httpx

# ==================== GEO HELPERS (PINCODE / STATES) ====================
INDIA_STATES_UT = [
    "Andhra Pradesh", "Arunachal Pradesh", "Assam", "Bihar", "Chhattisgarh", "Goa",
    "Gujarat", "Haryana", "Himachal Pradesh", "Jharkhand", "Karnataka", "Kerala",
    "Madhya Pradesh", "Maharashtra", "Manipur", "Meghalaya", "Mizoram", "Nagaland",
    "Odisha", "Punjab", "Rajasthan", "Sikkim", "Tamil Nadu", "Telangana", "Tripura",
    "Uttar Pradesh", "Uttarakhand", "West Bengal",
    "Andaman and Nicobar Islands", "Chandigarh", "Dadra and Nagar Haveli and Daman and Diu",
    "Delhi", "Jammu and Kashmir", "Ladakh", "Lakshadweep", "Puducherry"
]

PINCODE_API_BASE = "https://api.postalpincode.in/pincode/"
COUNTRIESNOW_STATES_API = "https://countriesnow.space/api/v0.1/countries/states"

async def lookup_india_pincode(pincode: str) -> Optional[dict]:
    """Return {city, district, state, country} for India PIN (6 digits)"""
    if not pincode or len(pincode) != 6 or not pincode.isdigit():
        return None

    async with httpx.AsyncClient(timeout=10.0, headers={"User-Agent": "adhesive-erp"}) as client:
        resp = await client.get(f"{PINCODE_API_BASE}{pincode}")
        if resp.status_code != 200:
            return None
        data = resp.json()

    # Expected: list with one element
    if not isinstance(data, list) or not data:
        return None
    entry = data[0]
    if entry.get("Status") != "Success":
        return None

    offices = entry.get("PostOffice") or []
    if not offices:
        return None

    po = offices[0]
    return {
        "country": "India",
        "state": po.get("State"),
        "district": po.get("District"),
        "city": po.get("Block") or po.get("Region") or po.get("Taluk")
    }

async def lookup_states_for_country(country_name: str) -> List[str]:
    """Free public API to get list of states/provinces for a country (no key)."""
    if not country_name:
        return []
    if country_name.strip().lower() in ["india", "bharat", "in"]:
        return INDIA_STATES_UT

    payload = {"country": country_name}
    async with httpx.AsyncClient(timeout=15.0, headers={"User-Agent": "adhesive-erp"}, follow_redirects=True) as client:
        resp = await client.post(COUNTRIESNOW_STATES_API, json=payload)
        if resp.status_code != 200:
            return []
        data = resp.json()

    states = []
    for s in (data.get("data", {}).get("states") or []):
        name = s.get("name")
        if name:
            states.append(name)
    return states

# ==================== PERMISSION HELPER ====================
async def get_data_filter(current_user: dict, module: str) -> dict:
    """Build query filter based on user's data access permissions"""
    user_id = current_user.get('id')
    role = current_user.get('role', 'viewer')
    
    # Admin sees everything
    if role == 'admin':
        return {}

    # CRM Leads hierarchy rule (requested): assigned salesperson + team leader + sales manager
    if module == "crm_leads":
        if role == "sales_manager":
            return {}

        if role == "sales_team_leader":
            reports = await db.users.find({"reports_to": user_id}, {"id": 1, "_id": 0}).to_list(1000)
            team_user_ids = [u.get("id") for u in reports if u.get("id")]
            team_user_ids.append(user_id)
            return {"$or": [
                {"assigned_to": {"$in": team_user_ids}},
                {"assigned_to": {"$in": [None, ""]}, "created_by": {"$in": team_user_ids}}
            ]}

        if role == "salesperson":
            return {"$or": [
                {"assigned_to": user_id},
                {"assigned_to": {"$in": [None, ""]}, "created_by": user_id}
            ]}

        # Default: if user isn't in sales hierarchy, show only own/assigned
        return {"$or": [
            {"assigned_to": user_id},
            {"assigned_to": {"$in": [None, ""]}, "created_by": user_id}
        ]}
    
    # Check user's custom access config
    access = await db.user_access.find_one({"user_id": user_id}, {"_id": 0})
    
    if access:
        access_level = access.get("data_access_level", "own")
        
        if access_level == "all":
            return {}
        elif access_level == "location":
            locations = access.get("assigned_locations", [])
            if locations:
                return {"$or": [
                    {"created_by": user_id},
                    {"assigned_to": user_id},
                    {"location": {"$in": locations}}
                ]}
        elif access_level == "team":
            # Get team members
            teams = access.get("assigned_teams", [])
            if teams:
                team_users = await db.users.find({"team": {"$in": teams}}, {"id": 1}).to_list(100)
                team_user_ids = [u["id"] for u in team_users]
                team_user_ids.append(user_id)
                return {"$or": [
                    {"created_by": {"$in": team_user_ids}},
                    {"assigned_to": {"$in": team_user_ids}}
                ]}
    
    # Default: user sees only their own data
    return {"$or": [
        {"created_by": user_id},
        {"assigned_to": user_id}
    ]}

# ==================== GST VALIDATION HELPER ====================
INDIAN_STATES = {
    "01": "Jammu & Kashmir", "02": "Himachal Pradesh", "03": "Punjab",
    "04": "Chandigarh", "05": "Uttarakhand", "06": "Haryana", "07": "Delhi",
    "08": "Rajasthan", "09": "Uttar Pradesh", "10": "Bihar", "11": "Sikkim",
    "12": "Arunachal Pradesh", "13": "Nagaland", "14": "Manipur", "15": "Mizoram",
    "16": "Tripura", "17": "Meghalaya", "18": "Assam", "19": "West Bengal",
    "20": "Jharkhand", "21": "Odisha", "22": "Chhattisgarh", "23": "Madhya Pradesh",
    "24": "Gujarat", "25": "Daman & Diu", "26": "Dadra & Nagar Haveli",
    "27": "Maharashtra", "28": "Andhra Pradesh", "29": "Karnataka", "30": "Goa",
    "31": "Lakshadweep", "32": "Kerala", "33": "Tamil Nadu", "34": "Puducherry",
    "35": "Andaman & Nicobar", "36": "Telangana", "37": "Andhra Pradesh (New)", "38": "Ladakh"
}

def validate_and_parse_gstin(gstin: str) -> dict:
    """Validate GSTIN format and extract state info"""
    gstin = gstin.upper().strip()
    
    if len(gstin) != 15:
        return {"valid": False, "error": "GSTIN must be 15 characters"}
    
    state_code = gstin[:2]
    if state_code not in INDIAN_STATES:
        return {"valid": False, "error": "Invalid state code"}
    
    pan = gstin[2:12]
    pan_pattern = r'^[A-Z]{5}[0-9]{4}[A-Z]{1}$'
    if not re.match(pan_pattern, pan):
        return {"valid": False, "error": "Invalid PAN format in GSTIN"}
    
    return {
        "valid": True,
        "state_code": state_code,
        "state_name": INDIAN_STATES.get(state_code, "Unknown"),
        "pan": pan
    }

# ==================== LEAD MODELS ====================
class LeadCreate(BaseModel):
    company_name: str
    contact_person: str
    email: str
    phone: str
    mobile: Optional[str] = None

    # Address
    address: Optional[str] = None
    country: str = "India"
    state: Optional[str] = None
    district: Optional[str] = None
    city: Optional[str] = None
    pincode: Optional[str] = None

    # Classification
    pipeline: str = "main"
    customer_type: Optional[str] = None

    # Stage
    status: Optional[str] = None

    source: str
    industry: Optional[str] = None
    product_interest: Optional[str] = None
    estimated_value: Optional[float] = None
    notes: Optional[str] = None
    assigned_to: Optional[str] = None
    next_followup_date: Optional[str] = None
    followup_activity: Optional[str] = None

class LeadUpdate(BaseModel):
    company_name: Optional[str] = None
    contact_person: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    mobile: Optional[str] = None

    address: Optional[str] = None
    country: Optional[str] = None
    state: Optional[str] = None
    district: Optional[str] = None
    city: Optional[str] = None
    pincode: Optional[str] = None

    pipeline: Optional[str] = None
    customer_type: Optional[str] = None

    source: Optional[str] = None
    industry: Optional[str] = None
    product_interest: Optional[str] = None
    estimated_value: Optional[float] = None
    notes: Optional[str] = None
    status: Optional[str] = None
    assigned_to: Optional[str] = None
    next_followup_date: Optional[str] = None
    followup_activity: Optional[str] = None
    lead_score: Optional[int] = None

class Lead(BaseModel):
    id: str
    company_name: str
    contact_person: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    mobile: Optional[str] = None

    address: Optional[str] = None
    country: Optional[str] = "India"
    state: Optional[str] = None
    district: Optional[str] = None
    city: Optional[str] = None
    pincode: Optional[str] = None

    pipeline: Optional[str] = "main"
    customer_type: Optional[str] = None

    source: Optional[str] = None
    industry: Optional[str] = None
    status: Optional[str] = "new"
    product_interest: Optional[str] = None
    estimated_value: Optional[float] = None
    notes: Optional[str] = None
    assigned_to: Optional[str] = None
    next_followup_date: Optional[str] = None
    followup_activity: Optional[str] = None
    lead_score: Optional[int] = 0
    last_contacted: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    created_by: Optional[str] = None
    updated_by: Optional[str] = None

# ==================== ACCOUNT MODELS ====================
class ContactPerson(BaseModel):
    name: str
    designation: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    mobile: Optional[str] = None
    is_primary: bool = False

class ShippingAddress(BaseModel):
    label: str = "Default"
    address: str
    city: str
    state: str
    pincode: str
    country: str = "India"

class AccountCreate(BaseModel):
    customer_name: str
    account_type: str = "Customer"
    gstin: Optional[str] = None
    pan: Optional[str] = None
    billing_address: Optional[str] = None
    billing_city: Optional[str] = None
    billing_state: Optional[str] = None
    billing_pincode: Optional[str] = None
    shipping_addresses: List[ShippingAddress] = []
    contacts: List[ContactPerson] = []
    credit_limit: float = 0
    credit_days: int = 30
    credit_control: str = "Warn"
    billing_country: str = "India"
    billing_district: Optional[str] = None

    payment_terms: str = "30 days"
    industry: Optional[str] = None
    website: Optional[str] = None
    agent_id: Optional[str] = None
    salesperson_id: Optional[str] = None
    location: Optional[str] = None
    notes: Optional[str] = None

class AccountUpdate(BaseModel):
    customer_name: Optional[str] = None
    account_type: Optional[str] = None
    gstin: Optional[str] = None
    pan: Optional[str] = None
    billing_address: Optional[str] = None
    billing_city: Optional[str] = None
    billing_state: Optional[str] = None
    billing_pincode: Optional[str] = None
    billing_country: Optional[str] = None
    billing_district: Optional[str] = None

    shipping_addresses: Optional[List[ShippingAddress]] = None
    contacts: Optional[List[ContactPerson]] = None
    credit_limit: Optional[float] = None
    credit_days: Optional[int] = None
    credit_control: Optional[str] = None
    payment_terms: Optional[str] = None
    industry: Optional[str] = None
    website: Optional[str] = None
    agent_id: Optional[str] = None
    salesperson_id: Optional[str] = None
    location: Optional[str] = None
    notes: Optional[str] = None
    is_active: Optional[bool] = None

class Account(BaseModel):
    id: str
    customer_name: Optional[str] = None
    account_type: Optional[str] = "customer"
    gstin: Optional[str] = None
    pan: Optional[str] = None
    billing_address: Optional[str] = None
    billing_country: Optional[str] = "India"
    billing_district: Optional[str] = None
    billing_city: Optional[str] = None
    billing_state: Optional[str] = None
    billing_pincode: Optional[str] = None
    shipping_addresses: Optional[List[dict]] = []
    contacts: Optional[List[dict]] = []
    contact_persons: Optional[List[dict]] = None
    credit_limit: Optional[float] = 0
    credit_days: Optional[int] = 30
    credit_control: Optional[str] = "warning"
    payment_terms: Optional[str] = None
    industry: Optional[str] = None
    website: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    mobile: Optional[str] = None
    agent_id: Optional[str] = None
    salesperson_id: Optional[str] = None
    salesperson_name: Optional[str] = None
    location: Optional[str] = None
    notes: Optional[str] = None
    is_active: Optional[bool] = True
    total_outstanding: Optional[float] = 0
    receivable_amount: Optional[float] = 0
    payable_amount: Optional[float] = 0
    avg_payment_days: Optional[float] = 0
    opening_balance: Optional[float] = 0
    lead_id: Optional[str] = None
    created_by: Optional[str] = None
    assigned_to: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

# ==================== QUOTATION MODELS ====================
class QuotationItem(BaseModel):
    item_id: Optional[str] = None
    item_name: str
    description: Optional[str] = None
    hsn_code: Optional[str] = None
    quantity: float
    unit: str = "Pcs"
    unit_price: float
    discount_percent: float = 0
    tax_percent: float = 18
    line_total: Optional[float] = None

class QuotationCreate(BaseModel):
    account_id: str
    contact_person: Optional[str] = None
    salesperson_id: Optional[str] = None
    reference: Optional[str] = None
    valid_until: str
    items: List[QuotationItem]
    transport: Optional[str] = None
    delivery_terms: Optional[str] = None
    payment_terms: Optional[str] = None
    terms_conditions: Optional[str] = None
    notes: Optional[str] = None
    header_discount_percent: float = 0

class QuotationUpdate(BaseModel):
    contact_person: Optional[str] = None
    salesperson_id: Optional[str] = None
    reference: Optional[str] = None
    valid_until: Optional[str] = None
    items: Optional[List[QuotationItem]] = None
    transport: Optional[str] = None
    delivery_terms: Optional[str] = None
    payment_terms: Optional[str] = None
    terms_conditions: Optional[str] = None
    notes: Optional[str] = None
    header_discount_percent: Optional[float] = None
    status: Optional[str] = None

class Quotation(BaseModel):
    id: str
    quote_number: str
    account_id: str
    account_name: Optional[str] = None
    contact_person: Optional[str] = None
    salesperson_id: Optional[str] = None
    reference: Optional[str] = None
    quote_date: str
    valid_until: str
    items: List[dict]
    subtotal: float
    header_discount_percent: float
    header_discount_amount: float
    taxable_amount: float
    cgst_amount: float
    sgst_amount: float
    igst_amount: float
    total_tax: float
    grand_total: float
    transport: Optional[str] = None
    delivery_terms: Optional[str] = None
    payment_terms: Optional[str] = None
    terms_conditions: Optional[str] = None
    notes: Optional[str] = None
    status: str
    converted_to_order: bool = False
    order_id: Optional[str] = None
    created_by: str
    created_at: str
    updated_at: Optional[str] = None

# ==================== GEO ENDPOINTS ====================
@router.get("/geo/india/states")
async def get_india_states(current_user: dict = Depends(get_current_user)):
    return {"country": "India", "states": INDIA_STATES_UT}

@router.get("/geo/states")
async def get_states(country: str, current_user: dict = Depends(get_current_user)):
    states = await lookup_states_for_country(country)
    return {"country": country, "states": states}

@router.get("/geo/pincode/{pincode}")
async def get_pincode_details(pincode: str, current_user: dict = Depends(get_current_user)):
    details = await lookup_india_pincode(pincode)
    if not details:
        raise HTTPException(status_code=404, detail="Pincode not found")
    return details


# ==================== CRM USERS (for assignment) ====================
@router.get("/users/sales")
async def get_sales_users(current_user: dict = Depends(get_current_user)):
    """Users eligible for lead assignment (sales roles)."""
    roles = ["salesperson", "sales_team_leader", "sales_manager", "admin"]
    users = await db.users.find({"role": {"$in": roles}}, {"_id": 0, "password": 0}).sort("name", 1).to_list(1000)
    return [{"id": u.get("id"), "name": u.get("name"), "email": u.get("email"), "role": u.get("role"), "team": u.get("team"), "reports_to": u.get("reports_to")} for u in users]


# ==================== SAMPLE MODELS ====================
class SampleItem(BaseModel):
    product_name: str
    product_specs: str
    quantity: float
    unit: str = "Pcs"


class SampleCreate(BaseModel):
    account_id: str
    contact_person: Optional[str] = None
    quotation_id: Optional[str] = None

    # Multi-item (requested)
    items: List[SampleItem]

    from_location: str
    courier: Optional[str] = None
    tracking_number: Optional[str] = None
    expected_delivery: Optional[str] = None
    feedback_due_date: str
    purpose: Optional[str] = None
    notes: Optional[str] = None


class SampleUpdate(BaseModel):
    contact_person: Optional[str] = None
    quotation_id: Optional[str] = None

    items: Optional[List[SampleItem]] = None

    from_location: Optional[str] = None
    courier: Optional[str] = None
    tracking_number: Optional[str] = None
    expected_delivery: Optional[str] = None
    feedback_due_date: Optional[str] = None
    purpose: Optional[str] = None
    notes: Optional[str] = None
    status: Optional[str] = None
    feedback_status: Optional[str] = None
    feedback_notes: Optional[str] = None
    feedback_date: Optional[str] = None
    return_date: Optional[str] = None
    return_condition: Optional[str] = None


class Sample(BaseModel):
    id: str
    sample_number: str
    account_id: str
    account_name: Optional[str] = None
    contact_person: Optional[str] = None
    quotation_id: Optional[str] = None

    items: Optional[List[dict]] = []

    from_location: str
    courier: Optional[str] = None
    tracking_number: Optional[str] = None
    expected_delivery: Optional[str] = None
    feedback_due_date: str
    purpose: Optional[str] = None
    notes: Optional[str] = None
    status: str
    feedback_status: str
    feedback_notes: Optional[str] = None
    feedback_date: Optional[str] = None
    return_date: Optional[str] = None
    return_condition: Optional[str] = None
    estimated_cost: float = 0
    sent_by: str
    created_at: str
    updated_at: Optional[str] = None

# ==================== FOLLOWUP MODELS ====================
class FollowupCreate(BaseModel):
    entity_type: str  # lead, account, quotation, sample
    entity_id: str
    followup_type: str  # call, email, meeting, visit
    scheduled_date: str
    notes: Optional[str] = None
    assigned_to: Optional[str] = None

class Followup(BaseModel):
    id: str
    entity_type: str
    entity_id: str
    followup_type: str
    scheduled_date: str
    completed_date: Optional[str] = None
    notes: Optional[str] = None
    outcome: Optional[str] = None
    assigned_to: Optional[str] = None
    status: str
    created_by: str
    created_at: str

# ==================== LEAD ENDPOINTS ====================
@router.post("/leads", response_model=Lead)
async def create_lead(lead_data: LeadCreate, current_user: dict = Depends(get_current_user)):
    lead_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()

    lead_payload = lead_data.model_dump()

    # Normalize assignment
    if lead_payload.get('assigned_to') in ['', 'unassigned']:
        lead_payload['assigned_to'] = None

    # If India PIN is provided, auto-fill geo fields
    if (lead_payload.get('country') or 'India').strip().lower() == 'india' and lead_payload.get('pincode'):
        geo = await lookup_india_pincode(lead_payload.get('pincode'))
        if geo:
            lead_payload['country'] = geo.get('country') or lead_payload.get('country')
            lead_payload['state'] = geo.get('state') or lead_payload.get('state')
            lead_payload['district'] = geo.get('district') or lead_payload.get('district')
            lead_payload['city'] = geo.get('city') or lead_payload.get('city')

    lead_doc = {
        'id': lead_id,
        **lead_payload,
        'status': lead_payload.get('status') or 'new',
        'lead_score': 0,
        'last_contacted': None,
        'created_by': current_user['id'],
        'created_at': now,
        'updated_at': now
    }

    await db.leads.insert_one(lead_doc)
    return Lead(**{k: v for k, v in lead_doc.items() if k != '_id'})

@router.get("/leads", response_model=List[Lead])
async def get_leads(
    source: Optional[str] = None, 
    status: Optional[str] = None,
    assigned_to: Optional[str] = None,
    industry: Optional[str] = None,
    city: Optional[str] = None,
    state: Optional[str] = None,
    search: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    # Apply permission-based filtering
    base_filter = await get_data_filter(current_user, "crm_leads")
    query = {**base_filter} if base_filter else {}
    
    if source:
        query['source'] = source
    if status:
        query['status'] = status
    if assigned_to:
        query['assigned_to'] = assigned_to
    if industry:
        query['industry'] = industry
    if city:
        query['city'] = {"$regex": city, "$options": "i"}
    if state:
        query['state'] = {"$regex": state, "$options": "i"}
    if search:
        query['$or'] = [
            {'company_name': {"$regex": search, "$options": "i"}},
            {'contact_person': {"$regex": search, "$options": "i"}},
            {'email': {"$regex": search, "$options": "i"}},
            {'phone': {"$regex": search, "$options": "i"}}
        ]
    if date_from:
        query['created_at'] = {"$gte": date_from}
    if date_to:
        if 'created_at' in query:
            query['created_at']['$lte'] = date_to
        else:
            query['created_at'] = {"$lte": date_to}

    leads = await db.leads.find(query, {'_id': 0}).sort('created_at', -1).to_list(1000)
    return [Lead(**lead) for lead in leads]

@router.post("/leads/{lead_id}/create-quotation")
async def create_quotation_from_lead(lead_id: str, current_user: dict = Depends(get_current_user)):
    """Create a draft quotation from a lead (intended when lead is in Proposal stage)."""
    lead = await db.leads.find_one({'id': lead_id}, {'_id': 0})
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    # Permission check: lead must be visible to user
    base_filter = await get_data_filter(current_user, "crm_leads")
    if base_filter:
        visible = await db.leads.find_one({"id": lead_id, **base_filter}, {"_id": 0})
        if not visible:
            raise HTTPException(status_code=403, detail="Access denied")

    # Enforce stage check
    if lead.get('status') != 'proposal':
        raise HTTPException(status_code=400, detail="Quotation can be created only when lead is in Proposal stage")

    # Ensure an Account exists (create one if absent)
    account_id = lead.get('account_id')
    if account_id:
        account = await db.accounts.find_one({'id': account_id}, {'_id': 0})
    else:
        account = None

    if not account:
        # Create minimal account from lead
        account_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        account_doc = {
            'id': account_id,
            'customer_name': lead.get('company_name'),
            'account_type': 'Customer',
            'gstin': 'NA',
            'pan': None,
            'billing_address': lead.get('address') or '',
            'billing_city': lead.get('city'),
            'billing_state': lead.get('state'),
            'billing_pincode': lead.get('pincode'),
            'shipping_addresses': [],
            'contacts': [{
                'name': lead.get('contact_person'),
                'designation': None,
                'email': lead.get('email'),
                'phone': lead.get('phone'),
                'mobile': lead.get('mobile'),
                'is_primary': True
            }],
            'credit_limit': 0,
            'credit_days': 30,
            'credit_control': 'Warn',
            'payment_terms': '30 days',
            'industry': lead.get('industry'),
            'website': None,
            'agent_id': None,
            'salesperson_id': lead.get('assigned_to') or None,
            'salesperson_name': None,
            'location': None,
            'notes': f"Auto-created from Lead {lead_id}",
            'is_active': True,
            'total_outstanding': 0,
            'receivable_amount': 0,
            'payable_amount': 0,
            'avg_payment_days': 0,
            'lead_id': lead_id,
            'created_by': current_user['id'],
            'assigned_to': lead.get('assigned_to') or current_user['id'],
            'created_at': now,
            'updated_at': now
        }
        await db.accounts.insert_one(account_doc)
        await db.leads.update_one({'id': lead_id}, {'$set': {'account_id': account_id, 'updated_at': now}})
        account = account_doc

    # Create draft quotation with prefilled contact person + reference
    quote_id = str(uuid.uuid4())
    now_dt = datetime.now(timezone.utc)
    quote_number = f"QT-{now_dt.strftime('%Y%m%d')}-{str(uuid.uuid4())[:6].upper()}"

    # Empty items; user will fill in UI
    items_dict = [{
        'item_id': None,
        'item_name': '---',
        'description': lead.get('product_interest'),
        'hsn_code': None,
        'quantity': 1,
        'unit': 'Pcs',
        'unit_price': 0,
        'discount_percent': 0,
        'tax_percent': 18,
        'line_total': 0
    }]
    totals = calculate_quotation_totals(items_dict, 0)

    quote_doc = {
        'id': quote_id,
        'quote_number': quote_number,
        'account_id': account_id,
        'account_name': account.get('customer_name'),
        'contact_person': lead.get('contact_person'),
        'salesperson_id': lead.get('assigned_to'),
        'reference': f"Lead: {lead_id}",
        'quote_date': now_dt.isoformat(),
        'valid_until': (now_dt + timedelta(days=15)).date().isoformat(),
        **totals,
        'transport': None,
        'delivery_terms': None,
        'payment_terms': account.get('payment_terms'),
        'terms_conditions': None,
        'notes': lead.get('notes'),
        'status': 'draft',
        'converted_to_order': False,
        'order_id': None,
        'created_by': current_user['id'],
        'created_at': now_dt.isoformat(),
        'updated_at': now_dt.isoformat()
    }

    await db.quotations.insert_one(quote_doc)
    return {'message': 'Quotation created from lead', 'quotation_id': quote_id, 'quote_number': quote_number}

@router.get("/leads/kanban/view")
async def get_leads_kanban(current_user: dict = Depends(get_current_user)):
    """Get leads organized by status for Kanban view"""
    base_filter = await get_data_filter(current_user, "crm_leads")
    
    # Try to get stages from Field Registry first
    field_config = await db.field_configurations.find_one(
        {'module': 'crm', 'entity': 'leads'},
        {'_id': 0}
    )
    
    # Use Field Registry stages if available, otherwise fall back to defaults
    if field_config and field_config.get('kanban_stages'):
        statuses = [s.get('value') for s in field_config.get('kanban_stages', []) if s.get('value')]
    else:
        statuses = ['new', 'hot_leads', 'cold_leads', 'contacted', 'qualified', 'proposal', 'negotiation', 'converted', 'customer', 'lost']
    
    # Always include 'new' as a fallback for legacy leads
    if 'new' not in statuses:
        statuses = ['new'] + statuses
    
    kanban_data = {}
    for status in statuses:
        query = {**base_filter, 'status': status} if base_filter else {'status': status}
        leads = await db.leads.find(query, {'_id': 0}).sort('updated_at', -1).to_list(100)
        kanban_data[status] = leads
    
    # Get status counts
    counts = {}
    for status in statuses:
        query = {**base_filter, 'status': status} if base_filter else {'status': status}
        counts[status] = await db.leads.count_documents(query)
    
    return {
        'columns': statuses,
        'statuses': statuses,
        'data': kanban_data,
        'counts': counts
    }

@router.get("/leads/{lead_id}", response_model=Lead)
async def get_lead(lead_id: str, current_user: dict = Depends(get_current_user)):
    base_filter = await get_data_filter(current_user, "crm_leads")
    query = {"id": lead_id, **base_filter} if base_filter else {"id": lead_id}
    lead = await db.leads.find_one(query, {'_id': 0})
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    return Lead(**lead)

@router.put("/leads/{lead_id}", response_model=Lead)
async def update_lead(lead_id: str, lead_data: LeadUpdate, current_user: dict = Depends(get_current_user)):
    base_filter = await get_data_filter(current_user, "crm_leads")
    query = {"id": lead_id, **base_filter} if base_filter else {"id": lead_id}
    existing = await db.leads.find_one(query, {'_id': 0})
    if not existing:
        raise HTTPException(status_code=404, detail="Lead not found")

    update_dict = {k: v for k, v in lead_data.model_dump().items() if v is not None}

    # Normalize assignment
    if update_dict.get('assigned_to') in ['', 'unassigned']:
        update_dict['assigned_to'] = None

    update_dict['updated_at'] = datetime.now(timezone.utc).isoformat()

    # If India PIN is provided/changed, auto-fill geo fields
    if (update_dict.get('country') or 'India').strip().lower() == 'india' and update_dict.get('pincode'):
        geo = await lookup_india_pincode(update_dict.get('pincode'))
        if geo:
            update_dict['country'] = geo.get('country') or update_dict.get('country')
            update_dict['state'] = geo.get('state') or update_dict.get('state')
            update_dict['district'] = geo.get('district') or update_dict.get('district')
            update_dict['city'] = geo.get('city') or update_dict.get('city')

    result = await db.leads.update_one(
        {'id': lead_id},
        {'$set': update_dict}
    )

    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Lead not found")

    lead = await db.leads.find_one({'id': lead_id}, {'_id': 0})
    return Lead(**lead)

@router.delete("/leads/{lead_id}")
async def delete_lead(lead_id: str, current_user: dict = Depends(get_current_user)):
    base_filter = await get_data_filter(current_user, "crm_leads")
    query = {"id": lead_id, **base_filter} if base_filter else {"id": lead_id}

    lead = await db.leads.find_one(query, {'_id': 0})
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    result = await db.leads.delete_one({'id': lead_id})

    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Lead not found")

    return {'message': 'Lead deleted successfully'}

@router.put("/leads/{lead_id}/contact")
async def mark_lead_contacted(lead_id: str, notes: Optional[str] = None, current_user: dict = Depends(get_current_user)):
    now = datetime.now(timezone.utc).isoformat()
    update_data = {
        'last_contacted': now,
        'updated_at': now
    }
    if notes:
        update_data['notes'] = notes
    
    result = await db.leads.update_one(
        {'id': lead_id},
        {'$set': update_data, '$inc': {'lead_score': 5}}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Lead not found")
    
    return {'message': 'Lead marked as contacted'}

@router.put("/leads/{lead_id}/move")
async def move_lead_status(lead_id: str, new_status: str, current_user: dict = Depends(get_current_user)):
    """Move lead to a new status (for Kanban drag-drop)"""
    valid_statuses = ['new', 'contacted', 'qualified', 'proposal', 'negotiation', 'converted', 'lost']
    if new_status not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of: {valid_statuses}")
    
    now = datetime.now(timezone.utc).isoformat()
    result = await db.leads.update_one(
        {'id': lead_id},
        {'$set': {'status': new_status, 'updated_at': now}}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Lead not found")
    
    return {'message': f'Lead moved to {new_status}'}

@router.put("/leads/{lead_id}/convert")
async def convert_lead_to_account(lead_id: str, account_data: AccountCreate, current_user: dict = Depends(get_current_user)):
    lead = await db.leads.find_one({'id': lead_id}, {'_id': 0})
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    
    if lead.get('status') == 'converted':
        raise HTTPException(status_code=400, detail="Lead already converted")
    
    account_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    
    account_doc = {
        'id': account_id,
        **account_data.model_dump(),
        'lead_id': lead_id,
        'is_active': True,
        'total_outstanding': 0,
        'created_at': now,
        'updated_at': now
    }
    
    # Convert ShippingAddress and ContactPerson to dict
    account_doc['shipping_addresses'] = [addr.model_dump() if hasattr(addr, 'model_dump') else addr for addr in account_doc.get('shipping_addresses', [])]
    account_doc['contacts'] = [c.model_dump() if hasattr(c, 'model_dump') else c for c in account_doc.get('contacts', [])]
    
    await db.accounts.insert_one(account_doc)
    await db.leads.update_one(
        {'id': lead_id}, 
        {'$set': {'status': 'converted', 'account_id': account_id, 'updated_at': now}}
    )
    
    return {'message': 'Lead converted to account', 'account_id': account_id}

@router.get("/leads/stats/summary")
async def get_leads_stats(current_user: dict = Depends(get_current_user)):
    pipeline = [
        {'$group': {'_id': '$status', 'count': {'$sum': 1}}}
    ]
    results = await db.leads.aggregate(pipeline).to_list(100)
    stats = {r['_id']: r['count'] for r in results}
    
    source_pipeline = [
        {'$group': {'_id': '$source', 'count': {'$sum': 1}}}
    ]
    source_results = await db.leads.aggregate(source_pipeline).to_list(100)
    by_source = {r['_id']: r['count'] for r in source_results}
    
    return {
        'total': sum(stats.values()),
        'by_status': stats,
        'by_source': by_source
    }

# ==================== ACCOUNT ENDPOINTS ====================
@router.get("/accounts/gst-lookup/{gstin}")
async def lookup_gst_for_account(gstin: str, current_user: dict = Depends(get_current_user)):
    """Validate GSTIN and return state information for auto-fill"""
    result = validate_and_parse_gstin(gstin)
    if not result.get("valid"):
        raise HTTPException(status_code=400, detail=result.get("error", "Invalid GSTIN"))
    
    return {
        "gstin": gstin.upper(),
        "valid": True,
        "state_code": result["state_code"],
        "state_name": result["state_name"],
        "pan": result["pan"],
        "suggested_billing_state": result["state_name"]
    }

@router.post("/accounts", response_model=Account)
async def create_account(account_data: AccountCreate, current_user: dict = Depends(get_current_user)):
    account_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    
    # Validate and auto-fill from GSTIN
    gstin_info = validate_and_parse_gstin(account_data.gstin)

    payload = account_data.model_dump()

    # Auto-fill geo fields for India PIN
    if (payload.get('billing_country') or 'India').strip().lower() == 'india' and payload.get('billing_pincode'):
        geo = await lookup_india_pincode(payload.get('billing_pincode'))
        if geo:
            payload['billing_country'] = geo.get('country') or payload.get('billing_country')
            payload['billing_state'] = geo.get('state') or payload.get('billing_state')
            payload['billing_district'] = geo.get('district') or payload.get('billing_district')
            payload['billing_city'] = geo.get('city') or payload.get('billing_city')
    
    account_doc = {
        'id': account_id,
        **payload,
        'is_active': True,
        'total_outstanding': 0,
        'receivable_amount': 0,
        'payable_amount': 0,
        'avg_payment_days': 0,
        'lead_id': None,
        'created_by': current_user['id'],
        'assigned_to': account_data.salesperson_id or current_user['id'],
        'created_at': now,
        'updated_at': now
    }
    
    # Auto-fill state from GSTIN if not provided
    if gstin_info.get("valid") and not account_doc.get('billing_state'):
        account_doc['billing_state'] = gstin_info.get('state_name')
    
    # Extract PAN from GSTIN if not provided
    if gstin_info.get("valid") and not account_doc.get('pan'):
        account_doc['pan'] = gstin_info.get('pan')
    
    # Get salesperson name if assigned
    if account_doc.get('salesperson_id'):
        salesperson = await db.users.find_one({'id': account_doc['salesperson_id']}, {'name': 1})
        account_doc['salesperson_name'] = salesperson.get('name') if salesperson else None
    
    # Convert nested models to dict
    account_doc['shipping_addresses'] = [addr.model_dump() if hasattr(addr, 'model_dump') else addr for addr in account_doc.get('shipping_addresses', [])]
    account_doc['contacts'] = [c.model_dump() if hasattr(c, 'model_dump') else c for c in account_doc.get('contacts', [])]
    
    await db.accounts.insert_one(account_doc)
    return Account(**{k: v for k, v in account_doc.items() if k != '_id'})

@router.get("/accounts", response_model=List[Account])
async def get_accounts(
    account_type: Optional[str] = None,
    is_active: Optional[bool] = None,
    location: Optional[str] = None,
    salesperson_id: Optional[str] = None,
    city: Optional[str] = None,
    state: Optional[str] = None,
    industry: Optional[str] = None,
    search: Optional[str] = None,
    has_outstanding: Optional[bool] = None,
    current_user: dict = Depends(get_current_user)
):
    # Apply permission-based filtering
    base_filter = await get_data_filter(current_user, "crm_accounts")
    query = {**base_filter} if base_filter else {}
    
    if account_type:
        query['account_type'] = account_type
    if is_active is not None:
        query['is_active'] = is_active
    if location:
        query['location'] = {"$regex": location, "$options": "i"}
    if salesperson_id:
        query['salesperson_id'] = salesperson_id
    if city:
        query['billing_city'] = {"$regex": city, "$options": "i"}
    if state:
        query['billing_state'] = {"$regex": state, "$options": "i"}
    if industry:
        query['industry'] = industry
    if search:
        query['$or'] = [
            {'customer_name': {"$regex": search, "$options": "i"}},
            {'gstin': {"$regex": search, "$options": "i"}}
        ]
    if has_outstanding:
        query['total_outstanding'] = {"$gt": 0}
    
    accounts = await db.accounts.find(query, {'_id': 0}).sort('created_at', -1).to_list(1000)
    return [Account(**account) for account in accounts]
    return [Account(**account) for account in accounts]

@router.get("/accounts/{account_id}", response_model=Account)
async def get_account(account_id: str, current_user: dict = Depends(get_current_user)):
    account = await db.accounts.find_one({'id': account_id}, {'_id': 0})
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    return Account(**account)

@router.put("/accounts/{account_id}", response_model=Account)
async def update_account(account_id: str, account_data: AccountUpdate, current_user: dict = Depends(get_current_user)):
    update_dict = {k: v for k, v in account_data.model_dump().items() if v is not None}

    # Auto-fill geo fields for India PIN if changed
    if (update_dict.get('billing_country') or 'India').strip().lower() == 'india' and update_dict.get('billing_pincode'):
        geo = await lookup_india_pincode(update_dict.get('billing_pincode'))
        if geo:
            update_dict['billing_country'] = geo.get('country') or update_dict.get('billing_country')
            update_dict['billing_state'] = geo.get('state') or update_dict.get('billing_state')
            update_dict['billing_district'] = geo.get('district') or update_dict.get('billing_district')
            update_dict['billing_city'] = geo.get('city') or update_dict.get('billing_city')

    update_dict['updated_at'] = datetime.now(timezone.utc).isoformat()
    
    # Convert nested models to dict
    if 'shipping_addresses' in update_dict:
        update_dict['shipping_addresses'] = [addr.model_dump() if hasattr(addr, 'model_dump') else addr for addr in update_dict['shipping_addresses']]
    if 'contacts' in update_dict:
        update_dict['contacts'] = [c.model_dump() if hasattr(c, 'model_dump') else c for c in update_dict['contacts']]
    
    result = await db.accounts.update_one(
        {'id': account_id},
        {'$set': update_dict}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Account not found")
    
    account = await db.accounts.find_one({'id': account_id}, {'_id': 0})
    return Account(**account)

@router.delete("/accounts/{account_id}")
async def delete_account(account_id: str, current_user: dict = Depends(get_current_user)):
    # Soft delete - mark as inactive
    result = await db.accounts.update_one(
        {'id': account_id},
        {'$set': {'is_active': False, 'updated_at': datetime.now(timezone.utc).isoformat()}}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Account not found")
    
    return {'message': 'Account deactivated successfully'}

@router.get("/accounts/{account_id}/credit-check")
async def check_account_credit(account_id: str, amount: float = 0, current_user: dict = Depends(get_current_user)):
    account = await db.accounts.find_one({'id': account_id}, {'_id': 0})
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    
    available_credit = account.get('credit_limit', 0) - account.get('total_outstanding', 0)
    can_proceed = available_credit >= amount
    
    return {
        'credit_limit': account.get('credit_limit', 0),
        'total_outstanding': account.get('total_outstanding', 0),
        'available_credit': available_credit,
        'requested_amount': amount,
        'can_proceed': can_proceed,
        'credit_control': account.get('credit_control', 'Warn'),
        'message': 'Credit available' if can_proceed else f"Insufficient credit. Available: ₹{available_credit:,.2f}"
    }

# ==================== QUOTATION ENDPOINTS ====================
def calculate_quotation_totals(items: List[dict], header_discount_percent: float = 0):
    subtotal = 0
    calculated_items = []
    
    for item in items:
        qty = item.get('quantity', 0)
        price = item.get('unit_price', 0)
        discount = item.get('discount_percent', 0)
        tax = item.get('tax_percent', 18)
        
        line_subtotal = qty * price
        line_discount = line_subtotal * (discount / 100)
        line_taxable = line_subtotal - line_discount
        line_tax = line_taxable * (tax / 100)
        line_total = line_taxable + line_tax
        
        calc_item = {**item, 'line_total': round(line_total, 2)}
        calculated_items.append(calc_item)
        subtotal += line_subtotal
    
    header_discount_amount = subtotal * (header_discount_percent / 100)
    taxable_amount = subtotal - header_discount_amount
    
    # Calculate GST (assuming intra-state for now - CGST + SGST)
    total_tax = 0
    cgst_amount = 0
    sgst_amount = 0
    igst_amount = 0
    
    for item in items:
        tax_rate = item.get('tax_percent', 18)
        item_taxable = (item.get('quantity', 0) * item.get('unit_price', 0)) * (1 - item.get('discount_percent', 0) / 100)
        item_taxable -= item_taxable * (header_discount_percent / 100)
        item_tax = item_taxable * (tax_rate / 100)
        total_tax += item_tax
        cgst_amount += item_tax / 2
        sgst_amount += item_tax / 2
    
    grand_total = taxable_amount + total_tax
    
    return {
        'items': calculated_items,
        'subtotal': round(subtotal, 2),
        'header_discount_percent': header_discount_percent,
        'header_discount_amount': round(header_discount_amount, 2),
        'taxable_amount': round(taxable_amount, 2),
        'cgst_amount': round(cgst_amount, 2),
        'sgst_amount': round(sgst_amount, 2),
        'igst_amount': round(igst_amount, 2),
        'total_tax': round(total_tax, 2),
        'grand_total': round(grand_total, 2)
    }

@router.post("/quotations", response_model=Quotation)
async def create_quotation(quote_data: QuotationCreate, current_user: dict = Depends(get_current_user)):
    # Verify account exists
    account = await db.accounts.find_one({'id': quote_data.account_id}, {'_id': 0})
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    
    quote_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc)
    quote_number = f"QT-{now.strftime('%Y%m%d')}-{str(uuid.uuid4())[:6].upper()}"
    
    # Calculate totals
    items_dict = [item.model_dump() for item in quote_data.items]
    totals = calculate_quotation_totals(items_dict, quote_data.header_discount_percent)
    
    quote_doc = {
        'id': quote_id,
        'quote_number': quote_number,
        'account_id': quote_data.account_id,
        'account_name': account.get('customer_name'),
        'contact_person': quote_data.contact_person,
        'salesperson_id': quote_data.salesperson_id,
        'reference': quote_data.reference,
        'quote_date': now.isoformat(),
        'valid_until': quote_data.valid_until,
        **totals,
        'transport': quote_data.transport,
        'delivery_terms': quote_data.delivery_terms,
        'payment_terms': quote_data.payment_terms or account.get('payment_terms'),
        'terms_conditions': quote_data.terms_conditions,
        'notes': quote_data.notes,
        'status': 'draft',
        'converted_to_order': False,
        'order_id': None,
        'created_by': current_user['id'],
        'created_at': now.isoformat(),
        'updated_at': now.isoformat()
    }
    
    await db.quotations.insert_one(quote_doc)
    return Quotation(**{k: v for k, v in quote_doc.items() if k != '_id'})

@router.get("/quotations", response_model=List[Quotation])
async def get_quotations(
    account_id: Optional[str] = None,
    status: Optional[str] = None,
    salesperson_id: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    query = {}
    if account_id:
        query['account_id'] = account_id
    if status:
        query['status'] = status
    if salesperson_id:
        query['salesperson_id'] = salesperson_id
    
    quotations = await db.quotations.find(query, {'_id': 0}).sort('created_at', -1).to_list(1000)
    return [Quotation(**quote) for quote in quotations]

@router.get("/quotations/{quote_id}", response_model=Quotation)
async def get_quotation(quote_id: str, current_user: dict = Depends(get_current_user)):
    quote = await db.quotations.find_one({'id': quote_id}, {'_id': 0})
    if not quote:
        raise HTTPException(status_code=404, detail="Quotation not found")
    return Quotation(**quote)

@router.put("/quotations/{quote_id}", response_model=Quotation)
async def update_quotation(quote_id: str, quote_data: QuotationUpdate, current_user: dict = Depends(get_current_user)):
    existing = await db.quotations.find_one({'id': quote_id}, {'_id': 0})
    if not existing:
        raise HTTPException(status_code=404, detail="Quotation not found")
    
    if existing.get('status') in ['accepted', 'converted']:
        raise HTTPException(status_code=400, detail="Cannot modify accepted or converted quotation")
    
    update_dict = {k: v for k, v in quote_data.model_dump().items() if v is not None}
    
    # Recalculate totals if items changed
    if 'items' in update_dict:
        items_dict = [item.model_dump() if hasattr(item, 'model_dump') else item for item in update_dict['items']]
        discount = update_dict.get('header_discount_percent', existing.get('header_discount_percent', 0))
        totals = calculate_quotation_totals(items_dict, discount)
        update_dict.update(totals)
    
    update_dict['updated_at'] = datetime.now(timezone.utc).isoformat()
    
    await db.quotations.update_one({'id': quote_id}, {'$set': update_dict})
    
    quote = await db.quotations.find_one({'id': quote_id}, {'_id': 0})
    return Quotation(**quote)

@router.put("/quotations/{quote_id}/status")
async def update_quotation_status(quote_id: str, status: str, current_user: dict = Depends(get_current_user)):
    valid_statuses = ['draft', 'sent', 'accepted', 'rejected', 'expired', 'revised']
    if status not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of: {valid_statuses}")
    
    result = await db.quotations.update_one(
        {'id': quote_id},
        {'$set': {'status': status, 'updated_at': datetime.now(timezone.utc).isoformat()}}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Quotation not found")
    
    return {'message': f'Quotation status updated to {status}'}

@router.post("/quotations/{quote_id}/convert-to-order")
async def convert_quotation_to_order(quote_id: str, current_user: dict = Depends(get_current_user)):
    quote = await db.quotations.find_one({'id': quote_id}, {'_id': 0})
    if not quote:
        raise HTTPException(status_code=404, detail="Quotation not found")
    
    if quote.get('converted_to_order'):
        raise HTTPException(status_code=400, detail="Quotation already converted to order")
    
    # Create sales order (simplified - actual implementation would be in sales module)
    order_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    
    order_doc = {
        'id': order_id,
        'order_number': f"SO-{datetime.now(timezone.utc).strftime('%Y%m%d')}-{str(uuid.uuid4())[:6].upper()}",
        'quotation_id': quote_id,
        'account_id': quote.get('account_id'),
        'account_name': quote.get('account_name'),
        'items': quote.get('items'),
        'subtotal': quote.get('subtotal'),
        'total_tax': quote.get('total_tax'),
        'grand_total': quote.get('grand_total'),
        'status': 'pending',
        'created_by': current_user['id'],
        'created_at': now
    }
    
    await db.sales_orders.insert_one(order_doc)
    await db.quotations.update_one(
        {'id': quote_id},
        {'$set': {'converted_to_order': True, 'order_id': order_id, 'status': 'accepted', 'updated_at': now}}
    )
    
    return {'message': 'Quotation converted to sales order', 'order_id': order_id}

@router.delete("/quotations/{quote_id}")
async def delete_quotation(quote_id: str, current_user: dict = Depends(get_current_user)):
    quote = await db.quotations.find_one({'id': quote_id}, {'_id': 0})
    if not quote:
        raise HTTPException(status_code=404, detail="Quotation not found")
    
    if quote.get('converted_to_order'):
        raise HTTPException(status_code=400, detail="Cannot delete converted quotation")
    
    await db.quotations.delete_one({'id': quote_id})
    return {'message': 'Quotation deleted successfully'}

# ==================== SAMPLE ENDPOINTS ====================
@router.post("/samples", response_model=Sample)
async def create_sample(sample_data: SampleCreate, current_user: dict = Depends(get_current_user)):
    # Verify account exists
    account = await db.accounts.find_one({'id': sample_data.account_id}, {'_id': 0})
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    
    sample_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    sample_number = f"SMP-{datetime.now(timezone.utc).strftime('%Y%m%d')}-{str(uuid.uuid4())[:6].upper()}"
    
    sample_payload = sample_data.model_dump()

    # Persist a flattened summary for quick display/search
    summary_product = sample_payload.get('items')[0].get('product_name') if sample_payload.get('items') else None
    summary_specs = sample_payload.get('items')[0].get('product_specs') if sample_payload.get('items') else None

    sample_doc = {
        'id': sample_id,
        'sample_number': sample_number,
        'account_id': sample_data.account_id,
        'account_name': account.get('customer_name'),
        **sample_payload,
        'product_name': summary_product,
        'product_specs': summary_specs,
        'status': 'created',
        'feedback_status': 'pending',
        'feedback_notes': None,
        'feedback_date': None,
        'return_date': None,
        'return_condition': None,
        'estimated_cost': 0,
        'sent_by': current_user['id'],
        'created_at': now,
        'updated_at': now
    }
    
    await db.samples.insert_one(sample_doc)
    return Sample(**{k: v for k, v in sample_doc.items() if k != '_id'})

@router.get("/samples", response_model=List[Sample])
async def get_samples(
    account_id: Optional[str] = None,
    status: Optional[str] = None,
    feedback_status: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    query = {}
    if account_id:
        query['account_id'] = account_id
    if status:
        query['status'] = status
    if feedback_status:
        query['feedback_status'] = feedback_status
    
    samples = await db.samples.find(query, {'_id': 0}).sort('created_at', -1).to_list(1000)
    return [Sample(**sample) for sample in samples]

@router.get("/samples/{sample_id}", response_model=Sample)
async def get_sample(sample_id: str, current_user: dict = Depends(get_current_user)):
    sample = await db.samples.find_one({'id': sample_id}, {'_id': 0})
    if not sample:
        raise HTTPException(status_code=404, detail="Sample not found")
    return Sample(**sample)

@router.put("/samples/{sample_id}", response_model=Sample)
async def update_sample(sample_id: str, sample_data: SampleUpdate, current_user: dict = Depends(get_current_user)):
    update_dict = {k: v for k, v in sample_data.model_dump().items() if v is not None}

    # Keep flattened summary in sync if items updated
    if 'items' in update_dict and update_dict.get('items'):
        update_dict['product_name'] = update_dict['items'][0].get('product_name')
        update_dict['product_specs'] = update_dict['items'][0].get('product_specs')

    update_dict['updated_at'] = datetime.now(timezone.utc).isoformat()
    
    result = await db.samples.update_one(
        {'id': sample_id},
        {'$set': update_dict}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Sample not found")
    
    sample = await db.samples.find_one({'id': sample_id}, {'_id': 0})
    return Sample(**sample)

@router.put("/samples/{sample_id}/dispatch")
async def dispatch_sample(sample_id: str, courier: str, tracking_number: Optional[str] = None, current_user: dict = Depends(get_current_user)):
    now = datetime.now(timezone.utc).isoformat()
    
    result = await db.samples.update_one(
        {'id': sample_id},
        {'$set': {
            'status': 'dispatched',
            'courier': courier,
            'tracking_number': tracking_number,
            'dispatch_date': now,
            'updated_at': now
        }}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Sample not found")
    
    return {'message': 'Sample dispatched successfully'}

@router.put("/samples/{sample_id}/feedback")
async def update_sample_feedback(
    sample_id: str,
    feedback_status: str,
    feedback_notes: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    valid_statuses = ['pending', 'positive', 'negative', 'needs_revision', 'no_response']
    if feedback_status not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"Invalid feedback status. Must be one of: {valid_statuses}")
    
    now = datetime.now(timezone.utc).isoformat()
    
    result = await db.samples.update_one(
        {'id': sample_id},
        {'$set': {
            'feedback_status': feedback_status,
            'feedback_notes': feedback_notes,
            'feedback_date': now,
            'updated_at': now
        }}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Sample not found")
    
    return {'message': 'Sample feedback updated'}

@router.put("/samples/{sample_id}/return")
async def mark_sample_returned(
    sample_id: str,
    return_condition: str,
    notes: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    valid_conditions = ['good', 'damaged', 'lost', 'consumed']
    if return_condition not in valid_conditions:
        raise HTTPException(status_code=400, detail=f"Invalid return condition. Must be one of: {valid_conditions}")
    
    now = datetime.now(timezone.utc).isoformat()
    
    result = await db.samples.update_one(
        {'id': sample_id},
        {'$set': {
            'status': 'returned',
            'return_date': now,
            'return_condition': return_condition,
            'return_notes': notes,
            'updated_at': now
        }}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Sample not found")
    
    return {'message': 'Sample marked as returned'}

@router.delete("/samples/{sample_id}")
async def delete_sample(sample_id: str, current_user: dict = Depends(get_current_user)):
    result = await db.samples.delete_one({'id': sample_id})
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Sample not found")
    
    return {'message': 'Sample deleted successfully'}

# ==================== FOLLOWUP ENDPOINTS ====================
@router.post("/followups", response_model=Followup)
async def create_followup(followup_data: FollowupCreate, current_user: dict = Depends(get_current_user)):
    followup_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    
    followup_doc = {
        'id': followup_id,
        **followup_data.model_dump(),
        'completed_date': None,
        'outcome': None,
        'status': 'scheduled',
        'created_by': current_user['id'],
        'created_at': now
    }
    
    await db.followups.insert_one(followup_doc)
    return Followup(**{k: v for k, v in followup_doc.items() if k != '_id'})

@router.get("/followups")
async def get_followups(
    entity_type: Optional[str] = None,
    entity_id: Optional[str] = None,
    status: Optional[str] = None,
    assigned_to: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    query = {}
    if entity_type:
        query['entity_type'] = entity_type
    if entity_id:
        query['entity_id'] = entity_id
    if status:
        query['status'] = status
    if assigned_to:
        query['assigned_to'] = assigned_to
    
    followups = await db.followups.find(query, {'_id': 0}).sort('scheduled_date', 1).to_list(1000)
    return followups

@router.put("/followups/{followup_id}/complete")
async def complete_followup(
    followup_id: str,
    outcome: str,
    notes: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    now = datetime.now(timezone.utc).isoformat()
    
    result = await db.followups.update_one(
        {'id': followup_id},
        {'$set': {
            'status': 'completed',
            'completed_date': now,
            'outcome': outcome,
            'completion_notes': notes
        }}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Follow-up not found")
    
    return {'message': 'Follow-up marked as completed'}

# ==================== CRM STATS ====================
@router.get("/stats/overview")
async def get_crm_overview(current_user: dict = Depends(get_current_user)):
    leads_count = await db.leads.count_documents({})
    accounts_count = await db.accounts.count_documents({'is_active': True})
    quotations_count = await db.quotations.count_documents({})
    samples_count = await db.samples.count_documents({})
    
    # Pending quotations
    pending_quotes = await db.quotations.count_documents({'status': {'$in': ['draft', 'sent']}})
    
    # Samples awaiting feedback
    pending_samples = await db.samples.count_documents({'feedback_status': 'pending'})
    
    # Quote conversion rate
    accepted_quotes = await db.quotations.count_documents({'status': 'accepted'})
    conversion_rate = (accepted_quotes / quotations_count * 100) if quotations_count > 0 else 0
    
    # Leads by status
    lead_status_pipeline = [{'$group': {'_id': '$status', 'count': {'$sum': 1}}}]
    lead_status_results = await db.leads.aggregate(lead_status_pipeline).to_list(100)
    leads_by_status = {r['_id']: r['count'] for r in lead_status_results}
    
    # Leads by source
    lead_source_pipeline = [{'$group': {'_id': '$source', 'count': {'$sum': 1}}}]
    lead_source_results = await db.leads.aggregate(lead_source_pipeline).to_list(100)
    leads_by_source = {r['_id']: r['count'] for r in lead_source_results}
    
    # Quotations by status
    quote_status_pipeline = [{'$group': {'_id': '$status', 'count': {'$sum': 1}, 'total': {'$sum': '$grand_total'}}}]
    quote_status_results = await db.quotations.aggregate(quote_status_pipeline).to_list(100)
    quotes_by_status = {r['_id']: {'count': r['count'], 'total': r['total']} for r in quote_status_results}
    
    # Total quote value
    total_quote_value = sum(q.get('total', 0) for q in quotes_by_status.values())
    
    # Accounts by state
    state_pipeline = [{'$group': {'_id': '$billing_state', 'count': {'$sum': 1}}}]
    state_results = await db.accounts.aggregate(state_pipeline).to_list(100)
    accounts_by_state = {r['_id']: r['count'] for r in state_results if r['_id']}
    
    # Top accounts by outstanding
    top_outstanding = await db.accounts.find(
        {'receivable_amount': {'$gt': 0}}, 
        {'_id': 0, 'customer_name': 1, 'receivable_amount': 1, 'billing_city': 1}
    ).sort('receivable_amount', -1).to_list(5)
    
    return {
        'leads': leads_count,
        'accounts': accounts_count,
        'quotations': quotations_count,
        'samples': samples_count,
        'pending_quotations': pending_quotes,
        'pending_samples': pending_samples,
        'quote_conversion_rate': round(conversion_rate, 1),
        'total_quote_value': round(total_quote_value, 2),
        'leads_by_status': leads_by_status,
        'leads_by_source': leads_by_source,
        'quotes_by_status': quotes_by_status,
        'accounts_by_state': accounts_by_state,
        'top_outstanding': top_outstanding
    }
