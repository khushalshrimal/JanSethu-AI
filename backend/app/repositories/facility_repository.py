import math
from sqlalchemy.orm import Session
from typing import List, Optional, Tuple
from app.models.facility import Facility, Department, EmergencyContact
from app.schemas.facility import FacilityCreate, DepartmentCreate

def haversine_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculates Haversine distance in kilometers between two geographic coordinates."""
    R = 6371.0 # Earth radius in km
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return round(R * c, 2)

class FacilityRepository:
    @staticmethod
    def get_all(
        db: Session,
        village: Optional[str] = None,
        district: Optional[str] = None,
        pincode: Optional[str] = None,
        emergency_only: bool = False
    ) -> List[Facility]:
        return FacilityRepository.search(
            db,
            village=village,
            district=district,
            pincode=pincode,
            emergency_capable=emergency_only
        )

    @staticmethod
    def search(
        db: Session,
        q: Optional[str] = None,
        pincode: Optional[str] = None,
        district: Optional[str] = None,
        village: Optional[str] = None,
        facility_type: Optional[str] = None,
        emergency_capable: Optional[bool] = None,
        department_id: Optional[int] = None,
        include_inactive: bool = False
    ) -> List[Facility]:
        """
        Unified healthcare discovery database search with deterministic filtering.
        """
        from sqlalchemy import or_
        from app.models.enums import FacilityStatus
        query = db.query(Facility)
        
        if not include_inactive:
            query = query.filter(Facility.is_active == True, Facility.status != FacilityStatus.INACTIVE)

        if q and q.strip():
            term = f"%{q.strip()}%"
            query = query.filter(
                or_(
                    Facility.name.ilike(term),
                    Facility.address.ilike(term),
                    Facility.village.ilike(term),
                    Facility.district.ilike(term),
                    Facility.pincode.ilike(term)
                )
            )

        if pincode and pincode.strip():
            query = query.filter(Facility.pincode == pincode.strip())

        if district and district.strip():
            query = query.filter(Facility.district.ilike(f"%{district.strip()}%"))

        if village and village.strip():
            query = query.filter(Facility.village.ilike(f"%{village.strip()}%"))

        if facility_type:
            if isinstance(facility_type, str):
                from app.models.enums import FacilityType
                try:
                    ft_enum = FacilityType(facility_type.upper())
                    query = query.filter(Facility.facility_type == ft_enum)
                except ValueError:
                    pass
            else:
                query = query.filter(Facility.facility_type == facility_type)

        if emergency_capable is True:
            query = query.filter(Facility.emergency_available == True)

        if department_id:
            query = query.join(Department).filter(
                Department.id == department_id,
                Department.is_active == True
            )

        return query.order_by(Facility.id.asc()).all()

    @staticmethod
    def get_nearby(
        db: Session,
        latitude: float,
        longitude: float,
        radius_km: float = 25.0
    ) -> List[Tuple[Facility, float]]:
        """
        Retrieves active facilities within radius_km sorted by nearest distance in km.
        """
        all_facilities = db.query(Facility).filter(Facility.is_active == True).all()
        nearby_results = []
        for fac in all_facilities:
            if fac.latitude is not None and fac.longitude is not None:
                dist = haversine_distance_km(latitude, longitude, fac.latitude, fac.longitude)
                if dist <= radius_km:
                    nearby_results.append((fac, dist))
        
        # Sort by distance ascending
        nearby_results.sort(key=lambda x: x[1])
        return nearby_results

    @staticmethod
    def get_by_id(db: Session, facility_id: int) -> Optional[Facility]:
        return db.query(Facility).filter(Facility.id == facility_id, Facility.is_active == True).first()

    @staticmethod
    def create_facility(db: Session, facility_in: FacilityCreate) -> Facility:
        db_facility = Facility(**facility_in.model_dump())
        db.add(db_facility)
        db.commit()
        db.refresh(db_facility)
        return db_facility

    @staticmethod
    def add_department(db: Session, facility_id: int, dept_in: DepartmentCreate) -> Department:
        db_dept = Department(facility_id=facility_id, **dept_in.model_dump())
        db.add(db_dept)
        db.commit()
        db.refresh(db_dept)
        return db_dept
