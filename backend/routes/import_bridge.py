"""
Import Bridge Module
Handles:
- Import Purchase Orders with duty, freight, insurance
- Landing Zone for Final Landed INR Rate calculation
- Auto-update inventory valuation
- Auto-update MSP (Minimum Sale Price)
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
import uuid
from server import db, get_current_user
from utils.document_numbering import generate_document_number

router = APIRouter()


# ==================== IMPORT PO MODELS ====================
class ImportPOItemCreate(BaseModel):
    item_id: str
    item_name: str
    quantity: float
    uom: str
    foreign_unit_price: float
    foreign_currency: str = "USD"  # USD, EUR, GBP, CNY, JPY
    hsn_code: Optional[str] = None


class ImportPOCreate(BaseModel):
    supplier_id: str
    po_date: str
    expected_arrival: str
    items: List[ImportPOItemCreate]
    foreign_currency: str = "USD"
    exchange_rate: float = 83.0  # INR per foreign currency
    
    # Shipping details
    port_of_loading: str
    port_of_discharge: str
    shipping_terms: str = "FOB"  # FOB, CIF, CNF, EXW, etc.
    shipping_line: Optional[str] = None
    container_type: str = "20ft"  # 20ft, 40ft, LCL
    
    # Payment terms
    payment_terms: str  # LC, TT, DA, DP
    lc_number: Optional[str] = None
    bank_name: Optional[str] = None
    
    notes: Optional[str] = None


class ImportPO(BaseModel):
    id: str
    po_number: str
    supplier_id: str
    supplier_name: Optional[str] = None
    po_date: str
    expected_arrival: str
    items: List[dict]
    
    # Currency
    foreign_currency: str
    exchange_rate: float
    total_foreign_value: float
    total_inr_value: float
    
    # Shipping
    port_of_loading: str
    port_of_discharge: str
    shipping_terms: str
    shipping_line: Optional[str] = None
    container_type: str
    
    # Payment
    payment_terms: str
    lc_number: Optional[str] = None
    bank_name: Optional[str] = None
    
    # Status
    status: str  # draft, confirmed, shipped, in_transit, customs, delivered, completed
    bl_number: Optional[str] = None  # Bill of Lading
    bl_date: Optional[str] = None
    
    notes: Optional[str] = None
    created_at: str
    created_by: str


# ==================== LANDING COST MODELS ====================
class LandingCostCreate(BaseModel):
    import_po_id: str
    
    # Duties & Taxes (in INR)
    basic_customs_duty: float = 0
    social_welfare_cess: float = 0  # 10% on BCD
    igst: float = 0
    anti_dumping_duty: float = 0
    safeguard_duty: float = 0
    
    # Freight & Insurance (in INR)
    ocean_freight: float = 0
    insurance: float = 0
    local_freight: float = 0  # Port to warehouse
    
    # Handling Charges
    cha_charges: float = 0  # Customs House Agent
    port_charges: float = 0
    container_detention: float = 0
    documentation_charges: float = 0
    
    # Other
    bank_charges: float = 0
    other_charges: float = 0
    
    # Exchange rate at time of payment (may differ from PO rate)
    settlement_exchange_rate: float = 0
    
    notes: Optional[str] = None


class LandingCost(BaseModel):
    id: str
    import_po_id: str
    po_number: Optional[str] = None
    
    # Original PO Value
    po_foreign_value: float
    po_exchange_rate: float
    po_inr_value: float
    
    # Duties
    basic_customs_duty: float
    social_welfare_cess: float
    igst: float
    anti_dumping_duty: float
    safeguard_duty: float
    total_duties: float
    
    # Freight & Insurance
    ocean_freight: float
    insurance: float
    local_freight: float
    total_freight: float
    
    # Handling
    cha_charges: float
    port_charges: float
    container_detention: float
    documentation_charges: float
    total_handling: float
    
    # Other
    bank_charges: float
    other_charges: float
    
    # Settlement
    settlement_exchange_rate: float
    forex_gain_loss: float  # Difference due to exchange rate change
    
    # Final Calculations
    total_landing_cost: float
    landed_inr_value: float  # PO value + all costs
    landed_rate_per_unit: Dict[str, Any]  # Per item landed rate details
    
    notes: Optional[str] = None
    status: str  # draft, calculated, finalized
    created_at: str
    created_by: str


# ==================== IMPORT PO ENDPOINTS ====================
@router.post("/purchase-orders", response_model=ImportPO)
async def create_import_po(data: ImportPOCreate, current_user: dict = Depends(get_current_user)):
    """Create import purchase order"""
    # Verify supplier
    supplier = await db.suppliers.find_one({'id': data.supplier_id}, {'_id': 0})
    supplier_name = supplier.get('supplier_name') if supplier else None
    
    po_id = str(uuid.uuid4())
    po_number = await generate_document_number(db, 'import_po', 'HO')
    
    # Calculate totals
    items = []
    total_foreign = 0
    for item in data.items:
        item_total = item.quantity * item.foreign_unit_price
        total_foreign += item_total
        items.append({
            **item.model_dump(),
            'line_total_foreign': item_total,
            'line_total_inr': item_total * data.exchange_rate
        })
    
    total_inr = total_foreign * data.exchange_rate
    
    po_doc = {
        'id': po_id,
        'po_number': po_number,
        'supplier_id': data.supplier_id,
        'supplier_name': supplier_name,
        'po_date': data.po_date,
        'expected_arrival': data.expected_arrival,
        'items': items,
        'foreign_currency': data.foreign_currency,
        'exchange_rate': data.exchange_rate,
        'total_foreign_value': total_foreign,
        'total_inr_value': total_inr,
        'port_of_loading': data.port_of_loading,
        'port_of_discharge': data.port_of_discharge,
        'shipping_terms': data.shipping_terms,
        'shipping_line': data.shipping_line,
        'container_type': data.container_type,
        'payment_terms': data.payment_terms,
        'lc_number': data.lc_number,
        'bank_name': data.bank_name,
        'status': 'draft',
        'bl_number': None,
        'bl_date': None,
        'notes': data.notes,
        'created_at': datetime.now(timezone.utc).isoformat(),
        'created_by': current_user['id']
    }
    
    await db.import_pos.insert_one(po_doc)
    return ImportPO(**{k: v for k, v in po_doc.items() if k != '_id'})


@router.get("/purchase-orders", response_model=List[ImportPO])
async def get_import_pos(
    status: Optional[str] = None,
    supplier_id: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Get all import POs"""
    query = {}
    if status:
        query['status'] = status
    if supplier_id:
        query['supplier_id'] = supplier_id
    
    pos = await db.import_pos.find(query, {'_id': 0}).sort('created_at', -1).to_list(500)
    return [ImportPO(**p) for p in pos]


@router.put("/purchase-orders/{po_id}/status")
async def update_import_po_status(
    po_id: str,
    status: str,
    bl_number: Optional[str] = None,
    bl_date: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Update import PO status"""
    valid_statuses = ['draft', 'confirmed', 'shipped', 'in_transit', 'customs', 'delivered', 'completed']
    if status not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of: {valid_statuses}")
    
    update_data = {'status': status, 'updated_at': datetime.now(timezone.utc).isoformat()}
    if bl_number:
        update_data['bl_number'] = bl_number
    if bl_date:
        update_data['bl_date'] = bl_date
    
    result = await db.import_pos.update_one(
        {'id': po_id},
        {'$set': update_data}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Import PO not found")
    
    return {'message': 'Status updated', 'po_id': po_id, 'status': status}


# ==================== LANDING COST ENDPOINTS ====================
@router.post("/landing-cost", response_model=LandingCost)
async def calculate_landing_cost(data: LandingCostCreate, current_user: dict = Depends(get_current_user)):
    """
    Calculate final landed INR rate for import PO
    This is the "Landing Zone" feature
    """
    # Get import PO
    po = await db.import_pos.find_one({'id': data.import_po_id}, {'_id': 0})
    if not po:
        raise HTTPException(status_code=404, detail="Import PO not found")
    
    cost_id = str(uuid.uuid4())
    
    # Calculate totals
    total_duties = (
        data.basic_customs_duty + data.social_welfare_cess + 
        data.igst + data.anti_dumping_duty + data.safeguard_duty
    )
    
    total_freight = data.ocean_freight + data.insurance + data.local_freight
    
    total_handling = (
        data.cha_charges + data.port_charges + 
        data.container_detention + data.documentation_charges
    )
    
    # Forex gain/loss calculation
    settlement_rate = data.settlement_exchange_rate or po['exchange_rate']
    forex_gain_loss = (settlement_rate - po['exchange_rate']) * po['total_foreign_value']
    
    # Total landing cost (excluding PO value)
    total_landing_cost = (
        total_duties + total_freight + total_handling +
        data.bank_charges + data.other_charges + forex_gain_loss
    )
    
    # Final landed value
    po_inr_value = po['total_foreign_value'] * settlement_rate
    landed_inr_value = po_inr_value + total_landing_cost
    
    # Calculate per-item landed rate
    landed_rate_per_unit = {}
    total_qty = sum(item['quantity'] for item in po['items'])
    
    for item in po['items']:
        item_proportion = item['quantity'] / total_qty
        item_landing_cost = total_landing_cost * item_proportion
        item_base_cost = item['quantity'] * item['foreign_unit_price'] * settlement_rate
        item_landed_value = item_base_cost + item_landing_cost
        landed_rate_per_unit[item['item_id']] = {
            'item_name': item['item_name'],
            'quantity': item['quantity'],
            'base_cost_inr': round(item_base_cost, 2),
            'landing_cost_inr': round(item_landing_cost, 2),
            'total_landed_inr': round(item_landed_value, 2),
            'landed_rate_per_unit': round(item_landed_value / item['quantity'], 2)
        }
    
    cost_doc = {
        'id': cost_id,
        'import_po_id': data.import_po_id,
        'po_number': po['po_number'],
        'po_foreign_value': po['total_foreign_value'],
        'po_exchange_rate': po['exchange_rate'],
        'po_inr_value': po_inr_value,
        'basic_customs_duty': data.basic_customs_duty,
        'social_welfare_cess': data.social_welfare_cess,
        'igst': data.igst,
        'anti_dumping_duty': data.anti_dumping_duty,
        'safeguard_duty': data.safeguard_duty,
        'total_duties': total_duties,
        'ocean_freight': data.ocean_freight,
        'insurance': data.insurance,
        'local_freight': data.local_freight,
        'total_freight': total_freight,
        'cha_charges': data.cha_charges,
        'port_charges': data.port_charges,
        'container_detention': data.container_detention,
        'documentation_charges': data.documentation_charges,
        'total_handling': total_handling,
        'bank_charges': data.bank_charges,
        'other_charges': data.other_charges,
        'settlement_exchange_rate': settlement_rate,
        'forex_gain_loss': round(forex_gain_loss, 2),
        'total_landing_cost': round(total_landing_cost, 2),
        'landed_inr_value': round(landed_inr_value, 2),
        'landed_rate_per_unit': landed_rate_per_unit,
        'notes': data.notes,
        'status': 'calculated',
        'created_at': datetime.now(timezone.utc).isoformat(),
        'created_by': current_user['id']
    }
    
    await db.landing_costs.insert_one(cost_doc)
    return LandingCost(**{k: v for k, v in cost_doc.items() if k != '_id'})


@router.get("/landing-cost/{po_id}")
async def get_landing_cost(po_id: str, current_user: dict = Depends(get_current_user)):
    """Get landing cost for an import PO"""
    cost = await db.landing_costs.find_one({'import_po_id': po_id}, {'_id': 0})
    if not cost:
        raise HTTPException(status_code=404, detail="Landing cost not calculated yet")
    return cost


@router.put("/landing-cost/{cost_id}/finalize")
async def finalize_landing_cost(cost_id: str, current_user: dict = Depends(get_current_user)):
    """
    Finalize landing cost and update:
    1. Inventory valuation (standard cost)
    2. MSP (Minimum Sale Price)
    """
    cost = await db.landing_costs.find_one({'id': cost_id}, {'_id': 0})
    if not cost:
        raise HTTPException(status_code=404, detail="Landing cost not found")
    
    if cost['status'] == 'finalized':
        raise HTTPException(status_code=400, detail="Already finalized")
    
    # Update item costs
    for item_id, item_data in cost['landed_rate_per_unit'].items():
        landed_rate = item_data['landed_rate_per_unit']
        
        # Update item standard cost
        await db.items.update_one(
            {'id': item_id},
            {'$set': {
                'standard_cost': landed_rate,
                'last_landed_rate': landed_rate,
                'last_landed_date': datetime.now(timezone.utc).isoformat(),
                'updated_at': datetime.now(timezone.utc).isoformat()
            }}
        )
        
        # Calculate and update MSP (landed cost + 20% margin minimum)
        msp = landed_rate * 1.2
        await db.items.update_one(
            {'id': item_id},
            {'$set': {'min_sale_price': round(msp, 2)}}
        )
    
    # Update landing cost status
    await db.landing_costs.update_one(
        {'id': cost_id},
        {'$set': {
            'status': 'finalized',
            'finalized_at': datetime.now(timezone.utc).isoformat(),
            'finalized_by': current_user['id']
        }}
    )
    
    return {
        'message': 'Landing cost finalized, inventory and MSP updated',
        'cost_id': cost_id,
        'items_updated': len(cost['landed_rate_per_unit'])
    }


# ==================== EXCHANGE RATE MANAGEMENT ====================
@router.get("/exchange-rates")
async def get_exchange_rates(current_user: dict = Depends(get_current_user)):
    """Get current exchange rates (can be integrated with API later)"""
    # Default rates - in production, fetch from API like Open Exchange Rates
    rates = await db.exchange_rates.find({}, {'_id': 0}).sort('date', -1).to_list(10)
    
    if not rates:
        # Default rates
        return {
            'base': 'INR',
            'date': datetime.now(timezone.utc).isoformat()[:10],
            'rates': {
                'USD': 83.50,
                'EUR': 90.00,
                'GBP': 105.00,
                'CNY': 11.50,
                'JPY': 0.56
            }
        }
    
    return rates[0]


@router.post("/exchange-rates")
async def update_exchange_rate(
    currency: str,
    rate: float,
    current_user: dict = Depends(get_current_user)
):
    """Update exchange rate"""
    if current_user['role'] not in ['admin', 'accountant']:
        raise HTTPException(status_code=403, detail="Access denied")
    
    today = datetime.now(timezone.utc).isoformat()[:10]
    
    await db.exchange_rates.update_one(
        {'date': today},
        {
            '$set': {f'rates.{currency}': rate, 'updated_at': datetime.now(timezone.utc).isoformat()},
            '$setOnInsert': {'base': 'INR', 'date': today}
        },
        upsert=True
    )
    
    return {'message': f'{currency} rate updated to {rate}'}
