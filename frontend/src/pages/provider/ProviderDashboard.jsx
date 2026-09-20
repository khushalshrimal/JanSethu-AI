import React, { useState, useEffect } from 'react';
import { providerService } from '../../services/providerService';
import { startConsultation, completeConsultation, markNoShow } from '../../services/appointmentService';

export default function ProviderDashboard() {
  const [metrics, setMetrics] = useState(null);
  const [appointments, setAppointments] = useState([]);
  const [schedule, setSchedule] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [actionSuccess, setActionSuccess] = useState(null);

  // Leave Form State
  const [leaveDate, setLeaveDate] = useState('');
  const [leaveReason, setLeaveReason] = useState('Doctor Leave / Emergency Duty');

  const fetchData = async () => {
    try {
      setLoading(true);
      setError(null);
      const [dashData, aptData, schedData] = await Promise.all([
        providerService.getDashboard(),
        providerService.getAppointments(),
        providerService.getSchedule()
      ]);
      setMetrics(dashData);
      setAppointments(aptData);
      setSchedule(schedData);
    } catch (err) {
      console.error("Error loading provider dashboard:", err);
      setError("Failed to load OPD queue data. Ensure you are logged in with a Provider or Admin account.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleStatusUpdate = async (aptId, newStatus) => {
    try {
      setActionSuccess(null);
      await providerService.updateAppointmentStatus(aptId, newStatus);
      setActionSuccess(`Appointment #${aptId} status updated to ${newStatus}`);
      fetchData();
    } catch (err) {
      alert("Failed to update status: " + (err.response?.data?.detail?.message || err.message));
    }
  };

  const handleStartConsultation = async (aptId) => {
    try {
      setActionSuccess(null);
      await startConsultation(aptId);
      setActionSuccess(`Consultation started for Appointment #${aptId}`);
      fetchData();
    } catch (err) {
      alert("Failed to start consultation: " + (err.response?.data?.detail || err.message));
    }
  };

  const handleCompleteConsultation = async (aptId) => {
    try {
      setActionSuccess(null);
      await completeConsultation(aptId);
      setActionSuccess(`Consultation completed for Appointment #${aptId}`);
      fetchData();
    } catch (err) {
      alert("Failed to complete consultation: " + (err.response?.data?.detail || err.message));
    }
  };

  const handleMarkNoShow = async (aptId) => {
    try {
      setActionSuccess(null);
      await markNoShow(aptId);
      setActionSuccess(`Appointment #${aptId} marked as No-Show`);
      fetchData();
    } catch (err) {
      alert("Failed to mark No-Show: " + (err.response?.data?.detail || err.message));
    }
  };

  const handleLeaveSubmit = async (e) => {
    e.preventDefault();
    if (!leaveDate) return;
    try {
      setActionSuccess(null);
      await providerService.createLeaveException({
        date: leaveDate,
        start_time: "09:00:00",
        end_time: "17:00:00",
        reason: leaveReason
      });
      setActionSuccess(`Leave exception submitted for ${leaveDate}. Dynamic slot availability updated across PWA and Phone engine.`);
      setLeaveDate('');
      fetchData();
    } catch (err) {
      alert("Failed to create schedule exception: " + (err.response?.data?.detail || err.message));
    }
  };

  if (loading) {
    return (
      <div className="max-w-7xl mx-auto px-4 py-8 text-center text-gray-600">
        <div className="inline-block animate-spin rounded-full h-8 w-8 border-4 border-emerald-600 border-t-transparent mb-4"></div>
        <p>Loading Provider OPD Console...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="max-w-7xl mx-auto px-4 py-8">
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-xl">
          {error}
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-4 py-8">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between mb-8 bg-gradient-to-r from-emerald-800 to-teal-900 text-white p-6 rounded-2xl shadow-lg">
        <div>
          <span className="text-xs font-bold uppercase tracking-wider bg-emerald-700 px-3 py-1 rounded-full">Healthcare Provider Console</span>
          <h1 className="text-2xl font-extrabold mt-2">{metrics?.doctor_name || 'OPD Management Console'}</h1>
          <p className="text-emerald-200 text-sm">{metrics?.facility_name} • {metrics?.department_name || 'General OPD'}</p>
        </div>
        <div className="mt-4 md:mt-0">
          <button onClick={fetchData} className="px-4 py-2 bg-white/10 hover:bg-white/20 text-white text-sm font-semibold rounded-xl backdrop-blur transition">
            🔄 Refresh OPD Queue
          </button>
        </div>
      </div>

      {actionSuccess && (
        <div className="mb-6 bg-emerald-50 border border-emerald-200 text-emerald-800 px-4 py-3 rounded-xl text-sm font-medium">
          ✅ {actionSuccess}
        </div>
      )}

      {/* Real Metrics Cards */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-4 mb-8">
        <div className="bg-white p-5 rounded-2xl shadow-sm border border-gray-100">
          <div className="text-gray-500 text-xs font-semibold uppercase">Today's Total</div>
          <div className="text-2xl font-black text-gray-900 mt-1">{metrics?.today_total || 0}</div>
        </div>
        <div className="bg-white p-5 rounded-2xl shadow-sm border border-amber-100 bg-amber-50/30">
          <div className="text-amber-700 text-xs font-semibold uppercase">Waiting Queue</div>
          <div className="text-2xl font-black text-amber-700 mt-1">{metrics?.waiting_count || 0}</div>
        </div>
        <div className="bg-white p-5 rounded-2xl shadow-sm border border-blue-100 bg-blue-50/30">
          <div className="text-blue-700 text-xs font-semibold uppercase">In Consultation</div>
          <div className="text-2xl font-black text-blue-700 mt-1">{metrics?.in_progress_count || 0}</div>
        </div>
        <div className="bg-white p-5 rounded-2xl shadow-sm border border-emerald-100 bg-emerald-50/30">
          <div className="text-emerald-700 text-xs font-semibold uppercase">Completed</div>
          <div className="text-2xl font-black text-emerald-700 mt-1">{metrics?.completed_count || 0}</div>
        </div>
        <div className="bg-white p-5 rounded-2xl shadow-sm border border-red-100 bg-red-50/30">
          <div className="text-red-700 text-xs font-semibold uppercase">Cancelled / No-Show</div>
          <div className="text-2xl font-black text-red-700 mt-1">{(metrics?.cancelled_count || 0) + (metrics?.no_show_count || 0)}</div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Patient Queue Management */}
        <div className="lg:col-span-2 space-y-6">
          <div className="bg-white p-6 rounded-2xl shadow-sm border border-gray-100">
            <h2 className="text-lg font-bold text-gray-900 mb-4 flex items-center gap-2">
              📋 Live OPD Patient Queue
            </h2>

            {appointments.length === 0 ? (
              <p className="text-gray-500 text-sm py-4">No appointments scheduled for today.</p>
            ) : (
              <div className="space-y-3">
                {appointments.map((apt) => (
                  <div key={apt.id} className="p-4 border border-gray-100 rounded-xl hover:border-gray-200 transition bg-gray-50/50 flex flex-col md:flex-row md:items-center justify-between gap-4">
                    <div>
                      <div className="flex items-center gap-2 flex-wrap">
                        <span className="text-xs font-bold px-2 py-0.5 rounded bg-gray-200 text-gray-800">#{apt.id}</span>
                        {apt.queue_token && (
                          <span className="text-xs font-mono font-black px-2 py-0.5 rounded bg-purple-100 text-purple-900 border border-purple-300">
                            Token: {apt.queue_token}
                          </span>
                        )}
                        <span className="text-sm font-semibold text-gray-900">{apt.patient?.name || 'Patient'}</span>
                        <span className="text-xs text-gray-500">({apt.patient?.phone || 'No Phone'})</span>
                        <span className="text-xs font-mono px-2 py-0.5 bg-emerald-100 text-emerald-800 rounded">{apt.booking_channel}</span>
                      </div>
                      <div className="text-xs text-gray-600 mt-1">
                        ⏰ {apt.start_time} - {apt.end_time} • {apt.reason_for_visit || 'OPD Visit'}
                      </div>
                      <div className="text-xs font-medium text-emerald-700 mt-1 flex items-center gap-2">
                        <span>Confirmation: <code className="bg-emerald-50 px-1 py-0.5 rounded">{apt.confirmation_code}</code></span>
                        {apt.visit_status && (
                          <span className="text-[10px] font-extrabold uppercase px-2 py-0.5 bg-indigo-100 text-indigo-900 rounded border border-indigo-200">
                            Visit: {apt.visit_status}
                          </span>
                        )}
                      </div>
                    </div>

                    <div className="flex items-center gap-2 flex-wrap">
                      <span className={`text-xs font-bold px-2.5 py-1 rounded-full ${
                        apt.status === 'IN_PROGRESS' ? 'bg-blue-100 text-blue-800 border border-blue-200' :
                        apt.status === 'COMPLETED' ? 'bg-emerald-100 text-emerald-800' :
                        apt.status === 'CANCELLED' ? 'bg-red-100 text-red-800' :
                        'bg-amber-100 text-amber-800'
                      }`}>
                        {apt.status}
                      </span>

                      {apt.status !== 'COMPLETED' && apt.status !== 'CANCELLED' && (
                        <div className="flex gap-1">
                          {apt.status !== 'IN_PROGRESS' && (
                            <button
                              onClick={() => handleStartConsultation(apt.id)}
                              className="text-xs font-semibold px-2.5 py-1.5 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition"
                            >
                              ▶ Start Consultation
                            </button>
                          )}
                          <button
                            onClick={() => handleCompleteConsultation(apt.id)}
                            className="text-xs font-semibold px-2.5 py-1.5 bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg transition"
                          >
                            ✓ Complete
                          </button>
                          <button
                            onClick={() => handleMarkNoShow(apt.id)}
                            className="text-xs font-semibold px-2.5 py-1.5 bg-amber-600 hover:bg-amber-700 text-white rounded-lg transition"
                          >
                            No-Show
                          </button>
                        </div>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Doctor Leave Exception & Schedule Control */}
        <div className="space-y-6">
          <div className="bg-white p-6 rounded-2xl shadow-sm border border-gray-100">
            <h2 className="text-lg font-bold text-gray-900 mb-4 flex items-center gap-2">
              📅 Apply Doctor Leave / Exception
            </h2>
            <form onSubmit={handleLeaveSubmit} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-gray-700 mb-1">Leave Date</label>
                <input
                  type="date"
                  value={leaveDate}
                  onChange={(e) => setLeaveDate(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-xl text-sm focus:ring-2 focus:ring-emerald-500 focus:outline-none"
                  required
                />
              </div>
              <div>
                <label className="block text-xs font-semibold text-gray-700 mb-1">Reason</label>
                <input
                  type="text"
                  value={leaveReason}
                  onChange={(e) => setLeaveReason(e.target.value)}
                  placeholder="Reason for leave"
                  className="w-full px-3 py-2 border border-gray-300 rounded-xl text-sm focus:ring-2 focus:ring-emerald-500 focus:outline-none"
                  required
                />
              </div>
              <button
                type="submit"
                className="w-full py-2.5 bg-emerald-700 hover:bg-emerald-800 text-white text-sm font-semibold rounded-xl shadow transition"
              >
                Submit Leave Exception
              </button>
            </form>
          </div>

          <div className="bg-white p-6 rounded-2xl shadow-sm border border-gray-100">
            <h2 className="text-lg font-bold text-gray-900 mb-3">Weekly Schedule Overview</h2>
            <div className="space-y-2 text-xs">
              {schedule.length === 0 ? (
                <p className="text-gray-500">No recurring schedule registered.</p>
              ) : (
                schedule.map((s) => (
                  <div key={s.id} className="flex justify-between py-1.5 border-b border-gray-100 last:border-0">
                    <span className="font-semibold text-gray-700">
                      {['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'][s.day_of_week] || `Day ${s.day_of_week}`}
                    </span>
                    <span className="text-gray-600">{s.start_time} - {s.end_time} ({s.slot_duration_minutes}m)</span>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
