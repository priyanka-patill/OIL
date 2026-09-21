import json
import math
from typing import Optional, List
from fastapi import APIRouter, Depends, Query, status, HTTPException
from sqlalchemy.orm import Session
from backend.database.database import get_db
from backend.database.models import User, UserRole, AuditLog
from backend.database.schemas import APIResponse, UserResponse, UserAdminUpdate, AuditLogResponse, AuditLogListResponse
from backend.security.dependencies import require_roles
from backend.services import auth_service

router = APIRouter(prefix="/admin", tags=["Admin Management"])

@router.get("/users", response_model=APIResponse[List[UserResponse]])
def list_users_admin(
    role: Optional[UserRole] = Query(None),
    is_active: Optional[bool] = Query(None),
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_roles([UserRole.ADMIN]))
):
    """Lists system users with optional filtering. Admin role required."""
    query = db.query(User)
    if role:
        query = query.filter(User.role == role)
    if is_active is not None:
        query = query.filter(User.is_active == is_active)

    users = query.order_by(User.id.asc()).all()
    user_responses = [UserResponse.model_validate(u) for u in users]
    return APIResponse(
        success=True,
        message="Users listed successfully.",
        data=user_responses
    )

@router.put("/users/{user_id}", response_model=APIResponse[UserResponse])
def update_user_admin(
    user_id: int,
    update_data: UserAdminUpdate,
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_roles([UserRole.ADMIN]))
):
    """Updates user role, site, department, or active status. Admin role required."""
    user = auth_service.update_user_admin(db, user_id, update_data, admin_user)
    return APIResponse(
        success=True,
        message="User updated successfully.",
        data=UserResponse.model_validate(user)
    )

@router.get("/audit-logs", response_model=APIResponse[AuditLogListResponse])
def list_audit_logs_admin(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    action: Optional[str] = Query(None),
    user_id: Optional[int] = Query(None),
    entity_type: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_roles([UserRole.ADMIN]))
):
    """Lists audit log events with filtering. Admin role required."""
    query = db.query(AuditLog)

    if action:
        query = query.filter(AuditLog.action.ilike(f"%{action}%"))
    if user_id:
        query = query.filter(AuditLog.user_id == user_id)
    if entity_type:
        query = query.filter(AuditLog.entity_type == entity_type)

    total = query.count()
    total_pages = math.ceil(total / page_size) if total > 0 else 1
    page = min(max(1, page), total_pages)
    offset = (page - 1) * page_size

    logs = query.order_by(AuditLog.id.desc()).offset(offset).limit(page_size).all()
    
    log_responses = []
    for l in logs:
        l_resp = AuditLogResponse.model_validate(l)
        l_resp.user_email = l.user.email if l.user else None
        log_responses.append(l_resp)

    list_resp = AuditLogListResponse(
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
        logs=log_responses
    )
    return APIResponse(
        success=True,
        message="Audit logs retrieved successfully.",
        data=list_resp
    )
