import React, { useEffect, useState } from 'react';
import { Calendar, Clock, UserCheck, Stethoscope, ArrowLeft, ArrowRight, CheckCircle2, AlertCircle } from 'lucide-react';
import { getFacilitySlots } from '../api';
import DemoBadge from '../components/DemoBadge';

export default function SlotSelectionScreen({ selectedFacility, setSelectedSlot, setActiveScreen, lang }) {
  const facility = selectedFacility || {
    id: 1,
    name: "District Civil Hospital (DEMO)",
    name_hi: "जिला नागरिक अस्पताल (डेमो)",
    area: "Sanganer",
    city: "Jaipur",
    address: "Tonk Road, Sanganer, Jaipur",
    contact_phone: "+91-141-2700100"
  };

  const [selectedDate, setSelectedDate] = useState('Tomorrow');
  const [slots, setSlots] = useState([]);
  const [chosenSlot, setChosenSlot] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadSlots() {
      setLoading(true);
      try {
        const data = await getFacilitySlots(facility.id);
        setSlots(data);
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    }
    loadSlots();
  }, [facility.id]);

  const handleConfirmSlot = () => {
    if (!chosenSlot) return;
    setSelectedSlot({ ...chosenSlot, facility_name: facility.name });
    setActiveScreen('confirmation');
  };

  return (
    <div className="space-y-6 pb-6">
      {/* Back button & Header */}
      <div className="flex items-center justify-between">
        <button
          onClick={() => setActiveScreen('facilities')}
          className="flex items-center gap-1.5 text-xs font-bold text-sky-700 bg-white border border-slate-200 px-3 py-1.5 rounded-xl hover:bg-sky-50 shadow-sm"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>{lang === 'hi' ? 'वापस जाएं' : 'Back to Facilities'}</span>
        </button>
        <DemoBadge lang={lang} />
      </div>

      {/* Facility Summary Header Card */}
      <div className="bg-sky-800 text-white p-5 rounded-3xl shadow-md space-y-2">
        <span className="bg-sky-900 text-amber-300 font-extrabold text-[10px] uppercase px-2.5 py-0.5 rounded-full">
          {lang === 'hi' ? 'चुना गया अस्पताल' : 'Selected Healthcare Facility'}
        </span>
        <h2 className="text-xl font-black leading-tight">
          {lang === 'hi' && facility.name_hi ? facility.name_hi : facility.name}
        </h2>
        <p className="text-xs text-sky-100">
          📍 {facility.area}, {facility.city} • 📞 {facility.contact_phone}
        </p>
      </div>

      {/* Date Filter Tabs */}
      <div className="bg-white p-2 rounded-2xl border border-slate-200 shadow-sm grid grid-cols-3 gap-2">
        {['Today', 'Tomorrow', 'Day After'].map((d) => {
          const isSelected = selectedDate === d;
          return (
            <button
              key={d}
              onClick={() => setSelectedDate(d)}
              className={`py-2.5 px-2 rounded-xl text-xs font-extrabold text-center transition ${
                isSelected
                  ? 'bg-sky-700 text-white shadow'
                  : 'bg-slate-50 text-slate-700 hover:bg-slate-100'
              }`}
            >
              📅 {d === 'Today' ? (lang === 'hi' ? 'आज' : 'Today') : d === 'Tomorrow' ? (lang === 'hi' ? 'कल' : 'Tomorrow') : (lang === 'hi' ? 'परसों' : 'Day After')}
            </button>
          );
        })}
      </div>

      {/* Slots Section */}
      <div className="bg-white p-5 rounded-3xl border border-slate-200 shadow-sm space-y-4">
        <div className="flex items-center justify-between border-b border-slate-100 pb-3">
          <h3 className="font-extrabold text-slate-900 text-sm flex items-center gap-2">
            <Clock className="w-5 h-5 text-sky-600" />
            {lang === 'hi' ? 'उपलब्ध डॉक्टर स्लॉट' : 'Available Appointment Slots'}
          </h3>
          <span className="text-xs text-slate-500 font-medium">
            {lang === 'hi' ? 'हरा = उपलब्ध, ग्रे = बुक' : 'Green = Available, Gray = Booked'}
          </span>
        </div>

        {loading ? (
          <div className="py-8 text-center text-slate-500 text-sm font-semibold animate-pulse">
            {lang === 'hi' ? 'स्लॉट लोड हो रहे हैं...' : 'Loading slots...'}
          </div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            {slots.map((s) => {
              const isChosen = chosenSlot?.id === s.id;
              const isAvailable = s.available;

              return (
                <button
                  key={s.id}
                  disabled={!isAvailable}
                  onClick={() => setChosenSlot(s)}
                  className={`p-4 rounded-2xl border text-left transition flex items-start justify-between ${
                    isChosen
                      ? 'bg-emerald-50 border-2 border-emerald-600 ring-2 ring-emerald-200 shadow-md'
                      : isAvailable
                      ? 'bg-white hover:bg-sky-50 border-slate-200 hover:border-sky-400'
                      : 'bg-slate-100 border-slate-200 text-slate-400 cursor-not-allowed opacity-70'
                  }`}
                >
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <Clock className={`w-4 h-4 ${isAvailable ? 'text-sky-600' : 'text-slate-400'}`} />
                      <span className="font-extrabold text-sm text-slate-900">{s.time}</span>
                    </div>
                    {s.doctor_name && (
                      <div className="text-xs font-bold text-slate-700 flex items-center gap-1">
                        <UserCheck className="w-3.5 h-3.5 text-slate-500" />
                        <span>{s.doctor_name}</span>
                      </div>
                    )}
                    {s.department && (
                      <div className="text-[11px] text-slate-500 font-medium flex items-center gap-1">
                        <Stethoscope className="w-3.5 h-3.5 text-slate-400" />
                        <span>{s.department}</span>
                      </div>
                    )}
                  </div>

                  <div>
                    {isChosen ? (
                      <CheckCircle2 className="w-6 h-6 text-emerald-600" />
                    ) : isAvailable ? (
                      <span className="bg-emerald-100 text-emerald-800 text-[10px] font-extrabold px-2 py-1 rounded-md">
                        {lang === 'hi' ? 'उपलब्ध' : 'Available'}
                      </span>
                    ) : (
                      <span className="bg-slate-200 text-slate-600 text-[10px] font-bold px-2 py-1 rounded-md">
                        {lang === 'hi' ? 'बुक हो गया' : 'Booked'}
                      </span>
                    )}
                  </div>
                </button>
              );
            })}
          </div>
        )}
      </div>

      {/* Action Footer */}
      <div className="bg-white p-4 rounded-3xl border border-slate-200 shadow-lg flex flex-col sm:flex-row items-center justify-between gap-3">
        <div className="text-xs text-slate-600">
          {chosenSlot ? (
            <span className="font-extrabold text-slate-900 text-sm">
              ✅ {lang === 'hi' ? 'चयनित समय:' : 'Selected:'} {chosenSlot.time} ({chosenSlot.department || 'General OPD'})
            </span>
          ) : (
            <span className="text-amber-800 font-bold flex items-center gap-1">
              <AlertCircle className="w-4 h-4 text-amber-600" />
              {lang === 'hi' ? 'कृपया आगे बढ़ने के लिए एक स्लॉट चुनें' : 'Please click a slot above to proceed'}
            </span>
          )}
        </div>

        <button
          disabled={!chosenSlot}
          onClick={handleConfirmSlot}
          className={`w-full sm:w-auto px-6 py-3.5 rounded-2xl font-extrabold text-sm shadow flex items-center justify-center gap-2 transition active:scale-95 ${
            chosenSlot
              ? 'bg-amber-400 hover:bg-amber-300 text-slate-950'
              : 'bg-slate-200 text-slate-400 cursor-not-allowed'
          }`}
        >
          <span>{lang === 'hi' ? 'अपॉइंटमेंट अनुरोध दर्ज करें' : 'Proceed to Patient Details'}</span>
          <ArrowRight className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
}
