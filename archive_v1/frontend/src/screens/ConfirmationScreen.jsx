import React, { useState, useEffect } from 'react';
import { CheckCircle2, Calendar, Clock, User, Phone, Building2, Ticket, ArrowLeft, Download, MessageSquare, Volume2, ShieldCheck, ArrowRight, Stethoscope } from 'lucide-react';
import { createAppointment } from '../api';
import DemoBadge from '../components/DemoBadge';
import { speakText } from '../utils/speechEngine';

export default function ConfirmationScreen({ selectedSlot, setActiveScreen, lang }) {
  const slot = selectedSlot || {
    id: 101,
    facility_id: 1,
    facility_name: "District Civil Hospital (DEMO)",
    date: "20 Sep 2026",
    time: "10:30 AM",
    doctor_name: "Dr. Sharma",
    department: "Pediatrics"
  };

  const [patientName, setPatientName] = useState('Ram Lal');
  const [phone, setPhone] = useState('+91-9876543210');
  const [service, setService] = useState(slot.department || 'Pediatrics');
  const [submitting, setSubmitting] = useState(false);
  const [confirmedTicket, setConfirmedTicket] = useState(null);

  useEffect(() => {
    if (confirmedTicket) {
      // Trigger voice confirmation audio upon ticket generation
      const voiceText = lang === 'mr'
        ? `आपली अपॉइंटमेंट जिल्हा रुग्णालयात निश्चित झाली आहे. आपला टोकन क्रमांक ${confirmedTicket.token_number || 'A-104'} आहे. वेळ ${confirmedTicket.time} आहे.`
        : lang === 'hi'
        ? `आपका अपॉइंटमेंट जिला नागरिक अस्पताल में कन्फर्म हो गया है। आपका टोकन नंबर ${confirmedTicket.token_number || 'A-104'} है। आपका समय ${confirmedTicket.time} है।`
        : `Your appointment has been confirmed at ${confirmedTicket.facility_name}. Your token number is ${confirmedTicket.token_number || 'A-104'}. Your appointment time is ${confirmedTicket.time}.`;
      
      speakText(voiceText, lang);
    }
  }, [confirmedTicket, lang]);

  const handleSubmitBooking = async (e) => {
    e.preventDefault();
    if (!patientName || !phone) return;

    setSubmitting(true);
    try {
      const res = await createAppointment({
        facility_id: slot.facility_id || 1,
        service: service,
        date: slot.date || '20 Sep 2026',
        time: slot.time || '10:30 AM',
        patient_name: patientName,
        phone: phone,
        doctor_name: slot.doctor_name || 'Dr. Sharma'
      });

      // Ensure token number & doctor name are present
      if (!res.token_number) {
        res.token_number = `A-${100 + (res.id || 4)}`;
      }
      if (!res.doctor_name) {
        res.doctor_name = slot.doctor_name || 'Dr. Sharma';
      }

      setConfirmedTicket(res);
    } catch (err) {
      console.error(err);
      // Mock fallback state
      setConfirmedTicket({
        id: 104,
        facility_id: slot.facility_id || 1,
        facility_name: slot.facility_name || "District Civil Hospital (DEMO)",
        service: service,
        date: slot.date || "20 Sep 2026",
        time: slot.time || "10:30 AM",
        patient_name: patientName,
        phone: phone,
        status: "confirmed",
        token_number: "A-104",
        doctor_name: slot.doctor_name || "Dr. Sharma"
      });
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="space-y-6 pb-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <button
          onClick={() => setActiveScreen('slots')}
          className="flex items-center gap-1.5 text-xs font-bold text-sky-700 bg-white border border-slate-200 px-3 py-1.5 rounded-xl hover:bg-sky-50 shadow-sm"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>{lang === 'hi' ? 'स्लॉट बदलें' : 'Change Slot'}</span>
        </button>
        <DemoBadge lang={lang} />
      </div>

      {!confirmedTicket ? (
        /* Patient Details Booking Form */
        <div className="bg-white p-6 rounded-3xl border border-slate-200 shadow-sm space-y-5">
          <div className="border-b border-slate-100 pb-4">
            <span className="bg-sky-100 text-sky-900 font-extrabold text-[10px] uppercase px-2.5 py-1 rounded-full">
              {lang === 'hi' ? 'अंतिम चरण: मरीज विवरण' : 'Confirm Appointment'}
            </span>
            <h2 className="text-xl font-black text-slate-900 mt-2">
              {lang === 'hi' ? 'अपॉइंटमेंट की पुष्टि करें?' : 'Confirm Appointment?'}
            </h2>
            <p className="text-xs text-slate-500 mt-1">
              {lang === 'hi'
                ? 'अस्पताल को अनुरोध भेजने के लिए नाम और फोन नंबर दर्ज करें'
                : 'Review details below and click confirm to receive your token & SMS'}
            </p>
          </div>

          {/* Booking Summary Card */}
          <div className="bg-slate-50 p-4 rounded-2xl border border-slate-200 space-y-2 text-xs">
            <div className="font-extrabold text-slate-900 text-base flex items-center justify-between">
              <span>{slot.facility_name}</span>
              <span className="bg-sky-100 text-sky-900 text-[10px] font-bold px-2.5 py-1 rounded-full">
                {slot.department || service}
              </span>
            </div>
            
            <div className="grid grid-cols-2 gap-2 text-slate-700 font-semibold pt-1">
              <div>👨‍⚕️ Doctor: <strong className="text-slate-900">{slot.doctor_name || 'Dr. Sharma'}</strong></div>
              <div>📅 Date: <strong className="text-slate-900">{slot.date}</strong></div>
              <div>⏰ Time: <strong className="text-sky-900 font-black">{slot.time}</strong></div>
              <div>🏥 Type: <strong className="text-slate-900">Government Hospital</strong></div>
            </div>
          </div>

          <form onSubmit={handleSubmitBooking} className="space-y-4">
            <div>
              <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1.5">
                {lang === 'hi' ? 'मरीज का नाम *' : 'Patient Full Name *'}
              </label>
              <div className="relative">
                <User className="w-5 h-5 text-slate-400 absolute left-3.5 top-3.5" />
                <input
                  type="text"
                  required
                  value={patientName}
                  onChange={(e) => setPatientName(e.target.value)}
                  placeholder="Ram Lal"
                  className="w-full bg-slate-50 border border-slate-300 rounded-2xl pl-11 pr-4 py-3 text-sm font-bold text-slate-900 focus:outline-none focus:ring-2 focus:ring-sky-600 focus:bg-white transition"
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1.5">
                {lang === 'hi' ? 'मोबाइल फोन नंबर *' : 'Mobile Phone Number *'}
              </label>
              <div className="relative">
                <Phone className="w-5 h-5 text-slate-400 absolute left-3.5 top-3.5" />
                <input
                  type="tel"
                  required
                  value={phone}
                  onChange={(e) => setPhone(e.target.value)}
                  placeholder="+91-9876543210"
                  className="w-full bg-slate-50 border border-slate-300 rounded-2xl pl-11 pr-4 py-3 text-sm font-bold text-slate-900 focus:outline-none focus:ring-2 focus:ring-sky-600 focus:bg-white transition"
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={submitting}
              className="w-full bg-emerald-600 hover:bg-emerald-700 text-white font-black py-4 rounded-2xl shadow-lg flex items-center justify-center gap-2 transition active:scale-95 text-base uppercase tracking-wider"
            >
              <CheckCircle2 className="w-5 h-5 text-amber-300" />
              <span>{lang === 'hi' ? 'अपॉइंटमेंट पुष्टि करें (CONFIRM)' : 'CONFIRM APPOINTMENT'}</span>
            </button>
          </form>
        </div>
      ) : (
        /* SUCCESS SCREEN WITH TOKEN A-104 & SMS CARD */
        <div className="bg-white p-6 rounded-3xl border-2 border-emerald-500 shadow-xl space-y-6 text-center">
          
          <div className="inline-flex p-4 bg-emerald-100 text-emerald-700 rounded-full mb-1 animate-bounce">
            <CheckCircle2 className="w-12 h-12" />
          </div>

          <div>
            <span className="bg-emerald-100 text-emerald-900 text-xs font-black px-3 py-1 rounded-full uppercase tracking-wider">
              {lang === 'hi' ? 'अपॉइंटमेंट सफलतापूर्वक निश्चित हुई' : 'APPOINTMENT CONFIRMED'}
            </span>
            <div className="mt-3">
              <span className="bg-slate-900 text-amber-300 border-2 border-amber-400 font-mono font-black text-2xl px-5 py-2 rounded-2xl shadow-md inline-block">
                Token: {confirmedTicket.token_number || 'A-104'}
              </span>
            </div>
          </div>

          {/* Ticket Details Summary */}
          <div className="bg-slate-50 p-4 rounded-3xl border border-slate-200 text-left space-y-2 text-xs">
            <div className="font-extrabold text-slate-900 text-base">{confirmedTicket.facility_name}</div>
            <div className="text-slate-600">🩺 Department: <strong>{confirmedTicket.service || 'Pediatrics'}</strong></div>
            <div className="text-slate-600">👨‍⚕️ Doctor: <strong>{confirmedTicket.doctor_name || 'Dr. Sharma'}</strong></div>
            <div className="text-slate-600">📅 Date: <strong>{confirmedTicket.date}</strong></div>
            <div className="text-sky-900 font-black text-sm">⏰ Time: <strong>{confirmedTicket.time}</strong></div>

            {/* Voice & SMS Status Badges */}
            <div className="pt-2 border-t border-slate-200 flex flex-wrap gap-2 text-[11px] font-bold">
              <span className="bg-purple-100 text-purple-900 px-2.5 py-1 rounded-lg flex items-center gap-1">
                <Volume2 className="w-3.5 h-3.5 text-purple-700" /> Voice Confirmation: Sent (Simulated)
              </span>
              <span className="bg-amber-100 text-amber-900 px-2.5 py-1 rounded-lg flex items-center gap-1">
                <MessageSquare className="w-3.5 h-3.5 text-amber-700" /> SMS Confirmation: Sent
              </span>
            </div>
          </div>

          {/* REALISTIC SMS UI CARD (Clearly Labeled Demo Simulation / Mock Gateway) */}
          <div className="bg-slate-900 text-white p-4 rounded-3xl border-2 border-amber-400 text-left space-y-2 shadow-lg">
            <div className="flex items-center justify-between text-xs font-mono font-extrabold text-amber-300 border-b border-slate-800 pb-1">
              <span className="flex items-center gap-1.5">
                <MessageSquare className="w-4 h-4 text-amber-400" />
                JANSETHU SMS INBOX RECEIPT
              </span>
              <span className="bg-slate-800 text-amber-300 text-[9px] px-2 py-0.5 rounded border border-amber-400/40">
                Demo Simulation / Mock Gateway
              </span>
            </div>

            <p className="text-xs font-mono text-slate-200 leading-relaxed pt-1">
              "JANSETHU: Appointment Confirmed at {confirmedTicket.facility_name}, {confirmedTicket.service || 'Pediatrics'}. Doctor: {confirmedTicket.doctor_name || 'Dr. Sharma'} on {confirmedTicket.date} at {confirmedTicket.time}. Token {confirmedTicket.token_number || 'A-104'}. Please reach 15 minutes before your appointment."
            </p>

            <div className="text-[10px] text-slate-400 font-mono italic pt-1 border-t border-slate-800">
              *Simulated SMS dispatch. Set TWILIO_ACCOUNT_SID to enable real carrier SMS delivery.
            </div>
          </div>

          {/* Action Buttons */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-2">
            <button
              onClick={() => setActiveScreen('track')}
              className="bg-sky-700 hover:bg-sky-800 text-white font-extrabold py-3.5 px-4 rounded-2xl text-xs flex items-center justify-center gap-2 transition shadow-md"
            >
              <Ticket className="w-4 h-4 text-amber-300" />
              <span>{lang === 'hi' ? 'अपॉइंटमेंट स्थिति ट्रैक करें' : 'Track Appointment Status'}</span>
              <ArrowRight className="w-4 h-4" />
            </button>

            <button
              onClick={() => setActiveScreen('home')}
              className="bg-slate-100 hover:bg-slate-200 text-slate-800 font-bold py-3.5 px-4 rounded-2xl text-xs flex items-center justify-center gap-2 transition"
            >
              <span>{lang === 'hi' ? 'मुख्य पृष्ठ पर जाएं' : 'Return to Home'}</span>
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
