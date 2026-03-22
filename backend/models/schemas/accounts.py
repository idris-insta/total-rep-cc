"""
Accounts Schemas - Pydantic models for Accounts module
"""
from pydantic import BaseModel
from typing import Optional, List


# ==================== INVOICE SCHEMAS ====================
class InvoiceItemCreate(BaseModel):
    item_id: Optional[str] = None
    description: str
    hsn_code: Optional[str] = None
    quantity: float
    unit: str = "Pcs"
    unit_price: float
    discount_percent: float = 0
    tax_percent: float = 18


class InvoiceCreate(BaseModel):
    invoice_type: str = "Sales"
    account_id: str
    order_id: Optional[str] = None
    items: List[InvoiceItemCreate]
    invoice_date: str
    due_date: str
    payment_terms: Optional[str] = None
    shipping_address: Optional[str] = None
    notes: Optional[str] = None


class InvoiceUpdate(BaseModel):
    invoice_date: Optional[str] = None
    due_date: Optional[str] = None
    payment_terms: Optional[str] = None
    shipping_address: Optional[str] = None
    notes: Optional[str] = None
    status: Optional[str] = None


class InvoiceResponse(BaseModel):
    id: str
    invoice_number: str
    invoice_type: str
    account_id: str
    account_name: Optional[str] = None
    account_gstin: Optional[str] = None
    items: List[dict]
    subtotal: float
    discount_amount: float
    taxable_amount: float
    cgst_amount: float
    sgst_amount: float
    igst_amount: float
    total_tax: float
    grand_total: float
    invoice_date: str
    due_date: str
    status: str
    paid_amount: float = 0
    balance_amount: float = 0
    created_at: Optional[str] = None


# ==================== PAYMENT SCHEMAS ====================
class PaymentInvoice(BaseModel):
    invoice_id: str
    amount: float


class PaymentCreate(BaseModel):
    payment_type: str  # receipt, payment
    account_id: str
    amount: float
    payment_date: str
    payment_mode: str  # cash, cheque, bank_transfer, upi, card
    bank_name: Optional[str] = None
    cheque_no: Optional[str] = None
    cheque_date: Optional[str] = None
    transaction_ref: Optional[str] = None
    invoices: List[PaymentInvoice] = []
    tds_amount: float = 0
    tds_section: Optional[str] = None
    notes: Optional[str] = None


class PaymentResponse(BaseModel):
    id: str
    payment_number: str
    payment_type: str
    account_id: str
    account_name: Optional[str] = None
    amount: float
    payment_date: str
    payment_mode: str
    status: str
    created_at: Optional[str] = None


# ==================== JOURNAL ENTRY SCHEMAS ====================
class JournalLine(BaseModel):
    account_code: str
    account_name: Optional[str] = None
    debit: float = 0
    credit: float = 0
    narration: Optional[str] = None


class JournalEntryCreate(BaseModel):
    entry_date: str
    reference: Optional[str] = None
    narration: str
    lines: List[JournalLine]


class JournalEntryResponse(BaseModel):
    id: str
    entry_number: str
    entry_date: str
    narration: str
    lines: List[dict]
    total_debit: float
    total_credit: float
    status: str
    created_at: Optional[str] = None
