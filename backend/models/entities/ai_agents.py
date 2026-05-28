"""
SQLAlchemy Entity Models - AI Agent Layer
Tracking tables for three core agents + supporting infrastructure:

  1. iSTIX Enforcer  – polls tasks every 4 h; escalates overdue to CEO
  2. Buying DNA      – purchase-cycle analysis; urgency = days_since / avg_cycle
  3. Document IO     – OCR capture of vendor invoices / LRs from email/WhatsApp

Supporting tables:
  - AIAgent registry with schedule and config
  - AgentRunLog (full audit trail)
  - ReorderAlert (Buying DNA output)
  - DocumentCapture (Document IO output)
  - AIInsight (cached dashboard insights with TTL)
"""
from sqlalchemy import String, DateTime, Boolean, Text, Integer, Float, ForeignKey, UniqueConstraint, Index
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime, timezone

from core.database import Base
from models.entities.base import UUIDMixin, TimestampMixin


# ==================== AGENT REGISTRY ====================

class AIAgent(Base, UUIDMixin, TimestampMixin):
    """Registry of all AI agents with their schedules and configuration"""
    __tablename__ = "ai_agents"

    agent_code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    agent_name: Mapped[str] = mapped_column(String(255), nullable=False)
    agent_type: Mapped[str] = mapped_column(String(50), nullable=False)
    # enforcer | buying_dna | document_io | forecasting | custom

    description: Mapped[str] = mapped_column(Text, nullable=True)
    schedule_cron: Mapped[str] = mapped_column(String(100), nullable=True)
    # "0 */4 * * *" = every 4 hours (iSTIX Enforcer)

    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    last_run_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    next_run_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)

    # Model, thresholds, escalation rules, API keys stored here
    config: Mapped[dict] = mapped_column(JSONB, nullable=True)

    total_runs: Mapped[int] = mapped_column(Integer, default=0)
    successful_runs: Mapped[int] = mapped_column(Integer, default=0)
    failed_runs: Mapped[int] = mapped_column(Integer, default=0)

    notes: Mapped[str] = mapped_column(Text, nullable=True)


class AgentRunLog(Base, UUIDMixin, TimestampMixin):
    """Full audit trail for every AI agent execution"""
    __tablename__ = "agent_run_logs"

    agent_id: Mapped[str] = mapped_column(String(36), ForeignKey("ai_agents.id"), nullable=False, index=True)
    agent_code: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    run_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True
    )
    trigger_type: Mapped[str] = mapped_column(String(50), default="schedule")   # schedule | manual | event

    status: Mapped[str] = mapped_column(String(50), default="running", index=True)
    # running | success | failed | partial

    duration_seconds: Mapped[float] = mapped_column(Float, nullable=True)
    records_processed: Mapped[int] = mapped_column(Integer, default=0)
    actions_taken: Mapped[int] = mapped_column(Integer, default=0)

    summary: Mapped[dict] = mapped_column(JSONB, nullable=True)
    error_details: Mapped[str] = mapped_column(Text, nullable=True)

    # LLM cost tracking (Claude / OpenAI calls)
    llm_tokens_used: Mapped[int] = mapped_column(Integer, nullable=True)
    llm_cost_usd: Mapped[float] = mapped_column(Float, nullable=True)

    __table_args__ = (
        Index("ix_agent_run_date", "agent_id", "run_at"),
    )


# ==================== iSTIX ENFORCER ====================

class TaskEscalation(Base, UUIDMixin, TimestampMixin):
    """
    iSTIX Enforcer output – one row per overdue task escalation.
    Escalation chain (configurable, default):
      level 1 (≥4h overdue)  → direct manager
      level 2 (≥8h overdue)  → department director
      level 3 (≥24h overdue) → CEO
    """
    __tablename__ = "task_escalations"

    task_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    # work_order | purchase_indent | leave_application | approval_workflow | custom
    task_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    task_reference: Mapped[str] = mapped_column(String(100), nullable=True)    # document number

    original_assignee_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    escalated_to_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)
    escalation_level: Mapped[int] = mapped_column(Integer, default=1)   # 1=manager | 2=director | 3=CEO

    overdue_since: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    hours_overdue: Mapped[float] = mapped_column(Float, default=0)
    due_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)

    escalation_message: Mapped[str] = mapped_column(Text, nullable=True)
    channel: Mapped[str] = mapped_column(String(50), default="email")   # email | whatsapp | in_app

    status: Mapped[str] = mapped_column(String(50), default="sent", index=True)
    # sent | acknowledged | resolved | auto_closed

    acknowledged_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    resolved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    agent_run_id: Mapped[str] = mapped_column(String(36), ForeignKey("agent_run_logs.id"), nullable=True)

    __table_args__ = (
        Index("ix_escalation_task", "task_type", "task_id"),
    )


# ==================== BUYING DNA ====================

class BuyingDNAProfile(Base, UUIDMixin, TimestampMixin):
    """
    Per-item / per-vendor purchase cycle DNA.
    The Buying DNA agent refreshes this after each purchase event.

    urgency_score = days_since_last_order / avg_cycle_days
    ≥ 1.0 → reorder is overdue; trigger ReorderAlert
    """
    __tablename__ = "buying_dna_profiles"

    item_id: Mapped[str] = mapped_column(String(36), ForeignKey("items.id"), nullable=False, index=True)
    vendor_id: Mapped[str] = mapped_column(String(36), ForeignKey("accounts.id"), nullable=True, index=True)

    # Purchase-cycle statistics (updated incrementally)
    avg_cycle_days: Mapped[float] = mapped_column(Float, nullable=True)
    min_cycle_days: Mapped[float] = mapped_column(Float, nullable=True)
    max_cycle_days: Mapped[float] = mapped_column(Float, nullable=True)
    total_orders: Mapped[int] = mapped_column(Integer, default=0)

    last_order_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    last_order_qty: Mapped[float] = mapped_column(Float, nullable=True)
    last_order_rate: Mapped[float] = mapped_column(Float, nullable=True)

    # Core urgency formula
    urgency_score: Mapped[float] = mapped_column(Float, default=0)
    urgency_updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)

    predicted_reorder_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    recommended_qty: Mapped[float] = mapped_column(Float, nullable=True)
    recommended_vendor_id: Mapped[str] = mapped_column(String(36), ForeignKey("accounts.id"), nullable=True)

    # [{date, rate, vendor_id}] – price trend for supplier negotiation
    price_history: Mapped[list] = mapped_column(JSONB, nullable=True)

    reorder_alert_sent: Mapped[bool] = mapped_column(Boolean, default=False)
    reorder_alert_sent_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)

    dna_insights: Mapped[dict] = mapped_column(JSONB, nullable=True)

    __table_args__ = (
        UniqueConstraint("item_id", "vendor_id", name="uq_buying_dna_item_vendor"),
    )


class ReorderAlert(Base, UUIDMixin, TimestampMixin):
    """Reorder alert emitted by the Buying DNA agent"""
    __tablename__ = "reorder_alerts"

    item_id: Mapped[str] = mapped_column(String(36), ForeignKey("items.id"), nullable=False, index=True)
    vendor_id: Mapped[str] = mapped_column(String(36), ForeignKey("accounts.id"), nullable=True)
    dna_profile_id: Mapped[str] = mapped_column(String(36), ForeignKey("buying_dna_profiles.id"), nullable=True)

    alert_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    urgency_score: Mapped[float] = mapped_column(Float, default=0)
    recommended_qty: Mapped[float] = mapped_column(Float, default=0)
    uom: Mapped[str] = mapped_column(String(50), nullable=True)
    estimated_rate: Mapped[float] = mapped_column(Float, nullable=True)
    alert_message: Mapped[str] = mapped_column(Text, nullable=True)

    status: Mapped[str] = mapped_column(String(50), default="pending", index=True)
    # pending | acknowledged | indent_created | po_created | dismissed

    acknowledged_by: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    acknowledged_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    indent_id: Mapped[str] = mapped_column(String(36), ForeignKey("purchase_indents.id"), nullable=True)
    agent_run_id: Mapped[str] = mapped_column(String(36), ForeignKey("agent_run_logs.id"), nullable=True)


# ==================== DOCUMENT IO AGENT ====================

class DocumentCapture(Base, UUIDMixin, TimestampMixin):
    """
    Document IO Agent – captures and parses third-party documents.

    Supported sources:  email | whatsapp | upload | api | scan
    Document types   :  vendor_invoice | lr | delivery_challan | grn_slip | other

    Flow:
      1. Raw file stored (file_path)
      2. OCR + LLM extraction → extracted_data (JSONB)
      3. Auto-match to vendor (accounts table)
      4. Human review → link to ERP document (purchase_invoice, grn, etc.)
    """
    __tablename__ = "document_captures"

    capture_number: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    capture_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    source: Mapped[str] = mapped_column(String(50), nullable=True, index=True)
    document_type: Mapped[str] = mapped_column(String(100), nullable=True, index=True)

    # Raw file
    file_name: Mapped[str] = mapped_column(String(255), nullable=True)
    file_path: Mapped[str] = mapped_column(String(500), nullable=True)
    file_size_kb: Mapped[int] = mapped_column(Integer, nullable=True)
    mime_type: Mapped[str] = mapped_column(String(100), nullable=True)

    # Sender metadata
    sender_email: Mapped[str] = mapped_column(String(255), nullable=True)
    sender_name: Mapped[str] = mapped_column(String(255), nullable=True)
    email_subject: Mapped[str] = mapped_column(String(500), nullable=True)

    extraction_status: Mapped[str] = mapped_column(String(50), default="pending", index=True)
    # pending | processing | extracted | failed | reviewed

    # Structured data extracted by OCR + LLM
    # Vendor invoice: {vendor_name, invoice_number, date, items:[...], total, gst_amounts}
    # LR           : {lr_number, date, from_city, to_city, vehicle, weight, consignor}
    extracted_data: Mapped[dict] = mapped_column(JSONB, nullable=True)

    extraction_confidence: Mapped[float] = mapped_column(Float, nullable=True)   # 0.0 – 1.0
    ocr_raw_text: Mapped[str] = mapped_column(Text, nullable=True)

    # ERP linkage after human review
    linked_to_type: Mapped[str] = mapped_column(String(100), nullable=True)
    linked_to_id: Mapped[str] = mapped_column(String(36), nullable=True, index=True)

    matched_vendor_id: Mapped[str] = mapped_column(String(36), ForeignKey("accounts.id"), nullable=True)
    match_confidence: Mapped[float] = mapped_column(Float, nullable=True)

    reviewed_by: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    reviewed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    review_notes: Mapped[str] = mapped_column(Text, nullable=True)

    agent_run_id: Mapped[str] = mapped_column(String(36), ForeignKey("agent_run_logs.id"), nullable=True)


# ==================== AI INSIGHT CACHE ====================

class AIInsight(Base, UUIDMixin, TimestampMixin):
    """
    TTL-cached AI-generated insights for the Executive Dashboard.
    Any agent can write here; the dashboard reads the latest valid row
    per insight_type + scope.  expired_at controls refresh cadence.
    """
    __tablename__ = "ai_insights"

    insight_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    # cash_flow_forecast | sales_trend | inventory_risk | production_efficiency
    # vendor_performance | customer_health | scrap_analysis | buying_urgency

    scope_entity_type: Mapped[str] = mapped_column(String(50), nullable=True)   # branch | item | vendor | customer
    scope_entity_id: Mapped[str] = mapped_column(String(36), nullable=True, index=True)

    title: Mapped[str] = mapped_column(String(500), nullable=True)
    summary: Mapped[str] = mapped_column(Text, nullable=True)
    insight_data: Mapped[dict] = mapped_column(JSONB, nullable=True)     # charts, tables, KPIs
    recommendations: Mapped[list] = mapped_column(JSONB, nullable=True)  # [{action, priority, impact}]
    severity: Mapped[str] = mapped_column(String(20), default="info")    # info | warning | critical

    generated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    expired_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    is_valid: Mapped[bool] = mapped_column(Boolean, default=True)

    agent_id: Mapped[str] = mapped_column(String(36), ForeignKey("ai_agents.id"), nullable=True)
    agent_run_id: Mapped[str] = mapped_column(String(36), ForeignKey("agent_run_logs.id"), nullable=True)

    __table_args__ = (
        Index("ix_insight_type_scope", "insight_type", "scope_entity_type", "scope_entity_id"),
    )
