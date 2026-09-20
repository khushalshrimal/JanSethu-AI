from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from typing import List, Callable, Optional
from app.database.session import get_db
from app.models.user import User
from app.models.enums import UserRole
from app.core.security import decode_access_token

reusable_oauth2 = OAuth2PasswordBearer(
    tokenUrl="/api/v1/auth/login",
    auto_error=False
)

def get_current_user(
    db: Session = Depends(get_db),
    token: Optional[str] = Depends(reusable_oauth2)
) -> User:
    """Validates JWT access token from Bearer header and returns the authenticated active user."""
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication token missing. Please log in.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = decode_access_token(token)
    if not payload or "sub" not in payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired authentication token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id_str = payload["sub"]
    try:
        user_id = int(user_id_str)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Malformed token subject.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User belonging to this token no longer exists.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive or suspended user account."
        )

    return user

def get_current_user_optional(
    db: Session = Depends(get_db),
    token: Optional[str] = Depends(reusable_oauth2)
) -> Optional[User]:
    if not token:
        return None
    try:
        return get_current_user(db, token)
    except HTTPException:
        return None

def require_roles(*allowed_roles: UserRole) -> Callable:
    """Enforces Role-Based Access Control (RBAC). Returns 403 Forbidden if user role is not permitted."""
    def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in allowed_roles:
            role_names = [r.value if hasattr(r, 'value') else str(r) for r in allowed_roles]
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Requires one of the following roles: {', '.join(role_names)}. Your role is '{current_user.role.value}'."
            )
        return current_user
    return role_checker
