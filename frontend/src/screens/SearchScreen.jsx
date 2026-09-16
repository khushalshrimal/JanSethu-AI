import React, { useState } from 'react';
import { Search, MapPin, Stethoscope, Filter, Building, Check } from 'lucide-react';
import DemoBadge from '../components/DemoBadge';

export default function SearchScreen({ setActiveScreen, setSelectedFacility, lang }) {
  const [city, setCity] = useState('Jaipur');
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedService, setSelectedService] = useState('All');
  const [facilityType, setFacilityType] = useState('All');

  const servicesList = [
    { id: 'All', en: 'All Services', hi: 'सभी सेवाएं' },
    { id: 'General OPD', en: 'General OPD', hi: 'सामान्य ओपीडी' },
    { id: 'Fever Clinic', en: 'Fever Clinic', hi: 'बुखार क्लिनिक' },
    { id: 'Maternity', en: 'Maternity & Child', hi: 'प्रसूति एवं बाल देखभाल' },
    { id: 'Vaccination', en: 'Child Vaccine', hi: 'बाल टीकाकरण' },
    { id: 'Dental', en: 'Dental OPD', hi: 'दंत चिकित्सा' }
  ];

  const typesList = [
    { id: 'All', en: 'All Types', hi: 'सभी प्रकार' },
    { id: 'Hospital', en: 'District Hospital', hi: 'जिला अस्पताल' },
    { id: 'PHC', en: 'PHC (Primary Centre)', hi: 'प्राथमिक केंद्र (PHC)' },
    { id: 'CHC', en: 'CHC (Community Centre)', hi: 'सामुदायिक केंद्र (CHC)' },
    { id: 'Mobile', en: 'Mobile Health Van', hi: 'मोबाइल स्वास्थ्य वैन' }
  ];

  const handleSearch = (e) => {
    e.preventDefault();
    setActiveScreen('facilities');
  };

  return (
    <div className="space-y-6 pb-6">
      {/* Title */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-extrabold text-slate-900 flex items-center gap-2">
            <Search className="w-6 h-6 text-sky-600" />
            {lang === 'hi' ? 'स्वास्थ्य केंद्र खोजें' : 'Search Healthcare Facilities'}
          </h2>
          <p className="text-xs text-slate-500 mt-0.5">
            {lang === 'hi'
              ? 'स्थान, ओपीडी सेवा या अस्पताल के प्रकार से खोजें'
              : 'Find hospitals, PHCs, & clinics by city or specialty'}
          </p>
        </div>
        <DemoBadge lang={lang} />
      </div>

      {/* Search Form */}
      <form onSubmit={handleSearch} className="bg-white p-5 rounded-3xl border border-slate-200 shadow-sm space-y-5">
        
        {/* Search Bar Input */}
        <div>
          <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-2">
            {lang === 'hi' ? 'खोजें (अस्पताल/बीमारी/क्षेत्र)' : 'Search Term / Area'}
          </label>
          <div className="relative">
            <Search className="w-5 h-5 text-slate-400 absolute left-3.5 top-3.5" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder={lang === 'hi' ? 'उदा. सांगानेर, बुखार, या जिला अस्पताल...' : 'e.g., Sanganer, Fever, Civil Hospital...'}
              className="w-full bg-slate-50 border border-slate-300 rounded-2xl pl-11 pr-4 py-3 text-sm font-semibold text-slate-900 focus:outline-none focus:ring-2 focus:ring-sky-600 focus:bg-white transition"
            />
          </div>
        </div>

        {/* Location / City Selector */}
        <div>
          <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-2">
            {lang === 'hi' ? 'शहर / जिला' : 'City / District'}
          </label>
          <div className="flex gap-2">
            {['Jaipur', 'New Delhi'].map((c) => (
              <button
                type="button"
                key={c}
                onClick={() => setCity(c)}
                className={`flex-1 py-3 px-4 rounded-xl text-xs font-extrabold flex items-center justify-center gap-2 border transition ${
                  city === c
                    ? 'bg-sky-700 text-white border-sky-700 shadow-sm'
                    : 'bg-slate-50 text-slate-700 border-slate-200 hover:bg-slate-100'
                }`}
              >
                <MapPin className="w-4 h-4" />
                <span>{c}</span>
              </button>
            ))}
          </div>
        </div>

        {/* Service Filter Chips */}
        <div>
          <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-2">
            {lang === 'hi' ? 'आवश्यक सेवा / ओपीडी' : 'Required Service / Specialty'}
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
                  <span>{lang === 'hi' ? s.hi : s.en}</span>
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
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
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
                {lang === 'hi' ? t.hi : t.en}
              </button>
            ))}
          </div>
        </div>

        {/* Submit Big Button */}
        <button
          type="submit"
          className="w-full bg-sky-700 hover:bg-sky-800 text-white font-extrabold py-4 rounded-2xl shadow-lg flex items-center justify-center gap-2 transition active:scale-95 text-base"
        >
          <Search className="w-5 h-5 text-amber-300" />
          <span>{lang === 'hi' ? 'स्वास्थ्य केंद्र परिणाम देखें' : 'Show Matching Facilities'}</span>
        </button>
      </form>
    </div>
  );
}
