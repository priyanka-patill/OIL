from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from backend.database.database import get_db
from backend.database.models import User
from backend.database.schemas import APIResponse, UserSignup, UserLogin, Token, UserResponse
from backend.security.dependencies import get_current_active_user
from backend.services import auth_service, audit_service

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/signup", response_model=APIResponse[UserResponse], status_code=status.HTTP_201_CREATED)
def signup(signup_data: UserSignup, db: Session = Depends(get_db)):
    """Registers a new user account (defaults strictly to HSE_USER role)."""
    user = auth_service.signup_user(db, signup_data)
    return APIResponse(
        success=True,
        message="User account registered successfully.",
        data=UserResponse.model_validate(user)
    )

@router.post("/login", response_model=APIResponse[Token])
def login(login_data: UserLogin, db: Session = Depends(get_db)):
    """Authenticates user credentials and returns a Bearer JWT access token."""
    token_data = auth_service.authenticate_user(db, login_data)
    token_resp = Token(
        access_token=token_data["access_token"],
        token_type=token_data["token_type"],
        expires_in_minutes=token_data["expires_in_minutes"],
        user=UserResponse.model_validate(token_data["user"])
    )
    return APIResponse(
        success=True,
        message="Login successful.",
        data=token_resp
    )

@router.post("/logout", response_model=APIResponse[None])
def logout(current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    """Logs out user and records audit log entry."""
    audit_service.log_audit_event(
        db, action="LOGOUT", user_id=current_user.id, entity_type="User", entity_id=current_user.id
    )
    return APIResponse(
        success=True,
        message="Logout successful.",
        data=None
    )

@router.get("/me", response_model=APIResponse[UserResponse])
def get_me(current_user: User = Depends(get_current_active_user)):
    """Returns the authenticated user profile."""
    return APIResponse(
        success=True,
        message="Current user profile retrieved.",
        data=UserResponse.model_validate(current_user)
    )
