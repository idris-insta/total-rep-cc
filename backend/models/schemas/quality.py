"""
Quality Schemas - Pydantic models for Quality module
"""
from pydantic import BaseModel
from typing import Optional, List


# ==================== QC INSPECTION SCHEMAS ====================
class TestParameter(BaseModel):
    parameter_name: str
    expected_value: Optional[str] = None
    actual_value: Optional[str] = None
    unit: Optional[str] = None
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    result: str  # pass, fail


class QCInspectionCreate(BaseModel):
    inspection_type: str  # incoming, in_process, final, customer_return
    reference_type: str  # grn, work_order, production_entry
    reference_id: str
    item_id: str
    batch_number: Optional[str] = None
    test_parameters: List[TestParameter]
    inspector: str
    notes: Optional[str] = None


class QCInspectionResponse(BaseModel):
    id: str
    inspection_number: str
    inspection_type: str
    reference_type: str
    reference_id: str
    item_id: str
    batch_number: Optional[str] = None
    test_parameters: List[dict]
    result: str  # pass, fail
    passed_tests: int
    total_tests: int
    pass_rate: float
    inspector: str
    notes: Optional[str] = None
    created_at: Optional[str] = None


# ==================== CUSTOMER COMPLAINT SCHEMAS ====================
class CustomerComplaintCreate(BaseModel):
    account_id: str
    invoice_id: Optional[str] = None
    batch_number: Optional[str] = None
    complaint_type: str  # quality, delivery, packaging, pricing, other
    description: str
    severity: str  # low, medium, high, critical


class CustomerComplaintUpdate(BaseModel):
    status: Optional[str] = None
    resolution: Optional[str] = None
    assigned_to: Optional[str] = None


class CustomerComplaintResponse(BaseModel):
    id: str
    complaint_number: str
    account_id: str
    invoice_id: Optional[str] = None
    batch_number: Optional[str] = None
    complaint_type: str
    description: str
    severity: str
    status: str
    resolution: Optional[str] = None
    resolved_at: Optional[str] = None
    created_at: Optional[str] = None


# ==================== TDS SCHEMAS ====================
class TDSCreate(BaseModel):
    item_id: str
    document_type: str  # tds, msds, coa, test_report
    document_url: str
    version: str
    notes: Optional[str] = None


class TDSResponse(BaseModel):
    id: str
    item_id: str
    document_type: str
    document_url: str
    version: str
    notes: Optional[str] = None
    created_at: Optional[str] = None


# ==================== QC PARAMETER SCHEMAS ====================
class QCParameterCreate(BaseModel):
    parameter_name: str
    category: str
    unit: Optional[str] = None
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    test_method: Optional[str] = None
    is_mandatory: bool = False


class QCParameterResponse(BaseModel):
    id: str
    parameter_name: str
    category: str
    unit: Optional[str] = None
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    test_method: Optional[str] = None
    is_mandatory: bool
    is_active: bool
    created_at: Optional[str] = None
