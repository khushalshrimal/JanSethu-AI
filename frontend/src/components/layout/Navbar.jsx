import React from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { Activity, Shield, PhoneCall, User, LogOut, Calendar, Building2, Home } from 'lucide-react';

export default function Navbar() {
  const { user, isAuthenticated, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const isActive = (path) => location.pathname === path;

  return (
    <header className="bg-sky-800 text-white shadow-md sticky top-0 z-50">
      <div className="max-w-6xl mx-auto px-4 py-3 flex items-center justify-between">
        {/* Brand Logo */}
        <Link to="/" className="flex items-center gap-2.5 group">
          <div className="bg-white/15 p-2 rounded-xl group-hover:bg-white/25 transition">
            <Activity className="w-6 h-6 text-amber-300" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="text-xl font-black tracking-tight leading-none">JanSethu AI</span>
              <span className="bg-amber-400 text-slate-950 text-[10px] font-black px-1.5 py-0.5 rounded uppercase">
                2.0 MVP
              </span>
            </div>
            <p className="text-[10px] text-sky-200 font-medium">Healthcare Access Platform</p>
          </div>
        </Link>

        {/* Navigation Links */}
        <nav className="hidden md:flex items-center gap-1 bg-sky-900/60 p-1 rounded-2xl border border-sky-700/50 text-xs font-semibold">
          <Link
            to="/"
            className={`px-3 py-1.5 rounded-xl flex items-center gap-1.5 transition ${
              isActive('/') ? 'bg-white text-sky-900 font-bold shadow-sm' : 'hover:bg-sky-800 text-sky-100'
            }`}
          >
            <Home className="w-3.5 h-3.5" />
            Home
          </Link>
          <Link
            to="/facilities"
            className={`px-3 py-1.5 rounded-xl flex items-center gap-1.5 transition ${
              isActive('/facilities') ? 'bg-white text-sky-900 font-bold shadow-sm' : 'hover:bg-sky-800 text-sky-100'
            }`}
          >
            <Building2 className="w-3.5 h-3.5" />
            Find Healthcare
          </Link>
          <Link
            to="/my-appointments"
            className={`px-3 py-1.5 rounded-xl flex items-center gap-1.5 transition ${
              isActive('/my-appointments') ? 'bg-white text-sky-900 font-bold shadow-sm' : 'hover:bg-sky-800 text-sky-100'
            }`}
          >
            <Calendar className="w-3.5 h-3.5" />
            My Appointments
          </Link>
          <Link
            to="/phone-simulator"
            className={`px-3 py-1.5 rounded-xl flex items-center gap-1.5 transition ${
              isActive('/phone-simulator') ? 'bg-amber-400 text-slate-950 font-bold shadow-sm' : 'hover:bg-sky-800 text-amber-300'
            }`}
          >
            <PhoneCall className="w-3.5 h-3.5" />
            Phone IVR Demo
          </Link>
          {(user?.role === 'PROVIDER' || user?.role === 'ADMIN') && (
            <Link
              to="/provider"
              className={`px-3 py-1.5 rounded-xl flex items-center gap-1.5 transition ${
                isActive('/provider') ? 'bg-emerald-400 text-slate-950 font-bold shadow-sm' : 'hover:bg-sky-800 text-emerald-200'
              }`}
            >
              <Activity className="w-3.5 h-3.5" />
              Provider OPD
            </Link>
          )}
          {user?.role === 'ADMIN' && (
            <Link
              to="/admin"
              className={`px-3 py-1.5 rounded-xl flex items-center gap-1.5 transition ${
                isActive('/admin') ? 'bg-purple-400 text-slate-950 font-bold shadow-sm' : 'hover:bg-sky-800 text-purple-200'
              }`}
            >
              <Shield className="w-3.5 h-3.5" />
              Admin Console
            </Link>
          )}
        </nav>

        {/* User Auth Controls */}
        <div className="flex items-center gap-2.5 text-xs font-semibold">
          {isAuthenticated ? (
            <div className="flex items-center gap-2 bg-sky-900/80 px-3 py-1.5 rounded-2xl border border-sky-700">
              <div className="flex items-center gap-1.5">
                <div className="w-6 h-6 rounded-full bg-amber-400 text-slate-950 flex items-center justify-center font-bold text-xs">
                  {user?.full_name ? user.full_name[0].toUpperCase() : 'U'}
                </div>
                <div className="hidden sm:block text-left">
                  <p className="text-[11px] font-bold leading-tight text-white">{user?.full_name}</p>
                  <p className="text-[9px] text-sky-300 capitalize leading-tight">{user?.role}</p>
                </div>
              </div>
              <button
                onClick={handleLogout}
                title="Logout"
                className="ml-1 text-sky-300 hover:text-white p-1 rounded-lg transition"
              >
                <LogOut className="w-4 h-4" />
              </button>
            </div>
          ) : (
            <div className="flex items-center gap-2">
              <Link
                to="/phone-simulator"
                className="px-3.5 py-1.5 bg-amber-400 hover:bg-amber-300 text-slate-950 rounded-xl font-black transition shadow-sm flex items-center gap-1.5"
              >
                <PhoneCall className="w-3.5 h-3.5 text-slate-950" />
                <span>Voice Call Assistant</span>
              </Link>
            </div>
          )}

          {/* Emergency 108 Call Quick Link */}
          <a
            href="tel:108"
            className="hidden lg:flex items-center gap-1 bg-rose-600 hover:bg-rose-500 px-3 py-1.5 rounded-xl text-white font-black text-xs transition"
          >
            <PhoneCall className="w-3.5 h-3.5 animate-pulse" />
            108 Emergency
          </a>
        </div>
      </div>

      {/* Mobile Bottom Navigation Bar */}
      <div className="md:hidden flex items-center justify-around bg-sky-900 border-t border-sky-700 py-2 text-[11px] font-semibold">
        <Link
          to="/"
          className={`flex flex-col items-center gap-0.5 ${isActive('/') ? 'text-amber-300 font-bold' : 'text-sky-200'}`}
        >
          <Home className="w-4 h-4" />
          <span>Home</span>
        </Link>
        <Link
          to="/facilities"
          className={`flex flex-col items-center gap-0.5 ${isActive('/facilities') ? 'text-amber-300 font-bold' : 'text-sky-200'}`}
        >
          <Building2 className="w-4 h-4" />
          <span>Facilities</span>
        </Link>
        <Link
          to="/my-appointments"
          className={`flex flex-col items-center gap-0.5 ${isActive('/my-appointments') ? 'text-amber-300 font-bold' : 'text-sky-200'}`}
        >
          <Calendar className="w-4 h-4" />
          <span>Appointments</span>
        </Link>
      </div>
    </header>
  );
}
