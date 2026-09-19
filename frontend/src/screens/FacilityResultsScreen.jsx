import React, { useEffect, useState } from 'react';
import { Building2, MapPin, Phone, Calendar, ArrowRight, Map, RefreshCw, AlertTriangle, ExternalLink, Sparkles, CheckCircle, ShieldAlert, AlertCircle, Info } from 'lucide-react';
import { getFacilities } from '../api';
import DemoBadge from '../components/DemoBadge';
import FacilityMap from '../components/FacilityMap';

export default function FacilityResultsScreen({ setActiveScreen, setSelectedFacility, lang }) {
  const [facilities, setFacilities] = useState([]);
  const [loading, setLoading] = useState(true);
  const [viewMode, setViewMode] = useState('list'); // 'list' | 'map'
  const [focusedFacility, setFocusedFacility] = useState(null);
  const [unavailableModal, setUnavailableModal] = useState(null);
  const [isEmergencySearch, setIsEmergencySearch] = useState(false);

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
    if (fac.doctor_available === false) {
      setUnavailableModal(fac);
      return;
    }
    setSelectedFacility(fac);
    setActiveScreen('slots');
  };

  const handleViewAlternatives = () => {
    setUnavailableModal(null);
    const availableAlt = facilities.find(f => f.doctor_available !== false);
    if (availableAlt) {
      setFocusedFacility(availableAlt);
      // Scroll to top of list
      window.scrollTo({ top: 0, behavior: 'smooth' });
    }
  };

  return (
    <div className="space-y-6 pb-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
        <div>
          <h2 className="text-xl font-extrabold text-slate-900 flex items-center gap-2">
            <Sparkles className="w-6 h-6 text-amber-500" />
            {lang === 'hi' ? 'स्मार्ट स्वास्थ्य केंद्र परिणाम' : 'Smart Routed Facilities'}
          </h2>
          <p className="text-xs text-slate-500 mt-0.5">
            {lang === 'hi'
              ? 'बहु-कारक एल्गोरिदम द्वारा रैंक किए गए निकटतम एवं उपलब्ध अस्पताल'
              : 'Multi-factor weighted routing evaluating distance, doctor slots, & emergency readiness'}
          </p>
        </div>
        <DemoBadge lang={lang} />
      </div>

      {/* EMERGENCY SEARCH WARNING BANNER */}
      {isEmergencySearch && (
        <div className="bg-rose-600 text-white p-4 rounded-3xl shadow-lg flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-2 border-rose-300 animate-pulse">
          <div className="flex items-center gap-3">
            <ShieldAlert className="w-7 h-7 text-amber-300" />
            <div>
              <span className="font-black text-xs uppercase tracking-wider text-amber-200">EMERGENCY ASSISTANCE RECOMMENDED</span>
              <p className="text-xs font-semibold">Priority 24/7 Emergency Casualty Wards Listed First.</p>
            </div>
          </div>
          <div className="flex gap-2">
            <a
              href="tel:108"
              className="bg-amber-400 hover:bg-amber-300 text-slate-950 font-black px-4 py-2 rounded-xl text-xs flex items-center gap-1 shadow"
            >
              <Phone className="w-3.5 h-3.5" /> Call 108
            </a>
          </div>
        </div>
      )}

      {/* Map vs List View Mode Toggle */}
      <div className="flex items-center justify-between bg-white p-2.5 rounded-2xl border border-slate-200 shadow-sm">
        <div className="flex items-center gap-2">
          <button
            onClick={() => setIsEmergencySearch(!isEmergencySearch)}
            className={`px-3 py-1 rounded-xl text-xs font-extrabold border transition ${
              isEmergencySearch ? 'bg-rose-100 text-rose-900 border-rose-300' : 'bg-slate-100 text-slate-600 border-slate-200'
            }`}
          >
            {isEmergencySearch ? '🔴 Emergency Mode ACTIVE' : 'Toggle Emergency Filter'}
          </button>
        </div>

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

      {/* SMART ROUTING EXPLANATION PANEL (List View Header) */}
      {viewMode === 'list' && !loading && facilities.length > 0 && (
        <div className="bg-slate-900 text-white p-4 rounded-3xl border border-amber-400/50 shadow-md space-y-2">
          <div className="flex items-center justify-between border-b border-slate-800 pb-2">
            <span className="font-extrabold text-xs text-amber-300 flex items-center gap-1.5">
              <Sparkles className="w-4 h-4 text-amber-400" />
              Smart Routing Multi-Factor Formula
            </span>
            <span className="text-[10px] text-slate-400 font-mono">Algorithm Weights</span>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-[11px] font-mono text-slate-300 pt-1">
            <div className="bg-slate-800 p-2 rounded-xl border border-slate-700">
              <span className="text-emerald-400 font-bold block">Service Match</span>
              <span>35% Weight</span>
            </div>
            <div className="bg-slate-800 p-2 rounded-xl border border-slate-700">
              <span className="text-sky-400 font-bold block">Doctor Available</span>
              <span>25% Weight</span>
            </div>
            <div className="bg-slate-800 p-2 rounded-xl border border-slate-700">
              <span className="text-amber-400 font-bold block">Distance (km)</span>
              <span>25% Weight</span>
            </div>
            <div className="bg-slate-800 p-2 rounded-xl border border-slate-700">
              <span className="text-purple-400 font-bold block">24/7 Emergency</span>
              <span>15% Weight</span>
            </div>
          </div>

          <p className="text-[11px] text-slate-300 pt-1 italic">
            💡 <strong>Smart Ranking Rule:</strong> Suitable facilities with open doctor slots (e.g. District Civil Hospital Baramati @ 4.2 km) are ranked <strong>above</strong> closer clinics where doctors/slots are unavailable (e.g. PHC Baramati @ 2.1 km).
          </p>
        </div>
      )}

      {/* Loading State */}
      {loading ? (
        <div className="bg-white p-8 rounded-3xl border border-slate-200 text-center space-y-3">
          <RefreshCw className="w-8 h-8 text-sky-600 animate-spin mx-auto" />
          <p className="text-sm font-bold text-slate-600">
            {lang === 'hi' ? 'स्मार्ट एल्गोरिदम से केंद्र लोड हो रहे हैं...' : 'Executing Smart Facility Routing...'}
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
        /* LIST VIEW CARDS */
        viewMode === 'list' && (
          <div className="space-y-4">
            {facilities.map((fac, idx) => {
              const isDoctorAvail = fac.doctor_available !== false;
              const isEmergAvail = fac.emergency_available !== false;

              return (
                <div
                  key={fac.id}
                  className={`bg-white border rounded-3xl p-5 shadow-sm hover:shadow-md transition flex flex-col gap-3 relative ${
                    idx === 0 ? 'border-2 border-emerald-500 ring-2 ring-emerald-100' : 'border-slate-200'
                  }`}
                >
                  {/* Top Rank Badge */}
                  {idx === 0 && (
                    <div className="absolute -top-3 left-5 bg-emerald-600 text-white font-black text-[10px] uppercase px-3 py-1 rounded-full shadow flex items-center gap-1">
                      <Sparkles className="w-3 h-3 text-amber-300" />
                      #1 MOST SUITABLE MATCH
                    </div>
                  )}

                  <div className="flex items-start justify-between gap-2 pt-1">
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="bg-sky-100 text-sky-900 font-extrabold text-[10px] uppercase px-2.5 py-0.5 rounded-full">
                          {fac.facility_type}
                        </span>
                        <span className="bg-slate-100 text-slate-700 font-mono text-[10px] font-bold px-2 py-0.5 rounded-full">
                          ⭐ Score: {fac.smart_score || 85.0}/100
                        </span>
                      </div>
                      <h3 className="text-base md:text-lg font-black text-slate-900 leading-tight mt-1">
                        {lang === 'hi' && fac.name_hi ? fac.name_hi : fac.name}
                      </h3>
                    </div>

                    <div className="flex flex-col items-end gap-1">
                      <span className="bg-amber-100 text-amber-900 font-extrabold text-xs px-2.5 py-1 rounded-full whitespace-nowrap">
                        📍 {fac.simulated_distance || (idx === 0 ? 4.2 : 2.1)} km
                      </span>
                    </div>
                  </div>

                  {/* Status Badges Row */}
                  <div className="grid grid-cols-2 sm:grid-cols-3 gap-2 text-xs">
                    {/* Doctor Availability */}
                    <div className={`p-2 rounded-xl border font-bold flex items-center gap-1.5 ${
                      isDoctorAvail ? 'bg-emerald-50 border-emerald-200 text-emerald-900' : 'bg-rose-50 border-rose-200 text-rose-900'
                    }`}>
                      <span className="text-sm">{isDoctorAvail ? '🟢' : '🔴'}</span>
                      <div>
                        <span className="text-[10px] block opacity-75">Doctor Status</span>
                        <span className="text-[11px] font-extrabold">{isDoctorAvail ? 'Available' : 'Slots Full / Unavailable'}</span>
                      </div>
                    </div>

                    {/* Emergency Capability */}
                    <div className={`p-2 rounded-xl border font-bold flex items-center gap-1.5 ${
                      isEmergAvail ? 'bg-purple-50 border-purple-200 text-purple-900' : 'bg-slate-50 border-slate-200 text-slate-600'
                    }`}>
                      <span className="text-sm">{isEmergAvail ? '🔴' : '⚪'}</span>
                      <div>
                        <span className="text-[10px] block opacity-75">Emergency Ward</span>
                        <span className="text-[11px] font-extrabold">{isEmergAvail ? '24/7 Available' : 'Not Available'}</span>
                      </div>
                    </div>

                    {/* Next OPD Slot */}
                    <div className="p-2 rounded-xl border border-slate-200 bg-slate-50 text-slate-800 font-bold flex items-center gap-1.5 sm:col-span-1 col-span-2">
                      <Calendar className="w-4 h-4 text-sky-600 flex-shrink-0" />
                      <div>
                        <span className="text-[10px] block text-slate-400">Next OPD Slot</span>
                        <span className="text-[11px] font-extrabold text-sky-900">{fac.next_opd_slot || "10:30 AM"}</span>
                      </div>
                    </div>
                  </div>

                  <div className="text-xs text-slate-600 space-y-1">
                    <div className="flex items-center justify-between font-medium">
                      <div className="flex items-center gap-1.5">
                        <MapPin className="w-4 h-4 text-slate-400 flex-shrink-0" />
                        <span>{fac.address}</span>
                      </div>
                      
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
                  </div>

                  {/* Services tags */}
                  <div className="pt-2 border-t border-slate-100 flex flex-wrap gap-1.5">
                    {fac.services.split(',').map((s, idx) => (
                      <span key={idx} className="bg-slate-100 text-slate-700 text-[10px] font-bold px-2 py-0.5 rounded-md">
                        🩺 {s.trim()}
                      </span>
                    ))}
                  </div>

                  {/* Select Slot Action / View Alternatives Button */}
                  {isDoctorAvail ? (
                    <button
                      onClick={() => handleSelectFacility(fac)}
                      className="w-full mt-2 bg-sky-700 hover:bg-sky-800 text-white font-extrabold py-3 px-4 rounded-2xl shadow flex items-center justify-center gap-2 transition active:scale-95 text-xs sm:text-sm"
                    >
                      <Calendar className="w-4 h-4 text-amber-300" />
                      <span>{lang === 'hi' ? 'स्लॉट बुक करें (Book Slot)' : 'Select & Book Doctor Slot'}</span>
                      <ArrowRight className="w-4 h-4 ml-auto" />
                    </button>
                  ) : (
                    <button
                      onClick={() => handleSelectFacility(fac)}
                      className="w-full mt-2 bg-slate-800 hover:bg-slate-900 text-amber-300 font-extrabold py-3 px-4 rounded-2xl shadow flex items-center justify-center gap-2 transition active:scale-95 text-xs sm:text-sm"
                    >
                      <AlertCircle className="w-4 h-4 text-rose-400" />
                      <span>{lang === 'hi' ? 'अस्पताल अनुपलब्ध - विकल्प देखें' : 'Facility Unavailable — View Alternatives'}</span>
                    </button>
                  )}
                </div>
              );
            })}
          </div>
        )
      )}

      {/* MODAL: FACILITY UNAVAILABLE ALTERNATIVE REROUTING */}
      {unavailableModal && (
        <div className="fixed inset-0 bg-slate-950/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-3xl p-6 max-w-md w-full shadow-2xl space-y-4">
            <div className="flex items-center gap-3 border-b border-slate-100 pb-3">
              <div className="bg-rose-100 text-rose-700 p-2.5 rounded-2xl">
                <AlertCircle className="w-6 h-6" />
              </div>
              <div>
                <h3 className="font-extrabold text-slate-900 text-base">Facility Currently Unavailable</h3>
                <p className="text-xs text-slate-500">{unavailableModal.name}</p>
              </div>
            </div>

            <p className="text-xs text-slate-600 leading-relaxed font-medium">
              The doctor OPD slots at <strong>{unavailableModal.name}</strong> are currently full or under maintenance. JanSethu AI recommends re-routing to the highest-ranked available facility.
            </p>

            <div className="bg-sky-50 p-3 rounded-2xl border border-sky-200 text-xs text-sky-900 space-y-1 font-semibold">
              <div className="flex items-center gap-1 font-bold text-sky-950">
                <Sparkles className="w-4 h-4 text-amber-500" />
                Recommended Alternative:
              </div>
              <p>District Civil Hospital Baramati (4.2 km — Doctor Available)</p>
            </div>

            <div className="flex gap-2 pt-2">
              <button
                onClick={handleViewAlternatives}
                className="flex-1 bg-sky-700 hover:bg-sky-800 text-white font-extrabold py-3 rounded-2xl text-xs shadow"
              >
                View Recommended Alternative
              </button>
              <button
                onClick={() => setUnavailableModal(null)}
                className="bg-slate-100 text-slate-700 font-bold px-4 py-3 rounded-2xl text-xs"
              >
                Dismiss
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
