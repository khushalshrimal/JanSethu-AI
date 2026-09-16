import React, { useEffect, useState } from 'react';
import { LayoutDashboard, CheckCircle, XCircle, Clock, Calendar, User, Phone, Building2, Filter, RefreshCw, AlertCircle } from 'lucide-react';
import { getAppointments, updateAppointmentStatus } from '../api';
import DemoBadge from '../components/DemoBadge';

export default function ProviderDashboardScreen({ lang }) {
  const [appointments, setAppointments] = useState([]);
  const [filterStatus, setFilterStatus] = useState('all');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadAppointments();
  }, []);

  async function loadAppointments() {
    setLoading(true);
    try {
      const data = await getAppointments();
      setAppointments(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  }

  const handleStatusUpdate = async (id, newStatus) => {
    try {
      await updateAppointmentStatus(id, newStatus);
      setAppointments(prev =>
        prev.map(item => item.id === id ? { ...item, status: newStatus } : item)
      );
    } catch (err) {
      console.error(err);
    }
  };

  const filteredAppointments = appointments.filter(a => {
    if (filterStatus === 'all') return true;
    return a.status === filterStatus;
  });

  const pendingCount = appointments.filter(a => a.status === 'pending').length;
  const confirmedCount = appointments.filter(a => a.status === 'confirmed').length;

  return (
    <div className="space-y-6 pb-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-extrabold text-slate-900 flex items-center gap-2">
            <LayoutDashboard className="w-6 h-6 text-sky-600" />
            {lang === 'hi' ? 'स्वास्थ्य प्रदाता डैशबोर्ड' : 'Healthcare Provider Dashboard'}
          </h2>
          <p className="text-xs text-slate-500 mt-0.5">
            {lang === 'hi'
              ? 'अस्पताल कर्मचारियों द्वारा अपॉइंटमेंट अनुरोध प्रबंधन'
              : 'Review, confirm, or reject patient appointment requests'}
          </p>
        </div>
        <DemoBadge lang={lang} />
      </div>

      {/* Overview Stat Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
        <div className="bg-white p-4 rounded-2xl border border-slate-200 shadow-sm flex items-center justify-between">
          <div>
            <div className="text-xs font-bold text-slate-500 uppercase">
              {lang === 'hi' ? 'कुल अनुरोध' : 'Total Requests'}
            </div>
            <div className="text-2xl font-black text-slate-900 mt-0.5">{appointments.length}</div>
          </div>
          <div className="bg-sky-100 text-sky-700 p-2.5 rounded-xl">
            <Calendar className="w-6 h-6" />
          </div>
        </div>

        <div className="bg-white p-4 rounded-2xl border border-amber-200 shadow-sm flex items-center justify-between">
          <div>
            <div className="text-xs font-bold text-amber-800 uppercase">
              {lang === 'hi' ? 'लंबित स्वीकृति' : 'Pending Approval'}
            </div>
            <div className="text-2xl font-black text-amber-900 mt-0.5">{pendingCount}</div>
          </div>
          <div className="bg-amber-100 text-amber-800 p-2.5 rounded-xl">
            <Clock className="w-6 h-6" />
          </div>
        </div>

        <div className="bg-white p-4 rounded-2xl border border-emerald-200 shadow-sm flex items-center justify-between">
          <div>
            <div className="text-xs font-bold text-emerald-800 uppercase">
              {lang === 'hi' ? 'स्वीकृत (Confirmed)' : 'Confirmed Appointments'}
            </div>
            <div className="text-2xl font-black text-emerald-900 mt-0.5">{confirmedCount}</div>
          </div>
          <div className="bg-emerald-100 text-emerald-800 p-2.5 rounded-xl">
            <CheckCircle className="w-6 h-6" />
          </div>
        </div>
      </div>

      {/* Filter Status Bar */}
      <div className="bg-white p-2.5 rounded-2xl border border-slate-200 shadow-sm flex items-center justify-between">
        <span className="text-xs font-bold text-slate-700 ml-2 flex items-center gap-1.5">
          <Filter className="w-4 h-4 text-slate-400" />
          {lang === 'hi' ? 'स्थिति अनुसार फ़िल्टर:' : 'Filter Requests:'}
        </span>
        <div className="flex gap-1.5">
          {['all', 'pending', 'confirmed', 'rejected'].map(st => (
            <button
              key={st}
              onClick={() => setFilterStatus(st)}
              className={`px-3 py-1.5 rounded-xl text-xs font-bold capitalize transition ${
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

      {/* Appointment Requests Table / List */}
      <div className="bg-white rounded-3xl border border-slate-200 shadow-sm p-5 space-y-4">
        <div className="flex items-center justify-between border-b border-slate-100 pb-3">
          <h3 className="font-extrabold text-slate-900 text-sm">
            {lang === 'hi' ? 'अपॉइंटमेंट अनुरोध सूची' : 'Patient Appointment Requests'}
          </h3>
          <button
            onClick={loadAppointments}
            className="text-xs font-bold text-sky-700 hover:text-sky-900 flex items-center gap-1"
          >
            <RefreshCw className="w-3.5 h-3.5" />
            <span>{lang === 'hi' ? 'ताज़ा करें' : 'Refresh'}</span>
          </button>
        </div>

        {loading ? (
          <div className="py-8 text-center text-slate-500 font-semibold text-sm animate-pulse">
            {lang === 'hi' ? 'डैशबोर्ड लोड हो रहा है...' : 'Loading provider requests...'}
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
                className="p-4 rounded-2xl border border-slate-200 bg-slate-50/50 hover:bg-white hover:shadow-sm transition flex flex-col sm:flex-row sm:items-center justify-between gap-3"
              >
                <div className="space-y-1">
                  <div className="flex items-center gap-2">
                    <span className="font-mono text-xs font-bold text-slate-500">#{apt.id}</span>
                    <span className="font-extrabold text-slate-900 text-base">{apt.patient_name}</span>
                    <span className={`text-[10px] font-extrabold px-2.5 py-0.5 rounded-full uppercase ${
                      apt.status === 'confirmed'
                        ? 'bg-emerald-100 text-emerald-800'
                        : apt.status === 'rejected'
                        ? 'bg-rose-100 text-rose-800'
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

                {/* Provider Decision Buttons */}
                <div className="flex items-center gap-2 self-start sm:self-center">
                  {apt.status === 'pending' && (
                    <>
                      <button
                        onClick={() => handleStatusUpdate(apt.id, 'confirmed')}
                        className="bg-emerald-600 hover:bg-emerald-700 text-white font-extrabold text-xs px-3 py-2 rounded-xl flex items-center gap-1 shadow-sm transition"
                      >
                        <CheckCircle className="w-4 h-4" />
                        <span>{lang === 'hi' ? 'स्वीकार करें' : 'Confirm'}</span>
                      </button>

                      <button
                        onClick={() => handleStatusUpdate(apt.id, 'rejected')}
                        className="bg-rose-600 hover:bg-rose-700 text-white font-extrabold text-xs px-3 py-2 rounded-xl flex items-center gap-1 shadow-sm transition"
                      >
                        <XCircle className="w-4 h-4" />
                        <span>{lang === 'hi' ? 'अस्वीकार करें' : 'Reject'}</span>
                      </button>
                    </>
                  )}

                  {apt.status !== 'pending' && (
                    <button
                      onClick={() => handleStatusUpdate(apt.id, 'pending')}
                      className="bg-slate-200 hover:bg-slate-300 text-slate-700 font-bold text-xs px-3 py-1.5 rounded-xl transition"
                    >
                      {lang === 'hi' ? 'पुनरावलोकन' : 'Reset to Pending'}
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
