from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.models.user import User, PatientProfile
from app.models.audit import AuditLog
from app.models.enums import UserRole
from app.core.security import create_access_token
from app.schemas.auth import RegisterRequest, LoginRequest, TokenResponse, CurrentUserResponse
from app.schemas.user import UserResponse, UserCreate, PatientProfileCreate
from app.services.user_service import UserService
from app.api.deps import get_current_user

router = APIRouter()

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register_customer(req: RegisterRequest, db: Session = Depends(get_db)):
    """
    Public customer registration.
    Enforces CUSTOMER role assignment and creates patient profile.
    Admin & Provider accounts must be created through administrative channels.
    """
    user_in = UserCreate(
        name=req.name,
        phone_number=req.phone_number,
        email=req.email,
        password=req.password,
        role=UserRole.CUSTOMER, # Hardcoded CUSTOMER for public endpoint
        preferred_language=req.preferred_language,
        patient_profile=PatientProfileCreate(
            village=req.village,
            district=req.district,
            pincode=req.pincode
        )
    )
    user = UserService.create_user(db, user_in)

    # Log security audit event
    audit = AuditLog(
        user_id=user.id,
        action="USER_REGISTERED",
        entity_type="User",
        entity_id=user.id,
        metadata_json={"role": "CUSTOMER", "phone": req.phone_number}
    )
    db.add(audit)
    db.commit()

    return user

@router.post("/login", response_model=TokenResponse)
def login(req: LoginRequest, db: Session = Depends(get_db)):
    """
    Authenticates user via phone number & password.
    Returns signed JWT access token.
    """
    user = db.query(User).filter(User.phone_number == req.phone_number).first()

    # Generic error message to prevent phone enumeration
    invalid_credentials_exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid phone number or password.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if not user:
        # Audit failed attempt
        audit = AuditLog(
            action="LOGIN_FAILED",
            entity_type="User",
            metadata_json={"phone_attempted": req.phone_number, "reason": "user_not_found"}
        )
        db.add(audit)
        db.commit()
        raise invalid_credentials_exc

    if not user.verify_password(req.password):
        audit = AuditLog(
            user_id=user.id,
            action="LOGIN_FAILED",
            entity_type="User",
            entity_id=user.id,
            metadata_json={"reason": "invalid_password"}
        )
        db.add(audit)
        db.commit()
        raise invalid_credentials_exc

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is suspended or inactive."
        )

    # Issue JWT token with user_id subject
    token = create_access_token(subject=user.id)

    # Audit login success
    audit = AuditLog(
        user_id=user.id,
        action="LOGIN_SUCCESS",
        entity_type="User",
        entity_id=user.id,
        metadata_json={"role": user.role.value}
    )
    db.add(audit)
    db.commit()

    user_resp = UserResponse.model_validate(user)
    return TokenResponse(
        access_token=token,
        token_type="bearer",
        user=user_resp
    )

@router.get("/me", response_model=CurrentUserResponse)
def get_current_user_profile(current_user: User = Depends(get_current_user)):
    """Retrieves authenticated user profile information."""
    return CurrentUserResponse.model_validate(current_user)

@router.post("/logout")
def logout(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    Stateless JWT logout endpoint.
    Client should discard token locally. Token revocation list can be attached in future phases.
    """
    audit = AuditLog(
        user_id=current_user.id,
        action="LOGOUT",
        entity_type="User",
        entity_id=current_user.id
    )
    db.add(audit)
    db.commit()
    return {"message": "Successfully logged out. Please discard your authentication token."}
