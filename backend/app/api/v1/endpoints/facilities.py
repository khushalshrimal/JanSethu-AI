from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database.session import get_db
from app.services.facility_service import FacilityService
from app.schemas.facility import FacilityCreate, FacilityResponse, DepartmentCreate, DepartmentResponse
from app.models.enums import UserRole
from app.models.user import User
from app.api.deps import require_roles

router = APIRouter()

@router.get("/", response_model=List[FacilityResponse])
def list_facilities(
    village: Optional[str] = Query(None, description="Filter by village"),
    district: Optional[str] = Query(None, description="Filter by district"),
    pincode: Optional[str] = Query(None, description="Filter by pincode"),
    emergency_only: bool = Query(False, description="Filter emergency capable facilities"),
    db: Session = Depends(get_db)
):
    """Public endpoint to search active healthcare facilities by village, district, pincode, or emergency status."""
    return FacilityService.list_facilities(db, village=village, district=district, pincode=pincode, emergency_only=emergency_only)

@router.get("/nearby", response_model=List[FacilityResponse])
def list_nearby_facilities(
    latitude: float = Query(..., description="User latitude coordinate"),
    longitude: float = Query(..., description="User longitude coordinate"),
    radius_km: float = Query(25.0, description="Search radius in kilometers"),
    db: Session = Depends(get_db)
):
    """Public endpoint to find active healthcare facilities within radius_km sorted by nearest distance."""
    return FacilityService.list_nearby_facilities(db, latitude=latitude, longitude=longitude, radius_km=radius_km)

@router.get("/search", response_model=List[FacilityResponse], summary="Unified Healthcare Discovery Search")
def search_facilities(
    q: Optional[str] = Query(None, description="Free text query matching name, address, village, district, or pincode"),
    pincode: Optional[str] = Query(None, description="Exact 6-digit PIN code"),
    district: Optional[str] = Query(None, description="District name"),
    village: Optional[str] = Query(None, description="Village or town name"),
    facility_type: Optional[str] = Query(None, description="PHC, CHC, GOVERNMENT_HOSPITAL, PRIVATE_HOSPITAL, CLINIC"),
    emergency_capable: Optional[bool] = Query(None, description="Filter 24/7 emergency-capable facilities"),
    emergency_available: Optional[bool] = Query(None, description="Alias for emergency_capable"),
    department_id: Optional[int] = Query(None, description="Filter facilities containing specific active department ID"),
    latitude: Optional[float] = Query(None, description="Optional GPS latitude for distance sorting"),
    longitude: Optional[float] = Query(None, description="Optional GPS longitude for distance sorting"),
    radius_km: Optional[float] = Query(None, description="Optional search radius in km when coordinates are provided"),
    include_inactive: bool = Query(False, description="Include inactive facilities in search results"),
    db: Session = Depends(get_db)
):
    """
    Unified healthcare discovery endpoint supporting text search, location parameters,
    facility classification, emergency status, department filters, and GPS distance calculation.
    """
    emg = emergency_capable if emergency_capable is not None else emergency_available
    return FacilityService.search_facilities(
        db,
        q=q,
        pincode=pincode,
        district=district,
        village=village,
        facility_type=facility_type,
        emergency_capable=emg,
        department_id=department_id,
        latitude=latitude,
        longitude=longitude,
        radius_km=radius_km,
        include_inactive=include_inactive
    )

@router.get("/{facility_id}/departments", response_model=List[DepartmentResponse])
def get_facility_departments(facility_id: int, db: Session = Depends(get_db)):
    """Public endpoint to list active departments for a specific facility."""
    fac = FacilityService.get_facility(db, facility_id)
    from app.models.facility import Department
    depts = db.query(Department).filter(
        Department.facility_id == facility_id,
        Department.is_active == True
    ).order_by(Department.name.asc()).all()
    return [DepartmentResponse.model_validate(d) for d in depts]

@router.get("/{facility_id}", response_model=FacilityResponse)
def get_facility(facility_id: int, db: Session = Depends(get_db)):
    """Public endpoint to retrieve facility details."""
    return FacilityService.get_facility(db, facility_id)

@router.post("/", response_model=FacilityResponse, status_code=status.HTTP_201_CREATED)
def create_facility(
    facility_in: FacilityCreate,
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_roles(UserRole.ADMIN))
):
    """ADMIN ONLY: Registers a new healthcare facility."""
    return FacilityService.create_facility(db, facility_in)

@router.post("/{facility_id}/departments", response_model=DepartmentResponse, status_code=status.HTTP_201_CREATED)
def add_department(
    facility_id: int,
    dept_in: DepartmentCreate,
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_roles(UserRole.ADMIN))
):
    """ADMIN ONLY: Adds a department to a facility."""
    return FacilityService.add_department(db, facility_id, dept_in)
