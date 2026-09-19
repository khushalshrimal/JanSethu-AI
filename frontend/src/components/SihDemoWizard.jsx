import React, { useState, useEffect } from 'react';
import { Play, Pause, ChevronRight, ChevronLeft, Sparkles, X, CheckCircle, Video } from 'lucide-react';

export const SIH_DEMO_STEPS = [
  {
    step: 1,
    title: "1. JanSethu AI Landing Screen",
    screen: "home",
    lang: "hi",
    narration: "Welcome to JanSethu AI, a voice-first healthcare access platform designed specifically for rural and underserved users in Maharashtra.",
    actionDescription: "Shows JanSethu AI landing hero banner, service categories, and voice search entry point."
  },
  {
    step: 2,
    title: "2. Dual-Channel Access Overview",
    screen: "home",
    lang: "hi",
    narration: "JanSethu AI connects citizens through two channels: smartphone PWA for web users, and simulated IVR phone calls for keypad feature phone users without internet.",
    actionDescription: "Explains smartphone PWA + feature phone IVR telephone channel."
  },
  {
    step: 3,
    title: "3. Start Simulated Feature Phone Call",
    screen: "phone",
    lang: "hi",
    narration: "Let us demonstrate a call from a basic feature phone. The user dials our toll-free JanSethu AI hotline number.",
    actionDescription: "Opens Nokia Feature Phone Simulator and starts simulated call."
  },
  {
    step: 4,
    title: "4. Telephony Language Selection (Hindi)",
    screen: "phone",
    lang: "hi",
    narration: "The IVR system greets the caller in Hindi and Marathi. The user selects Hindi by pressing 1 or speaking Hindi.",
    actionDescription: "IVR greets caller in Hindi ('जनसेतु AI में आपका स्वागत है')."
  },
  {
    step: 5,
    title: "5. Rural Patient Spoken Input",
    screen: "phone",
    lang: "hi",
    narration: "The patient speaks naturally in Hindi: 'Mujhe teen din se tez bukhar hai in Baramati.'",
    actionDescription: "Caller speaks fever query in Baramati."
  },
  {
    step: 6,
    title: "6. AI Understanding & Entity Extraction",
    screen: "phone",
    lang: "hi",
    narration: "JanSethu AI extracts key entities in real-time: Symptom = Fever, Duration = 3 days, Location = Baramati.",
    actionDescription: "AI Understanding panel populates extracted entities."
  },
  {
    step: 7,
    title: "7. Non-Diagnostic Safety Screening",
    screen: "phone",
    lang: "hi",
    narration: "Our safety engine evaluates symptoms. Since fever is a routine symptom, it routes to General OPD without issuing clinical diagnoses.",
    actionDescription: "Urgency classified as Routine OPD / Medium."
  },
  {
    step: 8,
    title: "8. Smart Facility Routing Search",
    screen: "facilities",
    lang: "hi",
    facility: {
      id: 1,
      name: 'Government Sub-District Hospital, Baramati',
      name_hi: 'सरकारी उप-जिला अस्पताल, बारामती',
      city: 'Baramati',
      area: 'Indapur Road',
      address: 'Opposite ST Stand, Indapur Road, Baramati 413106',
      services: 'General OPD, Pediatrics, Maternity, Emergency',
      contact_phone: '+91-2112-222108'
    },
    narration: "Smart Routing evaluates nearby facilities in Baramati based on distance, OPD service match, and doctor availability.",
    actionDescription: "Displays Baramati Government Sub-District Hospital with 95% Smart Score."
  },
  {
    step: 9,
    title: "9. Doctor Slot Grid & Availability",
    screen: "slots",
    facility: {
      id: 1,
      name: 'Government Sub-District Hospital, Baramati',
      name_hi: 'सरकारी उप-जिला अस्पताल, बारामती',
      city: 'Baramati',
      area: 'Indapur Road',
      address: 'Opposite ST Stand, Indapur Road, Baramati 413106',
      services: 'General OPD, Pediatrics, Maternity, Emergency',
      contact_phone: '+91-2112-222108'
    },
    narration: "The system displays live doctor availability for General OPD & Pediatrics at Baramati Hospital.",
    actionDescription: "Displays available OPD slots starting at 09:00 AM."
  },
  {
    step: 10,
    title: "10. Select 10:30 AM Slot",
    screen: "slots",
    facility: {
      id: 1,
      name: 'Government Sub-District Hospital, Baramati',
      name_hi: 'सरकारी उप-जिला अस्पताल, बारामती',
      city: 'Baramati',
      area: 'Indapur Road',
      address: 'Opposite ST Stand, Indapur Road, Baramati 413106',
      services: 'General OPD, Pediatrics, Maternity, Emergency',
      contact_phone: '+91-2112-222108'
    },
    slot: {
      id: 101,
      facility_id: 1,
      date: 'Tomorrow',
      time: '10:30 AM',
      doctor_name: 'Dr. Sharma',
      department: 'Pediatrics'
    },
    narration: "Patient selects the 10:30 AM slot with Dr. Sharma.",
    actionDescription: "Highlights 10:30 AM slot."
  },
  {
    step: 11,
    title: "11. Confirm Appointment Request",
    screen: "confirmation",
    facility: {
      id: 1,
      name: 'Government Sub-District Hospital, Baramati',
      name_hi: 'सरकारी उप-जिला अस्पताल, बारामती',
      city: 'Baramati',
      area: 'Indapur Road',
      address: 'Opposite ST Stand, Indapur Road, Baramati 413106',
      services: 'General OPD, Pediatrics, Maternity, Emergency',
      contact_phone: '+91-2112-222108'
    },
    slot: {
      id: 101,
      facility_id: 1,
      date: 'Tomorrow',
      time: '10:30 AM',
      doctor_name: 'Dr. Sharma',
      department: 'Pediatrics'
    },
    narration: "The patient confirms their details (Ramesh Pawar, Baramati).",
    actionDescription: "Fills patient confirmation form."
  },
  {
    step: 12,
    title: "12. Token Generation (Token A-104)",
    screen: "confirmation",
    facility: {
      id: 1,
      name: 'Government Sub-District Hospital, Baramati',
      name_hi: 'सरकारी उप-जिला अस्पताल, बारामती',
      city: 'Baramati',
      area: 'Indapur Road',
      address: 'Opposite ST Stand, Indapur Road, Baramati 413106',
      services: 'General OPD, Pediatrics, Maternity, Emergency',
      contact_phone: '+91-2112-222108'
    },
    slot: {
      id: 101,
      facility_id: 1,
      date: 'Tomorrow',
      time: '10:30 AM',
      doctor_name: 'Dr. Sharma',
      department: 'Pediatrics'
    },
    narration: "Appointment confirmed! Unique Token A-104 is generated and saved in SQLite database.",
    actionDescription: "Displays confirmed ticket card with Token A-104."
  },
  {
    step: 13,
    title: "13. Voice Confirmation Synthesis",
    screen: "confirmation",
    facility: {
      id: 1,
      name: 'Government Sub-District Hospital, Baramati',
      name_hi: 'सरकारी उप-जिला अस्पताल, बारामती',
      city: 'Baramati',
      area: 'Indapur Road',
      address: 'Opposite ST Stand, Indapur Road, Baramati 413106',
      services: 'General OPD, Pediatrics, Maternity, Emergency',
      contact_phone: '+91-2112-222108'
    },
    slot: {
      id: 101,
      facility_id: 1,
      date: 'Tomorrow',
      time: '10:30 AM',
      doctor_name: 'Dr. Sharma',
      department: 'Pediatrics'
    },
    narration: "JanSethu AI speaks confirmation back to the patient in Hindi: 'आपका अपॉइंटमेंट टोकन A-104 बारामती अस्पताल में कल 10:30 बजे पक्का हो गया है।'",
    actionDescription: "Plays audio voice confirmation synthesis."
  },
  {
    step: 14,
    title: "14. Simulated SMS Receipt Dispatch",
    screen: "confirmation",
    facility: {
      id: 1,
      name: 'Government Sub-District Hospital, Baramati',
      name_hi: 'सरकारी उप-जिला अस्पताल, बारामती',
      city: 'Baramati',
      area: 'Indapur Road',
      address: 'Opposite ST Stand, Indapur Road, Baramati 413106',
      services: 'General OPD, Pediatrics, Maternity, Emergency',
      contact_phone: '+91-2112-222108'
    },
    slot: {
      id: 101,
      facility_id: 1,
      date: 'Tomorrow',
      time: '10:30 AM',
      doctor_name: 'Dr. Sharma',
      department: 'Pediatrics'
    },
    narration: "An SMS confirmation is dispatched to the patient's phone containing Token A-104, date, time, and doctor name.",
    actionDescription: "Displays green SMS Confirmation receipt card."
  },
  {
    step: 15,
    title: "15. Live 6-Stage Appointment Tracking",
    screen: "track",
    narration: "The patient can track their appointment progress in real-time through a 6-stage status timeline.",
    actionDescription: "Opens TrackAppointmentScreen showing Token A-104 timeline."
  },
  {
    step: 16,
    title: "16. Healthcare Provider Dashboard",
    screen: "dashboard",
    narration: "On the healthcare provider side, hospital staff view Token A-104 live in their appointments table and can update status to 'Waiting' or 'In OPD'.",
    actionDescription: "Opens Provider Dashboard displaying Token A-104."
  },
  {
    step: 17,
    title: "17. Emergency Demo Trigger",
    screen: "emergency",
    narration: "Now let us test an emergency scenario. A caller reports: 'Mere papa ko saans lene mein bahut dikkat ho rahi hai.'",
    actionDescription: "Triggers emergency respiratory distress voice triage."
  },
  {
    step: 18,
    title: "18. Emergency Detection & Routing",
    screen: "emergency",
    narration: "JanSethu AI immediately detects a potential emergency. Standard OPD booking is paused, and the user is routed to 108 Emergency Ambulance & Baramati Trauma Unit.",
    actionDescription: "Displays 🚨 POTENTIAL EMERGENCY DETECTED alert banner and 108 call action."
  },
  {
    step: 19,
    title: "19. Full Marathi Language Support",
    screen: "voice",
    lang: "mr",
    narration: "Finally, JanSethu AI provides first-class Marathi voice and UI support for citizens across rural Maharashtra.",
    actionDescription: "Switches language to Marathi ('मराठी') and displays spoken Marathi responses."
  }
];

export default function SihDemoWizard({ currentStepIndex, setStepIndex, onStepExecute, isClosed, setIsClosed }) {
  const [autoPlay, setAutoPlay] = useState(false);

  const stepData = SIH_DEMO_STEPS[currentStepIndex] || SIH_DEMO_STEPS[0];

  useEffect(() => {
    let timer = null;
    if (autoPlay) {
      timer = setInterval(() => {
        setStepIndex(prev => {
          if (prev < SIH_DEMO_STEPS.length - 1) {
            const nextIdx = prev + 1;
            onStepExecute(SIH_DEMO_STEPS[nextIdx]);
            return nextIdx;
          } else {
            setAutoPlay(false);
            return prev;
          }
        });
      }, 4000);
    }
    return () => clearInterval(timer);
  }, [autoPlay, setStepIndex, onStepExecute]);

  const goToStep = (idx) => {
    if (idx >= 0 && idx < SIH_DEMO_STEPS.length) {
      setStepIndex(idx);
      onStepExecute(SIH_DEMO_STEPS[idx]);
    }
  };

  if (isClosed) return null;

  return (
    <div className="bg-slate-950 text-white p-4 rounded-2xl shadow-2xl border-2 border-sky-500 mb-4 space-y-3">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-800 pb-2">
        <div className="flex items-center gap-2">
          <span className="bg-gradient-to-r from-sky-500 to-blue-600 text-white font-black text-xs px-3 py-1 rounded-full flex items-center gap-1.5 shadow">
            <Video className="w-3.5 h-3.5" />
            SIH DEMO WIZARD
          </span>
          <span className="text-xs font-extrabold text-amber-400">
            Step {stepData.step} of {SIH_DEMO_STEPS.length}: {stepData.title}
          </span>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={() => setAutoPlay(!autoPlay)}
            className={`px-3 py-1 rounded-xl text-xs font-extrabold flex items-center gap-1 transition ${
              autoPlay ? 'bg-amber-400 text-slate-950 animate-pulse' : 'bg-slate-800 text-slate-200 hover:bg-slate-700'
            }`}
          >
            {autoPlay ? <Pause className="w-3.5 h-3.5" /> : <Play className="w-3.5 h-3.5" />}
            <span>{autoPlay ? 'PAUSE AUTO' : 'AUTO PLAY STORY'}</span>
          </button>

          <button
            onClick={() => setIsClosed(true)}
            className="text-slate-400 hover:text-white p-1 rounded-lg"
            title="Close Wizard"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Narration Box for Video Recording */}
      <div className="bg-slate-900 p-3 rounded-xl border border-slate-800 space-y-1">
        <div className="text-[10px] font-bold text-sky-400 uppercase tracking-wider">
          🎙️ Presenter Script (Say into mic during video recording):
        </div>
        <p className="text-xs text-slate-100 font-medium leading-relaxed italic">
          "{stepData.narration}"
        </p>
        <div className="text-[10px] text-slate-400 font-semibold pt-0.5">
          🎯 Action: {stepData.actionDescription}
        </div>
      </div>

      {/* Stepper Controls */}
      <div className="flex items-center justify-between gap-2 pt-1">
        <button
          onClick={() => goToStep(currentStepIndex - 1)}
          disabled={currentStepIndex === 0}
          className="bg-slate-800 hover:bg-slate-700 disabled:opacity-40 text-slate-200 font-bold text-xs px-3 py-1.5 rounded-xl flex items-center gap-1 transition"
        >
          <ChevronLeft className="w-4 h-4" />
          <span>PREVIOUS</span>
        </button>

        <div className="text-[11px] font-mono font-bold text-slate-400">
          {currentStepIndex + 1} / {SIH_DEMO_STEPS.length}
        </div>

        <button
          onClick={() => goToStep(currentStepIndex + 1)}
          disabled={currentStepIndex === SIH_DEMO_STEPS.length - 1}
          className="bg-sky-600 hover:bg-sky-500 disabled:opacity-40 text-white font-extrabold text-xs px-4 py-1.5 rounded-xl flex items-center gap-1 shadow transition"
        >
          <span>NEXT STEP</span>
          <ChevronRight className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
}
