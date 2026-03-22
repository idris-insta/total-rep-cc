"""
UOM Converter Utility - Dimensional Physics Engine
Handles conversions between KG, SQM, and PCS for adhesive tape industry

Key Formulas:
- SQM = (Width_mm / 1000) * (Length_m)
- Weight (KG) = SQM * GSM / 1000
- PCS = Total_Length / Length_per_piece

GSM (Grams per Square Meter) varies by product type:
- BOPP: 18-25 GSM
- PVC: 60-120 GSM
- Masking: 80-140 GSM
- Cloth: 150-280 GSM
- Foam: 200-800 GSM (depending on thickness)
"""

from typing import Dict, Optional, Tuple
from pydantic import BaseModel
import math


class DimensionalItem(BaseModel):
    """Item with dimensional properties for conversion"""
    thickness_microns: Optional[float] = None  # Thickness in microns
    width_mm: Optional[float] = None  # Width in millimeters
    length_m: Optional[float] = None  # Length in meters
    gsm: Optional[float] = None  # Grams per square meter
    density: Optional[float] = None  # Density g/cm3 for thickness-based calc
    item_type: str = "BOPP"  # BOPP, PVC, Masking, Cloth, Foam, etc.


# Default GSM values by product type
DEFAULT_GSM = {
    "BOPP": 22,
    "PVC": 90,
    "Masking": 110,
    "Cloth": 200,
    "Foam": 400,
    "Double-Sided": 100,
    "Kraft": 120,
    "Duct": 180,
    "Aluminum": 80,
    "Polyester": 25,
}

# Default density (g/cm3) for thickness-based GSM calculation
DEFAULT_DENSITY = {
    "BOPP": 0.91,
    "PVC": 1.35,
    "Masking": 1.0,
    "Cloth": 1.1,
    "Foam": 0.15,
    "Double-Sided": 1.1,
    "Kraft": 0.7,
    "Duct": 1.2,
    "Aluminum": 2.7,
    "Polyester": 1.39,
}


def calculate_gsm_from_thickness(thickness_microns: float, density: float) -> float:
    """
    Calculate GSM from thickness and density
    GSM = thickness (mm) * density (g/cm3) * 1000
    thickness_microns / 1000 = thickness_mm
    """
    thickness_mm = thickness_microns / 1000
    return thickness_mm * density * 1000


def calculate_sqm(width_mm: float, length_m: float) -> float:
    """
    Calculate Square Meters from Width (mm) and Length (m)
    SQM = (Width_mm / 1000) * Length_m
    """
    width_m = width_mm / 1000
    return width_m * length_m


def sqm_to_kg(sqm: float, gsm: float) -> float:
    """
    Convert Square Meters to Kilograms
    KG = SQM * GSM / 1000
    """
    return (sqm * gsm) / 1000


def kg_to_sqm(kg: float, gsm: float) -> float:
    """
    Convert Kilograms to Square Meters
    SQM = KG * 1000 / GSM
    """
    if gsm <= 0:
        return 0
    return (kg * 1000) / gsm


def sqm_to_pcs(total_sqm: float, width_mm: float, length_m: float) -> int:
    """
    Convert total SQM to number of pieces
    Each piece = (width_mm/1000) * length_m SQM
    """
    sqm_per_piece = calculate_sqm(width_mm, length_m)
    if sqm_per_piece <= 0:
        return 0
    return int(total_sqm / sqm_per_piece)


def pcs_to_sqm(pcs: int, width_mm: float, length_m: float) -> float:
    """
    Convert number of pieces to total SQM
    """
    sqm_per_piece = calculate_sqm(width_mm, length_m)
    return pcs * sqm_per_piece


def convert_all_uom(
    quantity: float,
    from_uom: str,
    width_mm: float,
    length_m: float,
    gsm: Optional[float] = None,
    item_type: str = "BOPP"
) -> Dict[str, float]:
    """
    Master conversion function - converts quantity to all UOMs
    
    Args:
        quantity: The quantity to convert
        from_uom: Source UOM ('KG', 'SQM', 'PCS', 'ROLL', 'MTR')
        width_mm: Width in millimeters
        length_m: Length in meters (per piece/roll)
        gsm: Grams per square meter (uses default if not provided)
        item_type: Product type for default GSM lookup
    
    Returns:
        Dict with 'kg', 'sqm', 'pcs', 'mtrs' values
    """
    # Use default GSM if not provided
    if gsm is None or gsm <= 0:
        gsm = DEFAULT_GSM.get(item_type, 50)
    
    sqm_per_piece = calculate_sqm(width_mm, length_m) if width_mm and length_m else 0
    
    result = {
        'kg': 0.0,
        'sqm': 0.0,
        'pcs': 0,
        'mtrs': 0.0,
        'rolls': 0
    }
    
    from_uom = from_uom.upper()
    
    if from_uom == 'KG':
        result['kg'] = quantity
        result['sqm'] = kg_to_sqm(quantity, gsm)
        if sqm_per_piece > 0:
            result['pcs'] = int(result['sqm'] / sqm_per_piece)
            result['rolls'] = result['pcs']
        if width_mm > 0:
            result['mtrs'] = result['sqm'] / (width_mm / 1000)
    
    elif from_uom == 'SQM':
        result['sqm'] = quantity
        result['kg'] = sqm_to_kg(quantity, gsm)
        if sqm_per_piece > 0:
            result['pcs'] = int(quantity / sqm_per_piece)
            result['rolls'] = result['pcs']
        if width_mm > 0:
            result['mtrs'] = quantity / (width_mm / 1000)
    
    elif from_uom in ['PCS', 'ROLL', 'ROLLS']:
        result['pcs'] = int(quantity)
        result['rolls'] = int(quantity)
        if sqm_per_piece > 0:
            result['sqm'] = quantity * sqm_per_piece
            result['kg'] = sqm_to_kg(result['sqm'], gsm)
        if length_m > 0:
            result['mtrs'] = quantity * length_m
    
    elif from_uom in ['MTR', 'MTRS', 'M']:
        result['mtrs'] = quantity
        if width_mm > 0:
            result['sqm'] = quantity * (width_mm / 1000)
            result['kg'] = sqm_to_kg(result['sqm'], gsm)
        if length_m > 0:
            result['pcs'] = int(quantity / length_m)
            result['rolls'] = result['pcs']
    
    # Round for display
    result['kg'] = round(result['kg'], 3)
    result['sqm'] = round(result['sqm'], 3)
    result['mtrs'] = round(result['mtrs'], 2)
    
    return result


def calculate_jumbo_to_slits(
    jumbo_width_mm: float,
    jumbo_length_m: float,
    slit_width_mm: float,
    slit_length_m: float,
    wastage_percent: float = 2.0
) -> Dict[str, any]:
    """
    Calculate how many slit rolls can be produced from a jumbo roll
    Used in Converting stage (Direct Slitting or Rewinding)
    
    Returns:
        Dict with slits_per_width, slits_per_length, total_slits, wastage_mm
    """
    # How many slits fit across the width
    slits_per_width = int(jumbo_width_mm / slit_width_mm)
    width_wastage = jumbo_width_mm - (slits_per_width * slit_width_mm)
    
    # How many slits fit along the length
    slits_per_length = int(jumbo_length_m / slit_length_m) if slit_length_m > 0 else 1
    
    # Total slits possible
    total_slits = slits_per_width * slits_per_length
    
    # Apply wastage factor
    effective_slits = int(total_slits * (1 - wastage_percent / 100))
    
    return {
        'slits_per_width': slits_per_width,
        'slits_per_length': slits_per_length,
        'total_theoretical': total_slits,
        'total_effective': effective_slits,
        'width_wastage_mm': width_wastage,
        'wastage_percent_applied': wastage_percent
    }


def validate_weight_integrity(
    declared_kg: float,
    sqm: float,
    gsm: float,
    tolerance_percent: float = 5.0
) -> Tuple[bool, float, str]:
    """
    Validate weight integrity - check if declared weight matches calculated weight
    Used for GRN verification and quality checks
    
    Returns:
        Tuple of (is_valid, deviation_percent, message)
    """
    calculated_kg = sqm_to_kg(sqm, gsm)
    
    if calculated_kg == 0:
        return False, 0, "Cannot calculate weight - missing dimensions"
    
    deviation = abs(declared_kg - calculated_kg)
    deviation_percent = (deviation / calculated_kg) * 100
    
    is_valid = deviation_percent <= tolerance_percent
    
    if is_valid:
        message = f"Weight OK: Declared {declared_kg:.3f} KG, Calculated {calculated_kg:.3f} KG (Deviation: {deviation_percent:.2f}%)"
    else:
        message = f"Weight MISMATCH: Declared {declared_kg:.3f} KG, Calculated {calculated_kg:.3f} KG (Deviation: {deviation_percent:.2f}% exceeds {tolerance_percent}% tolerance)"
    
    return is_valid, deviation_percent, message


def calculate_invoice_weight(items: list) -> Dict[str, float]:
    """
    Calculate total material weight for an invoice (for logistics)
    
    Args:
        items: List of invoice items with qty, width_mm, length_m, gsm, uom
    
    Returns:
        Dict with total_kg, total_sqm, total_pcs
    """
    total_kg = 0.0
    total_sqm = 0.0
    total_pcs = 0
    
    for item in items:
        qty = item.get('quantity', 0)
        width = item.get('width_mm', 0)
        length = item.get('length_m', 0)
        gsm = item.get('gsm', 50)
        uom = item.get('uom', 'PCS')
        item_type = item.get('item_type', 'BOPP')
        
        converted = convert_all_uom(qty, uom, width, length, gsm, item_type)
        
        total_kg += converted['kg']
        total_sqm += converted['sqm']
        total_pcs += converted['pcs']
    
    return {
        'total_kg': round(total_kg, 3),
        'total_sqm': round(total_sqm, 3),
        'total_pcs': total_pcs
    }
