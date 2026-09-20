import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { Search, MapPin, PhoneCall, Calendar, Building2, Shield, Activity, ArrowRight, Smartphone, Phone } from 'lucide-react';

export default function Home() {
  const navigate = useNavigate();
  const [searchQuery, setSearchQuery] = useState('');

  const handleSearchSubmit = (e) => {
    e.preventDefault();
    if (searchQuery.trim()) {
      navigate(`/facilities?q=${encodeURIComponent(searchQuery.trim())}`);
    } else {
      navigate('/facilities');
    }
  };

  const handleNearbyClick = () => {
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        (pos) => {
          const { latitude, longitude } = pos.coords;
          navigate(`/facilities?lat=${latitude}&lng=${longitude}&nearby=true`);
        },
        (err) => {
          // Fallback to default GPS coordinates if permission denied or unavailable
          navigate('/facilities?lat=18.5204&lng=73.8567&nearby=true');
        }
      );
    } else {
      navigate('/facilities?lat=18.5204&lng=73.8567&nearby=true');
    }
  };

  return (
    <div className="space-y-8 py-2">
      {/* Hero Section */}
      <div className="relative overflow-hidden bg-gradient-to-br from-sky-900 via-sky-800 to-slate-900 text-white rounded-3xl p-6 sm:p-10 shadow-xl border border-sky-700/50">
        <div className="relative z-10 max-w-2xl space-y-4">
          <div className="inline-flex items-center gap-2 px-3 py-1 bg-amber-400/20 text-amber-300 border border-amber-400/30 rounded-full text-xs font-bold">
            <Activity className="w-3.5 h-3.5 text-amber-400" />
            <span>JanSethu AI 2.0 — Dual Channel Access Engine</span>
          </div>

          <h1 className="text-3xl sm:text-4xl font-black tracking-tight leading-tight">
            Healthcare Access for Every Indian Citizen
          </h1>

          <p className="text-xs sm:text-sm text-sky-100 font-medium leading-relaxed">
            Find nearby government & rural healthcare centers (PHC/CHC/District Hospitals), discover OPD doctors, check real dynamic time slots, and book appointment confirmations in seconds.
          </p>

          {/* Search Box */}
          <form onSubmit={handleSearchSubmit} className="pt-2 flex flex-col sm:flex-row gap-2">
            <div className="relative flex-1">
              <Search className="w-4 h-4 text-slate-400 absolute left-4 top-3.5" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Enter Pincode (e.g., 411001), District, or Village name..."
                className="w-full pl-11 pr-4 py-3 bg-white text-slate-900 rounded-2xl text-xs font-semibold outline-none shadow-md focus:ring-2 focus:ring-amber-400 placeholder:text-slate-400"
              />
            </div>
            <button
              type="submit"
              className="px-6 py-3 bg-amber-400 hover:bg-amber-300 text-slate-950 font-black text-xs rounded-2xl transition shadow-md flex items-center justify-center gap-2"
            >
              <span>Search Facilities</span>
              <ArrowRight className="w-4 h-4" />
            </button>
          </form>

          {/* Location GPS Quick Button */}
          <div className="flex flex-wrap items-center gap-3 pt-1 text-xs">
            <button
              onClick={handleNearbyClick}
              type="button"
              className="px-3.5 py-2 bg-sky-900/90 hover:bg-sky-700 text-sky-100 rounded-xl border border-sky-600/50 font-bold transition flex items-center gap-1.5"
            >
              <MapPin className="w-3.5 h-3.5 text-emerald-400" />
              <span>Use My GPS Location</span>
            </button>
            <span className="text-sky-300 text-[11px] font-medium">
              Popular Pincodes: <button onClick={() => navigate('/facilities?q=411001')} className="underline font-semibold hover:text-white">411001 (Pune)</button>, <button onClick={() => navigate('/facilities?q=411002')} className="underline font-semibold hover:text-white">411002</button>
            </span>
          </div>
        </div>
      </div>

      {/* Quick Action Cards Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <Link
          to="/facilities"
          className="bg-white p-5 rounded-3xl border border-slate-200 shadow-sm hover:shadow-md hover:border-sky-300 transition group space-y-3"
        >
          <div className="p-3 bg-sky-100 text-sky-800 rounded-2xl w-fit group-hover:bg-sky-600 group-hover:text-white transition">
            <Building2 className="w-6 h-6" />
          </div>
          <div>
            <h3 className="font-extrabold text-slate-900 text-base">Healthcare Facilities</h3>
            <p className="text-xs text-slate-500 mt-1">Search PHC, CHC, & District Hospitals by district/pincode.</p>
          </div>
          <div className="text-xs font-bold text-sky-700 flex items-center gap-1 group-hover:translate-x-1 transition">
            Explore Facilities →
          </div>
        </Link>

        <Link
          to="/facilities"
          className="bg-white p-5 rounded-3xl border border-slate-200 shadow-sm hover:shadow-md hover:border-emerald-300 transition group space-y-3"
        >
          <div className="p-3 bg-emerald-100 text-emerald-800 rounded-2xl w-fit group-hover:bg-emerald-600 group-hover:text-white transition">
            <Calendar className="w-6 h-6" />
          </div>
          <div>
            <h3 className="font-extrabold text-slate-900 text-base">Book Doctor OPD Slot</h3>
            <p className="text-xs text-slate-500 mt-1">Check dynamic 15-minute OPD availability and reserve slot.</p>
          </div>
          <div className="text-xs font-bold text-emerald-700 flex items-center gap-1 group-hover:translate-x-1 transition">
            Book Appointment →
          </div>
        </Link>

        <Link
          to="/my-appointments"
          className="bg-white p-5 rounded-3xl border border-slate-200 shadow-sm hover:shadow-md hover:border-amber-300 transition group space-y-3"
        >
          <div className="p-3 bg-amber-100 text-amber-900 rounded-2xl w-fit group-hover:bg-amber-500 group-hover:text-white transition">
            <Shield className="w-6 h-6" />
          </div>
          <div>
            <h3 className="font-extrabold text-slate-900 text-base">My Appointments</h3>
            <p className="text-xs text-slate-500 mt-1">View backend confirmation codes, cancel or reschedule slots.</p>
          </div>
          <div className="text-xs font-bold text-amber-700 flex items-center gap-1 group-hover:translate-x-1 transition">
            Manage Bookings →
          </div>
        </Link>

        <a
          href="tel:108"
          className="bg-rose-50 p-5 rounded-3xl border-2 border-rose-200 shadow-sm hover:shadow-md hover:border-rose-400 transition group space-y-3"
        >
          <div className="p-3 bg-rose-600 text-white rounded-2xl w-fit">
            <PhoneCall className="w-6 h-6 animate-pulse" />
          </div>
          <div>
            <h3 className="font-extrabold text-rose-950 text-base">Emergency 108 Hotline</h3>
            <p className="text-xs text-rose-700 mt-1">Immediate dispatch for critical & trauma emergency cases.</p>
          </div>
          <div className="text-xs font-bold text-rose-800 flex items-center gap-1">
            Call 108 Emergency Now →
          </div>
        </a>
      </div>

      {/* Dual Channel Architecture Vision Card */}
      <div className="bg-slate-900 text-white p-6 sm:p-8 rounded-3xl border border-slate-800 shadow-lg space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800 pb-4">
          <div>
            <span className="text-[10px] font-black tracking-widest text-amber-400 uppercase">
              Architectural Standard
            </span>
            <h2 className="text-xl font-black text-white mt-0.5">
              Single Backend Model for Keypad Phones & Smartphones
            </h2>
          </div>
          <span className="px-3 py-1 bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 rounded-full text-xs font-bold w-fit">
            100% Real Database Source of Truth
          </span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 text-xs">
          <div className="bg-slate-800/80 p-5 rounded-2xl border border-slate-700/60 space-y-3">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-amber-400 text-slate-950 rounded-xl font-bold">
                <Phone className="w-5 h-5" />
              </div>
              <div>
                <h3 className="font-extrabold text-sm text-amber-300">Channel 1: Keypad Phone (Voice IVR + DTMF)</h3>
                <p className="text-[11px] text-slate-400">Primary Channel — Zero Internet Required</p>
              </div>
            </div>
            <p className="text-slate-300 font-medium leading-relaxed">
              Villagers call a local phone number on any basic keypad phone. AI voice agent speaks in native languages (Hindi, Marathi, English) and uses the exact same database API rules to check doctor availability and book appointments via SMS confirmation.
            </p>
          </div>

          <div className="bg-slate-800/80 p-5 rounded-2xl border border-slate-700/60 space-y-3">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-sky-500 text-white rounded-xl font-bold">
                <Smartphone className="w-5 h-5" />
              </div>
              <div>
                <h3 className="font-extrabold text-sm text-sky-300">Channel 2: Smartphone PWA (Web & Mobile App)</h3>
                <p className="text-[11px] text-slate-400">Secondary Channel — Rich Interactive Interface</p>
              </div>
            </div>
            <p className="text-slate-300 font-medium leading-relaxed">
              Smartphones access this web PWA. PWA users query the same dynamic slot calculation engine (`check_slot_availability`), reserve slots, track confirmation codes (`JS-2026-XXXXXX`), and receive SMS dispatch notifications.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
