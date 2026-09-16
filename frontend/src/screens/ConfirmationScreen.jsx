import React, { useState } from 'react';
import { CheckCircle2, Calendar, Clock, User, Phone, Building2, Ticket, ArrowLeft, Download, PhoneCall, RefreshCw } from 'lucide-react';
import { createAppointment } from '../api';
import DemoBadge from '../components/DemoBadge';

export default function ConfirmationScreen({ selectedSlot, setActiveScreen, lang }) {
  const slot = selectedSlot || {
    id: 101,
    facility_id: 1,
    facility_name: "District Civil Hospital (DEMO)",
    date: "Tomorrow",
    time: "10:30 AM",
    doctor_name: "Dr. Sunita Verma",
    department: "Pediatrics & Child Care"
  };

  const [patientName, setPatientName] = useState('');
  const [phone, setPhone] = useState('');
  const [service, setService] = useState(slot.department || 'General OPD');
  const [submitting, setSubmitting] = useState(false);
  const [confirmedTicket, setConfirmedTicket] = useState(null);

  const handleSubmitBooking = async (e) => {
    e.preventDefault();
    if (!patientName || !phone) return;

    setSubmitting(true);
    try {
      const res = await createAppointment({
        facility_id: slot.facility_id || 1,
        service: service,
        date: slot.date || 'Tomorrow',
        time: slot.time || '10:30 AM',
        patient_name: patientName,
        phone: phone
      });
      setConfirmedTicket(res);
    } catch (err) {
      console.error(err);
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
        /* Patient Details Form */
        <div className="bg-white p-6 rounded-3xl border border-slate-200 shadow-sm space-y-5">
          <div className="border-b border-slate-100 pb-4">
            <span className="bg-sky-100 text-sky-900 font-extrabold text-[10px] uppercase px-2.5 py-1 rounded-full">
              {lang === 'hi' ? 'अंतिम चरण: मरीज विवरण' : 'Final Step: Patient Information'}
            </span>
            <h2 className="text-xl font-black text-slate-900 mt-2">
              {lang === 'hi' ? 'अपॉइंटमेंट अनुरोध पूरा करें' : 'Confirm Appointment Request'}
            </h2>
            <p className="text-xs text-slate-500 mt-1">
              {lang === 'hi'
                ? 'अस्पताल को अनुरोध भेजने के लिए नाम और फोन नंबर दर्ज करें'
                : 'Enter details to submit request to healthcare provider dashboard'}
            </p>
          </div>

          {/* Slot Summary Pill */}
          <div className="bg-slate-50 p-4 rounded-2xl border border-slate-200 flex flex-col sm:flex-row sm:items-center justify-between gap-2 text-xs">
            <div>
              <div className="font-extrabold text-slate-900 text-sm">{slot.facility_name}</div>
              <div className="text-slate-600 mt-0.5">
                👨‍⚕️ {slot.doctor_name || 'OPD Doctor'} • 🩺 {service}
              </div>
            </div>
            <div className="bg-sky-100 text-sky-900 font-extrabold px-3 py-1.5 rounded-xl self-start sm:self-center">
              📅 {slot.date} @ {slot.time}
            </div>
          </div>

          <form onSubmit={handleSubmitBooking} className="space-y-4">
            <div>
              <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1.5">
                {lang === 'hi' ? 'मरीज का पूरा नाम *' : 'Patient Full Name *'}
              </label>
              <div className="relative">
                <User className="w-5 h-5 text-slate-400 absolute left-3.5 top-3.5" />
                <input
                  type="text"
                  required
                  value={patientName}
                  onChange={(e) => setPatientName(e.target.value)}
                  placeholder={lang === 'hi' ? 'उदा. राम लाल meena' : 'e.g., Ram Lal Meena'}
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
                  placeholder={lang === 'hi' ? '10 अंकों का मोबाइल नंबर' : '+91-9876543210'}
                  className="w-full bg-slate-50 border border-slate-300 rounded-2xl pl-11 pr-4 py-3 text-sm font-bold text-slate-900 focus:outline-none focus:ring-2 focus:ring-sky-600 focus:bg-white transition"
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={submitting}
              className="w-full bg-emerald-600 hover:bg-emerald-700 text-white font-black py-4 rounded-2xl shadow-lg flex items-center justify-center gap-2 transition active:scale-95 text-base"
            >
              {submitting ? (
                <>
                  <RefreshCw className="w-5 h-5 animate-spin" />
                  <span>{lang === 'hi' ? 'अनुरोध भेजा जा रहा है...' : 'Submitting Request...'}</span>
                </>
              ) : (
                <>
                  <CheckCircle2 className="w-5 h-5 text-amber-300" />
                  <span>{lang === 'hi' ? 'अनुरोध जमा करें (Submit Request)' : 'Confirm & Request Appointment'}</span>
                </>
              )}
            </button>
          </form>
        </div>
      ) : (
        /* Confirmed Ticket View */
        <div className="bg-white p-6 rounded-3xl border-2 border-emerald-500 shadow-xl space-y-6 text-center">
          
          <div className="inline-flex p-4 bg-emerald-100 text-emerald-700 rounded-full mb-1 animate-bounce">
            <CheckCircle2 className="w-12 h-12" />
          </div>

          <div>
            <span className="bg-emerald-100 text-emerald-900 text-xs font-black px-3 py-1 rounded-full uppercase tracking-wider">
              {lang === 'hi' ? 'अनुरोध सफलतापूर्वक प्राप्त हुआ' : 'Request Submitted Successfully'}
            </span>
            <h2 className="text-2xl font-black text-slate-900 mt-2">
              {lang === 'hi' ? 'अपॉइंटमेंट टोकन' : 'Appointment Booking Ticket'}
            </h2>
            <p className="text-xs text-slate-500 mt-1">
              {lang === 'hi'
                ? 'आपका अनुरोध स्वास्थ्य प्रदाता डैशबोर्ड पर भेज दिया गया है'
                : 'Your request has been delivered to the healthcare provider dashboard'}
            </p>
          </div>

          {/* Ticket Card Details */}
          <div className="bg-gradient-to-br from-slate-900 to-sky-950 text-white p-5 rounded-3xl text-left shadow-md space-y-3 relative overflow-hidden">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <div className="flex items-center gap-2">
                <Ticket className="w-5 h-5 text-amber-400" />
                <span className="font-mono font-bold text-amber-300 text-sm">
                  TICKET #{confirmedTicket.id || 'JAN-9012'}
                </span>
              </div>
              <span className="bg-amber-400 text-slate-950 font-black text-[10px] px-2.5 py-0.5 rounded-full uppercase">
                {confirmedTicket.status || 'PENDING'}
              </span>
            </div>

            <div className="space-y-1.5 text-xs">
              <div className="text-slate-400 font-semibold uppercase text-[10px]">Hospital / Facility</div>
              <div className="font-extrabold text-base text-white">{confirmedTicket.facility_name}</div>
              
              <div className="grid grid-cols-2 gap-2 pt-2 border-t border-slate-800/80">
                <div>
                  <div className="text-slate-400 font-semibold text-[10px]">Patient Name</div>
                  <div className="font-bold text-sky-200">{confirmedTicket.patient_name}</div>
                </div>
                <div>
                  <div className="text-slate-400 font-semibold text-[10px]">Contact Phone</div>
                  <div className="font-bold text-sky-200">{confirmedTicket.phone}</div>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-2 pt-2 border-t border-slate-800/80">
                <div>
                  <div className="text-slate-400 font-semibold text-[10px]">Date & Time</div>
                  <div className="font-bold text-amber-300">{confirmedTicket.date} @ {confirmedTicket.time}</div>
                </div>
                <div>
                  <div className="text-slate-400 font-semibold text-[10px]">Service / Department</div>
                  <div className="font-bold text-amber-300">{confirmedTicket.service}</div>
                </div>
              </div>
            </div>
          </div>

          {/* Ticket Action Buttons */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-2">
            <button
              onClick={() => alert(lang === 'hi' ? 'टोकन डाउनलोड हो गया है।' : 'Ticket saved to offline PWA storage!')}
              className="bg-slate-900 hover:bg-slate-800 text-white font-extrabold py-3.5 px-4 rounded-2xl text-xs flex items-center justify-center gap-2 transition"
            >
              <Download className="w-4 h-4 text-amber-400" />
              <span>{lang === 'hi' ? 'टोकन सहेजें (Save Ticket)' : 'Save / Print Ticket'}</span>
            </button>

            <button
              onClick={() => setActiveScreen('home')}
              className="bg-sky-700 hover:bg-sky-800 text-white font-extrabold py-3.5 px-4 rounded-2xl text-xs flex items-center justify-center gap-2 transition"
            >
              <span>{lang === 'hi' ? 'मुख्य पृष्ठ पर लौटें' : 'Return to Home'}</span>
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
