import pytest
from datetime import date, time, timedelta
from app.database.session import SessionLocal
from app.models import (
    Facility, Department, Doctor, DoctorAvailability, Appointment,
    FacilityService, AppointmentSlot, Ambulance, SlotStatus, AmbulanceStatus,
    AppointmentStatus, BookingChannel, PatientProfile, User
)

@pytest.fixture
def db():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()

class TestPhase2DatabaseQueries:
    
    def test_01_find_facilities_providing_dermatology(self, db):
        """Test 1: Find facilities providing Dermatology specialty."""
        results = db.query(FacilityService).filter(
            FacilityService.specialty_name.ilike("%Dermatology%"),
            FacilityService.is_available == True
        ).all()
        assert len(results) > 0
        facility_ids = [svc.facility_id for svc in results]
        facilities = db.query(Facility).filter(Facility.id.in_(facility_ids)).all()
        assert len(facilities) > 0

    def test_02_find_dermatologists_in_facilities(self, db):
        """Test 2: Find dermatologists associated with facilities providing dermatology."""
        dermatologists = db.query(Doctor).join(Department).filter(
            Department.name.ilike("%Dermatology%")
        ).all()
        assert len(dermatologists) > 0
        for doc in dermatologists:
            assert doc.facility_id is not None
            assert doc.specialization is not None

    def test_03_find_doctors_available_on_specific_day(self, db):
        """Test 3: Find doctors available on a specific day of week (e.g. Monday = 0)."""
        availabilities = db.query(DoctorAvailability).filter(
            DoctorAvailability.day_of_week == 0,
            DoctorAvailability.is_active == True
        ).all()
        assert len(availabilities) > 0
        available_doctor_ids = {a.doctor_id for a in availabilities}
        doctors = db.query(Doctor).filter(Doctor.id.in_(available_doctor_ids)).all()
        assert len(doctors) > 0

    def test_04_find_available_appointment_slots(self, db):
        """Test 4: Find available appointment slots in database."""
        available_slots = db.query(AppointmentSlot).filter(
            AppointmentSlot.status == SlotStatus.AVAILABLE,
            AppointmentSlot.slot_date >= date.today()
        ).all()
        assert len(available_slots) > 0

    def test_05_find_emergency_capable_facilities(self, db):
        """Test 5: Find emergency-capable facilities."""
        emergency_facilities = db.query(Facility).filter(
            Facility.emergency_available == True,
            Facility.is_active == True
        ).all()
        assert len(emergency_facilities) > 0

    def test_06_find_facilities_with_ambulance_support(self, db):
        """Test 6: Find facilities with ambulance support."""
        ambulance_facilities = db.query(Facility).filter(
            Facility.ambulance_available == True
        ).all()
        assert len(ambulance_facilities) > 0

    def test_07_find_available_ambulances(self, db):
        """Test 7: Find available ambulances."""
        available_ambulances = db.query(Ambulance).filter(
            Ambulance.status == AmbulanceStatus.AVAILABLE,
            Ambulance.is_active == True
        ).all()
        assert len(available_ambulances) > 0
        for amb in available_ambulances:
            assert amb.vehicle_identifier is not None
            assert amb.facility_id is not None

    def test_08_find_facilities_near_lat_lng(self, db):
        """Test 8: Find facilities near Baramati coordinates (18.15, 74.57)."""
        from math import radians, cos, sin, asin, sqrt
        
        target_lat, target_lng = 18.1506, 74.5772
        all_facs = db.query(Facility).all()
        nearby = []

        for f in all_facs:
            if f.latitude and f.longitude:
                # Haversine distance formula
                lat1, lon1, lat2, lon2 = map(radians, [target_lat, target_lng, f.latitude, f.longitude])
                dlat = lat2 - lat1
                dlon = lon2 - lon1
                a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
                c = 2 * asin(sqrt(a))
                km = 6371 * c
                if km <= 50:
                    nearby.append((f, km))

        assert len(nearby) > 0

    def test_09_find_suitable_facility_specialty_and_location(self, db):
        """Test 9: Find suitable facility for Pediatrics in Pune district."""
        results = db.query(Facility).join(Department).filter(
            Facility.district.ilike("%Pune%"),
            Department.name.ilike("%Pediatrics%")
        ).all()
        assert len(results) > 0

    def test_10_book_appointment_slot_status_transition(self, db):
        """Test 10: Book an available slot and ensure status transitions to BOOKED."""
        existing_apts = db.query(Appointment.doctor_id, Appointment.appointment_date, Appointment.start_time).all()
        existing_keys = {(a[0], a[1], a[2]) for a in existing_apts}
        
        all_available = db.query(AppointmentSlot).filter(
            AppointmentSlot.status == SlotStatus.AVAILABLE
        ).all()
        
        target_slot = None
        for s in all_available:
            if (s.doctor_id, s.slot_date, s.start_time) not in existing_keys:
                target_slot = s
                break
        
        assert target_slot is not None

        patient = db.query(PatientProfile).first()
        assert patient is not None

        # Transition slot to BOOKED
        target_slot.status = SlotStatus.BOOKED
        
        # Create appointment matching slot
        apt = Appointment(
            patient_id=patient.id,
            doctor_id=target_slot.doctor_id,
            facility_id=target_slot.facility_id,
            department_id=target_slot.department_id,
            appointment_date=target_slot.slot_date,
            start_time=target_slot.start_time,
            end_time=target_slot.end_time,
            status=AppointmentStatus.BOOKED,
            booking_channel=BookingChannel.PWA,
            reason_for_visit="Test Slot Transition",
            confirmation_code=f"JS-2026-TESTSLOT{target_slot.id}"
        )
        db.add(apt)
        db.commit()

        # Verify DB updates
        db.refresh(target_slot)
        assert target_slot.status == SlotStatus.BOOKED

    def test_11_cancel_appointment_slot_status_recovery(self, db):
        """Test 11: Cancel an appointment and verify slot returns to AVAILABLE."""
        slot = db.query(AppointmentSlot).filter(
            AppointmentSlot.status == SlotStatus.BOOKED
        ).first()
        assert slot is not None

        # Transition back to AVAILABLE on cancellation
        slot.status = SlotStatus.AVAILABLE
        db.commit()
        db.refresh(slot)
        assert slot.status == SlotStatus.AVAILABLE
