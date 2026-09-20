import React, { useEffect, useState } from 'react';
import { checkHealth, getFacilities, getEmergencyInfo } from '../api';
import { CheckCircle2, AlertTriangle, Building2, PhoneCall, Database, ShieldCheck } from 'lucide-react';

export default function HealthStatus({ lang }) {
  const [health, setHealth] = useState(null);
  const [facilities, setFacilities] = useState([]);
  const [emergency, setEmergency] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    async function fetchData() {
      try {
        setLoading(true);
        const [healthRes, facRes, emRes] = await Promise.all([
          checkHealth(),
          getFacilities(),
          getEmergencyInfo()
        ]);
        setHealth(healthRes);
        setFacilities(facRes);
        setEmergency(emRes);
        setError(null);
      } catch (err) {
        console.error("API Error:", err);
        setError(lang === 'hi' ? "बैकएंड सर्वर से कनेक्ट करने में विफल।" : "Failed to connect to backend server.");
      } finally {
        setLoading(false);
      }
    }
    fetchData();
  }, [lang]);

  return (
    <div className="space-y-6">
      {/* Demo Disclaimer Alert */}
      <div className="bg-amber-50 border-l-4 border-amber-500 p-4 rounded-r-xl shadow-sm">
        <div className="flex items-start gap-3">
          <AlertTriangle className="w-6 h-6 text-amber-600 flex-shrink-0 mt-0.5" />
          <div>
            <h3 className="font-bold text-amber-900 text-sm">
              {lang === 'hi' ? 'महत्वपूर्ण सूचना (डेमो प्रोटोटाइप)' : 'Important Notice (Demo Prototype)'}
            </h3>
            <p className="text-xs text-amber-800 mt-1 leading-relaxed">
              {lang === 'hi'
                ? 'यह प्रणाली केवल स्वास्थ्य सेवा पहुँच और नेविगेशन के लिए एक प्रोटोटाइप है। यह कोई डॉक्टरी सलाह या चिकित्सा निदान प्रदान नहीं करती है।'
                : 'This system is a prototype for healthcare navigation. It does NOT provide medical advice, diagnosis, or treatment.'}
            </p>
          </div>
        </div>
      </div>

      {/* Backend & DB Health Card */}
      <div className="bg-white p-5 rounded-2xl shadow-sm border border-slate-200">
        <div className="flex items-center justify-between border-b border-slate-100 pb-3 mb-4">
          <h2 className="font-bold text-slate-800 text-lg flex items-center gap-2">
            <Database className="w-5 h-5 text-sky-600" />
            {lang === 'hi' ? 'सिस्टम स्थिति और डेटाबेस' : 'System Health & Database'}
          </h2>
          {health?.status === 'ok' ? (
            <span className="inline-flex items-center gap-1.5 px-3 py-1 bg-emerald-100 text-emerald-800 text-xs font-semibold rounded-full">
              <CheckCircle2 className="w-4 h-4 text-emerald-600" />
              {lang === 'hi' ? 'ऑनलाइन' : 'Online'}
            </span>
          ) : (
            <span className="inline-flex items-center gap-1.5 px-3 py-1 bg-rose-100 text-rose-800 text-xs font-semibold rounded-full">
              <AlertTriangle className="w-4 h-4 text-rose-600" />
              {lang === 'hi' ? 'ऑफ़लाइन' : 'Offline'}
            </span>
          )}
        </div>

        {loading ? (
          <div className="py-6 text-center text-slate-500 animate-pulse">
            {lang === 'hi' ? 'कनेक्ट हो रहा है...' : 'Connecting to backend...'}
          </div>
        ) : error ? (
          <div className="p-4 bg-rose-50 text-rose-700 rounded-xl text-sm font-medium">
            {error}
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="bg-sky-50 p-4 rounded-xl border border-sky-100">
              <div className="text-xs font-medium text-sky-700">
                {lang === 'hi' ? 'बैकएंड स्थिति' : 'Backend Service'}
              </div>
              <div className="text-lg font-bold text-sky-900 mt-1">{health?.service}</div>
              <div className="text-xs text-sky-600 mt-1">v{health?.version} (SQLite)</div>
            </div>

            <div className="bg-emerald-50 p-4 rounded-xl border border-emerald-100">
              <div className="text-xs font-medium text-emerald-700">
                {lang === 'hi' ? 'उपलब्ध स्वास्थ्य केंद्र' : 'Available Facilities'}
              </div>
              <div className="text-2xl font-black text-emerald-900 mt-1">{facilities.length}</div>
              <div className="text-xs text-emerald-600 mt-1">
                {lang === 'hi' ? 'डेटाबेस से लोड हुआ' : 'Seeded in SQLite DB'}
              </div>
            </div>

            <div className="bg-purple-50 p-4 rounded-xl border border-purple-100">
              <div className="text-xs font-medium text-purple-700">
                {lang === 'hi' ? 'आपातकालीन हेल्पलाइन' : 'Emergency Contacts'}
              </div>
              <div className="text-2xl font-black text-purple-900 mt-1">
                {emergency?.contacts?.length || 0}
              </div>
              <div className="text-xs text-purple-600 mt-1">
                {lang === 'hi' ? 'राष्ट्रीय सेवाएं' : 'National Services'}
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Facilities Preview List */}
      <div className="bg-white p-5 rounded-2xl shadow-sm border border-slate-200">
        <h3 className="font-bold text-slate-800 text-base mb-3 flex items-center gap-2">
          <Building2 className="w-5 h-5 text-sky-600" />
          {lang === 'hi' ? 'पंजीकृत स्वास्थ्य सुविधाएं (चरण 1 डेटा)' : 'Registered Healthcare Facilities (Phase 1 Data)'}
        </h3>
        {facilities.length > 0 ? (
          <div className="space-y-3">
            {facilities.map((fac) => (
              <div key={fac.id} className="p-3.5 bg-slate-50 hover:bg-sky-50/50 border border-slate-200 rounded-xl transition flex flex-col md:flex-row md:items-center justify-between gap-2">
                <div>
                  <div className="font-bold text-slate-900 text-sm md:text-base">
                    {lang === 'hi' && fac.name_hi ? fac.name_hi : fac.name}
                  </div>
                  <div className="text-xs text-slate-600 mt-0.5">
                    📍 {fac.area}, {fac.city} • <span className="font-medium text-sky-700">{fac.facility_type}</span>
                  </div>
                  <div className="text-xs text-slate-500 mt-1">
                    🩺 {fac.services}
                  </div>
                </div>
                <div className="text-xs bg-white px-3 py-1.5 rounded-lg border border-slate-200 text-slate-700 font-medium self-start md:self-center">
                  📞 {fac.contact_phone}
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-sm text-slate-500 py-4">
            {lang === 'hi' ? 'कोई सुविधा नहीं मिली' : 'No facilities found'}
          </div>
        )}
      </div>

      {/* Emergency Quick Numbers */}
      {emergency && (
        <div className="bg-rose-50 border border-rose-200 p-5 rounded-2xl">
          <h3 className="font-bold text-rose-900 text-base mb-2 flex items-center gap-2">
            <PhoneCall className="w-5 h-5 text-rose-600" />
            {lang === 'hi' ? 'आपातकालीन सहायता' : 'Emergency Helplines'}
          </h3>
          <p className="text-xs text-rose-700 mb-3">
            {lang === 'hi' ? emergency.message_hi : emergency.message}
          </p>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            {emergency.contacts.map((c, idx) => (
              <div key={idx} className="bg-white p-3 rounded-xl border border-rose-200 shadow-sm flex items-center justify-between">
                <div>
                  <div className="text-xs font-bold text-slate-800">
                    {lang === 'hi' ? c.title_hi : c.title}
                  </div>
                  <div className="text-xs text-slate-500">
                    {lang === 'hi' ? c.description_hi : c.description}
                  </div>
                </div>
                <a
                  href={`tel:${c.number}`}
                  className="ml-2 bg-rose-600 text-white font-extrabold px-3 py-1.5 rounded-lg text-sm hover:bg-rose-700 transition"
                >
                  {c.number}
                </a>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
