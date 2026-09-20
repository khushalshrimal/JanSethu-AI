from sqlalchemy.orm import Session
from app.models.user import User, PatientProfile
from app.schemas.user import UserCreate

class UserRepository:
    @staticmethod
    def get_by_id(db: Session, user_id: int) -> User:
        return db.query(User).filter(User.id == user_id).first()

    @staticmethod
    def get_by_phone(db: Session, phone_number: str) -> User:
        return db.query(User).filter(User.phone_number == phone_number).first()

    @staticmethod
    def create_user(db: Session, user_in: UserCreate) -> User:
        hashed_pwd = User.hash_password(user_in.password)
        db_user = User(
            name=user_in.name,
            phone_number=user_in.phone_number,
            email=user_in.email,
            password_hash=hashed_pwd,
            role=user_in.role,
            preferred_language=user_in.preferred_language
        )
        db.add(db_user)
        db.commit()
        db.refresh(db_user)

        # Create patient profile automatically if provided or if role is CUSTOMER
        profile_data = user_in.patient_profile.model_dump() if user_in.patient_profile else {}
        patient_profile = PatientProfile(user_id=db_user.id, **profile_data)
        db.add(patient_profile)
        db.commit()
        db.refresh(db_user)
        return db_user
