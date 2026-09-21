from datetime import datetime
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List, Generic, TypeVar, Any
from backend.database.models import UserRole, ReportType, ReportStatus, HSEDecision

T = TypeVar("T")

class APIResponse(BaseModel, Generic[T]):
    success: bool = True
    message: str = "Success"
    data: Optional[T] = None

# --- AUTH & USER SCHEMAS ---
class UserSignup(BaseModel):
    name: str = Field(..., min_length=2, max_length=120)
    email: EmailStr
    password: str = Field(..., min_length=6, max_length=100)
    department: Optional[str] = None
    site: Optional[str] = None

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in_minutes: int
    user: "UserResponse"

class TokenData(BaseModel):
    user_id: Optional[int] = None
    email: Optional[str] = None
    role: Optional[UserRole] = None

class UserResponse(BaseModel):
    id: int
    name: str
    email: str
    role: UserRole
    department: Optional[str] = None
    site: Optional[str] = None
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True

class UserAdminUpdate(BaseModel):
    role: Optional[UserRole] = None
    department: Optional[str] = None
    site: Optional[str] = None
    is_active: Optional[bool] = None

# --- SAFETY REPORT SCHEMAS ---
class ReportCreate(BaseModel):
    report_type: ReportType = ReportType.NEAR_MISS
    date: str
    site: str
    refinery_unit: Optional[str] = None
    location: Optional[str] = None
    equipment_id: Optional[str] = None
    work_type: Optional[str] = None
    activity: Optional[str] = None
    department: Optional[str] = None
    description: str = Field(..., min_length=10)

    ppe_noncompliance: bool = False
    supervisor_negligence: bool = False
    maintenance_delay_or_issue: bool = False
    repeated_issue_ignored: bool = False
    previous_similar_reports: int = 0

    immediate_cause: Optional[str] = None
    potential_consequence: Optional[str] = None
    risk_level: Optional[str] = None
    corrective_action: Optional[str] = None
    action_status: Optional[str] = None

class ReportUpdate(BaseModel):
    report_type: Optional[ReportType] = None
    date: Optional[str] = None
    site: Optional[str] = None
    refinery_unit: Optional[str] = None
    location: Optional[str] = None
    equipment_id: Optional[str] = None
    work_type: Optional[str] = None
    activity: Optional[str] = None
    department: Optional[str] = None
    description: Optional[str] = Field(None, min_length=10)

    ppe_noncompliance: Optional[bool] = None
    supervisor_negligence: Optional[bool] = None
    maintenance_delay_or_issue: Optional[bool] = None
    repeated_issue_ignored: Optional[bool] = None
    previous_similar_reports: Optional[int] = None

    immediate_cause: Optional[str] = None
    potential_consequence: Optional[str] = None
    risk_level: Optional[str] = None
    corrective_action: Optional[str] = None
    action_status: Optional[str] = None
    status: Optional[ReportStatus] = None

class AIAnalysisResponse(BaseModel):
    id: int
    report_id: int
    model_version: str
    prediction: str
    classification: int
    probability_or_score: float
    threshold: float
    explanation_json: Optional[str] = None
    life_saving_rules_json: Optional[str] = None
    hazards_json: Optional[str] = None
    barrier_concerns_json: Optional[str] = None
    previous_similar_reports_count: Optional[int] = 0
    similar_reports_json: Optional[str] = None
    risk_level: Optional[str] = None
    risk_explanation_json: Optional[str] = None
    risk_methodology_version: Optional[str] = "RISK_EVAL_v1"
    similarity_methodology_version: Optional[str] = "SIM_EVAL_v1"
    analysis_status: str
    created_at: datetime

    class Config:
        from_attributes = True

class ReportAttachmentResponse(BaseModel):
    id: int
    report_id: int
    original_filename: str
    stored_filename: str
    file_extension: str
    mime_type: str
    file_size: int
    uploaded_by: int
    created_at: datetime

    class Config:
        from_attributes = True

class ReportResponse(BaseModel):
    id: int
    report_number: str
    created_by: int
    creator_name: Optional[str] = None
    report_type: ReportType
    date: str
    site: str
    refinery_unit: Optional[str] = None
    location: Optional[str] = None
    equipment_id: Optional[str] = None
    work_type: Optional[str] = None
    activity: Optional[str] = None
    department: Optional[str] = None
    description: str

    ppe_noncompliance: bool
    supervisor_negligence: bool
    maintenance_delay_or_issue: bool
    repeated_issue_ignored: bool
    previous_similar_reports: int

    immediate_cause: Optional[str] = None
    potential_consequence: Optional[str] = None
    risk_level: Optional[str] = None
    corrective_action: Optional[str] = None
    action_status: Optional[str] = None

    status: ReportStatus
    ai_analysis: Optional[AIAnalysisResponse] = None
    attachments: List[ReportAttachmentResponse] = []
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class ReportListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    total_pages: int
    reports: List[ReportResponse]

# --- HSE REVIEW SCHEMAS ---
class ReviewCreate(BaseModel):
    ai_prediction_accepted: bool = True
    hse_decision: HSEDecision = HSEDecision.ACCEPTED
    modified_classification: Optional[int] = None
    modified_lsr: Optional[List[str]] = None
    modified_hazards: Optional[List[str]] = None
    modified_barrier_concerns: Optional[List[str]] = None
    review_comment: Optional[str] = None

class ReviewResponse(BaseModel):
    id: int
    report_id: int
    reviewer_id: int
    reviewer_name: Optional[str] = None
    ai_prediction_accepted: bool
    hse_decision: HSEDecision
    modified_classification: Optional[int] = None
    modified_lsr_json: Optional[str] = None
    modified_hazards_json: Optional[str] = None
    modified_barrier_concerns_json: Optional[str] = None
    review_comment: Optional[str] = None
    reviewed_at: datetime

    class Config:
        from_attributes = True

# --- AUDIT LOG SCHEMAS ---
class AuditLogResponse(BaseModel):
    id: int
    user_id: Optional[int] = None
    user_email: Optional[str] = None
    action: str
    entity_type: Optional[str] = None
    entity_id: Optional[str] = None
    metadata_json: Optional[str] = None
    timestamp: datetime

    class Config:
        from_attributes = True

class AuditLogListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    total_pages: int
    logs: List[AuditLogResponse]
