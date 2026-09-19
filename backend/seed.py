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
                "name": "District Civil Hospital, Baramati (DEMO)",
                "name_hi": "जिला नागरिक अस्पताल बारामती (डेमो)",
                "city": "Baramati",
                "area": "Baramati Town",
                "address": "Bhigwan Road, Near Municipal Council, Baramati, Maharashtra 413102",
                "latitude": 18.1517,
                "longitude": 74.5770,
                "services": "General Medicine, Pediatrics, Emergency Care, Maternity & Child Health, ICU, Vaccination",
                "contact_phone": "+91-2112-222100",
                "facility_type": "District Government Hospital"
            },
            {
                "name": "Primary Health Centre (PHC) Baramati Rural (DEMO)",
                "name_hi": "प्राथमिक स्वास्थ्य केंद्र बारामती देहात (डेमो)",
                "city": "Baramati",
                "area": "Baramati Rural",
                "address": "Gram Panchayat Road, Baramati Dehat, Maharashtra 413102",
                "latitude": 18.1650,
                "longitude": 74.5600,
                "services": "General Medicine, Immunization",
                "contact_phone": "+91-2112-224200",
                "facility_type": "Primary Health Centre (PHC)"
            },
            {
                "name": "Sub-District Hospital, Sanganer (DEMO)",
                "name_hi": "उप-जिला अस्पताल सांगानेर (डेमो)",
                "city": "Jaipur",
                "area": "Sanganer",
                "address": "Tonk Road, Near Sanganer Flyover, Jaipur 302029",
                "latitude": 26.8206,
                "longitude": 75.8075,
                "services": "General OPD, Fever Clinic, Emergency Care, Maternity & Child Health, Vaccination",
                "contact_phone": "+91-141-2700100",
                "facility_type": "Sub-District Hospital"
            },
            {
                "name": "Government Urban Health Clinic Malviya Nagar (DEMO)",
                "name_hi": "सरकारी शहरी स्वास्थ्य क्लीनिक मालवीय नगर (डेमो)",
                "city": "Jaipur",
                "area": "Malviya Nagar",
                "address": "Sector 4, Malviya Nagar, Jaipur 302017",
                "latitude": 26.8549,
                "longitude": 75.8243,
                "services": "General Medicine, Dental OPD, TB Clinic",
                "contact_phone": "+91-141-2550200",
                "facility_type": "Primary Health Centre (PHC)"
            },
            {
                "name": "Community Health Centre (CHC) Sitapura (DEMO)",
                "name_hi": "सामुदायिक स्वास्थ्य केंद्र सीतापुरा (डेमो)",
                "city": "Jaipur",
                "area": "Sitapura",
                "address": "Sitapura Industrial Area, Near RIICO, Jaipur 302022",
                "latitude": 26.7794,
                "longitude": 75.8450,
                "services": "Maternity Ward, Pediatrics, Emergency First Aid, Dental OPD",
                "contact_phone": "+91-141-2770300",
                "facility_type": "Community Health Centre (CHC)"
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
