import datetime
from database import engine, SessionLocal, Base
import models

def seed_database():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()

    try:
        # Sample Facilities (Clearly marked DEMO data)
        facilities_data = [
            {
                "name": "District Civil Hospital (DEMO)",
                "name_hi": "जिला नागरिक अस्पताल (डेमो)",
                "city": "Jaipur",
                "area": "Sanganer",
                "address": "Tonk Road, Near Sanganer Flyover, Jaipur, Rajasthan 302029",
                "latitude": 26.8206,
                "longitude": 75.8075,
                "services": "General OPD, Fever Clinic, Emergency Care, Maternity & Child Health, Vaccination, Diagnostics",
                "contact_phone": "+91-141-2700100",
                "facility_type": "District Government Hospital"
            },
            {
                "name": "Primary Health Centre (PHC) Malviya Nagar (DEMO)",
                "name_hi": "प्राथमिक स्वास्थ्य केंद्र मालवीय नगर (डेमो)",
                "city": "Jaipur",
                "area": "Malviya Nagar",
                "address": "Sector 4, Malviya Nagar, Jaipur, Rajasthan 302017",
                "latitude": 26.8549,
                "longitude": 75.8243,
                "services": "General Medicine, Child Immunization, Basic Health Checkup, TB Clinic, Free Medicines",
                "contact_phone": "+91-141-2550200",
                "facility_type": "Primary Health Centre (PHC)"
            },
            {
                "name": "Community Health Centre (CHC) Chokhi Dhani Area (DEMO)",
                "name_hi": "सामुदायिक स्वास्थ्य केंद्र चौखी ढाणी क्षेत्र (डेमो)",
                "city": "Jaipur",
                "area": "Sitapura",
                "address": "Sitapura Industrial Area, Near RIICO, Jaipur 302022",
                "latitude": 26.7794,
                "longitude": 75.8450,
                "services": "Maternity Ward, Pediatrics, Emergency First Aid, Dental OPD, Eye Checkup",
                "contact_phone": "+91-141-2770300",
                "facility_type": "Community Health Centre (CHC)"
            },
            {
                "name": "JanSethu Mobile Health Van Station #1 (DEMO)",
                "name_hi": "जनसेतु मोबाइल स्वास्थ्य वैन स्टेशन #1 (डेमो)",
                "city": "Jaipur",
                "area": "Pratap Nagar",
                "address": "Kumbha Marg Bus Stand, Pratap Nagar, Jaipur",
                "latitude": 26.7938,
                "longitude": 75.8152,
                "services": "Mobile Doctor Unit, Free Blood Pressure & Sugar Check, Essential Medicines Distribution",
                "contact_phone": "+91-98290-11223",
                "facility_type": "Mobile Clinic"
            },
            {
                "name": "Government Sub-District Hospital (DEMO)",
                "name_hi": "सरकारी उप-जिला अस्पताल (डेमो)",
                "city": "New Delhi",
                "area": "Mehrauli",
                "address": "Main Road Mehrauli, Near Bus Terminal, New Delhi 110030",
                "latitude": 28.5204,
                "longitude": 77.1855,
                "services": "General Physician, Emergency First Aid, Orthopedics, Fever & Viral OPD, X-Ray",
                "contact_phone": "+91-11-2664010",
                "facility_type": "Sub-District Hospital"
            }
        ]

        created_facilities = []
        for f_data in facilities_data:
            fac = models.Facility(**f_data)
            db.add(fac)
            db.flush()
            created_facilities.append(fac)

        # Dates for slots (Today, Tomorrow, Day After)
        today = datetime.date.today()
        dates = [
            today.strftime("%Y-%m-%d"),
            (today + datetime.timedelta(days=1)).strftime("%Y-%m-%d"),
            (today + datetime.timedelta(days=2)).strftime("%Y-%m-%d")
        ]

        times = ["09:00 AM", "10:30 AM", "11:45 AM", "02:00 PM", "03:30 PM", "04:30 PM"]
        departments = [
            ("General Physician / OPD", "Dr. Rajesh Sharma"),
            ("Pediatrics / Child Specialist", "Dr. Sunita Verma"),
            ("Maternity & Gynaecology", "Dr. Anita Gupta"),
            ("Fever & Viral Care", "Dr. Manoj Kumar"),
            ("Dental Clinic", "Dr. Pooja Yadav")
        ]

        # Add slots for each facility
        for fac in created_facilities:
            for d in dates:
                for idx, t in enumerate(times):
                    dept, doc = departments[idx % len(departments)]
                    slot = models.Slot(
                        facility_id=fac.id,
                        date=d,
                        time=t,
                        available=(idx % 2 == 0 or idx == 1), # Some available, some booked
                        doctor_name=doc,
                        department=dept
                    )
                    db.add(slot)

        # Add initial sample appointment request
        sample_appointment = models.Appointment(
            facility_id=created_facilities[0].id,
            service="General OPD",
            date=dates[1],
            time="10:30 AM",
            patient_name="Ram Lal (DEMO)",
            phone="+91-9876543210",
            status="pending",
            created_at=datetime.datetime.utcnow()
        )
        db.add(sample_appointment)

        db.commit()
        print(f"Database seeded successfully with {len(created_facilities)} facilities and associated slots!")
    except Exception as e:
        db.rollback()
        print(f"Error seeding database: {e}")
        raise e
    finally:
        db.close()

if __name__ == "__main__":
    seed_database()
