import React, { useEffect, useState } from 'react';
import { Building2, MapPin, Phone, Calendar, ArrowRight, Map, RefreshCw, AlertTriangle, ExternalLink } from 'lucide-react';
import { getFacilities } from '../api';
import DemoBadge from '../components/DemoBadge';
import FacilityMap from '../components/FacilityMap';

export default function FacilityResultsScreen({ setActiveScreen, setSelectedFacility, lang }) {
  const [facilities, setFacilities] = useState([]);
  const [loading, setLoading] = useState(true);
  const [viewMode, setViewMode] = useState('list'); // 'list' | 'map'
  const [focusedFacility, setFocusedFacility] = useState(null);

  useEffect(() => {
    async function loadData() {
      setLoading(true);
      try {
        const data = await getFacilities();
        setFacilities(data);
        if (data.length > 0) {
          setFocusedFacility(data[0]);
        }
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
              ? 'डेटाबेस से प्राप्त सत्यापित स्वास्थ्य केंद्र (लाइव मानचित्र)'
              : 'Government hospitals, PHCs, & clinics from database'}
          </p>
        </div>
        <DemoBadge lang={lang} />
      </div>

      {/* Map vs List View Mode Toggle */}
      <div className="flex items-center justify-between bg-white p-2.5 rounded-2xl border border-slate-200 shadow-sm">
        <span className="text-xs font-bold text-slate-700 ml-2">
          {lang === 'hi' ? 'दृश्य का प्रकार:' : 'Display Mode:'}
        </span>
        <div className="flex gap-2">
          <button
            onClick={() => setViewMode('list')}
            className={`px-3 py-1.5 rounded-xl text-xs font-bold transition flex items-center gap-1.5 ${
              viewMode === 'list'
                ? 'bg-sky-700 text-white shadow'
                : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
            }`}
          >
            📋 <span>{lang === 'hi' ? 'सूची दृश्य' : 'List View'}</span>
          </button>
          
          <button
            onClick={() => setViewMode('map')}
            className={`px-3 py-1.5 rounded-xl text-xs font-bold flex items-center gap-1.5 transition ${
              viewMode === 'map'
                ? 'bg-sky-700 text-white shadow'
                : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
            }`}
          >
            <Map className="w-3.5 h-3.5" />
            <span>{lang === 'hi' ? 'नक्शा (Leaflet Map)' : 'Interactive Map'}</span>
          </button>
        </div>
      </div>

      {/* MAP VIEW */}
      {viewMode === 'map' && (
        <FacilityMap
          facilities={facilities}
          selectedFacility={focusedFacility}
          onSelectFacility={handleSelectFacility}
          lang={lang}
        />
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
        /* LIST VIEW */
        viewMode === 'list' && (
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
                  <div className="flex items-center justify-between font-medium">
                    <div className="flex items-center gap-1.5">
                      <MapPin className="w-4 h-4 text-slate-400 flex-shrink-0" />
                      <span>{fac.address}</span>
                    </div>
                    
                    {/* Directions Link */}
                    <a
                      href={`https://www.google.com/maps/dir/?api=1&destination=${fac.latitude},${fac.longitude}`}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-sky-700 hover:text-sky-900 font-bold text-[11px] flex items-center gap-1 whitespace-nowrap ml-2"
                    >
                      <span>GPS Maps</span>
                      <ExternalLink className="w-3 h-3" />
                    </a>
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
        )
      )}
    </div>
  );
}
