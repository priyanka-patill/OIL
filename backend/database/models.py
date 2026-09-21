import enum
from datetime import datetime, timezone
from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime, ForeignKey, 
    Text, Enum as SQLEnum, Float, Index
)
from sqlalchemy.orm import relationship
from backend.database.database import Base

class UserRole(str, enum.Enum):
    HSE_USER = "HSE_USER"
    HSE_MANAGER = "HSE_MANAGER"
    ADMIN = "ADMIN"

class ReportType(str, enum.Enum):
    UNSAFE_ACT = "UNSAFE_ACT"
    UNSAFE_CONDITION = "UNSAFE_CONDITION"
    NEAR_MISS = "NEAR_MISS"
    INCIDENT = "INCIDENT"

class ReportStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    SUBMITTED = "SUBMITTED"
    AI_ANALYZED = "AI_ANALYZED"
    HSE_REVIEW_PENDING = "HSE_REVIEW_PENDING"
    HSE_VALIDATED = "HSE_VALIDATED"
    ACTION_REQUIRED = "ACTION_REQUIRED"
    CLOSED = "CLOSED"

class HSEDecision(str, enum.Enum):
    PENDING = "PENDING"
    ACCEPTED = "ACCEPTED"
    MODIFIED = "MODIFIED"
    REJECTED = "REJECTED"

class InterventionStatus(str, enum.Enum):
    GENERATED = "GENERATED"
    PENDING_HSE_VALIDATION = "PENDING_HSE_VALIDATION"
    ACCEPTED = "ACCEPTED"
    MODIFIED = "MODIFIED"
    REJECTED = "REJECTED"

class HSEInterventionDecision(str, enum.Enum):
    ACCEPT = "ACCEPT"
    MODIFY = "MODIFY"
    REJECT = "REJECT"

class InterventionCategory(str, enum.Enum):
    ENERGY_ISOLATION = "ENERGY_ISOLATION"
    PERMIT_CONTROL = "PERMIT_CONTROL"
    PPE_CONTROL = "PPE_CONTROL"
    GAS_TESTING = "GAS_TESTING"
    CONFINED_SPACE_CONTROL = "CONFINED_SPACE_CONTROL"
    HOT_WORK_CONTROL = "HOT_WORK_CONTROL"
    WORKING_AT_HEIGHT_CONTROL = "WORKING_AT_HEIGHT_CONTROL"
    SUPERVISION = "SUPERVISION"
    MAINTENANCE = "MAINTENANCE"
    EQUIPMENT_GUARDING = "EQUIPMENT_GUARDING"
    TRAINING_AWARENESS = "TRAINING_AWARENESS"
    PROCEDURE_REVIEW = "PROCEDURE_REVIEW"
    HOUSEKEEPING = "HOUSEKEEPING"
    OTHER = "OTHER"

class ActionStatus(str, enum.Enum):
    APPROVED = "APPROVED"
    ASSIGNED = "ASSIGNED"
    IN_PROGRESS = "IN_PROGRESS"
    ON_HOLD = "ON_HOLD"
    COMPLETED = "COMPLETED"
    VERIFICATION_PENDING = "VERIFICATION_PENDING"
    VERIFIED = "VERIFIED"
    REOPENED = "REOPENED"
    CANCELLED = "CANCELLED"

class ActionPriority(str, enum.Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"

class SLAStatus(str, enum.Enum):
    NOT_STARTED = "NOT_STARTED"
    ACTIVE = "ACTIVE"
    DUE_SOON = "DUE_SOON"
    OVERDUE = "OVERDUE"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"

class SLACompletionTiming(str, enum.Enum):
    NOT_COMPLETED = "NOT_COMPLETED"
    COMPLETED_ON_TIME = "COMPLETED_ON_TIME"
    COMPLETED_LATE = "COMPLETED_LATE"

class InterventionPriority(str, enum.Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    INSUFFICIENT_DATA = "INSUFFICIENT_DATA"

def utc_now():
    return datetime.now(timezone.utc)

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(120), nullable=False)
    email = Column(String(120), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(SQLEnum(UserRole), default=UserRole.HSE_USER, nullable=False)
    department = Column(String(100), nullable=True)
    site = Column(String(100), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    # Relationships
    reports = relationship("SafetyReport", back_populates="creator")
    reviews = relationship("HSEReview", back_populates="reviewer")
    audit_logs = relationship("AuditLog", back_populates="user")

class SafetyReport(Base):
    __tablename__ = "safety_reports"

    id = Column(Integer, primary_key=True, index=True)
    report_number = Column(String(50), unique=True, index=True, nullable=False)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    report_type = Column(SQLEnum(ReportType), default=ReportType.NEAR_MISS, nullable=False)
    date = Column(String(20), nullable=False)
    site = Column(String(100), nullable=False)
    refinery_unit = Column(String(100), nullable=True)
    location = Column(String(100), nullable=True)
    equipment_id = Column(String(100), nullable=True)
    work_type = Column(String(100), nullable=True)
    activity = Column(String(100), nullable=True)
    department = Column(String(100), nullable=True)
    description = Column(Text, nullable=False)

    # Safety Precursor Boolean Flags
    ppe_noncompliance = Column(Boolean, default=False, nullable=False)
    supervisor_negligence = Column(Boolean, default=False, nullable=False)
    maintenance_delay_or_issue = Column(Boolean, default=False, nullable=False)
    repeated_issue_ignored = Column(Boolean, default=False, nullable=False)
    previous_similar_reports = Column(Integer, default=0, nullable=False)

    # Optional Post-Event HSE Investigation Fields
    immediate_cause = Column(String(255), nullable=True)
    potential_consequence = Column(String(255), nullable=True)
    risk_level = Column(String(50), nullable=True)
    corrective_action = Column(Text, nullable=True)
    action_status = Column(String(50), nullable=True)

    status = Column(SQLEnum(ReportStatus), default=ReportStatus.SUBMITTED, nullable=False, index=True)

    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    # Relationships
    creator = relationship("User", back_populates="reports")
    ai_analyses = relationship("AIAnalysis", back_populates="report", cascade="all, delete-orphan")
    hse_reviews = relationship("HSEReview", back_populates="report", cascade="all, delete-orphan")
    interventions = relationship("InterventionRecommendation", back_populates="report", cascade="all, delete-orphan")
    attachments = relationship("ReportAttachment", back_populates="report", cascade="all, delete-orphan", order_by="ReportAttachment.id.asc()")

    __table_args__ = (
        Index("idx_reports_site_type_status", "site", "report_type", "status"),
    )

class ReportAttachment(Base):
    """File attachments (Photos / Permits) associated with a SafetyReport."""
    __tablename__ = "report_attachments"

    id = Column(Integer, primary_key=True, index=True)
    report_id = Column(Integer, ForeignKey("safety_reports.id"), nullable=False, index=True)
    original_filename = Column(String(255), nullable=False)
    stored_filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    mime_type = Column(String(100), nullable=False)
    file_size = Column(Integer, nullable=False)
    file_extension = Column(String(20), nullable=False)
    uploaded_by = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    report = relationship("SafetyReport", back_populates="attachments")
    uploader = relationship("User")

class AIAnalysis(Base):
    """Storage structure reserved for Part 2C ML & AI Engine analysis."""
    __tablename__ = "ai_analyses"

    id = Column(Integer, primary_key=True, index=True)
    report_id = Column(Integer, ForeignKey("safety_reports.id"), nullable=False, index=True)
    model_version = Column(String(50), nullable=False)
    prediction = Column(String(50), nullable=False)
    classification = Column(Integer, nullable=False)
    probability_or_score = Column(Float, nullable=False)
    threshold = Column(Float, nullable=False)
    explanation_json = Column(Text, nullable=True)
    life_saving_rules_json = Column(Text, nullable=True)
    hazards_json = Column(Text, nullable=True)
    barrier_concerns_json = Column(Text, nullable=True)
    previous_similar_reports_count = Column(Integer, default=0, nullable=True)
    similar_reports_json = Column(Text, nullable=True)
    risk_level = Column(String(50), nullable=True)
    risk_explanation_json = Column(Text, nullable=True)
    risk_methodology_version = Column(String(50), default="RISK_EVAL_v1", nullable=True)
    similarity_methodology_version = Column(String(50), default="SIM_EVAL_v1", nullable=True)
    analysis_status = Column(String(50), default="COMPLETED", nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    report = relationship("SafetyReport", back_populates="ai_analyses")
    interventions = relationship("InterventionRecommendation", back_populates="ai_analysis", cascade="all, delete-orphan")

class HSEReview(Base):
    __tablename__ = "hse_reviews"

    id = Column(Integer, primary_key=True, index=True)
    report_id = Column(Integer, ForeignKey("safety_reports.id"), nullable=False, index=True)
    reviewer_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    ai_prediction_accepted = Column(Boolean, default=True, nullable=False)
    hse_decision = Column(SQLEnum(HSEDecision), default=HSEDecision.ACCEPTED, nullable=False)
    modified_classification = Column(Integer, nullable=True)
    modified_lsr_json = Column(Text, nullable=True)
    modified_hazards_json = Column(Text, nullable=True)
    modified_barrier_concerns_json = Column(Text, nullable=True)
    review_comment = Column(Text, nullable=True)
    reviewed_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    report = relationship("SafetyReport", back_populates="hse_reviews")
    reviewer = relationship("User", back_populates="reviews")

class InterventionRecommendation(Base):
    """Part 4A — Evidence-Based Intervention Recommendation Model."""
    __tablename__ = "intervention_recommendations"

    id = Column(Integer, primary_key=True, index=True)
    recommendation_number = Column(String(50), unique=True, index=True, nullable=False)

    # Source / Foreign References
    report_id = Column(Integer, ForeignKey("safety_reports.id"), nullable=True, index=True)
    analysis_id = Column(Integer, ForeignKey("ai_analyses.id"), nullable=True, index=True)
    recurring_pattern_id = Column(String(100), nullable=True, index=True)
    barrier_category = Column(String(100), nullable=True, index=True)

    # Core Recommendation Fields
    title = Column(String(255), nullable=False)
    category = Column(SQLEnum(InterventionCategory), default=InterventionCategory.OTHER, nullable=False, index=True)
    recommendation_text = Column(Text, nullable=False)
    rationale = Column(Text, nullable=False)
    priority_suggestion = Column(SQLEnum(InterventionPriority), default=InterventionPriority.MEDIUM, nullable=False, index=True)

    # Evidence Payload & Traceability
    evidence_summary = Column(Text, nullable=False)
    evidence_json = Column(Text, nullable=True)
    evidence_count = Column(Integer, default=1, nullable=False)
    first_observed = Column(String(20), nullable=True)
    latest_observed = Column(String(20), nullable=True)

    # Metadata & Version Preservation
    sif_classification = Column(String(50), nullable=True)
    hazards_json = Column(Text, nullable=True)
    life_saving_rules_json = Column(Text, nullable=True)
    bdi_score = Column(Float, nullable=True)
    escalation_indicators_json = Column(Text, nullable=True)

    model_version = Column(String(50), default="sif_model_v1", nullable=False)
    analytics_version = Column(String(50), default="safety_intelligence_v1", nullable=False)
    methodology_version = Column(String(50), default="intervention_rules_v1", nullable=False)

    status = Column(SQLEnum(InterventionStatus), default=InterventionStatus.PENDING_HSE_VALIDATION, nullable=False, index=True)

    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    # Relationships
    report = relationship("SafetyReport", back_populates="interventions")
    ai_analysis = relationship("AIAnalysis", back_populates="interventions")
    reviews = relationship("HSEInterventionReview", back_populates="intervention", cascade="all, delete-orphan", order_by="HSEInterventionReview.id.desc()")
    actions = relationship("Action", back_populates="intervention", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_interventions_report_category", "report_id", "category"),
    )

class HSEInterventionReview(Base):
    """Part 4B — Human-in-the-Loop HSE Review & Approval Model."""
    __tablename__ = "hse_intervention_reviews"

    id = Column(Integer, primary_key=True, index=True)
    intervention_id = Column(Integer, ForeignKey("intervention_recommendations.id"), nullable=False, index=True)
    reviewer_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    decision = Column(SQLEnum(HSEInterventionDecision), nullable=False)

    rejection_reason = Column(Text, nullable=True)
    review_comment = Column(Text, nullable=True)

    # HSE Modified Recommendation Fields (Immutability Principle: AI original values remain on intervention_recommendations)
    modified_title = Column(String(255), nullable=True)
    modified_recommendation_text = Column(Text, nullable=True)
    modified_category = Column(SQLEnum(InterventionCategory), nullable=True)
    modified_priority = Column(SQLEnum(InterventionPriority), nullable=True)

    # HSE Proposed Action Planning Metadata (Not operational actions)
    proposed_owner_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    proposed_department = Column(String(100), nullable=True)
    proposed_due_date = Column(String(20), nullable=True)

    reviewed_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    # Relationships
    intervention = relationship("InterventionRecommendation", back_populates="reviews")
    reviewer = relationship("User", foreign_keys=[reviewer_id])
    proposed_owner = relationship("User", foreign_keys=[proposed_owner_id])

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    action = Column(String(100), nullable=False, index=True)
    entity_type = Column(String(50), nullable=True)
    entity_id = Column(String(50), nullable=True)
    metadata_json = Column(Text, nullable=True)
    timestamp = Column(DateTime(timezone=True), default=utc_now, nullable=False, index=True)

    user = relationship("User", back_populates="audit_logs")


class Action(Base):
    """Part 4C — Operational Action Management & Assignment Model."""
    __tablename__ = "actions"

    id = Column(Integer, primary_key=True, index=True)
    action_number = Column(String(50), unique=True, index=True, nullable=False)

    # Core Linkages & Traceability
    intervention_id = Column(Integer, ForeignKey("intervention_recommendations.id"), nullable=False, index=True)
    report_id = Column(Integer, ForeignKey("safety_reports.id"), nullable=True, index=True)
    pattern_id = Column(String(100), nullable=True, index=True)
    barrier_id = Column(String(100), nullable=True, index=True)
    source_hse_review_id = Column(Integer, ForeignKey("hse_intervention_reviews.id"), nullable=True, index=True)

    # Operational Action Fields
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    assigned_user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    assigned_department = Column(String(100), nullable=True, index=True)
    site = Column(String(100), nullable=False, index=True)
    priority = Column(SQLEnum(ActionPriority), default=ActionPriority.MEDIUM, nullable=False, index=True)
    due_date = Column(String(20), nullable=False, index=True)
    status = Column(SQLEnum(ActionStatus), default=ActionStatus.ASSIGNED, nullable=False, index=True)

    # Server-Managed Lifecycle Timestamps
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)
    start_date = Column(DateTime(timezone=True), nullable=True)
    completion_date = Column(DateTime(timezone=True), nullable=True)
    verified_at = Column(DateTime(timezone=True), nullable=True)
    reopened_at = Column(DateTime(timezone=True), nullable=True)
    cancelled_at = Column(DateTime(timezone=True), nullable=True)

    # Immutability Traceability Payload
    evidence_snapshot_json = Column(Text, nullable=True)

    # Relationships
    intervention = relationship("InterventionRecommendation", back_populates="actions")
    report = relationship("SafetyReport")
    assigned_user = relationship("User", foreign_keys=[assigned_user_id])
    creator = relationship("User", foreign_keys=[created_by])
    source_hse_review = relationship("HSEInterventionReview")
    comments = relationship("ActionComment", back_populates="action", cascade="all, delete-orphan", order_by="ActionComment.id.asc()")
    sla = relationship("ActionSLA", back_populates="action", uselist=False, cascade="all, delete-orphan")
    evidences = relationship("ActionEvidence", back_populates="action", cascade="all, delete-orphan", order_by="ActionEvidence.id.asc()")
    completion_history = relationship("ActionCompletionHistory", back_populates="action", cascade="all, delete-orphan", order_by="ActionCompletionHistory.id.asc()")
    impact_analyses = relationship("ActionImpactAnalysis", back_populates="action", cascade="all, delete-orphan", order_by="ActionImpactAnalysis.id.desc()")

    __table_args__ = (
        Index("idx_actions_assigned_user_status", "assigned_user_id", "status"),
        Index("idx_actions_site_dept_status", "site", "assigned_department", "status"),
    )


class ActionComment(Base):
    """Part 4C — Action Comments Entity for Progress & Lifecycle Audit Threading."""
    __tablename__ = "action_comments"

    id = Column(Integer, primary_key=True, index=True)
    action_id = Column(Integer, ForeignKey("actions.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    comment = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    # Relationships
    action = relationship("Action", back_populates="comments")
    user = relationship("User")


class ActionSLA(Base):
    """Part 4D — Action SLA Monitoring & Time-Aware Tracking Model."""
    __tablename__ = "action_slas"

    id = Column(Integer, primary_key=True, index=True)
    action_id = Column(Integer, ForeignKey("actions.id"), unique=True, nullable=False, index=True)

    sla_status = Column(SQLEnum(SLAStatus), default=SLAStatus.ACTIVE, nullable=False, index=True)
    sla_start_at = Column(DateTime(timezone=True), nullable=False)
    due_at = Column(DateTime(timezone=True), nullable=False, index=True)
    sla_duration_minutes = Column(Integer, default=4320, nullable=False)
    due_soon_threshold_minutes = Column(Integer, default=1440, nullable=False)

    completed_at = Column(DateTime(timezone=True), nullable=True)
    completion_timing = Column(SQLEnum(SLACompletionTiming), default=SLACompletionTiming.NOT_COMPLETED, nullable=False, index=True)

    current_escalation_level = Column(Integer, default=0, nullable=False, index=True)
    last_reminder_at = Column(DateTime(timezone=True), nullable=True)
    last_escalation_at = Column(DateTime(timezone=True), nullable=True)

    reminder_count = Column(Integer, default=0, nullable=False)
    escalation_count = Column(Integer, default=0, nullable=False)

    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    # Relationships
    action = relationship("Action", back_populates="sla")
    reminders = relationship("ActionReminder", back_populates="sla", cascade="all, delete-orphan", order_by="ActionReminder.id.asc()")
    escalations = relationship("ActionEscalation", back_populates="sla", cascade="all, delete-orphan", order_by="ActionEscalation.id.asc()")

    __table_args__ = (
        Index("idx_action_slas_status_due", "sla_status", "due_at"),
    )


class ActionReminder(Base):
    """Part 4D — Auditable SLA Reminder Outbox Event Model."""
    __tablename__ = "action_reminders"

    id = Column(Integer, primary_key=True, index=True)
    action_id = Column(Integer, ForeignKey("actions.id"), nullable=False, index=True)
    sla_id = Column(Integer, ForeignKey("action_slas.id"), nullable=False, index=True)

    reminder_type = Column(String(50), nullable=False, index=True)  # DUE_SOON_REMINDER, OVERDUE_REMINDER
    scheduled_for = Column(DateTime(timezone=True), nullable=False)
    triggered_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    recipient_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    status = Column(String(50), default="SENT_AUDIT", nullable=False)
    message = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    # Relationships
    sla = relationship("ActionSLA", back_populates="reminders")
    action = relationship("Action")
    recipient = relationship("User")


class ActionEscalation(Base):
    """Part 4D — Auditable Action Escalation Event Model."""
    __tablename__ = "action_escalations"

    id = Column(Integer, primary_key=True, index=True)
    action_id = Column(Integer, ForeignKey("actions.id"), nullable=False, index=True)
    sla_id = Column(Integer, ForeignKey("action_slas.id"), nullable=False, index=True)

    escalation_level = Column(Integer, nullable=False, index=True)  # 1, 2, 3
    escalation_name = Column(String(100), nullable=False)
    overdue_minutes_at_trigger = Column(Integer, nullable=False)
    triggered_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    recipient_role_or_dept = Column(String(100), nullable=True)
    status = Column(String(50), default="TRIGGERED", nullable=False)
    reason = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    # Relationships
    sla = relationship("ActionSLA", back_populates="escalations")
    action = relationship("Action")


class SLAConfig(Base):
    """Part 4D — Configurable SLA Settings Model."""
    __tablename__ = "sla_configs"

    id = Column(Integer, primary_key=True, index=True)
    priority = Column(String(50), unique=True, nullable=False)  # HIGH, MEDIUM, LOW, DEFAULT
    default_duration_hours = Column(Integer, nullable=False)
    due_soon_threshold_hours = Column(Integer, nullable=False)
    escalation_l1_overdue_hours = Column(Integer, default=24, nullable=False)
    escalation_l2_overdue_hours = Column(Integer, default=48, nullable=False)
    escalation_l3_overdue_hours = Column(Integer, default=72, nullable=False)
    reminders_enabled = Column(Boolean, default=True, nullable=False)
    escalations_enabled = Column(Boolean, default=True, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)


class ActionEvidence(Base):
    """Part 4E — Action Completion Evidence Model."""
    __tablename__ = "action_evidences"

    id = Column(Integer, primary_key=True, index=True)
    action_id = Column(Integer, ForeignKey("actions.id"), nullable=False, index=True)
    uploaded_by = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    file_name = Column(String(255), nullable=False)
    file_type = Column(String(100), nullable=False)  # image/png, application/pdf, etc.
    file_path = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    uploaded_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    # Relationships
    action = relationship("Action", back_populates="evidences")
    uploader = relationship("User")


class ActionCompletionHistory(Base):
    """Part 4E — Multi-Cycle Action Completion & Verification History Audit Model."""
    __tablename__ = "action_completion_histories"

    id = Column(Integer, primary_key=True, index=True)
    action_id = Column(Integer, ForeignKey("actions.id"), nullable=False, index=True)
    cycle_number = Column(Integer, default=1, nullable=False)

    # Completion Stage
    completed_at = Column(DateTime(timezone=True), nullable=False)
    completed_by = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    completion_comment = Column(Text, nullable=False)

    # Verification / Reopen Stage
    verification_status = Column(String(50), default="PENDING", nullable=False, index=True)  # PENDING, VERIFIED, REOPENED
    verified_at = Column(DateTime(timezone=True), nullable=True)
    verified_by = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    verification_comment = Column(Text, nullable=True)

    reopened_at = Column(DateTime(timezone=True), nullable=True)
    reopened_by = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    reopen_reason = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    # Relationships
    action = relationship("Action", back_populates="completion_history")
    completer = relationship("User", foreign_keys=[completed_by])
    verifier = relationship("User", foreign_keys=[verified_by])
    reopener = relationship("User", foreign_keys=[reopened_by])


class ActionImpactAnalysis(Base):
    """Part 4E — Immutable Before/After Observational Impact Tracking Snapshot Model."""
    __tablename__ = "action_impact_analyses"

    id = Column(Integer, primary_key=True, index=True)
    action_id = Column(Integer, ForeignKey("actions.id"), nullable=False, index=True)
    intervention_id = Column(Integer, ForeignKey("intervention_recommendations.id"), nullable=False, index=True)
    report_id = Column(Integer, ForeignKey("safety_reports.id"), nullable=True, index=True)

    pattern_id = Column(String(100), nullable=True, index=True)
    barrier_id = Column(String(100), nullable=True, index=True)

    intervention_date = Column(DateTime(timezone=True), nullable=False)
    before_start = Column(String(20), nullable=False)
    before_end = Column(String(20), nullable=False)
    after_start = Column(String(20), nullable=False)
    after_end = Column(String(20), nullable=False)

    # 5 Safety Indicators Payload (JSON)
    metrics_json = Column(Text, nullable=False)

    overall_observed_change = Column(String(50), default="OBSERVED_DECREASE", nullable=False, index=True)  # OBSERVED_DECREASE, OBSERVED_INCREASE, OBSERVED_STABLE, INSUFFICIENT_DATA, NOT_COMPARABLE
    data_sufficiency_status = Column(String(50), default="SUFFICIENT", nullable=False, index=True)  # SUFFICIENT, INSUFFICIENT_DATA
    data_sufficiency_reason = Column(Text, nullable=True)

    methodology_version = Column(String(50), default="impact_methodology_v1", nullable=False)
    calculated_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    # Relationships
    action = relationship("Action", back_populates="impact_analyses")
    intervention = relationship("InterventionRecommendation")


class ChatConversation(Base):
    """Conversational Session for OIL HSE Safety Assistant."""
    __tablename__ = "chat_conversations"

    id = Column(String(50), primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    title = Column(String(255), default="Safety Assistant Chat", nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    user = relationship("User")
    messages = relationship("ChatMessage", back_populates="conversation", cascade="all, delete-orphan", order_by="ChatMessage.id")


class ChatMessage(Base):
    """Message item inside ChatConversation."""
    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(String(50), ForeignKey("chat_conversations.id"), nullable=False, index=True)
    sender = Column(String(20), nullable=False)  # 'user' or 'assistant'
    content = Column(Text, nullable=False)
    sources_json = Column(Text, nullable=True)   # Serialized list of sources
    actions_json = Column(Text, nullable=True)   # Serialized list of UI action buttons
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    conversation = relationship("ChatConversation", back_populates="messages")





