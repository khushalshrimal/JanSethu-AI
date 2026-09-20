from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.repositories.user_repository import UserRepository
from app.schemas.user import UserCreate, UserResponse

class UserService:
    @staticmethod
    def create_user(db: Session, user_in: UserCreate) -> UserResponse:
        existing = UserRepository.get_by_phone(db, user_in.phone_number)
        if existing:
            if existing.verify_password("temp_dtmf_pwd") or existing.verify_password("temp_voice_pwd"):
                from app.models.user import User
                existing.name = user_in.name
                existing.password_hash = User.hash_password(user_in.password)
                if user_in.preferred_language:
                    existing.preferred_language = user_in.preferred_language
                db.commit()
                db.refresh(existing)
                return existing
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"User with phone number '{user_in.phone_number}' already exists."
            )
        return UserRepository.create_user(db, user_in)

    @staticmethod
    def get_user(db: Session, user_id: int) -> UserResponse:
        user = UserRepository.get_by_id(db, user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with ID {user_id} not found."
            )
        return user
