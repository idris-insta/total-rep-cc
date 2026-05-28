# AdhesiveFlow ERP – Merge & Integration Guide

> Branch: `claude/setup-erp-database-schema-ElYjS`  
> Prepared: 2026-05-28

---

## 1. What This Branch Contains

### Phase 1 – New SQLAlchemy Models (6 new files)

| File | Tables added | Purpose |
|------|-------------|---------|
| `backend/models/entities/dimensional_gl.py` | `cost_centers`, `projects`, `product_lines`, `general_ledger`, `fiscal_years`, `budget_allocations`, `approval_workflows` | Dimensional Accounting – every GL line tagged with branch/CC/project/product-line |
| `backend/models/entities/item_variants.py` | `item_groups`, `uom_conversions`, `item_uom_profiles`, `item_sku_templates`, `item_variants`, `price_lists`, `price_list_items` | SKU template system (IS-51110V-045WHNANL format) + Multi-UOM (Buying/Stocking/Selling) |
| `backend/models/entities/manufacturing_physics.py` | `bills_of_materials`, `bom_items`, `adhesive_mix_formulas`, `coating_orders`, `jumbo_rolls`, `slitting_orders`, `production_shift_logs`, `scrap_entries` | 7-stage manufacturing physics engine with Redline Guard (>7% scrap locks production) |
| `backend/models/entities/hrms_extended.py` | `leave_balances`, `leave_applications`, `shift_masters`, `employee_shift_roster`, `attendance_records`, `employee_salary_assignments`, `payroll_runs`, `payslip_entries`, `employee_loans_ext`, `asset_categories`, `fixed_assets`, `asset_depreciation_entries` | Extended HRMS: shifts, payroll with PF/ESI/TDS, fixed assets & SLM depreciation |
| `backend/models/entities/procurement_full.py` | `purchase_indents`, `purchase_enquiries`, `vendor_quotations`, `goods_received_notes`, `purchase_invoices`, `landed_cost_vouchers` | Full procurement chain: Indent → Enquiry → L1/L2 Vendor Quote → GRN → Invoice → Landed Cost |
| `backend/models/entities/ai_agents.py` | `ai_agents`, `agent_run_logs`, `task_escalations`, `buying_dna_profiles`, `reorder_alerts`, `document_captures`, `ai_insights` | AI agent infrastructure: iSTIX Enforcer (4h escalation cycle), Buying DNA, Document IO |

### Phase 1 – Migration SQL

`backend/migrations/001_phase1_schema.sql` – idempotent DDL (`CREATE TABLE IF NOT EXISTS`, `CREATE INDEX IF NOT EXISTS`).  
Includes seed data: fiscal year 2024-25, 3 AI agent configs, 4 shift masters, 5 product lines, 5 cost centers.

### Housekeeping

- `.gitignore` – rewritten; removed ~25 duplicate `*.env` entries
- `backend/.env.example` – new comprehensive template
- `backend/core/legacy_db.py` – `MODEL_MAP` extended with all 47 Phase 1 tables
- `backend/server.py` – added `GET /api/health` liveness endpoint
- `docker-compose.yml`, `backend/Dockerfile`, `frontend/Dockerfile`, `frontend/nginx.conf` – full Docker deployment stack

---

## 2. Conflict Risk Assessment

### Zero-conflict files (safe to merge)
- All 6 new model files (net-new)
- `001_phase1_schema.sql` (net-new)
- `.env.example` (net-new)
- `docker-compose.yml`, `Dockerfile`s, `nginx.conf` (net-new)

### Low-risk edits (review recommended)
- `models/entities/__init__.py` – added 47 imports and `__all__` entries at the bottom; no existing lines changed
- `backend/core/legacy_db.py` – appended to the `MODEL_MAP` dict only
- `backend/server.py` – added one `/api/health` endpoint after existing dashboard endpoints

### Potential merge conflict zones
- `.gitignore` – if the target repo also cleaned up its gitignore, do a diff and keep the superset of rules

---

## 3. Directory Structure

```
total-rep-cc/
├── backend/
│   ├── api/v1/                  # Layered FastAPI routers (PostgreSQL-native)
│   │   ├── accounts.py
│   │   ├── crm.py
│   │   ├── hrms.py
│   │   ├── inventory.py
│   │   ├── procurement.py
│   │   ├── production.py
│   │   ├── quality.py
│   │   ├── sales_incentives.py
│   │   └── settings.py
│   ├── core/
│   │   ├── config.py            # pydantic-settings; reads .env
│   │   ├── database.py          # async SQLAlchemy engine + session factory
│   │   ├── legacy_db.py         # MongoDB-style shim wrapping SQLAlchemy
│   │   └── security.py
│   ├── migrations/
│   │   └── 001_phase1_schema.sql  # Phase 1 DDL (idempotent)
│   ├── models/entities/
│   │   ├── __init__.py          # Re-exports all models in load order
│   │   ├── base.py              # User, Role, Lead, Account, Quotation, Sample, Followup
│   │   ├── inventory.py
│   │   ├── production.py
│   │   ├── accounts.py
│   │   ├── procurement.py
│   │   ├── hrms.py
│   │   ├── other.py             # QC, Sales, Settings, Branch, Chat, Drive, EInvoice …
│   │   ├── dimensional_gl.py    # ← Phase 1
│   │   ├── item_variants.py     # ← Phase 1
│   │   ├── manufacturing_physics.py  # ← Phase 1
│   │   ├── hrms_extended.py     # ← Phase 1
│   │   ├── procurement_full.py  # ← Phase 1
│   │   └── ai_agents.py         # ← Phase 1
│   ├── repositories/            # Async CRUD wrappers
│   ├── routes/                  # Legacy routes (migrating to api/v1/)
│   ├── services/
│   ├── .env.example             # ← New: copy to .env and fill in values
│   ├── Dockerfile               # ← New
│   ├── requirements.txt
│   └── server.py
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── pages/               # Full page components per ERP module
│   │   ├── modules/             # Reusable module widgets
│   │   ├── context/             # React context providers
│   │   └── hooks/
│   ├── Dockerfile               # ← New (multi-stage: Node build → Nginx)
│   ├── nginx.conf               # ← New (SPA fallback + /api proxy)
│   ├── package.json
│   └── vite.config.js
├── docker-compose.yml           # ← New (postgres + backend + frontend)
├── .gitignore                   # Updated
└── MERGE_GUIDE.md               # This file
```

---

## 4. Prerequisites

| Tool | Min version | Notes |
|------|------------|-------|
| Python | 3.11+ | |
| PostgreSQL | 15+ | Needs `pgcrypto` extension for `gen_random_uuid()` |
| Node.js | 20+ | |
| Yarn | 1.22+ | `npm install -g yarn` |
| Docker + Docker Compose | 24+ | Only for containerised deployment |

---

## 5. Environment Setup (Local Dev)

```bash
# 1. Clone / pull branch
git checkout claude/setup-erp-database-schema-ElYjS

# 2. Backend
cd backend
cp .env.example .env
# Edit .env – set DATABASE_URL, JWT_SECRET (see below), API keys

# Generate a strong JWT secret:
python -c "import secrets; print(secrets.token_hex(32))"

python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# 3. Database
createdb adhesive_erp             # or use psql
psql adhesive_erp -c "CREATE EXTENSION IF NOT EXISTS pgcrypto;"
psql adhesive_erp < migrations/001_phase1_schema.sql

# 4. Start backend
uvicorn server:app --reload --port 8001

# 5. Frontend (separate terminal)
cd ../frontend
yarn install
yarn start                        # http://localhost:3000
```

---

## 6. Docker Deployment

```bash
# At repo root
cp backend/.env.example .env
# Edit .env – fill POSTGRES_PASSWORD, JWT_SECRET, LLM keys

docker compose up -d --build

# Check health
curl http://localhost:8001/api/health
# {"status":"ok","version":"2.0.0"}

# Access UI
open http://localhost
```

To run migration against a containerised DB:
```bash
docker compose exec postgres psql -U erp_user -d adhesive_erp \
    -f /docker-entrypoint-initdb.d/001_phase1_schema.sql
```

---

## 7. Running the Migration Against an Existing Database

The migration file is fully idempotent. Run it against any existing database; it will skip tables/indexes that already exist:

```bash
psql "$DATABASE_URL" < backend/migrations/001_phase1_schema.sql
```

After running, verify key tables:
```sql
SELECT tablename FROM pg_tables
WHERE schemaname = 'public'
  AND tablename IN (
    'dimensional_gl', 'item_variants', 'coating_orders',
    'jumbo_rolls', 'slitting_orders', 'ai_agents', 'buying_dna_profiles'
  )
ORDER BY tablename;
```

---

## 8. API Reference Summary

### Existing endpoints (unchanged)
| Prefix | File | Notes |
|--------|------|-------|
| `/api/v1/crm` | `api/v1/crm.py` | PostgreSQL-native |
| `/api/v1/inventory` | `api/v1/inventory.py` | PostgreSQL-native |
| `/api/v1/production` | `api/v1/production.py` | |
| `/api/v1/accounts` | `api/v1/accounts.py` | |
| `/api/v1/hrms` | `api/v1/hrms.py` | |
| `/api/v1/procurement` | `api/v1/procurement.py` | |
| `/api/auth/...` | `server.py` | JWT login/register |

### New endpoint added by this branch
| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/health` | Liveness probe; returns `{"status":"ok"}` |

### Phase 1 tables accessible via legacy `db` shim (no new routes yet)
The `MODEL_MAP` in `backend/core/legacy_db.py` now exposes all 47 Phase 1 tables. New v1 API routes for manufacturing, dimensional GL, and AI agent management should be added as `api/v1/manufacturing.py`, `api/v1/dimensional_gl.py`, etc. in subsequent sprints.

---

## 9. Key Business Rules Implemented

### Physics Engine (manufacturing_physics.py)
```
weight_per_roll_kg = sqm_per_roll × (thickness_microns / 1_000_000) × (density_g_cm3 × 1000)
```
Stored as `ItemVariant.weight_per_roll_kg` – pre-computed, never recalculated at runtime.

### Redline Guard (CoatingOrder)
- `scrap_pct = (input_weight_kg - output_weight_kg) / input_weight_kg × 100`
- If `scrap_pct > 7.0`: sets `redline_triggered = True`, `production_locked = True`
- Production resumes only when `redline_override_by` (Director role) + `redline_override_reason` are set

### iSTIX Escalation Ladder (TaskEscalation)
| Level | Trigger | Recipient |
|-------|---------|-----------|
| 1 | ≥ 4 hours overdue | Manager |
| 2 | ≥ 8 hours overdue | Director |
| 3 | ≥ 24 hours overdue | CEO |

Cron: `0 */4 * * *` (every 4 hours)

### Buying DNA Urgency Score (BuyingDNAProfile)
```
urgency_score = days_since_last_order / avg_cycle_days
```
If `urgency_score ≥ 1.0` → generates a `ReorderAlert`

### SKU Template Format
```
IS-51110V-045WHNANL
↑ category prefix
      ↑ base product code
              ↑ variant suffix (adhesive/liner/color codes)

Variant code: IS-51110V-045WHNANL-48x100
                                   ↑  ↑
                               width  length (mm × m)
```

### Multi-UOM
| Layer | UOM | Example |
|-------|-----|---------|
| Buying | Tons | 1 Ton |
| Stocking | KG | 1000 KG |
| Selling | Rolls / Boxes | 200 Rolls |

Conversion stored in `ItemUOMProfile.buying_to_stocking_factor` and `weight_per_roll_kg`.

---

## 10. Merge Steps for Target Repository

```bash
# In the target repo
git remote add source https://github.com/idris-insta/total-rep-cc.git
git fetch source claude/setup-erp-database-schema-ElYjS

# Review the diff
git diff main source/claude/setup-erp-database-schema-ElYjS -- \
    backend/models/entities/__init__.py \
    backend/core/legacy_db.py \
    backend/server.py \
    .gitignore

# Merge (prefer rebase for clean history)
git checkout -b feat/adhesiveflow-phase1
git merge --no-ff source/claude/setup-erp-database-schema-ElYjS

# Resolve any conflicts in __init__.py / legacy_db.py (additive only)
# Then run tests
cd backend && pytest tests/ -v

# Apply migration
psql "$DATABASE_URL" < backend/migrations/001_phase1_schema.sql
```

---

## 11. Known Gaps / Next Sprints

| Item | Priority | Notes |
|------|----------|-------|
| `api/v1/manufacturing.py` | High | REST endpoints for CoatingOrder, SlittingOrder, JumboRoll |
| `api/v1/dimensional_gl.py` | High | GL entry, P&L by cost center/project |
| `api/v1/procurement_full.py` | High | Indent→GRN→Invoice workflow endpoints |
| `api/v1/ai_agents.py` | Medium | Agent run trigger, escalation management |
| Redline override UI | High | Director dashboard widget |
| iSTIX background task | Medium | APScheduler / Celery job for escalation runs |
| Buying DNA job | Medium | Nightly cron to update `urgency_score`, fire `ReorderAlert` |
| `frontend/src/pages/Manufacturing.jsx` | High | Coating + Slitting workflow UI |
| `frontend/src/pages/DimensionalGL.jsx` | Medium | MIS P&L by dimension |
| Production → SKU variant picker | Medium | Width × Length matrix in Work Order |
