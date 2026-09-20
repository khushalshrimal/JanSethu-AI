// Mock Data for JanSethu AI Prototype

export const MOCK_FACILITIES = [
  {
    id: 1,
    name: "District Civil Hospital (DEMO)",
    name_hi: "जिला नागरिक अस्पताल (डेमो)",
    city: "Jaipur",
    area: "Sanganer",
    address: "Tonk Road, Near Sanganer Flyover, Jaipur, Rajasthan 302029",
    latitude: 26.8206,
    longitude: 75.8075,
    services: "General OPD, Fever Clinic, Emergency Care, Maternity & Child Health, Vaccination, Diagnostics",
    contact_phone: "+91-141-2700100",
    facility_type: "District Government Hospital",
    distance: "1.2 km"
  },
  {
    id: 2,
    name: "Primary Health Centre (PHC) Malviya Nagar (DEMO)",
    name_hi: "प्राथमिक स्वास्थ्य केंद्र मालवीय नगर (डेमो)",
    city: "Jaipur",
    area: "Malviya Nagar",
    address: "Sector 4, Malviya Nagar, Jaipur, Rajasthan 302017",
    latitude: 26.8549,
    longitude: 75.8243,
    services: "General Medicine, Child Immunization, Basic Health Checkup, TB Clinic, Free Medicines",
    contact_phone: "+91-141-2550200",
    facility_type: "Primary Health Centre (PHC)",
    distance: "2.5 km"
  },
  {
    id: 3,
    name: "Community Health Centre (CHC) Chokhi Dhani Area (DEMO)",
    name_hi: "सामुदायिक स्वास्थ्य केंद्र चौखी ढाणी क्षेत्र (डेमो)",
    city: "Jaipur",
    area: "Sitapura",
    address: "Sitapura Industrial Area, Near RIICO, Jaipur 302022",
    latitude: 26.7794,
    longitude: 75.8450,
    services: "Maternity Ward, Pediatrics, Emergency First Aid, Dental OPD, Eye Checkup",
    contact_phone: "+91-141-2770300",
    facility_type: "Community Health Centre (CHC)",
    distance: "3.8 km"
  },
  {
    id: 4,
    name: "JanSethu Mobile Health Van Station #1 (DEMO)",
    name_hi: "जनसेतु मोबाइल स्वास्थ्य वैन स्टेशन #1 (डेमो)",
    city: "Jaipur",
    area: "Pratap Nagar",
    address: "Kumbha Marg Bus Stand, Pratap Nagar, Jaipur",
    latitude: 26.7938,
    longitude: 75.8152,
    services: "Mobile Doctor Unit, Free Blood Pressure & Sugar Check, Essential Medicines Distribution",
    contact_phone: "+91-98290-11223",
    facility_type: "Mobile Clinic",
    distance: "0.8 km"
  },
  {
    id: 5,
    name: "Government Sub-District Hospital (DEMO)",
    name_hi: "सरकारी उप-जिला अस्पताल (डेमो)",
    city: "New Delhi",
    area: "Mehrauli",
    address: "Main Road Mehrauli, Near Bus Terminal, New Delhi 110030",
    latitude: 28.5204,
    longitude: 77.1855,
    services: "General Physician, Emergency First Aid, Orthopedics, Fever & Viral OPD, X-Ray",
    contact_phone: "+91-11-2664010",
    facility_type: "Sub-District Hospital",
    distance: "4.5 km"
  }
];

export const MOCK_SLOTS = [
  { id: 101, facility_id: 1, date: "Tomorrow", time: "09:00 AM", available: true, doctor_name: "Dr. Rajesh Sharma", department: "General OPD" },
  { id: 102, facility_id: 1, date: "Tomorrow", time: "10:30 AM", available: true, doctor_name: "Dr. Sunita Verma", department: "Pediatrics & Child Care" },
  { id: 103, facility_id: 1, date: "Tomorrow", time: "11:45 AM", available: false, doctor_name: "Dr. Anita Gupta", department: "Maternity & OPD" },
  { id: 104, facility_id: 1, date: "Tomorrow", time: "02:00 PM", available: true, doctor_name: "Dr. Manoj Kumar", department: "Fever Clinic" },
  { id: 105, facility_id: 1, date: "Tomorrow", time: "03:30 PM", available: true, doctor_name: "Dr. Pooja Yadav", department: "Dental OPD" },
  
  { id: 201, facility_id: 2, date: "Tomorrow", time: "09:30 AM", available: true, doctor_name: "Dr. Ramesh Meena", department: "General Medicine" },
  { id: 202, facility_id: 2, date: "Tomorrow", time: "11:00 AM", available: true, doctor_name: "Dr. Kirti Jain", department: "Vaccination & Child Health" },
  { id: 203, facility_id: 2, date: "Tomorrow", time: "02:30 PM", available: true, doctor_name: "Dr. Ramesh Meena", department: "General Medicine" }
];

export const MOCK_APPOINTMENTS = [
  {
    id: 4,
    token_number: "A-104",
    facility_id: 1,
    facility_name: "District Civil Hospital, Baramati (DEMO)",
    patient_name: "Demo Patient",
    phone: "+91-9876543210",
    doctor_name: "Dr. Sharma",
    service: "General OPD",
    date: "Tomorrow",
    time: "10:30 AM",
    status: "confirmed",
    created_at: "2026-09-20T10:00:00Z"
  },
  {
    id: 1002,
    token_number: "A-105",
    facility_id: 2,
    facility_name: "Primary Health Centre Malviya Nagar (DEMO)",
    patient_name: "Sita Devi",
    phone: "+91-9829012345",
    doctor_name: "Dr. Sunita Verma",
    service: "Child Immunization",
    date: "Tomorrow",
    time: "11:00 AM",
    status: "waiting",
    created_at: "2026-09-20T09:30:00Z"
  }
];

export const MOCK_EMERGENCY = {
  message: "For life-threatening medical emergencies, call emergency ambulance services immediately.",
  message_hi: "गंभीर आपातकालीन चिकित्सा के लिए तुरंत एम्बुलेंस सेवा 108 पर कॉल करें।",
  contacts: [
    {
      title: "National Emergency Ambulance",
      title_hi: "राष्ट्रीय आपातकालीन एम्बुलेंस",
      number: "108",
      description: "24/7 Free emergency ambulance dispatch",
      description_hi: "24 घंटे निःशुल्क एम्बुलेंस सेवा"
    },
    {
      title: "Medical & Health Advice Helpline",
      title_hi: "चिकित्सा व स्वास्थ्य परामर्श हेल्पलाइन",
      number: "104",
      description: "Free tele-consultation & medical information",
      description_hi: "निःशुल्क स्वास्थ्य परामर्श और जानकारी"
    },
    {
      title: "Women Emergency Helpline",
      title_hi: "महिला सुरक्षा व आपात सहायता",
      number: "181",
      description: "24/7 Women helpline & safety support",
      description_hi: "24/7 महिला सहायता और सुरक्षा"
    },
    {
      title: "Child Helpline",
      title_hi: "चाइल्ड हेल्पलाइन",
      number: "1098",
      description: "Emergency assistance for children",
      description_hi: "बच्चों के लिए आपातकालीन सहायता"
    }
  ]
};

export const MOCK_VOICE_PROMPTS = [
  {
    en: "I need to see a doctor tomorrow.",
    hi: "मुझे कल डॉक्टर को दिखाना है।"
  },
  {
    en: "Is there a fever clinic near Sanganer?",
    hi: "क्या सांगानेर के पास बुखार का अस्पताल है?"
  },
  {
    en: "Find child vaccination availability.",
    hi: "बच्चों के टीके की सुविधा कहाँ मिलेगी?"
  },
  {
    en: "Emergency ambulance contact number.",
    hi: "एम्बुलेंस का इमरजेंसी नंबर बताओ।"
  }
];
