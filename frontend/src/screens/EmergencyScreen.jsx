import React, { useEffect, useState } from 'react';
import { PhoneCall, AlertOctagon, ShieldAlert, HeartPulse, Building2, MapPin, ExternalLink, UserCheck, Share2, Info } from 'lucide-react';
import { getEmergencyInfo, getEmergencyFacilities } from '../api';
import DemoBadge from '../components/DemoBadge';

export default function EmergencyScreen({ lang }) {
  const [emergencyData, setEmergencyData] = useState(null);
  const [emergencyHospitals, setEmergencyHospitals] = useState([]);
  const [userLocation, setUserLocation] = useState('Sanganer, Jaipur, Rajasthan 302029');

  useEffect(() => {
    async function loadData() {
      try {
        const [emRes, facRes] = await Promise.all([
          getEmergencyInfo(),
          getEmergencyFacilities()
        ]);
        setEmergencyData(emRes);
        setEmergencyHospitals(facRes);
      } catch (err) {
        console.error(err);
      }
    }
    loadData();
  }, []);

  return (
    <div className="space-y-6 pb-6">
      {/* Title Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-extrabold text-rose-950 flex items-center gap-2">
            <PhoneCall className="w-6 h-6 text-rose-600 animate-pulse" />
            {lang === 'hi' ? 'आपातकालीन सहायता (Emergency Access)' : 'Emergency Medical Access'}
          </h2>
          <p className="text-xs text-rose-800 mt-0.5 font-medium">
            {lang === 'hi'
              ? '24 घंटे निःशुल्क राष्ट्रीय एम्बुलेंस एवं हेल्पलाइन'
              : 'Immediate escalation to human emergency dispatchers'}
          </p>
        </div>
        <DemoBadge lang={lang} />
      </div>

      {/* POTENTIAL EMERGENCY ALERT BANNER WHEN ESCALATED */}
      <div className="bg-rose-900 text-white p-5 rounded-3xl shadow-xl border-2 border-rose-500 space-y-3">
        <div className="flex items-center justify-between">
          <span className="bg-amber-400 text-slate-950 font-black text-xs px-3 py-1 rounded-full uppercase tracking-wider flex items-center gap-1">
            <AlertOctagon className="w-3.5 h-3.5 text-slate-950" />
            🚨 POTENTIAL EMERGENCY DETECTED
          </span>
          <span className="text-[11px] font-bold text-rose-200">Routine OPD Booking Paused</span>
        </div>

        <div className="space-y-1">
          <h3 className="text-lg font-black text-amber-300">
            {lang === 'hi'
              ? 'गंभीर आपात स्थिति: नियमित अपॉइंटमेंट बुकिंग रोकी गई'
              : 'Emergency Escalation Protocol Initiated'}
          </h3>
          <p className="text-xs text-rose-100 leading-relaxed font-medium">
            {lang === 'hi'
              ? 'श्वसन संबंधी या गंभीर लक्षण पाए गए ("Mere papa ko saans lene mein bahut dikkat ho rahi hai")। तुरंत 108 एम्बुलेंस से संपर्क करें या नजदीकी आपातकालीन अस्पताल जाएं।'
              : 'Reported symptoms indicate severe respiratory distress ("Mere papa ko saans lene mein bahut dikkat ho rahi hai"). Standard routine OPD booking is paused. Immediate emergency dispatch is strongly advised.'}
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-2.5 pt-1">
          <a
            href="tel:108"
            className="bg-amber-400 hover:bg-amber-300 text-slate-950 font-black px-4 py-2.5 rounded-xl text-xs flex items-center gap-1.5 shadow transition"
          >
            <PhoneCall className="w-4 h-4 text-slate-950" />
            <span>[ CALL 108 EMERGENCY ]</span>
          </a>

          <a
            href="#emergency-facilities"
            className="bg-white/10 hover:bg-white/20 text-white font-extrabold px-4 py-2.5 rounded-xl text-xs border border-rose-300/40 flex items-center gap-1.5 transition"
          >
            <Building2 className="w-4 h-4 text-amber-300" />
            <span>[ FIND EMERGENCY FACILITY ]</span>
          </a>
        </div>
      </div>

      {/* STRICT NON-DIAGNOSTIC SAFETY DISCLAIMER BANNER */}
      <div className="bg-rose-950 text-white p-5 rounded-3xl shadow-xl border-2 border-rose-600 space-y-2">
        <div className="flex items-center gap-3">
          <AlertOctagon className="w-7 h-7 text-amber-400 flex-shrink-0 animate-bounce" />
          <h3 className="font-black text-lg text-amber-300">
            {lang === 'hi' ? 'सुरक्षा चेतावनी (Non-Diagnostic System)' : 'Safety Notice & Policy'}
          </h3>
        </div>
        <p className="text-xs text-rose-100 leading-relaxed font-medium">
          {lang === 'hi'
            ? 'जनसेतु AI केवल एक स्वास्थ्य पहुँच और नेविगेशन प्लेटफ़ॉर्म है। यह कोई डॉक्टरी सलाह, लक्षणों का निदान, या चिकित्सा उपचार प्रदान नहीं करता है। गंभीर या जानलेवा आपात स्थिति में तुरंत एम्बुलेंस 108 पर कॉल करें।'
            : 'JanSethu AI is an access and navigation platform only. It DOES NOT provide medical diagnosis, treatment recommendations, or automated symptom triage. For urgent or life-threatening medical emergencies, dial National Ambulance Dispatcher 108 immediately.'}
        </p>
      </div>

      {/* PROMINENT 1-TAP 108 AMBULANCE DIAL BUTTON */}
      <div className="bg-gradient-to-br from-rose-600 via-rose-700 to-red-800 text-white p-6 rounded-3xl shadow-xl space-y-3">
        <div className="flex items-center justify-between">
          <span className="bg-amber-400 text-slate-950 font-black text-xs px-3 py-1 rounded-full uppercase tracking-wider">
            {lang === 'hi' ? '1-टैप एम्बुलेंस कॉल' : 'Direct Emergency Call'}
          </span>
          <span className="text-xs text-rose-200 font-bold">24/7 Free Helpline</span>
        </div>

        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="space-y-1">
            <h3 className="text-3xl font-black">
              {lang === 'hi' ? 'एम्बुलेंस कॉल करें: 108' : 'Call Ambulance: 108'}
            </h3>
            <p className="text-xs text-rose-100 font-medium">
              {lang === 'hi'
                ? 'राष्ट्रीय आपातकालीन एम्बुलेंस सेवा ऑपरेटर से तुरंत बात करें'
                : 'Connects directly to National Emergency Ambulance Service Dispatcher'}
            </p>
          </div>

          <a
            href="tel:108"
            className="bg-white hover:bg-amber-100 text-rose-700 font-black px-6 py-4 rounded-2xl text-base shadow-xl flex items-center justify-center gap-3 transition transform active:scale-95"
          >
            <PhoneCall className="w-6 h-6 text-rose-600 animate-pulse" />
            <span>{lang === 'hi' ? '108 डायल करें' : 'DIAL 108 NOW'}</span>
          </a>
        </div>
      </div>

      {/* EMERGENCY LOCATION READ-OUT CARD FOR 108 DISPATCHER */}
      <div className="bg-white p-4 rounded-2xl border border-rose-200 shadow-sm space-y-2">
        <div className="flex items-center justify-between text-xs font-bold text-slate-700">
          <span className="flex items-center gap-1.5 text-rose-800 font-extrabold">
            <MapPin className="w-4 h-4 text-rose-600" />
            {lang === 'hi' ? 'ऑपरेटर को बताने के लिए आपका पता:' : 'Location to read out to 108 dispatcher:'}
          </span>
          <span className="bg-slate-100 text-slate-600 text-[10px] px-2 py-0.5 rounded">GPS Active</span>
        </div>
        <div className="bg-rose-50/70 p-3 rounded-xl font-mono text-xs font-bold text-slate-900 border border-rose-100 flex items-center justify-between">
          <span>📍 {userLocation}</span>
          <button
            onClick={() => alert(lang === 'hi' ? 'स्थान कॉपी हो गया' : 'Location address copied!')}
            className="text-[10px] text-sky-700 font-bold underline ml-2"
          >
            Copy
          </button>
        </div>
      </div>

      {/* HUMAN HELPLINES DIRECTORY */}
      <div className="bg-white p-5 rounded-3xl border border-slate-200 shadow-sm space-y-4">
        <div className="border-b border-slate-100 pb-3">
          <h3 className="font-extrabold text-slate-900 text-base flex items-center gap-2">
            <ShieldAlert className="w-5 h-5 text-rose-600" />
            {lang === 'hi' ? 'मानव परामर्शदाता एवं आपातकालीन हेल्पलाइन' : 'Human Operator Helplines & Advice'}
          </h3>
          <p className="text-xs text-slate-500 mt-0.5">
            {lang === 'hi'
              ? 'सरकारी चिकित्सकों और सलाहकारों से सीधे बात करें'
              : 'Direct telephone access to qualified medical advisors & emergency workers'}
          </p>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          {(emergencyData?.contacts || []).map((c, idx) => (
            <div
              key={idx}
              className="p-4 rounded-2xl border border-slate-200 bg-slate-50/70 hover:bg-rose-50/50 hover:border-rose-300 transition flex items-center justify-between gap-3"
            >
              <div>
                <div className="font-extrabold text-slate-900 text-sm">
                  {lang === 'hi' ? c.title_hi : c.title}
                </div>
                <div className="text-xs text-slate-500 mt-0.5">
                  {lang === 'hi' ? c.description_hi : c.description}
                </div>
              </div>

              <a
                href={`tel:${c.number.split('/')[0].trim()}`}
                className="bg-rose-600 hover:bg-rose-700 text-white font-black px-3.5 py-2.5 rounded-xl text-xs shadow transition flex items-center gap-1.5 whitespace-nowrap"
              >
                <PhoneCall className="w-3.5 h-3.5" />
                <span>Call {c.number}</span>
              </a>
            </div>
          ))}
        </div>
      </div>

      {/* NEARBY EMERGENCY HOSPITALS LIST */}
      <div className="bg-white p-5 rounded-3xl border border-slate-200 shadow-sm space-y-4">
        <div className="border-b border-slate-100 pb-3">
          <h3 className="font-extrabold text-slate-900 text-base flex items-center gap-2">
            <Building2 className="w-5 h-5 text-sky-600" />
            {lang === 'hi' ? 'नजदीकी आपातकालीन वार्ड अस्पताल' : 'Nearby Hospitals with 24/7 Emergency Wards'}
          </h3>
          <p className="text-xs text-slate-500 mt-0.5">
            {lang === 'hi'
              ? 'डेटाबेस से सत्यापित नजदीकी आपातकालीन केंद्र'
              : 'Hospitals from SQLite database providing emergency trauma care'}
          </p>
        </div>

        <div className="space-y-3">
          {emergencyHospitals.map(h => (
            <div
              key={h.id}
              className="p-4 bg-slate-50 border border-slate-200 rounded-2xl flex flex-col sm:flex-row sm:items-center justify-between gap-3"
            >
              <div>
                <span className="inline-block bg-rose-100 text-rose-900 font-extrabold text-[10px] uppercase px-2.5 py-0.5 rounded-full mb-1">
                  24/7 Emergency Care
                </span>
                <div className="font-extrabold text-slate-900 text-base">{h.name}</div>
                <div className="text-xs text-slate-600 mt-0.5">📍 {h.address}</div>
                <div className="text-[11px] text-slate-500 mt-1">🩺 {h.services}</div>
              </div>

              <div className="flex items-center gap-2 self-start sm:self-center">
                <a
                  href={`tel:${h.contact_phone}`}
                  className="bg-rose-600 hover:bg-rose-700 text-white font-extrabold text-xs px-3.5 py-2.5 rounded-xl shadow flex items-center gap-1.5 whitespace-nowrap"
                >
                  <PhoneCall className="w-3.5 h-3.5" />
                  <span>Call Hospital</span>
                </a>

                <a
                  href={`https://www.google.com/maps/dir/?api=1&destination=${h.latitude},${h.longitude}`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="bg-white border border-slate-300 hover:bg-slate-100 text-slate-800 font-bold text-xs px-3 py-2.5 rounded-xl shadow-sm flex items-center gap-1"
                >
                  <span>GPS</span>
                  <ExternalLink className="w-3 h-3 text-sky-600" />
                </a>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
