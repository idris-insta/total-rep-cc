-- =============================================================================
-- AdhesiveFlow ERP – Phase 1 Schema Migration
-- Instabiz Solutions (Adhesive Tapes Industry)
-- PostgreSQL 15+  |  UUIDs  |  JSONB for extensibility
--
-- Run order:
--   1. Dimensional GL (branches extension, cost_centers, projects, product_lines,
--      general_ledger, fiscal_years, budget_allocations, approval_workflows)
--   2. SKU & Multi-UOM (item_groups, uom_conversions, item_uom_profiles,
--      item_sku_templates, item_variants, price_lists, price_list_items)
--   3. Manufacturing Physics (bom_headers, bom_items, adhesive_mix_formulas,
--      coating_orders, jumbo_rolls, slitting_orders, production_shift_logs,
--      scrap_entries)
--   4. HRMS Extended (leave_balances, leave_applications, shift_masters,
--      employee_shift_rosters, attendance_records,
--      employee_salary_assignments, payroll_runs, payslip_entries,
--      employee_loans_ext, asset_categories, fixed_assets,
--      asset_depreciation_entries)
--   5. Full Procurement (purchase_indents, purchase_enquiries,
--      vendor_quotations, goods_received_notes, purchase_invoices,
--      landed_cost_vouchers)
--   6. AI Agent Layer (ai_agents, agent_run_logs, task_escalations,
--      buying_dna_profiles, reorder_alerts, document_captures, ai_insights)
-- =============================================================================

-- Enable pgcrypto for UUID generation if not already enabled
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Helper: auto-update updated_at on any UPDATE
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW() AT TIME ZONE 'UTC';
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;


-- =============================================================================
-- SECTION 1: DIMENSIONAL GL
-- =============================================================================

-- 1.1  Extend existing branches table with GST / state info (idempotent)
ALTER TABLE branches
    ADD COLUMN IF NOT EXISTS state_code    VARCHAR(10),
    ADD COLUMN IF NOT EXISTS gstin         VARCHAR(20),
    ADD COLUMN IF NOT EXISTS is_default    BOOLEAN DEFAULT FALSE;

-- 1.2  Cost Centers
CREATE TABLE IF NOT EXISTS cost_centers (
    id              VARCHAR(36)     PRIMARY KEY DEFAULT gen_random_uuid()::text,
    code            VARCHAR(50)     NOT NULL UNIQUE,
    name            VARCHAR(255)    NOT NULL,
    parent_id       VARCHAR(36)     REFERENCES cost_centers(id) ON DELETE SET NULL,
    branch_id       VARCHAR(36)     REFERENCES branches(id) ON DELETE SET NULL,
    is_group        BOOLEAN         DEFAULT FALSE,
    is_active       BOOLEAN         DEFAULT TRUE,
    budget_amount   NUMERIC(18,4)   DEFAULT 0,
    custom_fields   JSONB,
    created_at      TIMESTAMPTZ     DEFAULT NOW(),
    updated_at      TIMESTAMPTZ     DEFAULT NOW(),
    created_by      VARCHAR(36),
    updated_by      VARCHAR(36)
);
CREATE INDEX IF NOT EXISTS ix_cost_centers_code ON cost_centers(code);
CREATE INDEX IF NOT EXISTS ix_cost_centers_branch ON cost_centers(branch_id);

-- 1.3  Projects
CREATE TABLE IF NOT EXISTS projects (
    id              VARCHAR(36)     PRIMARY KEY DEFAULT gen_random_uuid()::text,
    code            VARCHAR(50)     NOT NULL UNIQUE,
    name            VARCHAR(255)    NOT NULL,
    project_type    VARCHAR(50),
    start_date      TIMESTAMPTZ,
    end_date        TIMESTAMPTZ,
    budget_amount   NUMERIC(18,4)   DEFAULT 0,
    actual_spend    NUMERIC(18,4)   DEFAULT 0,
    status          VARCHAR(50)     DEFAULT 'active',
    manager_id      VARCHAR(36)     REFERENCES users(id) ON DELETE SET NULL,
    branch_id       VARCHAR(36)     REFERENCES branches(id) ON DELETE SET NULL,
    is_active       BOOLEAN         DEFAULT TRUE,
    custom_fields   JSONB,
    created_at      TIMESTAMPTZ     DEFAULT NOW(),
    updated_at      TIMESTAMPTZ     DEFAULT NOW(),
    created_by      VARCHAR(36),
    updated_by      VARCHAR(36)
);

-- 1.4  Product Lines
CREATE TABLE IF NOT EXISTS product_lines (
    id              VARCHAR(36)     PRIMARY KEY DEFAULT gen_random_uuid()::text,
    code            VARCHAR(50)     NOT NULL UNIQUE,
    name            VARCHAR(255)    NOT NULL,
    description     TEXT,
    is_active       BOOLEAN         DEFAULT TRUE,
    custom_fields   JSONB,
    created_at      TIMESTAMPTZ     DEFAULT NOW(),
    updated_at      TIMESTAMPTZ     DEFAULT NOW(),
    created_by      VARCHAR(36),
    updated_by      VARCHAR(36)
);

-- 1.5  General Ledger (core dimensional transaction table)
CREATE TABLE IF NOT EXISTS general_ledger (
    id                  VARCHAR(36)     PRIMARY KEY DEFAULT gen_random_uuid()::text,
    posting_date        TIMESTAMPTZ     NOT NULL,
    fiscal_year         VARCHAR(10)     NOT NULL,           -- e.g. "2024-25"
    fiscal_period       SMALLINT        NOT NULL,           -- 1-12

    -- Voucher reference
    voucher_type        VARCHAR(50)     NOT NULL,
    voucher_number      VARCHAR(100)    NOT NULL,
    voucher_id          VARCHAR(36),

    -- Account
    account_id          VARCHAR(36)     NOT NULL REFERENCES chart_of_accounts(id),
    account_code        VARCHAR(50)     NOT NULL,
    account_name        VARCHAR(255)    NOT NULL,

    -- Amounts (INR)
    debit               NUMERIC(18,4)   NOT NULL DEFAULT 0,
    credit              NUMERIC(18,4)   NOT NULL DEFAULT 0,
    balance             NUMERIC(18,4)   DEFAULT 0,

    -- Dimension tags
    branch_id           VARCHAR(36)     REFERENCES branches(id),
    cost_center_id      VARCHAR(36)     REFERENCES cost_centers(id),
    project_id          VARCHAR(36)     REFERENCES projects(id),
    product_line_id     VARCHAR(36)     REFERENCES product_lines(id),

    -- Party
    party_type          VARCHAR(50),
    party_id            VARCHAR(36),
    party_name          VARCHAR(255),

    -- Metadata
    narration           TEXT,
    is_cancelled        BOOLEAN         DEFAULT FALSE,
    is_opening          BOOLEAN         DEFAULT FALSE,
    maker_id            VARCHAR(36)     REFERENCES users(id),
    approver_id         VARCHAR(36)     REFERENCES users(id),
    approved_at         TIMESTAMPTZ,
    dimensions          JSONB,          -- extra dimension tags

    created_at          TIMESTAMPTZ     DEFAULT NOW(),
    updated_at          TIMESTAMPTZ     DEFAULT NOW(),
    created_by          VARCHAR(36),
    updated_by          VARCHAR(36)
);

CREATE INDEX IF NOT EXISTS ix_gl_date_account        ON general_ledger(posting_date, account_id);
CREATE INDEX IF NOT EXISTS ix_gl_voucher             ON general_ledger(voucher_type, voucher_number);
CREATE INDEX IF NOT EXISTS ix_gl_branch_period       ON general_ledger(branch_id, fiscal_year, fiscal_period);
CREATE INDEX IF NOT EXISTS ix_gl_cc_period           ON general_ledger(cost_center_id, fiscal_year, fiscal_period);
CREATE INDEX IF NOT EXISTS ix_gl_project             ON general_ledger(project_id);
CREATE INDEX IF NOT EXISTS ix_gl_cancelled           ON general_ledger(is_cancelled) WHERE is_cancelled = FALSE;

-- 1.6  Fiscal Years
CREATE TABLE IF NOT EXISTS fiscal_years (
    id          VARCHAR(36)     PRIMARY KEY DEFAULT gen_random_uuid()::text,
    name        VARCHAR(20)     NOT NULL UNIQUE,
    start_date  TIMESTAMPTZ     NOT NULL,
    end_date    TIMESTAMPTZ     NOT NULL,
    is_active   BOOLEAN         DEFAULT TRUE,
    is_closed   BOOLEAN         DEFAULT FALSE,
    closed_by   VARCHAR(36)     REFERENCES users(id),
    closed_at   TIMESTAMPTZ,
    created_at  TIMESTAMPTZ     DEFAULT NOW(),
    updated_at  TIMESTAMPTZ     DEFAULT NOW(),
    created_by  VARCHAR(36),
    updated_by  VARCHAR(36)
);

-- 1.7  Budget Allocations
CREATE TABLE IF NOT EXISTS budget_allocations (
    id              VARCHAR(36)     PRIMARY KEY DEFAULT gen_random_uuid()::text,
    fiscal_year     VARCHAR(10)     NOT NULL,
    fiscal_period   SMALLINT,
    account_id      VARCHAR(36)     NOT NULL REFERENCES chart_of_accounts(id),
    branch_id       VARCHAR(36)     REFERENCES branches(id),
    cost_center_id  VARCHAR(36)     REFERENCES cost_centers(id),
    project_id      VARCHAR(36)     REFERENCES projects(id),
    budget_amount   NUMERIC(18,4)   DEFAULT 0,
    notes           TEXT,
    created_at      TIMESTAMPTZ     DEFAULT NOW(),
    updated_at      TIMESTAMPTZ     DEFAULT NOW(),
    created_by      VARCHAR(36),
    updated_by      VARCHAR(36)
);
CREATE INDEX IF NOT EXISTS ix_budget_fy ON budget_allocations(fiscal_year);

-- 1.8  Approval Workflows (Maker-Checker)
CREATE TABLE IF NOT EXISTS approval_workflows (
    id              VARCHAR(36)     PRIMARY KEY DEFAULT gen_random_uuid()::text,
    document_type   VARCHAR(100)    NOT NULL,
    document_id     VARCHAR(36)     NOT NULL,
    document_number VARCHAR(100),
    status          VARCHAR(50)     DEFAULT 'pending_approval',
    -- pending_approval | approved | rejected | cancelled

    maker_id        VARCHAR(36)     NOT NULL REFERENCES users(id),
    maker_name      VARCHAR(255),
    submitted_at    TIMESTAMPTZ     DEFAULT NOW(),

    approver_id     VARCHAR(36)     REFERENCES users(id),
    approver_name   VARCHAR(255),
    actioned_at     TIMESTAMPTZ,

    remarks         TEXT,
    rejection_reason TEXT,
    amount          NUMERIC(18,4),
    metadata_json   JSONB,

    created_at      TIMESTAMPTZ     DEFAULT NOW(),
    updated_at      TIMESTAMPTZ     DEFAULT NOW(),
    created_by      VARCHAR(36),
    updated_by      VARCHAR(36)
);
CREATE INDEX IF NOT EXISTS ix_appr_wf_doc    ON approval_workflows(document_type, document_id);
CREATE INDEX IF NOT EXISTS ix_appr_wf_status ON approval_workflows(status);


-- =============================================================================
-- SECTION 2: SKU & MULTI-UOM
-- =============================================================================

-- 2.1  Item Groups (unlimited hierarchy)
CREATE TABLE IF NOT EXISTS item_groups (
    id                  VARCHAR(36)     PRIMARY KEY DEFAULT gen_random_uuid()::text,
    code                VARCHAR(50)     NOT NULL UNIQUE,
    name                VARCHAR(255)    NOT NULL,
    parent_id           VARCHAR(36)     REFERENCES item_groups(id),
    is_group            BOOLEAN         DEFAULT FALSE,
    product_line_id     VARCHAR(36)     REFERENCES product_lines(id),
    default_gst_rate    NUMERIC(6,2)    DEFAULT 18.00,
    default_hsn         VARCHAR(20),
    is_active           BOOLEAN         DEFAULT TRUE,
    custom_fields       JSONB,
    created_at          TIMESTAMPTZ     DEFAULT NOW(),
    updated_at          TIMESTAMPTZ     DEFAULT NOW(),
    created_by          VARCHAR(36),
    updated_by          VARCHAR(36)
);

-- 2.2  UOM Conversions
CREATE TABLE IF NOT EXISTS uom_conversions (
    id          VARCHAR(36)     PRIMARY KEY DEFAULT gen_random_uuid()::text,
    item_id     VARCHAR(36)     REFERENCES items(id) ON DELETE CASCADE,
    from_uom    VARCHAR(50)     NOT NULL,
    to_uom      VARCHAR(50)     NOT NULL,
    factor      NUMERIC(18,8)   NOT NULL,           -- to_uom = from_uom × factor
    notes       TEXT,
    created_at  TIMESTAMPTZ     DEFAULT NOW(),
    updated_at  TIMESTAMPTZ     DEFAULT NOW(),
    created_by  VARCHAR(36),
    updated_by  VARCHAR(36),
    UNIQUE (item_id, from_uom, to_uom)
);

-- 2.3  Item UOM Profiles
CREATE TABLE IF NOT EXISTS item_uom_profiles (
    id                          VARCHAR(36)     PRIMARY KEY DEFAULT gen_random_uuid()::text,
    item_id                     VARCHAR(36)     NOT NULL UNIQUE REFERENCES items(id) ON DELETE CASCADE,
    buying_uom                  VARCHAR(50)     DEFAULT 'Tons',
    stocking_uom                VARCHAR(50)     DEFAULT 'KG',
    selling_uom                 VARCHAR(50)     DEFAULT 'Rolls',
    buying_to_stocking_factor   NUMERIC(18,8)   DEFAULT 1000,
    weight_per_roll_kg          NUMERIC(12,6),
    rolls_per_box               INTEGER,
    selling_uom_alt             VARCHAR(50),
    notes                       TEXT,
    created_at                  TIMESTAMPTZ     DEFAULT NOW(),
    updated_at                  TIMESTAMPTZ     DEFAULT NOW(),
    created_by                  VARCHAR(36),
    updated_by                  VARCHAR(36)
);

-- 2.4  Item SKU Templates
CREATE TABLE IF NOT EXISTS item_sku_templates (
    id                  VARCHAR(36)     PRIMARY KEY DEFAULT gen_random_uuid()::text,
    sku_code            VARCHAR(100)    NOT NULL UNIQUE,
    item_id             VARCHAR(36)     NOT NULL REFERENCES items(id) ON DELETE CASCADE,
    sku_segments        JSONB,
    -- e.g. {"brand":"IS","spec":"51110","version":"V","micron":"045","attrs":"WHNANL"}
    base_material       VARCHAR(100),
    adhesive_type       VARCHAR(100),
    color               VARCHAR(50),
    thickness_microns   NUMERIC(10,4),
    gsm                 NUMERIC(10,4),
    core_diameter_mm    NUMERIC(10,4),
    density_g_cm3       NUMERIC(10,6),
    is_active           BOOLEAN         DEFAULT TRUE,
    notes               TEXT,
    created_at          TIMESTAMPTZ     DEFAULT NOW(),
    updated_at          TIMESTAMPTZ     DEFAULT NOW(),
    created_by          VARCHAR(36),
    updated_by          VARCHAR(36)
);
CREATE INDEX IF NOT EXISTS ix_sku_template_item ON item_sku_templates(item_id);

-- 2.5  Item Variants  (width × length pairs)
CREATE TABLE IF NOT EXISTS item_variants (
    id                  VARCHAR(36)     PRIMARY KEY DEFAULT gen_random_uuid()::text,
    sku_template_id     VARCHAR(36)     NOT NULL REFERENCES item_sku_templates(id) ON DELETE CASCADE,
    item_id             VARCHAR(36)     NOT NULL REFERENCES items(id) ON DELETE CASCADE,
    variant_code        VARCHAR(150)    NOT NULL UNIQUE,
    width_mm            NUMERIC(10,4)   NOT NULL,
    length_m            NUMERIC(10,4)   NOT NULL,
    -- Physics (pre-computed)
    -- sqm_per_roll     = (width_mm/1000) × length_m
    -- weight_per_roll_kg = sqm × (thickness_microns/1e6) × (density_g_cm3×1000)
    sqm_per_roll        NUMERIC(14,6),
    weight_per_roll_kg  NUMERIC(14,6),
    -- Pricing
    purchase_price      NUMERIC(14,4)   DEFAULT 0,
    selling_price       NUMERIC(14,4)   DEFAULT 0,
    mrp                 NUMERIC(14,4),
    -- Stock (denormalized for fast reads)
    stock_rolls         NUMERIC(14,4)   DEFAULT 0,
    stock_kg            NUMERIC(14,4)   DEFAULT 0,
    barcode             VARCHAR(100),
    is_active           BOOLEAN         DEFAULT TRUE,
    custom_fields       JSONB,
    created_at          TIMESTAMPTZ     DEFAULT NOW(),
    updated_at          TIMESTAMPTZ     DEFAULT NOW(),
    created_by          VARCHAR(36),
    updated_by          VARCHAR(36),
    UNIQUE (sku_template_id, width_mm, length_m)
);
CREATE INDEX IF NOT EXISTS ix_variant_sku_template ON item_variants(sku_template_id);
CREATE INDEX IF NOT EXISTS ix_variant_barcode       ON item_variants(barcode) WHERE barcode IS NOT NULL;

-- 2.6  Price Lists
CREATE TABLE IF NOT EXISTS price_lists (
    id                  VARCHAR(36)     PRIMARY KEY DEFAULT gen_random_uuid()::text,
    name                VARCHAR(255)    NOT NULL,
    currency            VARCHAR(10)     DEFAULT 'INR',
    price_list_type     VARCHAR(20)     DEFAULT 'selling',
    branch_id           VARCHAR(36)     REFERENCES branches(id),
    valid_from          TIMESTAMPTZ,
    valid_to            TIMESTAMPTZ,
    is_active           BOOLEAN         DEFAULT TRUE,
    notes               TEXT,
    created_at          TIMESTAMPTZ     DEFAULT NOW(),
    updated_at          TIMESTAMPTZ     DEFAULT NOW(),
    created_by          VARCHAR(36),
    updated_by          VARCHAR(36)
);

-- 2.7  Price List Items
CREATE TABLE IF NOT EXISTS price_list_items (
    id              VARCHAR(36)     PRIMARY KEY DEFAULT gen_random_uuid()::text,
    price_list_id   VARCHAR(36)     NOT NULL REFERENCES price_lists(id) ON DELETE CASCADE,
    item_id         VARCHAR(36)     REFERENCES items(id),
    variant_id      VARCHAR(36)     REFERENCES item_variants(id),
    uom             VARCHAR(50)     DEFAULT 'Rolls',
    rate            NUMERIC(14,4)   NOT NULL,
    min_qty         NUMERIC(14,4)   DEFAULT 0,
    discount_percent NUMERIC(6,2)   DEFAULT 0,
    created_at      TIMESTAMPTZ     DEFAULT NOW(),
    updated_at      TIMESTAMPTZ     DEFAULT NOW(),
    created_by      VARCHAR(36),
    updated_by      VARCHAR(36)
);
CREATE INDEX IF NOT EXISTS ix_pli_list_item ON price_list_items(price_list_id, item_id, variant_id);


-- =============================================================================
-- SECTION 3: MANUFACTURING PHYSICS ENGINE
-- =============================================================================

-- 3.1  BOM Headers
CREATE TABLE IF NOT EXISTS bom_headers (
    id                  VARCHAR(36)     PRIMARY KEY DEFAULT gen_random_uuid()::text,
    bom_number          VARCHAR(50)     NOT NULL UNIQUE,
    item_id             VARCHAR(36)     NOT NULL REFERENCES items(id),
    variant_id          VARCHAR(36)     REFERENCES item_variants(id),
    output_qty          NUMERIC(14,4)   DEFAULT 1,
    output_uom          VARCHAR(50)     DEFAULT 'KG',
    thickness_microns   NUMERIC(10,4),
    density_g_cm3       NUMERIC(10,6),
    bom_type            VARCHAR(50)     DEFAULT 'manufacturing',
    stage               VARCHAR(50),
    is_active           BOOLEAN         DEFAULT TRUE,
    is_default          BOOLEAN         DEFAULT TRUE,
    version             INTEGER         DEFAULT 1,
    notes               TEXT,
    custom_fields       JSONB,
    created_at          TIMESTAMPTZ     DEFAULT NOW(),
    updated_at          TIMESTAMPTZ     DEFAULT NOW(),
    created_by          VARCHAR(36),
    updated_by          VARCHAR(36)
);

-- 3.2  BOM Line Items
CREATE TABLE IF NOT EXISTS bom_items (
    id              VARCHAR(36)     PRIMARY KEY DEFAULT gen_random_uuid()::text,
    bom_id          VARCHAR(36)     NOT NULL REFERENCES bom_headers(id) ON DELETE CASCADE,
    item_id         VARCHAR(36)     NOT NULL REFERENCES items(id),
    sequence        INTEGER         DEFAULT 1,
    qty_per_unit    NUMERIC(14,6)   NOT NULL,
    uom             VARCHAR(50)     DEFAULT 'KG',
    qty_formula     VARCHAR(255),
    scrap_percent   NUMERIC(6,4)    DEFAULT 0,
    item_type       VARCHAR(50)     DEFAULT 'raw_material',
    notes           TEXT,
    created_at      TIMESTAMPTZ     DEFAULT NOW(),
    updated_at      TIMESTAMPTZ     DEFAULT NOW(),
    created_by      VARCHAR(36),
    updated_by      VARCHAR(36)
);
CREATE INDEX IF NOT EXISTS ix_bom_items_bom ON bom_items(bom_id);

-- 3.3  Adhesive Mix Formulas
CREATE TABLE IF NOT EXISTS adhesive_mix_formulas (
    id                      VARCHAR(36)     PRIMARY KEY DEFAULT gen_random_uuid()::text,
    formula_code            VARCHAR(50)     NOT NULL UNIQUE,
    formula_name            VARCHAR(255)    NOT NULL,
    output_item_id          VARCHAR(36)     REFERENCES items(id),
    output_qty_kg           NUMERIC(14,4)   DEFAULT 100,
    components              JSONB,
    -- [{item_id, item_name, qty_kg, percentage, notes}]
    viscosity_cps           NUMERIC(12,4),
    solid_content_percent   NUMERIC(6,4),
    ph_value                NUMERIC(6,4),
    is_active               BOOLEAN         DEFAULT TRUE,
    version                 INTEGER         DEFAULT 1,
    notes                   TEXT,
    created_at              TIMESTAMPTZ     DEFAULT NOW(),
    updated_at              TIMESTAMPTZ     DEFAULT NOW(),
    created_by              VARCHAR(36),
    updated_by              VARCHAR(36)
);

-- 3.4  Coating Orders (Stage 1)
CREATE TABLE IF NOT EXISTS coating_orders (
    id                      VARCHAR(36)     PRIMARY KEY DEFAULT gen_random_uuid()::text,
    co_number               VARCHAR(50)     NOT NULL UNIQUE,
    work_order_id           VARCHAR(36)     REFERENCES work_orders(id),
    machine_id              VARCHAR(36)     REFERENCES machines(id),
    planned_date            TIMESTAMPTZ     NOT NULL,
    status                  VARCHAR(50)     DEFAULT 'planned',
    -- Input materials
    bopp_item_id            VARCHAR(36)     REFERENCES items(id),
    bopp_roll_width_mm      NUMERIC(10,4),
    bopp_input_kg           NUMERIC(14,4)   DEFAULT 0,
    bopp_input_sqm          NUMERIC(14,4)   DEFAULT 0,
    adhesive_formula_id     VARCHAR(36)     REFERENCES adhesive_mix_formulas(id),
    adhesive_input_kg       NUMERIC(14,4)   DEFAULT 0,
    liner_item_id           VARCHAR(36)     REFERENCES items(id),
    liner_input_kg          NUMERIC(14,4)   DEFAULT 0,
    -- Physics targets
    target_thickness_microns NUMERIC(10,4),
    target_coating_gsm      NUMERIC(10,4),
    target_sqm              NUMERIC(14,4),
    target_output_kg        NUMERIC(14,4),
    -- Actuals
    actual_output_kg        NUMERIC(14,4)   DEFAULT 0,
    actual_output_sqm       NUMERIC(14,4)   DEFAULT 0,
    scrap_kg                NUMERIC(14,4)   DEFAULT 0,
    scrap_percent           NUMERIC(7,4)    DEFAULT 0,
    -- Redline Guard (threshold = 7%)
    redline_triggered       BOOLEAN         DEFAULT FALSE,
    redline_override_by     VARCHAR(36)     REFERENCES users(id),
    redline_override_at     TIMESTAMPTZ,
    redline_override_reason TEXT,
    -- Output
    jumbo_roll_batch        VARCHAR(100),
    jumbo_item_id           VARCHAR(36)     REFERENCES items(id),
    shift                   VARCHAR(20),
    operator_id             VARCHAR(36)     REFERENCES users(id),
    supervisor_id           VARCHAR(36)     REFERENCES users(id),
    qc_passed               BOOLEAN,
    qc_params               JSONB,
    notes                   TEXT,
    custom_fields           JSONB,
    created_at              TIMESTAMPTZ     DEFAULT NOW(),
    updated_at              TIMESTAMPTZ     DEFAULT NOW(),
    created_by              VARCHAR(36),
    updated_by              VARCHAR(36)
);
CREATE INDEX IF NOT EXISTS ix_coating_status        ON coating_orders(status);
CREATE INDEX IF NOT EXISTS ix_coating_jumbo_batch   ON coating_orders(jumbo_roll_batch) WHERE jumbo_roll_batch IS NOT NULL;
CREATE INDEX IF NOT EXISTS ix_coating_redline       ON coating_orders(redline_triggered) WHERE redline_triggered = TRUE;

-- 3.5  Jumbo Rolls
CREATE TABLE IF NOT EXISTS jumbo_rolls (
    id                  VARCHAR(36)     PRIMARY KEY DEFAULT gen_random_uuid()::text,
    batch_number        VARCHAR(100)    NOT NULL UNIQUE,
    coating_order_id    VARCHAR(36)     REFERENCES coating_orders(id),
    item_id             VARCHAR(36)     NOT NULL REFERENCES items(id),
    roll_width_mm       NUMERIC(10,4)   NOT NULL,
    roll_length_m       NUMERIC(14,4),
    thickness_microns   NUMERIC(10,4),
    gross_weight_kg     NUMERIC(14,4)   DEFAULT 0,
    core_weight_kg      NUMERIC(14,4)   DEFAULT 0,
    net_weight_kg       NUMERIC(14,4)   DEFAULT 0,
    sqm                 NUMERIC(14,4)   DEFAULT 0,
    status              VARCHAR(50)     DEFAULT 'in_stock',
    warehouse_id        VARCHAR(36)     REFERENCES warehouses(id),
    manufacture_date    TIMESTAMPTZ,
    expiry_date         TIMESTAMPTZ,
    qc_approved         BOOLEAN,
    qc_inspector_id     VARCHAR(36)     REFERENCES users(id),
    qc_params           JSONB,
    notes               TEXT,
    created_at          TIMESTAMPTZ     DEFAULT NOW(),
    updated_at          TIMESTAMPTZ     DEFAULT NOW(),
    created_by          VARCHAR(36),
    updated_by          VARCHAR(36)
);
CREATE INDEX IF NOT EXISTS ix_jumbo_status ON jumbo_rolls(status);

-- 3.6  Slitting Orders (Stage 2)
CREATE TABLE IF NOT EXISTS slitting_orders (
    id                      VARCHAR(36)     PRIMARY KEY DEFAULT gen_random_uuid()::text,
    so_number               VARCHAR(50)     NOT NULL UNIQUE,
    work_order_id           VARCHAR(36)     REFERENCES work_orders(id),
    machine_id              VARCHAR(36)     REFERENCES machines(id),
    planned_date            TIMESTAMPTZ     NOT NULL,
    status                  VARCHAR(50)     DEFAULT 'planned',
    input_jumbo_rolls       JSONB,          -- [{jumbo_roll_id, batch_number, qty_kg, sqm}]
    total_input_kg          NUMERIC(14,4)   DEFAULT 0,
    total_input_sqm         NUMERIC(14,4)   DEFAULT 0,
    target_item_id          VARCHAR(36)     REFERENCES items(id),
    target_variant_id       VARCHAR(36)     REFERENCES item_variants(id),
    target_width_mm         NUMERIC(10,4)   NOT NULL,
    target_length_m         NUMERIC(10,4)   NOT NULL,
    target_rolls            INTEGER,
    expected_output_kg      NUMERIC(14,4),
    expected_output_sqm     NUMERIC(14,4),
    actual_output_rolls     INTEGER         DEFAULT 0,
    actual_output_kg        NUMERIC(14,4)   DEFAULT 0,
    scrap_kg                NUMERIC(14,4)   DEFAULT 0,
    edge_trim_kg            NUMERIC(14,4)   DEFAULT 0,
    scrap_percent           NUMERIC(7,4)    DEFAULT 0,
    -- Redline Guard
    redline_triggered       BOOLEAN         DEFAULT FALSE,
    redline_override_by     VARCHAR(36)     REFERENCES users(id),
    redline_override_at     TIMESTAMPTZ,
    redline_override_reason TEXT,
    slitting_plan           JSONB,          -- [{lane, width_mm, rolls_count}]
    output_batch            VARCHAR(100),
    output_warehouse_id     VARCHAR(36)     REFERENCES warehouses(id),
    shift                   VARCHAR(20),
    operator_id             VARCHAR(36)     REFERENCES users(id),
    supervisor_id           VARCHAR(36)     REFERENCES users(id),
    qc_params               JSONB,
    notes                   TEXT,
    custom_fields           JSONB,
    created_at              TIMESTAMPTZ     DEFAULT NOW(),
    updated_at              TIMESTAMPTZ     DEFAULT NOW(),
    created_by              VARCHAR(36),
    updated_by              VARCHAR(36)
);
CREATE INDEX IF NOT EXISTS ix_slitting_status   ON slitting_orders(status);
CREATE INDEX IF NOT EXISTS ix_slitting_redline  ON slitting_orders(redline_triggered) WHERE redline_triggered = TRUE;

-- 3.7  Production Shift Logs
CREATE TABLE IF NOT EXISTS production_shift_logs (
    id              VARCHAR(36)     PRIMARY KEY DEFAULT gen_random_uuid()::text,
    shift_date      TIMESTAMPTZ     NOT NULL,
    shift           VARCHAR(20)     NOT NULL,
    machine_id      VARCHAR(36)     REFERENCES machines(id),
    stage           VARCHAR(50)     NOT NULL,
    reference_type  VARCHAR(50),
    reference_id    VARCHAR(36),
    operator_id     VARCHAR(36)     REFERENCES users(id),
    start_time      TIMESTAMPTZ,
    end_time        TIMESTAMPTZ,
    input_kg        NUMERIC(14,4)   DEFAULT 0,
    output_kg       NUMERIC(14,4)   DEFAULT 0,
    scrap_kg        NUMERIC(14,4)   DEFAULT 0,
    scrap_percent   NUMERIC(7,4)    DEFAULT 0,
    downtime_minutes INTEGER        DEFAULT 0,
    downtime_reason TEXT,
    redline_flag    BOOLEAN         DEFAULT FALSE,
    shift_params    JSONB,
    notes           TEXT,
    created_at      TIMESTAMPTZ     DEFAULT NOW(),
    updated_at      TIMESTAMPTZ     DEFAULT NOW(),
    created_by      VARCHAR(36),
    updated_by      VARCHAR(36)
);
CREATE INDEX IF NOT EXISTS ix_shift_log_date ON production_shift_logs(shift_date);

-- 3.8  Scrap Entries
CREATE TABLE IF NOT EXISTS scrap_entries (
    id                  VARCHAR(36)     PRIMARY KEY DEFAULT gen_random_uuid()::text,
    entry_number        VARCHAR(50)     NOT NULL UNIQUE,
    entry_date          TIMESTAMPTZ     DEFAULT NOW(),
    reference_type      VARCHAR(50),
    reference_id        VARCHAR(36),
    stage               VARCHAR(50),
    scrap_type          VARCHAR(100),
    scrap_kg            NUMERIC(14,4)   DEFAULT 0,
    scrap_sqm           NUMERIC(14,4)   DEFAULT 0,
    input_kg            NUMERIC(14,4)   DEFAULT 0,
    scrap_percent       NUMERIC(7,4)    DEFAULT 0,
    -- Redline Guard
    exceeds_threshold   BOOLEAN         DEFAULT FALSE,
    threshold_percent   NUMERIC(6,2)    DEFAULT 7.00,
    production_locked   BOOLEAN         DEFAULT FALSE,
    override_by         VARCHAR(36)     REFERENCES users(id),
    override_at         TIMESTAMPTZ,
    disposal_method     VARCHAR(100),
    disposal_value      NUMERIC(14,4)   DEFAULT 0,
    notes               TEXT,
    recorded_by         VARCHAR(36)     REFERENCES users(id),
    created_at          TIMESTAMPTZ     DEFAULT NOW(),
    updated_at          TIMESTAMPTZ     DEFAULT NOW(),
    created_by          VARCHAR(36),
    updated_by          VARCHAR(36)
);
CREATE INDEX IF NOT EXISTS ix_scrap_ref       ON scrap_entries(reference_type, reference_id);
CREATE INDEX IF NOT EXISTS ix_scrap_redline   ON scrap_entries(exceeds_threshold) WHERE exceeds_threshold = TRUE;


-- =============================================================================
-- SECTION 4: HRMS EXTENDED + FIXED ASSETS
-- =============================================================================

-- 4.1  Leave Balances
CREATE TABLE IF NOT EXISTS leave_balances (
    id              VARCHAR(36)     PRIMARY KEY DEFAULT gen_random_uuid()::text,
    employee_id     VARCHAR(36)     NOT NULL REFERENCES employees(id) ON DELETE CASCADE,
    leave_type_id   VARCHAR(36)     NOT NULL REFERENCES leave_types(id),
    fiscal_year     VARCHAR(10)     NOT NULL,
    opening_balance NUMERIC(8,2)    DEFAULT 0,
    entitlement     NUMERIC(8,2)    DEFAULT 0,
    taken           NUMERIC(8,2)    DEFAULT 0,
    encashed        NUMERIC(8,2)    DEFAULT 0,
    closing_balance NUMERIC(8,2)    DEFAULT 0,
    created_at      TIMESTAMPTZ     DEFAULT NOW(),
    updated_at      TIMESTAMPTZ     DEFAULT NOW(),
    created_by      VARCHAR(36),
    updated_by      VARCHAR(36),
    UNIQUE (employee_id, leave_type_id, fiscal_year)
);

-- 4.2  Leave Applications (enhanced workflow)
CREATE TABLE IF NOT EXISTS leave_applications (
    id                  VARCHAR(36)     PRIMARY KEY DEFAULT gen_random_uuid()::text,
    application_number  VARCHAR(50)     NOT NULL UNIQUE,
    employee_id         VARCHAR(36)     NOT NULL REFERENCES employees(id),
    leave_type_id       VARCHAR(36)     NOT NULL REFERENCES leave_types(id),
    from_date           TIMESTAMPTZ     NOT NULL,
    to_date             TIMESTAMPTZ     NOT NULL,
    total_days          NUMERIC(5,2)    NOT NULL,
    half_day            BOOLEAN         DEFAULT FALSE,
    reason              TEXT,
    status              VARCHAR(50)     DEFAULT 'pending',
    approver_id         VARCHAR(36)     REFERENCES users(id),
    approved_at         TIMESTAMPTZ,
    rejection_reason    TEXT,
    attachments         JSONB,
    created_at          TIMESTAMPTZ     DEFAULT NOW(),
    updated_at          TIMESTAMPTZ     DEFAULT NOW(),
    created_by          VARCHAR(36),
    updated_by          VARCHAR(36)
);
CREATE INDEX IF NOT EXISTS ix_leave_app_emp    ON leave_applications(employee_id);
CREATE INDEX IF NOT EXISTS ix_leave_app_status ON leave_applications(status);

-- 4.3  Shift Masters
CREATE TABLE IF NOT EXISTS shift_masters (
    id              VARCHAR(36)     PRIMARY KEY DEFAULT gen_random_uuid()::text,
    shift_code      VARCHAR(20)     NOT NULL UNIQUE,
    shift_name      VARCHAR(100)    NOT NULL,
    start_time      VARCHAR(10)     NOT NULL,
    end_time        VARCHAR(10)     NOT NULL,
    grace_minutes   INTEGER         DEFAULT 10,
    is_night_shift  BOOLEAN         DEFAULT FALSE,
    is_active       BOOLEAN         DEFAULT TRUE,
    created_at      TIMESTAMPTZ     DEFAULT NOW(),
    updated_at      TIMESTAMPTZ     DEFAULT NOW(),
    created_by      VARCHAR(36),
    updated_by      VARCHAR(36)
);

-- 4.4  Employee Shift Roster
CREATE TABLE IF NOT EXISTS employee_shift_rosters (
    id              VARCHAR(36)     PRIMARY KEY DEFAULT gen_random_uuid()::text,
    employee_id     VARCHAR(36)     NOT NULL REFERENCES employees(id),
    shift_id        VARCHAR(36)     NOT NULL REFERENCES shift_masters(id),
    effective_from  TIMESTAMPTZ     NOT NULL,
    effective_to    TIMESTAMPTZ,
    notes           TEXT,
    created_at      TIMESTAMPTZ     DEFAULT NOW(),
    updated_at      TIMESTAMPTZ     DEFAULT NOW(),
    created_by      VARCHAR(36),
    updated_by      VARCHAR(36)
);
CREATE INDEX IF NOT EXISTS ix_shift_roster_emp ON employee_shift_rosters(employee_id);

-- 4.5  Attendance Records
CREATE TABLE IF NOT EXISTS attendance_records (
    id                      VARCHAR(36)     PRIMARY KEY DEFAULT gen_random_uuid()::text,
    employee_id             VARCHAR(36)     NOT NULL REFERENCES employees(id),
    attendance_date         TIMESTAMPTZ     NOT NULL,
    shift_id                VARCHAR(36)     REFERENCES shift_masters(id),
    in_time                 TIMESTAMPTZ,
    out_time                TIMESTAMPTZ,
    working_hours           NUMERIC(6,2)    DEFAULT 0,
    overtime_hours          NUMERIC(6,2)    DEFAULT 0,
    status                  VARCHAR(50)     DEFAULT 'present',
    is_late                 BOOLEAN         DEFAULT FALSE,
    late_minutes            INTEGER         DEFAULT 0,
    early_exit_minutes      INTEGER         DEFAULT 0,
    leave_application_id    VARCHAR(36)     REFERENCES leave_applications(id),
    biometric_log_id        VARCHAR(100),
    entry_source            VARCHAR(20)     DEFAULT 'manual',
    notes                   TEXT,
    approved_by             VARCHAR(36)     REFERENCES users(id),
    created_at              TIMESTAMPTZ     DEFAULT NOW(),
    updated_at              TIMESTAMPTZ     DEFAULT NOW(),
    created_by              VARCHAR(36),
    updated_by              VARCHAR(36),
    UNIQUE (employee_id, attendance_date)
);
CREATE INDEX IF NOT EXISTS ix_att_rec_date ON attendance_records(attendance_date);

-- 4.6  Employee Salary Assignments
CREATE TABLE IF NOT EXISTS employee_salary_assignments (
    id                      VARCHAR(36)     PRIMARY KEY DEFAULT gen_random_uuid()::text,
    employee_id             VARCHAR(36)     NOT NULL REFERENCES employees(id),
    salary_structure_id     VARCHAR(36)     NOT NULL REFERENCES salary_structures(id),
    effective_from          TIMESTAMPTZ     NOT NULL,
    effective_to            TIMESTAMPTZ,
    ctc_annual              NUMERIC(14,4)   DEFAULT 0,
    basic_monthly           NUMERIC(14,4)   DEFAULT 0,
    gross_monthly           NUMERIC(14,4)   DEFAULT 0,
    component_overrides     JSONB,
    pf_employee_percent     NUMERIC(6,4)    DEFAULT 12.00,
    pf_employer_percent     NUMERIC(6,4)    DEFAULT 12.00,
    esi_employee_percent    NUMERIC(6,4)    DEFAULT 0.75,
    esi_employer_percent    NUMERIC(6,4)    DEFAULT 3.25,
    esi_applicable          BOOLEAN         DEFAULT TRUE,
    approved_by             VARCHAR(36)     REFERENCES users(id),
    notes                   TEXT,
    created_at              TIMESTAMPTZ     DEFAULT NOW(),
    updated_at              TIMESTAMPTZ     DEFAULT NOW(),
    created_by              VARCHAR(36),
    updated_by              VARCHAR(36)
);
CREATE INDEX IF NOT EXISTS ix_sal_assign_emp ON employee_salary_assignments(employee_id);

-- 4.7  Payroll Runs
CREATE TABLE IF NOT EXISTS payroll_runs (
    id                  VARCHAR(36)     PRIMARY KEY DEFAULT gen_random_uuid()::text,
    run_number          VARCHAR(50)     NOT NULL UNIQUE,
    payroll_month       VARCHAR(7)      NOT NULL,       -- "2024-03"
    fiscal_year         VARCHAR(10)     NOT NULL,
    branch_id           VARCHAR(36)     REFERENCES branches(id),
    status              VARCHAR(50)     DEFAULT 'draft',
    total_employees     INTEGER         DEFAULT 0,
    total_gross         NUMERIC(18,4)   DEFAULT 0,
    total_deductions    NUMERIC(18,4)   DEFAULT 0,
    total_net_pay       NUMERIC(18,4)   DEFAULT 0,
    total_pf_employee   NUMERIC(18,4)   DEFAULT 0,
    total_pf_employer   NUMERIC(18,4)   DEFAULT 0,
    total_esi_employee  NUMERIC(18,4)   DEFAULT 0,
    total_esi_employer  NUMERIC(18,4)   DEFAULT 0,
    total_tds           NUMERIC(18,4)   DEFAULT 0,
    processed_by        VARCHAR(36)     REFERENCES users(id),
    approved_by         VARCHAR(36)     REFERENCES users(id),
    approved_at         TIMESTAMPTZ,
    payment_date        TIMESTAMPTZ,
    payment_mode        VARCHAR(50),
    notes               TEXT,
    created_at          TIMESTAMPTZ     DEFAULT NOW(),
    updated_at          TIMESTAMPTZ     DEFAULT NOW(),
    created_by          VARCHAR(36),
    updated_by          VARCHAR(36)
);

-- 4.8  Payslip Entries
CREATE TABLE IF NOT EXISTS payslip_entries (
    id                  VARCHAR(36)     PRIMARY KEY DEFAULT gen_random_uuid()::text,
    payroll_run_id      VARCHAR(36)     NOT NULL REFERENCES payroll_runs(id),
    employee_id         VARCHAR(36)     NOT NULL REFERENCES employees(id),
    payroll_month       VARCHAR(7)      NOT NULL,
    working_days        NUMERIC(5,2)    DEFAULT 0,
    present_days        NUMERIC(5,2)    DEFAULT 0,
    absent_days         NUMERIC(5,2)    DEFAULT 0,
    leave_days          NUMERIC(5,2)    DEFAULT 0,
    overtime_hours      NUMERIC(6,2)    DEFAULT 0,
    -- Earnings
    basic               NUMERIC(14,4)   DEFAULT 0,
    hra                 NUMERIC(14,4)   DEFAULT 0,
    ta                  NUMERIC(14,4)   DEFAULT 0,
    special_allowance   NUMERIC(14,4)   DEFAULT 0,
    overtime_amount     NUMERIC(14,4)   DEFAULT 0,
    other_earnings      NUMERIC(14,4)   DEFAULT 0,
    gross_earnings      NUMERIC(14,4)   DEFAULT 0,
    -- Statutory deductions
    pf_employee         NUMERIC(14,4)   DEFAULT 0,
    esi_employee        NUMERIC(14,4)   DEFAULT 0,
    professional_tax    NUMERIC(14,4)   DEFAULT 0,
    tds                 NUMERIC(14,4)   DEFAULT 0,
    loan_emi            NUMERIC(14,4)   DEFAULT 0,
    advance_recovery    NUMERIC(14,4)   DEFAULT 0,
    other_deductions    NUMERIC(14,4)   DEFAULT 0,
    total_deductions    NUMERIC(14,4)   DEFAULT 0,
    -- Employer contributions
    pf_employer         NUMERIC(14,4)   DEFAULT 0,
    esi_employer        NUMERIC(14,4)   DEFAULT 0,
    net_pay             NUMERIC(14,4)   DEFAULT 0,
    -- Detail (for e-payslip)
    earnings_detail     JSONB,
    deductions_detail   JSONB,
    bank_account        VARCHAR(50),
    payment_status      VARCHAR(50)     DEFAULT 'pending',
    payment_reference   VARCHAR(100),
    paid_at             TIMESTAMPTZ,
    created_at          TIMESTAMPTZ     DEFAULT NOW(),
    updated_at          TIMESTAMPTZ     DEFAULT NOW(),
    created_by          VARCHAR(36),
    updated_by          VARCHAR(36),
    UNIQUE (payroll_run_id, employee_id)
);
CREATE INDEX IF NOT EXISTS ix_payslip_emp ON payslip_entries(employee_id);

-- 4.9  Employee Loans (extended)
CREATE TABLE IF NOT EXISTS employee_loans_ext (
    id                  VARCHAR(36)     PRIMARY KEY DEFAULT gen_random_uuid()::text,
    loan_number         VARCHAR(50)     NOT NULL UNIQUE,
    employee_id         VARCHAR(36)     NOT NULL REFERENCES employees(id),
    loan_type           VARCHAR(50)     DEFAULT 'advance',
    loan_amount         NUMERIC(14,4)   NOT NULL,
    outstanding_amount  NUMERIC(14,4)   DEFAULT 0,
    emi_amount          NUMERIC(14,4)   DEFAULT 0,
    disbursement_date   TIMESTAMPTZ,
    tenure_months       INTEGER         DEFAULT 1,
    status              VARCHAR(50)     DEFAULT 'active',
    approved_by         VARCHAR(36)     REFERENCES users(id),
    repayment_schedule  JSONB,
    notes               TEXT,
    created_at          TIMESTAMPTZ     DEFAULT NOW(),
    updated_at          TIMESTAMPTZ     DEFAULT NOW(),
    created_by          VARCHAR(36),
    updated_by          VARCHAR(36)
);

-- 4.10  Asset Categories
CREATE TABLE IF NOT EXISTS asset_categories (
    id                          VARCHAR(36)     PRIMARY KEY DEFAULT gen_random_uuid()::text,
    code                        VARCHAR(50)     NOT NULL UNIQUE,
    name                        VARCHAR(255)    NOT NULL,
    depreciation_method         VARCHAR(50)     DEFAULT 'straight_line',
    useful_life_years           NUMERIC(6,2)    DEFAULT 5,
    depreciation_rate_percent   NUMERIC(8,4),
    salvage_value_percent       NUMERIC(6,2)    DEFAULT 5,
    gl_account_id               VARCHAR(36)     REFERENCES chart_of_accounts(id),
    depreciation_account_id     VARCHAR(36)     REFERENCES chart_of_accounts(id),
    accumulated_dep_account_id  VARCHAR(36)     REFERENCES chart_of_accounts(id),
    is_active                   BOOLEAN         DEFAULT TRUE,
    notes                       TEXT,
    created_at                  TIMESTAMPTZ     DEFAULT NOW(),
    updated_at                  TIMESTAMPTZ     DEFAULT NOW(),
    created_by                  VARCHAR(36),
    updated_by                  VARCHAR(36)
);

-- 4.11  Fixed Assets
CREATE TABLE IF NOT EXISTS fixed_assets (
    id                          VARCHAR(36)     PRIMARY KEY DEFAULT gen_random_uuid()::text,
    asset_code                  VARCHAR(50)     NOT NULL UNIQUE,
    asset_name                  VARCHAR(255)    NOT NULL,
    asset_category_id           VARCHAR(36)     NOT NULL REFERENCES asset_categories(id),
    branch_id                   VARCHAR(36)     REFERENCES branches(id),
    cost_center_id              VARCHAR(36)     REFERENCES cost_centers(id),
    -- Acquisition
    purchase_date               TIMESTAMPTZ     NOT NULL,
    installation_date           TIMESTAMPTZ,
    purchase_invoice_id         VARCHAR(36)     REFERENCES invoices(id),
    supplier_id                 VARCHAR(36)     REFERENCES accounts(id),
    -- Cost
    gross_block                 NUMERIC(18,4)   NOT NULL,
    salvage_value               NUMERIC(18,4)   DEFAULT 0,
    depreciable_amount          NUMERIC(18,4)   DEFAULT 0,
    -- Depreciation
    is_depreciable              BOOLEAN         DEFAULT TRUE,
    depreciation_method         VARCHAR(50)     DEFAULT 'straight_line',
    -- SLM : annual_dep = (gross_block - salvage_value) / useful_life_years
    -- WDV : annual_dep = net_block × rate / 100
    useful_life_years           NUMERIC(6,2)    DEFAULT 5,
    depreciation_rate_percent   NUMERIC(8,4),
    accumulated_depreciation    NUMERIC(18,4)   DEFAULT 0,
    net_block                   NUMERIC(18,4)   DEFAULT 0,
    -- Status
    status                      VARCHAR(50)     DEFAULT 'active',
    disposal_date               TIMESTAMPTZ,
    disposal_value              NUMERIC(18,4),
    disposal_reason             TEXT,
    location                    VARCHAR(255),
    custodian_id                VARCHAR(36)     REFERENCES employees(id),
    -- Insurance
    insurance_policy            VARCHAR(100),
    insurance_expiry            TIMESTAMPTZ,
    insured_value               NUMERIC(18,4),
    notes                       TEXT,
    custom_fields               JSONB,
    created_at                  TIMESTAMPTZ     DEFAULT NOW(),
    updated_at                  TIMESTAMPTZ     DEFAULT NOW(),
    created_by                  VARCHAR(36),
    updated_by                  VARCHAR(36)
);
CREATE INDEX IF NOT EXISTS ix_fixed_asset_status ON fixed_assets(status);

-- 4.12  Asset Depreciation Entries
CREATE TABLE IF NOT EXISTS asset_depreciation_entries (
    id                  VARCHAR(36)     PRIMARY KEY DEFAULT gen_random_uuid()::text,
    asset_id            VARCHAR(36)     NOT NULL REFERENCES fixed_assets(id),
    fiscal_year         VARCHAR(10)     NOT NULL,
    fiscal_period       SMALLINT        NOT NULL,
    depreciation_date   TIMESTAMPTZ     NOT NULL,
    opening_net_block   NUMERIC(18,4)   DEFAULT 0,
    depreciation_amount NUMERIC(18,4)   DEFAULT 0,
    closing_net_block   NUMERIC(18,4)   DEFAULT 0,
    method_used         VARCHAR(50),
    gl_entry_id         VARCHAR(36)     REFERENCES general_ledger(id),
    journal_entry_id    VARCHAR(36)     REFERENCES journal_entries(id),
    is_posted           BOOLEAN         DEFAULT FALSE,
    posted_by           VARCHAR(36)     REFERENCES users(id),
    created_at          TIMESTAMPTZ     DEFAULT NOW(),
    updated_at          TIMESTAMPTZ     DEFAULT NOW(),
    created_by          VARCHAR(36),
    updated_by          VARCHAR(36),
    UNIQUE (asset_id, fiscal_year, fiscal_period)
);


-- =============================================================================
-- SECTION 5: FULL PROCUREMENT CHAIN
-- =============================================================================

-- 5.1  Purchase Indents
CREATE TABLE IF NOT EXISTS purchase_indents (
    id              VARCHAR(36)     PRIMARY KEY DEFAULT gen_random_uuid()::text,
    indent_number   VARCHAR(50)     NOT NULL UNIQUE,
    indent_date     TIMESTAMPTZ     DEFAULT NOW(),
    requested_by    VARCHAR(36)     REFERENCES users(id),
    department      VARCHAR(100),
    branch_id       VARCHAR(36)     REFERENCES branches(id),
    cost_center_id  VARCHAR(36)     REFERENCES cost_centers(id),
    warehouse_id    VARCHAR(36)     REFERENCES warehouses(id),
    required_date   TIMESTAMPTZ,
    priority        VARCHAR(20)     DEFAULT 'normal',
    items           JSONB,
    -- [{item_id, item_name, qty, uom, purpose, available_stock, remarks}]
    status          VARCHAR(50)     DEFAULT 'pending',
    approved_by     VARCHAR(36)     REFERENCES users(id),
    approved_at     TIMESTAMPTZ,
    rejection_reason TEXT,
    work_order_id   VARCHAR(36)     REFERENCES work_orders(id),
    notes           TEXT,
    custom_fields   JSONB,
    created_at      TIMESTAMPTZ     DEFAULT NOW(),
    updated_at      TIMESTAMPTZ     DEFAULT NOW(),
    created_by      VARCHAR(36),
    updated_by      VARCHAR(36)
);
CREATE INDEX IF NOT EXISTS ix_indent_status ON purchase_indents(status);

-- 5.2  Purchase Enquiries
CREATE TABLE IF NOT EXISTS purchase_enquiries (
    id                  VARCHAR(36)     PRIMARY KEY DEFAULT gen_random_uuid()::text,
    enquiry_number      VARCHAR(50)     NOT NULL UNIQUE,
    enquiry_date        TIMESTAMPTZ     DEFAULT NOW(),
    indent_id           VARCHAR(36)     REFERENCES purchase_indents(id),
    branch_id           VARCHAR(36)     REFERENCES branches(id),
    items               JSONB,
    vendors             JSONB,          -- [{account_id, vendor_name, email, sent_at, status}]
    response_due_date   TIMESTAMPTZ,
    status              VARCHAR(50)     DEFAULT 'sent',
    created_by          VARCHAR(36)     REFERENCES users(id),
    notes               TEXT,
    created_at          TIMESTAMPTZ     DEFAULT NOW(),
    updated_at          TIMESTAMPTZ     DEFAULT NOW(),
    updated_by          VARCHAR(36)
);

-- 5.3  Vendor Quotations
CREATE TABLE IF NOT EXISTS vendor_quotations (
    id              VARCHAR(36)     PRIMARY KEY DEFAULT gen_random_uuid()::text,
    quotation_number VARCHAR(50)    NOT NULL UNIQUE,
    enquiry_id      VARCHAR(36)     REFERENCES purchase_enquiries(id),
    vendor_id       VARCHAR(36)     NOT NULL REFERENCES accounts(id),
    quote_date      TIMESTAMPTZ     DEFAULT NOW(),
    valid_until     TIMESTAMPTZ,
    items           JSONB,
    subtotal        NUMERIC(18,4)   DEFAULT 0,
    tax_amount      NUMERIC(18,4)   DEFAULT 0,
    freight         NUMERIC(18,4)   DEFAULT 0,
    grand_total     NUMERIC(18,4)   DEFAULT 0,
    delivery_days   INTEGER,
    payment_terms   VARCHAR(255),
    status          VARCHAR(50)     DEFAULT 'received',
    is_selected     BOOLEAN         DEFAULT FALSE,
    selection_reason TEXT,
    attachments     JSONB,
    notes           TEXT,
    created_at      TIMESTAMPTZ     DEFAULT NOW(),
    updated_at      TIMESTAMPTZ     DEFAULT NOW(),
    created_by      VARCHAR(36),
    updated_by      VARCHAR(36)
);
CREATE INDEX IF NOT EXISTS ix_vq_enquiry ON vendor_quotations(enquiry_id);
CREATE INDEX IF NOT EXISTS ix_vq_vendor  ON vendor_quotations(vendor_id);

-- 5.4  Goods Received Notes
CREATE TABLE IF NOT EXISTS goods_received_notes (
    id                      VARCHAR(36)     PRIMARY KEY DEFAULT gen_random_uuid()::text,
    grn_number              VARCHAR(50)     NOT NULL UNIQUE,
    grn_date                TIMESTAMPTZ     DEFAULT NOW(),
    po_id                   VARCHAR(36)     REFERENCES purchase_orders(id),
    vendor_id               VARCHAR(36)     NOT NULL REFERENCES accounts(id),
    warehouse_id            VARCHAR(36)     NOT NULL REFERENCES warehouses(id),
    branch_id               VARCHAR(36)     REFERENCES branches(id),
    vendor_invoice_number   VARCHAR(100),
    lr_number               VARCHAR(100),
    lr_date                 TIMESTAMPTZ,
    vehicle_number          VARCHAR(50),
    transporter             VARCHAR(255),
    items                   JSONB,
    total_received_qty      NUMERIC(14,4)   DEFAULT 0,
    total_accepted_qty      NUMERIC(14,4)   DEFAULT 0,
    total_rejected_qty      NUMERIC(14,4)   DEFAULT 0,
    subtotal                NUMERIC(18,4)   DEFAULT 0,
    tax_amount              NUMERIC(18,4)   DEFAULT 0,
    grand_total             NUMERIC(18,4)   DEFAULT 0,
    status                  VARCHAR(50)     DEFAULT 'pending_qc',
    received_by             VARCHAR(36)     REFERENCES users(id),
    qc_done_by              VARCHAR(36)     REFERENCES users(id),
    qc_done_at              TIMESTAMPTZ,
    stock_ledger_created    BOOLEAN         DEFAULT FALSE,
    attachments             JSONB,
    notes                   TEXT,
    custom_fields           JSONB,
    created_at              TIMESTAMPTZ     DEFAULT NOW(),
    updated_at              TIMESTAMPTZ     DEFAULT NOW(),
    created_by              VARCHAR(36),
    updated_by              VARCHAR(36)
);
CREATE INDEX IF NOT EXISTS ix_grn_status ON goods_received_notes(status);
CREATE INDEX IF NOT EXISTS ix_grn_po     ON goods_received_notes(po_id);
CREATE INDEX IF NOT EXISTS ix_grn_vendor ON goods_received_notes(vendor_id);

-- 5.5  Purchase Invoices (Accounts Payable)
CREATE TABLE IF NOT EXISTS purchase_invoices (
    id                      VARCHAR(36)     PRIMARY KEY DEFAULT gen_random_uuid()::text,
    invoice_number          VARCHAR(50)     NOT NULL UNIQUE,
    vendor_invoice_number   VARCHAR(100),
    invoice_date            TIMESTAMPTZ     DEFAULT NOW(),
    due_date                TIMESTAMPTZ,
    vendor_id               VARCHAR(36)     NOT NULL REFERENCES accounts(id),
    grn_id                  VARCHAR(36)     REFERENCES goods_received_notes(id),
    po_id                   VARCHAR(36)     REFERENCES purchase_orders(id),
    branch_id               VARCHAR(36)     REFERENCES branches(id),
    cost_center_id          VARCHAR(36)     REFERENCES cost_centers(id),
    invoice_type            VARCHAR(50)     DEFAULT 'goods',
    items                   JSONB,
    -- GST
    subtotal                NUMERIC(18,4)   DEFAULT 0,
    cgst_amount             NUMERIC(18,4)   DEFAULT 0,
    sgst_amount             NUMERIC(18,4)   DEFAULT 0,
    igst_amount             NUMERIC(18,4)   DEFAULT 0,
    cess_amount             NUMERIC(18,4)   DEFAULT 0,
    tax_amount              NUMERIC(18,4)   DEFAULT 0,
    place_of_supply         VARCHAR(100),
    reverse_charge          BOOLEAN         DEFAULT FALSE,
    -- TDS
    tds_applicable          BOOLEAN         DEFAULT FALSE,
    tds_section             VARCHAR(20),
    tds_rate_percent        NUMERIC(6,4)    DEFAULT 0,
    tds_amount              NUMERIC(18,4)   DEFAULT 0,
    grand_total             NUMERIC(18,4)   DEFAULT 0,
    paid_amount             NUMERIC(18,4)   DEFAULT 0,
    balance_amount          NUMERIC(18,4)   DEFAULT 0,
    status                  VARCHAR(50)     DEFAULT 'pending_approval',
    -- Maker-Approver
    maker_id                VARCHAR(36)     REFERENCES users(id),
    approver_id             VARCHAR(36)     REFERENCES users(id),
    approved_at             TIMESTAMPTZ,
    gl_posted               BOOLEAN         DEFAULT FALSE,
    gl_posted_at            TIMESTAMPTZ,
    attachments             JSONB,
    notes                   TEXT,
    internal_notes          TEXT,
    custom_fields           JSONB,
    created_at              TIMESTAMPTZ     DEFAULT NOW(),
    updated_at              TIMESTAMPTZ     DEFAULT NOW(),
    created_by              VARCHAR(36),
    updated_by              VARCHAR(36)
);
CREATE INDEX IF NOT EXISTS ix_pinv_status ON purchase_invoices(status);
CREATE INDEX IF NOT EXISTS ix_pinv_vendor ON purchase_invoices(vendor_id);
CREATE INDEX IF NOT EXISTS ix_pinv_date   ON purchase_invoices(invoice_date);

-- 5.6  Landed Cost Vouchers
CREATE TABLE IF NOT EXISTS landed_cost_vouchers (
    id                      VARCHAR(36)     PRIMARY KEY DEFAULT gen_random_uuid()::text,
    lcv_number              VARCHAR(50)     NOT NULL UNIQUE,
    lcv_date                TIMESTAMPTZ     DEFAULT NOW(),
    grn_ids                 JSONB,
    vendor_id               VARCHAR(36)     REFERENCES accounts(id),
    cost_components         JSONB,          -- [{component, amount, account_id}]
    total_landed_cost       NUMERIC(18,4)   DEFAULT 0,
    distribution_method     VARCHAR(50)     DEFAULT 'by_value',
    item_allocations        JSONB,          -- [{grn_id, item_id, base_amount, allocated_cost, new_cost_rate}]
    status                  VARCHAR(50)     DEFAULT 'draft',
    posted_by               VARCHAR(36)     REFERENCES users(id),
    posted_at               TIMESTAMPTZ,
    notes                   TEXT,
    created_at              TIMESTAMPTZ     DEFAULT NOW(),
    updated_at              TIMESTAMPTZ     DEFAULT NOW(),
    created_by              VARCHAR(36),
    updated_by              VARCHAR(36)
);


-- =============================================================================
-- SECTION 6: AI AGENT LAYER
-- =============================================================================

-- 6.1  AI Agent Registry
CREATE TABLE IF NOT EXISTS ai_agents (
    id              VARCHAR(36)     PRIMARY KEY DEFAULT gen_random_uuid()::text,
    agent_code      VARCHAR(50)     NOT NULL UNIQUE,
    agent_name      VARCHAR(255)    NOT NULL,
    agent_type      VARCHAR(50)     NOT NULL,
    description     TEXT,
    schedule_cron   VARCHAR(100),
    is_enabled      BOOLEAN         DEFAULT TRUE,
    last_run_at     TIMESTAMPTZ,
    next_run_at     TIMESTAMPTZ,
    config          JSONB,          -- model, thresholds, escalation rules
    total_runs      INTEGER         DEFAULT 0,
    successful_runs INTEGER         DEFAULT 0,
    failed_runs     INTEGER         DEFAULT 0,
    notes           TEXT,
    created_at      TIMESTAMPTZ     DEFAULT NOW(),
    updated_at      TIMESTAMPTZ     DEFAULT NOW(),
    created_by      VARCHAR(36),
    updated_by      VARCHAR(36)
);

-- 6.2  Agent Run Logs
CREATE TABLE IF NOT EXISTS agent_run_logs (
    id                  VARCHAR(36)     PRIMARY KEY DEFAULT gen_random_uuid()::text,
    agent_id            VARCHAR(36)     NOT NULL REFERENCES ai_agents(id),
    agent_code          VARCHAR(50)     NOT NULL,
    run_at              TIMESTAMPTZ     DEFAULT NOW(),
    trigger_type        VARCHAR(50)     DEFAULT 'schedule',
    status              VARCHAR(50)     DEFAULT 'running',
    duration_seconds    NUMERIC(10,3),
    records_processed   INTEGER         DEFAULT 0,
    actions_taken       INTEGER         DEFAULT 0,
    summary             JSONB,
    error_details       TEXT,
    llm_tokens_used     INTEGER,
    llm_cost_usd        NUMERIC(10,6),
    created_at          TIMESTAMPTZ     DEFAULT NOW(),
    updated_at          TIMESTAMPTZ     DEFAULT NOW(),
    created_by          VARCHAR(36),
    updated_by          VARCHAR(36)
);
CREATE INDEX IF NOT EXISTS ix_agent_run_agent_date ON agent_run_logs(agent_id, run_at DESC);

-- 6.3  Task Escalations (iSTIX Enforcer output)
CREATE TABLE IF NOT EXISTS task_escalations (
    id                      VARCHAR(36)     PRIMARY KEY DEFAULT gen_random_uuid()::text,
    task_type               VARCHAR(100)    NOT NULL,
    task_id                 VARCHAR(36)     NOT NULL,
    task_reference          VARCHAR(100),
    original_assignee_id    VARCHAR(36)     REFERENCES users(id),
    escalated_to_id         VARCHAR(36)     NOT NULL REFERENCES users(id),
    escalation_level        SMALLINT        DEFAULT 1,
    overdue_since           TIMESTAMPTZ     NOT NULL,
    hours_overdue           NUMERIC(8,2)    DEFAULT 0,
    due_date                TIMESTAMPTZ,
    escalation_message      TEXT,
    channel                 VARCHAR(50)     DEFAULT 'email',
    status                  VARCHAR(50)     DEFAULT 'sent',
    acknowledged_at         TIMESTAMPTZ,
    resolved_at             TIMESTAMPTZ,
    agent_run_id            VARCHAR(36)     REFERENCES agent_run_logs(id),
    created_at              TIMESTAMPTZ     DEFAULT NOW(),
    updated_at              TIMESTAMPTZ     DEFAULT NOW(),
    created_by              VARCHAR(36),
    updated_by              VARCHAR(36)
);
CREATE INDEX IF NOT EXISTS ix_escalation_task   ON task_escalations(task_type, task_id);
CREATE INDEX IF NOT EXISTS ix_escalation_status ON task_escalations(status);

-- 6.4  Buying DNA Profiles
CREATE TABLE IF NOT EXISTS buying_dna_profiles (
    id                      VARCHAR(36)     PRIMARY KEY DEFAULT gen_random_uuid()::text,
    item_id                 VARCHAR(36)     NOT NULL REFERENCES items(id),
    vendor_id               VARCHAR(36)     REFERENCES accounts(id),
    avg_cycle_days          NUMERIC(10,4),
    min_cycle_days          NUMERIC(10,4),
    max_cycle_days          NUMERIC(10,4),
    total_orders            INTEGER         DEFAULT 0,
    last_order_date         TIMESTAMPTZ,
    last_order_qty          NUMERIC(14,4),
    last_order_rate         NUMERIC(14,4),
    -- urgency = days_since_last_order / avg_cycle_days
    urgency_score           NUMERIC(10,6)   DEFAULT 0,
    urgency_updated_at      TIMESTAMPTZ,
    predicted_reorder_date  TIMESTAMPTZ,
    recommended_qty         NUMERIC(14,4),
    recommended_vendor_id   VARCHAR(36)     REFERENCES accounts(id),
    price_history           JSONB,          -- [{date, rate, vendor_id}]
    reorder_alert_sent      BOOLEAN         DEFAULT FALSE,
    reorder_alert_sent_at   TIMESTAMPTZ,
    dna_insights            JSONB,
    created_at              TIMESTAMPTZ     DEFAULT NOW(),
    updated_at              TIMESTAMPTZ     DEFAULT NOW(),
    created_by              VARCHAR(36),
    updated_by              VARCHAR(36),
    UNIQUE (item_id, vendor_id)
);
CREATE INDEX IF NOT EXISTS ix_dna_urgency ON buying_dna_profiles(urgency_score DESC);

-- 6.5  Reorder Alerts
CREATE TABLE IF NOT EXISTS reorder_alerts (
    id                  VARCHAR(36)     PRIMARY KEY DEFAULT gen_random_uuid()::text,
    item_id             VARCHAR(36)     NOT NULL REFERENCES items(id),
    vendor_id           VARCHAR(36)     REFERENCES accounts(id),
    dna_profile_id      VARCHAR(36)     REFERENCES buying_dna_profiles(id),
    alert_date          TIMESTAMPTZ     DEFAULT NOW(),
    urgency_score       NUMERIC(10,6)   DEFAULT 0,
    recommended_qty     NUMERIC(14,4)   DEFAULT 0,
    uom                 VARCHAR(50),
    estimated_rate      NUMERIC(14,4),
    alert_message       TEXT,
    status              VARCHAR(50)     DEFAULT 'pending',
    acknowledged_by     VARCHAR(36)     REFERENCES users(id),
    acknowledged_at     TIMESTAMPTZ,
    indent_id           VARCHAR(36)     REFERENCES purchase_indents(id),
    agent_run_id        VARCHAR(36)     REFERENCES agent_run_logs(id),
    created_at          TIMESTAMPTZ     DEFAULT NOW(),
    updated_at          TIMESTAMPTZ     DEFAULT NOW(),
    created_by          VARCHAR(36),
    updated_by          VARCHAR(36)
);
CREATE INDEX IF NOT EXISTS ix_reorder_item   ON reorder_alerts(item_id);
CREATE INDEX IF NOT EXISTS ix_reorder_status ON reorder_alerts(status);

-- 6.6  Document Captures (Document IO Agent)
CREATE TABLE IF NOT EXISTS document_captures (
    id                      VARCHAR(36)     PRIMARY KEY DEFAULT gen_random_uuid()::text,
    capture_number          VARCHAR(50)     NOT NULL UNIQUE,
    capture_date            TIMESTAMPTZ     DEFAULT NOW(),
    source                  VARCHAR(50),
    document_type           VARCHAR(100),
    file_name               VARCHAR(255),
    file_path               VARCHAR(500),
    file_size_kb            INTEGER,
    mime_type               VARCHAR(100),
    sender_email            VARCHAR(255),
    sender_name             VARCHAR(255),
    email_subject           VARCHAR(500),
    extraction_status       VARCHAR(50)     DEFAULT 'pending',
    extracted_data          JSONB,          -- {vendor_name, invoice_number, date, items, total, ...}
    extraction_confidence   NUMERIC(5,4),
    ocr_raw_text            TEXT,
    linked_to_type          VARCHAR(100),
    linked_to_id            VARCHAR(36),
    matched_vendor_id       VARCHAR(36)     REFERENCES accounts(id),
    match_confidence        NUMERIC(5,4),
    reviewed_by             VARCHAR(36)     REFERENCES users(id),
    reviewed_at             TIMESTAMPTZ,
    review_notes            TEXT,
    agent_run_id            VARCHAR(36)     REFERENCES agent_run_logs(id),
    created_at              TIMESTAMPTZ     DEFAULT NOW(),
    updated_at              TIMESTAMPTZ     DEFAULT NOW(),
    created_by              VARCHAR(36),
    updated_by              VARCHAR(36)
);
CREATE INDEX IF NOT EXISTS ix_doc_cap_status ON document_captures(extraction_status);
CREATE INDEX IF NOT EXISTS ix_doc_cap_type   ON document_captures(document_type);

-- 6.7  AI Insights (Dashboard Cache)
CREATE TABLE IF NOT EXISTS ai_insights (
    id                  VARCHAR(36)     PRIMARY KEY DEFAULT gen_random_uuid()::text,
    insight_type        VARCHAR(100)    NOT NULL,
    scope_entity_type   VARCHAR(50),
    scope_entity_id     VARCHAR(36),
    title               VARCHAR(500),
    summary             TEXT,
    insight_data        JSONB,          -- charts, tables, KPIs
    recommendations     JSONB,          -- [{action, priority, impact}]
    severity            VARCHAR(20)     DEFAULT 'info',
    generated_at        TIMESTAMPTZ     DEFAULT NOW(),
    expired_at          TIMESTAMPTZ,
    is_valid            BOOLEAN         DEFAULT TRUE,
    agent_id            VARCHAR(36)     REFERENCES ai_agents(id),
    agent_run_id        VARCHAR(36)     REFERENCES agent_run_logs(id),
    created_at          TIMESTAMPTZ     DEFAULT NOW(),
    updated_at          TIMESTAMPTZ     DEFAULT NOW(),
    created_by          VARCHAR(36),
    updated_by          VARCHAR(36)
);
CREATE INDEX IF NOT EXISTS ix_insight_type_scope ON ai_insights(insight_type, scope_entity_type, scope_entity_id);
CREATE INDEX IF NOT EXISTS ix_insight_valid      ON ai_insights(is_valid, expired_at) WHERE is_valid = TRUE;


-- =============================================================================
-- SECTION 7: SEED DATA
-- =============================================================================

-- Fiscal Year 2024-25
INSERT INTO fiscal_years (id, name, start_date, end_date, is_active)
VALUES (gen_random_uuid()::text, '2024-25', '2024-04-01 00:00:00+00', '2025-03-31 23:59:59+00', TRUE)
ON CONFLICT (name) DO NOTHING;

-- AI Agents seed
INSERT INTO ai_agents (id, agent_code, agent_name, agent_type, schedule_cron, config)
VALUES
  (gen_random_uuid()::text, 'ISTIX_ENFORCER', 'iSTIX Enforcer',
   'enforcer', '0 */4 * * *',
   '{"escalation_levels": [
       {"level": 1, "hours_threshold": 4,  "notify_role": "manager"},
       {"level": 2, "hours_threshold": 8,  "notify_role": "director"},
       {"level": 3, "hours_threshold": 24, "notify_role": "ceo"}
     ],
     "channels": ["email", "whatsapp", "in_app"]}'::jsonb),
  (gen_random_uuid()::text, 'BUYING_DNA', 'Buying DNA Analyzer',
   'buying_dna', '0 6 * * *',
   '{"urgency_threshold": 1.0,
     "alert_channels": ["email", "in_app"],
     "cycle_lookback_days": 365}'::jsonb),
  (gen_random_uuid()::text, 'DOC_IO', 'Document IO Agent',
   'document_io', '*/30 * * * *',
   '{"sources": ["email", "whatsapp", "upload"],
     "ocr_engine": "google_vision",
     "llm_model": "claude-sonnet-4-6",
     "confidence_threshold": 0.80}'::jsonb)
ON CONFLICT (agent_code) DO NOTHING;

-- Default Shift Masters
INSERT INTO shift_masters (id, shift_code, shift_name, start_time, end_time, grace_minutes, is_night_shift)
VALUES
  (gen_random_uuid()::text, 'MORN', 'Morning Shift', '06:00', '14:00', 10, FALSE),
  (gen_random_uuid()::text, 'EVE',  'Evening Shift', '14:00', '22:00', 10, FALSE),
  (gen_random_uuid()::text, 'NITE', 'Night Shift',   '22:00', '06:00', 10, TRUE),
  (gen_random_uuid()::text, 'GEN',  'General Shift', '09:00', '18:00', 15, FALSE)
ON CONFLICT (shift_code) DO NOTHING;

-- Default Product Lines
INSERT INTO product_lines (id, code, name)
VALUES
  (gen_random_uuid()::text, 'BOPP-TAPE',    'BOPP Adhesive Tape'),
  (gen_random_uuid()::text, 'MASKING',      'Masking Tape'),
  (gen_random_uuid()::text, 'FOAM-TAPE',    'Foam Tape'),
  (gen_random_uuid()::text, 'DOUBLE-SIDED', 'Double-Sided Tape'),
  (gen_random_uuid()::text, 'SPECIALTY',    'Specialty Tapes')
ON CONFLICT (code) DO NOTHING;

-- Default Cost Centers
INSERT INTO cost_centers (id, code, name, is_group)
VALUES
  (gen_random_uuid()::text, 'HO',      'Head Office',         FALSE),
  (gen_random_uuid()::text, 'BWD-PLT', 'BWD Plant',           FALSE),
  (gen_random_uuid()::text, 'SGM-PLT', 'SGM Plant',           FALSE),
  (gen_random_uuid()::text, 'SALES',   'Sales Department',    FALSE),
  (gen_random_uuid()::text, 'ADMIN',   'Administration',      FALSE)
ON CONFLICT (code) DO NOTHING;

-- Redline Guard parameter note (informational)
COMMENT ON COLUMN coating_orders.redline_triggered IS
  'Set TRUE when scrap_percent > 7.0%. Locks production until Director override.';
COMMENT ON COLUMN slitting_orders.redline_triggered IS
  'Set TRUE when (scrap_kg + edge_trim_kg) / total_input_kg × 100 > 7.0%.';
COMMENT ON COLUMN item_variants.variant_code IS
  'Auto-generated: sku_template.sku_code + "-" + width_mm + "x" + length_m. Width/Length NOT in base SKU.';

-- =============================================================================
-- END OF MIGRATION 001
-- =============================================================================
