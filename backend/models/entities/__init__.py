"""
SQLAlchemy Entity Models Package
All database models for PostgreSQL

Load order matters for FK resolution:
  1. base / other (User, Branch, ChartOfAccounts)
  2. inventory (Item, Warehouse)
  3. accounts (Invoice, JournalEntry)
  4. procurement (PurchaseOrder, GRN)
  5. hrms (Employee, LeaveType, SalaryStructure)
  6. production (Machine, WorkOrder)
  7. dimensional_gl (CostCenter, Project, ProductLine, GeneralLedger)
  8. item_variants (ItemSKUTemplate, ItemVariant)
  9. manufacturing_physics (BOM, CoatingOrder, JumboRoll, SlittingOrder)
 10. hrms_extended (LeaveBalance, PayrollRun, FixedAsset, ...)
 11. procurement_full (PurchaseIndent, GoodsReceivedNote, PurchaseInvoice, ...)
 12. ai_agents (AIAgent, BuyingDNAProfile, DocumentCapture, ...)
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

# ── NEW PHASE-1 MODULES ──────────────────────────────────────────────────────

# Dimensional GL (CostCenter, Project, ProductLine, GeneralLedger, FiscalYear,
#                  BudgetAllocation, ApprovalWorkflow)
from models.entities.dimensional_gl import (
    CostCenter,
    Project,
    ProductLine,
    GeneralLedger,
    FiscalYear,
    BudgetAllocation,
    ApprovalWorkflow,
)

# SKU Templates, Variants, Multi-UOM, Price Lists
from models.entities.item_variants import (
    ItemGroup,
    UOMConversion,
    ItemUOMProfile,
    ItemSKUTemplate,
    ItemVariant,
    PriceList,
    PriceListItem,
)

# Manufacturing Physics Engine
from models.entities.manufacturing_physics import (
    BillOfMaterials,
    BOMItem,
    AdhesiveMixFormula,
    CoatingOrder,
    JumboRoll,
    SlittingOrder,
    ProductionShiftLog,
    ScrapEntry,
)

# HRMS Extended + Fixed Assets
from models.entities.hrms_extended import (
    LeaveBalance,
    LeaveApplication,
    ShiftMaster,
    EmployeeShiftRoster,
    AttendanceRecord,
    EmployeeSalaryAssignment,
    PayrollRun,
    PayslipEntry,
    EmployeeLoan,
    AssetCategory,
    FixedAsset,
    AssetDepreciationEntry,
)

# Full Procurement Chain
from models.entities.procurement_full import (
    PurchaseIndent,
    PurchaseEnquiry,
    VendorQuotation,
    GoodsReceivedNote,
    PurchaseInvoice,
    LandedCostVoucher,
)

# AI Agent Layer
from models.entities.ai_agents import (
    AIAgent,
    AgentRunLog,
    TaskEscalation,
    BuyingDNAProfile,
    ReorderAlert,
    DocumentCapture,
    AIInsight,
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
    # AI (legacy)
    'AIQuery', 'CustomReport',
    # ── Phase 1: Dimensional GL ──────────────────────────────────────────
    'CostCenter', 'Project', 'ProductLine',
    'GeneralLedger', 'FiscalYear', 'BudgetAllocation', 'ApprovalWorkflow',
    # ── Phase 1: SKU & Multi-UOM ─────────────────────────────────────────
    'ItemGroup', 'UOMConversion', 'ItemUOMProfile',
    'ItemSKUTemplate', 'ItemVariant',
    'PriceList', 'PriceListItem',
    # ── Phase 1: Manufacturing Physics ───────────────────────────────────
    'BillOfMaterials', 'BOMItem', 'AdhesiveMixFormula',
    'CoatingOrder', 'JumboRoll',
    'SlittingOrder', 'ProductionShiftLog', 'ScrapEntry',
    # ── Phase 1: HRMS Extended + Assets ──────────────────────────────────
    'LeaveBalance', 'LeaveApplication',
    'ShiftMaster', 'EmployeeShiftRoster', 'AttendanceRecord',
    'EmployeeSalaryAssignment', 'PayrollRun', 'PayslipEntry', 'EmployeeLoan',
    'AssetCategory', 'FixedAsset', 'AssetDepreciationEntry',
    # ── Phase 1: Full Procurement Chain ──────────────────────────────────
    'PurchaseIndent', 'PurchaseEnquiry', 'VendorQuotation',
    'GoodsReceivedNote', 'PurchaseInvoice', 'LandedCostVoucher',
    # ── Phase 1: AI Agent Layer ───────────────────────────────────────────
    'AIAgent', 'AgentRunLog', 'TaskEscalation',
    'BuyingDNAProfile', 'ReorderAlert',
    'DocumentCapture', 'AIInsight',
]
