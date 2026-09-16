import React from 'react';
import { Mic, Search, PhoneCall, Building2, Calendar, Stethoscope, HeartPulse, ShieldAlert } from 'lucide-react';
import DemoBadge from '../components/DemoBadge';

export default function HomeScreen({ setActiveScreen, lang }) {
  return (
    <div className="space-y-6 pb-6">
      {/* Top Banner & Hero */}
      <div className="bg-gradient-to-br from-sky-700 via-sky-800 to-indigo-900 text-white rounded-3xl p-6 shadow-md relative overflow-hidden">
        <div className="flex items-center justify-between mb-3">
          <span className="bg-amber-400 text-slate-950 text-xs font-black px-3 py-1 rounded-full uppercase tracking-wider">
            {lang === 'hi' ? 'वॉयस-फर्स्ट प्लेटफॉर्म' : 'Voice-First Platform'}
          </span>
          <DemoBadge lang={lang} />
        </div>

        <h1 className="text-2xl md:text-3xl font-extrabold leading-tight mt-2">
          {lang === 'hi'
            ? 'स्वास्थ्य सेवा आसानी से खोजें'
            : 'Find Healthcare Access Simply'}
        </h1>
        <p className="text-sky-100 text-sm mt-1 max-w-lg leading-relaxed">
          {lang === 'hi'
            ? 'बोलकर या बटन दबाकर नजदीकी सरकारी अस्पताल, प्राथमिक स्वास्थ्य केंद्र और डॉक्टर स्लॉट खोजें।'
            : 'Voice & simple touch platform for finding government hospitals, PHCs, and doctor appointment slots.'}
        </p>

        {/* Hero Big Voice Button */}
        <div className="mt-6 flex justify-center">
          <button
            onClick={() => setActiveScreen('voice')}
            className="w-full sm:w-auto bg-amber-400 hover:bg-amber-300 text-slate-950 font-black px-6 py-4 rounded-2xl shadow-xl flex items-center justify-center gap-3 transition transform active:scale-95 text-lg"
          >
            <div className="bg-slate-950 text-amber-400 p-2.5 rounded-full animate-bounce">
              <Mic className="w-7 h-7" />
            </div>
            <span>
              {lang === 'hi' ? 'बोलकर अस्पताल खोजें' : 'Speak to Find Healthcare'}
            </span>
          </button>
        </div>
      </div>

      {/* Main Grid Actions */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        {/* Voice Assistant Card */}
        <button
          onClick={() => setActiveScreen('voice')}
          className="bg-white hover:bg-sky-50/70 border-2 border-sky-100 hover:border-sky-300 p-5 rounded-2xl shadow-sm text-left transition flex items-start gap-4"
        >
          <div className="bg-sky-100 text-sky-700 p-3 rounded-xl flex-shrink-0">
            <Mic className="w-8 h-8" />
          </div>
          <div>
            <h2 className="font-extrabold text-slate-900 text-lg">
              {lang === 'hi' ? 'आवाज सहायक' : 'Voice Assistant'}
            </h2>
            <p className="text-xs text-slate-600 mt-1 leading-relaxed">
              {lang === 'hi'
                ? 'अपनी भाषा में बोलकर अस्पताल और स्लॉट खोजें।'
                : 'Search facilities & slots by speaking in Hindi or English.'}
            </p>
          </div>
        </button>

        {/* Search Facilities Card */}
        <button
          onClick={() => setActiveScreen('search')}
          className="bg-white hover:bg-emerald-50/70 border-2 border-emerald-100 hover:border-emerald-300 p-5 rounded-2xl shadow-sm text-left transition flex items-start gap-4"
        >
          <div className="bg-emerald-100 text-emerald-700 p-3 rounded-xl flex-shrink-0">
            <Search className="w-8 h-8" />
          </div>
          <div>
            <h2 className="font-extrabold text-slate-900 text-lg">
              {lang === 'hi' ? 'अस्पताल खोजें' : 'Healthcare Search'}
            </h2>
            <p className="text-xs text-slate-600 mt-1 leading-relaxed">
              {lang === 'hi'
                ? 'शहर, क्षेत्र या बीमारी के आधार पर केंद्र खोजें।'
                : 'Browse hospitals, PHCs, & available services by area.'}
            </p>
          </div>
        </button>

        {/* Emergency Help Card */}
        <button
          onClick={() => setActiveScreen('emergency')}
          className="bg-rose-50 hover:bg-rose-100/70 border-2 border-rose-200 p-5 rounded-2xl shadow-sm text-left transition flex items-start gap-4 sm:col-span-2"
        >
          <div className="bg-rose-600 text-white p-3 rounded-xl flex-shrink-0 animate-pulse">
            <PhoneCall className="w-8 h-8" />
          </div>
          <div className="flex-1">
            <div className="flex items-center justify-between">
              <h2 className="font-extrabold text-rose-950 text-lg">
                {lang === 'hi' ? 'आपातकालीन सहायता (108)' : 'Emergency Help (108)'}
              </h2>
              <span className="bg-rose-200 text-rose-900 font-extrabold text-xs px-2.5 py-1 rounded-full">
                24/7 Helpline
              </span>
            </div>
            <p className="text-xs text-rose-800 mt-1 leading-relaxed">
              {lang === 'hi'
                ? 'एम्बुलेंस (108), स्वास्थ्य हेल्पलाइन (104), और नजदीकी आपातकालीन वार्ड।'
                : 'Ambulance (108), health helpline (104), and emergency medical ward contacts.'}
            </p>
          </div>
        </button>
      </div>

      {/* Popular Categories / Quick Chips */}
      <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm">
        <h3 className="font-bold text-slate-800 text-sm mb-3">
          {lang === 'hi' ? 'मुख्य स्वास्थ्य सेवाएं' : 'Key Healthcare Services'}
        </h3>
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          {[
            { title: lang === 'hi' ? 'बुखार / सामान्य' : 'General & Fever', icon: Stethoscope, service: 'General OPD' },
            { title: lang === 'hi' ? 'प्रसूति एवं महिला' : 'Maternity Care', icon: HeartPulse, service: 'Maternity' },
            { title: lang === 'hi' ? 'बाल टीकाकरण' : 'Child Vaccine', icon: Building2, service: 'Vaccination' },
            { title: lang === 'hi' ? 'आपातकालीन वार्ड' : 'Emergency Ward', icon: ShieldAlert, service: 'Emergency Care' }
          ].map((item, idx) => {
            const Icon = item.icon;
            return (
              <button
                key={idx}
                onClick={() => setActiveScreen('facilities')}
                className="p-3 bg-slate-50 hover:bg-sky-50 border border-slate-200 hover:border-sky-300 rounded-xl text-center flex flex-col items-center justify-center transition"
              >
                <Icon className="w-6 h-6 text-sky-700 mb-1" />
                <span className="text-xs font-bold text-slate-800">{item.title}</span>
              </button>
            );
          })}
        </div>
      </div>
    </div>
  );
}
