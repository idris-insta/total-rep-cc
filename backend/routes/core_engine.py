"""
CORE ENGINE MODULE - The 6 Pillars of AdhesiveFlow ERP

1. Physics Engine - Unit Conversion (KG ↔ SQM ↔ PCS)
2. Production Redline - 7% Scrap Lock + Mass Balance
3. CRM Buying DNA - AI Purchase Pattern Tracking
4. Multi-Branch Ledger - GST Bridge (GJ/MH/DL)
5. Import Bridge - Landed Cost & MSP Calculator
6. Director Cockpit - Pulse Dashboard with Override
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone, timedelta
import uuid
from server import db, get_current_user

router = APIRouter()


# ==================== 1. PHYSICS ENGINE - UNIT CONVERSION ====================
class UnitConversionRequest(BaseModel):
    item_id: Optional[str] = None
    from_unit: str  # KG, SQM, PCS, MTR, ROL
    to_unit: str
    quantity: float
    # Item specifications (if item_id not provided)
    thickness_micron: Optional[float] = None
    width_mm: Optional[float] = None
    length_m: Optional[float] = None
    density_kg_m3: Optional[float] = 920  # Default BOPP density


class UnitConversionResponse(BaseModel):
    from_value: float
    from_unit: str
    to_value: float
    to_unit: str
    conversion_factor: float
    formula_used: str


@router.post("/physics/convert", response_model=UnitConversionResponse)
async def convert_units(data: UnitConversionRequest, current_user: dict = Depends(get_current_user)):
    """
    Physics Engine: Convert between KG, SQM, PCS, MTR, ROL
    Master formula for adhesive tape industry
    """
    specs = {}
    
    # Get item specs if item_id provided
    if data.item_id:
        item = await db.items.find_one({"id": data.item_id}, {"_id": 0})
        if item:
            specs = item.get("specifications", {})
    
    # Use provided specs or item specs
    thickness = data.thickness_micron or specs.get("thickness", 40)  # microns
    width = data.width_mm or specs.get("width", 48)  # mm
    length = data.length_m or specs.get("length", 65)  # meters per roll
    density = data.density_kg_m3 or specs.get("density", 920)  # kg/m³
    
    # Convert thickness to meters
    thickness_m = thickness / 1_000_000
    # Convert width to meters
    width_m = width / 1000
    
    # Calculate base values
    # Volume per roll (m³) = thickness × width × length
    volume_per_roll = thickness_m * width_m * length
    # Weight per roll (kg) = volume × density
    kg_per_roll = volume_per_roll * density
    # Area per roll (sqm) = width × length
    sqm_per_roll = width_m * length
    
    # Conversion logic
    result = 0
    formula = ""
    
    if data.from_unit == "KG":
        if data.to_unit == "SQM":
            # KG to SQM: weight / (thickness × density)
            result = data.quantity / (thickness_m * density)
            formula = f"SQM = KG / (thickness_m × density) = {data.quantity} / ({thickness_m} × {density})"
        elif data.to_unit == "PCS" or data.to_unit == "ROL":
            result = data.quantity / kg_per_roll
            formula = f"PCS = KG / kg_per_roll = {data.quantity} / {kg_per_roll:.4f}"
        elif data.to_unit == "MTR":
            sqm = data.quantity / (thickness_m * density)
            result = sqm / width_m
            formula = f"MTR = (KG / (thickness × density)) / width"
        else:
            result = data.quantity
            
    elif data.from_unit == "SQM":
        if data.to_unit == "KG":
            result = data.quantity * thickness_m * density
            formula = f"KG = SQM × thickness_m × density = {data.quantity} × {thickness_m} × {density}"
        elif data.to_unit == "PCS" or data.to_unit == "ROL":
            result = data.quantity / sqm_per_roll
            formula = f"PCS = SQM / sqm_per_roll = {data.quantity} / {sqm_per_roll:.4f}"
        elif data.to_unit == "MTR":
            result = data.quantity / width_m
            formula = f"MTR = SQM / width_m = {data.quantity} / {width_m}"
        else:
            result = data.quantity
            
    elif data.from_unit in ["PCS", "ROL"]:
        if data.to_unit == "KG":
            result = data.quantity * kg_per_roll
            formula = f"KG = PCS × kg_per_roll = {data.quantity} × {kg_per_roll:.4f}"
        elif data.to_unit == "SQM":
            result = data.quantity * sqm_per_roll
            formula = f"SQM = PCS × sqm_per_roll = {data.quantity} × {sqm_per_roll:.4f}"
        elif data.to_unit == "MTR":
            result = data.quantity * length
            formula = f"MTR = PCS × length_per_roll = {data.quantity} × {length}"
        else:
            result = data.quantity
            
    elif data.from_unit == "MTR":
        if data.to_unit == "SQM":
            result = data.quantity * width_m
            formula = f"SQM = MTR × width_m = {data.quantity} × {width_m}"
        elif data.to_unit == "KG":
            sqm = data.quantity * width_m
            result = sqm * thickness_m * density
            formula = f"KG = MTR × width × thickness × density"
        elif data.to_unit in ["PCS", "ROL"]:
            result = data.quantity / length
            formula = f"PCS = MTR / length_per_roll = {data.quantity} / {length}"
        else:
            result = data.quantity
    else:
        result = data.quantity
        formula = "Same unit - no conversion"
    
    return UnitConversionResponse(
        from_value=data.quantity,
        from_unit=data.from_unit,
        to_value=round(result, 4),
        to_unit=data.to_unit,
        conversion_factor=round(result / data.quantity if data.quantity > 0 else 0, 6),
        formula_used=formula
    )


@router.get("/physics/item-conversions/{item_id}")
async def get_item_conversion_table(item_id: str, current_user: dict = Depends(get_current_user)):
    """Get all conversion factors for an item"""
    item = await db.items.find_one({"id": item_id}, {"_id": 0})
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    
    specs = item.get("specifications", {})
    thickness = specs.get("thickness", 40) / 1_000_000  # to meters
    width = specs.get("width", 48) / 1000  # to meters
    length = specs.get("length", 65)
    density = specs.get("density", 920)
    
    kg_per_roll = thickness * width * length * density
    sqm_per_roll = width * length
    
    return {
        "item_id": item_id,
        "item_name": item.get("item_name"),
        "specifications": specs,
        "conversion_factors": {
            "kg_per_roll": round(kg_per_roll, 4),
            "sqm_per_roll": round(sqm_per_roll, 4),
            "kg_per_sqm": round(thickness * density, 6),
            "sqm_per_kg": round(1 / (thickness * density), 4) if thickness * density > 0 else 0,
            "mtrs_per_roll": length,
            "rolls_per_kg": round(1 / kg_per_roll, 4) if kg_per_roll > 0 else 0,
        }
    }


# ==================== 2. PRODUCTION REDLINE - 7% SCRAP LOCK ====================
SCRAP_LIMIT_PERCENT = 7.0  # Hard limit


class ProductionEntryRequest(BaseModel):
    wo_id: str
    quantity_produced: float
    wastage: float
    operator_id: Optional[str] = None
    shift: Optional[str] = None
    notes: Optional[str] = None


class RedlineCheckResponse(BaseModel):
    allowed: bool
    scrap_percent: float
    limit_percent: float
    message: str
    mass_balance_ok: bool
    mass_balance_variance: float
    requires_approval: bool
    approval_reason: Optional[str] = None


@router.post("/redline/check-entry")
async def check_production_entry(data: ProductionEntryRequest, current_user: dict = Depends(get_current_user)):
    """
    Production Redline: Check if entry is within 7% scrap limit
    Also performs mass-balance check
    """
    # Get work order
    wo = await db.work_orders.find_one({"id": data.wo_id}, {"_id": 0})
    if not wo:
        raise HTTPException(status_code=404, detail="Work order not found")
    
    # Calculate scrap percentage
    total_output = data.quantity_produced + data.wastage
    scrap_percent = (data.wastage / total_output * 100) if total_output > 0 else 0
    
    # Get existing entries for this WO
    existing_entries = await db.production_entries.find({"wo_id": data.wo_id}, {"_id": 0}).to_list(1000)
    total_produced = sum(e.get("quantity_produced", 0) for e in existing_entries) + data.quantity_produced
    total_wastage = sum(e.get("wastage", 0) for e in existing_entries) + data.wastage
    cumulative_scrap = (total_wastage / (total_produced + total_wastage) * 100) if (total_produced + total_wastage) > 0 else 0
    
    # Mass Balance Check
    # Raw material consumed should equal output + wastage (within tolerance)
    raw_material_issued = wo.get("raw_material_issued", 0)
    expected_output = raw_material_issued * 0.93  # 93% yield expected (7% scrap)
    mass_balance_variance = abs(total_produced - expected_output) / expected_output * 100 if expected_output > 0 else 0
    mass_balance_ok = mass_balance_variance <= 5  # 5% tolerance
    
    # Decision
    allowed = scrap_percent <= SCRAP_LIMIT_PERCENT
    requires_approval = False
    approval_reason = None
    
    if scrap_percent > SCRAP_LIMIT_PERCENT:
        requires_approval = True
        approval_reason = f"Scrap {scrap_percent:.1f}% exceeds {SCRAP_LIMIT_PERCENT}% limit"
    
    if not mass_balance_ok:
        requires_approval = True
        approval_reason = (approval_reason or "") + f" | Mass balance variance {mass_balance_variance:.1f}%"
    
    message = "Entry allowed" if allowed else f"REDLINE: Scrap exceeds {SCRAP_LIMIT_PERCENT}%. Director approval required."
    
    return RedlineCheckResponse(
        allowed=allowed and mass_balance_ok,
        scrap_percent=round(scrap_percent, 2),
        limit_percent=SCRAP_LIMIT_PERCENT,
        message=message,
        mass_balance_ok=mass_balance_ok,
        mass_balance_variance=round(mass_balance_variance, 2),
        requires_approval=requires_approval,
        approval_reason=approval_reason
    )


@router.post("/redline/override")
async def override_redline(
    wo_id: str,
    override_reason: str,
    current_user: dict = Depends(get_current_user)
):
    """Director override for redline entries"""
    if current_user['role'] not in ['admin', 'director']:
        raise HTTPException(status_code=403, detail="Only directors can override redline")
    
    override_doc = {
        "id": str(uuid.uuid4()),
        "wo_id": wo_id,
        "override_by": current_user['id'],
        "override_by_name": current_user.get('name', ''),
        "reason": override_reason,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.redline_overrides.insert_one(override_doc)
    
    return {"message": "Redline override approved", "override_id": override_doc["id"]}


# ==================== 3. CRM BUYING DNA - AI PURCHASE PATTERNS ====================
@router.get("/buying-dna/late-customers")
async def get_late_customers(current_user: dict = Depends(get_current_user)):
    """Get all customers who are late on their expected order"""
    customers = await db.customers.find({}, {"_id": 0, "id": 1, "name": 1}).to_list(1000)
    
    late_customers = []
    for customer in customers:
        dna = await get_buying_dna_for_customer(customer["id"], current_user)
        if dna.get("is_late"):
            late_customers.append({
                "customer_id": customer["id"],
                "customer_name": customer.get("name"),
                "days_late": dna.get("days_late"),
                "avg_interval": dna.get("average_order_interval_days"),
                "avg_order_value": dna.get("average_order_value"),
                "followup_message": dna.get("followup_message")
            })
    
    return sorted(late_customers, key=lambda x: x["days_late"], reverse=True)


@router.get("/buying-dna/{customer_id}")
async def get_buying_dna_for_customer(customer_id: str, current_user: dict = Depends(get_current_user)):
    """
    Analyze customer's buying pattern - frequency, items, amounts
    """
    # Get all orders for this customer
    orders = await db.invoices.find({
        "customer_id": customer_id,
        "invoice_type": "Sales",
        "status": {"$ne": "cancelled"}
    }, {"_id": 0}).sort("invoice_date", -1).to_list(1000)
    
    if len(orders) < 2:
        return {
            "customer_id": customer_id,
            "has_pattern": False,
            "message": "Not enough order history to analyze"
        }
    
    # Calculate average days between orders
    order_dates = [datetime.fromisoformat(o["invoice_date"][:10]) for o in orders if o.get("invoice_date")]
    if len(order_dates) < 2:
        return {"customer_id": customer_id, "has_pattern": False, "message": "Not enough dated orders"}
    
    intervals = []
    for i in range(len(order_dates) - 1):
        delta = (order_dates[i] - order_dates[i+1]).days
        if delta > 0:
            intervals.append(delta)
    
    avg_interval = sum(intervals) / len(intervals) if intervals else 30
    
    # Check if customer is late
    last_order_date = order_dates[0]
    days_since_last = (datetime.now() - last_order_date).days
    days_late = days_since_last - avg_interval
    is_late = days_late > 2  # Late if more than 2 days past expected
    
    # Favorite products
    product_counts = {}
    for order in orders:
        for item in order.get("items", []):
            item_name = item.get("item_name", "Unknown")
            if item_name not in product_counts:
                product_counts[item_name] = {"count": 0, "total_qty": 0, "total_value": 0}
            product_counts[item_name]["count"] += 1
            product_counts[item_name]["total_qty"] += item.get("quantity", 0)
            product_counts[item_name]["total_value"] += item.get("amount", 0)
    
    top_products = sorted(product_counts.items(), key=lambda x: x[1]["total_value"], reverse=True)[:5]
    
    # Average order value
    avg_order_value = sum(o.get("total_amount", 0) for o in orders) / len(orders)
    
    # Generate follow-up message if late
    followup_message = None
    if is_late:
        customer = await db.customers.find_one({"id": customer_id}, {"_id": 0})
        customer_name = customer.get("name", "Valued Customer") if customer else "Valued Customer"
        followup_message = f"""Hi {customer_name},

We noticed it's been {days_since_last} days since your last order. Based on your usual ordering pattern of every {int(avg_interval)} days, we wanted to check if you need any supplies.

Your frequently ordered items:
{chr(10).join([f"- {p[0]}" for p in top_products[:3]])}

Please let us know if we can assist with your next order.

Best regards,
AdhesiveFlow Team"""
    
    return {
        "customer_id": customer_id,
        "has_pattern": True,
        "average_order_interval_days": round(avg_interval, 1),
        "days_since_last_order": days_since_last,
        "expected_next_order_in": max(0, int(avg_interval - days_since_last)),
        "is_late": is_late,
        "days_late": max(0, int(days_late)),
        "average_order_value": round(avg_order_value, 2),
        "total_orders": len(orders),
        "top_products": [{"name": p[0], **p[1]} for p in top_products],
        "followup_message": followup_message,
        "last_order_date": last_order_date.isoformat()[:10]
    }


# ==================== 4. MULTI-BRANCH LEDGER - GST BRIDGE ====================
GST_STATES = {
    "GJ": {"name": "Gujarat", "code": "24", "rate": 18},
    "MH": {"name": "Maharashtra", "code": "27", "rate": 18},
    "DL": {"name": "Delhi", "code": "07", "rate": 18},
    "KA": {"name": "Karnataka", "code": "29", "rate": 18},
    "TN": {"name": "Tamil Nadu", "code": "33", "rate": 18},
    "RJ": {"name": "Rajasthan", "code": "08", "rate": 18},
}


@router.get("/gst-bridge/summary")
async def get_gst_bridge_summary(
    period: str,  # MMYYYY format
    current_user: dict = Depends(get_current_user)
):
    """
    Multi-Branch GST Summary - Consolidated view across branches
    """
    month = int(period[:2])
    year = int(period[2:])
    start_date = f"{year}-{month:02d}-01"
    end_month = month + 1 if month < 12 else 1
    end_year = year if month < 12 else year + 1
    end_date = f"{end_year}-{end_month:02d}-01"
    
    # Get all invoices for the period
    invoices = await db.invoices.find({
        "invoice_date": {"$gte": start_date, "$lt": end_date},
        "status": {"$ne": "cancelled"}
    }, {"_id": 0}).to_list(10000)
    
    # Branch-wise breakdown
    branch_summary = {}
    for inv in invoices:
        branch = inv.get("branch", inv.get("location", "HEAD_OFFICE"))
        if branch not in branch_summary:
            branch_summary[branch] = {
                "sales": {"count": 0, "taxable": 0, "cgst": 0, "sgst": 0, "igst": 0, "total": 0},
                "purchase": {"count": 0, "taxable": 0, "cgst": 0, "sgst": 0, "igst": 0, "total": 0}
            }
        
        inv_type = "sales" if inv.get("invoice_type") == "Sales" else "purchase"
        branch_summary[branch][inv_type]["count"] += 1
        branch_summary[branch][inv_type]["taxable"] += inv.get("subtotal", 0)
        branch_summary[branch][inv_type]["cgst"] += inv.get("cgst_amount", 0)
        branch_summary[branch][inv_type]["sgst"] += inv.get("sgst_amount", 0)
        branch_summary[branch][inv_type]["igst"] += inv.get("igst_amount", 0)
        branch_summary[branch][inv_type]["total"] += inv.get("total_amount", 0)
    
    # Consolidated totals
    consolidated = {
        "sales": {"count": 0, "taxable": 0, "cgst": 0, "sgst": 0, "igst": 0, "total": 0},
        "purchase": {"count": 0, "taxable": 0, "cgst": 0, "sgst": 0, "igst": 0, "total": 0}
    }
    for branch_data in branch_summary.values():
        for inv_type in ["sales", "purchase"]:
            for key in consolidated[inv_type]:
                consolidated[inv_type][key] += branch_data[inv_type][key]
    
    # GST payable
    output_tax = consolidated["sales"]["cgst"] + consolidated["sales"]["sgst"] + consolidated["sales"]["igst"]
    input_tax = consolidated["purchase"]["cgst"] + consolidated["purchase"]["sgst"] + consolidated["purchase"]["igst"]
    net_gst_payable = output_tax - input_tax
    
    return {
        "period": f"{month:02d}/{year}",
        "branch_wise": branch_summary,
        "consolidated": consolidated,
        "gst_computation": {
            "output_tax": round(output_tax, 2),
            "input_tax": round(input_tax, 2),
            "net_gst_payable": round(net_gst_payable, 2),
            "status": "PAYABLE" if net_gst_payable > 0 else "REFUND"
        }
    }


# ==================== 5. IMPORT BRIDGE - LANDED COST CALCULATOR ====================
class LandedCostRequest(BaseModel):
    fob_value_usd: float
    exchange_rate: float = 83.0
    freight_usd: float = 0
    insurance_percent: float = 1.1  # % of FOB
    basic_customs_duty_percent: float = 10
    social_welfare_surcharge_percent: float = 10  # of BCD
    igst_percent: float = 18
    clearing_charges_inr: float = 15000
    transport_to_warehouse_inr: float = 10000
    quantity_units: float = 1
    uom: str = "KG"


class LandedCostResponse(BaseModel):
    fob_value_inr: float
    freight_inr: float
    insurance_inr: float
    cif_value_inr: float
    basic_customs_duty: float
    social_welfare_surcharge: float
    igst: float
    total_duties: float
    clearing_charges: float
    transport_charges: float
    total_landed_cost: float
    landed_cost_per_unit: float
    minimum_selling_price: float  # 15% margin
    recommended_selling_price: float  # 25% margin
    breakdown: Dict[str, float]


@router.post("/import-bridge/landed-cost", response_model=LandedCostResponse)
async def calculate_landed_cost(data: LandedCostRequest, current_user: dict = Depends(get_current_user)):
    """
    Import Bridge: Calculate complete landed cost and MSP
    """
    # Step 1: FOB to INR
    fob_inr = data.fob_value_usd * data.exchange_rate
    
    # Step 2: Add freight
    freight_inr = data.freight_usd * data.exchange_rate
    
    # Step 3: Insurance (% of FOB)
    insurance_inr = fob_inr * (data.insurance_percent / 100)
    
    # Step 4: CIF Value
    cif_inr = fob_inr + freight_inr + insurance_inr
    
    # Step 5: Basic Customs Duty
    bcd = cif_inr * (data.basic_customs_duty_percent / 100)
    
    # Step 6: Social Welfare Surcharge (on BCD)
    sws = bcd * (data.social_welfare_surcharge_percent / 100)
    
    # Step 7: Assessable Value for IGST
    assessable_value = cif_inr + bcd + sws
    
    # Step 8: IGST
    igst = assessable_value * (data.igst_percent / 100)
    
    # Step 9: Total Duties
    total_duties = bcd + sws + igst
    
    # Step 10: Total Landed Cost
    total_landed = cif_inr + total_duties + data.clearing_charges_inr + data.transport_to_warehouse_inr
    
    # Per unit cost
    landed_per_unit = total_landed / data.quantity_units if data.quantity_units > 0 else 0
    
    # MSP with margins
    msp_15 = landed_per_unit * 1.15  # 15% margin minimum
    rsp_25 = landed_per_unit * 1.25  # 25% recommended
    
    return LandedCostResponse(
        fob_value_inr=round(fob_inr, 2),
        freight_inr=round(freight_inr, 2),
        insurance_inr=round(insurance_inr, 2),
        cif_value_inr=round(cif_inr, 2),
        basic_customs_duty=round(bcd, 2),
        social_welfare_surcharge=round(sws, 2),
        igst=round(igst, 2),
        total_duties=round(total_duties, 2),
        clearing_charges=round(data.clearing_charges_inr, 2),
        transport_charges=round(data.transport_to_warehouse_inr, 2),
        total_landed_cost=round(total_landed, 2),
        landed_cost_per_unit=round(landed_per_unit, 2),
        minimum_selling_price=round(msp_15, 2),
        recommended_selling_price=round(rsp_25, 2),
        breakdown={
            "fob_percent": round(fob_inr / total_landed * 100, 1),
            "freight_percent": round(freight_inr / total_landed * 100, 1),
            "duties_percent": round(total_duties / total_landed * 100, 1),
            "other_percent": round((data.clearing_charges_inr + data.transport_to_warehouse_inr) / total_landed * 100, 1)
        }
    )


# ==================== 6. DIRECTOR COCKPIT - PULSE & OVERRIDE ====================
@router.get("/cockpit/pulse")
async def get_director_pulse(current_user: dict = Depends(get_current_user)):
    """
    Director Cockpit: Complete pulse view of business
    """
    if current_user['role'] not in ['admin', 'director']:
        raise HTTPException(status_code=403, detail="Director access required")
    
    today = datetime.now(timezone.utc)
    month_start = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    
    # Cash Pulse
    ar = await db.invoices.aggregate([
        {'$match': {'invoice_type': 'Sales', 'status': {'$nin': ['paid', 'cancelled']}}},
        {'$group': {'_id': None, 'total': {'$sum': '$balance_amount'}}}
    ]).to_list(1)
    total_ar = ar[0]['total'] if ar else 0
    
    ap = await db.invoices.aggregate([
        {'$match': {'invoice_type': 'Purchase', 'status': {'$nin': ['paid', 'cancelled']}}},
        {'$group': {'_id': None, 'total': {'$sum': '$balance_amount'}}}
    ]).to_list(1)
    total_ap = ap[0]['total'] if ap else 0
    
    # Production Pulse
    work_orders = await db.work_orders.find({"status": "in_progress"}, {"_id": 0}).to_list(100)
    production_entries = await db.production_entries.find({}, {"_id": 0}).to_list(1000)
    total_produced = sum(e.get("quantity_produced", 0) for e in production_entries)
    total_wastage = sum(e.get("wastage", 0) for e in production_entries)
    avg_scrap = (total_wastage / (total_produced + total_wastage) * 100) if (total_produced + total_wastage) > 0 else 0
    
    # Redline alerts
    redline_alerts = []
    for wo in work_orders:
        wo_entries = [e for e in production_entries if e.get("wo_id") == wo.get("id")]
        wo_produced = sum(e.get("quantity_produced", 0) for e in wo_entries)
        wo_wastage = sum(e.get("wastage", 0) for e in wo_entries)
        wo_scrap = (wo_wastage / (wo_produced + wo_wastage) * 100) if (wo_produced + wo_wastage) > 0 else 0
        if wo_scrap > SCRAP_LIMIT_PERCENT:
            redline_alerts.append({
                "wo_id": wo.get("id"),
                "wo_number": wo.get("wo_number"),
                "scrap_percent": round(wo_scrap, 1),
                "limit": SCRAP_LIMIT_PERCENT
            })
    
    # Sales Pulse
    mtd_sales = await db.invoices.aggregate([
        {'$match': {'invoice_type': 'Sales', 'invoice_date': {'$gte': month_start.isoformat()[:10]}, 'status': {'$ne': 'cancelled'}}},
        {'$group': {'_id': None, 'total': {'$sum': '$total_amount'}, 'count': {'$sum': 1}}}
    ]).to_list(1)
    
    return {
        "timestamp": today.isoformat(),
        "cash_pulse": {
            "receivables": round(total_ar, 2),
            "payables": round(total_ap, 2),
            "net_position": round(total_ar - total_ap, 2),
            "health": "GOOD" if total_ar > total_ap else "ATTENTION"
        },
        "production_pulse": {
            "work_orders_active": len(work_orders),
            "avg_scrap_percent": round(avg_scrap, 1),
            "scrap_limit": SCRAP_LIMIT_PERCENT,
            "scrap_status": "OK" if avg_scrap <= SCRAP_LIMIT_PERCENT else "REDLINE",
            "redline_alerts": redline_alerts
        },
        "sales_pulse": {
            "mtd_sales": round(mtd_sales[0]['total'], 2) if mtd_sales else 0,
            "mtd_orders": mtd_sales[0]['count'] if mtd_sales else 0
        },
        "override_queue": len(redline_alerts)
    }


@router.get("/cockpit/overrides-pending")
async def get_pending_overrides(current_user: dict = Depends(get_current_user)):
    """Get all pending override requests"""
    if current_user['role'] not in ['admin', 'director']:
        raise HTTPException(status_code=403, detail="Director access required")
    
    # Get WOs that need override
    work_orders = await db.work_orders.find({"status": "in_progress"}, {"_id": 0}).to_list(100)
    production_entries = await db.production_entries.find({}, {"_id": 0}).to_list(1000)
    approved_overrides = await db.redline_overrides.find({}, {"_id": 0, "wo_id": 1}).to_list(1000)
    approved_wo_ids = [o["wo_id"] for o in approved_overrides]
    
    pending = []
    for wo in work_orders:
        if wo.get("id") in approved_wo_ids:
            continue
            
        wo_entries = [e for e in production_entries if e.get("wo_id") == wo.get("id")]
        wo_produced = sum(e.get("quantity_produced", 0) for e in wo_entries)
        wo_wastage = sum(e.get("wastage", 0) for e in wo_entries)
        wo_scrap = (wo_wastage / (wo_produced + wo_wastage) * 100) if (wo_produced + wo_wastage) > 0 else 0
        
        if wo_scrap > SCRAP_LIMIT_PERCENT:
            pending.append({
                "wo_id": wo.get("id"),
                "wo_number": wo.get("wo_number"),
                "item_name": wo.get("item_name"),
                "machine": wo.get("machine_id"),
                "scrap_percent": round(wo_scrap, 1),
                "excess_scrap": round(wo_scrap - SCRAP_LIMIT_PERCENT, 1),
                "potential_loss": round(wo_wastage * 100, 2)  # Estimated loss in INR
            })
    
    return {"pending_count": len(pending), "pending_overrides": pending}
