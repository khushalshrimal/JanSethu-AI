import React, { useState, useEffect } from 'react';
import { useSearchParams, Link } from 'react-router-dom';
import { getFacilities, searchNearbyFacilities } from '../services/facilityService';
import { Building2, MapPin, Search, Phone, ShieldAlert, ArrowRight, RefreshCw, Compass } from 'lucide-react';

export default function Facilities() {
  const [searchParams, setSearchParams] = useSearchParams();
  const query = searchParams.get('q') || '';
  const latParam = searchParams.get('lat');
  const lngParam = searchParams.get('lng');
  const isNearby = searchParams.get('nearby') === 'true';

  const [facilities, setFacilities] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const [searchInput, setSearchInput] = useState(query);
  const [radiusKm, setRadiusKm] = useState(10);
  const [useGpsMode, setUseGpsMode] = useState(isNearby);
  const [userCoords, setUserCoords] = useState(
    latParam && lngParam ? { lat: parseFloat(latParam), lng: parseFloat(lngParam) } : null
  );

  const fetchFacilitiesData = async () => {
    setLoading(true);
    setError(null);
    try {
      if (useGpsMode && userCoords) {
        const data = await searchNearbyFacilities(userCoords.lat, userCoords.lng, radiusKm);
        setFacilities(data);
      } else if (searchInput.trim()) {
        const q = searchInput.trim();
        // check if pincode numeric or district
        const isNumeric = /^\d+$/.test(q);
        const params = isNumeric ? { pincode: q } : { search: q };
        const data = await getFacilities(params);
        setFacilities(data);
      } else {
        const data = await getFacilities({});
        setFacilities(data);
      }
    } catch (err) {
      setError(err.message || err.response?.data?.detail || 'Failed to load healthcare facilities.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (latParam && lngParam) {
      setUserCoords({ lat: parseFloat(latParam), lng: parseFloat(lngParam) });
      setUseGpsMode(true);
    }
    fetchFacilitiesData();
  }, [searchParams, radiusKm, useGpsMode]);

  const handleSearchSubmit = (e) => {
    e.preventDefault();
    setUseGpsMode(false);
    if (searchInput.trim()) {
      setSearchParams({ q: searchInput.trim() });
    } else {
      setSearchParams({});
    }
  };

  const handleActivateGps = () => {
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        (pos) => {
          const coords = { lat: pos.coords.latitude, lng: pos.coords.longitude };
          setUserCoords(coords);
          setUseGpsMode(true);
          setSearchParams({ lat: coords.lat, lng: coords.lng, nearby: 'true' });
        },
        () => {
          // Fallback location Pune (18.5204, 73.8567)
          const coords = { lat: 18.5204, lng: 73.8567 };
          setUserCoords(coords);
          setUseGpsMode(true);
          setSearchParams({ lat: coords.lat, lng: coords.lng, nearby: 'true' });
        }
      );
    } else {
      const coords = { lat: 18.5204, lng: 73.8567 };
      setUserCoords(coords);
      setUseGpsMode(true);
      setSearchParams({ lat: coords.lat, lng: coords.lng, nearby: 'true' });
    }
  };

  return (
    <div className="space-y-6 py-2">
      {/* Header & Controls */}
      <div className="bg-white p-6 rounded-3xl border border-slate-200 shadow-sm space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-100 pb-4">
          <div>
            <h1 className="text-2xl font-black text-slate-900 flex items-center gap-2">
              <Building2 className="w-6 h-6 text-sky-700" />
              Healthcare Facilities
            </h1>
            <p className="text-xs text-slate-500 font-medium">
              Discover verified PHC, CHC, & District Hospitals connected to JanSethu
            </p>
          </div>

          <button
            onClick={handleActivateGps}
            className={`px-4 py-2 rounded-xl text-xs font-bold transition flex items-center gap-1.5 ${
              useGpsMode
                ? 'bg-emerald-600 text-white shadow-sm'
                : 'bg-emerald-50 hover:bg-emerald-100 text-emerald-800 border border-emerald-200'
            }`}
          >
            <Compass className="w-4 h-4" />
            <span>{useGpsMode ? 'GPS Location Active' : 'Find Facilities Near Me (GPS)'}</span>
          </button>
        </div>

        {/* Filter Controls Bar */}
        <div className="flex flex-col md:flex-row gap-3">
          <form onSubmit={handleSearchSubmit} className="flex-1 flex gap-2">
            <div className="relative flex-1">
              <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-3" />
              <input
                type="text"
                value={searchInput}
                onChange={(e) => setSearchInput(e.target.value)}
                placeholder="Search by pincode, district (e.g. Pune), or village..."
                className="w-full pl-10 pr-4 py-2.5 bg-slate-50 border border-slate-300 rounded-xl text-xs font-semibold outline-none focus:ring-2 focus:ring-sky-500"
              />
            </div>
            <button
              type="submit"
              className="px-4 py-2.5 bg-sky-700 hover:bg-sky-800 text-white rounded-xl text-xs font-bold transition"
            >
              Search
            </button>
          </form>

          {useGpsMode && (
            <div className="flex items-center gap-2 bg-emerald-50 px-3 py-1.5 rounded-xl border border-emerald-200 text-xs text-emerald-950 font-semibold">
              <span>Radius:</span>
              <select
                value={radiusKm}
                onChange={(e) => setRadiusKm(Number(e.target.value))}
                className="bg-white border border-emerald-300 rounded-lg px-2 py-1 text-xs font-bold"
              >
                <option value={5}>5 km</option>
                <option value={10}>10 km</option>
                <option value={20}>20 km</option>
                <option value={50}>50 km</option>
              </select>
            </div>
          )}
        </div>
      </div>

      {/* Facilities List Grid */}
      {loading ? (
        <div className="bg-white p-12 rounded-3xl border border-slate-200 text-center space-y-3">
          <RefreshCw className="w-8 h-8 text-sky-600 animate-spin mx-auto" />
          <p className="text-xs font-bold text-slate-600">Querying Real Database Facilities...</p>
        </div>
      ) : error ? (
        <div className="bg-rose-50 border border-rose-200 p-6 rounded-3xl text-rose-900 text-xs font-bold">
          {error}
        </div>
      ) : facilities.length === 0 ? (
        <div className="bg-amber-50 border border-amber-200 p-8 rounded-3xl text-center space-y-2">
          <p className="font-extrabold text-slate-800 text-sm">No Healthcare Facilities Found</p>
          <p className="text-xs text-slate-600 font-medium">
            Try searching for another pincode (e.g. <strong>411001</strong>) or district (e.g. <strong>Pune</strong>).
          </p>
          <button
            onClick={() => {
              setSearchInput('');
              setUseGpsMode(false);
              setSearchParams({});
            }}
            className="mt-2 px-4 py-2 bg-slate-900 text-white rounded-xl text-xs font-bold"
          >
            Clear Filters & View All
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {facilities.map((fac) => (
            <div
              key={fac.id}
              className="bg-white p-5 rounded-3xl border border-slate-200 shadow-sm hover:shadow-md transition space-y-4 flex flex-col justify-between"
            >
              <div className="space-y-2">
                <div className="flex items-start justify-between gap-2">
                  <span className="bg-sky-100 text-sky-800 text-[10px] font-black px-2.5 py-0.5 rounded-full uppercase tracking-wide">
                    {fac.category || 'Healthcare Center'}
                  </span>
                  {fac.has_emergency_24x7 && (
                    <span className="bg-rose-100 text-rose-800 text-[10px] font-black px-2.5 py-0.5 rounded-full uppercase flex items-center gap-1">
                      <ShieldAlert className="w-3 h-3 text-rose-600" />
                      24x7 Emergency
                    </span>
                  )}
                  {fac.distance_km !== undefined && fac.distance_km !== null && (
                    <span className="bg-emerald-100 text-emerald-800 text-[10px] font-black px-2 py-0.5 rounded-full">
                      {fac.distance_km.toFixed(1)} km away
                    </span>
                  )}
                </div>

                <h3 className="font-black text-slate-900 text-lg leading-tight">{fac.name}</h3>

                <p className="text-xs text-slate-500 font-medium flex items-start gap-1.5">
                  <MapPin className="w-4 h-4 text-sky-600 flex-shrink-0 mt-0.5" />
                  <span>
                    {fac.address}, {fac.village ? `${fac.village}, ` : ''}{fac.district} - {fac.pincode}
                  </span>
                </p>

                {fac.phone && (
                  <p className="text-xs text-slate-600 font-semibold flex items-center gap-1.5">
                    <Phone className="w-3.5 h-3.5 text-slate-400" />
                    <span>Contact: {fac.phone}</span>
                  </p>
                )}
              </div>

              <div className="pt-3 border-t border-slate-100 flex items-center justify-between">
                <span className="text-[11px] text-slate-400 font-mono">ID: #{fac.id}</span>
                <Link
                  to={`/facilities/${fac.id}`}
                  className="px-4 py-2 bg-sky-700 hover:bg-sky-800 text-white rounded-xl text-xs font-bold transition flex items-center gap-1.5 shadow-sm"
                >
                  <span>View Doctors & OPD</span>
                  <ArrowRight className="w-3.5 h-3.5" />
                </Link>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
