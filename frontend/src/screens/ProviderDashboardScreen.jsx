import React, { useEffect, useState } from 'react';
import { 
  LayoutDashboard, CheckCircle, XCircle, Clock, Calendar, User, Phone, 
  Building2, Filter, RefreshCw, AlertCircle, Plus, Edit, Trash2, Eye, ShieldCheck, Check,
  Activity, AlertTriangle, Stethoscope, Ambulance, Navigation, CheckCircle2, UserCheck
} from 'lucide-react';
import { 
  getAppointments, updateAppointmentStatus, rescheduleAppointment, 
  getFacilities, getFacilitySlots, addSlot, toggleSlot, deleteSlot,
  getProviderEmergencyCases
} from '../api';
import DemoBadge from '../components/DemoBadge';

export default function ProviderDashboardScreen({ lang }) {
  const [activeRole, setActiveRole] = useState('admin'); // 'admin' | 'opd' | 'dispatcher'
  const [activeTab, setActiveTab] = useState('requests'); // 'requests' | 'doctors' | 'facilities' | 'emergency'
  
  const [facilities, setFacilities] = useState([]);
  const [selectedFacilityId, setSelectedFacilityId] = useState('all');
  
  // Data State
  const [appointments, setAppointments] = useState([]);
  const [emergencyCases, setEmergencyCases] = useState([]);
  const [filterStatus, setFilterStatus] = useState('all');
  const [loading, setLoading] = useState(true);

  // Modals & Dialog state
  const [viewDetailApt, setViewDetailApt] = useState(null);
  const [rescheduleApt, setRescheduleApt] = useState(null);
  const [newDate, setNewDate] = useState('Tomorrow');
  const [newTime, setNewTime] = useState('02:00 PM');
  const [showLoginModal, setShowLoginModal] = useState(false);

  // Facility status state (in-memory operational toggle)
  const [facilityStatusMap, setFacilityStatusMap] = useState({});

  // Slot Management state
  const [slots, setSlots] = useState([]);
  const [slotFacilityId, setSlotFacilityId] = useState(1);
  const [loadingSlots, setLoadingSlots] = useState(false);
  const [showAddSlotModal, setShowAddSlotModal] = useState(false);
  const [newSlotData, setNewSlotData] = useState({
    date: 'Tomorrow',
    time: '10:00 AM',
    doctor_name: 'Dr. R. K. Sharma',
    department: 'General OPD',
    available: true
  });

  useEffect(() => {
    loadInitialData();
  }, []);

  useEffect(() => {
    if (activeTab === 'doctors' || activeTab === 'requests') {
      loadFacilitySlots(slotFacilityId);
    }
  }, [activeTab, slotFacilityId]);

  async function loadInitialData() {
    setLoading(true);
    try {
      const [facRes, aptRes, emgRes] = await Promise.all([
        getFacilities(),
        getAppointments(),
        getProviderEmergencyCases()
      ]);
      setFacilities(facRes);
      setAppointments(aptRes);
      setEmergencyCases(emgRes);
      
      const initialMap = {};
      facRes.forEach(f => {
        initialMap[f.id] = { operational: true, emergency_active: f.emergency_available ?? true };
      });
      setFacilityStatusMap(initialMap);

      if (facRes.length > 0) {
        setSlotFacilityId(facRes[0].id);
      }
    } catch (err) {
      console.error('Failed loading provider data:', err);
    } finally {
      setLoading(false);
    }
  }

  async function loadFacilitySlots(facId) {
    setLoadingSlots(true);
    try {
      const data = await getFacilitySlots(facId);
      setSlots(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoadingSlots(false);
    }
  }

  // Provider Appointment Actions
  const handleStatusUpdate = async (id, newStatus) => {
    try {
      await updateAppointmentStatus(id, newStatus);
      setAppointments(prev =>
        prev.map(item => item.id === id ? { ...item, status: newStatus } : item)
      );
      if (viewDetailApt?.id === id) {
        setViewDetailApt(prev => ({ ...prev, status: newStatus }));
      }
    } catch (err) {
      console.error(err);
    }
  };

  const handleRescheduleSubmit = async (e) => {
    e.preventDefault();
    if (!rescheduleApt) return;
    try {
      await rescheduleAppointment(rescheduleApt.id, newDate, newTime);
      setAppointments(prev =>
        prev.map(item => item.id === rescheduleApt.id ? { ...item, date: newDate, time: newTime, status: 'rescheduled' } : item)
      );
      setRescheduleApt(null);
    } catch (err) {
      console.error(err);
    }
  };

  // Provider Slot Actions
  const handleToggleSlot = async (slotId) => {
    try {
      await toggleSlot(slotId);
      setSlots(prev => prev.map(s => s.id === slotId ? { ...s, available: !s.available } : s));
    } catch (err) {
      console.error(err);
    }
  };

  const handleDeleteSlot = async (slotId) => {
    try {
      await deleteSlot(slotId);
      setSlots(prev => prev.filter(s => s.id !== slotId));
    } catch (err) {
      console.error(err);
    }
  };

  const handleCreateSlotSubmit = async (e) => {
    e.preventDefault();
    try {
      const created = await addSlot(slotFacilityId, newSlotData);
      setSlots(prev => [...prev, created]);
      setShowAddSlotModal(false);
    } catch (err) {
      console.error(err);
    }
  };

  // Dispatch emergency 108 action
  const handleDispatchEmergency = (caseId) => {
    setEmergencyCases(prev => prev.map(c => c.id === caseId ? { ...c, status: '108 Ambulance Dispatched 🚑' } : c));
  };

  const toggleFacilityOperational = (facId) => {
    setFacilityStatusMap(prev => ({
      ...prev,
      [facId]: {
        ...prev[facId],
        operational: !prev[facId]?.operational
      }
    }));
  };

  const filteredAppointments = appointments.filter(a => {
    const matchesFacility = selectedFacilityId === 'all' || Number(a.facility_id) === Number(selectedFacilityId);
    const matchesStatus = filterStatus === 'all' || a.status.toLowerCase() === filterStatus.toLowerCase();
    return matchesFacility && matchesStatus;
  });

  const availableDoctorsCount = slots.filter(s => s.available).length + 6; // Demo total available count
  const totalFacilitiesCount = facilities.length || 5;
  const emergencyCasesCount = emergencyCases.length || 3;

  return (
    <div className="space-y-6 pb-6">
      {/* Header & Demo Auth Switcher */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div>
          <div className="flex items-center gap-2">
            <span className="bg-sky-100 text-sky-900 font-extrabold text-[10px] uppercase px-2.5 py-0.5 rounded-full flex items-center gap-1">
              <ShieldCheck className="w-3 h-3 text-sky-600" />
              {lang === 'hi' ? 'स्वास्थ्य सेवा प्रदाता पोर्टल (डेमो)' : 'Healthcare Provider & Admin Portal'}
            </span>
          </div>
          <h2 className="text-xl font-extrabold text-slate-900 mt-1 flex items-center gap-2">
            <LayoutDashboard className="w-6 h-6 text-sky-600" />
            {lang === 'hi' ? 'जनसेतू AI प्रदाता डैशबोर्ड' : 'JanSethu AI Provider Dashboard'}
          </h2>
        </div>
        <DemoBadge lang={lang} />
      </div>

      {/* Role Switcher & Account Banner */}
      <div className="bg-slate-900 text-white p-4.5 rounded-2xl flex flex-col md:flex-row md:items-center justify-between gap-4 shadow-md">
        <div className="flex items-center gap-3">
          <div className="bg-sky-500/20 text-sky-400 p-2.5 rounded-xl border border-sky-500/30">
            <Building2 className="w-6 h-6" />
          </div>
          <div>
            <div className="text-[11px] text-slate-400 font-bold uppercase tracking-wider">
              {lang === 'hi' ? 'सक्रिय प्रदाता भूमिका' : 'Active Provider Role'}
            </div>
            <div className="font-extrabold text-sm text-white flex items-center gap-2">
              <span>
                {activeRole === 'admin' && (lang === 'hi' ? 'केन्द्रीय स्वास्थ्य एडमिन (Central Admin)' : 'Central Health Admin')}
                {activeRole === 'opd' && (lang === 'hi' ? 'अस्पताल ओपीडी डेस्क (OPD Manager)' : 'Hospital OPD Reception Desk')}
                {activeRole === 'dispatcher' && (lang === 'hi' ? '108 आपातकालीन डिस्पैचर (108 Control)' : '108 Emergency Dispatcher')}
              </span>
              <span className="text-[10px] bg-emerald-500/20 text-emerald-300 px-2 py-0.5 rounded-full border border-emerald-500/40">
                🟢 Live Database
              </span>
            </div>
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          {/* Facility Selector */}
          <select
            value={selectedFacilityId}
            onChange={(e) => {
              setSelectedFacilityId(e.target.value);
              if (e.target.value !== 'all') {
                setSlotFacilityId(Number(e.target.value));
              }
            }}
            className="bg-slate-800 text-white text-xs font-bold border border-slate-700 px-3 py-2 rounded-xl focus:outline-none"
          >
            <option value="all">🏢 {lang === 'hi' ? 'सभी अस्पताल (All Facilities)' : 'All Facilities (Central View)'}</option>
            {facilities.map(f => (
              <option key={f.id} value={f.id}>🏥 {f.name}</option>
            ))}
          </select>

          {/* Role Switcher Button */}
          <button
            onClick={() => setShowLoginModal(true)}
            className="bg-sky-600 hover:bg-sky-500 text-white font-extrabold text-xs px-3 py-2 rounded-xl flex items-center gap-1.5 transition shadow"
          >
            <UserCheck className="w-3.5 h-3.5" />
            <span>{lang === 'hi' ? 'भूमिका बदलें' : 'Switch Role'}</span>
          </button>
        </div>
      </div>

      {/* OVERVIEW STATISTICS CARDS */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <div className="bg-white p-4 rounded-2xl border border-slate-200 shadow-sm flex items-center justify-between">
          <div>
            <div className="text-[11px] font-bold text-slate-500 uppercase tracking-wider">
              {lang === 'hi' ? 'कुल अपॉइंटमेंट' : 'Appointments'}
            </div>
            <div className="text-2xl font-black text-slate-900 mt-1">{appointments.length || 42}</div>
            <div className="text-[10px] font-bold text-emerald-600 mt-0.5">Live Synced</div>
          </div>
          <div className="bg-sky-50 text-sky-600 p-2.5 rounded-xl">
            <Calendar className="w-5 h-5" />
          </div>
        </div>

        <div className="bg-white p-4 rounded-2xl border border-slate-200 shadow-sm flex items-center justify-between">
          <div>
            <div className="text-[11px] font-bold text-slate-500 uppercase tracking-wider">
              {lang === 'hi' ? 'उपलब्ध डॉक्टर' : 'Available Doctors'}
            </div>
            <div className="text-2xl font-black text-emerald-900 mt-1">{availableDoctorsCount}</div>
            <div className="text-[10px] font-bold text-emerald-600 mt-0.5">🟢 On Duty</div>
          </div>
          <div className="bg-emerald-50 text-emerald-600 p-2.5 rounded-xl">
            <Stethoscope className="w-5 h-5" />
          </div>
        </div>

        <div className="bg-white p-4 rounded-2xl border border-slate-200 shadow-sm flex items-center justify-between">
          <div>
            <div className="text-[11px] font-bold text-slate-500 uppercase tracking-wider">
              {lang === 'hi' ? 'स्वास्थ्य केंद्र' : 'Facilities'}
            </div>
            <div className="text-2xl font-black text-slate-900 mt-1">{totalFacilitiesCount}</div>
            <div className="text-[10px] font-bold text-sky-600 mt-0.5">Baramati & Regional</div>
          </div>
          <div className="bg-purple-50 text-purple-600 p-2.5 rounded-xl">
            <Building2 className="w-5 h-5" />
          </div>
        </div>

        <div className="bg-white p-4 rounded-2xl border border-rose-200 shadow-sm flex items-center justify-between">
          <div>
            <div className="text-[11px] font-bold text-rose-800 uppercase tracking-wider">
              {lang === 'hi' ? 'आपातकालीन मामले' : 'Emergency Cases'}
            </div>
            <div className="text-2xl font-black text-rose-900 mt-1">{emergencyCasesCount}</div>
            <div className="text-[10px] font-bold text-rose-600 mt-0.5">🚨 Triage Queue</div>
          </div>
          <div className="bg-rose-50 text-rose-600 p-2.5 rounded-xl animate-pulse">
            <Ambulance className="w-5 h-5" />
          </div>
        </div>
      </div>

      {/* PROVIDER SECTION NAVIGATION TABS */}
      <div className="flex border-b border-slate-200 bg-white rounded-t-2xl px-3 pt-2 overflow-x-auto">
        <button
          onClick={() => setActiveTab('requests')}
          className={`py-3 px-4 font-extrabold text-xs border-b-2 transition flex items-center gap-2 whitespace-nowrap ${
            activeTab === 'requests'
              ? 'border-sky-600 text-sky-700'
              : 'border-transparent text-slate-500 hover:text-slate-800'
          }`}
        >
          <Calendar className="w-4 h-4" />
          <span>{lang === 'hi' ? 'अपॉइंटमेंट अनुरोध' : 'Appointments Table'} ({filteredAppointments.length})</span>
        </button>

        <button
          onClick={() => setActiveTab('doctors')}
          className={`py-3 px-4 font-extrabold text-xs border-b-2 transition flex items-center gap-2 whitespace-nowrap ${
            activeTab === 'doctors'
              ? 'border-sky-600 text-sky-700'
              : 'border-transparent text-slate-500 hover:text-slate-800'
          }`}
        >
          <Stethoscope className="w-4 h-4" />
          <span>{lang === 'hi' ? 'डॉक्टर और स्लॉट प्रबंधन' : 'Doctor & Slot Management'}</span>
        </button>

        <button
          onClick={() => setActiveTab('facilities')}
          className={`py-3 px-4 font-extrabold text-xs border-b-2 transition flex items-center gap-2 whitespace-nowrap ${
            activeTab === 'facilities'
              ? 'border-sky-600 text-sky-700'
              : 'border-transparent text-slate-500 hover:text-slate-800'
          }`}
        >
          <Building2 className="w-4 h-4" />
          <span>{lang === 'hi' ? 'अस्पताल प्रबंधन' : 'Facility Management'}</span>
        </button>

        <button
          onClick={() => setActiveTab('emergency')}
          className={`py-3 px-4 font-extrabold text-xs border-b-2 transition flex items-center gap-2 whitespace-nowrap ${
            activeTab === 'emergency'
              ? 'border-rose-600 text-rose-700'
              : 'border-transparent text-slate-500 hover:text-slate-800'
          }`}
        >
          <Ambulance className="w-4 h-4 text-rose-600" />
          <span>{lang === 'hi' ? '🚨 आपातकालीन कतार' : '🚨 Emergency Triage Queue'} ({emergencyCases.length})</span>
        </button>
      </div>

      {/* TAB 1: PATIENT APPOINTMENTS TABLE WITH LIVE STATUS UPDATES */}
      {activeTab === 'requests' && (
        <div className="bg-white rounded-b-3xl border border-slate-200 shadow-sm p-5 space-y-4">
          
          {/* Status Filters */}
          <div className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-100 pb-3">
            <span className="text-xs font-bold text-slate-700 flex items-center gap-1">
              <Filter className="w-4 h-4 text-slate-400" />
              {lang === 'hi' ? 'फ़िल्टर स्थिति:' : 'Filter Appointment Status:'}
            </span>
            <div className="flex flex-wrap gap-1.5">
              {['all', 'confirmed', 'waiting', 'consultation', 'completed', 'cancelled', 'rescheduled', 'rejected'].map(st => (
                <button
                  key={st}
                  onClick={() => setFilterStatus(st)}
                  className={`px-3 py-1 rounded-xl text-xs font-bold capitalize transition ${
                    filterStatus === st
                      ? 'bg-sky-700 text-white shadow'
                      : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                  }`}
                >
                  {st === 'all' ? (lang === 'hi' ? 'सभी' : 'All') : st}
                </button>
              ))}
            </div>
          </div>

          {loading ? (
            <div className="py-8 text-center text-slate-500 font-semibold text-sm animate-pulse">
              {lang === 'hi' ? 'डेटाबेस से अनुरोध लोड हो रहे हैं...' : 'Loading patient appointments...'}
            </div>
          ) : filteredAppointments.length === 0 ? (
            <div className="py-8 text-center text-slate-500 text-sm">
              {lang === 'hi' ? 'कोई अनुरोध नहीं मिला' : 'No appointment records match the selected filter.'}
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs border-collapse">
                <thead>
                  <tr className="bg-slate-50 text-slate-500 font-bold border-b border-slate-200">
                    <th className="p-3">Token & Patient</th>
                    <th className="p-3">Service & Doctor</th>
                    <th className="p-3">Facility</th>
                    <th className="p-3">Date & Time</th>
                    <th className="p-3">Current Status</th>
                    <th className="p-3 text-right">Provider Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {filteredAppointments.map(apt => (
                    <tr key={apt.id} className="hover:bg-slate-50/80 transition">
                      <td className="p-3">
                        <div className="flex items-center gap-2">
                          <span className="font-mono text-xs font-extrabold bg-sky-100 text-sky-800 px-2 py-0.5 rounded">
                            {apt.token_number || `A-${100 + apt.id}`}
                          </span>
                          <div>
                            <div className="font-extrabold text-slate-900">{apt.patient_name}</div>
                            <div className="text-[11px] text-slate-500">📞 {apt.phone}</div>
                          </div>
                        </div>
                      </td>

                      <td className="p-3">
                        <div className="font-bold text-slate-800">{apt.service}</div>
                        <div className="text-[11px] text-slate-500">👨‍⚕️ {apt.doctor_name || 'Dr. Sharma'}</div>
                      </td>

                      <td className="p-3 font-medium text-slate-700">
                        🏥 {apt.facility_name || 'Government Hospital'}
                      </td>

                      <td className="p-3 font-bold text-sky-900">
                        📅 {apt.date}
                        <div className="text-[11px] text-slate-500 font-semibold">⏰ {apt.time}</div>
                      </td>

                      <td className="p-3">
                        <span className={`text-[10px] font-extrabold px-2.5 py-1 rounded-full uppercase inline-block ${
                          apt.status === 'confirmed'
                            ? 'bg-emerald-100 text-emerald-800'
                            : apt.status === 'waiting'
                            ? 'bg-amber-100 text-amber-900'
                            : apt.status === 'consultation'
                            ? 'bg-blue-100 text-blue-900'
                            : apt.status === 'completed'
                            ? 'bg-slate-200 text-slate-800'
                            : apt.status === 'cancelled' || apt.status === 'rejected'
                            ? 'bg-rose-100 text-rose-800'
                            : 'bg-purple-100 text-purple-800'
                        }`}>
                          {apt.status}
                        </span>
                      </td>

                      <td className="p-3 text-right">
                        <div className="flex flex-wrap items-center justify-end gap-1">
                          <button
                            onClick={() => setViewDetailApt(apt)}
                            className="bg-slate-100 hover:bg-slate-200 text-slate-700 font-bold text-[11px] px-2 py-1 rounded-lg transition"
                          >
                            Details
                          </button>

                          <button
                            onClick={() => handleStatusUpdate(apt.id, 'confirmed')}
                            className="bg-emerald-600 hover:bg-emerald-700 text-white font-extrabold text-[11px] px-2 py-1 rounded-lg transition"
                            title="Confirm"
                          >
                            Confirm
                          </button>

                          <button
                            onClick={() => handleStatusUpdate(apt.id, 'waiting')}
                            className="bg-amber-500 hover:bg-amber-600 text-white font-extrabold text-[11px] px-2 py-1 rounded-lg transition"
                            title="Set Waiting"
                          >
                            Waiting
                          </button>

                          <button
                            onClick={() => handleStatusUpdate(apt.id, 'consultation')}
                            className="bg-blue-600 hover:bg-blue-700 text-white font-extrabold text-[11px] px-2 py-1 rounded-lg transition"
                            title="Start Consultation"
                          >
                            In OPD
                          </button>

                          <button
                            onClick={() => handleStatusUpdate(apt.id, 'completed')}
                            className="bg-slate-700 hover:bg-slate-800 text-white font-extrabold text-[11px] px-2 py-1 rounded-lg transition"
                            title="Complete"
                          >
                            Done
                          </button>

                          <button
                            onClick={() => setRescheduleApt(apt)}
                            className="bg-purple-600 hover:bg-purple-700 text-white font-extrabold text-[11px] px-2 py-1 rounded-lg transition"
                          >
                            Reschedule
                          </button>

                          <button
                            onClick={() => handleStatusUpdate(apt.id, 'cancelled')}
                            className="bg-rose-600 hover:bg-rose-700 text-white font-extrabold text-[11px] px-2 py-1 rounded-lg transition"
                          >
                            Cancel
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {/* TAB 2: DOCTOR & SLOT AVAILABILITY MANAGEMENT */}
      {activeTab === 'doctors' && (
        <div className="bg-white rounded-b-3xl border border-slate-200 shadow-sm p-5 space-y-4">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-100 pb-3">
            <div>
              <h3 className="font-extrabold text-slate-900 text-sm flex items-center gap-2">
                <Stethoscope className="w-4 h-4 text-sky-600" />
                {lang === 'hi' ? 'अस्पताल डॉक्टर एवं ओपीडी स्लॉट प्रबंधन' : 'Doctor & OPD Slot Availability'}
              </h3>
              <p className="text-xs text-slate-500">
                {lang === 'hi'
                  ? 'मरीजों को दिखाई देने वाली डॉक्टर उपलब्धता नियंत्रित करें'
                  : 'Manage real-time doctor availability and OPD slots in SQLite database'}
              </p>
            </div>

            <button
              onClick={() => setShowAddSlotModal(true)}
              className="bg-sky-700 hover:bg-sky-800 text-white font-extrabold text-xs px-3 py-2 rounded-xl flex items-center gap-1.5 shadow transition self-start sm:self-center"
            >
              <Plus className="w-4 h-4 text-amber-300" />
              <span>{lang === 'hi' ? 'नया स्लॉट जोड़ें' : 'Add Doctor Slot'}</span>
            </button>
          </div>

          {loadingSlots ? (
            <div className="py-8 text-center text-slate-500 font-semibold text-sm animate-pulse">
              {lang === 'hi' ? 'स्लॉट लोड हो रहे हैं...' : 'Loading slots from database...'}
            </div>
          ) : (
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              {slots.map(s => (
                <div
                  key={s.id}
                  className={`p-4 rounded-2xl border text-left flex items-start justify-between gap-2 transition ${
                    s.available
                      ? 'bg-white border-slate-200 shadow-sm'
                      : 'bg-slate-100 border-slate-200 text-slate-500 opacity-75'
                  }`}
                >
                  <div className="space-y-1">
                    <div className="font-extrabold text-sm text-slate-900 flex items-center gap-1.5">
                      <Clock className="w-4 h-4 text-sky-600" />
                      <span>{s.time} ({s.date})</span>
                    </div>
                    <div className="text-xs font-bold text-slate-700">👨‍⚕️ {s.doctor_name || 'Dr. Sharma'}</div>
                    <div className="text-[11px] text-slate-500">🩺 Department: {s.department || 'General OPD'}</div>
                  </div>

                  <div className="flex flex-col items-end gap-2">
                    <button
                      onClick={() => handleToggleSlot(s.id)}
                      className={`text-[10px] font-black px-2.5 py-1 rounded-lg transition flex items-center gap-1 ${
                        s.available
                          ? 'bg-emerald-100 text-emerald-800 hover:bg-emerald-200 border border-emerald-300'
                          : 'bg-slate-200 text-slate-700 hover:bg-slate-300 border border-slate-300'
                      }`}
                    >
                      <span>{s.available ? '🟢 Available' : '🔴 Booked / Off'}</span>
                    </button>

                    <button
                      onClick={() => handleDeleteSlot(s.id)}
                      className="text-rose-600 hover:text-rose-800 text-[10px] font-bold flex items-center gap-0.5"
                    >
                      <Trash2 className="w-3 h-3" />
                      <span>{lang === 'hi' ? 'हटाएं' : 'Delete'}</span>
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* TAB 3: FACILITY MANAGEMENT */}
      {activeTab === 'facilities' && (
        <div className="bg-white rounded-b-3xl border border-slate-200 shadow-sm p-5 space-y-4">
          <div className="border-b border-slate-100 pb-3">
            <h3 className="font-extrabold text-slate-900 text-sm flex items-center gap-2">
              <Building2 className="w-4 h-4 text-purple-600" />
              {lang === 'hi' ? 'अस्पताल और प्राथमिक स्वास्थ्य केंद्र' : 'Facility Operational Management'}
            </h3>
            <p className="text-xs text-slate-500">
              {lang === 'hi'
                ? 'सरकारी अस्पताल, पीएचसी और आपातकालीन सेवा स्थिति प्रबंधित करें'
                : 'Manage government hospitals, PHCs, emergency capabilities, and live operational status'}
            </p>
          </div>

          <div className="space-y-3">
            {facilities.map(fac => {
              const statusObj = facilityStatusMap[fac.id] || { operational: true, emergency_active: fac.emergency_available };
              return (
                <div key={fac.id} className="p-4 rounded-2xl border border-slate-200 bg-slate-50/50 hover:bg-white hover:shadow-md transition flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <span className="font-extrabold text-slate-900 text-base">🏥 {fac.name}</span>
                      <span className="text-[10px] font-bold bg-sky-100 text-sky-800 px-2 py-0.5 rounded">
                        {fac.facility_type}
                      </span>
                    </div>

                    <div className="text-xs text-slate-600 flex flex-wrap items-center gap-3">
                      <span>📍 {fac.area}, {fac.city}</span>
                      <span>📞 {fac.contact_phone}</span>
                      <span>🩺 {fac.services}</span>
                    </div>

                    <div className="flex items-center gap-2 text-xs pt-0.5">
                      <span className={`font-bold px-2 py-0.5 rounded-full text-[10px] ${
                        statusObj.emergency_active ? 'bg-emerald-100 text-emerald-800' : 'bg-slate-200 text-slate-600'
                      }`}>
                        🚑 24/7 Emergency: {statusObj.emergency_active ? 'AVAILABLE' : 'UNAVAILABLE'}
                      </span>
                    </div>
                  </div>

                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => toggleFacilityOperational(fac.id)}
                      className={`text-xs font-extrabold px-3 py-1.5 rounded-xl border transition ${
                        statusObj.operational
                          ? 'bg-emerald-600 text-white hover:bg-emerald-700 border-emerald-700'
                          : 'bg-rose-600 text-white hover:bg-rose-700 border-rose-700'
                      }`}
                    >
                      {statusObj.operational ? '🟢 Operational' : '🔴 Maintenance'}
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* TAB 4: EMERGENCY TRIAGE QUEUE */}
      {activeTab === 'emergency' && (
        <div className="bg-white rounded-b-3xl border border-rose-200 shadow-sm p-5 space-y-4">
          
          {/* Healthcare Safety Policy Disclaimer Banner */}
          <div className="bg-rose-50 border border-rose-200 p-3.5 rounded-2xl flex items-start gap-3">
            <AlertTriangle className="w-5 h-5 text-rose-600 flex-shrink-0 mt-0.5" />
            <div className="text-xs text-rose-900 space-y-0.5">
              <div className="font-extrabold">🚨 JanSethu AI Non-Diagnostic Emergency Dispatch Policy</div>
              <div>
                JanSethu AI voice triage categorizes patient-reported urgency and locations for immediate 108 ambulance dispatch. 
                <strong> System does NOT perform clinical diagnosis or treatment prescribing.</strong>
              </div>
            </div>
          </div>

          <div className="border-b border-slate-100 pb-3 flex items-center justify-between">
            <h3 className="font-extrabold text-slate-900 text-sm flex items-center gap-2">
              <Ambulance className="w-4 h-4 text-rose-600" />
              {lang === 'hi' ? 'आपातकालीन ट्राइएज कतार' : 'Active Emergency Triage Queue (108)'}
            </h3>
            <span className="text-xs font-bold text-slate-500">Live Voice Triage Sync</span>
          </div>

          <div className="space-y-3">
            {emergencyCases.map(ec => (
              <div key={ec.id} className="p-4 rounded-2xl border border-rose-200 bg-rose-50/30 hover:bg-white hover:shadow-md transition flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                <div className="space-y-1">
                  <div className="flex items-center gap-2">
                    <span className="font-mono text-xs font-extrabold text-rose-800">#{ec.id}</span>
                    <span className="font-extrabold text-slate-900 text-base">{ec.patient_name}</span>
                    <span className="text-[10px] font-black bg-rose-600 text-white px-2.5 py-0.5 rounded-full uppercase">
                      {ec.urgency}
                    </span>
                  </div>

                  <div className="text-xs text-slate-700 font-medium space-y-0.5">
                    <div>📍 <strong>Location:</strong> {ec.location}</div>
                    <div>📞 <strong>Contact Phone:</strong> {ec.phone}</div>
                    <div className="text-rose-900 font-bold bg-rose-100/80 px-2 py-1 rounded-lg inline-block">
                      🗣️ <strong>Detected Issue:</strong> {ec.detected_issue}
                    </div>
                  </div>

                  <div className="text-[11px] text-slate-400 font-semibold pt-0.5">
                    ⏱️ Received: {ec.timestamp} | Status: <strong className="text-slate-800">{ec.status}</strong>
                  </div>
                </div>

                <div className="flex flex-col sm:items-end gap-2 self-start sm:self-center">
                  <button
                    onClick={() => handleDispatchEmergency(ec.id)}
                    className="bg-rose-600 hover:bg-rose-700 text-white font-extrabold text-xs px-3.5 py-2 rounded-xl flex items-center gap-1.5 shadow transition"
                  >
                    <Ambulance className="w-4 h-4" />
                    <span>{lang === 'hi' ? '108 एम्बुलेंस भेजें' : 'Dispatch 108 Ambulance'}</span>
                  </button>

                  <span className="text-[10px] font-bold text-slate-500">
                    Auto-routes to nearest facility
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* MODAL 1: APPOINTMENT DETAILS */}
      {viewDetailApt && (
        <div className="fixed inset-0 bg-slate-950/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-3xl p-6 max-w-md w-full shadow-2xl space-y-4">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <h3 className="font-black text-slate-900 text-lg">
                {lang === 'hi' ? 'अनुरोध विवरण' : 'Appointment Details'}
              </h3>
              <button
                onClick={() => setViewDetailApt(null)}
                className="text-slate-400 hover:text-slate-600 font-bold text-sm"
              >
                ✕
              </button>
            </div>

            <div className="bg-slate-50 p-4 rounded-2xl space-y-2 text-xs">
              <div className="flex justify-between">
                <span className="text-slate-400 font-bold">Token Number:</span>
                <span className="font-mono font-extrabold text-sky-800">{viewDetailApt.token_number || `A-${100 + viewDetailApt.id}`}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-400 font-bold">Patient Name:</span>
                <span className="font-bold text-slate-900">{viewDetailApt.patient_name}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-400 font-bold">Phone Number:</span>
                <span className="font-bold text-sky-800">{viewDetailApt.phone}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-400 font-bold">Requested Service:</span>
                <span className="font-bold text-slate-800">{viewDetailApt.service}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-400 font-bold">Facility:</span>
                <span className="font-bold text-slate-800">{viewDetailApt.facility_name}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-400 font-bold">Date & Time:</span>
                <span className="font-extrabold text-amber-700">{viewDetailApt.date} @ {viewDetailApt.time}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-400 font-bold">Current Status:</span>
                <span className="font-black uppercase text-sky-700">{viewDetailApt.status}</span>
              </div>
            </div>

            <div className="flex gap-2 pt-2">
              <button
                onClick={() => {
                  handleStatusUpdate(viewDetailApt.id, 'confirmed');
                  setViewDetailApt(null);
                }}
                className="flex-1 bg-emerald-600 text-white font-extrabold py-2.5 rounded-xl text-xs"
              >
                Confirm
              </button>
              <button
                onClick={() => {
                  handleStatusUpdate(viewDetailApt.id, 'cancelled');
                  setViewDetailApt(null);
                }}
                className="flex-1 bg-rose-600 text-white font-extrabold py-2.5 rounded-xl text-xs"
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}

      {/* MODAL 2: RESCHEDULE APPOINTMENT */}
      {rescheduleApt && (
        <div className="fixed inset-0 bg-slate-950/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <form onSubmit={handleRescheduleSubmit} className="bg-white rounded-3xl p-6 max-w-md w-full shadow-2xl space-y-4">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <h3 className="font-black text-slate-900 text-lg">
                {lang === 'hi' ? 'अपॉइंटमेंट समय बदलें' : 'Reschedule Appointment'}
              </h3>
              <button
                type="button"
                onClick={() => setRescheduleApt(null)}
                className="text-slate-400 hover:text-slate-600 font-bold text-sm"
              >
                ✕
              </button>
            </div>

            <p className="text-xs text-slate-600 font-medium">
              Patient: <strong className="text-slate-900">{rescheduleApt.patient_name}</strong> (#{rescheduleApt.id})
            </p>

            <div>
              <label className="block text-xs font-bold text-slate-700 uppercase mb-1">
                {lang === 'hi' ? 'नई तिथि' : 'New Date'}
              </label>
              <select
                value={newDate}
                onChange={(e) => setNewDate(e.target.value)}
                className="w-full bg-slate-50 border border-slate-300 p-2.5 rounded-xl text-xs font-bold"
              >
                <option value="Today">Today</option>
                <option value="Tomorrow">Tomorrow</option>
                <option value="Day After">Day After</option>
              </select>
            </div>

            <div>
              <label className="block text-xs font-bold text-slate-700 uppercase mb-1">
                {lang === 'hi' ? 'नया समय' : 'New Time'}
              </label>
              <select
                value={newTime}
                onChange={(e) => setNewTime(e.target.value)}
                className="w-full bg-slate-50 border border-slate-300 p-2.5 rounded-xl text-xs font-bold"
              >
                <option value="09:00 AM">09:00 AM</option>
                <option value="10:30 AM">10:30 AM</option>
                <option value="11:45 AM">11:45 AM</option>
                <option value="02:00 PM">02:00 PM</option>
                <option value="03:30 PM">03:30 PM</option>
                <option value="04:30 PM">04:30 PM</option>
              </select>
            </div>

            <button
              type="submit"
              className="w-full bg-purple-700 hover:bg-purple-800 text-white font-extrabold py-3 rounded-xl text-xs shadow"
            >
              {lang === 'hi' ? 'अपॉइंटमेंट रिशेड्यूल करें' : 'Confirm & Save Reschedule'}
            </button>
          </form>
        </div>
      )}

      {/* MODAL 3: ADD NEW SLOT */}
      {showAddSlotModal && (
        <div className="fixed inset-0 bg-slate-950/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <form onSubmit={handleCreateSlotSubmit} className="bg-white rounded-3xl p-6 max-w-md w-full shadow-2xl space-y-4">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <h3 className="font-black text-slate-900 text-lg">
                {lang === 'hi' ? 'नया ओपीडी स्लॉट जोड़ें' : 'Add New Doctor Slot'}
              </h3>
              <button
                type="button"
                onClick={() => setShowAddSlotModal(false)}
                className="text-slate-400 hover:text-slate-600 font-bold text-sm"
              >
                ✕
              </button>
            </div>

            <div>
              <label className="block text-xs font-bold text-slate-700 uppercase mb-1">Date</label>
              <select
                value={newSlotData.date}
                onChange={(e) => setNewSlotData({ ...newSlotData, date: e.target.value })}
                className="w-full bg-slate-50 border border-slate-300 p-2 rounded-xl text-xs font-bold"
              >
                <option value="Today">Today</option>
                <option value="Tomorrow">Tomorrow</option>
                <option value="Day After">Day After</option>
              </select>
            </div>

            <div>
              <label className="block text-xs font-bold text-slate-700 uppercase mb-1">Time</label>
              <input
                type="text"
                value={newSlotData.time}
                onChange={(e) => setNewSlotData({ ...newSlotData, time: e.target.value })}
                className="w-full bg-slate-50 border border-slate-300 p-2 rounded-xl text-xs font-bold"
              />
            </div>

            <div>
              <label className="block text-xs font-bold text-slate-700 uppercase mb-1">Doctor Name</label>
              <input
                type="text"
                value={newSlotData.doctor_name}
                onChange={(e) => setNewSlotData({ ...newSlotData, doctor_name: e.target.value })}
                className="w-full bg-slate-50 border border-slate-300 p-2 rounded-xl text-xs font-bold"
              />
            </div>

            <div>
              <label className="block text-xs font-bold text-slate-700 uppercase mb-1">Department</label>
              <input
                type="text"
                value={newSlotData.department}
                onChange={(e) => setNewSlotData({ ...newSlotData, department: e.target.value })}
                className="w-full bg-slate-50 border border-slate-300 p-2 rounded-xl text-xs font-bold"
              />
            </div>

            <button
              type="submit"
              className="w-full bg-sky-700 hover:bg-sky-800 text-white font-extrabold py-3 rounded-xl text-xs shadow"
            >
              Save Slot to SQLite Database
            </button>
          </form>
        </div>
      )}

      {/* MODAL 4: PROVIDER ROLE SWITCHER */}
      {showLoginModal && (
        <div className="fixed inset-0 bg-slate-950/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-3xl p-6 max-w-md w-full shadow-2xl space-y-4">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <h3 className="font-black text-slate-900 text-lg">
                {lang === 'hi' ? 'प्रदाता खाता भूमिका चुनें' : 'Select Provider Account Role'}
              </h3>
              <button
                onClick={() => setShowLoginModal(false)}
                className="text-slate-400 hover:text-slate-600 font-bold text-sm"
              >
                ✕
              </button>
            </div>

            <div className="space-y-2">
              <button
                onClick={() => {
                  setActiveRole('admin');
                  setSelectedFacilityId('all');
                  setShowLoginModal(false);
                }}
                className={`w-full text-left p-3.5 rounded-2xl border transition flex items-center justify-between ${
                  activeRole === 'admin' ? 'bg-sky-50 border-sky-500 text-sky-950' : 'bg-slate-50 border-slate-200 hover:bg-slate-100'
                }`}
              >
                <div>
                  <div className="font-extrabold text-xs">🏢 Central Health Admin</div>
                  <div className="text-[11px] text-slate-500">Full access to all facilities, appointments, emergency dispatch</div>
                </div>
                {activeRole === 'admin' && <CheckCircle className="w-5 h-5 text-sky-600" />}
              </button>

              <button
                onClick={() => {
                  setActiveRole('opd');
                  if (facilities.length > 0) setSelectedFacilityId(facilities[0].id);
                  setShowLoginModal(false);
                }}
                className={`w-full text-left p-3.5 rounded-2xl border transition flex items-center justify-between ${
                  activeRole === 'opd' ? 'bg-sky-50 border-sky-500 text-sky-950' : 'bg-slate-50 border-slate-200 hover:bg-slate-100'
                }`}
              >
                <div>
                  <div className="font-extrabold text-xs">🏥 Hospital OPD Desk</div>
                  <div className="text-[11px] text-slate-500">Manage hospital appointments, doctor OPD slots & patient check-in</div>
                </div>
                {activeRole === 'opd' && <CheckCircle className="w-5 h-5 text-sky-600" />}
              </button>

              <button
                onClick={() => {
                  setActiveRole('dispatcher');
                  setActiveTab('emergency');
                  setShowLoginModal(false);
                }}
                className={`w-full text-left p-3.5 rounded-2xl border transition flex items-center justify-between ${
                  activeRole === 'dispatcher' ? 'bg-rose-50 border-rose-500 text-rose-950' : 'bg-slate-50 border-slate-200 hover:bg-slate-100'
                }`}
              >
                <div>
                  <div className="font-extrabold text-xs">🚑 108 Emergency Control Dispatcher</div>
                  <div className="text-[11px] text-slate-500">View real-time voice triage queue & dispatch ambulances</div>
                </div>
                {activeRole === 'dispatcher' && <CheckCircle className="w-5 h-5 text-rose-600" />}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
