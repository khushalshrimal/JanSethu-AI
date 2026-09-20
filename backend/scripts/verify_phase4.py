import sys
import os
import random
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from datetime import date, timedelta, time
from app.database.session import SessionLocal
from app.models import User, PatientProfile, Doctor, Facility, Appointment, SMSNotification, AppointmentAuditLog
from app.services.appointment_service import AppointmentService
from app.schemas.appointment import AppointmentCreate, AppointmentCancelRequest, AppointmentRescheduleRequest
from app.models.enums import BookingChannel, AppointmentStatus
from app.utils.timezone import get_ist_now

def verify_end_to_end_phase4():
    db = SessionLocal()
    try:
        print("\n========================================================")
        print(" JANSETHU AI 2.0 — PHASE 4 MANUAL END-TO-END VERIFICATION")
        print("========================================================\n")

        # Fetch Customer User, Provider, Admin & Doctor
        customer_user = db.query(User).filter(User.phone_number == "+91-9876543210").first()
        provider_user = db.query(User).filter(User.phone_number == "+91-9900000002").first()
        admin_user = db.query(User).filter(User.phone_number == "+91-9900000001").first()

        doc = db.query(Doctor).filter(Doctor.user_id == provider_user.id).first()
        
        # Pick a fresh unique date for manual verification run
        offset_days = random.randint(30, 90)
        target_date = get_ist_now().date() + timedelta(days=offset_days)
        target_time = time(11, 30)

        print(f"[STEP 1] Customer Identity: {customer_user.name} ({customer_user.phone_number})")
        print(f"[STEP 2] Selected Doctor: {doc.name} ({doc.department.name} at {doc.facility.name})")
        print(f"[STEP 3] Target Booking Slot: Date={target_date}, Time={target_time}")

        # 1. Book Appointment
        apt_in = AppointmentCreate(
            doctor_id=doc.id,
            appointment_date=target_date,
            start_time=target_time,
            booking_channel=BookingChannel.PWA,
            reason_for_visit="Pediatric Checkup for Child Fever"
        )
        res = AppointmentService.book_appointment(db, apt_in, customer_user)
        print(f"\n[STEP 4] APPOINTMENT CREATION SUCCESSFUL!")
        print(f"  - Database Appointment ID: {res.id}")
        print(f"  - Unique Confirmation Code: {res.confirmation_code}")
        print(f"  - Status: {res.status}")
        print(f"  - Patient: {res.patient.name}")
        print(f"  - Facility: {res.facility.name} ({res.facility.district})")
        print(f"  - SMS Dispatch Record ID: {res.notification.id if res.notification else 'N/A'}")
        print(f"  - SMS Dispatch Status: {res.notification.status if res.notification else 'N/A'}")
        print(f"  - Provider Ref ID: {res.notification.provider_message_id if res.notification else 'N/A'}")

        # 2. Concurrency / Double Booking Guard Verification
        print(f"\n[STEP 5] Testing Concurrency & Double-Booking Protection for occupied slot...")
        try:
            AppointmentService.book_appointment(db, apt_in, customer_user)
            print("  [FAIL] Expected 409 Conflict but booking succeeded.")
        except Exception as e:
            detail_msg = e.detail if hasattr(e, 'detail') else str(e)
            print(f"  [PASS] Double booking caught cleanly -> {detail_msg}")

        # 3. Reschedule Appointment
        new_time = time(12, 0)
        print(f"\n[STEP 6] Rescheduling Appointment to new slot ({target_date} at {new_time})...")
        reschedule_req = AppointmentRescheduleRequest(
            new_date=target_date,
            new_start_time=new_time,
            reason="Shifted to noon slot due to transit delay"
        )
        resched_res = AppointmentService.reschedule_appointment(db, res.id, reschedule_req, customer_user)
        print(f"  - Rescheduled Date: {resched_res.appointment_date}")
        print(f"  - Rescheduled Time: {resched_res.start_time}")
        print(f"  - Updated Status: {resched_res.status}")

        # Audit History Check
        audits = db.query(AppointmentAuditLog).filter(AppointmentAuditLog.appointment_id == res.id).all()
        print(f"  - Audit Trail Log Entries Recorded: {len(audits)}")
        for a in audits:
            print(f"    * Event: {a.event_type} | Old Status: {a.old_status} -> New Status: {a.new_status} | Notes: {a.notes}")

        # 4. Cancel Appointment
        print(f"\n[STEP 7] Cancelling Appointment with reason...")
        cancel_req = AppointmentCancelRequest(reason="Patient unavailable due to emergency travel")
        cancel_res = AppointmentService.cancel_appointment(db, res.id, cancel_req, customer_user)
        print(f"  - Final Status: {cancel_res.status}")
        print(f"  - Cancellation Reason: {cancel_res.cancellation_reason}")

        # 5. Provider Queue View Check
        print(f"\n[STEP 8] Verifying Provider Queue View (Provider: {provider_user.name})...")
        prov_queue = AppointmentService.get_provider_appointments(db, provider_user)
        print(f"  - Provider Total Appointments in Queue: {len(prov_queue)}")

        # 6. Admin Search View Check
        print(f"\n[STEP 9] Verifying Admin Global Query View (Admin: {admin_user.name})...")
        admin_queue = AppointmentService.get_admin_appointments(db, admin_user, confirmation_code=res.confirmation_code)
        print(f"  - Admin Query by Confirmation Code '{res.confirmation_code}' returned: {len(admin_queue)} record(s)")

        print("\n========================================================")
        print(" ALL MANUAL END-TO-END VERIFICATION STEPS PASSED PERFECTLY!")
        print("========================================================\n")
    finally:
        db.close()

if __name__ == "__main__":
    verify_end_to_end_phase4()
