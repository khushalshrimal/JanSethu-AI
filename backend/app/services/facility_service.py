from sqlalchemy.orm import Session
from typing import List, Optional
from fastapi import HTTPException, status
from app.repositories.facility_repository import FacilityRepository
from app.schemas.facility import FacilityCreate, FacilityResponse, DepartmentCreate, DepartmentResponse

class FacilityService:
    @staticmethod
    def list_facilities(
        db: Session,
        village: Optional[str] = None,
        district: Optional[str] = None,
        pincode: Optional[str] = None,
        emergency_only: bool = False
    ) -> List[FacilityResponse]:
        facs = FacilityRepository.search(
            db,
            village=village,
            district=district,
            pincode=pincode,
            emergency_capable=emergency_only
        )
        return [FacilityResponse.model_validate(f) for f in facs]

    @staticmethod
    def search_facilities(
        db: Session,
        q: Optional[str] = None,
        pincode: Optional[str] = None,
        district: Optional[str] = None,
        village: Optional[str] = None,
        facility_type: Optional[str] = None,
        emergency_capable: Optional[bool] = None,
        department_id: Optional[int] = None,
        latitude: Optional[float] = None,
        longitude: Optional[float] = None,
        radius_km: Optional[float] = None,
        include_inactive: bool = False
    ) -> List[FacilityResponse]:
        """
        Unified healthcare discovery service supporting text search, pincode, district, village,
        facility type, emergency capability, department filter, and optional GPS distance sorting.
        """
        # Validate coordinates & radius if supplied
        if latitude is not None and (latitude < -90 or latitude > 90):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Latitude must be between -90 and 90 degrees.")
        if longitude is not None and (longitude < -180 or longitude > 180):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Longitude must be between -180 and 180 degrees.")
        if radius_km is not None and radius_km <= 0:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Search radius must be greater than 0 km.")

        facs = FacilityRepository.search(
            db,
            q=q,
            pincode=pincode,
            district=district,
            village=village,
            facility_type=facility_type,
            emergency_capable=emergency_capable,
            department_id=department_id,
            include_inactive=include_inactive
        )

        response_list = []
        effective_radius = radius_km or 25.0

        for f in facs:
            item = FacilityResponse.model_validate(f)
            if latitude is not None and longitude is not None and f.latitude is not None and f.longitude is not None:
                from app.repositories.facility_repository import haversine_distance_km
                dist = haversine_distance_km(latitude, longitude, f.latitude, f.longitude)
                if radius_km is not None and dist > effective_radius:
                    continue
                item.distance_km = dist
            response_list.append(item)

        # Sort by distance if GPS coordinates were provided, else preserve name order
        if latitude is not None and longitude is not None:
            response_list.sort(key=lambda x: x.distance_km if x.distance_km is not None else 99999.0)

        return response_list

    @staticmethod
    def list_nearby_facilities(
        db: Session,
        latitude: float,
        longitude: float,
        radius_km: float = 25.0
    ) -> List[FacilityResponse]:
        results = FacilityRepository.get_nearby(db, latitude, longitude, radius_km)
        response_list = []
        for fac, dist in results:
            item = FacilityResponse.model_validate(fac)
            item.distance_km = dist
            response_list.append(item)
        return response_list

    @staticmethod
    def get_facility(db: Session, facility_id: int) -> FacilityResponse:
        fac = FacilityRepository.get_by_id(db, facility_id)
        if not fac:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Facility with ID {facility_id} not found or inactive."
            )
        return fac

    @staticmethod
    def create_facility(db: Session, facility_in: FacilityCreate) -> FacilityResponse:
        return FacilityRepository.create_facility(db, facility_in)

    @staticmethod
    def add_department(db: Session, facility_id: int, dept_in: DepartmentCreate) -> DepartmentResponse:
        fac = FacilityRepository.get_by_id(db, facility_id)
        if not fac:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Facility with ID {facility_id} not found."
            )
        return FacilityRepository.add_department(db, facility_id, dept_in)
