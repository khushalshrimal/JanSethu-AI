import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { getMyAppointments, cancelAppointment, rescheduleAppointment, lookupAppointmentByConfirmationCode, checkInAppointment } from '../services/appointmentService';
import { getDoctorAvailability } from '../services/doctorService';
import { Calendar, Clock, MapPin, Search, AlertCircle, RefreshCw, XCircle, CheckCircle, RotateCw, FileText, ArrowRight } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

export default function MyAppointments() {
  const { user, isAuthenticated } = useAuth();
  const navigate = useNavigate();

  const [appointments, setAppointments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState('ALL');

  // Confirmation Code Lookup state
  const [codeQuery, setCodeQuery] = useState('');
  const [lookupResult, setLookupResult] = useState(null);
  const [lookupLoading, setLookupLoading] = useState(false);
  const [lookupError, setLookupError] = useState(null);

  // Cancellation Modal state
  const [cancelingAppt, setCancelingAppt] = useState(null);
  const [cancelReason, setCancelReason] = useState('Schedule change / Patient personal request');
  const [cancelLoading, setCancelLoading] = useState(false);

  // Reschedule Modal state
  const [reschedulingAppt, setReschedulingAppt] = useState(null);
  const [rescheduleDate, setRescheduleDate] = useState(new Date().toISOString().split('T')[0]);
  const [rescheduleSlots, setRescheduleSlots] = useState([]);
  const [rescheduleSlotLoading, setRescheduleSlotLoading] = useState(false);
  const [selectedRescheduleSlot, setSelectedRescheduleSlot] = useState(null);
  const [rescheduleLoading, setRescheduleLoading] = useState(false);
  const [rescheduleError, setRescheduleError] = useState(null);

  const fetchAppointments = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await getMyAppointments();
      setAppointments(data);
    } catch (err) {
      setError(err.message || err.response?.data?.detail || 'Failed to fetch appointments.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAppointments();
  }, []);

  const handleLookupSubmit = async (e) => {
    e.preventDefault();
    if (!codeQuery.trim()) return;
    setLookupLoading(true);
    setLookupError(null);
    setLookupResult(null);
    try {
      const result = await lookupAppointmentByConfirmationCode(codeQuery.trim());
      setLookupResult(result);
    } catch (err) {
      setLookupError(err.response?.data?.detail || 'No appointment found matching this confirmation code.');
    } finally {
      setLookupLoading(false);
    }
  };

  const handleCheckIn = async (apptId) => {
    try {
      const res = await checkInAppointment(apptId);
      alert(`Check-in Successful! Your Queue Token is ${res.queue_token}`);
      fetchAppointments();
    } catch (err) {
      alert(err.response?.data?.detail || 'Check-in failed.');
    }
  };

  const handleOpenCancelModal = (appt) => {
    setCancelingAppt(appt);
    setCancelReason('Schedule change / Patient personal request');
  };

  const handleConfirmCancel = async () => {
    if (!cancelingAppt) return;
    setCancelLoading(true);
    try {
      await cancelAppointment(cancelingAppt.id, cancelReason);
      setCancelingAppt(null);
      fetchAppointments();
    } catch (err) {
      alert(err.response?.data?.detail || 'Failed to cancel appointment.');
    } finally {
      setCancelLoading(false);
    }
  };

  const handleOpenRescheduleModal = async (appt) => {
    setReschedulingAppt(appt);
    setRescheduleDate(appt.date);
    setSelectedRescheduleSlot(null);
    setRescheduleError(null);
    fetchRescheduleAvailability(appt.doctor_id, appt.date);
  };

  const fetchRescheduleAvailability = async (docId, dateStr) => {
    setRescheduleSlotLoading(true);
    setRescheduleError(null);
    try {
      const avail = await getDoctorAvailability(docId, dateStr);
      setRescheduleSlots(avail.slots || []);
    } catch (err) {
      setRescheduleError('Failed to fetch available slots for rescheduling.');
    } finally {
      setRescheduleSlotLoading(false);
    }
  };

  const handleRescheduleDateChange = (newDate) => {
    setRescheduleDate(newDate);
    setSelectedRescheduleSlot(null);
    if (reschedulingAppt) {
      fetchRescheduleAvailability(reschedulingAppt.doctor_id, newDate);
    }
  };

  const handleConfirmReschedule = async () => {
    if (!reschedulingAppt || !selectedRescheduleSlot) return;
    setRescheduleLoading(true);
    setRescheduleError(null);
    try {
      await rescheduleAppointment(
        reschedulingAppt.id,
        rescheduleDate,
        selectedRescheduleSlot.start_time,
        selectedRescheduleSlot.end_time
      );
      setReschedulingAppt(null);
      fetchAppointments();
    } catch (err) {
      setRescheduleError(err.response?.data?.detail || 'Failed to reschedule appointment.');
    } finally {
      setRescheduleLoading(false);
    }
  };

  const filteredAppointments = appointments.filter((appt) => {
    if (activeTab === 'UPCOMING') return appt.status === 'CONFIRMED' || appt.status === 'CHECKED_IN';
    if (activeTab === 'COMPLETED') return appt.status === 'COMPLETED';
    if (activeTab === 'CANCELLED') return appt.status === 'CANCELLED';
    return true;
  });

  return (
    <div className="space-y-6 py-2">
      {/* Header */}
      <div className="bg-white p-6 rounded-3xl border border-slate-200 shadow-sm space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-100 pb-3">
          <div>
            <h1 className="text-2xl font-black text-slate-900 flex items-center gap-2">
              <Calendar className="w-6 h-6 text-sky-700" />
              My OPD Appointments
            </h1>
            <p className="text-xs text-slate-500 font-medium">
              Manage your reserved doctor slots, check-in status, and confirmation tickets
            </p>
          </div>

          <button
            onClick={fetchAppointments}
            className="px-3.5 py-1.5 bg-sky-50 text-sky-700 hover:bg-sky-100 rounded-xl text-xs font-bold transition flex items-center gap-1.5"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
            <span>Refresh List</span>
          </button>
        </div>

        {/* Ticket Lookup Box */}
        <div className="bg-slate-50 p-4 rounded-2xl border border-slate-200 space-y-2">
          <label className="block text-xs font-bold text-slate-700 uppercase flex items-center gap-1">
            <Search className="w-3.5 h-3.5 text-sky-600" />
            Quick Confirmation Ticket Lookup
          </label>
          <form onSubmit={handleLookupSubmit} className="flex gap-2">
            <input
              type="text"
              value={codeQuery}
              onChange={(e) => setCodeQuery(e.target.value)}
              placeholder="Enter Code (e.g. JS-2026-X8F92K)..."
              className="flex-1 px-3 py-2 bg-white border border-slate-300 rounded-xl text-xs font-mono font-bold outline-none focus:ring-2 focus:ring-sky-500"
            />
            <button
              type="submit"
              disabled={lookupLoading}
              className="px-4 py-2 bg-sky-700 hover:bg-sky-800 text-white rounded-xl text-xs font-bold transition"
            >
              {lookupLoading ? 'Searching...' : 'Lookup Ticket'}
            </button>
          </form>

          {lookupError && (
            <p className="text-xs text-rose-700 font-semibold pt-1">{lookupError}</p>
          )}

          {lookupResult && (
            <div className="mt-3 bg-white p-4 rounded-xl border-2 border-emerald-400 space-y-2 text-xs">
              <div className="flex items-center justify-between">
                <span className="font-mono font-black text-sm text-sky-900">
                  {lookupResult.confirmation_code}
                </span>
                <span className="bg-emerald-100 text-emerald-900 text-[10px] font-black px-2 py-0.5 rounded uppercase">
                  {lookupResult.status}
                </span>
              </div>
              <p className="font-bold text-slate-800">
                Dr. {lookupResult.doctor_name} ({lookupResult.department_name})
              </p>
              <p className="text-slate-600">
                Date: <strong>{lookupResult.date}</strong> at <strong>{lookupResult.start_time} - {lookupResult.end_time}</strong>
              </p>
              <p className="text-slate-500 text-[11px]">Patient: {lookupResult.patient_name} ({lookupResult.patient_phone})</p>
              <button
                onClick={() => navigate('/confirmation', { state: { appointment: lookupResult } })}
                className="mt-1 px-3 py-1.5 bg-emerald-600 text-white rounded-lg text-[11px] font-bold inline-flex items-center gap-1"
              >
                Open Ticket View →
              </button>
            </div>
          )}
        </div>
      </div>

      {/* Appointments List for All Patient Sessions */}
      <div className="space-y-4">
          {/* Tabs */}
          <div className="flex items-center gap-2 border-b border-slate-200 pb-2">
            {['ALL', 'UPCOMING', 'COMPLETED', 'CANCELLED'].map((tab) => (
              <button
                key={tab}
                onClick={() => setActiveTab(tab)}
                className={`px-4 py-2 rounded-xl text-xs font-extrabold transition ${
                  activeTab === tab
                    ? 'bg-sky-800 text-white shadow-sm'
                    : 'bg-white text-slate-600 hover:bg-slate-100 border border-slate-200'
                }`}
              >
                {tab}
              </button>
            ))}
          </div>

          {loading ? (
            <div className="bg-white p-12 rounded-3xl border border-slate-200 text-center space-y-2">
              <RefreshCw className="w-6 h-6 text-sky-600 animate-spin mx-auto" />
              <p className="text-xs font-bold text-slate-500">Loading Your Appointments...</p>
            </div>
          ) : error ? (
            <div className="bg-rose-50 border border-rose-200 p-6 rounded-3xl text-rose-900 text-xs font-bold">
              {error}
            </div>
          ) : filteredAppointments.length === 0 ? (
            <div className="bg-white p-8 rounded-3xl border border-slate-200 text-center space-y-2 text-xs font-semibold text-slate-500">
              No appointments found in this category.
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {filteredAppointments.map((appt) => {
                const isConfirmed = appt.status === 'CONFIRMED' || appt.status === 'CHECKED_IN';
                const isCancelled = appt.status === 'CANCELLED';

                return (
                  <div
                    key={appt.id}
                    className="bg-white p-5 rounded-3xl border border-slate-200 shadow-sm space-y-4 flex flex-col justify-between"
                  >
                    <div className="space-y-2">
                      <div className="flex items-center justify-between gap-1 flex-wrap">
                        <div className="flex items-center gap-1.5">
                          <span className="font-mono font-black text-xs text-sky-800 bg-sky-50 px-2.5 py-1 rounded-lg border border-sky-200">
                            {appt.confirmation_code}
                          </span>
                          {appt.queue_token && (
                            <span className="font-mono font-black text-xs text-purple-900 bg-purple-100 px-2.5 py-1 rounded-lg border border-purple-300">
                              {appt.queue_token}
                            </span>
                          )}
                        </div>
                        <div className="flex items-center gap-1">
                          {appt.visit_status && appt.visit_status !== 'NOT_CHECKED_IN' && (
                            <span className="text-[10px] font-black px-2 py-0.5 rounded uppercase bg-indigo-100 text-indigo-900 border border-indigo-200">
                              {appt.visit_status}
                            </span>
                          )}
                          <span className={`text-[10px] font-black px-2.5 py-0.5 rounded-full uppercase ${
                            isConfirmed
                              ? 'bg-emerald-100 text-emerald-900'
                              : isCancelled
                              ? 'bg-rose-100 text-rose-900'
                              : 'bg-slate-100 text-slate-800'
                          }`}>
                            {appt.status}
                          </span>
                        </div>
                      </div>

                      <h3 className="font-black text-slate-900 text-base leading-tight">
                        Dr. {appt.doctor_name || 'OPD Doctor'}
                      </h3>
                      <p className="text-xs font-bold text-sky-700">{appt.department_name}</p>

                      <p className="text-xs text-slate-500 font-medium flex items-center gap-1.5">
                        <MapPin className="w-3.5 h-3.5 text-slate-400" />
                        <span>{appt.facility_name}</span>
                      </p>

                      <div className="grid grid-cols-2 gap-2 text-xs pt-1">
                        <div className="bg-slate-50 p-2 rounded-xl border border-slate-100">
                          <span className="text-[10px] text-slate-400 uppercase font-bold">Date</span>
                          <p className="font-extrabold text-slate-800">{appt.date}</p>
                        </div>
                        <div className="bg-slate-50 p-2 rounded-xl border border-slate-100">
                          <span className="text-[10px] text-slate-400 uppercase font-bold">Time Slot</span>
                          <p className="font-extrabold text-slate-800">{appt.start_time} - {appt.end_time}</p>
                        </div>
                      </div>
                    </div>

                    <div className="pt-3 border-t border-slate-100 flex items-center justify-between gap-2 flex-wrap">
                      <div className="flex items-center gap-1">
                        <button
                          onClick={() => navigate('/confirmation', { state: { appointment: appt } })}
                          className="px-3 py-1.5 bg-slate-100 hover:bg-slate-200 text-slate-800 rounded-xl text-xs font-bold transition flex items-center gap-1"
                        >
                          <FileText className="w-3.5 h-3.5 text-sky-600" />
                          <span>Ticket</span>
                        </button>

                        {isConfirmed && (!appt.queue_token || appt.visit_status === 'NOT_CHECKED_IN') && (
                          <button
                            onClick={() => handleCheckIn(appt.id)}
                            className="px-3 py-1.5 bg-emerald-600 hover:bg-emerald-700 text-white rounded-xl text-xs font-black transition flex items-center gap-1 shadow-sm"
                          >
                            <CheckCircle className="w-3.5 h-3.5" />
                            <span>Check In</span>
                          </button>
                        )}
                      </div>

                      {isConfirmed && (
                        <div className="flex items-center gap-1">
                          <button
                            onClick={() => handleOpenRescheduleModal(appt)}
                            className="px-3 py-1.5 bg-amber-50 hover:bg-amber-100 text-amber-900 border border-amber-300 rounded-xl text-xs font-bold transition flex items-center gap-1"
                          >
                            <RotateCw className="w-3.5 h-3.5 text-amber-700" />
                            <span>Reschedule</span>
                          </button>

                          <button
                            onClick={() => handleOpenCancelModal(appt)}
                            className="px-3 py-1.5 bg-rose-50 hover:bg-rose-100 text-rose-800 border border-rose-300 rounded-xl text-xs font-bold transition flex items-center gap-1"
                          >
                            <XCircle className="w-3.5 h-3.5 text-rose-600" />
                            <span>Cancel</span>
                          </button>
                        </div>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>

      {/* Cancellation Modal */}
      {cancelingAppt && (
        <div className="fixed inset-0 bg-slate-900/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-white p-6 rounded-3xl border border-slate-200 max-w-md w-full space-y-4 shadow-xl">
            <h3 className="text-lg font-black text-slate-900 flex items-center gap-2">
              <XCircle className="w-5 h-5 text-rose-600" />
              Cancel Appointment
            </h3>
            <p className="text-xs text-slate-600">
              Are you sure you want to cancel appointment <strong>{cancelingAppt.confirmation_code}</strong> for Dr. {cancelingAppt.doctor_name}?
            </p>

            <div>
              <label className="block text-xs font-bold text-slate-700 uppercase mb-1">
                Reason for Cancellation
              </label>
              <textarea
                value={cancelReason}
                onChange={(e) => setCancelReason(e.target.value)}
                className="w-full p-3 bg-slate-50 border border-slate-300 rounded-xl text-xs font-medium outline-none"
                rows={3}
              />
            </div>

            <div className="flex items-center justify-end gap-2 pt-2">
              <button
                onClick={() => setCancelingAppt(null)}
                className="px-4 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-xl text-xs font-bold"
              >
                Keep Booking
              </button>
              <button
                onClick={handleConfirmCancel}
                disabled={cancelLoading}
                className="px-4 py-2 bg-rose-600 hover:bg-rose-700 text-white rounded-xl text-xs font-bold"
              >
                {cancelLoading ? 'Canceling...' : 'Confirm Cancellation'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Reschedule Modal */}
      {reschedulingAppt && (
        <div className="fixed inset-0 bg-slate-900/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-white p-6 rounded-3xl border border-slate-200 max-w-lg w-full space-y-4 shadow-xl max-h-[90vh] overflow-y-auto">
            <h3 className="text-lg font-black text-slate-900 flex items-center gap-2">
              <RotateCw className="w-5 h-5 text-amber-600" />
              Reschedule OPD Slot
            </h3>
            <p className="text-xs text-slate-600">
              Rescheduling for Dr. <strong>{reschedulingAppt.doctor_name}</strong> (Code: {reschedulingAppt.confirmation_code})
            </p>

            {rescheduleError && (
              <p className="p-3 bg-rose-50 text-rose-800 rounded-xl text-xs font-bold">{rescheduleError}</p>
            )}

            <div>
              <label className="block text-xs font-bold text-slate-700 uppercase mb-1">
                Select New Date
              </label>
              <input
                type="date"
                value={rescheduleDate}
                onChange={(e) => handleRescheduleDateChange(e.target.value)}
                className="w-full px-3 py-2 bg-slate-50 border border-slate-300 rounded-xl text-xs font-bold outline-none"
              />
            </div>

            <div>
              <label className="block text-xs font-bold text-slate-700 uppercase mb-2">
                Available Time Slots on {rescheduleDate}
              </label>

              {rescheduleSlotLoading ? (
                <div className="py-6 text-center text-xs text-slate-500 font-bold">
                  Loading slots...
                </div>
              ) : rescheduleSlots.length === 0 ? (
                <div className="py-4 text-center text-xs text-amber-800 bg-amber-50 rounded-xl">
                  No slots available on this date.
                </div>
              ) : (
                <div className="grid grid-cols-3 gap-2">
                  {rescheduleSlots.map((slot, idx) => {
                    const isAvail = slot.status === 'AVAILABLE';
                    const isSelected = selectedRescheduleSlot?.start_time === slot.start_time;

                    return (
                      <button
                        key={idx}
                        disabled={!isAvail}
                        onClick={() => setSelectedRescheduleSlot(slot)}
                        className={`p-2 rounded-xl text-xs border text-center transition ${
                          isSelected
                            ? 'bg-amber-400 text-slate-950 font-black border-amber-500'
                            : isAvail
                            ? 'bg-emerald-50 text-emerald-950 border-emerald-300 hover:bg-emerald-100 font-semibold'
                            : 'bg-slate-100 text-slate-400 cursor-not-allowed line-through'
                        }`}
                      >
                        {slot.start_time}
                      </button>
                    );
                  })}
                </div>
              )}
            </div>

            <div className="flex items-center justify-end gap-2 pt-2 border-t border-slate-100">
              <button
                onClick={() => setReschedulingAppt(null)}
                className="px-4 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-xl text-xs font-bold"
              >
                Close
              </button>
              <button
                onClick={handleConfirmReschedule}
                disabled={rescheduleLoading || !selectedRescheduleSlot}
                className="px-4 py-2 bg-amber-400 hover:bg-amber-300 text-slate-950 rounded-xl text-xs font-black transition"
              >
                {rescheduleLoading ? 'Rescheduling...' : 'Confirm Reschedule'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
