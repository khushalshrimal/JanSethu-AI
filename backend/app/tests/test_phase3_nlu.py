import unittest
import pytest
from app.services.llm_service import DeterministicNLUParser, LLMService
from app.services.conversation_manager import ConversationManager
from app.schemas.conversation import ConversationRequest
from app.schemas.nlu import NLUIntent
from app.models.enums import Language
from scripts.seed import seed_database


class TestPhase3NLU(unittest.IsolatedAsyncioTestCase):
    """
    Comprehensive Phase 3 LLM / NLU Agent Test Suite for JanSethu AI.
    Contains 150+ unit and integration tests across English, Hindi, Hinglish, and Marathi.
    Validates structured intent classification, multi-entity extraction, confidence handling,
    deterministic safety preemption, multi-turn state retention, dynamic clarification, and zero hallucination.
    """

    @classmethod
    def setUpClass(cls):
        seed_database(force_reset=True)

    def setUp(self):
        ConversationManager.clear_all_sessions()

    # =========================================================================
    # PART 1: 50+ ENGLISH NLU TEST CASES
    # =========================================================================

    def test_en_01_greeting(self):
        res = DeterministicNLUParser.parse("Hello, good morning!")
        self.assertEqual(res.intent, NLUIntent.GENERAL_GREETING)

    def test_en_02_provide_name(self):
        res = DeterministicNLUParser.parse("My name is Ramesh")
        self.assertEqual(res.entities.patient_name, "Ramesh")

    def test_en_03_find_specialist_dermatology(self):
        res = DeterministicNLUParser.parse("I need a skin doctor in Baramati")
        self.assertIn(res.intent, [NLUIntent.FIND_SPECIALIST, NLUIntent.FIND_DOCTOR])
        self.assertEqual(res.entities.specialty, "Dermatology")
        self.assertEqual(res.entities.location, "Baramati")

    def test_en_04_find_specialist_pediatrics(self):
        res = DeterministicNLUParser.parse("Looking for a child doctor near Pune")
        self.assertIn(res.intent, [NLUIntent.FIND_SPECIALIST, NLUIntent.FIND_DOCTOR])
        self.assertEqual(res.entities.specialty, "Pediatrics")
        self.assertEqual(res.entities.location, "Pune")

    def test_en_05_find_specialist_orthopedics(self):
        res = DeterministicNLUParser.parse("I need an bone specialist for knee pain")
        self.assertEqual(res.entities.specialty, "Orthopedics")

    def test_en_06_find_facility_pincode(self):
        res = DeterministicNLUParser.parse("Find hospital near 413106")
        self.assertIn(res.intent, [NLUIntent.FIND_FACILITY, NLUIntent.FACILITY_SEARCH])
        self.assertEqual(res.entities.pincode, "413106")

    def test_en_07_emergency_breathing(self):
        res = DeterministicNLUParser.parse("My father is having severe shortness of breath")
        self.assertTrue(res.emergency)
        self.assertEqual(res.intent, NLUIntent.EMERGENCY)

    def test_en_08_emergency_chest_pain(self):
        res = DeterministicNLUParser.parse("I have severe chest pain and dizziness")
        self.assertTrue(res.emergency)
        self.assertEqual(res.intent, NLUIntent.EMERGENCY)

    def test_en_09_emergency_ambulance_108(self):
        res = DeterministicNLUParser.parse("Need an emergency 108 ambulance right now")
        self.assertTrue(res.emergency)
        self.assertTrue(res.entities.ambulance_requested)

    def test_en_10_book_appointment_tomorrow(self):
        res = DeterministicNLUParser.parse("Book an appointment for tomorrow at 4 PM")
        self.assertIn(res.intent, [NLUIntent.BOOK_APPOINTMENT, NLUIntent.SLOT_SEARCH])
        self.assertEqual(res.entities.date, "tomorrow")
        self.assertEqual(res.entities.time, "16:00")

    def test_en_11_check_my_appointments(self):
        res = DeterministicNLUParser.parse("Show my active appointments")
        self.assertEqual(res.intent, NLUIntent.MY_APPOINTMENTS)

    def test_en_12_cancel_appointment(self):
        res = DeterministicNLUParser.parse("Cancel my appointment")
        self.assertEqual(res.intent, NLUIntent.CANCEL_APPOINTMENT)

    def test_en_13_reschedule_appointment(self):
        res = DeterministicNLUParser.parse("Reschedule my appointment to tomorrow")
        self.assertEqual(res.intent, NLUIntent.RESCHEDULE_APPOINTMENT)
        self.assertEqual(res.entities.date, "tomorrow")

    def test_en_14_language_change_hindi(self):
        res = DeterministicNLUParser.parse("Switch language to Hindi")
        self.assertEqual(res.intent, NLUIntent.LANGUAGE_CHANGE)

    def test_en_15_thank_you(self):
        res = DeterministicNLUParser.parse("Thank you so much for your help")
        self.assertEqual(res.intent, NLUIntent.THANK_YOU)

    def test_en_16_goodbye(self):
        res = DeterministicNLUParser.parse("Goodbye, have a great day")
        self.assertEqual(res.intent, NLUIntent.GOODBYE)

    def test_en_17_gynecology_search(self):
        res = DeterministicNLUParser.parse("Need a maternity women doctor in Satara")
        self.assertEqual(res.entities.specialty, "Gynecology")
        self.assertEqual(res.entities.location, "Satara")

    def test_en_18_ent_specialist(self):
        res = DeterministicNLUParser.parse("Looking for an ENT throat specialist")
        self.assertEqual(res.entities.specialty, "ENT")

    def test_en_19_cardiology_search(self):
        res = DeterministicNLUParser.parse("Search for a heart doctor in Pune")
        self.assertEqual(res.entities.specialty, "Cardiology")
        self.assertEqual(res.entities.location, "Pune")

    def test_en_20_general_medicine(self):
        res = DeterministicNLUParser.parse("I have fever and headache")
        self.assertEqual(res.entities.specialty, "General Medicine")
        self.assertIn("fever", res.entities.symptoms)

    def test_en_21_provide_location_standalone(self):
        res = DeterministicNLUParser.parse("Baramati")
        self.assertEqual(res.entities.location, "Baramati")

    def test_en_22_doctor_name_extraction(self):
        res = DeterministicNLUParser.parse("Check availability for Dr. Rajesh Sharma")
        self.assertEqual(res.entities.doctor_name, "Dr. Rajesh Sharma")

    def test_en_23_facility_name_extraction(self):
        res = DeterministicNLUParser.parse("Show doctors in Baramati Hospital")
        self.assertEqual(res.entities.facility_name, "Baramati Hospital")

    def test_en_24_accident_emergency(self):
        res = DeterministicNLUParser.parse("Road accident near bus stand, send help")
        self.assertTrue(res.emergency)

    def test_en_25_unconscious_emergency(self):
        res = DeterministicNLUParser.parse("Patient is unconscious and not responding")
        self.assertTrue(res.emergency)

    def test_en_26_severe_bleeding_emergency(self):
        res = DeterministicNLUParser.parse("Heavy bleeding after injury")
        self.assertTrue(res.emergency)

    def test_en_27_phc_search(self):
        res = DeterministicNLUParser.parse("Find PHC near Indapur")
        self.assertEqual(res.entities.facility_type, "PHC")
        self.assertEqual(res.entities.location, "Indapur")

    def test_en_28_chc_search(self):
        res = DeterministicNLUParser.parse("Where is the CHC in Baramati?")
        self.assertEqual(res.entities.facility_type, "CHC")

    def test_en_29_sub_district_hospital(self):
        res = DeterministicNLUParser.parse("Find District Hospital in Pune")
        self.assertEqual(res.entities.facility_type, "DISTRICT_HOSPITAL")

    def test_en_30_morning_time_period(self):
        res = DeterministicNLUParser.parse("Need morning slot tomorrow")
        self.assertEqual(res.entities.time_period, "morning")
        self.assertEqual(res.entities.date, "tomorrow")

    def test_en_31_afternoon_time_period(self):
        res = DeterministicNLUParser.parse("Available afternoon slots today")
        self.assertEqual(res.entities.time_period, "afternoon")
        self.assertEqual(res.entities.date, "today")

    def test_en_32_evening_time_period(self):
        res = DeterministicNLUParser.parse("Evening doctor timing")
        self.assertEqual(res.entities.time_period, "evening")

    def test_en_33_referral_id_lookup(self):
        res = DeterministicNLUParser.parse("Check referral JS-2026-ABCDEF")
        self.assertEqual(res.entities.referral_id, "JS-2026-ABCDEF")

    def test_en_34_confirm_booking_yes(self):
        res = DeterministicNLUParser.parse("Yes, confirm the appointment")
        self.assertIn(res.intent, [NLUIntent.CONFIRM_APPOINTMENT, NLUIntent.BOOK_APPOINTMENT])

    def test_en_35_correction_phrase(self):
        res = DeterministicNLUParser.parse("No, not Pune, Baramati")
        self.assertTrue(res.entities.is_correction)

    def test_en_36_ambiguous_doctor(self):
        res = DeterministicNLUParser.parse("I need a doctor")
        self.assertIn(res.intent, [NLUIntent.FIND_DOCTOR, NLUIntent.DOCTOR_SEARCH, NLUIntent.UNKNOWN])

    def test_en_37_ambiguous_hospital(self):
        res = DeterministicNLUParser.parse("Find a hospital")
        self.assertIn(res.intent, [NLUIntent.FIND_FACILITY, NLUIntent.FACILITY_SEARCH])

    def test_en_38_today_date(self):
        res = DeterministicNLUParser.parse("Slot for today")
        self.assertEqual(res.entities.date, "today")

    def test_en_39_day_after_tomorrow(self):
        res = DeterministicNLUParser.parse("Book day after tomorrow")
        self.assertEqual(res.entities.date, "day_after_tomorrow")

    def test_en_40_medical_help(self):
        res = DeterministicNLUParser.parse("How can JanSethu help me?")
        self.assertEqual(res.intent, NLUIntent.MEDICAL_HELP)

    def test_en_41_patient_relation_mother(self):
        res = DeterministicNLUParser.parse("Doctor for my mother")
        self.assertEqual(res.entities.patient_relation, "mother")

    def test_en_42_patient_relation_child(self):
        res = DeterministicNLUParser.parse("Doctor for my baby")
        self.assertEqual(res.entities.patient_relation, "child")

    def test_en_43_solapur_location(self):
        res = DeterministicNLUParser.parse("Hospitals in Solapur")
        self.assertEqual(res.entities.location, "Solapur")

    def test_en_44_nashik_location(self):
        res = DeterministicNLUParser.parse("Pediatrician in Nashik")
        self.assertEqual(res.entities.location, "Nashik")

    def test_en_45_kolhapur_location(self):
        res = DeterministicNLUParser.parse("Dermatologist in Kolhapur")
        self.assertEqual(res.entities.location, "Kolhapur")

    def test_en_46_sangavi_location(self):
        res = DeterministicNLUParser.parse("Skin clinic in Sangavi area")
        self.assertEqual(res.entities.location, "Sangavi")

    def test_en_47_unknown_query(self):
        res = DeterministicNLUParser.parse("xyz123 random words")
        self.assertEqual(res.intent, NLUIntent.UNKNOWN)

    def test_en_48_slot_time_explicit(self):
        res = DeterministicNLUParser.parse("Book 10:30 AM slot")
        self.assertEqual(res.entities.time, "10:30")

    def test_en_49_emergency_override_priority(self):
        res = DeterministicNLUParser.parse("Emergency! I need doctor for chest pain")
        self.assertTrue(res.emergency)
        self.assertEqual(res.intent, NLUIntent.EMERGENCY)

    def test_en_50_language_change_marathi(self):
        res = DeterministicNLUParser.parse("Change language to Marathi")
        self.assertEqual(res.intent, NLUIntent.LANGUAGE_CHANGE)

    def test_en_51_patient_relation_father(self):
        res = DeterministicNLUParser.parse("My father needs a doctor")
        self.assertEqual(res.entities.patient_relation, "father")

    def test_en_52_dental_specialist(self):
        res = DeterministicNLUParser.parse("Need dentist for tooth pain")
        self.assertEqual(res.entities.specialty, "Dentistry")

    # =========================================================================
    # PART 2: 50+ HINDI / HINGLISH NLU TEST CASES
    # =========================================================================

    def test_hi_01_greeting(self):
        res = DeterministicNLUParser.parse("नमस्ते, जनसेतु में आपका स्वागत है")
        self.assertEqual(res.language, Language.HI)
        self.assertEqual(res.intent, NLUIntent.GENERAL_GREETING)

    def test_hi_02_provide_name(self):
        res = DeterministicNLUParser.parse("मेरा नाम रमेश है")
        self.assertEqual(res.entities.patient_name, "Ramesh")

    def test_hi_03_find_specialist_hinglish(self):
        res = DeterministicNLUParser.parse("Mujhe skin ka doctor chahiye")
        self.assertEqual(res.entities.specialty, "Dermatology")

    def test_hi_04_find_specialist_hindi_script(self):
        res = DeterministicNLUParser.parse("मुझे त्वचा के डॉक्टर की जरूरत है।")
        self.assertEqual(res.entities.specialty, "Dermatology")

    def test_hi_05_location_query(self):
        res = DeterministicNLUParser.parse("Baramati ke paas koi hospital hai?")
        self.assertEqual(res.entities.location, "Baramati")
        self.assertIn(res.intent, [NLUIntent.FIND_FACILITY, NLUIntent.FACILITY_SEARCH])

    def test_hi_06_mother_doctor_tomorrow(self):
        res = DeterministicNLUParser.parse("Meri maa ko kal doctor ko dikhana hai.")
        self.assertEqual(res.entities.patient_relation, "mother")
        self.assertEqual(res.entities.date, "tomorrow")

    def test_hi_07_emergency_breathing(self):
        res = DeterministicNLUParser.parse("Mere papa ko saans lene mein bahut dikkat ho rahi hai.")
        self.assertTrue(res.emergency)
        self.assertEqual(res.intent, NLUIntent.EMERGENCY)
        self.assertEqual(res.entities.patient_relation, "father")

    def test_hi_08_emergency_explicit(self):
        res = DeterministicNLUParser.parse("Emergency hai, jaldi ambulance bhejo!")
        self.assertTrue(res.emergency)

    def test_hi_09_emergency_hindi_script(self):
        res = DeterministicNLUParser.parse("मेरे पापा को सांस नहीं आ रही।")
        self.assertTrue(res.emergency)

    def test_hi_10_kal_4_baje_appointment(self):
        res = DeterministicNLUParser.parse("Kal 4 baje doctor chahiye.")
        self.assertEqual(res.entities.date, "tomorrow")
        self.assertEqual(res.entities.time, "16:00")

    def test_hi_11_pediatrics_hinglish(self):
        res = DeterministicNLUParser.parse("Bachon ke doctor ki zarurat hai")
        self.assertEqual(res.entities.specialty, "Pediatrics")

    def test_hi_12_orthopedics_hinglish(self):
        res = DeterministicNLUParser.parse("Haddi ke doctor ko dikhana hai")
        self.assertEqual(res.entities.specialty, "Orthopedics")

    def test_hi_13_gynecology_hinglish(self):
        res = DeterministicNLUParser.parse("Mahila doctor chahiye pregnant patient ke liye")
        self.assertEqual(res.entities.specialty, "Gynecology")

    def test_hi_14_fever_general_medicine(self):
        res = DeterministicNLUParser.parse("Mujhe तेज bukhar aur sar dard hai")
        self.assertEqual(res.entities.specialty, "General Medicine")

    def test_hi_15_chest_pain_emergency(self):
        res = DeterministicNLUParser.parse("Seene mein bahut tez dard ho raha hai")
        self.assertTrue(res.emergency)

    def test_hi_16_bleeding_emergency(self):
        res = DeterministicNLUParser.parse("Bahut zyada khoon nikal raha hai")
        self.assertTrue(res.emergency)

    def test_hi_17_behosh_emergency(self):
        res = DeterministicNLUParser.parse("Patient behosh ho gaya hai")
        self.assertTrue(res.emergency)

    def test_hi_18_pune_location(self):
        res = DeterministicNLUParser.parse("Pune mein accha hospital batao")
        self.assertEqual(res.entities.location, "Pune")

    def test_hi_19_indapur_location(self):
        res = DeterministicNLUParser.parse("Indapur mein doctor chahiye")
        self.assertEqual(res.entities.location, "Indapur")

    def test_hi_20_satara_location(self):
        res = DeterministicNLUParser.parse("Satara mein clinic hai kya?")
        self.assertEqual(res.entities.location, "Satara")

    def test_hi_21_doctor_availability_check(self):
        res = DeterministicNLUParser.parse("Dr. Rajesh Sharma kab available hain?")
        self.assertEqual(res.entities.doctor_name, "Dr. Rajesh Sharma")
        self.assertIn(res.intent, [NLUIntent.CHECK_AVAILABILITY, NLUIntent.DOCTOR_AVAILABILITY])

    def test_hi_22_my_appointments(self):
        res = DeterministicNLUParser.parse("Meri appointment dekho")
        self.assertEqual(res.intent, NLUIntent.MY_APPOINTMENTS)

    def test_hi_23_cancel_appointment(self):
        res = DeterministicNLUParser.parse("Appointment cancel kar do")
        self.assertEqual(res.intent, NLUIntent.CANCEL_APPOINTMENT)

    def test_hi_24_confirm_booking(self):
        res = DeterministicNLUParser.parse("Haan, confirm kar do")
        self.assertIn(res.intent, [NLUIntent.CONFIRM_APPOINTMENT, NLUIntent.BOOK_APPOINTMENT])

    def test_hi_25_subah_time_period(self):
        res = DeterministicNLUParser.parse("Kal subah ka slot chahiye")
        self.assertEqual(res.entities.date, "tomorrow")
        self.assertEqual(res.entities.time_period, "morning")

    def test_hi_26_shaam_time_period(self):
        res = DeterministicNLUParser.parse("Aaj shaam doctor milenge?")
        self.assertEqual(res.entities.date, "today")
        self.assertEqual(res.entities.time_period, "evening")

    def test_hi_27_dopahar_time_period(self):
        res = DeterministicNLUParser.parse("Dopahar mein appointment chahiye")
        self.assertEqual(res.entities.time_period, "afternoon")

    def test_hi_28_dhanyawad_thanks(self):
        res = DeterministicNLUParser.parse("Bahut bahut dhanyawad")
        self.assertEqual(res.intent, NLUIntent.THANK_YOU)

    def test_hi_29_alvida_goodbye(self):
        res = DeterministicNLUParser.parse("Alvida, phir milenge")
        self.assertEqual(res.intent, NLUIntent.GOODBYE)

    def test_hi_30_correction_location(self):
        res = DeterministicNLUParser.parse("Nahi, Jaipur nahi Ajmer")
        self.assertTrue(res.entities.is_correction)
        self.assertEqual(res.entities.city, "Ajmer")

    def test_hi_31_pincode_extraction(self):
        res = DeterministicNLUParser.parse("Hospital near pincode 413102")
        self.assertEqual(res.entities.pincode, "413102")

    def test_hi_32_eye_doctor(self):
        res = DeterministicNLUParser.parse("Aankh ke doctor ko dikhana hai")
        self.assertEqual(res.entities.specialty, "Ophthalmology")

    def test_hi_33_dental_doctor(self):
        res = DeterministicNLUParser.parse("Daant ke doctor chahiye")
        self.assertEqual(res.entities.specialty, "Dentistry")

    def test_hi_34_phc_hospital_query(self):
        res = DeterministicNLUParser.parse("Baramati ka PHC hospital kahan hai?")
        self.assertEqual(res.entities.facility_type, "PHC")
        self.assertEqual(res.entities.location, "Baramati")

    def test_hi_35_chc_hospital_query(self):
        res = DeterministicNLUParser.parse("Indapur CHC hospital mein doctor hain?")
        self.assertEqual(res.entities.facility_type, "CHC")
        self.assertEqual(res.entities.location, "Indapur")

    def test_hi_36_government_hospital(self):
        res = DeterministicNLUParser.parse("Government hospital mein appointment chahiye")
        self.assertEqual(res.entities.facility_type, "DISTRICT_HOSPITAL")

    def test_hi_37_doctor_chahiye_ambiguous(self):
        res = DeterministicNLUParser.parse("Doctor chahiye.")
        self.assertIn(res.intent, [NLUIntent.FIND_DOCTOR, NLUIntent.DOCTOR_SEARCH, NLUIntent.UNKNOWN])

    def test_hi_38_hospital_chahiye_ambiguous(self):
        res = DeterministicNLUParser.parse("Hospital chahiye.")
        self.assertIn(res.intent, [NLUIntent.FIND_FACILITY, NLUIntent.FACILITY_SEARCH])

    def test_hi_39_108_call(self):
        res = DeterministicNLUParser.parse("108 ko call karo, emergency hai")
        self.assertTrue(res.emergency)
        self.assertTrue(res.entities.ambulance_requested)

    def test_hi_40_parso_date(self):
        res = DeterministicNLUParser.parse("Parso ka appointment chahiye")
        self.assertEqual(res.entities.date, "day_after_tomorrow")

    def test_hi_41_reschedule_time(self):
        res = DeterministicNLUParser.parse("Time badlo kal ke liye")
        self.assertEqual(res.intent, NLUIntent.RESCHEDULE_APPOINTMENT)

    def test_hi_42_referral_code_hindi(self):
        res = DeterministicNLUParser.parse("Mera referral ID hai JS-2026-XYZ123")
        self.assertEqual(res.entities.referral_id, "JS-2026-XYZ123")

    def test_hi_43_pet_dard_general_medicine(self):
        res = DeterministicNLUParser.parse("Pet dard ke liye doctor chahiye")
        self.assertEqual(res.entities.specialty, "General Medicine")
        self.assertIn("pet dard", res.entities.symptoms)

    def test_hi_44_khansi_cold(self):
        res = DeterministicNLUParser.parse("Khansi aur cold ki dawa ke liye physician")
        self.assertEqual(res.entities.specialty, "General Medicine")

    def test_hi_45_english_language_switch(self):
        res = DeterministicNLUParser.parse("English mein baat karo")
        self.assertEqual(res.intent, NLUIntent.LANGUAGE_CHANGE)

    def test_hi_46_marathi_language_switch(self):
        res = DeterministicNLUParser.parse("Marathi mein batao")
        self.assertEqual(res.intent, NLUIntent.LANGUAGE_CHANGE)

    def test_hi_47_address_batao(self):
        res = DeterministicNLUParser.parse("Baramati hospital ka address batao")
        self.assertEqual(res.entities.location, "Baramati")

    def test_hi_48_is_correction_city(self):
        res = DeterministicNLUParser.parse("Badlo city Pune karo")
        self.assertTrue(res.entities.is_correction)

    def test_hi_49_bache_ka_doctor(self):
        res = DeterministicNLUParser.parse("Chote bache ka doctor Baramati mein")
        self.assertEqual(res.entities.specialty, "Pediatrics")
        self.assertEqual(res.entities.location, "Baramati")

    def test_hi_50_haddi_doctor_indapur(self):
        res = DeterministicNLUParser.parse("Haddi ka doctor Indapur mein hai kya?")
        self.assertEqual(res.entities.specialty, "Orthopedics")
        self.assertEqual(res.entities.location, "Indapur")

    def test_hi_51_serious_problem_emergency(self):
        res = DeterministicNLUParser.parse("Bahut serious problem hai, jaldi help bhejo")
        self.assertTrue(res.emergency)

    def test_hi_52_mera_naam_rahul(self):
        res = DeterministicNLUParser.parse("Mera naam Rahul hai")
        self.assertEqual(res.entities.patient_name, "Rahul")

    # =========================================================================
    # PART 3: 50+ MARATHI NLU TEST CASES
    # =========================================================================

    def test_mr_01_marathi_language_detection(self):
        res = DeterministicNLUParser.parse("मला त्वचारोग तज्ज्ञ हवा आहे.")
        self.assertEqual(res.language, Language.MR)

    def test_mr_02_find_specialist_dermatology(self):
        res = DeterministicNLUParser.parse("मला त्वचारोग तज्ज्ञ हवा आहे.")
        self.assertEqual(res.entities.specialty, "Dermatology")

    def test_mr_03_emergency_breathing(self):
        res = DeterministicNLUParser.parse("माझ्या वडिलांना श्वास घेण्यास त्रास होत आहे.")
        self.assertTrue(res.emergency)
        self.assertEqual(res.intent, NLUIntent.EMERGENCY)

    def test_mr_04_appointment_request(self):
        res = DeterministicNLUParser.parse("मला डॉक्टरची अपॉइंटमेंट हवी आहे.")
        self.assertIn(res.intent, [NLUIntent.BOOK_APPOINTMENT, NLUIntent.FIND_DOCTOR])

    def test_mr_05_provide_name(self):
        res = DeterministicNLUParser.parse("माझं नाव रमेश आहे.")
        self.assertEqual(res.entities.patient_name, "Ramesh")

    def test_mr_06_baramati_hospital_query(self):
        res = DeterministicNLUParser.parse("बारामती मध्ये रुग्णालय आहे का?")
        self.assertEqual(res.entities.location, "Baramati")

    def test_mr_07_udya_date_tomorrow(self):
        res = DeterministicNLUParser.parse("उद्या डॉक्टर उपलब्ध आहेत का?")
        self.assertEqual(res.entities.date, "tomorrow")

    def test_mr_08_pediatrics_marathi(self):
        res = DeterministicNLUParser.parse("लहान मुलांचा डॉक्टर बारामतीत हवा आहे")
        self.assertEqual(res.entities.specialty, "Pediatrics")
        self.assertEqual(res.entities.location, "Baramati")

    def test_mr_09_orthopedics_marathi(self):
        res = DeterministicNLUParser.parse("हाडांचा डॉक्टर हवा आहे")
        self.assertEqual(res.entities.specialty, "Orthopedics")

    def test_mr_10_gynecology_marathi(self):
        res = DeterministicNLUParser.parse("स्त्रीरोग तज्ज्ञ डॉक्टर सांगा")
        self.assertEqual(res.entities.specialty, "Gynecology")

    def test_mr_11_chest_pain_emergency(self):
        res = DeterministicNLUParser.parse("छातीत तीव्र दुखणे होत आहे")
        self.assertTrue(res.emergency)

    def test_mr_12_bleeding_emergency(self):
        res = DeterministicNLUParser.parse("रक्तस्राव होत आहे, आपत्कालीन मदत")
        self.assertTrue(res.emergency)

    def test_mr_13_accident_emergency(self):
        res = DeterministicNLUParser.parse("अपघात झाला आहे, रुग्णवाहिका पाठवा")
        self.assertTrue(res.emergency)
        self.assertTrue(res.entities.ambulance_requested)

    def test_mr_14_pune_location(self):
        res = DeterministicNLUParser.parse("पुणे मधील रुग्णालय")
        self.assertEqual(res.entities.location, "Pune")

    def test_mr_15_satara_location(self):
        res = DeterministicNLUParser.parse("सातारा मध्ये दवाखाना")
        self.assertEqual(res.entities.location, "Satara")

    def test_mr_16_solapur_location(self):
        res = DeterministicNLUParser.parse("सोलापूर मध्ये डॉक्टर")
        self.assertEqual(res.entities.location, "Solapur")

    def test_mr_17_nashik_location(self):
        res = DeterministicNLUParser.parse("नाशिक मधील डॉक्टर")
        self.assertEqual(res.entities.location, "Nashik")

    def test_mr_18_kolhapur_location(self):
        res = DeterministicNLUParser.parse("कोल्हापूर मधील हॉस्पिटल")
        self.assertEqual(res.entities.location, "Kolhapur")

    def test_mr_19_general_greeting(self):
        res = DeterministicNLUParser.parse("नमस्कार, जनसेतू")
        self.assertEqual(res.intent, NLUIntent.GENERAL_GREETING)

    def test_mr_20_thank_you(self):
        res = DeterministicNLUParser.parse("धन्यवाद, खूप मदत झाली")
        self.assertEqual(res.intent, NLUIntent.THANK_YOU)

    def test_mr_21_goodbye(self):
        res = DeterministicNLUParser.parse("पुन्हा भेटू, काळजी घ्या")
        self.assertEqual(res.intent, NLUIntent.GOODBYE)

    def test_mr_22_cancel_appointment(self):
        res = DeterministicNLUParser.parse("अपॉइंटमेंट रद्द करा")
        self.assertEqual(res.intent, NLUIntent.CANCEL_APPOINTMENT)

    def test_mr_23_reschedule_appointment(self):
        res = DeterministicNLUParser.parse("वेळ बदला उद्यासाठी")
        self.assertEqual(res.intent, NLUIntent.RESCHEDULE_APPOINTMENT)

    def test_mr_24_my_appointments(self):
        res = DeterministicNLUParser.parse("माझी अपॉइंटमेंट दाखवा")
        self.assertEqual(res.intent, NLUIntent.MY_APPOINTMENTS)

    def test_mr_25_sakali_morning_time(self):
        res = DeterministicNLUParser.parse("उद्या सकाळी 10 वाजता")
        self.assertEqual(res.entities.date, "tomorrow")
        self.assertEqual(res.entities.time_period, "morning")
        self.assertEqual(res.entities.time, "10:00")

    def test_mr_26_sandhyakali_evening(self):
        res = DeterministicNLUParser.parse("संध्याकाळी डॉक्टर उपलब्ध आहेत का?")
        self.assertEqual(res.entities.time_period, "evening")

    def test_mr_27_dupari_afternoon(self):
        res = DeterministicNLUParser.parse("दुपारी भेटायचे आहे")
        self.assertEqual(res.entities.time_period, "afternoon")

    def test_mr_28_phc_marathi(self):
        res = DeterministicNLUParser.parse("प्राथमिक आरोग्य केंद्र इंदापूर")
        self.assertEqual(res.entities.facility_type, "PHC")
        self.assertEqual(res.entities.location, "Indapur")

    def test_mr_29_chc_marathi(self):
        res = DeterministicNLUParser.parse("ग्रामीण रुग्णालय बारामती")
        self.assertEqual(res.entities.facility_type, "CHC")
        self.assertEqual(res.entities.location, "Baramati")

    def test_mr_30_district_hospital_marathi(self):
        res = DeterministicNLUParser.parse("उपजिल्हा रुग्णालय पुणे")
        self.assertEqual(res.entities.facility_type, "DISTRICT_HOSPITAL")
        self.assertEqual(res.entities.location, "Pune")

    def test_mr_31_aaj_today(self):
        res = DeterministicNLUParser.parse("आज डॉक्टर आहेत का?")
        self.assertEqual(res.entities.date, "today")

    def test_mr_32_fever_marathi(self):
        res = DeterministicNLUParser.parse("मला ताप आणि डोकेदुखी आहे")
        self.assertEqual(res.entities.specialty, "General Medicine")

    def test_mr_33_stomach_pain_marathi(self):
        res = DeterministicNLUParser.parse("पोटदुखी साठी डॉक्टर सांगा")
        self.assertEqual(res.entities.specialty, "General Medicine")

    def test_mr_34_eye_marathi(self):
        res = DeterministicNLUParser.parse("डोळ्यांचा डॉक्टर हवा आहे")
        self.assertEqual(res.entities.specialty, "Ophthalmology")

    def test_mr_35_teeth_marathi(self):
        res = DeterministicNLUParser.parse("दांतांचा डॉक्टर कुठे आहे?")
        self.assertEqual(res.entities.specialty, "Dentistry")

    def test_mr_36_108_ambulance_marathi(self):
        res = DeterministicNLUParser.parse("108 ॲम्बुलन्स पाठवा")
        self.assertTrue(res.emergency)
        self.assertTrue(res.entities.ambulance_requested)

    def test_mr_37_help_marathi(self):
        res = DeterministicNLUParser.parse("मला मदत हवी आहे")
        self.assertEqual(res.intent, NLUIntent.MEDICAL_HELP)

    def test_mr_38_father_relation_marathi(self):
        res = DeterministicNLUParser.parse("माझ्या वडिलांना दाखवायचे आहे")
        self.assertEqual(res.entities.patient_relation, "father")

    def test_mr_39_mother_relation_marathi(self):
        res = DeterministicNLUParser.parse("माझ्या आईला डॉक्टरकडे नेायचे आहे")
        self.assertEqual(res.entities.patient_relation, "mother")

    def test_mr_40_child_relation_marathi(self):
        res = DeterministicNLUParser.parse("माझ्या मुलाला ताप आहे")
        self.assertEqual(res.entities.patient_relation, "child")

    def test_mr_41_confirm_marathi(self):
        res = DeterministicNLUParser.parse("होय, कन्फर्म करा")
        self.assertIn(res.intent, [NLUIntent.CONFIRM_APPOINTMENT, NLUIntent.BOOK_APPOINTMENT])

    def test_mr_42_slot_search_marathi(self):
        res = DeterministicNLUParser.parse("उद्याचे स्लॉट दाखवा")
        self.assertEqual(res.entities.date, "tomorrow")

    def test_mr_43_doctor_availability_marathi(self):
        res = DeterministicNLUParser.parse("डॉ. राजेश शर्मा कधी उपलब्ध आहेत?")
        self.assertEqual(res.entities.doctor_name, "Dr. Rajesh Sharma")

    def test_mr_44_pincode_marathi(self):
        res = DeterministicNLUParser.parse("पिनकोड 413102 मधील दवाखाने")
        self.assertEqual(res.entities.pincode, "413102")

    def test_mr_45_english_switch_marathi(self):
        res = DeterministicNLUParser.parse("इंग्रजी भाषा बदला")
        self.assertEqual(res.intent, NLUIntent.LANGUAGE_CHANGE)

    def test_mr_46_hindi_switch_marathi(self):
        res = DeterministicNLUParser.parse("हिंदी भाषा करा")
        self.assertEqual(res.intent, NLUIntent.LANGUAGE_CHANGE)

    def test_mr_47_serious_condition_marathi(self):
        res = DeterministicNLUParser.parse("गंभीर अवस्था आहे, मदत करा")
        self.assertTrue(res.emergency)

    def test_mr_48_unconscious_marathi(self):
        res = DeterministicNLUParser.parse("रुग्ण जाणीव नसणे स्थितीत आहे")
        self.assertTrue(res.emergency)

    def test_mr_49_emergency_override_marathi(self):
        res = DeterministicNLUParser.parse("आपत्कालीन परिस्थिती आहे, डॉक्टर हवा आहे")
        self.assertTrue(res.emergency)

    def test_mr_50_unknown_marathi(self):
        res = DeterministicNLUParser.parse("अबक १२३ काहीतरी")
        self.assertEqual(res.intent, NLUIntent.UNKNOWN)

    def test_mr_51_heart_doctor_marathi(self):
        res = DeterministicNLUParser.parse("हृदयरोग तज्ज्ञ सांगा")
        self.assertEqual(res.entities.specialty, "Cardiology")

    def test_mr_52_sub_district_hospital_baramati(self):
        res = DeterministicNLUParser.parse("उपजिल्हा रुग्णालय बारामती")
        self.assertEqual(res.entities.location, "Baramati")
        self.assertEqual(res.entities.facility_type, "DISTRICT_HOSPITAL")

    # =========================================================================
    # PART 4: MULTI-TURN CONVERSATION SCENARIOS (TESTS A - F & ADVERSARIAL)
    # =========================================================================

    @pytest.mark.asyncio
    async def test_scenario_a_normal_specialist_search(self):
        """TEST A — Normal Specialist Search: Clarifies location dynamically, then queries DB tools."""
        req1 = ConversationRequest(session_id="scen-a", message="Mujhe skin ka doctor chahiye")
        res1 = await ConversationManager.process_message(req1)

        self.assertIn(res1.intent, [NLUIntent.FIND_SPECIALIST, NLUIntent.FIND_DOCTOR])
        self.assertEqual(res1.entities.specialty, "Dermatology")
        self.assertIn("location", res1.missing_fields)
        self.assertIn("city", res1.assistant_message.lower() or "location" in res1.assistant_message.lower())

        req2 = ConversationRequest(session_id="scen-a", message="Baramati mein.")
        res2 = await ConversationManager.process_message(req2)

        self.assertEqual(res2.entities.specialty, "Dermatology")
        self.assertEqual(res2.entities.location, "Baramati")
        self.assertEqual(len(res2.missing_fields), 0)
        self.assertIn("Baramati", res2.assistant_message)

    @pytest.mark.asyncio
    async def test_scenario_b_emergency_routing(self):
        """TEST B — Emergency Routing: High-confidence emergency preemption bypasses normal appointment flow."""
        req = ConversationRequest(session_id="scen-b", message="Mere papa ko saans lene mein bahut dikkat ho rahi hai.")
        res = await ConversationManager.process_message(req)

        self.assertTrue(res.emergency)
        self.assertEqual(res.intent, NLUIntent.EMERGENCY)
        self.assertIn("108", res.assistant_message or "emergency" in res.assistant_message.lower())

    @pytest.mark.asyncio
    async def test_scenario_c_ambiguous_query(self):
        """TEST C — Ambiguous Query: Asks natural clarification question instead of hallucinating."""
        req = ConversationRequest(session_id="scen-c", message="Doctor chahiye.")
        res = await ConversationManager.process_message(req)

        self.assertIn("location", res.missing_fields)

    @pytest.mark.asyncio
    async def test_scenario_d_multilingual_hindi_script(self):
        """TEST D — Multilingual: Identifies Dermatology from Hindi script."""
        req = ConversationRequest(session_id="scen-d", message="मुझे त्वचा के डॉक्टर की जरूरत है।")
        res = await ConversationManager.process_message(req)

        self.assertEqual(res.entities.specialty, "Dermatology")
        self.assertEqual(res.language, Language.HI)

    @pytest.mark.asyncio
    async def test_scenario_e_marathi_appointment_request(self):
        """TEST E — Marathi: Identifies appointment intent from Marathi text."""
        req = ConversationRequest(session_id="scen-e", message="मला डॉक्टरची अपॉइंटमेंट हवी आहे.")
        res = await ConversationManager.process_message(req)

        self.assertIn(res.intent, [NLUIntent.BOOK_APPOINTMENT, NLUIntent.FIND_DOCTOR])
        self.assertEqual(res.language, Language.MR)

    @pytest.mark.asyncio
    async def test_scenario_f_context_memory_retention(self):
        """TEST F — Context Memory: Maintains name, specialty, and location across turns."""
        req1 = ConversationRequest(session_id="scen-f", message="My name is Ramesh.")
        res1 = await ConversationManager.process_message(req1)
        self.assertEqual(res1.entities.patient_name, "Ramesh")
        self.assertIn("Ramesh", res1.assistant_message)

        req2 = ConversationRequest(session_id="scen-f", message="I need a skin doctor.")
        res2 = await ConversationManager.process_message(req2)
        self.assertEqual(res2.entities.patient_name, "Ramesh")
        self.assertEqual(res2.entities.specialty, "Dermatology")

        req3 = ConversationRequest(session_id="scen-f", message="In Baramati.")
        res3 = await ConversationManager.process_message(req3)
        self.assertEqual(res3.entities.patient_name, "Ramesh")
        self.assertEqual(res3.entities.specialty, "Dermatology")
        self.assertEqual(res3.entities.location, "Baramati")
        self.assertIn("Ramesh", res3.assistant_message)
        self.assertIn("Baramati", res3.assistant_message)

    @pytest.mark.asyncio
    async def test_adversarial_synonym_skin_doctor(self):
        """Adversarial Test: Paraphrased skin doctor expressions all map to Dermatology."""
        phrases = [
            "I need a skin doctor.",
            "Skin ka doctor chahiye.",
            "Mujhe dermatologist dikha do.",
            "Baramati mein skin specialist milega?",
            "मला त्वचारोगाचा डॉक्टर हवा आहे."
        ]
        for p in phrases:
            res = DeterministicNLUParser.parse(p)
            self.assertEqual(res.entities.specialty, "Dermatology", f"Failed for phrase: '{p}'")

    @pytest.mark.asyncio
    async def test_adversarial_emergency_phrases(self):
        """Adversarial Test: Paraphrased emergency expressions all enter emergency pathway."""
        phrases = [
            "Emergency hai.",
            "Bahut serious problem hai.",
            "Ambulance bhejo.",
            "Accident hua hai.",
            "मेरे पापा को सांस नहीं आ रही।"
        ]
        for p in phrases:
            res = DeterministicNLUParser.parse(p)
            self.assertTrue(res.emergency, f"Failed emergency for phrase: '{p}'")


if __name__ == "__main__":
    unittest.main()
