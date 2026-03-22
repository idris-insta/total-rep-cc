"""
Document Numbering Series Utility
Generates document numbers based on configurable series

Format: PREFIX/BRANCH/FY/SEQ
Example: INV/MH/2425/0001, PO/GJ/2425/0042

Supports:
- Branch-wise numbering
- Financial year based sequences
- Custom prefixes per document type
- Auto-increment sequences
"""

from datetime import datetime, timezone
from typing import Optional, Dict
import re


def get_financial_year(date: datetime = None) -> str:
    """
    Get financial year code (April to March)
    Returns format: '2425' for FY 2024-25
    """
    if date is None:
        date = datetime.now(timezone.utc)
    
    year = date.year
    month = date.month
    
    # FY starts in April
    if month < 4:
        start_year = year - 1
    else:
        start_year = year
    
    end_year = start_year + 1
    
    return f"{str(start_year)[-2:]}{str(end_year)[-2:]}"


def get_branch_code(branch_name: str) -> str:
    """
    Get branch code from branch name
    Maharashtra -> MH, Gujarat -> GJ, Delhi -> DL
    """
    state_codes = {
        'maharashtra': 'MH',
        'gujarat': 'GJ',
        'delhi': 'DL',
        'karnataka': 'KA',
        'tamil nadu': 'TN',
        'west bengal': 'WB',
        'uttar pradesh': 'UP',
        'rajasthan': 'RJ',
        'madhya pradesh': 'MP',
        'andhra pradesh': 'AP',
        'telangana': 'TS',
        'kerala': 'KL',
        'punjab': 'PB',
        'haryana': 'HR',
        'bihar': 'BR',
        'odisha': 'OR',
        'jharkhand': 'JH',
        'assam': 'AS',
        'chhattisgarh': 'CG',
        'goa': 'GA',
        'head office': 'HO',
        'main': 'HO',
    }
    
    branch_lower = branch_name.lower().strip()
    return state_codes.get(branch_lower, branch_name[:2].upper())


# Default document prefixes
DOCUMENT_PREFIXES = {
    'invoice': 'INV',
    'sales_invoice': 'SI',
    'purchase_invoice': 'PI',
    'quotation': 'QT',
    'sales_order': 'SO',
    'purchase_order': 'PO',
    'delivery_note': 'DN',
    'grn': 'GRN',
    'credit_note': 'CN',
    'debit_note': 'DN',
    'payment': 'PAY',
    'receipt': 'REC',
    'journal': 'JV',
    'work_order': 'WO',
    'production_entry': 'PE',
    'stock_transfer': 'ST',
    'gatepass_in': 'GPI',
    'gatepass_out': 'GPO',
    'qc_inspection': 'QC',
    'complaint': 'CMP',
    'lead': 'LD',
    'sample': 'SMP',
    'employee': 'EMP',
    'leave': 'LV',
    'payroll': 'PR',
    'expense': 'EXP',
}


async def get_next_sequence(
    db,
    doc_type: str,
    branch_code: str = 'HO',
    fy_code: str = None
) -> int:
    """
    Get next sequence number for a document type
    Uses MongoDB findAndModify for atomic increment
    """
    if fy_code is None:
        fy_code = get_financial_year()
    
    counter_id = f"{doc_type}_{branch_code}_{fy_code}"
    
    result = await db.document_counters.find_one_and_update(
        {'_id': counter_id},
        {'$inc': {'seq': 1}},
        upsert=True,
        return_document=True
    )
    
    return result.get('seq', 1)


async def generate_document_number(
    db,
    doc_type: str,
    branch_code: str = 'HO',
    custom_prefix: str = None,
    date: datetime = None
) -> str:
    """
    Generate document number with format: PREFIX/BRANCH/FY/SEQ
    
    Args:
        db: Database connection
        doc_type: Type of document (invoice, po, etc.)
        branch_code: Branch code (MH, GJ, DL)
        custom_prefix: Override default prefix
        date: Date for FY calculation
    
    Returns:
        Document number string like 'INV/MH/2425/0001'
    """
    # Get prefix
    prefix = custom_prefix or DOCUMENT_PREFIXES.get(doc_type.lower(), doc_type.upper()[:3])
    
    # Get FY code
    fy_code = get_financial_year(date)
    
    # Get next sequence
    seq = await get_next_sequence(db, doc_type, branch_code, fy_code)
    
    # Format sequence with padding
    seq_str = str(seq).zfill(4)
    
    return f"{prefix}/{branch_code}/{fy_code}/{seq_str}"


async def generate_simple_number(
    db,
    doc_type: str,
    date: datetime = None
) -> str:
    """
    Generate simple document number: PREFIX-YYYYMMDD-SEQ
    For documents that don't need branch-wise tracking
    """
    prefix = DOCUMENT_PREFIXES.get(doc_type.lower(), doc_type.upper()[:3])
    
    if date is None:
        date = datetime.now(timezone.utc)
    
    date_str = date.strftime('%Y%m%d')
    
    counter_id = f"{doc_type}_{date_str}"
    
    result = await db.document_counters.find_one_and_update(
        {'_id': counter_id},
        {'$inc': {'seq': 1}},
        upsert=True,
        return_document=True
    )
    
    seq = result.get('seq', 1)
    
    return f"{prefix}-{date_str}-{str(seq).zfill(4)}"


def parse_document_number(doc_number: str) -> Dict:
    """
    Parse document number to extract components
    
    Returns:
        Dict with prefix, branch, fy, sequence
    """
    parts = doc_number.split('/')
    
    if len(parts) == 4:
        return {
            'prefix': parts[0],
            'branch': parts[1],
            'fy': parts[2],
            'sequence': int(parts[3])
        }
    elif '-' in doc_number:
        # Simple format: PREFIX-YYYYMMDD-SEQ
        parts = doc_number.split('-')
        return {
            'prefix': parts[0],
            'date': parts[1] if len(parts) > 1 else None,
            'sequence': int(parts[2]) if len(parts) > 2 else 0
        }
    
    return {'raw': doc_number}


async def get_series_config(db, doc_type: str) -> Dict:
    """
    Get document numbering series configuration
    Allows admin to customize prefix, format, etc.
    """
    config = await db.numbering_series.find_one(
        {'doc_type': doc_type},
        {'_id': 0}
    )
    
    if not config:
        return {
            'doc_type': doc_type,
            'prefix': DOCUMENT_PREFIXES.get(doc_type.lower(), doc_type.upper()[:3]),
            'format': 'PREFIX/BRANCH/FY/SEQ',
            'seq_padding': 4,
            'branch_wise': True,
            'fy_wise': True
        }
    
    return config


async def update_series_config(db, doc_type: str, config: Dict) -> Dict:
    """
    Update document numbering series configuration
    """
    await db.numbering_series.update_one(
        {'doc_type': doc_type},
        {'$set': config},
        upsert=True
    )
    
    return await get_series_config(db, doc_type)
