from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from backend.database.models import User, UserRole
from backend.database.schemas import UserSignup, UserLogin, UserAdminUpdate
from backend.security.auth import hash_password, verify_password, create_access_token
from backend.services.audit_service import log_audit_event

def signup_user(db: Session, signup_data: UserSignup) -> User:
    """
    Registers a new user account.
    CRITICAL SECURITY RULE: Public signups default strictly to HSE_USER.
    Admin escalation via signup is forbidden.
    """
    existing_user = db.query(User).filter(User.email == signup_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User with this email address already exists."
        )

    user = User(
        name=signup_data.name,
        email=signup_data.email.lower().strip(),
        password_hash=hash_password(signup_data.password),
        role=UserRole.HSE_USER, # Enforce HSE_USER for public signup
        department=signup_data.department,
        site=signup_data.site,
        is_active=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    log_audit_event(
        db, action="USER_CREATED", user_id=user.id, 
        entity_type="User", entity_id=user.id, 
        metadata={"name": user.name, "email": user.email, "role": user.role.value}
    )
    return user

def authenticate_user(db: Session, login_data: UserLogin) -> dict:
    """Authenticates user, verifies credentials, and generates access token."""
    user = db.query(User).filter(User.email == login_data.email.lower().strip()).first()
    if not user or not verify_password(login_data.password, user.password_hash):
        log_audit_event(
            db, action="LOGIN_FAILED", 
            metadata={"email": login_data.email, "reason": "Invalid credentials"}
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        log_audit_event(
            db, action="LOGIN_FAILED", user_id=user.id,
            metadata={"email": login_data.email, "reason": "Inactive account"}
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is deactivated. Contact Admin."
        )

    token = create_access_token(user_id=user.id, email=user.email, role=user.role)
    
    log_audit_event(
        db, action="LOGIN_SUCCESS", user_id=user.id,
        entity_type="User", entity_id=user.id
    )

    return {
        "access_token": token,
        "token_type": "bearer",
        "expires_in_minutes": 120,
        "user": user
    }

def update_user_admin(db: Session, target_user_id: int, update_data: UserAdminUpdate, admin_user: User) -> User:
    """Allows Admin users to update user role, department, site, or active status."""
    target_user = db.query(User).filter(User.id == target_user_id).first()
    if not target_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")

    changes = {}
    if update_data.role is not None:
        changes["role_old"] = target_user.role.value
        target_user.role = update_data.role
        changes["role_new"] = update_data.role.value

    if update_data.department is not None:
        target_user.department = update_data.department

    if update_data.site is not None:
        target_user.site = update_data.site

    if update_data.is_active is not None:
        changes["is_active_old"] = target_user.is_active
        target_user.is_active = update_data.is_active
        changes["is_active_new"] = update_data.is_active

    db.commit()
    db.refresh(target_user)

    log_audit_event(
        db, action="ADMIN_USER_UPDATED", user_id=admin_user.id,
        entity_type="User", entity_id=target_user.id, metadata=changes
    )
    return target_user
