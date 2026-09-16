import React, { useEffect, useState } from 'react';
import { PhoneCall, AlertOctagon, ShieldAlert, HeartPulse, Building2, MapPin, ExternalLink } from 'lucide-react';
import { getEmergencyInfo, getFacilities } from '../api';
import DemoBadge from '../components/DemoBadge';

export default function EmergencyScreen({ lang }) {
  const [emergencyData, setEmergencyData] = useState(null);
  const [emergencyHospitals, setEmergencyHospitals] = useState([]);

  useEffect(() => {
    async function loadEmergencyData() {
      try {
        const [emRes, facRes] = await Promise.all([
          getEmergencyInfo(),
          getFacilities()
        ]);
        setEmergencyData(emRes);
        setEmergencyHospitals(facRes);
      } catch (err) {
        console.error(err);
      }
    }
    loadEmergencyData();
  }, []);

  return (
    <div className="space-y-6 pb-6">
      {/* Title Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-extrabold text-rose-950 flex items-center gap-2">
            <PhoneCall className="w-6 h-6 text-rose-600 animate-pulse" />
            {lang === 'hi' ? 'आपातकालीन सहायता (Emergency Help)' : 'Emergency Healthcare Services'}
          </h2>
          <p className="text-xs text-rose-800 mt-0.5 font-medium">
            {lang === 'hi'
              ? '24 घंटे निःशुल्क एम्बुलेंस एवं आपातकालीन सहायता'
              : 'Direct helpline dials for urgent medical emergencies'}
          </p>
        </div>
        <DemoBadge lang={lang} />
      </div>

      {/* Critical Disclaimer Alert */}
      <div className="bg-rose-600 text-white p-5 rounded-3xl shadow-lg border-2 border-rose-700 flex items-start gap-4">
        <AlertOctagon className="w-8 h-8 text-amber-300 flex-shrink-0 mt-0.5 animate-bounce" />
        <div>
          <h3 className="font-extrabold text-lg">
            {lang === 'hi' ? 'आपातकालीन सूचना' : 'Emergency Notice'}
          </h3>
          <p className="text-xs text-rose-100 mt-1 leading-relaxed">
            {lang === 'hi'
              ? 'गंभीर या जानलेवा आपात स्थिति में तुरंत एम्बुलेंस 108 पर कॉल करें। जनसेतु AI कोई डॉक्टरी सलाह या आपातकालीन चिकित्सा प्रदान नहीं करता है।'
              : 'For life-threatening medical emergencies, please dial 108 immediately. JanSethu AI is an access platform and does NOT provide direct medical treatment.'}
          </p>
        </div>
      </div>

      {/* Immediate 108 Big Button */}
      <a
        href="tel:108"
        className="w-full bg-gradient-to-r from-rose-600 to-red-700 hover:from-rose-700 hover:to-red-800 text-white p-6 rounded-3xl shadow-xl flex items-center justify-between transition transform active:scale-95 group"
      >
        <div className="flex items-center gap-4">
          <div className="bg-white text-rose-600 p-4 rounded-2xl shadow">
            <PhoneCall className="w-8 h-8" />
          </div>
          <div className="text-left">
            <span className="bg-amber-400 text-slate-950 font-black text-[10px] uppercase px-2.5 py-0.5 rounded-full">
              Toll-Free Ambulance
            </span>
            <h3 className="text-2xl md:text-3xl font-black mt-1">
              {lang === 'hi' ? 'एम्बुलेंस 108 पर कॉल करें' : 'Call Ambulance 108'}
            </h3>
            <p className="text-xs text-rose-100 mt-0.5">
              {lang === 'hi' ? '24/7 निःशुल्क राष्ट्रीय एम्बुलेंस सेवा' : 'National Emergency Dispatcher'}
            </p>
          </div>
        </div>
        <div className="hidden sm:block text-2xl font-black bg-white/20 px-4 py-2 rounded-2xl border border-white/30">
          108 📞
        </div>
      </a>

      {/* Helplines List */}
      <div className="bg-white p-5 rounded-3xl border border-slate-200 shadow-sm space-y-4">
        <h3 className="font-extrabold text-slate-900 text-base flex items-center gap-2">
          <ShieldAlert className="w-5 h-5 text-rose-600" />
          {lang === 'hi' ? 'राष्ट्रीय आपातकालीन नंबर' : 'National Emergency Helplines'}
        </h3>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          {(emergencyData?.contacts || []).map((c, idx) => (
            <div
              key={idx}
              className="p-4 rounded-2xl border border-slate-200 bg-slate-50 hover:bg-rose-50/50 hover:border-rose-200 transition flex items-center justify-between gap-2"
            >
              <div>
                <div className="font-bold text-slate-900 text-sm">
                  {lang === 'hi' ? c.title_hi : c.title}
                </div>
                <div className="text-xs text-slate-500 mt-0.5">
                  {lang === 'hi' ? c.description_hi : c.description}
                </div>
              </div>
              <a
                href={`tel:${c.number}`}
                className="bg-rose-600 hover:bg-rose-700 text-white font-black px-4 py-2 rounded-xl text-sm shadow transition flex items-center gap-1.5"
              >
                <span>{c.number}</span>
                <ExternalLink className="w-3.5 h-3.5" />
              </a>
            </div>
          ))}
        </div>
      </div>

      {/* Emergency Wards & Hospitals */}
      <div className="bg-white p-5 rounded-3xl border border-slate-200 shadow-sm space-y-3">
        <h3 className="font-extrabold text-slate-900 text-base flex items-center gap-2">
          <Building2 className="w-5 h-5 text-sky-600" />
          {lang === 'hi' ? 'आपातकालीन वार्ड वाले अस्पताल' : 'Hospitals with 24/7 Emergency Wards'}
        </h3>

        <div className="space-y-2.5">
          {emergencyHospitals.map(h => (
            <div
              key={h.id}
              className="p-3.5 bg-slate-50 border border-slate-200 rounded-2xl flex items-center justify-between gap-3 text-xs"
            >
              <div>
                <div className="font-bold text-slate-900 text-sm">{h.name}</div>
                <div className="text-slate-600 mt-0.5">📍 {h.area}, {h.city}</div>
              </div>
              <a
                href={`tel:${h.contact_phone}`}
                className="bg-sky-700 hover:bg-sky-800 text-white font-bold px-3 py-2 rounded-xl whitespace-nowrap shadow-sm"
              >
                📞 {h.contact_phone}
              </a>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
