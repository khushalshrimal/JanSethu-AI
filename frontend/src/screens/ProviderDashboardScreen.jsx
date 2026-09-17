import React, { useEffect, useState } from 'react';
import { 
  LayoutDashboard, CheckCircle, XCircle, Clock, Calendar, User, Phone, 
  Building2, Filter, RefreshCw, AlertCircle, Plus, Edit, Trash2, Eye, ShieldCheck, Check
} from 'lucide-react';
import { 
  getAppointments, updateAppointmentStatus, rescheduleAppointment, 
  getFacilities, getFacilitySlots, addSlot, toggleSlot, deleteSlot 
} from '../api';
import DemoBadge from '../components/DemoBadge';

export default function ProviderDashboardScreen({ lang }) {
  const [activeTab, setActiveTab] = useState('requests'); // 'requests' | 'slots'
  const [facilities, setFacilities] = useState([]);
  const [selectedFacilityId, setSelectedFacilityId] = useState('all');
  
  // Appointment state
  const [appointments, setAppointments] = useState([]);
  const [filterStatus, setFilterStatus] = useState('all');
  const [loading, setLoading] = useState(true);

  // Modals & Dialog state
  const [viewDetailApt, setViewDetailApt] = useState(null);
  const [rescheduleApt, setRescheduleApt] = useState(null);
  const [newDate, setNewDate] = useState('Tomorrow');
  const [newTime, setNewTime] = useState('02:00 PM');

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
    if (activeTab === 'slots') {
      loadFacilitySlots(slotFacilityId);
    }
  }, [activeTab, slotFacilityId]);

  async function loadInitialData() {
    setLoading(true);
    try {
      const [facRes, aptRes] = await Promise.all([
        getFacilities(),
        getAppointments()
      ]);
      setFacilities(facRes);
      setAppointments(aptRes);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  }

  async function loadAppointments() {
    setLoading(true);
    try {
      const params = selectedFacilityId !== 'all' ? { facility_id: selectedFacilityId } : {};
      const data = await getAppointments(params);
      setAppointments(data);
    } catch (err) {
      console.error(err);
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

  const filteredAppointments = appointments.filter(a => {
    const matchesFacility = selectedFacilityId === 'all' || Number(a.facility_id) === Number(selectedFacilityId);
    const matchesStatus = filterStatus === 'all' || a.status === filterStatus;
    return matchesFacility && matchesStatus;
  });

  const pendingCount = appointments.filter(a => a.status === 'pending').length;
  const confirmedCount = appointments.filter(a => a.status === 'confirmed').length;
  const rejectedCount = appointments.filter(a => a.status === 'rejected').length;
  const rescheduledCount = appointments.filter(a => a.status === 'rescheduled').length;

  return (
    <div className="space-y-6 pb-6">
      {/* Header & Demo Auth Switcher */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div>
          <div className="flex items-center gap-2">
            <span className="bg-sky-100 text-sky-900 font-extrabold text-[10px] uppercase px-2.5 py-0.5 rounded-full flex items-center gap-1">
              <ShieldCheck className="w-3 h-3 text-sky-600" />
              {lang === 'hi' ? 'प्रदाता पोर्टल (डेमो)' : 'Provider Portal (DEMO)'}
            </span>
          </div>
          <h2 className="text-xl font-extrabold text-slate-900 mt-1 flex items-center gap-2">
            <LayoutDashboard className="w-6 h-6 text-sky-600" />
            {lang === 'hi' ? 'स्वास्थ्य प्रदाता डैशबोर्ड' : 'Healthcare Provider Dashboard'}
          </h2>
        </div>
        <DemoBadge lang={lang} />
      </div>

      {/* Demo Login Banner */}
      <div className="bg-slate-900 text-white p-4 rounded-2xl flex flex-col sm:flex-row sm:items-center justify-between gap-3 shadow-md">
        <div className="flex items-center gap-3">
          <div className="bg-sky-500/20 text-sky-400 p-2.5 rounded-xl">
            <Building2 className="w-6 h-6" />
          </div>
          <div>
            <div className="text-xs text-slate-400 font-medium">
              {lang === 'hi' ? 'लॉग इन प्रदाता खाता:' : 'Active Demo Provider Account:'}
            </div>
            <div className="font-extrabold text-sm text-white">
              {selectedFacilityId === 'all'
                ? (lang === 'hi' ? 'समस्त सरकारी अस्पताल एडमिन' : 'Central Admin (All Facilities)')
                : facilities.find(f => Number(f.id) === Number(selectedFacilityId))?.name || 'District Hospital'}
            </div>
          </div>
        </div>

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
          <option value="all">🏢 {lang === 'hi' ? 'सभी अस्पताल (All Facilities)' : 'All Facilities (Central Admin)'}</option>
          {facilities.map(f => (
            <option key={f.id} value={f.id}>🏥 {f.name}</option>
          ))}
        </select>
      </div>

      {/* Overview Statistics Cards */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <div className="bg-white p-3.5 rounded-2xl border border-slate-200 shadow-sm">
          <div className="text-[11px] font-bold text-slate-500 uppercase">
            {lang === 'hi' ? 'कुल अनुरोध' : 'Total Requests'}
          </div>
          <div className="text-2xl font-black text-slate-900 mt-0.5">{appointments.length}</div>
        </div>

        <div className="bg-white p-3.5 rounded-2xl border border-amber-200 shadow-sm">
          <div className="text-[11px] font-bold text-amber-800 uppercase">
            {lang === 'hi' ? 'लंबित' : 'Pending'}
          </div>
          <div className="text-2xl font-black text-amber-900 mt-0.5">{pendingCount}</div>
        </div>

        <div className="bg-white p-3.5 rounded-2xl border border-emerald-200 shadow-sm">
          <div className="text-[11px] font-bold text-emerald-800 uppercase">
            {lang === 'hi' ? 'स्वीकृत' : 'Confirmed'}
          </div>
          <div className="text-2xl font-black text-emerald-900 mt-0.5">{confirmedCount}</div>
        </div>

        <div className="bg-white p-3.5 rounded-2xl border border-purple-200 shadow-sm">
          <div className="text-[11px] font-bold text-purple-800 uppercase">
            {lang === 'hi' ? 'पुनर्निर्धारित' : 'Rescheduled'}
          </div>
          <div className="text-2xl font-black text-purple-900 mt-0.5">{rescheduledCount}</div>
        </div>
      </div>

      {/* Provider Section Tabs */}
      <div className="flex border-b border-slate-200 bg-white rounded-t-2xl px-3 pt-2">
        <button
          onClick={() => setActiveTab('requests')}
          className={`py-3 px-4 font-extrabold text-xs border-b-2 transition flex items-center gap-2 ${
            activeTab === 'requests'
              ? 'border-sky-600 text-sky-700'
              : 'border-transparent text-slate-500 hover:text-slate-800'
          }`}
        >
          <Calendar className="w-4 h-4" />
          <span>{lang === 'hi' ? 'अपॉइंटमेंट अनुरोध' : 'Patient Requests'} ({filteredAppointments.length})</span>
        </button>

        <button
          onClick={() => setActiveTab('slots')}
          className={`py-3 px-4 font-extrabold text-xs border-b-2 transition flex items-center gap-2 ${
            activeTab === 'slots'
              ? 'border-sky-600 text-sky-700'
              : 'border-transparent text-slate-500 hover:text-slate-800'
          }`}
        >
          <Clock className="w-4 h-4" />
          <span>{lang === 'hi' ? 'डॉक्टर स्लॉट प्रबंधन' : 'Slot Management'}</span>
        </button>
      </div>

      {/* TAB 1: PATIENT APPOINTMENTS LIST */}
      {activeTab === 'requests' && (
        <div className="bg-white rounded-b-3xl border border-slate-200 shadow-sm p-5 space-y-4">
          
          {/* Status Filters */}
          <div className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-100 pb-3">
            <span className="text-xs font-bold text-slate-700 flex items-center gap-1">
              <Filter className="w-4 h-4 text-slate-400" />
              {lang === 'hi' ? 'फ़िल्टर:' : 'Filter Status:'}
            </span>
            <div className="flex flex-wrap gap-1.5">
              {['all', 'pending', 'confirmed', 'rescheduled', 'rejected'].map(st => (
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
              {lang === 'hi' ? 'डेटाबेस से अनुरोध लोड हो रहे हैं...' : 'Loading patient requests...'}
            </div>
          ) : filteredAppointments.length === 0 ? (
            <div className="py-8 text-center text-slate-500 text-sm">
              {lang === 'hi' ? 'कोई अनुरोध नहीं मिला' : 'No requests found for this filter.'}
            </div>
          ) : (
            <div className="space-y-3">
              {filteredAppointments.map(apt => (
                <div
                  key={apt.id}
                  className="p-4 rounded-2xl border border-slate-200 bg-slate-50/60 hover:bg-white hover:shadow-md transition flex flex-col md:flex-row md:items-center justify-between gap-3"
                >
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <span className="font-mono text-xs font-bold text-slate-400">#{apt.id}</span>
                      <span className="font-black text-slate-900 text-base">{apt.patient_name}</span>
                      <span className={`text-[10px] font-extrabold px-2.5 py-0.5 rounded-full uppercase ${
                        apt.status === 'confirmed'
                          ? 'bg-emerald-100 text-emerald-800'
                          : apt.status === 'rejected'
                          ? 'bg-rose-100 text-rose-800'
                          : apt.status === 'rescheduled'
                          ? 'bg-purple-100 text-purple-800'
                          : 'bg-amber-100 text-amber-900'
                      }`}>
                        {apt.status}
                      </span>
                    </div>

                    <div className="text-xs text-slate-600 flex flex-wrap items-center gap-3">
                      <span>📞 {apt.phone}</span>
                      <span>🏥 {apt.facility_name}</span>
                      <span>🩺 {apt.service}</span>
                    </div>

                    <div className="text-xs font-bold text-sky-800">
                      📅 {apt.date} @ {apt.time}
                    </div>
                  </div>

                  {/* Actions */}
                  <div className="flex flex-wrap items-center gap-1.5 self-start md:self-center">
                    <button
                      onClick={() => setViewDetailApt(apt)}
                      className="bg-white border border-slate-200 hover:bg-slate-100 text-slate-700 font-bold text-xs px-2.5 py-1.5 rounded-xl flex items-center gap-1 transition shadow-sm"
                    >
                      <Eye className="w-3.5 h-3.5 text-sky-600" />
                      <span>{lang === 'hi' ? 'विवरण' : 'Details'}</span>
                    </button>

                    <button
                      onClick={() => handleStatusUpdate(apt.id, 'confirmed')}
                      className="bg-emerald-600 hover:bg-emerald-700 text-white font-extrabold text-xs px-2.5 py-1.5 rounded-xl flex items-center gap-1 transition shadow-sm"
                    >
                      <CheckCircle className="w-3.5 h-3.5" />
                      <span>{lang === 'hi' ? 'स्वीकार' : 'Confirm'}</span>
                    </button>

                    <button
                      onClick={() => setRescheduleApt(apt)}
                      className="bg-purple-600 hover:bg-purple-700 text-white font-extrabold text-xs px-2.5 py-1.5 rounded-xl flex items-center gap-1 transition shadow-sm"
                    >
                      <Clock className="w-3.5 h-3.5" />
                      <span>{lang === 'hi' ? 'समय बदलें' : 'Reschedule'}</span>
                    </button>

                    <button
                      onClick={() => handleStatusUpdate(apt.id, 'rejected')}
                      className="bg-rose-600 hover:bg-rose-700 text-white font-extrabold text-xs px-2.5 py-1.5 rounded-xl flex items-center gap-1 transition shadow-sm"
                    >
                      <XCircle className="w-3.5 h-3.5" />
                      <span>{lang === 'hi' ? 'अस्वीकार' : 'Reject'}</span>
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* TAB 2: DOCTOR SLOT MANAGEMENT */}
      {activeTab === 'slots' && (
        <div className="bg-white rounded-b-3xl border border-slate-200 shadow-sm p-5 space-y-4">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-100 pb-3">
            <div>
              <h3 className="font-extrabold text-slate-900 text-sm">
                {lang === 'hi' ? 'अस्पताल स्लॉट प्रबंधन' : 'Doctor & OPD Slot Availability'}
              </h3>
              <p className="text-xs text-slate-500">
                {lang === 'hi'
                  ? 'मरीजों को दिखाई देने वाले ओपीडी स्लॉट नियंत्रित करें'
                  : 'Manage available doctor slots directly in SQLite database'}
              </p>
            </div>

            <button
              onClick={() => setShowAddSlotModal(true)}
              className="bg-sky-700 hover:bg-sky-800 text-white font-extrabold text-xs px-3 py-2 rounded-xl flex items-center gap-1.5 shadow transition self-start sm:self-center"
            >
              <Plus className="w-4 h-4 text-amber-300" />
              <span>{lang === 'hi' ? 'नया स्लॉट जोड़ें' : 'Add New Slot'}</span>
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
                      ? 'bg-white border-slate-200'
                      : 'bg-slate-100 border-slate-200 text-slate-500 opacity-75'
                  }`}
                >
                  <div className="space-y-1">
                    <div className="font-extrabold text-sm text-slate-900 flex items-center gap-1.5">
                      <Clock className="w-4 h-4 text-sky-600" />
                      <span>{s.time} ({s.date})</span>
                    </div>
                    <div className="text-xs font-bold text-slate-700">👨‍⚕️ {s.doctor_name || 'OPD Doctor'}</div>
                    <div className="text-[11px] text-slate-500">🩺 {s.department || 'General'}</div>
                  </div>

                  <div className="flex flex-col items-end gap-2">
                    <button
                      onClick={() => handleToggleSlot(s.id)}
                      className={`text-[10px] font-black px-2.5 py-1 rounded-lg transition ${
                        s.available
                          ? 'bg-emerald-100 text-emerald-800 hover:bg-emerald-200'
                          : 'bg-slate-200 text-slate-700 hover:bg-slate-300'
                      }`}
                    >
                      {s.available ? (lang === 'hi' ? 'उपलब्ध (Available)' : 'Available') : (lang === 'hi' ? 'बुक (Booked)' : 'Booked')}
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
                <span className="text-slate-400 font-bold">Ticket ID:</span>
                <span className="font-mono font-extrabold text-slate-800">#{viewDetailApt.id}</span>
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
                  handleStatusUpdate(viewDetailApt.id, 'rejected');
                  setViewDetailApt(null);
                }}
                className="flex-1 bg-rose-600 text-white font-extrabold py-2.5 rounded-xl text-xs"
              >
                Reject
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
    </div>
  );
}
