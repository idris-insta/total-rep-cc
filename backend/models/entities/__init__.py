"""
SQLAlchemy Entity Models Package
All database models for PostgreSQL
"""

# Base and User models
from models.entities.base import (
    Base,
    UUIDMixin,
    TimestampMixin,
    User,
    Role,
    Lead,
    Account,
    Quotation,
    Sample,
    Followup
)

# Inventory models
from models.entities.inventory import (
    Item,
    Warehouse,
    Stock,
    StockTransfer,
    StockAdjustment,
    Batch,
    BinLocation,
    StockLedger
)

# Production models
from models.entities.production import (
    Machine,
    OrderSheet,
    WorkOrder,
    ProductionEntry,
    RMRequisition,
    WorkOrderStage,
    StageEntry
)

# Accounts & Finance models
from models.entities.accounts import (
    Invoice,
    Payment,
    JournalEntry,
    ChartOfAccounts,
    Ledger,
    LedgerGroup,
    LedgerEntry,
    Expense
)

# Procurement models
from models.entities.procurement import (
    Supplier,
    PurchaseOrder,
    PurchaseRequisition,
    GRN,
    LandingCost
)

# HRMS models
from models.entities.hrms import (
    Employee,
    Attendance,
    LeaveRequest,
    LeaveType,
    SalaryStructure,
    Payroll,
    Loan,
    Holiday
)

# Quality, Sales, Settings, and Other models
from models.entities.other import (
    QCInspection,
    QCParameter,
    CustomerComplaint,
    TDSDocument,
    SalesTarget,
    IncentiveSlab,
    IncentivePayout,
    SalesAchievement,
    FieldConfiguration,
    SystemSetting,
    CompanyProfile,
    Branch,
    NumberSeries,
    Document,
    DriveFolder,
    DriveFile,
    Notification,
    ActivityLog,
    ApprovalRequest,
    ChatRoom,
    ChatMessage,
    EInvoice,
    EWayBill,
    Transporter,
    Gatepass,
    DeliveryChallan,
    AIQuery,
    CustomReport
)

__all__ = [
    # Base
    'Base', 'UUIDMixin', 'TimestampMixin',
    # Auth
    'User', 'Role',
    # CRM
    'Lead', 'Account', 'Quotation', 'Sample', 'Followup',
    # Inventory
    'Item', 'Warehouse', 'Stock', 'StockTransfer', 'StockAdjustment', 'Batch', 'BinLocation', 'StockLedger',
    # Production
    'Machine', 'OrderSheet', 'WorkOrder', 'ProductionEntry', 'RMRequisition', 'WorkOrderStage', 'StageEntry',
    # Accounts
    'Invoice', 'Payment', 'JournalEntry', 'ChartOfAccounts', 'Ledger', 'LedgerGroup', 'LedgerEntry', 'Expense',
    # Procurement
    'Supplier', 'PurchaseOrder', 'PurchaseRequisition', 'GRN', 'LandingCost',
    # HRMS
    'Employee', 'Attendance', 'LeaveRequest', 'LeaveType', 'SalaryStructure', 'Payroll', 'Loan', 'Holiday',
    # Quality
    'QCInspection', 'QCParameter', 'CustomerComplaint', 'TDSDocument',
    # Sales Incentives
    'SalesTarget', 'IncentiveSlab', 'IncentivePayout', 'SalesAchievement',
    # Settings
    'FieldConfiguration', 'SystemSetting', 'CompanyProfile', 'Branch', 'NumberSeries',
    # Documents
    'Document', 'DriveFolder', 'DriveFile',
    # Activity
    'Notification', 'ActivityLog', 'ApprovalRequest',
    # Chat
    'ChatRoom', 'ChatMessage',
    # GST/E-Invoice
    'EInvoice', 'EWayBill', 'Transporter',
    # Delivery
    'Gatepass', 'DeliveryChallan',
    # AI
    'AIQuery', 'CustomReport',
]
