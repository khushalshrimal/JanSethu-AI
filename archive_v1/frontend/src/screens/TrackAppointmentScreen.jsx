import React, { useState, useEffect } from 'react';
import { Search, Calendar, Clock, MapPin, Building2, User, Phone, CheckCircle, AlertCircle, RefreshCw, MessageSquare, ShieldCheck, Ticket } from 'lucide-react';
import { getAppointments } from '../api';
import DemoBadge from '../components/DemoBadge';

export default function TrackAppointmentScreen({ lang }) {
  const [phoneNumber, setPhoneNumber] = useState('+91-9876543210');
  const [appointments, setAppointments] = useState([]);
  const [loading, setLoading] = useState(false);
  const [searched, setSearched] = useState(false);

  useEffect(() => {
    handleSearch();
  }, []);

  const handleSearch = async (e) => {
    if (e) e.preventDefault();
    setLoading(true);
    setSearched(true);
    try {
      const data = await getAppointments({ phone: phoneNumber });
      setAppointments(data || []);
    } catch (err) {
      console.error(err);
      setAppointments([]);
    } finally {
      setLoading(false);
    }
  };

  const getStatusBadge = (status) => {
    switch (status) {
      case 'confirmed':
        return (
          <span className="inline-flex items-center gap-1 bg-emerald-100 text-emerald-800 font-extrabold text-xs px-3 py-1 rounded-full border border-emerald-300">
            <CheckCircle className="w-3.5 h-3.5" />
            {lang === 'hi' ? 'पुष्टि की गई (Confirmed)' : lang === 'mr' ? 'निश्चित झाले (Confirmed)' : 'Confirmed'}
          </span>
        );
      case 'rescheduled':
        return (
          <span className="inline-flex items-center gap-1 bg-amber-100 text-amber-800 font-extrabold text-xs px-3 py-1 rounded-full border border-amber-300">
            <RefreshCw className="w-3.5 h-3.5" />
            {lang === 'hi' ? 'पुनर्निर्धारित (Rescheduled)' : lang === 'mr' ? 'पुन्हा वेळ निश्चित (Rescheduled)' : 'Rescheduled'}
          </span>
        );
      case 'rejected':
      case 'cancelled':
        return (
          <span className="inline-flex items-center gap-1 bg-rose-100 text-rose-800 font-extrabold text-xs px-3 py-1 rounded-full border border-rose-300">
            <AlertCircle className="w-3.5 h-3.5" />
            {lang === 'hi' ? 'रद्द (Cancelled)' : lang === 'mr' ? 'रद्द केले (Cancelled)' : 'Cancelled'}
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center gap-1 bg-sky-100 text-sky-800 font-extrabold text-xs px-3 py-1 rounded-full border border-sky-300">
            <Clock className="w-3.5 h-3.5 animate-spin" />
            {lang === 'hi' ? 'प्रतीक्षारत (Pending Review)' : lang === 'mr' ? 'प्रतिक्षाधीन (Pending)' : 'Pending Review'}
          </span>
        );
    }
  };

  const renderTimeline = (apt) => {
    const isConfirmed = apt.status === 'confirmed' || apt.status === 'consultation' || apt.status === 'completed';
    const isConsultation = apt.status === 'consultation' || apt.status === 'completed';
    const isCompleted = apt.status === 'completed';
    const isRejected = apt.status === 'rejected' || apt.status === 'cancelled';
    const token = apt.token_number || `A-${100 + (apt.id || 4)}`;
    const doctor = apt.doctor_name || 'Dr. Sharma';

    return (
      <div className="mt-4 pt-4 border-t border-slate-200">
        <h4 className="text-xs font-bold uppercase tracking-wider text-slate-500 mb-3 flex items-center justify-between">
          <span>{lang === 'hi' ? '6-चरणीय अपॉइंटमेंट स्थिति टाइमलाइन' : '6-Stage Live Journey Timeline'}</span>
          <span className="bg-sky-100 text-sky-900 font-extrabold text-[10px] px-2 py-0.5 rounded-full">Token: {token}</span>
        </h4>

        <div className="relative pl-6 space-y-4 before:absolute before:left-2 before:top-2 before:bottom-2 before:w-0.5 before:bg-slate-200">
          {/* Step 1: Requested */}
          <div className="relative">
            <div className="absolute -left-6 top-0.5 w-4 h-4 rounded-full bg-emerald-600 text-white flex items-center justify-center text-[10px] font-bold">✓</div>
            <div>
              <p className="text-xs font-bold text-slate-800">1. Appointment Requested</p>
              <p className="text-[11px] text-slate-500">Submitted via JanSethu Telephony / PWA</p>
            </div>
          </div>

          {/* Step 2: Confirmed & Token Issued */}
          <div className="relative">
            <div className={`absolute -left-6 top-0.5 w-4 h-4 rounded-full flex items-center justify-center text-[10px] font-bold ${
              isConfirmed ? 'bg-emerald-600 text-white' : isRejected ? 'bg-rose-600 text-white' : 'bg-amber-400 text-slate-900'
            }`}>
              {isConfirmed ? '✓' : isRejected ? '✕' : '2'}
            </div>
            <div>
              <p className="text-xs font-bold text-slate-800">2. Confirmed & Token Issued ({token})</p>
              <p className="text-[11px] text-slate-500">Slot verified and SMS ticket generated</p>
            </div>
          </div>

          {/* Step 3: Hospital Notified */}
          <div className="relative">
            <div className={`absolute -left-6 top-0.5 w-4 h-4 rounded-full flex items-center justify-center text-[10px] font-bold ${
              isConfirmed ? 'bg-emerald-600 text-white' : 'bg-slate-300 text-slate-600'
            }`}>
              {isConfirmed ? '✓' : '3'}
            </div>
            <div>
              <p className="text-xs font-bold text-slate-800">3. Hospital OPD Desk Notified</p>
              <p className="text-[11px] text-slate-500">Delivered to Provider Dashboard OPD Queue</p>
            </div>
          </div>

          {/* Step 4: Waiting in Queue */}
          <div className="relative">
            <div className={`absolute -left-6 top-0.5 w-4 h-4 rounded-full flex items-center justify-center text-[10px] font-bold ${
              isConfirmed ? 'bg-amber-400 text-slate-950 font-black' : 'bg-slate-300 text-slate-600'
            }`}>
              4
            </div>
            <div>
              <p className="text-xs font-bold text-slate-800">4. Patient Waiting in Queue</p>
              <p className="text-[11px] text-slate-500">Arrive 15 minutes before slot at OPD Counter</p>
            </div>
          </div>

          {/* Step 5: Doctor Consultation */}
          <div className="relative">
            <div className={`absolute -left-6 top-0.5 w-4 h-4 rounded-full flex items-center justify-center text-[10px] font-bold ${
              isConsultation ? 'bg-emerald-600 text-white' : 'bg-slate-300 text-slate-600'
            }`}>
              5
            </div>
            <div>
              <p className="text-xs font-bold text-slate-800">5. Doctor Consultation ({doctor})</p>
              <p className="text-[11px] text-slate-500">Active OPD consultation with specialist</p>
            </div>
          </div>

          {/* Step 6: Completed */}
          <div className="relative">
            <div className={`absolute -left-6 top-0.5 w-4 h-4 rounded-full flex items-center justify-center text-[10px] font-bold ${
              isCompleted ? 'bg-emerald-600 text-white' : 'bg-slate-300 text-slate-600'
            }`}>
              6
            </div>
            <div>
              <p className="text-xs font-bold text-slate-800">6. Completed & Follow-up</p>
              <p className="text-[11px] text-slate-500">Consultation finished, prescription issued</p>
            </div>
          </div>
        </div>
      </div>
    );
  };

  return (
    <div className="space-y-6 pb-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-extrabold text-slate-900 flex items-center gap-2">
            <Ticket className="w-6 h-6 text-sky-600" />
            {lang === 'hi' ? 'अपॉइंटमेंट ट्रैक करें' : lang === 'mr' ? 'अपॉइंटमेंट ट्रॅक करा' : 'Track Appointment Status'}
          </h2>
          <p className="text-xs text-slate-500 mt-0.5">
            {lang === 'hi'
              ? 'अपना फोन नंबर दर्ज करके अपनी हालिया अपॉइंटमेंट स्थिति और टाइमलाइन देखें'
              : 'Enter patient mobile number to view appointment status & live timeline'}
          </p>
        </div>
        <DemoBadge lang={lang} />
      </div>

      {/* Phone Lookup Form */}
      <form onSubmit={handleSearch} className="bg-white p-5 rounded-3xl border border-slate-200 shadow-sm space-y-4">
        <div>
          <label className="block text-xs font-bold text-slate-700 mb-1">
            {lang === 'hi' ? 'मरीज का मोबाइल नंबर' : lang === 'mr' ? 'रुग्णाचा मोबाईल क्रमांक' : 'Patient Mobile Number'}
          </label>
          <div className="flex gap-2">
            <div className="relative flex-1">
              <Phone className="w-5 h-5 text-slate-400 absolute left-3.5 top-3.5" />
              <input
                type="text"
                value={phoneNumber}
                onChange={(e) => setPhoneNumber(e.target.value)}
                placeholder="+91-9876543210"
                className="w-full pl-11 pr-4 py-3 bg-slate-50 border border-slate-300 rounded-2xl text-sm font-semibold focus:ring-2 focus:ring-sky-500 focus:outline-none"
              />
            </div>
            <button
              type="submit"
              disabled={loading}
              className="bg-sky-600 hover:bg-sky-700 text-white font-bold px-6 py-3 rounded-2xl flex items-center gap-2 transition active:scale-95 shadow-md"
            >
              {loading ? <RefreshCw className="w-5 h-5 animate-spin" /> : <Search className="w-5 h-5" />}
              <span>{lang === 'hi' ? 'खोजें' : lang === 'mr' ? 'शोधा' : 'Track'}</span>
            </button>
          </div>
        </div>
      </form>

      {/* Results List */}
      {loading ? (
        <div className="text-center py-12 text-slate-500 bg-white rounded-3xl border border-slate-200">
          <RefreshCw className="w-8 h-8 animate-spin mx-auto text-sky-600 mb-2" />
          <p className="text-sm font-semibold">{lang === 'hi' ? 'लोड हो रहा है...' : 'Searching appointment records...'}</p>
        </div>
      ) : appointments.length > 0 ? (
        <div className="space-y-4">
          {appointments.map((apt) => (
            <div key={apt.id} className="bg-white p-5 rounded-3xl border border-slate-200 shadow-md space-y-4">
              <div className="flex items-start justify-between border-b border-slate-100 pb-3">
                <div>
                  <span className="text-[10px] font-black uppercase text-sky-700 bg-sky-50 px-2.5 py-1 rounded-full border border-sky-200">
                    TICKET #{apt.id}
                  </span>
                  <h3 className="font-extrabold text-slate-900 text-lg mt-1">{apt.facility_name}</h3>
                </div>
                {getStatusBadge(apt.status)}
              </div>

              <div className="grid grid-cols-2 gap-3 text-xs">
                <div className="flex items-center gap-2 bg-slate-50 p-2.5 rounded-xl border border-slate-100">
                  <User className="w-4 h-4 text-sky-600" />
                  <div>
                    <span className="text-[10px] text-slate-400 block">{lang === 'hi' ? 'मरीज' : 'Patient'}</span>
                    <span className="font-bold text-slate-800">{apt.patient_name}</span>
                  </div>
                </div>

                <div className="flex items-center gap-2 bg-slate-50 p-2.5 rounded-xl border border-slate-100">
                  <Building2 className="w-4 h-4 text-sky-600" />
                  <div>
                    <span className="text-[10px] text-slate-400 block">{lang === 'hi' ? 'विभाग' : 'Department'}</span>
                    <span className="font-bold text-slate-800">{apt.service}</span>
                  </div>
                </div>

                <div className="flex items-center gap-2 bg-slate-50 p-2.5 rounded-xl border border-slate-100">
                  <Calendar className="w-4 h-4 text-emerald-600" />
                  <div>
                    <span className="text-[10px] text-slate-400 block">{lang === 'hi' ? 'दिनांक' : 'Date'}</span>
                    <span className="font-bold text-slate-800">{apt.date}</span>
                  </div>
                </div>

                <div className="flex items-center gap-2 bg-slate-50 p-2.5 rounded-xl border border-slate-100">
                  <Clock className="w-4 h-4 text-amber-600" />
                  <div>
                    <span className="text-[10px] text-slate-400 block">{lang === 'hi' ? 'समय' : 'Time'}</span>
                    <span className="font-bold text-slate-800">{apt.time}</span>
                  </div>
                </div>
              </div>

              {/* SMS Notification Banner */}
              <div className="bg-slate-900 text-white p-3 rounded-2xl flex items-start gap-3 text-xs border border-slate-800">
                <MessageSquare className="w-4 h-4 text-amber-400 mt-0.5 flex-shrink-0" />
                <div>
                  <span className="text-[10px] font-bold text-amber-300 uppercase block">JanSethu SMS Dispatch</span>
                  <p className="font-mono text-[11px] text-slate-300 mt-0.5">
                    "JanSethu Ticket #{apt.id}: Appointment {apt.status} for {apt.patient_name} at {apt.facility_name} on {apt.date} ({apt.time})."
                  </p>
                </div>
              </div>

              {/* Step Timeline */}
              {renderTimeline(apt)}
            </div>
          ))}
        </div>
      ) : searched ? (
        <div className="text-center py-12 bg-white rounded-3xl border border-slate-200 p-6">
          <AlertCircle className="w-10 h-10 text-amber-500 mx-auto mb-2" />
          <h3 className="font-bold text-slate-800 text-base">
            {lang === 'hi' ? 'कोई अपॉइंटमेंट नहीं मिली' : 'No Appointments Found'}
          </h3>
          <p className="text-xs text-slate-500 mt-1">
            {lang === 'hi'
              ? 'इस नंबर से कोई अपॉइंटमेंट दर्ज नहीं है। कृपया नया स्लॉट बुक करें।'
              : `No appointments registered under ${phoneNumber}. Try booking a new slot.`}
          </p>
        </div>
      ) : null}
    </div>
  );
}
