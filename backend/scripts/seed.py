import sys
import os
from datetime import time, datetime, date

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app.database.session import SessionLocal, engine
from app.database.base import Base
from app.models import (
    User, PatientProfile, Facility, Department, Doctor, DoctorAvailability,
    DoctorScheduleException, Appointment, EmergencyContact, UserRole, FacilityType,
    Language, AppointmentStatus, BookingChannel
)

def seed_database(force_reset=True):
    print("[1/5] Initializing database schema...")
    if force_reset:
        print("[INFO] Force resetting old seed data...")
        engine.dispose()
        Base.metadata.drop_all(bind=engine)
        Base.metadata.create_all(bind=engine)
    else:
        Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        if db.query(Facility).count() > 0:
            print("[INFO] Database already seeded. Skipping initial seed.")
            db.close()
            engine.dispose()
            return

        print("[2/5] Seeding Demo Users with PBKDF2 Salted Hashes...")
        admin_user = User(
            name="System Administrator",
            phone_number="+91-9900000001",
            email="admin@jansethu.gov.in",
            password_hash=User.hash_password("AdminPass123!"),
            role=UserRole.ADMIN,
            preferred_language=Language.EN
        )
        db.add(admin_user)

        provider_user = User(
            name="Dr. Rajesh Sharma",
            phone_number="+91-9900000002",
            email="dr.sharma@baramatihosp.gov.in",
            password_hash=User.hash_password("DoctorPass123!"),
            role=UserRole.PROVIDER,
            preferred_language=Language.HI
        )
        db.add(provider_user)

        customer1 = User(
            name="Rahul Pawar",
            phone_number="+91-9876543210",
            email="rahul.pawar@demo.in",
            password_hash=User.hash_password("UserPass123!"),
            role=UserRole.CUSTOMER,
            preferred_language=Language.HI
        )
        db.add(customer1)
        db.flush()

        profile1 = PatientProfile(
            user_id=customer1.id,
            date_of_birth="1992-05-14",
            gender="Male",
            village="Baramati Rural",
            district="Pune",
            state="Maharashtra",
            pincode="413106",
            emergency_contact_name="Suresh Pawar",
            emergency_contact_phone="+91-9876500000"
        )
        db.add(profile1)

        customer2 = User(
            name="Anita Kamble",
            phone_number="+91-9822114455",
            email="anita.k@demo.in",
            password_hash=User.hash_password("UserPass123!"),
            role=UserRole.CUSTOMER,
            preferred_language=Language.MR
        )
        db.add(customer2)
        db.flush()

        profile2 = PatientProfile(
            user_id=customer2.id,
            date_of_birth="1988-11-20",
            gender="Female",
            village="Indapur Area",
            district="Pune",
            state="Maharashtra",
            pincode="413132"
        )
        db.add(profile2)

        print("[3/5] Seeding Healthcare Facilities with Geolocation...")
        fac1 = Facility(
            name="Government Sub-District Hospital, Baramati",
            facility_type=FacilityType.GOVERNMENT_HOSPITAL,
            description="100-bed government referral hospital with 24/7 Casualty & Pediatrics ICU.",
            address="Opposite ST Stand, Indapur Road",
            village="Baramati",
            district="Pune",
            state="Maharashtra",
            pincode="413106",
            latitude=18.1506,
            longitude=74.5772,
            phone_number="+91-2112-222108",
            emergency_available=True
        )
        fac2 = Facility(
            name="Primary Health Centre, Indapur",
            facility_type=FacilityType.PHC,
            description="Rural Primary Health Centre focusing on maternal immunization and general OPD.",
            address="Main Road, Near Panchayat Office",
            village="Indapur",
            district="Pune",
            state="Maharashtra",
            pincode="413132",
            latitude=18.1158,
            longitude=75.0312,
            phone_number="+91-2111-223304",
            emergency_available=False
        )
        fac3 = Facility(
            name="Community Health Centre, Malegaon Rural",
            facility_type=FacilityType.CHC,
            description="Community health facility with emergency stabilization and maternity wards.",
            address="Nira Road, Malegaon Budruk",
            village="Malegaon",
            district="Pune",
            state="Maharashtra",
            pincode="413115",
            latitude=18.1320,
            longitude=74.4980,
            phone_number="+91-2112-254100",
            emergency_available=True
        )
        fac4 = Facility(
            name="Sub-District Hospital, Daund",
            facility_type=FacilityType.GOVERNMENT_HOSPITAL,
            description="Government sub-district hospital with 24/7 emergency trauma care and general medicine OPD.",
            address="Railway Colony Road",
            village="Daund",
            district="Pune",
            state="Maharashtra",
            pincode="413801",
            latitude=18.4650,
            longitude=74.5900,
            phone_number="+91-2117-262211",
            emergency_available=True
        )
        fac5 = Facility(
            name="Primary Health Centre, Phaltan Rural",
            facility_type=FacilityType.PHC,
            description="Primary healthcare centre serving Phaltan rural cluster for immunization and maternal OPD.",
            address="Station Road, Phaltan",
            village="Phaltan",
            district="Satara",
            state="Maharashtra",
            pincode="415523",
            latitude=17.9870,
            longitude=74.4320,
            phone_number="+91-2166-220055",
            emergency_available=False
        )
        fac6 = Facility(
            name="Noble Care Multi-Specialty Clinic & Hospital",
            facility_type=FacilityType.PRIVATE_HOSPITAL,
            description="Private healthcare clinic providing orthopedic, pediatric, and general medicine consultations.",
            address="Pentanagar, Bhigwan Road",
            village="Baramati",
            district="Pune",
            state="Maharashtra",
            pincode="413102",
            latitude=18.1590,
            longitude=74.5820,
            phone_number="+91-2112-243000",
            emergency_available=True
        )
        fac7 = Facility(
            name="Government District Hospital, Jaipur",
            facility_type=FacilityType.GOVERNMENT_HOSPITAL,
            description="200-bed government referral hospital in Jaipur with 24/7 Casualty, General Medicine & Pediatrics OPD.",
            address="MI Road, Near Railway Station",
            village="Jaipur",
            district="Jaipur",
            state="Rajasthan",
            pincode="302001",
            latitude=26.9124,
            longitude=75.7873,
            phone_number="+91-141-2365108",
            emergency_available=True
        )

        db.add_all([fac1, fac2, fac3, fac4, fac5, fac6, fac7])
        db.flush()

        print("[4/5] Seeding Departments, Doctors & Availabilities...")
        dept_peds = Department(facility_id=fac1.id, name="Pediatrics", description="Child Specialist & OPD")
        dept_gen = Department(facility_id=fac1.id, name="General Medicine", description="General OPD & Fever Clinic")
        dept_ortho = Department(facility_id=fac1.id, name="Orthopedics", description="Bone & Joint OPD")
        dept_gyn = Department(facility_id=fac1.id, name="Gynecology & Maternity", description="Maternal Care & Labor Ward")
        dept_emg = Department(facility_id=fac1.id, name="Emergency & Casualty", description="24/7 Trauma & Resuscitation")
        
        dept_phc_gen = Department(facility_id=fac2.id, name="General OPD", description="Primary Healthcare & Immunization")
        dept_phc_mat = Department(facility_id=fac2.id, name="Maternal Care", description="Antenatal & Postnatal Care")

        dept_chc_gen = Department(facility_id=fac3.id, name="General Medicine", description="CHC General OPD")
        dept_chc_peds = Department(facility_id=fac3.id, name="Pediatrics", description="Child Care Unit")

        dept_daund_gen = Department(facility_id=fac4.id, name="General Medicine", description="Daund General OPD")
        dept_noble_gen = Department(facility_id=fac6.id, name="General Medicine & Surgery", description="Private OPD Clinic")
        dept_jaipur_gen = Department(facility_id=fac7.id, name="General Medicine", description="Jaipur General OPD & Fever Clinic")

        db.add_all([
            dept_peds, dept_gen, dept_ortho, dept_gyn, dept_emg,
            dept_phc_gen, dept_phc_mat, dept_chc_gen, dept_chc_peds,
            dept_daund_gen, dept_noble_gen, dept_jaipur_gen
        ])
        db.flush()

        doc1 = Doctor(
            user_id=provider_user.id,
            facility_id=fac1.id,
            department_id=dept_peds.id,
            name="Dr. Rajesh Sharma",
            qualification="MD (Pediatrics)",
            specialization="Child Specialist",
            phone_number="+91-9900000002"
        )
        doc_jaipur = Doctor(
            facility_id=fac7.id,
            department_id=dept_jaipur_gen.id,
            name="Dr. Amit Sharma",
            qualification="MD (General Medicine)",
            specialization="Physician & Fever Specialist",
            phone_number="+91-141-99887766"
        )
        doc2 = Doctor(
            facility_id=fac1.id,
            department_id=dept_ortho.id,
            name="Dr. Priya Patil",
            qualification="MS (Orthopedics)",
            specialization="Orthopedic Surgeon"
        )
        doc3 = Doctor(
            facility_id=fac1.id,
            department_id=dept_gen.id,
            name="Dr. Amit Kulkarni",
            qualification="MD (General Medicine)",
            specialization="Consultant Physician"
        )
        doc4 = Doctor(
            facility_id=fac3.id,
            department_id=dept_chc_peds.id,
            name="Dr. Sunita Deshmukh",
            qualification="MD (Pediatrics)",
            specialization="Pediatrician"
        )
        doc5 = Doctor(
            facility_id=fac2.id,
            department_id=dept_phc_gen.id,
            name="Dr. Anil Deshmukh",
            qualification="MBBS",
            specialization="Rural Medical Officer"
        )
        doc6 = Doctor(
            facility_id=fac2.id,
            department_id=dept_phc_mat.id,
            name="Dr. Vaishali Shinde",
            qualification="DGO",
            specialization="Maternal Care Specialist"
        )
        doc7 = Doctor(
            facility_id=fac4.id,
            department_id=dept_daund_gen.id,
            name="Dr. Ramesh Jadhav",
            qualification="MD (Internal Medicine)",
            specialization="General Physician"
        )
        doc8 = Doctor(
            facility_id=fac6.id,
            department_id=dept_noble_gen.id,
            name="Dr. Nitin More",
            qualification="MS (General Surgery)",
            specialization="Surgeon & Consultant"
        )

        db.add_all([doc1, doc_jaipur, doc2, doc3, doc4, doc5, doc6, doc7, doc8])
        db.flush()

        # Recurring Availabilities (Mon - Sun, 09:00 AM - 01:00 PM)
        for doc in [doc1, doc_jaipur, doc2, doc3, doc4, doc5, doc6, doc7, doc8]:
            for day in range(0, 7): # All 7 days of the week
                avail = DoctorAvailability(
                    doctor_id=doc.id,
                    day_of_week=day,
                    start_time=time(9, 0),
                    end_time=time(13, 0),
                    slot_duration_minutes=30
                )
                db.add(avail)

        # Seed Doctor Schedule Exception (Doctor 1 Leave / Emergency Duty on 2026-10-25)
        exc1 = DoctorScheduleException(
            doctor_id=doc1.id,
            date=date(2026, 10, 25),
            start_time=time(10, 0),
            end_time=time(11, 30),
            reason="Emergency Casualty & Hospital Inspection Duty"
        )
        db.add(exc1)

        # Seed Confirmed/Booked Appointment for Dr. Sharma on 2026-10-25 at 09:00 AM
        apt1 = Appointment(
            patient_id=profile1.id,
            doctor_id=doc1.id,
            facility_id=fac1.id,
            department_id=dept_peds.id,
            appointment_date=date(2026, 10, 25),
            start_time=time(9, 0),
            end_time=time(9, 30),
            status=AppointmentStatus.BOOKED,
            booking_channel=BookingChannel.PWA,
            reason_for_visit="Pediatric Consultation for Child Fever",
            confirmation_code="JS-2026-SEED101"
        )
        db.add(apt1)

        # Seed Cancelled Appointment for Dr. Sharma on 2026-10-26 at 11:30 AM
        apt2 = Appointment(
            patient_id=profile1.id,
            doctor_id=doc1.id,
            facility_id=fac1.id,
            department_id=dept_peds.id,
            appointment_date=date(2026, 10, 26),
            start_time=time(11, 30),
            end_time=time(12, 0),
            status=AppointmentStatus.CANCELLED,
            cancellation_reason="Patient was out of town",
            cancelled_at=datetime.utcnow(),
            booking_channel=BookingChannel.PHONE,
            reason_for_visit="Routine child checkup",
            confirmation_code="JS-2026-SEED102"
        )
        db.add(apt2)

        # Seed Completed Appointment for Dr. Patel on 2026-09-15 at 10:00 AM
        apt3 = Appointment(
            patient_id=profile2.id,
            doctor_id=doc2.id,
            facility_id=fac1.id,
            department_id=dept_gen.id,
            appointment_date=date(2026, 9, 15),
            start_time=time(10, 0),
            end_time=time(10, 30),
            status=AppointmentStatus.COMPLETED,
            booking_channel=BookingChannel.PWA,
            reason_for_visit="General Health Checkup",
            confirmation_code="JS-2026-SEED103"
        )
        db.add(apt3)

        print("[5/5] Seeding Emergency Contacts...")
        emg1 = EmergencyContact(facility_id=fac1.id, name="Baramati 108 Ambulance Dispatch", phone_number="108", contact_type="AMBULANCE", priority=1)
        emg2 = EmergencyContact(facility_id=fac1.id, name="Hospital Casualty Desk", phone_number="+91-2112-222108", contact_type="CASUALTY", priority=2)
        emg3 = EmergencyContact(facility_id=fac3.id, name="Malegaon CHC Ambulance", phone_number="108", contact_type="AMBULANCE", priority=1)
        db.add_all([emg1, emg2, emg3])

        db.commit()
        print("[SUCCESS] Database re-seeded with facilities, doctors, 7-day schedules, exceptions & sample appointments!")
    except Exception as e:
        db.rollback()
        print("[ERROR] Database seeding failed:", e)
        raise e
    finally:
        db.close()
        engine.dispose()

if __name__ == "__main__":
    seed_database(force_reset=True)
