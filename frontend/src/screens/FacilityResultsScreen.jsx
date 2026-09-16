import React, { useEffect, useState } from 'react';
import { Building2, MapPin, Phone, Calendar, ArrowRight, Map, RefreshCw, AlertTriangle } from 'lucide-react';
import { getFacilities } from '../api';
import DemoBadge from '../components/DemoBadge';

export default function FacilityResultsScreen({ setActiveScreen, setSelectedFacility, lang }) {
  const [facilities, setFacilities] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showMapMock, setShowMapMock] = useState(false);

  useEffect(() => {
    async function loadData() {
      setLoading(true);
      try {
        const data = await getFacilities();
        setFacilities(data);
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, []);

  const handleSelectFacility = (fac) => {
    setSelectedFacility(fac);
    setActiveScreen('slots');
  };

  return (
    <div className="space-y-6 pb-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-extrabold text-slate-900 flex items-center gap-2">
            <Building2 className="w-6 h-6 text-sky-600" />
            {lang === 'hi' ? 'उपलब्ध स्वास्थ्य केंद्र' : 'Healthcare Facilities'}
          </h2>
          <p className="text-xs text-slate-500 mt-0.5">
            {lang === 'hi'
              ? 'आपके क्षेत्र में 5 केंद्र पाए गए (डेमो सूची)'
              : 'Found matching government facilities near you'}
          </p>
        </div>
        <DemoBadge lang={lang} />
      </div>

      {/* Map vs List Toggle */}
      <div className="flex items-center justify-between bg-white p-2.5 rounded-2xl border border-slate-200 shadow-sm">
        <span className="text-xs font-bold text-slate-700 ml-2">
          {lang === 'hi' ? 'दृश्य बदलें:' : 'View Mode:'}
        </span>
        <div className="flex gap-2">
          <button
            onClick={() => setShowMapMock(false)}
            className={`px-3 py-1.5 rounded-xl text-xs font-bold transition ${
              !showMapMock
                ? 'bg-sky-700 text-white shadow'
                : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
            }`}
          >
            📋 {lang === 'hi' ? 'सूची दृश्य' : 'List View'}
          </button>
          <button
            onClick={() => setShowMapMock(true)}
            className={`px-3 py-1.5 rounded-xl text-xs font-bold flex items-center gap-1.5 transition ${
              showMapMock
                ? 'bg-sky-700 text-white shadow'
                : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
            }`}
          >
            <Map className="w-3.5 h-3.5" />
            <span>{lang === 'hi' ? 'नक्शा (मैप)' : 'Map Preview'}</span>
          </button>
        </div>
      </div>

      {/* Map Mock Simulation Box */}
      {showMapMock && (
        <div className="bg-sky-950 text-white rounded-3xl p-6 text-center border-2 border-sky-400 relative overflow-hidden shadow-inner min-h-[220px] flex flex-col items-center justify-center">
          <Map className="w-12 h-12 text-amber-400 animate-pulse mb-2" />
          <h3 className="font-extrabold text-base">
            {lang === 'hi' ? 'ओपनस्ट्रीटमैप लाइव व्यू (प्रोटोटाइप)' : 'OpenStreetMap Interface (Prototype)'}
          </h3>
          <p className="text-xs text-sky-200 mt-1 max-w-sm">
            {lang === 'hi'
              ? 'सांगानेर एवं जयपुर क्षेत्र के अस्पतालों के जीपीएस लोकेशन पिन'
              : 'GPS pin markers for District Hospitals, PHCs, & Health Vans in Jaipur'}
          </p>
          <div className="mt-4 flex gap-2">
            <span className="bg-sky-800 text-sky-100 text-[10px] font-bold px-2.5 py-1 rounded-full border border-sky-600">
              📍 26.8206° N, 75.8075° E
            </span>
          </div>
        </div>
      )}

      {/* Loading State */}
      {loading ? (
        <div className="bg-white p-8 rounded-3xl border border-slate-200 text-center space-y-3">
          <RefreshCw className="w-8 h-8 text-sky-600 animate-spin mx-auto" />
          <p className="text-sm font-bold text-slate-600">
            {lang === 'hi' ? 'डेटाबेस से केंद्र लोड हो रहे हैं...' : 'Fetching facilities from database...'}
          </p>
        </div>
      ) : facilities.length === 0 ? (
        /* Empty State */
        <div className="bg-white p-8 rounded-3xl border border-slate-200 text-center space-y-3">
          <AlertTriangle className="w-10 h-10 text-amber-500 mx-auto" />
          <h3 className="font-bold text-slate-800">
            {lang === 'hi' ? 'कोई केंद्र नहीं मिला' : 'No Facilities Found'}
          </h3>
          <p className="text-xs text-slate-500">
            {lang === 'hi' ? 'कृपया अपनी खोज शब्द बदलें' : 'Try broadening your search criteria.'}
          </p>
        </div>
      ) : (
        /* Facilities List */
        <div className="space-y-4">
          {facilities.map((fac) => (
            <div
              key={fac.id}
              className="bg-white border border-slate-200 rounded-3xl p-5 shadow-sm hover:shadow-md transition flex flex-col gap-3"
            >
              <div className="flex items-start justify-between gap-2">
                <div>
                  <span className="inline-block bg-sky-100 text-sky-900 font-extrabold text-[10px] uppercase px-2.5 py-0.5 rounded-full mb-1">
                    {fac.facility_type}
                  </span>
                  <h3 className="text-base md:text-lg font-black text-slate-900 leading-tight">
                    {lang === 'hi' && fac.name_hi ? fac.name_hi : fac.name}
                  </h3>
                </div>
                {fac.distance && (
                  <span className="bg-amber-100 text-amber-900 font-bold text-xs px-2.5 py-1 rounded-full whitespace-nowrap">
                    📍 {fac.distance}
                  </span>
                )}
              </div>

              <div className="text-xs text-slate-600 space-y-1">
                <div className="flex items-center gap-1.5 font-medium">
                  <MapPin className="w-4 h-4 text-slate-400 flex-shrink-0" />
                  <span>{fac.address}</span>
                </div>
                <div className="flex items-center gap-1.5 text-slate-500">
                  <Phone className="w-4 h-4 text-slate-400 flex-shrink-0" />
                  <span>{fac.contact_phone}</span>
                </div>
              </div>

              {/* Services tags */}
              <div className="pt-2 border-t border-slate-100 flex flex-wrap gap-1.5">
                {fac.services.split(',').map((s, idx) => (
                  <span key={idx} className="bg-slate-100 text-slate-700 text-[10px] font-bold px-2 py-0.5 rounded-md">
                    🩺 {s.trim()}
                  </span>
                ))}
              </div>

              {/* Select Slot Action */}
              <button
                onClick={() => handleSelectFacility(fac)}
                className="w-full mt-2 bg-sky-700 hover:bg-sky-800 text-white font-extrabold py-3 px-4 rounded-2xl shadow flex items-center justify-center gap-2 transition active:scale-95 text-xs sm:text-sm"
              >
                <Calendar className="w-4 h-4 text-amber-300" />
                <span>{lang === 'hi' ? 'उपलब्ध स्लॉट देखें एवं चुनें' : 'View & Book Available Slots'}</span>
                <ArrowRight className="w-4 h-4 ml-auto" />
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
