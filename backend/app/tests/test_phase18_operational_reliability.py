import unittest
import pytest
import json
from datetime import datetime, date, timedelta, time
from fastapi.testclient import TestClient

from app.main import app
from app.database.session import SessionLocal, engine
from app.models.user import User, PatientProfile
from app.models.facility import Facility, Department
from app.models.doctor import Doctor, DoctorAvailability, DoctorScheduleException
from app.models.appointment import Appointment
from app.models.telephony import CallSession
from app.models.enums import (
    UserRole, Language, BookingChannel, AppointmentStatus, CallSessionStatus,
    FacilityStatus, DepartmentStatus, DoctorStatus, ExceptionType
)
from app.models.audit import AuditLog
from app.services.phone_session_service import PhoneSessionService
from app.services.availability_service import AvailabilityService
from app.services.appointment_service import AppointmentService
from app.services.admin_service import AdminService
from app.services.provider_service import ProviderService
from app.services.facility_service import FacilityService
from app.core.security import create_access_token
from app.utils.timezone import get_today_ist
from scripts.seed import seed_database


class TestPhase18OperationalReliability(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        engine.dispose()
        seed_database(force_reset=True)
        engine.dispose()
        cls.client = TestClient(app)

    def setUp(self):
        self.db = SessionLocal()
        self.admin_user = self.db.query(User).filter(User.role == UserRole.ADMIN).first()
        self.customer_user = self.db.query(User).filter(User.role == UserRole.CUSTOMER).first()
        self.provider_user = self.db.query(User).filter(User.role == UserRole.PROVIDER).first()

        self.patient = self.db.query(PatientProfile).filter(PatientProfile.user_id == self.customer_user.id).first()
        if not self.patient:
            self.patient = self.db.query(PatientProfile).first()

        self.facility = self.db.query(Facility).first()
        self.department = self.db.query(Department).filter(Department.facility_id == self.facility.id).first()
        self.doctor = self.db.query(Doctor).filter(Doctor.facility_id == self.facility.id).first()

        self.admin_headers = {"Authorization": f"Bearer {create_access_token(self.admin_user.id)}"}
        self.customer_headers = {"Authorization": f"Bearer {create_access_token(self.customer_user.id)}"}
        self.provider_headers = {"Authorization": f"Bearer {create_access_token(self.provider_user.id)}"}

    def tearDown(self):
        self.db.close()

    def test_01_facility_status_defaults_to_active(self):
        """1. Verify Facility default status is ACTIVE."""
        fac = Facility(
            name="Test PHC Default",
            facility_type="PHC",
            address="Village Center",
            district="Pune",
            pincode="411001",
            phone_number="+919876543210"
        )
        self.db.add(fac)
        self.db.commit()
        self.assertEqual(fac.status, FacilityStatus.ACTIVE)
        self.assertTrue(fac.is_active)

    def test_02_department_status_defaults_to_active(self):
        """2. Verify Department default status is ACTIVE."""
        dept = Department(
            facility_id=self.facility.id,
            name="General Medicine Test"
        )
        self.db.add(dept)
        self.db.commit()
        self.assertEqual(dept.status, DepartmentStatus.ACTIVE)
        self.assertTrue(dept.is_active)

    def test_03_doctor_status_defaults_to_active(self):
        """3. Verify Doctor default status is ACTIVE."""
        doc = Doctor(
            facility_id=self.facility.id,
            department_id=self.department.id,
            name="Dr. Default Test",
            qualification="MBBS",
            specialization="General"
        )
        self.db.add(doc)
        self.db.commit()
        self.assertEqual(doc.status, DoctorStatus.ACTIVE)
        self.assertTrue(doc.is_active)

    def test_04_schedule_exception_type_defaults_to_leave(self):
        """4. Verify DoctorScheduleException default exception_type is LEAVE."""
        today = get_today_ist()
        exc = DoctorScheduleException(
            doctor_id=self.doctor.id,
            date=today,
            start_time=time(9, 0),
            end_time=time(17, 0)
        )
        self.db.add(exc)
        self.db.commit()
        self.assertEqual(exc.exception_type, ExceptionType.LEAVE)

    def test_05_facility_status_transition_to_temporarily_unavailable(self):
        """5. Transition facility status to TEMPORARILY_UNAVAILABLE via AdminService."""
        res = AdminService.toggle_facility_status(
            db=self.db,
            facility_id=self.facility.id,
            is_active=False,
            current_user=self.admin_user,
            status_val=FacilityStatus.TEMPORARILY_UNAVAILABLE
        )
        self.assertEqual(res.status, FacilityStatus.TEMPORARILY_UNAVAILABLE)

        # Restore
        AdminService.toggle_facility_status(self.db, self.facility.id, True, self.admin_user, FacilityStatus.ACTIVE)

    def test_06_facility_status_transition_to_inactive(self):
        """6. Transition facility status to INACTIVE via AdminService."""
        res = AdminService.toggle_facility_status(
            db=self.db,
            facility_id=self.facility.id,
            is_active=False,
            current_user=self.admin_user,
            status_val=FacilityStatus.INACTIVE
        )
        self.assertEqual(res.status, FacilityStatus.INACTIVE)

        # Restore
        AdminService.toggle_facility_status(self.db, self.facility.id, True, self.admin_user, FacilityStatus.ACTIVE)

    def test_07_inactive_facility_excluded_from_search(self):
        """7. Inactive facility excluded from standard search."""
        self.facility.status = FacilityStatus.INACTIVE
        self.db.commit()

        facs = FacilityService.search_facilities(self.db, pincode=self.facility.pincode, include_inactive=False)
        self.assertNotIn(self.facility.id, [f.id for f in facs])

        # Restore
        self.facility.status = FacilityStatus.ACTIVE
        self.db.commit()

    def test_08_temporarily_unavailable_facility_included_in_emergency_search(self):
        """8. TEMPORARILY_UNAVAILABLE facility included in emergency search if emergency capable."""
        self.facility.status = FacilityStatus.TEMPORARILY_UNAVAILABLE
        self.facility.emergency_available = True
        self.db.commit()

        facs = FacilityService.search_facilities(self.db, emergency_capable=True)
        self.assertIn(self.facility.id, [f.id for f in facs])

        # Restore
        self.facility.status = FacilityStatus.ACTIVE
        self.db.commit()

    def test_09_temporarily_unavailable_facility_blocks_opd_booking(self):
        """9. TEMPORARILY_UNAVAILABLE facility rejects OPD booking."""
        self.facility.status = FacilityStatus.TEMPORARILY_UNAVAILABLE
        self.db.commit()

        today = get_today_ist() + timedelta(days=1)
        apt_in = {
            "doctor_id": self.doctor.id,
            "facility_id": self.facility.id,
            "department_id": self.department.id,
            "appointment_date": today.strftime("%Y-%m-%d"),
            "start_time": "10:00:00",
            "reason_for_visit": "OPD Checkup"
        }

        resp = self.client.post("/api/v1/appointments", json=apt_in, headers=self.customer_headers)
        self.assertEqual(resp.status_code, 400)
        self.assertIn("FACILITY_TEMPORARILY_UNAVAILABLE", str(resp.json()))

        # Restore
        self.facility.status = FacilityStatus.ACTIVE
        self.db.commit()

    def test_10_inactive_department_blocks_opd_booking(self):
        """10. INACTIVE department rejects OPD booking."""
        self.department.status = DepartmentStatus.INACTIVE
        self.db.commit()

        today = get_today_ist() + timedelta(days=1)
        apt_in = {
            "doctor_id": self.doctor.id,
            "facility_id": self.facility.id,
            "department_id": self.department.id,
            "appointment_date": today.strftime("%Y-%m-%d"),
            "start_time": "10:00:00",
            "reason_for_visit": "OPD Checkup"
        }

        resp = self.client.post("/api/v1/appointments", json=apt_in, headers=self.customer_headers)
        self.assertEqual(resp.status_code, 400)
        self.assertIn("DEPARTMENT_INACTIVE", str(resp.json()))

        # Restore
        self.department.status = DepartmentStatus.ACTIVE
        self.db.commit()

    def test_11_inactive_doctor_blocks_opd_booking(self):
        """11. INACTIVE doctor rejects OPD booking."""
        self.doctor.status = DoctorStatus.INACTIVE
        self.db.commit()

        today = get_today_ist() + timedelta(days=1)
        apt_in = {
            "doctor_id": self.doctor.id,
            "facility_id": self.facility.id,
            "department_id": self.department.id,
            "appointment_date": today.strftime("%Y-%m-%d"),
            "start_time": "10:00:00",
            "reason_for_visit": "OPD Checkup"
        }

        resp = self.client.post("/api/v1/appointments", json=apt_in, headers=self.customer_headers)
        self.assertEqual(resp.status_code, 400)
        self.assertIn("DOCTOR_INACTIVE", str(resp.json()))

        # Restore
        self.doctor.status = DoctorStatus.ACTIVE
        self.db.commit()

    def test_12_doctor_on_leave_blocks_opd_booking(self):
        """12. Doctor ON_LEAVE rejects OPD booking."""
        self.doctor.status = DoctorStatus.ON_LEAVE
        self.db.commit()

        today = get_today_ist() + timedelta(days=1)
        apt_in = {
            "doctor_id": self.doctor.id,
            "facility_id": self.facility.id,
            "department_id": self.department.id,
            "appointment_date": today.strftime("%Y-%m-%d"),
            "start_time": "10:00:00",
            "reason_for_visit": "OPD Checkup"
        }

        resp = self.client.post("/api/v1/appointments", json=apt_in, headers=self.customer_headers)
        self.assertEqual(resp.status_code, 400)
        self.assertIn("DOCTOR_ON_LEAVE", str(resp.json()))

        # Restore
        self.doctor.status = DoctorStatus.ACTIVE
        self.db.commit()

    def test_13_custom_hours_exception_limits_availability(self):
        """13. CUSTOM_HOURS schedule exception restricts available slots to custom bounds."""
        target_date = get_today_ist() + timedelta(days=1)

        avail = self.db.query(DoctorAvailability).filter(
            DoctorAvailability.doctor_id == self.doctor.id,
            DoctorAvailability.day_of_week == target_date.weekday()
        ).first()
        if not avail:
            avail = DoctorAvailability(
                doctor_id=self.doctor.id,
                day_of_week=target_date.weekday(),
                start_time=time(9, 0),
                end_time=time(17, 0),
                slot_duration_minutes=30
            )
            self.db.add(avail)
            self.db.commit()

        exc = DoctorScheduleException(
            doctor_id=self.doctor.id,
            date=target_date,
            start_time=time(10, 0),
            end_time=time(12, 0),
            exception_type=ExceptionType.CUSTOM_HOURS,
            reason="Special Morning Clinic"
        )
        self.db.add(exc)
        self.db.commit()

        res = AvailabilityService.generate_doctor_slots(self.db, self.doctor.id, target_date)
        available_slots = [s for s in res.slots if s.status == "AVAILABLE"]
        for s in available_slots:
            s_time = datetime.strptime(s.start_time, "%H:%M").time()
            self.assertTrue(time(10, 0) <= s_time < time(12, 0))

        # Cleanup exception
        self.db.delete(exc)
        self.db.commit()

    def test_14_doctor_leave_exception_cancels_or_blocks_slots(self):
        """14. Doctor LEAVE schedule exception blocks all slots on target date."""
        target_date = get_today_ist() + timedelta(days=2)
        exc = DoctorScheduleException(
            doctor_id=self.doctor.id,
            date=target_date,
            start_time=time(0, 0),
            end_time=time(23, 59),
            exception_type=ExceptionType.LEAVE,
            reason="Medical Leave"
        )
        self.db.add(exc)
        self.db.commit()

        res = AvailabilityService.generate_doctor_slots(self.db, self.doctor.id, target_date)
        available_slots = [s for s in res.slots if s.status == "AVAILABLE"]
        self.assertEqual(len(available_slots), 0)

        # Cleanup
        self.db.delete(exc)
        self.db.commit()

    def test_15_prebooking_validation_rejects_inactive_facility(self):
        """15. Server-side pre-booking validation rejects inactive facility via API."""
        self.facility.status = FacilityStatus.INACTIVE
        self.db.commit()

        target_date = get_today_ist() + timedelta(days=1)
        resp = self.client.post("/api/v1/appointments", json={
            "doctor_id": self.doctor.id,
            "facility_id": self.facility.id,
            "department_id": self.department.id,
            "appointment_date": target_date.strftime("%Y-%m-%d"),
            "start_time": "10:00:00",
            "reason_for_visit": "Checkup"
        }, headers=self.customer_headers)

        self.assertEqual(resp.status_code, 400)
        self.assertIn("FACILITY_INACTIVE", str(resp.json()))

        # Restore
        self.facility.status = FacilityStatus.ACTIVE
        self.db.commit()

    def test_16_prebooking_validation_rejects_inactive_department(self):
        """16. Server-side pre-booking validation rejects inactive department via API."""
        self.department.status = DepartmentStatus.INACTIVE
        self.db.commit()

        target_date = get_today_ist() + timedelta(days=1)
        resp = self.client.post("/api/v1/appointments", json={
            "doctor_id": self.doctor.id,
            "facility_id": self.facility.id,
            "department_id": self.department.id,
            "appointment_date": target_date.strftime("%Y-%m-%d"),
            "start_time": "10:00:00",
            "reason_for_visit": "Checkup"
        }, headers=self.customer_headers)

        self.assertEqual(resp.status_code, 400)
        self.assertIn("DEPARTMENT_INACTIVE", str(resp.json()))

        # Restore
        self.department.status = DepartmentStatus.ACTIVE
        self.db.commit()

    def test_17_prebooking_validation_rejects_doctor_on_leave(self):
        """17. Server-side pre-booking validation rejects doctor on leave via API."""
        self.doctor.status = DoctorStatus.ON_LEAVE
        self.db.commit()

        target_date = get_today_ist() + timedelta(days=1)
        resp = self.client.post("/api/v1/appointments", json={
            "doctor_id": self.doctor.id,
            "facility_id": self.facility.id,
            "department_id": self.department.id,
            "appointment_date": target_date.strftime("%Y-%m-%d"),
            "start_time": "10:00:00",
            "reason_for_visit": "Checkup"
        }, headers=self.customer_headers)

        self.assertEqual(resp.status_code, 400)
        self.assertIn("DOCTOR_ON_LEAVE", str(resp.json()))

        # Restore
        self.doctor.status = DoctorStatus.ACTIVE
        self.db.commit()

    def test_18_admin_toggle_facility_status_creates_audit_log(self):
        """18. Admin status update creates audit log entry FACILITY_STATUS_CHANGED."""
        AdminService.toggle_facility_status(
            db=self.db,
            facility_id=self.facility.id,
            is_active=False,
            current_user=self.admin_user,
            status_val=FacilityStatus.TEMPORARILY_UNAVAILABLE
        )

        audit = self.db.query(AuditLog).filter(
            AuditLog.action == "FACILITY_STATUS_CHANGED",
            AuditLog.entity_id == self.facility.id
        ).first()

        self.assertIsNotNone(audit)
        self.assertEqual(audit.user_id, self.admin_user.id)

        # Restore
        AdminService.toggle_facility_status(self.db, self.facility.id, True, self.admin_user, FacilityStatus.ACTIVE)

    def test_19_admin_toggle_department_status_creates_audit_log(self):
        """19. Admin status update creates audit log entry DEPARTMENT_STATUS_CHANGED."""
        AdminService.toggle_department_status(
            db=self.db,
            dept_id=self.department.id,
            is_active=False,
            current_user=self.admin_user,
            status_val=DepartmentStatus.INACTIVE
        )

        audit = self.db.query(AuditLog).filter(
            AuditLog.action == "DEPARTMENT_STATUS_CHANGED",
            AuditLog.entity_id == self.department.id
        ).first()

        self.assertIsNotNone(audit)

        # Restore
        AdminService.toggle_department_status(self.db, self.department.id, True, self.admin_user, DepartmentStatus.ACTIVE)

    def test_20_admin_toggle_doctor_status_creates_audit_log(self):
        """20. Admin status update creates audit log entry DOCTOR_STATUS_CHANGED."""
        AdminService.toggle_doctor_status(
            db=self.db,
            doctor_id=self.doctor.id,
            is_active=False,
            current_user=self.admin_user,
            status_val=DoctorStatus.ON_LEAVE
        )

        audit = self.db.query(AuditLog).filter(
            AuditLog.action == "DOCTOR_STATUS_CHANGED",
            AuditLog.entity_id == self.doctor.id
        ).first()

        self.assertIsNotNone(audit)

        # Restore
        AdminService.toggle_doctor_status(self.db, self.doctor.id, True, self.admin_user, DoctorStatus.ACTIVE)

    def test_21_provider_update_doctor_status(self):
        """21. Provider updates assigned doctor status via ProviderService."""
        self.doctor.user_id = self.provider_user.id
        self.db.commit()

        res = ProviderService.update_provider_doctor_status(
            db=self.db,
            target_doctor_id=self.doctor.id,
            status_val=DoctorStatus.ON_LEAVE,
            current_user=self.provider_user
        )
        self.assertEqual(res.status, DoctorStatus.ON_LEAVE)

        # Restore
        ProviderService.update_provider_doctor_status(self.db, self.doctor.id, DoctorStatus.ACTIVE, self.provider_user)

    def test_22_provider_create_leave_exception_creates_audit_log(self):
        """22. Provider creating leave exception generates audit log DOCTOR_LEAVE_CREATED."""
        self.doctor.user_id = self.provider_user.id
        self.db.commit()

        today = get_today_ist() + timedelta(days=5)
        req = {
            "doctor_id": self.doctor.id,
            "date": today.strftime("%Y-%m-%d"),
            "start_time": "09:00:00",
            "end_time": "17:00:00",
            "exception_type": "LEAVE",
            "reason": "Personal Leave"
        }

        from app.schemas.provider import DoctorScheduleExceptionCreate
        exc_in = DoctorScheduleExceptionCreate(**req)
        ProviderService.create_leave_exception(self.db, exc_in, self.provider_user)

        audit = self.db.query(AuditLog).filter(
            AuditLog.action == "DOCTOR_LEAVE_CREATED",
            AuditLog.entity_id == self.doctor.id
        ).first()

        self.assertIsNotNone(audit)

    def test_23_phone_dtmf_department_unavailable_prompt(self):
        """23. Phone DTMF flow renders DEPARTMENT_UNAVAILABLE when department doctors are inactive."""
        dept_docs = self.db.query(Doctor).filter(Doctor.department_id == self.department.id).all()
        for d in dept_docs:
            d.status = DoctorStatus.INACTIVE
        self.db.commit()

        session = PhoneSessionService.start_session(self.db, "+919999988881")
        PhoneSessionService.process_dtmf_input(self.db, session.id, "1") # Greeting -> Main Menu
        PhoneSessionService.process_dtmf_input(self.db, session.id, "1") # Book OPD -> Facility Selection
        PhoneSessionService.process_dtmf_input(self.db, session.id, "1") # Select Facility -> Department Selection
        res = PhoneSessionService.process_dtmf_input(self.db, session.id, "1") # Select Dept

        self.assertEqual(res.current_state, "DEPARTMENT_UNAVAILABLE")
        self.assertIn("Is department mein abhi appointment available nahi hai", res.prompt_text)

        # Restore
        for d in dept_docs:
            d.status = DoctorStatus.ACTIVE
        self.db.commit()

    def test_24_phone_voice_department_unavailable_prompt(self):
        """24. Phone Voice flow renders DEPARTMENT_UNAVAILABLE when department status is INACTIVE."""
        all_depts = self.db.query(Department).filter(Department.facility_id == self.facility.id).all()
        for d in all_depts:
            d.status = DepartmentStatus.INACTIVE
        self.db.commit()

        session = PhoneSessionService.start_session(self.db, "+919999988882")
        PhoneSessionService.process_dtmf_input(self.db, session.id, "1") # Greeting -> Main Menu
        PhoneSessionService.process_dtmf_input(self.db, session.id, "1") # Main Menu -> Facility Selection
        res = PhoneSessionService.process_dtmf_input(self.db, session.id, "1") # Select Facility -> DEPARTMENT_UNAVAILABLE

        self.assertEqual(res.current_state, "DEPARTMENT_UNAVAILABLE")

        # Restore
        for d in all_depts:
            d.status = DepartmentStatus.ACTIVE
        self.db.commit()

    def test_25_phone_facility_temporarily_unavailable_prompt(self):
        """25. Selecting TEMPORARILY_UNAVAILABLE facility in phone flow transitions to FACILITY_UNAVAILABLE."""
        self.facility.status = FacilityStatus.TEMPORARILY_UNAVAILABLE
        self.db.commit()

        session = PhoneSessionService.start_session(self.db, "+919999988883")
        PhoneSessionService.process_dtmf_input(self.db, session.id, "1") # Main menu
        PhoneSessionService.process_dtmf_input(self.db, session.id, "1") # Book OPD
        res = PhoneSessionService.process_dtmf_input(self.db, session.id, "1") # Select Facility

        self.assertEqual(res.current_state, "FACILITY_UNAVAILABLE")
        self.assertIn("vartaman mein upalabdh nahi hai", res.prompt_text)

        # Restore
        self.facility.status = FacilityStatus.ACTIVE
        self.db.commit()

    def test_26_phone_session_bypasses_inactive_facilities(self):
        """26. Main menu facility list bypasses INACTIVE facilities in phone session."""
        self.facility.status = FacilityStatus.INACTIVE
        self.db.commit()

        session = PhoneSessionService.start_session(self.db, "+919999988884")
        PhoneSessionService.process_dtmf_input(self.db, session.id, "1")
        PhoneSessionService.process_dtmf_input(self.db, session.id, "1")

        context = json.loads(session.context_json) if session.context_json else {}
        fac_ids = [f["id"] for f in context.get("facilities", [])]
        self.assertNotIn(self.facility.id, fac_ids)

        # Restore
        self.facility.status = FacilityStatus.ACTIVE
        self.db.commit()

    def test_27_pwa_availability_response_hides_inactive_doctor_slots(self):
        """27. Availability endpoint returns 0 available slots when doctor is ON_LEAVE."""
        self.doctor.status = DoctorStatus.ON_LEAVE
        self.db.commit()

        target_date = get_today_ist() + timedelta(days=1)
        resp = self.client.get(f"/api/v1/doctors/{self.doctor.id}/availability?date={target_date}")

        self.assertEqual(resp.status_code, 200)
        slots = resp.json().get("slots", [])
        avail_slots = [s for s in slots if s["status"] == "AVAILABLE"]
        self.assertEqual(len(avail_slots), 0)

        # Restore
        self.doctor.status = DoctorStatus.ACTIVE
        self.db.commit()

    def test_28_historical_appointments_preserved_when_facility_inactive(self):
        """28. Changing facility status to INACTIVE preserves existing appointment records."""
        target_date = get_today_ist() + timedelta(days=3)
        apt = Appointment(
            patient_id=self.patient.id,
            doctor_id=self.doctor.id,
            facility_id=self.facility.id,
            department_id=self.department.id,
            appointment_date=target_date,
            start_time=time(10, 0),
            end_time=time(10, 30),
            status=AppointmentStatus.CONFIRMED,
            booking_channel=BookingChannel.PWA,
            confirmation_code="JS-HIST-FAC-TEST"
        )
        self.db.add(apt)
        self.db.commit()
        apt_id = apt.id

        self.facility.status = FacilityStatus.INACTIVE
        self.db.commit()

        saved_apt = self.db.query(Appointment).filter(Appointment.id == apt_id).first()
        self.assertIsNotNone(saved_apt)
        self.assertEqual(saved_apt.status, AppointmentStatus.CONFIRMED)

        # Restore
        self.facility.status = FacilityStatus.ACTIVE
        self.db.commit()

    def test_29_historical_appointments_preserved_when_doctor_on_leave(self):
        """29. Changing doctor status to ON_LEAVE preserves existing appointment records."""
        target_date = get_today_ist() + timedelta(days=4)
        apt = Appointment(
            patient_id=self.patient.id,
            doctor_id=self.doctor.id,
            facility_id=self.facility.id,
            department_id=self.department.id,
            appointment_date=target_date,
            start_time=time(11, 0),
            end_time=time(11, 30),
            status=AppointmentStatus.CONFIRMED,
            booking_channel=BookingChannel.PHONE,
            confirmation_code="JS-HIST-DOC-TEST"
        )
        self.db.add(apt)
        self.db.commit()
        apt_id = apt.id

        self.doctor.status = DoctorStatus.ON_LEAVE
        self.db.commit()

        saved_apt = self.db.query(Appointment).filter(Appointment.id == apt_id).first()
        self.assertIsNotNone(saved_apt)
        self.assertEqual(saved_apt.status, AppointmentStatus.CONFIRMED)

        # Restore
        self.doctor.status = DoctorStatus.ACTIVE
        self.db.commit()

    def test_30_emergency_108_lookup_unaffected_by_opd_unavailability(self):
        """30. Emergency 108 lookup and emergency mode remain active even if OPD is unavailable."""
        self.facility.status = FacilityStatus.TEMPORARILY_UNAVAILABLE
        self.facility.emergency_available = True
        self.db.commit()

        session = PhoneSessionService.start_session(self.db, "+919999988885")
        PhoneSessionService.process_dtmf_input(self.db, session.id, "1")
        res = PhoneSessionService.process_dtmf_input(self.db, session.id, "4")

        self.assertEqual(res.current_state, "EMERGENCY")
        self.assertIn("108", res.prompt_text)

        # Restore
        self.facility.status = FacilityStatus.ACTIVE
        self.db.commit()
