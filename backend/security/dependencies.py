from typing import List, Callable
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from backend.database.database import get_db
from backend.database.models import User, UserRole
from backend.security.auth import decode_access_token

security_scheme = HTTPBearer(auto_error=False)

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security_scheme),
    db: Session = Depends(get_db)
) -> User:
    """Extracts and validates the authenticated user from the Bearer JWT token."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate authentication credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    if not credentials or not credentials.credentials:
        raise credentials_exception
        
    token = credentials.credentials
    payload = decode_access_token(token)
    if not payload:
        raise credentials_exception
        
    user_id = payload.get("sub")
    if not user_id:
        raise credentials_exception
        
    user = db.query(User).filter(User.id == int(user_id)).first()
    if not user:
        raise credentials_exception
        
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user account. Contact Admin."
        )
        
    return user

def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """Returns current user if active."""
    return current_user

def require_roles(allowed_roles: List[UserRole]) -> Callable:
    """Dependency factory enforcing backend Role-Based Access Control (RBAC)."""
    def role_checker(current_user: User = Depends(get_current_active_user)) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Action forbidden for role '{current_user.role.value}'. Requires one of: {[r.value for r in allowed_roles]}"
            )
        return current_user
    return role_checker
