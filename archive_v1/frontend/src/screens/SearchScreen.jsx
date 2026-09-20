import React, { useState } from 'react';
import { Search, MapPin, Stethoscope, Filter, Building, Check, RefreshCw, Sparkles, ShieldCheck } from 'lucide-react';
import DemoBadge from '../components/DemoBadge';

export default function SearchScreen({ setActiveScreen, setSelectedFacility, lang }) {
  const [city, setCity] = useState('Baramati');
  const [searchQuery, setSearchQuery] = useState('Baramati');
  const [selectedService, setSelectedService] = useState('General OPD');
  const [facilityType, setFacilityType] = useState('All');
  const [searching, setSearching] = useState(false);

  const servicesList = [
    { id: 'All', en: 'All Services', hi: 'सभी सेवाएं', mr: 'सर्व सेवा' },
    { id: 'General OPD', en: 'General OPD', hi: 'सामान्य ओपीडी', mr: 'सामान्य ओपीडी' },
    { id: 'Fever Clinic', en: 'Fever Clinic', hi: 'बुखार क्लिनिक', mr: 'ताप क्लिनिक' },
    { id: 'Maternity', en: 'Maternity & Child', hi: 'प्रसूति एवं बाल देखभाल', mr: 'प्रसूती व बाल संगोपन' },
    { id: 'Vaccination', en: 'Child Vaccine', hi: 'बाल टीकाकरण', mr: 'बाल लसीकरण' },
    { id: 'Dental', en: 'Dental OPD', hi: 'दंत चिकित्सा', mr: 'दंत सेवा' }
  ];

  const typesList = [
    { id: 'All', en: 'All Types', hi: 'सभी प्रकार', mr: 'सर्व प्रकार' },
    { id: 'Hospital', en: 'District Hospital', hi: 'जिला अस्पताल', mr: 'जिल्हा रुग्णालय' },
    { id: 'PHC', en: 'PHC (Primary Centre)', hi: 'प्राथमिक केंद्र (PHC)', mr: 'प्राथमिक आरोग्य केंद्र (PHC)' },
    { id: 'CHC', en: 'CHC (Community Centre)', hi: 'सामुदायिक केंद्र (CHC)', mr: 'समुदाय केंद्र (CHC)' }
  ];

  const handleSearch = (e) => {
    e.preventDefault();
    setSearching(true);
    setTimeout(() => {
      setSearching(false);
      setActiveScreen('facilities');
    }, 1200);
  };

  return (
    <div className="space-y-6 pb-6">
      {/* Title */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-extrabold text-slate-900 flex items-center gap-2">
            <Search className="w-6 h-6 text-sky-600" />
            {lang === 'hi' ? 'स्मार्ट स्वास्थ्य केंद्र खोजें' : lang === 'mr' ? 'स्मार्ट आरोग्य केंद्र शोधा' : 'Smart Healthcare Facility Search'}
          </h2>
          <p className="text-xs text-slate-500 mt-0.5">
            {lang === 'hi'
              ? 'दूरी, डॉक्टर उपलब्धता और सेवा के आधार पर स्मार्ट रूटिंग'
              : 'Multi-factor routing considering distance, service match, and doctor availability'}
          </p>
        </div>
        <DemoBadge lang={lang} />
      </div>

      {/* Search Form */}
      <form onSubmit={handleSearch} className="bg-white p-5 rounded-3xl border border-slate-200 shadow-sm space-y-5">
        
        {/* Search Bar Input (Village / Area / PIN) */}
        <div>
          <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-2">
            {lang === 'hi' ? 'गांव / क्षेत्र / पिन कोड' : lang === 'mr' ? 'गाव / परिसर / पिन कोड' : 'Village / Area / PIN Code'}
          </label>
          <div className="relative">
            <MapPin className="w-5 h-5 text-slate-400 absolute left-3.5 top-3.5" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder={lang === 'hi' ? 'उदा. बारामती, 413102, सांगानेर...' : 'e.g., Baramati, 413102, Sanganer...'}
              className="w-full bg-slate-50 border border-slate-300 rounded-2xl pl-11 pr-4 py-3 text-sm font-semibold text-slate-900 focus:outline-none focus:ring-2 focus:ring-sky-600 focus:bg-white transition"
            />
          </div>
        </div>

        {/* Location / City Selector */}
        <div>
          <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-2">
            {lang === 'hi' ? 'त्वरित क्षेत्र (Quick Areas)' : 'Quick Sample Areas'}
          </label>
          <div className="flex flex-wrap gap-2">
            {['Baramati', 'Sanganer', 'Sitapura', 'Malviya Nagar'].map((c) => (
              <button
                type="button"
                key={c}
                onClick={() => {
                  setCity(c);
                  setSearchQuery(c);
                }}
                className={`py-2 px-3 rounded-xl text-xs font-extrabold flex items-center gap-1.5 border transition ${
                  searchQuery === c
                    ? 'bg-sky-700 text-white border-sky-700 shadow-sm'
                    : 'bg-slate-50 text-slate-700 border-slate-200 hover:bg-slate-100'
                }`}
              >
                <MapPin className="w-3.5 h-3.5" />
                <span>{c}</span>
              </button>
            ))}
          </div>
        </div>

        {/* Service Filter Chips */}
        <div>
          <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-2">
            {lang === 'hi' ? 'आवश्यक सेवा / ओपीडी' : 'Required Service / OPD'}
          </label>
          <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
            {servicesList.map((s) => {
              const isSelected = selectedService === s.id;
              return (
                <button
                  type="button"
                  key={s.id}
                  onClick={() => setSelectedService(s.id)}
                  className={`p-2.5 rounded-xl text-xs font-bold border transition text-left flex items-center justify-between ${
                    isSelected
                      ? 'bg-emerald-50 text-emerald-900 border-emerald-400 font-extrabold'
                      : 'bg-slate-50 text-slate-700 border-slate-200 hover:bg-slate-100'
                  }`}
                >
                  <span>{lang === 'hi' ? s.hi : lang === 'mr' ? s.mr : s.en}</span>
                  {isSelected && <Check className="w-4 h-4 text-emerald-600" />}
                </button>
              );
            })}
          </div>
        </div>

        {/* Facility Type Filter */}
        <div>
          <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-2">
            {lang === 'hi' ? 'केंद्र का प्रकार' : 'Facility Category'}
          </label>
          <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
            {typesList.map((t) => (
              <button
                type="button"
                key={t.id}
                onClick={() => setFacilityType(t.id)}
                className={`p-2.5 rounded-xl text-[11px] font-bold border text-center transition ${
                  facilityType === t.id
                    ? 'bg-sky-100 text-sky-900 border-sky-400 font-extrabold'
                    : 'bg-slate-50 text-slate-600 border-slate-200 hover:bg-slate-100'
                }`}
              >
                {lang === 'hi' ? t.hi : lang === 'mr' ? t.mr : t.en}
              </button>
            ))}
          </div>
        </div>

        {/* Search Status Verification Checklist (Shown during search) */}
        {searching ? (
          <div className="bg-slate-900 text-white p-4 rounded-2xl space-y-2 border border-sky-500/50 shadow-lg text-xs font-mono">
            <div className="flex items-center gap-2 text-amber-300 font-extrabold border-b border-slate-800 pb-2">
              <RefreshCw className="w-4 h-4 animate-spin text-amber-400" />
              <span>Evaluating Smart Routing Factors...</span>
            </div>
            <div className="space-y-1 text-slate-300 text-[11px]">
              <div className="flex items-center gap-1.5 text-emerald-400 font-bold">✓ Location & PIN matched ({searchQuery})</div>
              <div className="flex items-center gap-1.5 text-emerald-400 font-bold">✓ Service requirement verified ({selectedService})</div>
              <div className="flex items-center gap-1.5 text-amber-300 font-bold animate-pulse">⚡ Checking SQLite doctor slot availability...</div>
              <div className="flex items-center gap-1.5 text-slate-400">⏳ Ranking suitable available facilities over closer unavailable clinics...</div>
            </div>
          </div>
        ) : (
          /* Submit Big Button */
          <button
            type="submit"
            className="w-full bg-sky-700 hover:bg-sky-800 text-white font-extrabold py-4 rounded-2xl shadow-lg flex items-center justify-center gap-2 transition active:scale-95 text-base"
          >
            <Sparkles className="w-5 h-5 text-amber-300" />
            <span>{lang === 'hi' ? 'स्मार्ट रूटिंग परिणाम देखें' : 'Run Smart Facility Routing'}</span>
          </button>
        )}
      </form>
    </div>
  );
}
