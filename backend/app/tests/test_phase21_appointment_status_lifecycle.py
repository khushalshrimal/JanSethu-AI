import unittest
from datetime import date, time, timedelta
from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.database.session import SessionLocal, engine
from app.database.base import Base
from app.models import (
    User, PatientProfile, Facility, Department, Doctor, Appointment,
    UserRole, FacilityType, Language, AppointmentStatus, BookingChannel
)
from app.services.appointment_service import AppointmentService
from app.services.provider_service import ProviderService
from app.schemas.appointment import AppointmentCreate, AppointmentCancelRequest, AppointmentRescheduleRequest
from app.schemas.provider import AppointmentStatusUpdateRequest
from app.utils.timezone import get_ist_now

class TestPhase21AppointmentStatusLifecycle(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        Base.metadata.create_all(bind=engine)

    def setUp(self):
        self.db: Session = SessionLocal()
        ist_now = get_ist_now()
        self.valid_future_date = ist_now.date() + timedelta(days=2)

        # Setup test entities with unique emails
        suffix = f"{int(ist_now.timestamp() * 1000)}"
        self.customer_user = User(
            name="Status Test Patient",
            email=f"status_patient_{suffix}@test.com",
            phone_number=f"98765{suffix[-5:]}",
            password_hash="test_hash",
            role=UserRole.CUSTOMER,
            is_active=True
        )
        self.db.add(self.customer_user)

        self.provider_user = User(
            name="Status Test Doctor",
            email=f"status_doctor_{suffix}@test.com",
            phone_number=f"91234{suffix[-5:]}",
            password_hash="test_hash",
            role=UserRole.PROVIDER,
            is_active=True
        )
        self.db.add(self.provider_user)
        self.db.commit()

        self.patient = PatientProfile(
            user_id=self.customer_user.id,
            gender="MALE",
            district="Pune"
        )
        self.db.add(self.patient)

        self.facility = Facility(
            name=f"Status Test PHC {suffix}",
            facility_type=FacilityType.PHC,
            address="123 Hospital Road",
            district="Pune",
            village="Testing Village",
            pincode="411001",
            is_active=True
        )
        self.db.add(self.facility)
        self.db.commit()

        self.department = Department(
            facility_id=self.facility.id,
            name="General OPD",
            is_active=True
        )
        self.db.add(self.department)
        self.db.commit()

        self.doctor = Doctor(
            user_id=self.provider_user.id,
            facility_id=self.facility.id,
            department_id=self.department.id,
            name="Dr. Status Specialist",
            qualification="MBBS, MD",
            specialization="Cardiology",
            experience_years=8,
            is_active=True
        )
        self.db.add(self.doctor)
        self.db.commit()
        self.db.refresh(self.customer_user)
        self.db.refresh(self.provider_user)

    def tearDown(self):
        self.db.close()

    def _create_test_appointment(self, slot_idx=0) -> AppointmentResponse:
        start_hour = 9 + ((slot_idx * 30) // 60)
        start_min = (slot_idx * 30) % 60
        apt_in = AppointmentCreate(
            doctor_id=self.doctor.id,
            facility_id=self.facility.id,
            department_id=self.department.id,
            appointment_date=self.valid_future_date,
            start_time=time(start_hour, start_min),
            booking_channel=BookingChannel.PWA,
            reason_for_visit="Routine OPD Status Test"
        )
        return AppointmentService.book_appointment(self.db, apt_in, self.customer_user)

    # 1. New appointment -> PENDING / Active Upcoming
    def test_01_new_appointment_is_pending_or_active(self):
        res = self._create_test_appointment(9)
        self.assertIn(res.status, [AppointmentStatus.PENDING, AppointmentStatus.BOOKED, AppointmentStatus.CONFIRMED])

    # 2. PENDING appears in UPCOMING
    def test_02_pending_appears_in_upcoming(self):
        res = self._create_test_appointment(10)
        upcoming = AppointmentService.get_my_appointments(self.db, self.customer_user, upcoming=True)
        found_ids = [a.id for a in upcoming]
        self.assertIn(res.id, found_ids)

    # 3. PENDING appointment can be cancelled
    def test_03_pending_appointment_can_be_cancelled(self):
        res = self._create_test_appointment(11)
        cancel_req = AppointmentCancelRequest(reason="Patient personal conflict")
        cancel_res = AppointmentService.cancel_appointment(self.db, res.id, cancel_req, self.customer_user)
        self.assertEqual(cancel_res.status, AppointmentStatus.CANCELLED)

    # 4. Cancellation -> CANCELLED
    def test_04_cancellation_sets_cancelled_status(self):
        res = self._create_test_appointment(12)
        cancel_req = AppointmentCancelRequest(reason="Doctor unavailable")
        cancel_res = AppointmentService.cancel_appointment(self.db, res.id, cancel_req, self.customer_user)
        self.assertEqual(cancel_res.status, AppointmentStatus.CANCELLED)
        
        # Verify directly in DB
        db_apt = self.db.query(Appointment).filter(Appointment.id == res.id).first()
        self.assertEqual(db_apt.status, AppointmentStatus.CANCELLED)

    # 5. CANCELLED appears in CANCELLED history
    def test_05_cancelled_appears_in_cancelled_filter(self):
        res = self._create_test_appointment(13)
        AppointmentService.cancel_appointment(self.db, res.id, AppointmentCancelRequest(reason="Cancel test"), self.customer_user)
        cancelled_apts = AppointmentService.get_my_appointments(self.db, self.customer_user, status_filter=AppointmentStatus.CANCELLED)
        found_ids = [a.id for a in cancelled_apts]
        self.assertIn(res.id, found_ids)

    # 6. CANCELLED is not shown in UPCOMING
    def test_06_cancelled_is_not_shown_in_upcoming(self):
        res = self._create_test_appointment(14)
        AppointmentService.cancel_appointment(self.db, res.id, AppointmentCancelRequest(reason="Cancel test"), self.customer_user)
        upcoming = AppointmentService.get_my_appointments(self.db, self.customer_user, upcoming=True)
        found_ids = [a.id for a in upcoming]
        self.assertNotIn(res.id, found_ids)

    # 7. PENDING can be marked COMPLETED
    def test_07_pending_can_be_marked_completed(self):
        res = self._create_test_appointment(15)
        comp_res = AppointmentService.complete_consultation(self.db, res.id, current_user=self.provider_user)
        self.assertEqual(comp_res.status, AppointmentStatus.COMPLETED)

    # 8. COMPLETED appears in COMPLETED history
    def test_08_completed_appears_in_completed_filter(self):
        res = self._create_test_appointment(16)
        AppointmentService.complete_consultation(self.db, res.id, current_user=self.provider_user)
        completed_apts = AppointmentService.get_my_appointments(self.db, self.customer_user, status_filter=AppointmentStatus.COMPLETED)
        found_ids = [a.id for a in completed_apts]
        self.assertIn(res.id, found_ids)

    # 9. COMPLETED cannot be cancelled through normal flow
    def test_09_completed_cannot_be_cancelled(self):
        res = self._create_test_appointment(17)
        AppointmentService.complete_consultation(self.db, res.id, current_user=self.provider_user)
        with self.assertRaises(HTTPException) as ctx:
            AppointmentService.cancel_appointment(self.db, res.id, AppointmentCancelRequest(reason="Try cancel"), self.customer_user)
        self.assertEqual(ctx.exception.status_code, 400)

    # 10. CANCELLED cannot become COMPLETED
    def test_10_cancelled_cannot_become_completed(self):
        res = self._create_test_appointment(18)
        AppointmentService.cancel_appointment(self.db, res.id, AppointmentCancelRequest(reason="Try cancel"), self.customer_user)
        with self.assertRaises(HTTPException) as ctx:
            AppointmentService.complete_consultation(self.db, res.id, current_user=self.provider_user)
        self.assertEqual(ctx.exception.status_code, 400)

        # Provider dashboard update status should also fail
        req = AppointmentStatusUpdateRequest(status=AppointmentStatus.COMPLETED)
        with self.assertRaises(HTTPException) as ctx2:
            ProviderService.update_appointment_status(self.db, res.id, req, self.provider_user)
        self.assertEqual(ctx2.exception.status_code, 400)

    # 11. Referral ID lookup finds PENDING appointment
    def test_11_referral_id_lookup_finds_pending_appointment(self):
        res = self._create_test_appointment(19)
        found = AppointmentService.get_by_confirmation_code(self.db, res.confirmation_code)
        self.assertEqual(found.id, res.id)
        self.assertIn(found.status, [AppointmentStatus.PENDING, AppointmentStatus.BOOKED, AppointmentStatus.CONFIRMED])

    # 12. Referral ID lookup finds COMPLETED appointment
    def test_12_referral_id_lookup_finds_completed_appointment(self):
        res = self._create_test_appointment(20)
        AppointmentService.complete_consultation(self.db, res.id, current_user=self.provider_user)
        found = AppointmentService.get_by_confirmation_code(self.db, res.confirmation_code)
        self.assertEqual(found.id, res.id)
        self.assertEqual(found.status, AppointmentStatus.COMPLETED)

    # 13. Referral ID lookup finds CANCELLED appointment
    def test_13_referral_id_lookup_finds_cancelled_appointment(self):
        res = self._create_test_appointment(21)
        AppointmentService.cancel_appointment(self.db, res.id, AppointmentCancelRequest(reason="Cancel test"), self.customer_user)
        found = AppointmentService.get_by_confirmation_code(self.db, res.confirmation_code)
        self.assertEqual(found.id, res.id)
        self.assertEqual(found.status, AppointmentStatus.CANCELLED)

    # 14. Rescheduled appointment preserves correct status
    def test_14_rescheduled_appointment_preserves_status(self):
        res = self._create_test_appointment(22)
        new_date = self.valid_future_date + timedelta(days=1)
        resched_req = AppointmentRescheduleRequest(new_date=new_date, new_start_time=time(10, 0))
        rescheduled = AppointmentService.reschedule_appointment(
            self.db,
            res.id,
            reschedule_in=resched_req,
            current_user=self.customer_user
        )
        self.assertIn(rescheduled.status, [AppointmentStatus.PENDING, AppointmentStatus.BOOKED, AppointmentStatus.CONFIRMED])
        self.assertEqual(rescheduled.appointment_date, new_date)

    # 15. Multiple appointments have independent statuses
    def test_15_multiple_appointments_have_independent_statuses(self):
        res1 = self._create_test_appointment(23)
        res2 = self._create_test_appointment(24)

        AppointmentService.cancel_appointment(self.db, res1.id, AppointmentCancelRequest(reason="Cancel apt 1"), self.customer_user)
        AppointmentService.complete_consultation(self.db, res2.id, current_user=self.provider_user)

        check1 = AppointmentService.get_by_confirmation_code(self.db, res1.confirmation_code)
        check2 = AppointmentService.get_by_confirmation_code(self.db, res2.confirmation_code)

        self.assertEqual(check1.status, AppointmentStatus.CANCELLED)
        self.assertEqual(check2.status, AppointmentStatus.COMPLETED)

    # 16. Refreshing My Appointments preserves database status
    def test_16_get_my_appointments_preserves_db_status(self):
        res = self._create_test_appointment(25)
        # Fetch 1
        list1 = AppointmentService.get_my_appointments(self.db, self.customer_user)
        apt1 = next(a for a in list1 if a.id == res.id)
        self.assertIn(apt1.status, [AppointmentStatus.PENDING, AppointmentStatus.BOOKED, AppointmentStatus.CONFIRMED])

        # Complete
        AppointmentService.complete_consultation(self.db, res.id, current_user=self.provider_user)

        # Fetch 2
        list2 = AppointmentService.get_my_appointments(self.db, self.customer_user)
        apt2 = next(a for a in list2 if a.id == res.id)
        self.assertEqual(apt2.status, AppointmentStatus.COMPLETED)

    # 17. Unauthenticated/Guest cancellation allows canceling without token
    def test_17_guest_unauthenticated_cancellation(self):
        res = self._create_test_appointment(26)
        cancel_res = AppointmentService.cancel_appointment(
            self.db,
            res.id,
            cancel_in=AppointmentCancelRequest(reason="Guest cancellation"),
            current_user=None
        )
        self.assertEqual(cancel_res.status, AppointmentStatus.CANCELLED)

        # Verify via lookup
        found = AppointmentService.get_by_confirmation_code(self.db, res.confirmation_code, current_user=None)
        self.assertEqual(found.status, AppointmentStatus.CANCELLED)

    # 18. Unauthenticated get_appointment_by_id succeeds
    def test_18_guest_unauthenticated_get_appointment(self):
        res = self._create_test_appointment(27)
        fetched = AppointmentService.get_appointment_by_id(self.db, res.id, current_user=None)
        self.assertEqual(fetched.id, res.id)
        self.assertEqual(fetched.confirmation_code, res.confirmation_code)

if __name__ == "__main__":
    unittest.main()
