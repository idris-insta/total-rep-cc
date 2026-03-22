"""
SQLAlchemy Entity Models - Accounts & Finance Module
"""
from sqlalchemy import Column, String, DateTime, Boolean, Text, Integer, Float, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime, timezone

from core.database import Base
from models.entities.base import UUIDMixin, TimestampMixin


class Invoice(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "invoices"
    
    invoice_number: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    invoice_type: Mapped[str] = mapped_column(String(50), default="Sales", index=True)  # Sales, Purchase, Credit Note, Debit Note
    account_id: Mapped[str] = mapped_column(String(36), ForeignKey("accounts.id"), nullable=True, index=True)
    order_id: Mapped[str] = mapped_column(String(36), nullable=True)  # Linked order
    invoice_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)
    due_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="draft", index=True)  # draft, sent, partial, paid, overdue, cancelled
    payment_terms: Mapped[str] = mapped_column(String(255), nullable=True)
    
    # Addresses
    billing_address: Mapped[str] = mapped_column(Text, nullable=True)
    shipping_address: Mapped[str] = mapped_column(Text, nullable=True)
    
    # Line items
    items: Mapped[list] = mapped_column(JSONB, nullable=True)
    
    # Amounts
    subtotal: Mapped[float] = mapped_column(Float, default=0)
    discount_percent: Mapped[float] = mapped_column(Float, default=0)
    discount_amount: Mapped[float] = mapped_column(Float, default=0)
    taxable_amount: Mapped[float] = mapped_column(Float, default=0)
    cgst_amount: Mapped[float] = mapped_column(Float, default=0)
    sgst_amount: Mapped[float] = mapped_column(Float, default=0)
    igst_amount: Mapped[float] = mapped_column(Float, default=0)
    cess_amount: Mapped[float] = mapped_column(Float, default=0)
    tax_amount: Mapped[float] = mapped_column(Float, default=0)
    total_tax: Mapped[float] = mapped_column(Float, default=0)  # Alias for tax_amount
    grand_total: Mapped[float] = mapped_column(Float, default=0)  # Alias for total_amount
    round_off: Mapped[float] = mapped_column(Float, default=0)
    total_amount: Mapped[float] = mapped_column(Float, default=0)
    paid_amount: Mapped[float] = mapped_column(Float, default=0)
    balance_amount: Mapped[float] = mapped_column(Float, default=0)
    
    # References
    quotation_id: Mapped[str] = mapped_column(String(36), ForeignKey("quotations.id"), nullable=True)
    sales_order_id: Mapped[str] = mapped_column(String(36), nullable=True)
    po_number: Mapped[str] = mapped_column(String(100), nullable=True)  # Customer's PO
    notes: Mapped[str] = mapped_column(Text, nullable=True)
    
    # Denormalized account info for display
    account_name: Mapped[str] = mapped_column(String(255), nullable=True)
    account_gstin: Mapped[str] = mapped_column(String(20), nullable=True)
    
    # GST Details
    place_of_supply: Mapped[str] = mapped_column(String(100), nullable=True)
    reverse_charge: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # E-Invoice
    irn: Mapped[str] = mapped_column(String(100), nullable=True)  # Invoice Reference Number
    ack_number: Mapped[str] = mapped_column(String(100), nullable=True)
    ack_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    signed_invoice: Mapped[str] = mapped_column(Text, nullable=True)
    signed_qr_code: Mapped[str] = mapped_column(Text, nullable=True)
    
    terms_conditions: Mapped[str] = mapped_column(Text, nullable=True)
    notes: Mapped[str] = mapped_column(Text, nullable=True)
    internal_notes: Mapped[str] = mapped_column(Text, nullable=True)
    custom_fields: Mapped[dict] = mapped_column(JSONB, nullable=True)


class Payment(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "payments"
    
    payment_number: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    payment_type: Mapped[str] = mapped_column(String(50), default="receipt", index=True)  # receipt, payment
    account_id: Mapped[str] = mapped_column(String(36), ForeignKey("accounts.id"), nullable=True, index=True)
    payment_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)
    amount: Mapped[float] = mapped_column(Float, default=0)
    payment_mode: Mapped[str] = mapped_column(String(50), nullable=True)  # cash, cheque, bank_transfer, upi, card
    reference_number: Mapped[str] = mapped_column(String(100), nullable=True)  # Cheque number, UTR, etc.
    bank_account: Mapped[str] = mapped_column(String(100), nullable=True)
    
    # Invoice allocation
    allocations: Mapped[list] = mapped_column(JSONB, nullable=True)  # Array of invoice allocations
    
    status: Mapped[str] = mapped_column(String(50), default="completed", index=True)
    notes: Mapped[str] = mapped_column(Text, nullable=True)
    custom_fields: Mapped[dict] = mapped_column(JSONB, nullable=True)


class JournalEntry(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "journal_entries"
    
    entry_number: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    entry_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)
    entry_type: Mapped[str] = mapped_column(String(50), nullable=True)  # general, adjustment, opening, closing
    reference_type: Mapped[str] = mapped_column(String(50), nullable=True)
    reference_id: Mapped[str] = mapped_column(String(36), nullable=True)
    
    # Debit and Credit entries
    entries: Mapped[list] = mapped_column(JSONB, nullable=True)  # Array of {ledger_id, debit, credit, narration}
    
    total_debit: Mapped[float] = mapped_column(Float, default=0)
    total_credit: Mapped[float] = mapped_column(Float, default=0)
    narration: Mapped[str] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="posted")
    custom_fields: Mapped[dict] = mapped_column(JSONB, nullable=True)


class ChartOfAccounts(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "chart_of_accounts"
    
    account_code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    account_name: Mapped[str] = mapped_column(String(255), nullable=False)
    account_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)  # Asset, Liability, Equity, Revenue, Expense
    parent_id: Mapped[str] = mapped_column(String(36), ForeignKey("chart_of_accounts.id"), nullable=True)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    is_group: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    opening_balance: Mapped[float] = mapped_column(Float, default=0)
    current_balance: Mapped[float] = mapped_column(Float, default=0)
    custom_fields: Mapped[dict] = mapped_column(JSONB, nullable=True)


class Ledger(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "ledgers"
    
    ledger_code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    ledger_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    ledger_group_id: Mapped[str] = mapped_column(String(36), ForeignKey("ledger_groups.id"), nullable=True)
    account_id: Mapped[str] = mapped_column(String(36), ForeignKey("accounts.id"), nullable=True)  # Linked party
    opening_balance: Mapped[float] = mapped_column(Float, default=0)
    current_balance: Mapped[float] = mapped_column(Float, default=0)
    credit_limit: Mapped[float] = mapped_column(Float, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    custom_fields: Mapped[dict] = mapped_column(JSONB, nullable=True)


class LedgerGroup(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "ledger_groups"
    
    group_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    parent_id: Mapped[str] = mapped_column(String(36), ForeignKey("ledger_groups.id"), nullable=True)
    group_type: Mapped[str] = mapped_column(String(50), nullable=True)  # Asset, Liability, Income, Expense
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False)
    affects_gross_profit: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class LedgerEntry(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "ledger_entries"
    
    ledger_id: Mapped[str] = mapped_column(String(36), ForeignKey("ledgers.id"), nullable=False, index=True)
    entry_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)
    voucher_type: Mapped[str] = mapped_column(String(50), nullable=True)
    voucher_number: Mapped[str] = mapped_column(String(100), nullable=True, index=True)
    reference_type: Mapped[str] = mapped_column(String(50), nullable=True)
    reference_id: Mapped[str] = mapped_column(String(36), nullable=True)
    debit: Mapped[float] = mapped_column(Float, default=0)
    credit: Mapped[float] = mapped_column(Float, default=0)
    balance: Mapped[float] = mapped_column(Float, default=0)
    narration: Mapped[str] = mapped_column(Text, nullable=True)


class Expense(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "expenses"
    
    expense_number: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    expense_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)
    category: Mapped[str] = mapped_column(String(100), nullable=True, index=True)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    amount: Mapped[float] = mapped_column(Float, default=0)
    tax_amount: Mapped[float] = mapped_column(Float, default=0)
    total_amount: Mapped[float] = mapped_column(Float, default=0)
    payment_mode: Mapped[str] = mapped_column(String(50), nullable=True)
    vendor_name: Mapped[str] = mapped_column(String(255), nullable=True)
    invoice_number: Mapped[str] = mapped_column(String(100), nullable=True)
    employee_id: Mapped[str] = mapped_column(String(36), ForeignKey("employees.id"), nullable=True)
    department: Mapped[str] = mapped_column(String(100), nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="pending", index=True)
    approved_by: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    attachments: Mapped[list] = mapped_column(JSONB, nullable=True)
    custom_fields: Mapped[dict] = mapped_column(JSONB, nullable=True)
