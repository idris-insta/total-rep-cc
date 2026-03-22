# InstaBiz Industrial ERP - Product Requirements Document

## Overview
InstaBiz Industrial ERP is a comprehensive enterprise resource planning system specifically designed for the **Adhesive Tapes & Sealants industry**. The system integrates ERP, CRM, HRMS, Accounts, Production, Quality, and AI-powered Business Intelligence modules.

## The 6 Pillars of AdhesiveFlow ERP ✅ COMPLETE

### 1. Physics Engine (The Master Math)
**File:** `/app/backend/routes/core_engine.py`
- Auto-converts between Weight (KG), Area (SQM), and Pieces (PCS)
- Formula: KG = SQM × thickness_m × density
- Supports: KG, SQM, PCS, ROL, MTR
- API: `POST /api/core/physics/convert`

### 2. Production Redline (The Guardrail)
- Hard lock if scrap exceeds 7%
- Mass-Balance check (raw material vs output)
- Director override capability
- APIs: `POST /api/core/redline/check-entry`, `POST /api/core/redline/override`

### 3. CRM Buying DNA (The Hunter) ✅ ENHANCED
- AI learns customer purchase frequency
- Alerts if customer is 2+ days late
- Auto-drafts WhatsApp follow-up messages
- Full Buying DNA Dashboard with pattern analysis
- APIs: 
  - `GET /api/buying-dna/patterns` - All customer patterns with urgency scoring
  - `GET /api/buying-dna/dashboard` - Dashboard summary
  - `POST /api/buying-dna/followup-log` - Log follow-up actions
- Frontend: `/buying-dna` - Full UI with search, filters, WhatsApp integration

### 4. Multi-Branch Ledger (The Tax Bridge)
- Handles GST for Gujarat, Mumbai, Delhi
- Treats business as one whole, tax records separate
- Branch-wise and consolidated views
- API: `GET /api/core/gst-bridge/summary`

### 5. Import Bridge (The Margin Protector)
- Enter container cost → Auto-calculates Landed Cost
- Shows MSP (Minimum Selling Price) with 15% margin
- Shows RSP (Recommended Selling Price) with 25% margin
- API: `POST /api/core/import-bridge/landed-cost`

### 6. Director Cockpit (The Command Center)
- Cash Pulse (AR/AP position)
- Production Pulse (Scrap %, Active WOs, Redline alerts)
- Sales Pulse (MTD Sales, Orders)
- Override Queue with approval buttons
- APIs: `GET /api/core/cockpit/pulse`, `GET /api/core/cockpit/overrides-pending`

---

## Core Logic
**Meta-Data Driven Architecture** (100% customizable fields) with a **Dimensional Physics Engine** (KG ↔ SQM ↔ PCS conversions).

## Tech Stack
- **Frontend:** React 19, Tailwind CSS, Shadcn UI, react-beautiful-dnd, **Vite** (migrated from CRA/CRACO - January 2026)
- **Backend:** FastAPI (Python) with Layered Architecture (API → Service → Repository)
- **Database:** **PostgreSQL 15** with SQLAlchemy 2.0 async (migrated from MongoDB - February 2026)
- **Authentication:** JWT with Role-Based Access Control (RBAC)
- **AI Integration:** Gemini 3 Flash via Emergent LLM Key

---

## Module Status

### Module 1: Dimensional Item Master ✅ ENHANCED
**Feature:** Multi-UOM Dimensional Tracking

**Implemented:**
- Item codes, names, categories (Raw Material, Semi-Finished, Finished Goods, Packaging)
- Item types (BOPP, Masking, Double-Sided, Cloth, PVC, Foam)
- Specifications: Thickness (Microns), Width (MM), Length (Mtrs), Color, Adhesive Type
- **NEW: GSM field** for weight calculation
- **NEW: Dual-UOM stock tracking** (stock_kg, stock_sqm, stock_pcs)
- **NEW: UOM Conversion endpoint** `/api/inventory/items/{id}/convert-uom`
- MSP (Min Sale Price) and Last Landed Rate fields

**UOM Converter Utility:** `/app/backend/utils/uom_converter.py`
- `convert_all_uom()` - Master conversion function
- `calculate_sqm()` - Width × Length to SQM
- `sqm_to_kg()` / `kg_to_sqm()` - Weight conversions
- `calculate_jumbo_to_slits()` - Production yield calculation
- `validate_weight_integrity()` - GRN verification

---

### Module 2: Multi-Branch & Multi-GST Accounting ✅ NEW
**File:** `/app/backend/routes/branches.py`

**Implemented:**
- Branch entity with state, GSTIN, address
- Branch-Bridge Ledger for inter-branch transactions
- Individual Branch Dashboards (`/api/branches/{id}/dashboard`)
- Consolidated Director Dashboard (`/api/branches/consolidated/dashboard`)
- Tax numbering series per branch

**Document Numbering:** `/app/backend/utils/document_numbering.py`
- Format: `PREFIX/BRANCH/FY/SEQ` (e.g., INV/MH/2425/0001)
- Financial year calculation (April to March)
- Branch code extraction from state
- Configurable series per document type

---

### Module 3: Two-Stage Production Engine ✅ NEW
**File:** `/app/backend/routes/production_v2.py`

**Stage 1: Coating (Chemical transformation)**
- Water-Based (BOPP), Hotmelt (Single/Double Side), PVC
- Input: Film + Adhesive + Pigment + Liner
- Output: Coated Jumbo rolls (SQM)

**Stage 2: Converting (Physical transformation)**
- Process A: Direct Slitting (Jumbo → Finished Boxes)
- Process B: Rewinding & Cutting (Jumbo → Log Roll → PCS)

**Features:**
- RM Requisition system (deducts from inventory)
- **7% Redline Guard** - Auto-locks if scrap exceeds 7%, requires Director approval
- Batch tracking throughout

**Endpoints:**
- `POST /api/production-v2/rm-requisitions` - Create RM requisition
- `PUT /api/production-v2/rm-requisitions/{id}/issue` - Issue materials
- `POST /api/production-v2/coating-batches` - Create coating batch
- `PUT /api/production-v2/coating-batches/{id}/complete` - Complete with scrap check
- `POST /api/production-v2/converting-jobs` - Create converting job
- `GET /api/production-v2/summary/{wo_id}` - Full production summary

---

### Module 4: 8-Stage CRM & Account Success ✅ COMPLETED
**Files:** `/app/backend/routes/crm.py`, `/app/frontend/src/pages/LeadsPage.js`

**Pipeline:** New Lead → Prospect → Enquiry → Negotiation → Finalization → Quotation → Converted → Regular Customer

**Implemented:**
- Kanban board with drag-and-drop
- District field + State dropdown
- Pincode auto-fill (City, State, District)
- Customer Type & Assign To fields
- Lead assignment with hierarchical visibility
- Quotation creation from leads
- Multi-item Samples

---

### Module 5: Gatepass System ✅ NEW
**File:** `/app/backend/routes/gatepass.py`

**Features:**
- Inward Gatepass (linked to GRN)
- Outward Gatepass (linked to Delivery Note)
- Transporter Master
- Vehicle & Driver tracking
- Returnable/Non-returnable items
- LR Number tracking

**Endpoints:**
- `POST /api/gatepass/` - Create gatepass
- `GET /api/gatepass/` - List with filters
- `PUT /api/gatepass/{id}/approve` - Approve gatepass
- `PUT /api/gatepass/{id}/complete` - Mark completed
- `GET /api/gatepass/vehicle-log` - Vehicle movement history

---

### Module 6: Expense & Financial Control ✅ NEW
**File:** `/app/backend/routes/expenses.py`

**Features:**
- 12 Default Expense Buckets (Exhibitions, Marketing, Utilities, etc.)
- Budget tracking per bucket
- Expense entries with approval workflow
- Reimbursement tracking
- Branch-wise expense analytics

**Endpoints:**
- `POST /api/expenses/buckets/bootstrap` - Initialize default buckets
- `POST /api/expenses/entries` - Create expense entry
- `PUT /api/expenses/entries/{id}/submit` - Submit for approval
- `PUT /api/expenses/entries/{id}/approve` - Approve expense
- `GET /api/expenses/analytics/by-bucket` - Analytics by category
- `GET /api/expenses/analytics/trend` - Monthly trend

---

### Module 7: HRMS (Performance-Linked) ✅ ENHANCED

#### 7a. Payroll Module ✅ NEW
**File:** `/app/backend/routes/payroll.py`

**Features:**
- Dual Salary (Daily/Monthly wage types)
- Attendance-to-Payroll linking
- Statutory Deductions:
  - PF: 12% employee + 12% employer (wage ceiling ₹15,000)
  - ESI: 0.75% employee + 3.25% employer (wage ceiling ₹21,000)
  - PT: Maharashtra slabs (₹0/₹175/₹200)
  - TDS: Configurable percentage
- Salary Structure per employee
- Bulk payroll processing
- Payslip generation

**Endpoints:**
- `POST /api/payroll/salary-structures` - Create salary structure
- `POST /api/payroll/process` - Process individual payroll
- `POST /api/payroll/process-bulk` - Bulk processing
- `GET /api/payroll/{id}/payslip` - Generate payslip data
- `PUT /api/payroll/{id}/approve` - Approve (requires approval)

#### 7b. Employee Document Vault ✅ NEW
**File:** `/app/backend/routes/employee_vault.py`

**Document Types:** Aadhaar, PAN, Passport, Driving License, Educational Certificates, Bank Documents, etc.

**Features:**
- File upload with employee folders
- Document verification workflow
- Expiry date tracking with alerts
- Asset Assignment tracking (laptop, mobile, vehicle, ID card)
- Complete vault summary per employee

**Endpoints:**
- `POST /api/employee-vault/documents` - Upload document
- `GET /api/employee-vault/documents` - List documents
- `PUT /api/employee-vault/documents/{id}/verify` - Verify document
- `GET /api/employee-vault/documents/expiring` - Expiring documents
- `POST /api/employee-vault/assets` - Assign asset
- `PUT /api/employee-vault/assets/{id}/return` - Return asset
- `GET /api/employee-vault/{emp_id}/vault-summary` - Complete summary

#### 7c. Sales Incentives ✅ NEW
**File:** `/app/backend/routes/sales_incentives.py`

**Features:**
- Target Setting (Monthly/Quarterly/Yearly)
- 5 Default Incentive Slabs:
  - Below Target (0-80%): 0%
  - 80-100%: 1% of achieved
  - 100-120%: 2% of achieved
  - 120-150%: 3% of achieved
  - Super Achiever (150%+): 5% of achieved
- Auto-bonus for exceeding target (5% of excess)
- Incentive payout tracking
- Sales Leaderboard

**Endpoints:**
- `POST /api/sales-incentives/slabs/bootstrap` - Initialize slabs
- `POST /api/sales-incentives/targets` - Create target
- `PUT /api/sales-incentives/targets/{id}/update-achievement` - Update achievement
- `POST /api/sales-incentives/calculate/{target_id}` - Calculate incentive
- `GET /api/sales-incentives/leaderboard` - Sales leaderboard

---

### Module 8: Procurement (Local & Import) ✅ ENHANCED

#### Import Bridge ✅ NEW
**File:** `/app/backend/routes/import_bridge.py`

**Features:**
- Import PO with foreign currency
- Multi-currency support (USD, EUR, GBP, CNY, JPY)
- Shipping terms (FOB, CIF, CNF, EXW)
- LC/TT payment tracking

**Landing Cost Calculator:**
- Basic Customs Duty + Social Welfare Cess
- IGST, Anti-dumping duty, Safeguard duty
- Ocean Freight, Insurance, Local Freight
- CHA charges, Port charges, Documentation
- Forex gain/loss calculation
- Final Landed INR Rate per item
- **Auto-update MSP** on finalization

**Endpoints:**
- `POST /api/imports/purchase-orders` - Create import PO
- `POST /api/imports/landing-cost` - Calculate landing cost
- `PUT /api/imports/landing-cost/{id}/finalize` - Finalize & update MSP
- `GET /api/imports/exchange-rates` - Get rates
- `POST /api/imports/exchange-rates` - Update rate

---

### Module 9: Power Settings (Metadata Heart) ✅ COMPLETED
**File:** `/app/backend/routes/customization.py`

**Features:**
- Custom Field Registry
- Report Templates
- Dynamic field addition to any module

---

### Module 10: Director Command Center ✅ NEW
**File:** `/app/backend/routes/director_dashboard.py`

**The 10th Screen - Consolidated Pulse View**

**Cash Pulse:**
- Total AR/AP
- Overdue amounts
- Cash & Bank balance
- AR/AP Aging (0-30, 31-60, 61-90, 90+ days)

**Production Pulse:**
- Work orders in progress
- Target vs Completed
- Average scrap % vs 7% standard
- Machines running/idle
- Pending approvals (Redline alerts)

**Sales Pulse:**
- MTD/YTD Sales vs Target
- Achievement %
- Average order value
- Orders today/this month
- Top 5 products & customers

**Alerts Dashboard:**
- Pending approvals
- Overdue invoices (>30 days)
- Low stock alerts
- Expiring documents

**Endpoints:**
- `GET /api/director/cash-pulse`
- `GET /api/director/production-pulse`
- `GET /api/director/sales-pulse`
- `GET /api/director/alerts`
- `GET /api/director/summary` - Complete dashboard

---

## File Structure
```
/app/
├── backend/
│   ├── routes/
│   │   ├── crm.py                 # ✅ CRM Module
│   │   ├── inventory.py           # ✅ Inventory (Enhanced with UOM)
│   │   ├── production.py          # ✅ Basic Production
│   │   ├── production_v2.py       # ✅ NEW: Two-Stage Production
│   │   ├── procurement.py         # ✅ Local Procurement
│   │   ├── accounts.py            # ✅ Accounts & COA
│   │   ├── hrms.py                # ✅ Basic HRMS
│   │   ├── quality.py             # ✅ Quality Module
│   │   ├── dashboard.py           # ✅ General Dashboard
│   │   ├── settings.py            # ✅ User Settings
│   │   ├── customization.py       # ✅ Custom Fields
│   │   ├── documents.py           # ✅ Document Upload
│   │   ├── master_data.py         # ✅ Master Data
│   │   ├── permissions.py         # ✅ RBAC
│   │   ├── approvals.py           # ✅ Approval System
│   │   ├── reports.py             # ✅ Reports
│   │   ├── branches.py            # ✅ NEW: Multi-Branch
│   │   ├── gatepass.py            # ✅ NEW: Gatepass
│   │   ├── expenses.py            # ✅ NEW: Expense Buckets
│   │   ├── payroll.py             # ✅ NEW: Payroll
│   │   ├── employee_vault.py      # ✅ NEW: Document Vault
│   │   ├── sales_incentives.py    # ✅ NEW: Sales Incentives
│   │   ├── import_bridge.py       # ✅ NEW: Import & Landing Cost
│   │   └── director_dashboard.py  # ✅ NEW: Director Command Center
│   └── utils/
│       ├── uom_converter.py       # ✅ NEW: Dimensional Physics Engine
│       ├── document_numbering.py  # ✅ NEW: Doc Numbering Series
│       └── permissions.py         # ✅ Permission Utils
├── frontend/
│   └── src/
│       └── pages/
│           ├── Dashboard.js       # ✅ Main Dashboard
│           ├── CRM.js             # ✅ CRM Module
│           ├── LeadsPage.js       # ✅ Leads Kanban
│           ├── Inventory.js       # ✅ Inventory
│           ├── Procurement.js     # ✅ Procurement
│           ├── Production.js      # ✅ Production
│           ├── Accounts.js        # ✅ Accounts
│           ├── HRMS.js            # ✅ HRMS
│           ├── Quality.js         # ✅ Quality
│           ├── Settings.js        # ✅ Settings
│           ├── Approvals.js       # ⚠️ Shell (needs UI)
│           └── Reports.js         # ⚠️ Shell (needs UI)
└── memory/
    └── PRD.md
```

---

## Login Credentials
- **Email:** admin@instabiz.com
- **Password:** adminpassword

---

## Next Steps (Frontend UI)
1. Build UI for Director Command Center
2. Build UI for Payroll module
3. Build UI for Import Bridge / Landing Cost
4. Build UI for Gatepass system
5. Build UI for Employee Document Vault
6. Build UI for Sales Incentives
7. Enhance Inventory UI with dual-UOM view

---

## Recent Updates (January 2026)

### "Powerhouse ERP" Enhancement - New Modules Added

#### Module 11: GST Compliance ✅ NEW
**File:** `/app/backend/routes/gst_compliance.py`

**Features:**
- GSTR-1 (Outward Supplies) Report Generation with B2B, B2C, CDNR tables
- GSTR-3B Summary Report with tax calculation
- E-Invoice Generation (IRN + QR Code)
- E-Way Bill Generation with validity tracking
- Input Tax Credit (ITC) Tracking & Reconciliation
- HSN Summary Reports

**Endpoints:**
- `GET /api/gst/gstr1/{period}` - Generate GSTR-1 (period format: MMYYYY)
- `GET /api/gst/gstr3b/{period}` - Generate GSTR-3B
- `GET /api/gst/itc/{period}` - ITC summary
- `POST /api/gst/e-invoice/generate/{invoice_id}` - Generate E-Invoice
- `POST /api/gst/eway-bill/generate/{invoice_id}` - Generate E-Way Bill
- `GET /api/gst/hsn-summary/{period}` - HSN summary

---

#### Module 12: Advanced Inventory ✅ NEW
**File:** `/app/backend/routes/inventory_advanced.py`

**Features:**
- Batch Tracking (lot number, manufacturing date, expiry date)
- Serial Number Assignment
- Bin Location Management (warehouse zones)
- Stock Aging Analysis
- Auto Reorder System with PO generation
- Barcode Lookup
- Multi-method Stock Valuation (FIFO, LIFO, Weighted Avg)

**Endpoints:**
- `POST /api/inventory-advanced/batches` - Create batch
- `GET /api/inventory-advanced/batches/expiring` - Expiring batches
- `POST /api/inventory-advanced/serial-numbers` - Generate serial numbers
- `POST /api/inventory-advanced/bin-locations` - Create bin location
- `GET /api/inventory-advanced/stock-aging` - Stock aging report
- `GET /api/inventory-advanced/reorder-alerts` - Low stock alerts
- `GET /api/inventory-advanced/stock-valuation` - Stock valuation

---

#### Module 13: Reports & Analytics ✅ NEW
**File:** `/app/backend/routes/reports_analytics.py`

**Features:**
- Sales Analytics (Daily, Weekly, Monthly, YoY comparison)
- Purchase Analytics with top suppliers
- Inventory Reports (summary, movement)
- Financial Reports (P&L, Cash Flow)
- Top Products & Customers reports
- Dashboard KPIs

**Endpoints:**
- `GET /api/analytics/dashboard/kpis` - All KPIs
- `GET /api/analytics/sales/summary?period={period}` - Sales summary with growth
- `GET /api/analytics/sales/trend` - Sales trend
- `GET /api/analytics/sales/top-products` - Top selling products
- `GET /api/analytics/sales/top-customers` - Top customers
- `GET /api/analytics/purchases/summary` - Purchase summary
- `GET /api/analytics/inventory/summary` - Inventory summary
- `GET /api/analytics/financial/profit-loss` - P&L report
- `GET /api/analytics/financial/cash-flow` - Cash flow report

---

#### Module 14: Enhanced HRMS ✅ NEW
**File:** `/app/backend/routes/hrms_enhanced.py`

**Features:**
- Attendance Tracking (Check-in/Check-out with working hours calculation)
- Leave Management (6 default types: CL, SL, EL, LOP, ML, PL)
- Leave Balance Tracking
- Statutory Compliance (PF/ESI/PT/LWF calculation)
- Loan & Advance Management with EMI schedules
- Holiday Calendar

**Endpoints:**
- `POST /api/hrms-enhanced/attendance` - Mark attendance
- `POST /api/hrms-enhanced/attendance/check-in` - Self check-in
- `GET /api/hrms-enhanced/attendance/summary/{emp_id}/{month}` - Monthly summary
- `GET /api/hrms-enhanced/leave-types` - List leave types
- `POST /api/hrms-enhanced/leave-applications` - Apply leave
- `PUT /api/hrms-enhanced/leave-applications/{id}/approve` - Approve leave
- `GET /api/hrms-enhanced/leave-balance/{employee_id}` - Leave balance
- `GET /api/hrms-enhanced/statutory/config` - Statutory config
- `GET /api/hrms-enhanced/statutory/calculate/{emp_id}` - Calculate deductions
- `POST /api/hrms-enhanced/loans` - Create loan/advance
- `PUT /api/hrms-enhanced/loans/{id}/pay-emi` - Pay EMI
- `GET /api/hrms-enhanced/holidays/{year}` - Holiday calendar

---

#### Module 15: Notifications & Alerts ✅ NEW
**File:** `/app/backend/routes/notifications.py`

**Features:**
- Payment Due Reminders (3-day and overdue alerts)
- Low Stock Alerts (critical & warning levels)
- Pending Approval Notifications
- Expiring Batch Alerts
- Activity Logging

**Endpoints:**
- `GET /api/notifications/notifications` - List notifications
- `GET /api/notifications/notifications/count` - Unread count
- `PUT /api/notifications/notifications/{id}/read` - Mark as read
- `PUT /api/notifications/notifications/read-all` - Mark all read
- `POST /api/notifications/alerts/generate` - Auto-generate system alerts
- `GET /api/notifications/reminders/payment-due` - Payment reminders
- `POST /api/notifications/activity-log` - Log activity
- `GET /api/notifications/activity-log` - Activity history

---

### Frontend Dashboards Added

1. **GST Compliance Dashboard** (`/gst-compliance`)
   - GSTR-1/3B tabs with detailed breakdowns
   - ITC reconciliation view
   - E-Invoice and E-Way Bill management

2. **Reports & Analytics Dashboard** (`/analytics`)
   - KPI cards (Today's sales, Month sales, Pending POs, Alerts)
   - Sales performance with growth comparison
   - Top products & customers
   - P&L summary
   - Inventory overview

3. **HRMS Dashboard** (`/hrms-dashboard`)
   - Attendance management with quick check-in/out
   - Leave management with approval workflow
   - Loans & advances tracking
   - Statutory compliance overview

4. **Advanced Inventory Dashboard** (`/advanced-inventory`) ✅ NEW
   - Batch tracking with expiry management
   - Serial number generation
   - Bin location management (Aisle/Rack/Shelf)
   - Stock aging analysis (0-30, 31-60, 61-90, 91-180, 180+ days)
   - Stock valuation (Weighted Average method)
   - Reorder alerts with auto PO suggestion
   - Barcode/Item code lookup

5. **Notification Center** ✅ NEW
   - Real-time notification bell in header with unread badge
   - Dropdown notification list with priority badges
   - Mark as read/Mark all read functionality
   - Auto-generate system alerts button
   - Polls for new notifications every 30 seconds

---

### Auto-Populate Feature ✅ IMPLEMENTED

**Reusable Components:**
- `ItemSearchSelect.js` - Debounced search for items with auto-fill
- `CustomerSearchSelect.js` - Debounced search for customers with auto-fill

**Integrated in:**
- CRM (Quotations) - Customer & Item auto-populate
- Procurement (Purchase Orders) - Item auto-populate
- Production (Work Orders) - Item auto-populate with spec fields ✅ NEW
- Accounts (Invoices) - Customer & Item auto-populate

---

### Bug Fix: ObjectId Serialization ✅ RESOLVED

**Issue:** MongoDB `_id` field causing serialization errors in API responses
**Solution:** Added `{"_id": 0}` projection to all `find()` and `find_one()` queries, and filtered `_id` from POST response documents

**Tests:** 36/36 backend tests passed (100% success rate)

### Bug Fix: Dashboard KeyError ✅ RESOLVED (January 2026)

**Issue:** Direct dict access causing KeyError in dashboard.py
**Solution:** Changed `inv['field']` to `inv.get('field', 0)` with defaults

---

## Next Steps (Priority Order)

### P0 - Critical
1. ~~Fix ObjectId serialization bug~~ ✅ DONE
2. ~~Build Frontend for Advanced Inventory~~ ✅ DONE
3. ~~Build Notifications UI~~ ✅ DONE

### P1 - High Priority
1. ~~Extend auto-populate to Production~~ ✅ DONE
2. ~~Implement Meta-Data Driven UI ("Power Settings")~~ ✅ DONE
3. ~~Implement Document Editor for Orders/Invoices~~ ✅ DONE

### P2 - Medium Priority (NEXT)
1. External API Integrations:
   - Live GST / E-invoice / E-waybill APIs
   - B2B Portals (IndiaMart, Alibaba)
   - Payment gateways
   - WhatsApp/Email notifications
2. ~~AI-Powered BI Dashboard (LLM integration)~~ ✅ DONE

### P3 - Refactoring
1. Break down `CRM.js` into smaller components
2. Move Pydantic models to `/app/backend/models/` directory
3. File cleanup and directory restructuring

---

## New Features Added (January 2026 - Session 2)

### Module 16: Power Settings (Custom Field Registry) ✅ NEW
**Files:** `/app/backend/routes/custom_fields.py`, `/app/frontend/src/pages/PowerSettings.js`

**Features:**
- 12 module configurations (CRM, Inventory, Production, Accounts, HRMS, Procurement)
- Dynamic custom field creation (text, number, date, select, multiselect, checkbox, textarea, file)
- Field properties: required, searchable, filterable, show in list
- Section grouping for fields
- Seed default fields for common use cases
- Drag-and-drop field reordering (visual)

**Endpoints:**
- `GET /api/custom-fields/modules` - List 12 available modules
- `GET /api/custom-fields/fields/{module}` - Get fields for a module
- `POST /api/custom-fields/fields` - Create custom field
- `PUT /api/custom-fields/fields/{id}` - Update field
- `DELETE /api/custom-fields/fields/{id}` - Delete field
- `POST /api/custom-fields/seed-defaults` - Seed default fields

---

### Module 17: Document Editor ✅ NEW
**Files:** `/app/backend/routes/documents.py`, `/app/frontend/src/pages/DocumentEditor.js`

**Features:**
- 5 document templates: Sales Invoice, Quotation, Purchase Order, Delivery Challan, Work Order
- Visual canvas editor with drag-and-drop elements
- Element types: Text, Data Field, Image/Logo, Table, Line, Rectangle
- Data field binding (company, customer, document, items, totals, bank details)
- Properties panel for element customization
- Zoom, grid, preview, export PDF controls
- Template save/load functionality

**Endpoints:**
- `GET /api/documents/templates` - List saved templates
- `POST /api/documents/templates` - Save template
- `GET /api/documents/templates/{type}` - Get template by type

---

## Test Files
- `/app/tests/test_new_modules.py` - 36 tests for powerhouse modules
- `/app/tests/test_dashboard_notifications.py` - 7 tests for dashboard & notifications
- `/app/tests/test_new_features_iteration4.py` - 26 tests for Power Settings & Document Editor
- `/app/tests/test_ai_bi_dashboard.py` - 24 tests for AI BI Dashboard
- `/app/test_reports/iteration_6.json` - Latest test report (100% pass)

---

## Module 18: AI Business Intelligence Dashboard ✅ NEW (January 2026)
**Files:** `/app/backend/routes/ai_bi.py`, `/app/frontend/src/pages/AIBIDashboard.js`
**AI Provider:** Gemini 3 Flash via Emergent LLM Key

### Features:

**1. Natural Language Queries**
- Ask questions about business data in plain English
- Example: "What were our top 5 products this month?"
- Suggested queries for quick access
- Query history tracking
- API: `POST /api/ai/nl-query`

**2. AI-Generated Insights**
- Auto-analyze sales, inventory, production, finance
- Structure: Key Findings → Opportunities → Risks → Recommended Actions
- Focus areas: All, Sales, Inventory, Production, Finance
- Time periods: Week, Month, Quarter, Year
- API: `POST /api/ai/generate-insights`

**3. Predictive Analytics**
- Forecast sales, inventory needs, cash flow
- Configurable horizon: 7 to 90 days
- Includes confidence levels and scenarios
- Historical data visualization
- API: `POST /api/ai/predict`

**4. Smart Alerts**
- AI detects anomalies and unusual patterns
- Alert types: CRITICAL, WARNING, INFO
- Categories: Sales, Inventory, Production, Finance, Customer
- Shows summary stats: overdue invoices, low stock, scrap rate
- API: `POST /api/ai/smart-alerts`

### Frontend Route: `/ai-dashboard`
- Beautiful purple/indigo gradient theme
- 4 tabs: Ask AI, Insights, Predict, Smart Alerts
- Suggested queries, recent queries panel
- Real-time AI responses

---

## Build System Migration: CRA → Vite ✅ COMPLETE (January 2026)

### Migration Details
- **Old Stack:** Create React App (CRA) + CRACO
- **New Stack:** Vite 7.3.1 + @vitejs/plugin-react-swc

### Changes Made:
1. **Installed:** `vite`, `@vitejs/plugin-react-swc`
2. **Removed:** `react-scripts`, `@craco/craco`, `@babel/plugin-proposal-private-property-in-object`, `cra-template`
3. **Created:** `/app/frontend/vite.config.js` - Full Vite configuration with:
   - Visual edits plugin for Emergent integration
   - Path alias (`@` → `src/`)
   - JSX loader configuration for `.js` files
   - Allowed hosts configuration for preview domain
4. **Moved:** `index.html` from `/public/` to root
5. **Renamed:** All `.js` files in `src/` to `.jsx` (85 files)
6. **Updated:** Environment variables from `REACT_APP_*` to `VITE_*`
7. **Updated:** `package.json` scripts: `start`, `build`, `preview`

### Environment Variables:
- **Old:** `process.env.REACT_APP_BACKEND_URL`
- **New:** `import.meta.env.VITE_BACKEND_URL`

### Test Results:
- All 8 key pages tested and working (100% success rate)
- Login, Dashboard, CRM, Director Center, AI BI, Inventory, Production, Navigation
- Test report: `/app/test_reports/iteration_7.json`

### Benefits:
- Faster hot reload (native ESM)
- Modern build system
- Better dependency management
- No more CRA/CRACO conflicts

---

## File Structure

```
/app/
├── backend/
│   ├── .env
│   ├── requirements.txt
│   ├── server.py
│   └── routes/
│       ├── core_engine.py     # 6 Pillars implementation
│       ├── ai_bi.py           # AI Business Intelligence
│       ├── custom_fields.py   # Power Settings
│       ├── documents.py       # Document Editor
│       ├── gst_compliance.py
│       ├── inventory_advanced.py
│       ├── reports_analytics.py
│       ├── hrms_enhanced.py
│       └── notifications.py
└── frontend/
    ├── index.html             # Vite entry HTML
    ├── vite.config.js         # Vite configuration
    ├── package.json
    └── src/
        ├── index.jsx          # Entry point
        ├── App.jsx            # Routes
        ├── components/
        │   ├── ui/            # Shadcn components
        │   ├── layout/
        │   │   └── MainLayout.jsx
        │   └── NotificationCenter.jsx
        └── pages/
            ├── Dashboard.jsx
            ├── DirectorDashboard.jsx
            ├── AIBIDashboard.jsx
            ├── PowerSettings.jsx
            ├── DocumentEditor.jsx
            ├── AdvancedInventory.jsx
            └── ... (other pages)
```

---

## Test Credentials
- **Email:** `admin@instabiz.com`
- **Password:** `adminpassword`

---

## Next Steps (Priority Order)

### P1 - High Priority
1. **Dynamic Form Rendering:** Make forms render dynamically from Power Settings metadata
2. **Canvas Document Editor:** Implement core canvas editing functionality
3. **External API Integrations:** GST/E-invoicing, B2B portals, payment gateways

### P2 - Medium Priority
1. WhatsApp/Email notification integration
2. Advanced reporting with PDF exports
3. Mobile-responsive improvements

### P3 - Refactoring
1. Break down `CRM.jsx` into smaller components
2. Move Pydantic models to `/app/backend/models/`
3. Sidebar enhancements (search, favorites)

---

## Session Update - January 2026 (Continued)

### P1/P2 Features Completed ✅

#### 1. Dynamic Form Rendering ✅
- **Created:** `useCustomFields` hook (`/app/frontend/src/hooks/useCustomFields.jsx`)
  - Fetches custom fields for any module from Power Settings
  - Groups fields by section
  - Provides initial values generator
  
- **Created:** `DynamicFormFields` component (`/app/frontend/src/components/DynamicFormFields.jsx`)
  - Renders 8+ field types dynamically: text, number, textarea, select, multiselect, checkbox, date, file
  - Supports section grouping with headers
  - Configurable column layout (1, 2, or 3 columns)
  - Help text popovers for fields
  
- **Integrated into:**
  - CRM Leads (`/app/frontend/src/pages/LeadsPage.jsx`) - Shows Business Info section with Industry, Revenue, Employees
  - Inventory Items (`/app/frontend/src/pages/Inventory.jsx`) - Custom Fields tab in item form
  - HRMS Employees (`/app/frontend/src/pages/HRMS.jsx`) - Custom Fields tab in employee form

#### 2. Document Editor (Canvas-Based) ✅
- **Location:** `/app/frontend/src/pages/DocumentEditor.jsx`
- **Templates:** Sales Invoice, Quotation, Purchase Order, Delivery Challan, Work Order
- **Element Types:** Text, Data Field, Image/Logo, Table, Line, Rectangle
- **Features:**
  - Drag-and-drop element positioning
  - Properties panel for editing (position, size, font, alignment)
  - Data field placeholders (company info, customer info, items, totals, bank)
  - Grid display for alignment
  - Zoom controls (50-150%)
  - Save, Preview, Export PDF buttons

#### 3. PDF & Excel Export ✅
- **Backend Endpoints:** (`/app/backend/routes/reports_analytics.py`)
  - `GET /api/analytics/export/pdf/{report_type}` - Generates styled PDF reports
  - `GET /api/analytics/export/excel/{report_type}` - Generates Excel workbooks
  - Report types: sales, inventory, customers
  - Supports period filter (today, week, month, quarter, year)
  
- **Frontend Integration:** (`/app/frontend/src/pages/ReportsDashboard.jsx`)
  - Export dropdown with PDF and Excel options
  - Separate sections for Sales, Inventory, and Customer reports
  - Downloads with timestamped filenames

- **Libraries Used:**
  - `reportlab` - PDF generation with tables, styling, colors
  - `xlsxwriter` - Excel workbook generation with formatting

### Test Results
- **Test Report:** `/app/test_reports/iteration_8.json`
- **Backend Tests:** 17/17 passed (100%)
- **Frontend Tests:** All UI features verified (100%)
- **Test File:** `/app/backend/tests/test_p1_p2_features.py`

### Architecture Updates
```
/app/frontend/src/
├── hooks/
│   └── useCustomFields.jsx     # NEW - Custom fields hook
├── components/
│   └── DynamicFormFields.jsx   # NEW - Dynamic form renderer
└── pages/
    ├── LeadsPage.jsx           # UPDATED - Dynamic fields
    ├── Inventory.jsx           # UPDATED - Dynamic fields tab
    ├── HRMS.jsx                # UPDATED - Dynamic fields tab
    └── ReportsDashboard.jsx    # UPDATED - Export dropdown
```

---

## Session Update - January 2026 (Major Feature Addition)

### New Features Implemented ✅

#### 1. Inter-User Chat System ✅
- **Backend:** `/app/backend/routes/chat.py`
- **Frontend:** `/app/frontend/src/pages/Chat.jsx`
- **Features:**
  - Direct Messages (1-on-1 chats)
  - Group Chats (create groups, add/remove members, admins)
  - Task Assignment from chat (create, assign, track status)
  - File/image attachments
  - Message reactions
  - Polling-based updates (5 second intervals)
  - Read receipts
- **API Endpoints:**
  - `GET /api/chat/conversations` - List all conversations
  - `GET /api/chat/messages/dm/{user_id}` - Get DM messages
  - `POST /api/chat/messages/dm/{user_id}` - Send DM
  - `POST /api/chat/groups` - Create group
  - `GET /api/chat/messages/group/{group_id}` - Get group messages
  - `GET/POST /api/chat/tasks` - Task management
  - `POST /api/chat/upload` - File uploads

#### 2. Drive System (Google Drive-style) ✅
- **Backend:** `/app/backend/routes/drive.py`
- **Frontend:** `/app/frontend/src/pages/Drive.jsx`
- **Features:**
  - File upload (docs, sheets, PDFs, images, videos)
  - Folder organization with nesting
  - File sharing with permission levels (view/edit)
  - Favorites, Recent files, Shared with me views
  - File preview (images, PDFs)
  - Storage quota tracking (5GB limit)
  - Grid/List view toggle
- **Storage:** `/app/uploads/drive/`
- **API Endpoints:**
  - `POST /api/drive/upload` - Upload files
  - `GET/POST /api/drive/folders` - Folder management
  - `GET /api/drive/files` - File listing with filters
  - `GET /api/drive/files/{id}/download` - Download file
  - `POST /api/drive/files/{id}/share` - Share file
  - `GET /api/drive/storage` - Storage stats

#### 3. Bulk Import System ✅
- **Backend:** `/app/backend/routes/bulk_import.py`
- **Frontend:** `/app/frontend/src/pages/BulkImport.jsx`
- **Import Types:**
  - Customers/Vendors (with GSTIN, contact, address)
  - Items/Products (with HSN, specs, pricing)
  - Opening Balance (debit/credit balances)
  - Opening Stock (item quantities by warehouse)
- **Features:**
  - Excel template downloads (.xlsx)
  - Upload with validation
  - Error reporting (missing fields, duplicates, not found)
  - Import guidelines and tips
- **API Endpoints:**
  - `GET /api/bulk-import/templates/{type}` - Download template
  - `POST /api/bulk-import/customers` - Import customers
  - `POST /api/bulk-import/items` - Import items
  - `POST /api/bulk-import/opening-balance` - Import balances
  - `POST /api/bulk-import/opening-stock` - Import stock

#### 4. GST E-Invoice & E-Way Bill ✅ (MOCKED)
- **Backend:** `/app/backend/routes/einvoice.py`
- **Frontend:** `/app/frontend/src/pages/EInvoice.jsx`
- **Features:**
  - IRN Generation (Mock mode - generates fake IRN)
  - QR Code generation for invoices
  - Bulk IRN generation
  - IRN cancellation (within 24 hours)
  - E-Way Bill generation for invoices > ₹50,000
  - API credentials management (NIC integration ready)
  - Activity logs tracking
- **Note:** Currently in **MOCK MODE**. Real NIC API credentials can be configured for production.
- **API Endpoints:**
  - `POST /api/einvoice/generate-irn` - Generate IRN
  - `POST /api/einvoice/generate-irn/bulk` - Bulk IRN
  - `POST /api/einvoice/cancel-irn` - Cancel IRN
  - `POST /api/einvoice/generate-eway-bill` - Generate E-Way Bill
  - `GET /api/einvoice/summary` - Summary stats
  - `GET /api/einvoice/pending-invoices` - Pending list

### Test Results
- **Test Report:** `/app/test_reports/iteration_9.json`
- **Backend Tests:** 21/21 passed (100%)
- **Frontend Tests:** All UI verified (100%)

### Navigation Updates
Added to sidebar: Chat, Drive, Bulk Import, E-Invoice

### Dependencies Added
- `pandas` - Excel file processing
- `openpyxl` - Excel template generation
- `qrcode[pil]` - QR code generation for E-Invoice


---

## Session Update - January 2026 (P0 Bug Fix & Refactoring)

### P0 Fix: Customization Tab ✅ FIXED
**File:** `/app/frontend/src/pages/Customization.jsx`

**Issue:** User reported "THE CUSTOMIZATION TAB IS ALSO NOT WORKING PROPERLY, MANY FUNCTIONS ARE EMPTY"

**Root Cause:** 
- Report Builder tab only showed static description text with non-functional "Create Report" button
- Missing tabs for Email Templates, Notifications
- Quick action cards were not clickable to switch tabs

**Fixes Implemented:**
1. **Report Builder Tab (NEW)**
   - Full CRUD functionality for report templates
   - Dynamic column selection based on module
   - Execute reports and view results in dialog
   - Module options: CRM, Inventory, Production, Accounts, HRMS, Quality
   - Chart type selection (bar, line, pie)

2. **Email Templates Tab (NEW)**
   - Pre-populated with 4 default templates: Welcome Email, Invoice, Payment Reminder, Order Confirmation
   - Create/Edit email templates with variable placeholders
   - Template activation/deactivation

3. **Notification Rules Tab (NEW)**
   - Pre-populated with 4 default rules: Low Stock Alert, Payment Overdue, Lead Assigned, WO Completed
   - Configure trigger events and notification channels (In-App, Email, SMS, WhatsApp)
   - Rule enable/disable toggle

4. **API Documentation Tab (ENHANCED)**
   - Added "Open Swagger UI" button linking to /docs
   - Added "Copy Base URL" button with clipboard functionality

5. **Import/Export Tab (NEW)**
   - Navigation links to Bulk Import and Reports pages
   - Supported import formats documentation

6. **Quick Cards (FIXED)**
   - All 6 cards now clickable and switch to corresponding tab
   - Visual highlight on selected card

**Bug Fixed by Testing Agent:**
- Create Report dialog crashed due to empty string value in SelectItem
- Fixed: Changed `<SelectItem value="">` to `<SelectItem value="none">`

### Test Results
- **Test Report:** `/app/test_reports/iteration_10.json`
- **Frontend Tests:** 100% pass rate
- **All 6 tabs verified functional:**
  - Custom Fields ✅
  - Report Builder ✅
  - Email Templates ✅
  - Notifications ✅
  - API Docs ✅
  - Import/Export ✅

### P2 Tasks Status
- **Backend Pydantic Models:** `/app/backend/models/schemas.py` created with comprehensive models
- **CRM.jsx Refactoring:** Deferred - file is 2235 lines but currently stable. Created `/app/frontend/src/components/crm/CRMOverview.jsx` as starting point

### Next Steps
1. Continue CRM.jsx component extraction (AccountsList, QuotationsList, SamplesList)
2. Update route files to import from centralized schemas.py
3. Add sidebar search/filter and favorites feature
4. Implement real-time WebSocket for Chat system

---

## Session Update - January 2026 (Grand Blueprint Implementation)

### New Features Implemented

#### 1. Dashboard Quick Actions Widget ✅
**File:** `/app/frontend/src/pages/Dashboard.jsx`

**Features:**
- **6 Quick Links:** Add Lead, Create Quotation, New Invoice, Run Report, Custom Fields, AI Dashboard
- **Action Items:** Shows count of items needing attention (overdue invoices, pending approvals, low stock, stalled WOs)
- **System Health Card:** Shows uptime status and link to Director Command Center
- **Smart Prioritization:** High-priority items highlighted in red/orange

#### 2. Autonomous Collector Module ✅ (The Revenue Hunter)
**Backend:** `/app/backend/routes/autonomous_collector.py`
**Frontend:** `/app/frontend/src/pages/AutonomousCollector.jsx`

**Features based on Grand Blueprint:**

**A. Debtor Segmentation**
- GOLD: Pays within terms, score 80-100
- SILVER: Occasional delays, score 50-79
- BRONZE: Frequent delays, score 20-49
- BLOCKED: Auto-blocked for non-payment, score 0-19
- Payment score calculation based on: credit days, overdue invoices, credit limit usage

**B. Emergency Controls ("The Nuke Button")**
- HALT_PRODUCTION: Stop all production
- FREEZE_ORDERS: Block new orders
- BLOCK_SHIPPING: Halt all shipments
- LOCKDOWN: Full business lockdown
- Configurable scope (All branches / Specific branch)
- Duration-based controls
- Director-only access

**C. Smart Payment Reminders**
- Auto-generated reminders for:
  - GENTLE_REMINDER: Invoices due within 3 days
  - OVERDUE_NOTICE: Invoices past due
  - URGENT_REMINDER: Invoices 30+ days overdue
- Pre-drafted WhatsApp/Email messages with customer details
- Priority classification (HIGH/MEDIUM)

**D. Collection Analytics**
- Total invoiced vs collected
- Collection efficiency percentage
- Average collection days
- Daily collection trend
- Period filters (week/month/quarter/year)

**E. Block/Unblock Debtors**
- Manual account blocking with reason
- Auto-block rules (3+ overdue invoices, ₹50K+ outstanding)
- Audit trail for all block/unblock actions

### Test Results
- **Test Report:** `/app/test_reports/iteration_11.json`
- **Backend Tests:** 100% (8/8 tests passed)
- **Frontend Tests:** 100% - All features verified

### API Endpoints Added
```
GET  /api/collector/debtors/segmentation
POST /api/collector/debtors/{id}/block
POST /api/collector/debtors/{id}/unblock
GET  /api/collector/reminders/pending
POST /api/collector/emergency/activate
POST /api/collector/emergency/deactivate/{id}
GET  /api/collector/emergency/status
GET  /api/collector/analytics/collection
GET  /api/collector/quick-actions
```

### Navigation Updates
- Added "Collector" link with Zap icon in sidebar (under Accounts)
- Route `/collector` mapped to AutonomousCollector page

---

## Session Update - January 2026 (Priority Tasks Batch)

### P2: Sidebar Search & Favorites ✅ COMPLETE
**File:** `/app/frontend/src/components/layout/MainLayout.jsx`

**Features:**
- **Search Bar:** Real-time filter for navigation items
- **Favorites:** Star/unstar menu items, stored in localStorage
- **Favorites Section:** Appears at top of sidebar when items are starred
- **Parent Group Display:** Shows parent group when searching nested items

### P3: Buying DNA Sales Hunter ✅ COMPLETE
**Backend:** `/app/backend/routes/buying_dna.py`
**Frontend:** `/app/frontend/src/pages/BuyingDNA.jsx`

**Features (From Grand Blueprint):**
- **Purchase Rhythm Analysis:** Calculates average order interval per customer
- **Urgency Scoring:** 
  - URGENT_FOLLOWUP: Overdue > 50% of avg interval
  - GENTLE_REMINDER: Any overdue
  - PRE_EMPTIVE_CHECK: 80%+ of avg interval passed
  - NO_ACTION: On track
- **WhatsApp Draft Messages:** Pre-written messages with customer name, days overdue
- **Follow-up Logging:** Track whatsapp_sent, call_made, email_sent actions
- **Summary Dashboard:** 4 cards showing counts per urgency level

**API Endpoints:**
```
GET  /api/buying-dna/patterns - All customer buying patterns
GET  /api/buying-dna/patterns/{account_id} - Single account pattern
GET  /api/buying-dna/dashboard - Dashboard summary
POST /api/buying-dna/followup-log - Log follow-up action
```

### P3: Real-time Chat ✅ COMPLETE
**Backend:** `/app/backend/routes/realtime_chat.py`
**Frontend:** Uses existing `/app/frontend/src/pages/Chat.jsx`

**Features:**
- **WebSocket Support:** Real-time messaging via `/api/realtime-chat/ws/{user_id}`
- **REST Fallback:** Full REST API for non-WebSocket clients
- **Room Types:** direct, group, channel
- **Typing Indicators:** Broadcast to room members
- **Read Receipts:** Track which users have read messages
- **Online Status:** Track and broadcast user online/offline status

**API Endpoints:**
```
WS   /api/realtime-chat/ws/{user_id} - WebSocket connection
GET  /api/realtime-chat/rooms - List user's chat rooms
POST /api/realtime-chat/rooms - Create new room
GET  /api/realtime-chat/rooms/{room_id}/messages - Get messages
POST /api/realtime-chat/rooms/{room_id}/messages - Send message (REST)
GET  /api/realtime-chat/online-users - List online users
```

### Test Results (Iteration 12)
- **Test Report:** `/app/test_reports/iteration_12.json`
- **Backend Tests:** 100% (9/9 tests passed)
- **Frontend Tests:** 100% - All features verified

### Navigation Updates
- Added "Buying DNA" link with DNA icon in sidebar
- Route `/buying-dna` mapped to BuyingDNA page

---

## Session Update - January 2026 (Customer Health Score)

### Customer Health Score Feature ✅ COMPLETE
**Backend:** `/app/backend/routes/customer_health.py`
**Frontend Page:** `/app/frontend/src/pages/CustomerHealth.jsx`
**Widget:** `/app/frontend/src/components/CustomerHealthWidget.jsx`

**Combined Analysis (From Grand Blueprint):**
- **Buying DNA Weight:** 40% (purchase rhythm analysis)
- **Debtor Segmentation Weight:** 60% (payment behavior)
- **Formula:** `health_score = buying_score * 0.4 + payment_score * 0.6`

**Health Status Levels:**
- CRITICAL: Score 0-39 (🔴)
- AT_RISK: Score 40-59 (🟠)
- HEALTHY: Score 60-79 (🟢)
- EXCELLENT: Score 80-100 (⭐)

**Features:**
- Unified customer health view combining buying + payment metrics
- Auto-generated risk factors based on analysis
- Auto-generated recommended actions
- Priority ranking (worst health first)
- WhatsApp/Phone quick actions
- Filter by status (CRITICAL, AT_RISK, HEALTHY, EXCELLENT)
- Search by customer name
- At-risk outstanding amount alert

**API Endpoints:**
```
GET /api/customer-health/scores - Full health scores list
GET /api/customer-health/scores/{id} - Single customer health
GET /api/customer-health/widget - Dashboard widget data
```

**UI Integration:**
- Widget added to CRM Overview page (`/crm`)
- Full page at `/customer-health`
- Navigation sidebar: "Customer Health" with Heart icon

### Test Results (Iteration 13)
- **Test Report:** `/app/test_reports/iteration_13.json`
- **Backend Tests:** 100% (7/7 tests passed)
- **Frontend Tests:** 100% - All features verified

---

## Session Update - January 2026 (PDF Generation)

### PDF Preview & Download Feature ✅ COMPLETE
**Backend:** `/app/backend/routes/pdf_generator.py`
**Frontend Updated:** `Accounts.jsx`, `CRM.jsx`

**Professional PDF Generation using ReportLab:**
- Company header with logo area, address, GSTIN
- Document title (TAX INVOICE, QUOTATION, etc.)
- Customer/Bill To section with GSTIN
- Line items table with HSN, Qty, Rate, Discount, Tax, Amount
- Totals section with subtotal, discount, GST breakdown (CGST/SGST)
- Bank details for payment
- Authorized Signatory footer

**API Endpoints:**
```
GET /api/pdf/invoice/{id}/pdf - Download Invoice PDF
GET /api/pdf/invoice/{id}/preview - Preview Invoice PDF (inline)
GET /api/pdf/quotation/{id}/pdf - Download Quotation PDF  
GET /api/pdf/quotation/{id}/preview - Preview Quotation PDF (inline)
GET /api/pdf/invoices/bulk-pdf?invoice_ids=id1,id2 - Bulk download
```

**Frontend Buttons Added:**
- **Accounts Invoice Table:** Eye (Preview), FileDown (Download), Printer (Print)
- **CRM Quotations Table:** Eye (Preview), FileDown (Download)

### Test Results (Iteration 14)
- **Test Report:** `/app/test_reports/iteration_14.json`
- **Backend Tests:** 100% (8/8 tests passed)
- **Frontend Tests:** 100% - All buttons verified

---

## Session Update - January 2026 (Comprehensive PDF & Communication)

### PDF Generation for ALL Modules ✅ COMPLETE
**Backend:** `/app/backend/routes/pdf_all_modules.py`

**Document Types with Styled PDFs:**
| Document | Theme Color | Title |
|----------|-------------|-------|
| Invoice | Blue (#1e3a5f) | TAX INVOICE |
| Quotation | Purple (#7c3aed) | QUOTATION |
| Work Order | Purple (#7c3aed) | WORK ORDER |
| Delivery Challan | Green (#059669) | DELIVERY CHALLAN |
| Purchase Order | Red (#dc2626) | PURCHASE ORDER |
| Sample | Amber (#f59e0b) | SAMPLE DISPATCH NOTE |
| Payment | Green (#10b981) | PAYMENT RECEIPT |

**API Endpoints for each type:**
```
GET /api/pdf/{type}/{id}/pdf - Download PDF
GET /api/pdf/{type}/{id}/preview - Preview PDF (inline)
```

**PDF Features:**
- Company header with GSTIN, address, contact
- Customer/vendor info section
- Line items table with appropriate columns
- Totals with tax breakdown
- Bank details (for invoices)
- Authorized signatory footer
- Amount in words (for payments)

### Email & WhatsApp Communication ✅ COMPLETE
**Backend:** `/app/backend/routes/document_communication.py`
**Frontend:** `/app/frontend/src/components/DocumentActions.jsx`

**Email Features:**
- Send any document type with PDF attachment
- Pre-composed subject and body based on document type
- Custom message support
- CC recipients
- Communication logging

**WhatsApp Features:**
- Generate WhatsApp message with PDF link
- Pre-composed message templates with emojis
- Opens WhatsApp web/app with pre-filled message
- Copy message to clipboard option
- Communication logging

**API Endpoints:**
```
POST /api/communicate/email/send - Send email with PDF
POST /api/communicate/email/preview - Preview email content
POST /api/communicate/whatsapp/send - Generate WhatsApp message
POST /api/communicate/whatsapp/preview - Preview WhatsApp message
GET  /api/communicate/history - Communication history
GET  /api/communicate/history/{type}/{id} - Document-specific history
POST /api/communicate/quick-send/invoice/{id} - Quick send invoice
POST /api/communicate/quick-send/quotation/{id} - Quick send quotation
```

**Frontend Integration:**
- Universal `DocumentActions` component with dropdown menu
- Buttons: Preview, Download, Print, Email, WhatsApp
- Email dialog with recipient, subject, message fields
- WhatsApp dialog with phone, name, custom message fields
- Integrated in Accounts (Invoices) and CRM (Quotations)

### Test Results (Iteration 15)
- **Test Report:** `/app/test_reports/iteration_15.json`
- **Backend Tests:** 97% (35/36 passed, 1 skipped)
- **Frontend Tests:** 100% - All DocumentActions verified

### Note on Email
⚠️ **MOCKED:** Email sending is logged but not actually sent via SMTP. For production, integrate with SendGrid, SES, or SMTP service.

---

## Session Update - January 2026 (Field Registry - Command Center)

### Field Registry Feature ✅ COMPLETE (NEW)
**Backend:** `/app/backend/routes/field_registry.py`
**Frontend Page:** `/app/frontend/src/pages/FieldRegistry.jsx`
**Hook:** `/app/frontend/src/hooks/useFieldRegistry.jsx`
**Dynamic Form:** `/app/frontend/src/components/DynamicRegistryForm.jsx`

**The "Command Registry" - Metadata-Driven Field Configuration System**

This is the foundation for making ALL fields editable, reorderable, and customizable. Admin users can:
- ✏️ Edit field name/label
- ➕➖ Add or remove fields
- 🔄 Change display order (drag & drop)
- ⭐ Set as compulsory or optional
- 🎨 Change field type (text, number, dropdown, date, multi-select, checkbox, textarea, email, phone, currency, auto)
- 📝 Edit dropdown options

**Implementation Scope:**
1. **CRM - Leads**
   - A. **Kanban Stages** (9 stages): Hot Leads, Cold Leads, Contacted, Qualified, Proposal, Negotiation, Converted, Customer, Lost
   - B. **Form Fields** (20 fields): Company Name, Contact Person, Email, Phone, Source (dropdown), Address, Country, Pincode, State, District, City (auto-fill from pincode), Customer Type (dropdown), Assigned To (dropdown), Stage (dropdown), Industry (dropdown), Products of Interest (multi-select), Estimated Value (dropdown), Next Follow-up Date, Follow-up Activity (dropdown), Notes
   - C. **Field Sections**: Basic Info, Address, Classification, Follow-up

2. **CRM - Customer Accounts**
   - A. **Display Fields** (10): Company Name, City/State, Total Outstanding, Credit Limit/Days, Avg Payment Days, Sales Person, Monthly Avg Turnover, YTD Turnover, GST No, Phone
   - B. **Form Fields** (28): Basic (Company, Industry, GST, PAN, Website, Aadhar, Bank), Address (Billing, Shipping, Same-as-billing), Contacts (Name, Designation, Phone, Email), Credit Terms (Limit, Days, Control)

3. **CRM - Quotations**
   - A. **Display Fields**: Quote No (auto), Company, Date, Amount, Status, Notes, Comments + Convert to Order
   - B. **Form Fields**: Customer info, Line Items (Item Code/Name, Thickness, Width, Length, Color, Qty, Rate, Brand, Instructions, Marking), Subtotal, Tax, Grand Total, T&C

4. **CRM - Samples**
   - A. **Display Fields**: Sample No (auto), Customer, Products, Quantity, Status (dropdown), Feedback (dropdown), Due Date
   - B. **Form Fields**: Customer, Contact Person, Sample Items (Product, Thickness, Color, Width, Length, Qty, Unit), From Location, Courier, Tracking No, Feedback Due Date, Purpose (dropdown), Notes

**Masters Module Architecture (9 Master Lists):**
1. **Customer Master** - The Revenue Base (GSTIN, Branch, Buying DNA Rhythm, Credit Limit, Distance from Sarigam)
2. **Supplier Master** - The Sourcing Base (Material Category: Film/Adhesive/Core, Lead Time, Reliability Score)
3. **Item Master** - The Physics Base (Base Category: BOPP/PVC, UOM: KG/SQM/PCS, Microns, GSM, Adhesive Type)
4. **Item Code Master** - The Inventory Logic (Internal SKU, Barcode/QR, Warehouse Rack Location)
5. **Price Master** - The Margin Protector (Customer-Specific Pricing, Volume Discounts, MSP)
6. **Machine Master** - The Plant Heart (Machine Name, Design Capacity, Power Consumption, Maintenance Cycle)
7. **Employee Master** - The Accountability Base (Role, Biometric ID, Department, Target KPIs)
8. **Expense Master** - The Leakage Tracker (Category, Budget Cap, Branch Allocation)
9. **Report Type List** - The Executive View (Frequency, Recipients, KPI Focus)

**API Endpoints:**
```
GET  /api/field-registry/modules                           - List all modules and entities
GET  /api/field-registry/masters                           - List master types
POST /api/field-registry/config                            - Save field configuration (Admin only)
GET  /api/field-registry/config/{module}/{entity}          - Get field config for entity
GET  /api/field-registry/config/{module}                   - Get all configs for module
DELETE /api/field-registry/config/{module}/{entity}        - Reset to default
POST /api/field-registry/options/{module}/{entity}/{field} - Save dropdown options
GET  /api/field-registry/options/{module}/{entity}/{field} - Get dropdown options
POST /api/field-registry/stages/{module}/{entity}          - Save Kanban stages
GET  /api/field-registry/stages/{module}/{entity}          - Get Kanban stages
PUT  /api/field-registry/config/{module}/{entity}/reorder  - Reorder fields
PUT  /api/field-registry/stages/{module}/{entity}/reorder  - Reorder stages
POST /api/field-registry/masters/{type}                    - Save master config
GET  /api/field-registry/masters/{type}/config             - Get master config
```

**UI Features:**
- Module selector (CRM, Inventory, Accounts, Production, Procurement, HRMS)
- Entity selector (per module)
- 3-tab configuration panel: Kanban Stages, Form Fields, List Display
- Drag & drop reordering with visual drag handles
- Color badges for Kanban stages (10 color options)
- Field editor dialog for adding/editing fields
- Section grouping (Basic Info, Address, Classification, Follow-up, etc.)
- Required badge indicator
- Options count for dropdown fields
- Save Changes button (Admin only)
- Unsaved Changes indicator
- Reload button

**Access Control:**
- Edit/Save: Admin and Director roles only
- View: All authenticated users

### Test Results (Iteration 16)
- **Test Report:** `/app/test_reports/iteration_16.json`
- **Backend Tests:** 100% (21/21 tests passed)
- **Frontend Tests:** 100% - All features verified
- **Test File:** `/app/backend/tests/test_field_registry.py`

---

## Session Update - January 2026 (Warehouse & Stock Management)

### Warehouse & Stock Management Module ✅ COMPLETE
**Backend:** `/app/backend/routes/warehouse_stock.py`

**Key Features Implemented:**

**1. Warehouse Management (GST-wise)**
- Each warehouse has its own GSTIN for separate accounting
- Add Warehouse form fields: Code, Name, Prefix, GSTIN, Pincode, State, City, Address, Bank Details, Email, Contact
- Consolidated + Separate view per warehouse
- Auto-generates document prefixes per warehouse

**2. Serial Number Master**
- Configurable per document type per warehouse
- Fields: Prefix, Suffix, Separator, FY Format (2425, 24-25, 2024-25)
- Number length, Auto-reset on new FY
- Sample format preview

**3. Stock Operations**
- Stock Register (warehouse-wise)
- Stock Transfers between warehouses (Draft → In Transit → Received)
- Stock Adjustments (Opening, Closing, Increase, Decrease, Damage, Expired, Recount)
- Item Ledger showing all movements
- Consolidated stock view across warehouses

**4. Batch & Barcode Management**
- Batch number generator
- QR Code/Barcode generation
- Label generator with item specs
- Rack location tracking

**5. Customer Accounts Updates**
- Added "Opening Balance" field in Basic Info section
- Added "Aadhar No" field
- Added "Bank Details" field

**6. Inventory Items Field Configuration**
- 28 fields across 4 sections:
  - Basic: Item Code, Name, Type, Category, HSN, Primary UOM, Secondary UOM, Conversion Method
  - Specs: Base Material, Adhesive Type, Thickness, Color, Width, Length
  - Pricing: Cost Price, Margin %, Min Selling Price (auto-calculate), MRP
  - Inventory: Reorder Level, Safety Stock, Lead Time, Shelf Life, Label Format, Barcode

**API Endpoints:**
```
# Warehouse
GET/POST /api/warehouse/warehouses
GET/PUT  /api/warehouse/warehouses/{id}

# Serial Numbers
GET/POST /api/warehouse/serial-configs
GET      /api/warehouse/generate-serial/{doc_type}/{warehouse_id}

# Batches & Barcodes
POST     /api/warehouse/batches
GET      /api/warehouse/batches
GET      /api/warehouse/generate-barcode/{data}
GET      /api/warehouse/generate-label/{item_id}

# Stock Transfers
POST     /api/warehouse/stock-transfers
PUT      /api/warehouse/stock-transfers/{id}/dispatch
PUT      /api/warehouse/stock-transfers/{id}/receive
GET      /api/warehouse/stock-transfers

# Stock Adjustments
POST     /api/warehouse/stock-adjustments
PUT      /api/warehouse/stock-adjustments/{id}/approve
GET      /api/warehouse/stock-adjustments

# Reports
GET      /api/warehouse/stock-register
GET      /api/warehouse/item-ledger/{item_id}
GET      /api/warehouse/consolidated-stock
```

---

## Session Update - January 2026 (Dynamic Forms Fix)

### Field Registry Engine - Dynamic Forms Integration ✅ COMPLETE

**Issue:** User reported "The updates are not showing, fields are still the same" - The Field Registry configuration UI was built but the actual forms were not rendering dynamically from the configuration.

**Root Cause:** 
- `DynamicRegistryForm.jsx` component and `useFieldRegistry.jsx` hook were created but NOT connected to the actual form dialogs
- `LeadFormDialog` in `LeadsPage.jsx` still had hardcoded form fields instead of using the dynamic components

**Fix Implemented:**
1. **Updated `LeadFormDialog`** (`/app/frontend/src/pages/LeadsPage.jsx`)
   - Integrated `useFieldRegistry('crm', 'leads')` hook to fetch field configuration
   - Replaced hardcoded form fields with `DynamicFormFields` component
   - Added fallback to basic form if registry not loaded
   - Preserved pincode auto-fill functionality for address fields

2. **Dynamic Form Rendering Features:**
   - Fields grouped by sections (Basic Info, Address, Classification, Follow-up)
   - Required field markers (*) displayed
   - Dropdown options loaded from Field Registry configuration
   - Multiselect fields render with clickable badges
   - "Customize Fields" button opens Field Registry for quick configuration

**Architecture:**
```
User Action                  Flow
─────────────────────────────────────────────────────────
1. Open Add Lead Dialog  →  useFieldRegistry('crm', 'leads') fetches config
                         →  API: GET /api/field-registry/config/crm/leads
                         →  Returns: { fields: [...], kanban_stages: [...] }

2. Form Renders          →  DynamicFormFields receives formFields array
                         →  Groups by section, sorts by order
                         →  Renders appropriate input for each field_type

3. User Fills Form       →  onChange updates formData state
                         →  Pincode triggers geo auto-fill if 6 digits

4. Submit                →  POST /api/crm/leads with all field values
```

**Files Modified:**
- `/app/frontend/src/pages/LeadsPage.jsx` - Integrated dynamic form rendering
- Removed unused `useCustomFields` import (replaced by `useFieldRegistry`)

**Test Results:**
- **Test Report:** `/app/test_reports/iteration_17.json`
- **Backend Tests:** 21/21 passed (100%)
- **Frontend Tests:** All dynamic form features verified (100%)

**Features Verified Working:**
| Feature | Status |
|---------|--------|
| Field Registry page loads at /field-registry | ✅ PASS |
| Modules selector (CRM, Inventory, etc.) | ✅ PASS |
| Entities selector (Leads, Accounts, Quotations, Samples) | ✅ PASS |
| Kanban Stages tab with drag-drop | ✅ PASS |
| Form Fields tab with 20 fields | ✅ PASS |
| Add Lead form renders dynamically | ✅ PASS |
| Fields grouped by sections | ✅ PASS |
| Required field markers (*) | ✅ PASS |
| Dropdown options from registry | ✅ PASS |
| Lead creation with dynamic form | ✅ PASS |
| Customize Fields button works | ✅ PASS |

---

## Session Update - January 2026 (Inventory & Dynamic Forms Wiring)

### Inventory Module UI Wired Up ✅ COMPLETE

**Status:** The complete Warehouse & Inventory Management frontend UI is now accessible.

**Changes Made:**
1. **Sidebar Navigation Updated** (`MainLayout.jsx`):
   - Expanded Inventory group with 6 navigation items:
     - Stock & Items (`/inventory`)
     - Warehouses (`/inventory/warehouses`)
     - Stock Register (`/inventory/stock-register`)
     - Stock Transfers (`/inventory/stock-transfers`)
     - Adjustments (`/inventory/stock-adjustments`)
     - Advanced (`/advanced-inventory`)

2. **Routes Already Existed** (`App.jsx` lines 107-114):
   - All warehouse and inventory routes were already defined
   - Just needed sidebar navigation links

**Working Pages:**
- `/inventory/warehouses` - Warehouse Dashboard with 5 warehouses, summary stats, quick actions
- `/inventory/warehouses/new` - Create new warehouse
- `/inventory/warehouses/:id` - Edit warehouse
- `/inventory/stock-register` - Stock Register with search and filters
- `/inventory/stock-transfers` - Stock Transfer list with status filters
- `/inventory/stock-transfers/new` - Create new transfer
- `/inventory/stock-adjustments` - Stock Adjustment list
- `/inventory/stock-adjustments/new` - Create new adjustment

---

### CRM Dynamic Forms Integration ✅ COMPLETE

**Status:** All CRM forms now have Field Registry integration with conditional rendering.

**Changes Made:**
1. **AccountsList Component** (lines 754-763):
   - Added `useFieldRegistry('crm', 'customer_accounts')` hook
   - "Basic Info" tab conditionally renders `DynamicFormFields` component
   - Falls back to hardcoded fields if no registry config exists
   - Addresses, Contacts, Credit tabs remain specialized UI

2. **QuotationsList Component** (lines 1391-1401):
   - Added `useFieldRegistry('crm', 'quotations')` hook
   - Core header fields (Customer, Contact, Reference, Valid Until) remain hardcoded
   - Dynamic header fields render below core fields
   - Line items table remains specialized UI

3. **SamplesList Component** (lines 1958-1968):
   - Added `useFieldRegistry('crm', 'samples')` hook
   - Core header fields (Customer, Contact Person) remain hardcoded
   - Dynamic header fields render below core fields
   - Sample items array management remains specialized UI

**Test Results:**
- **Test Report:** `/app/test_reports/iteration_18.json`
- **Frontend Tests:** 10/10 passed (100%)

**Features Verified Working:**
| Feature | Status |
|---------|--------|
| Inventory sidebar navigation | ✅ PASS |
| Warehouse Dashboard loads | ✅ PASS |
| Stock Register loads | ✅ PASS |
| Stock Transfers loads | ✅ PASS |
| Stock Adjustments loads | ✅ PASS |
| CRM Accounts form opens correctly | ✅ PASS |
| CRM Quotations form opens correctly | ✅ PASS |
| CRM Samples form opens correctly | ✅ PASS |
| Leads dynamic form renders | ✅ PASS |
| CRM Overview dashboard | ✅ PASS |

---

### Default Field Registry Configurations ✅ COMPLETE (January 2026)

**Status:** Default field configurations added for all CRM entities.

**Backend Changes (`field_registry.py`):**
1. **customer_accounts entity** - 10 dynamic fields in `basic` section:
   - Customer Name, Account Type, Industry, GSTIN, PAN, Website, Aadhar No, Opening Balance, Bank Details, Notes

2. **quotations entity** - 7 dynamic fields in `header` section:
   - Transport, Delivery Terms, Payment Terms, Validity (Days), Overall Discount %, Internal Notes, Terms & Conditions

3. **samples entity** - 8 dynamic fields in `header` section:
   - Purpose, Related Quotation, Dispatch Location, Courier/Transport, Tracking Number, Expected Delivery, Feedback Due Date, Notes

**API Tests Verified:**
- `/api/field-registry/config/crm/customer_accounts` → 10 fields (basic section)
- `/api/field-registry/config/crm/quotations` → 7 fields (header section)
- `/api/field-registry/config/crm/samples` → 8 fields (header section)

---

## Next Steps (Priority Order)

### P0 - Critical (COMPLETED)
1. ~~**Wire up Inventory Module Navigation**~~ ✅ DONE
2. ~~**Integrate Dynamic Forms in CRM.jsx**~~ ✅ DONE
3. ~~**Configure Field Registry with default fields**~~ ✅ DONE

### P1 - High Priority (COMPLETED)
1. ~~**Production Module Phase 1**~~ ✅ DONE - Dashboard, Machine Master, Stage Views
2. ~~**Production Module Phase 2**~~ ✅ DONE - Order Sheet creation from Sales Orders, Work Order assignment
3. ~~**Production Module Phase 3**~~ ✅ DONE - DPR (Daily Production Report) with daily/weekly views
4. ~~**Production Module Phase 4**~~ ✅ DONE (Jan 23, 2026) - Enhanced Order Sheet Tabbed Views (Order-wise, Product-wise, Machine-wise)
5. ~~**Production Module Phase 5**~~ ✅ DONE (Jan 23, 2026) - Stage-specific Production Entry Forms with detailed wastage calculation
6. ~~**Production Module Phase 6**~~ ✅ DONE (Jan 24, 2026) - Inventory Integration (Stock holds on order sheet, release on delivery)

### P1 - Next Priority
1. Real-time Chat WebSocket integration
2. GST E-Invoicing API integration (NIC credentials)

### P2 - Medium Priority
1. Refactor `CRM.jsx` into smaller components (currently 2300+ lines)
2. Refactor `ProductionStages.jsx` into smaller components (currently 2100+ lines)
3. Centralize Pydantic models into `/app/backend/models/schemas.py`

### P3 - Future Enhancements
1. AI Predictive Revenue Forecasting
2. "Dimensional Physics Engine" for inventory unit conversion
3. Drive System file editing
4. Advanced Report Builder
5. External API Integrations (IndiaMart, payment gateways)

---

## Production Module Phase 6 - Inventory Integration (January 24, 2026) ✅ COMPLETE

### Stock Hold System
When an order sheet is created from a sales order, raw materials are automatically **reserved** (held) in inventory.

**Stock Hold APIs:**
- `POST /api/production-stages/order-sheets/from-so` - Creates order sheet AND holds stock
- `GET /api/production-stages/inventory/holds` - List all stock holds
- `GET /api/production-stages/inventory/stock-status` - Available vs Reserved quantities

**Stock Release APIs:**
- `PUT /api/production-stages/work-order-stages/{id}/status` - Update status, auto-release on "delivered"
- `POST /api/production-stages/order-sheets/{id}/mark-delivered` - Mark entire order delivered

### Database Collections
- `stock_holds` - Tracks reserved quantities per item per sales order
- `stock_ledger` - Updated when stock is formally deducted

### Workflow
1. **Order Sheet Created** → Raw materials reserved (`status: 'held'`)
2. **Production Progresses** → Work orders move through stages
3. **All WOs Delivered** → Stock released and deducted from inventory

---

## Field Registry Expansion (January 24, 2026) ✅ COMPLETE

### All 8 Modules Now Configurable

| Module | Entities | Total Fields |
|--------|----------|--------------|
| **CRM** | Leads (20), Accounts (21), Quotations (20+9 line), Samples (10) | 60+ fields |
| **Inventory** | Items (28), Warehouses (13), Transfers (10), Adjustments (7) | 61 fields |
| **Production** | Machines (17), Order Sheets (12), Work Orders (14) | 43 fields |
| **Finance** | Invoices (22+9 line), Purchase Invoices (10), Payments (12) | 44 fields |
| **Procurement** | Purchase Orders (11+7 line), GRN (11) | 29 fields |
| **Quality** | Inspections (12+4 params) | 16 fields |
| **HRMS** | Employees (25), Attendance (9), Leaves (9) | 43 fields |
| **Settings** | Users (9), Company (19) | 28 fields |

**Total: 300+ configurable fields across 20+ entities**

### Test Report: `/app/test_reports/iteration_23.json`
- Backend: 32/32 tests passed (100%)
- Frontend: 15/15 features verified (100%)

## Production Module Implementation (January 2026) ✅ PHASE 1 COMPLETE

### Overview
7-Stage Manufacturing Workflow for adhesive tape production:
1. **Coating** - Base material + Adhesive + Release paper → Jumbo Roll (UOM: KG → SQM)
2. **Slitting** - Jumbo roll → Cut rolls (UOM: SQM)
3. **Rewinding** - Jumbo roll → Log rolls (UOM: SQM → Length)
4. **Cutting** - Log rolls → Cut width rolls (UOM: Width)
5. **Packing** - Cut rolls → Packed products (QC video upload)
6. **Ready to Deliver** - Dispatch preparation
7. **Delivered** - Final status (stock auto-deduct after invoice)

### Backend Implementation
**File:** `/app/backend/routes/production_stages.py`

**Machine Master API:**
- `GET /api/production-stages/machines` - List all machines with filters
- `GET /api/production-stages/machines/{id}` - Get machine details
- `POST /api/production-stages/machines` - Create machine with wastage norm
- `PUT /api/production-stages/machines/{id}` - Update machine
- `GET /api/production-stages/machines/suggest/{product_id}` - Auto-suggest based on history

**Order Sheet API:**
- `GET /api/production-stages/order-sheets` - List order sheets
- `GET /api/production-stages/order-sheets/{id}` - Get detail with 3 views
- `POST /api/production-stages/order-sheets` - Create from Sales Order (auto-generates work orders)

**Work Order Stages API:**
- `GET /api/production-stages/work-order-stages` - List with filters
- `PUT /api/production-stages/work-order-stages/{id}/assign-machine` - Assign machine
- `PUT /api/production-stages/work-order-stages/{id}/start` - Start work order
- `POST /api/production-stages/work-order-stages/{id}/entry` - Record production entry
- `POST /api/production-stages/work-order-stages/{id}/comment` - Add comment

**Stage Dashboard API:**
- `GET /api/production-stages/stages/{stage}/dashboard` - Stage-specific metrics
- `GET /api/production-stages/dashboard` - Main production dashboard

**Reports API:**
- `GET /api/production-stages/reports/stage-wise` - Stage-wise production report
- `GET /api/production-stages/reports/machine-wise` - Machine-wise report with wastage analysis

### Frontend Implementation
**File:** `/app/frontend/src/pages/ProductionStages.jsx`

**Components:**
1. **ProductionStagesDashboard** - Main dashboard with:
   - Summary cards (Total SKU, PCS/SQM in process, Overall progress)
   - Priority overview (Urgent, High, Normal, Low)
   - 7-stage pipeline with visual progress indicators
   - Quick actions (Create Order Sheet, Manage Machines, View Reports)

2. **MachineMaster** - Machine CRUD with:
   - Machine cards showing code, name, type, location, capacity
   - **Configurable wastage norm per machine** (highlighted feature)
   - Type and location filters
   - Add/Edit dialog with all fields

3. **OrderSheetsList** - Order sheets table with progress tracking

4. **StageDetailView** - Per-stage dashboard with:
   - Summary stats (Pending, In Progress, Completed, Wastage %)
   - Production quantities with progress bar
   - Work orders table with machine assignment

### Navigation
**Sidebar:** Production group expanded with:
- Overview → `/production`
- Work Orders → `/production-stages`
- Machines → `/production-stages/machines`
- Order Sheets → `/production-stages/order-sheets`

### Test Results (Phase 1)
- **Test Report:** `/app/test_reports/iteration_19.json`
- **Backend Tests:** 22/22 passed (100%)
- **Frontend Tests:** 10/10 features verified (100%)

### Key Features Verified (Phase 1)
| Feature | Status |
|---------|--------|
| Production Dashboard with 7-stage pipeline | ✅ PASS |
| Summary Cards (SKU, PCS, SQM, Progress) | ✅ PASS |
| Machine Master with CRUD | ✅ PASS |
| Configurable wastage norms per machine | ✅ PASS |
| Machine type/location filters | ✅ PASS |
| Stage Detail View with metrics | ✅ PASS |
| Order Sheets List page | ✅ PASS |
| Sidebar Navigation (4 items) | ✅ PASS |
| API Dashboard endpoint | ✅ PASS |

### Sample Machines Created
1. **COAT-01** - Coating Line 1 - Main (BWD, 150 sqm/hour, 4% wastage norm)
2. **SLIT-01** - Slitting Machine 1 (BWD, 200 pcs/hour, 2% wastage norm)
3. **REW-01** - Rewinding Line 1 (SGM, 100 rolls/hour, 2% wastage norm)

---

## Production Module Phase 2 (January 2026) ✅ COMPLETE

### Order Sheet Creation from Sales Orders
**Workflow:** Sales Order → Order Sheet → Work Orders (auto-generated)

**Frontend Components:**
1. **Order Sheet Creation Dialog** (`ProductionStages.jsx`):
   - Lists available (unconverted) sales orders
   - Shows customer name, order value, item count
   - One-click conversion to Order Sheet
   - Auto-generates work orders for all stages (6 stages × items = total WOs)

2. **Order Sheet Detail View** with 3 Tabs:
   - **Tab 1: Order-wise** - Order No, Customer, Status, Comments for confirmations
   - **Tab 2: Product-wise** - Products tracked through all stages with visual progress
   - **Tab 3: Machine-wise** - Work assigned to each machine with load tracking

3. **Work Order Detail View**:
   - Target/Completed/Wastage statistics with progress bar
   - Machine assignment from filtered list (by stage type)
   - "Start Production" button
   - Production entry form with wastage tracking

4. **Production Entry Form**:
   - Start/End Time
   - Input Quantity + UOM (PCS, KG, SQM, Rolls, MTR)
   - Output Quantity + UOM
   - Wastage Quantity + Reason (Setup, Defect, Material, Trim, Other)
   - Notes
   - Automatic wastage % calculation and norm comparison

### Backend Endpoints (Phase 2)
- `GET /api/production-stages/sales-orders/available` - Unconverted sales orders
- `POST /api/production-stages/order-sheets` - Create with auto work orders
- `GET /api/production-stages/order-sheets/{id}` - Detail with 3 views
- `PUT /api/production-stages/work-order-stages/{id}/assign-machine` - Assign machine
- `PUT /api/production-stages/work-order-stages/{id}/start` - Start work order
- `POST /api/production-stages/work-order-stages/{id}/entry` - Record production

### Test Results (Phase 2)
- **Test Report:** `/app/test_reports/iteration_20.json`
- **Frontend Tests:** 10/10 features verified (100%)

### Key Features Verified (Phase 2)
| Feature | Status |
|---------|--------|
| Order Sheet List displays existing order sheets | ✅ PASS |
| Order Sheet Creation Dialog with sales order selection | ✅ PASS |
| Order Sheet Detail with 3-tab layout | ✅ PASS |
| Work Orders Table (12 WOs generated) | ✅ PASS |
| Work Order Detail with stats | ✅ PASS |
| Assign Machine Dialog (filtered by stage) | ✅ PASS |
| Machine Assignment updates work order | ✅ PASS |
| Start Production changes status | ✅ PASS |
| Production Entry Form with wastage tracking | ✅ PASS |
| Dashboard stats update correctly | ✅ PASS |

### Sample Data Created
- **Order Sheet:** OS-20260123-6FAA76 (Test Manufacturing Co., 2 items)
- **Work Orders:** 12 total (2 items × 6 stages)
- **Production Entry:** 1 entry on COAT-01 machine

---

## Production Module Phase 3 - DPR Reports (January 2026) ✅ COMPLETE

### Daily Production Report (DPR) System

**Backend Endpoints:**
- `GET /api/production-stages/dpr/{report_date}` - Comprehensive daily report
- `GET /api/production-stages/dpr/{report_date}/stage/{stage}` - Stage-specific DPR
- `GET /api/production-stages/dpr/summary/weekly` - 7-day trend analysis

**Frontend Component (`ProductionStages.jsx` - DPRReports):**
- **Daily Report Tab:**
  - Summary cards: Total Entries, Work Orders Active, Total Output, Total Wastage, Hours Worked
  - Stage-wise Production Summary table
  - Machine Production tables per stage with wastage norm comparison
  
- **Weekly Trend Tab:**
  - 7-day totals: Total Output, Total Wastage, Avg Daily Output, Avg Wastage %
  - Daily Trend table with date-wise breakdown
  
- **Stage Details Tab:**
  - Stage selector dropdown
  - Stage-specific metrics (Coating: KGs, SQM; Slitting: SQM, PCS, CTN; etc.)

**Stage-Specific Metrics:**
| Stage | Key Metrics |
|-------|-------------|
| Coating | total_kgs_in, total_kgs_out, total_rolls, total_sqm, time_per_roll |
| Slitting | total_sqm_in, total_sqm_out, total_pcs, total_ctn, hourly_avg_pcs/sqm |
| Rewinding | total_length_in, total_length_out, total_logs, balance_jumbo |
| Cutting | total_width_in, total_width_out, calculated_vs_actual |
| Packing | total_pcs_in, total_pcs_out, total_ctn, qc_videos_count |

**Navigation:**
- Production sidebar updated with 5 items: Overview, Work Orders, Machines, Order Sheets, **DPR Reports**

---

## Bug Fix - Leads Kanban (January 2026) ✅ FIXED

**Issue:** New leads not appearing in Kanban view
**Root Cause:** Backend Kanban API hardcoded statuses didn't include 'new', and Field Registry stages didn't have 'new' stage

**Fixes Applied:**
1. Backend `/api/crm/leads/kanban/view` now reads stages from Field Registry with 'new' as fallback
2. Field Registry default stages updated to include 'new' as order 0
3. Database Field Registry configuration updated to include all 10 stages

**Result:** 10 leads across 10 stages now displaying correctly

---

## Comprehensive Module Review (January 2026) ✅ VERIFIED

### Test Report: `/app/test_reports/iteration_21.json`
### Success Rate: 100% (10/10 features)

### All Modules Verified:
| Module | Feature | Status |
|--------|---------|--------|
| Production | DPR Reports page with Daily/Weekly/Stage tabs | ✅ PASS |
| Production | Stage-wise Summary table | ✅ PASS |
| Production | Machine Production with wastage norm | ✅ PASS |
| Production | Weekly Trend analysis | ✅ PASS |
| CRM | Leads Kanban with 10 stages | ✅ PASS |
| CRM | Accounts dynamic form with 4 tabs | ✅ PASS |
| Inventory | Warehouse Dashboard with 5 locations | ✅ PASS |
| Production | 7-stage pipeline dashboard | ✅ PASS |
| Production | Sidebar with 5 navigation items | ✅ PASS |
| Settings | Field Registry with module/entity selectors | ✅ PASS |

### Current System Status:
- **14 Customer Accounts** in CRM
- **10 Leads** across 10 stages (New, Hot Leads, Cold Leads, Contacted, Qualified, Proposal, Negotiation, Converted, Customer, Lost)
- **5 Warehouses** (GST Locations)
- **3 Production Machines** (COAT-01, SLIT-01, REW-01)
- **1 Order Sheet** with 12 Work Orders
- **1 Production Entry** recorded

---

## Production Module Phase 4 & 5 (January 23, 2026) ✅ COMPLETE

### Phase 4: Enhanced Order Sheet Tabbed Views

**Order Sheet Detail Page** (`/production-stages/order-sheets/{id}`) enhanced with rich visualizations:

1. **Order-wise Tab** (Enhanced):
   - Progress bar with percentage
   - Work order counts (Pending, In Progress, Completed)
   - Clickable work order list with stage badges
   - Status-colored badges

2. **Product-wise Tab** (New Visual Pipeline):
   - Each product shows 6-stage pipeline (Coating → Slitting → Rewinding → Cutting → Packing → Ready)
   - Color-coded stage indicators:
     - Green: All work orders completed
     - Blue (pulsing): Work in progress
     - Yellow: Pending work orders
     - Gray: No work orders yet
   - Work order counts per stage
   - Clickable work orders within each stage

3. **Machine-wise Tab** (Enhanced):
   - Machine cards with cyan accents
   - Utilization percentage and progress bar
   - Target/Completed/Remaining stats
   - Work order counts by status
   - Empty state with "Go to Machine Master" button

### Phase 5: Stage-Specific Production Entry Forms

**Stage Form Configurations** (`STAGE_FORM_FIELDS` constant):

| Stage | Title | Description | Specific Fields |
|-------|-------|-------------|-----------------|
| Coating | Coating Entry | Base Film + Adhesive → Jumbo Roll | Jumbo Roll Width/Length/Weight (mm, m, kg), SQM Produced, Base Film/Adhesive/Liner Used (kg), Coating Speed (m/min), Drying Temp (°C) |
| Slitting | Slitting Entry | Jumbo Roll → Cut Rolls | Parent Roll ID, SQM Input/Output, Number of Slits, Slit Widths (comma-separated), Edge Trim Width |
| Rewinding | Rewinding Entry | Jumbo Roll → Log Rolls | Parent Roll ID, Number of Logs, Log Length (m), Core Size (1"/1.5"/2"/3"), Tension Setting |
| Cutting | Cutting Entry | Log Rolls → Cut Width Rolls | Parent Log ID, Cut Length (m), Pieces per Log, Total Pieces |
| Packing | Packing Entry | Cut Rolls → Packed Cartons | Packing Type (shrink/carton/pallet/pouch), Pieces per Carton, Cartons Packed, Net/Gross Weight, QC Status (pass/fail/conditional), QC Video URL |
| Ready to Deliver | Ready to Deliver Entry | Dispatch Preparation | Cartons Ready, Total Weight |

**Enhanced Production Entry Dialog** features:
- Stage-aware header with icon and description
- Three sections with color-coded backgrounds:
  - Gray: Time & Operator
  - Blue: Input & Output Quantities
  - Purple: Stage-specific fields
  - Red: Wastage Tracking
- Dynamic wastage percentage calculation
- Enhanced wastage reasons (Setup, Defect, Material, Edge Trim, Adhesive Issue, Core Defect, Other)
- Notes/Remarks text area

**Backend Schema Update** (`StageEntryCreate` Pydantic model):
Added 25+ optional stage-specific fields for detailed data capture.

### Test Report: `/app/test_reports/iteration_22.json`
### Success Rate: 100% (10/10 features)

| Feature | Status |
|---------|--------|
| Production Dashboard with 7-stage pipeline | ✅ PASS |
| Order Sheet Detail with 3 tabs | ✅ PASS |
| Order-wise tab with progress visualization | ✅ PASS |
| Product-wise tab with visual pipeline | ✅ PASS |
| Machine-wise tab with utilization | ✅ PASS |
| Work Order Detail page | ✅ PASS |
| Add Production Entry button | ✅ PASS |
| Coating stage entry form fields | ✅ PASS |
| Wastage tracking section | ✅ PASS |
| DPR Reports page | ✅ PASS |

---


---

## Architectural Refactoring - Layered Architecture (February 2026) ✅ IN PROGRESS

### Overview
Major architectural refactoring from monolithic structure to a modular, layered architecture following clean code principles.

### New Architecture Pattern
```
Repository Layer → Service Layer → API Layer
   (Data Access)    (Business Logic)    (HTTP Routes)
```

### Directory Structure (Backend)
```
/app/backend/
├── api/                    # API Layer (Routes)
│   └── v1/
│       ├── crm/            # CRM routes (leads, accounts, quotations, samples)
│       ├── inventory/      # Inventory routes (items, warehouses, transfers, adjustments)
│       └── production/     # Production routes (machines, order-sheets, work-orders)
├── services/               # Business Logic Layer
│   ├── crm/service.py      # CRM services (LeadService, AccountService, etc.)
│   ├── inventory/service.py # Inventory services (ItemService, WarehouseService, etc.)
│   └── production/service.py # Production services (MachineService, WorkOrderService, etc.)
├── repositories/           # Data Access Layer
│   ├── base.py             # BaseRepository with CRUD operations
│   ├── crm.py              # CRM repositories
│   ├── inventory.py        # Inventory repositories
│   └── production.py       # Production repositories
├── models/                 # Pydantic Models
│   └── schemas/
│       ├── crm.py          # CRM schemas (LeadCreate, AccountResponse, etc.)
│       ├── inventory.py    # Inventory schemas
│       └── production.py   # Production schemas
└── core/                   # Core utilities
    ├── config.py           # Settings/configuration
    ├── database.py         # MongoDB connection
    ├── security.py         # JWT auth, password hashing
    └── exceptions.py       # Custom exceptions
```

### v1 API Endpoints (New Layered Architecture)

**CRM Module:**
- `GET /api/v1/crm/leads` - List leads
- `GET /api/v1/crm/leads/kanban/view` - Kanban view
- `POST /api/v1/crm/leads` - Create lead
- `PUT /api/v1/crm/leads/{id}` - Update lead
- `DELETE /api/v1/crm/leads/{id}` - Delete lead
- `GET /api/v1/crm/accounts` - List accounts
- `GET /api/v1/crm/quotations` - List quotations
- `GET /api/v1/crm/samples` - List samples

**Inventory Module:**
- `GET /api/v1/inventory/items` - List items
- `GET /api/v1/inventory/items/low-stock` - Low stock alerts
- `GET /api/v1/inventory/warehouses` - List warehouses
- `GET /api/v1/inventory/transfers` - List transfers
- `GET /api/v1/inventory/adjustments` - List adjustments

**Production Module:**
- `GET /api/v1/production/machines` - List machines
- `GET /api/v1/production/machines/available` - Available machines
- `GET /api/v1/production/order-sheets` - List order sheets
- `GET /api/v1/production/work-orders` - List work orders
- `GET /api/v1/production/work-orders/in-progress` - In-progress work orders

### Testing Results (Iteration 24)
- **Backend:** 100% (21/21 tests passed)
- **Frontend:** 100% (Dashboard and login verified)
- **Test File:** `/app/backend/tests/test_v1_layered_api.py`

### Backward Compatibility
- Legacy routes at `/api/{module}` still functional
- New v1 routes at `/api/v1/{module}` use layered architecture
- Frontend continues to use legacy routes (migration planned)

### Next Steps for Refactoring
1. Migrate Accounts module to layered architecture
2. Migrate HRMS module to layered architecture
3. Migrate Procurement module to layered architecture
4. Update frontend to use v1 API endpoints
5. Deprecate legacy routes after frontend migration

---

## Login Credentials
- **Email:** admin@instabiz.com
- **Password:** adminpassword

---

## Last Updated: February 16, 2026

---

## Architectural Refactoring - Phase 2 Complete (February 16, 2026)

### Newly Refactored Modules
Three additional modules have been refactored to use the layered architecture:

1. **Accounts Module** (Invoices, Payments)
   - Repository: `/app/backend/repositories/accounts.py`
   - Service: `/app/backend/services/accounts/service.py`
   - API: `/app/backend/api/v1/accounts/`
   - Features: Invoice CRUD, aging analysis, payment recording

2. **HRMS Module** (Employees, Attendance, Leave Requests, Payroll)
   - Repository: `/app/backend/repositories/hrms.py`
   - Service: `/app/backend/services/hrms/service.py`
   - API: `/app/backend/api/v1/hrms/`
   - Features: Employee management, attendance tracking, leave approval, payroll generation

3. **Procurement Module** (Suppliers, Purchase Orders, GRN)
   - Repository: `/app/backend/repositories/procurement.py`
   - Service: `/app/backend/services/procurement/service.py`
   - API: `/app/backend/api/v1/procurement/`
   - Features: Supplier management, PO lifecycle, GRN with inventory integration

### New v1 API Endpoints

**Accounts Module:**
- `GET /api/v1/accounts/invoices` - List invoices
- `GET /api/v1/accounts/invoices/overdue` - Overdue invoices
- `GET /api/v1/accounts/invoices/aging` - Aging analysis
- `POST /api/v1/accounts/invoices` - Create invoice
- `POST /api/v1/accounts/payments` - Create payment

**HRMS Module:**
- `GET /api/v1/hrms/employees` - List employees
- `POST /api/v1/hrms/employees` - Create employee
- `GET /api/v1/hrms/attendance` - List attendance
- `POST /api/v1/hrms/attendance/{id}/check-in` - Check in
- `POST /api/v1/hrms/attendance/{id}/check-out` - Check out
- `GET /api/v1/hrms/leave-requests` - List leave requests
- `GET /api/v1/hrms/leave-requests/pending` - Pending requests
- `PUT /api/v1/hrms/leave-requests/{id}/approve` - Approve request
- `POST /api/v1/hrms/payroll/generate` - Generate payroll

**Procurement Module:**
- `GET /api/v1/procurement/suppliers` - List suppliers
- `POST /api/v1/procurement/suppliers` - Create supplier
- `GET /api/v1/procurement/purchase-orders` - List POs
- `GET /api/v1/procurement/purchase-orders/pending` - Pending POs
- `POST /api/v1/procurement/purchase-orders` - Create PO
- `PUT /api/v1/procurement/purchase-orders/{id}/send` - Send PO
- `POST /api/v1/procurement/grn` - Create GRN

### Frontend API Migration
Created module-specific API services in `/app/frontend/src/core/api/`:
- `client.js` - Updated with v1Api axios instance
- `index.js` - Exports all module APIs
- `crm.js` - CRM API service
- `inventory.js` - Inventory API service
- `production.js` - Production API service
- `accounts.js` - Accounts API service
- `hrms.js` - HRMS API service
- `procurement.js` - Procurement API service

### Testing Results (Iteration 25)
- **Backend:** 100% (15/15 tests passed)
- **Frontend:** 100% (Dashboard, CRM, Inventory pages verified)
- **Test File:** `/app/backend/tests/test_v1_accounts_hrms_procurement.py`

### Total Modules Refactored: 6
1. CRM (Leads, Accounts, Quotations, Samples)
2. Inventory (Items, Warehouses, Transfers, Adjustments)
3. Production (Machines, Order Sheets, Work Orders)
4. Accounts (Invoices, Payments)
5. HRMS (Employees, Attendance, Leave Requests, Payroll)
6. Procurement (Suppliers, Purchase Orders, GRN)

---

## Last Updated: February 16, 2026

---

## Architectural Refactoring - COMPLETE (February 16, 2026) ✅

### All 9 Modules Refactored

| Module | Repository | Service | API | Status |
|--------|------------|---------|-----|--------|
| CRM | ✅ | ✅ | ✅ | Complete |
| Inventory | ✅ | ✅ | ✅ | Complete |
| Production | ✅ | ✅ | ✅ | Complete |
| Accounts | ✅ | ✅ | ✅ | Complete |
| HRMS | ✅ | ✅ | ✅ | Complete |
| Procurement | ✅ | ✅ | ✅ | Complete |
| Quality | ✅ | ✅ | ✅ | Complete |
| Sales Incentives | ✅ | ✅ | ✅ | Complete |
| Settings | ✅ | ✅ | ✅ | Complete |

### Backend Architecture Summary
```
/app/backend/
├── api/v1/                    # API Layer - 9 module routers
├── services/                  # Business Logic - 9 service modules
├── repositories/              # Data Access - 9 repository files + base
├── models/schemas/            # Pydantic Models - 9 schema files
└── core/                      # Config, DB, Security, Exceptions
```

### Frontend Architecture Summary
```
/app/frontend/src/core/api/    # 9 module API services
├── crm.js
├── inventory.js
├── production.js
├── accounts.js
├── hrms.js
├── procurement.js
├── quality.js
├── salesIncentives.js
└── settings.js
```

### Testing Summary
- **Iteration 24:** CRM, Inventory, Production - 21/21 passed
- **Iteration 25:** Accounts, HRMS, Procurement - 15/15 passed
- **Iteration 26:** Quality, Sales Incentives, Settings - 16/16 passed
- **Total:** 52/52 tests passed (100%)

### API Route Pattern
All v1 routes follow: `/api/v1/{module}/{resource}`

Examples:
- `/api/v1/crm/leads`
- `/api/v1/inventory/items`
- `/api/v1/production/machines`
- `/api/v1/quality/inspections`
- `/api/v1/sales-incentives/targets`
- `/api/v1/settings/branches`

### Backward Compatibility
- Legacy routes at `/api/{module}` still functional
- Frontend can gradually migrate to v1 API services
- No breaking changes to existing functionality

---

## Last Updated: February 16, 2026


---

## Database Migration - MongoDB to PostgreSQL (February 16, 2026) ✅ COMPLETE

### Migration Summary
Complete database migration from MongoDB to PostgreSQL with zero downtime approach.

### Technical Changes

**Database:**
- **From:** MongoDB (motor/pymongo async driver)
- **To:** PostgreSQL 15 with SQLAlchemy 2.0 async (asyncpg)

**Architecture:**
- Created SQLAlchemy ORM models in `/app/backend/models/entities/`
- Updated repositories to use SQLAlchemy queries
- Created compatibility layer (`core/legacy_db.py`) for legacy routes

### New Entity Models
```
/app/backend/models/entities/
├── __init__.py          # Exports all models
├── base.py              # User, Role, Lead, Account, Quotation, Sample, Followup
├── inventory.py         # Item, Warehouse, Stock, StockTransfer, Batch, StockLedger
├── production.py        # Machine, OrderSheet, WorkOrder, ProductionEntry, WorkOrderStage
├── accounts.py          # Invoice, Payment, JournalEntry, ChartOfAccounts, Ledger, Expense
├── procurement.py       # Supplier, PurchaseOrder, PurchaseRequisition, GRN, LandingCost
├── hrms.py              # Employee, Attendance, LeaveRequest, Payroll, Loan, Holiday
└── other.py             # QCInspection, SalesTarget, SystemSetting, Branch, Notification, etc.
```

### Database Schema Features
- **Primary Keys:** UUID (String 36) for all tables
- **Timestamps:** created_at, updated_at, created_by, updated_by on all tables
- **JSONB:** Used for flexible fields (custom_fields, items arrays, specifications)
- **Foreign Keys:** Proper relationships with indexes
- **Constraints:** Unique constraints on codes, emails, document numbers

### Legacy Compatibility Layer
`core/legacy_db.py` provides MongoDB-like interface:
- `db.collection.find_one(query)` → SQLAlchemy select with filters
- `db.collection.find(query).to_list()` → SELECT with conditions
- `db.collection.insert_one(doc)` → INSERT
- `db.collection.update_one(query, {$set: data})` → UPDATE
- `db.collection.delete_one(query)` → DELETE
- Supports MongoDB operators: `$in`, `$nin`, `$ne`, `$lt`, `$lte`, `$gt`, `$gte`, `$regex`

### Environment Variables
```env
# Old (MongoDB - removed)
# MONGO_URL=mongodb://localhost:27017
# DB_NAME=instabiz

# New (PostgreSQL)
DATABASE_URL=postgresql+asyncpg://erp_user:erp_secure_password@localhost:5432/adhesive_erp
```

### Dependencies Updated
**Removed:**
- motor
- pymongo

**Added:**
- asyncpg
- SQLAlchemy[asyncio]
- greenlet

### Testing Results
- **Test Report:** `/app/test_reports/iteration_27.json`
- **Backend Tests:** 16/16 passed (100%)
- **Features Verified:**
  - Authentication (login, token validation)
  - Dashboard (CRM, revenue, inventory metrics)
  - CRM Leads CRUD (v1 API)
  - Inventory Items CRUD (v1 API)
  - Legacy routes (via compatibility layer)

### Migration Notes
- Tables auto-created on server startup via `init_db()`
- Fresh start - no data migration required
- PostgreSQL service started via `service postgresql start`
- MongoDB service stopped (no longer needed)

---
