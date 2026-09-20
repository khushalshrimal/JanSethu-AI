import React, { useState, useEffect } from 'react';
import { apiClient } from '../../services/api';

export default function AdminTelephony() {
  const [sessions, setSessions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [outboundPhone, setOutboundPhone] = useState('');
  const [outboundSuccess, setOutboundSuccess] = useState(null);

  const fetchSessions = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await apiClient.get('/telephony/sessions');
      setSessions(response.data);
    } catch (err) {
      console.error("Failed to load telephony sessions:", err);
      setError("Failed to fetch telephony session logs. Admin access required.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSessions();
  }, []);

  const handleSimulateOutbound = async (e) => {
    e.preventDefault();
    if (!outboundPhone) return;
    try {
      setOutboundSuccess(null);
      const response = await apiClient.post('/telephony/webhooks/outbound', {
        to_number: outboundPhone
      });
      setOutboundSuccess(`Outbound call simulated to ${response.data.to_number} (Provider Call ID: ${response.data.provider_call_id})`);
      setOutboundPhone('');
      fetchSessions();
    } catch (err) {
      alert("Failed to initiate outbound call: " + (err.response?.data?.detail || err.message));
    }
  };

  if (loading) {
    return (
      <div className="py-6 text-center text-gray-500 text-sm">
        <div className="inline-block animate-spin rounded-full h-6 w-6 border-2 border-slate-700 border-t-transparent mb-2"></div>
        <p>Loading Telephony Operational Data...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-4 bg-red-50 border border-red-200 text-red-700 rounded-xl text-sm">
        {error}
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {outboundSuccess && (
        <div className="bg-emerald-50 border border-emerald-200 text-emerald-800 p-3 rounded-xl text-xs font-semibold">
          ✅ {outboundSuccess}
        </div>
      )}

      {/* Outbound Simulation Control */}
      <div className="bg-white p-5 rounded-2xl border border-gray-100 shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h3 className="text-sm font-bold text-gray-900">📞 Initiate Outbound Call Session (Simulated)</h3>
          <p className="text-xs text-gray-500">Triggers a provider-neutral outbound call session simulation for appointment reminders.</p>
        </div>
        <form onSubmit={handleSimulateOutbound} className="flex gap-2 text-xs">
          <input
            type="text"
            value={outboundPhone}
            onChange={(e) => setOutboundPhone(e.target.value)}
            placeholder="Recipient Phone (+91-9876543210)"
            className="px-3 py-2 border rounded-xl w-64 focus:outline-none focus:ring-2 focus:ring-slate-800"
            required
          />
          <button
            type="submit"
            className="px-4 py-2 bg-slate-900 hover:bg-slate-800 text-white font-bold rounded-xl transition whitespace-nowrap"
          >
            Start Outbound Call
          </button>
        </form>
      </div>

      {/* Call Session Table */}
      <div className="bg-white p-6 rounded-2xl shadow-sm border border-gray-100">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-bold text-gray-900">Active & Recent Call Sessions</h2>
          <button onClick={fetchSessions} className="text-xs font-semibold px-3 py-1.5 bg-slate-100 hover:bg-slate-200 text-slate-800 rounded-lg transition">
            🔄 Refresh Sessions
          </button>
        </div>

        {sessions.length === 0 ? (
          <p className="text-gray-500 text-xs py-4">No call sessions recorded yet.</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-xs text-left border-collapse">
              <thead>
                <tr className="border-b border-gray-200 text-gray-500 uppercase font-semibold">
                  <th className="py-2.5 px-3">Session ID</th>
                  <th className="py-2.5 px-3">Caller (Masked)</th>
                  <th className="py-2.5 px-3">Provider</th>
                  <th className="py-2.5 px-3">Provider Call ID</th>
                  <th className="py-2.5 px-3">Current State</th>
                  <th className="py-2.5 px-3">Status</th>
                  <th className="py-2.5 px-3">Language</th>
                  <th className="py-2.5 px-3">Started At</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {sessions.map((s) => (
                  <tr key={s.id} className="hover:bg-gray-50">
                    <td className="py-2.5 px-3 font-mono font-bold text-gray-800">#{s.id}</td>
                    <td className="py-2.5 px-3 font-medium text-gray-900">{s.caller_phone_masked}</td>
                    <td className="py-2.5 px-3">
                      <span className="bg-slate-100 text-slate-800 font-semibold px-2 py-0.5 rounded text-[10px] uppercase">
                        {s.provider}
                      </span>
                    </td>
                    <td className="py-2.5 px-3 font-mono text-gray-600">{s.provider_call_id || 'N/A'}</td>
                    <td className="py-2.5 px-3">
                      <span className="bg-amber-100 text-amber-800 font-bold px-2 py-0.5 rounded text-[10px]">
                        {s.current_state}
                      </span>
                    </td>
                    <td className="py-2.5 px-3">
                      <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                        s.is_active ? 'bg-emerald-100 text-emerald-800' : 'bg-gray-100 text-gray-600'
                      }`}>
                        {s.is_active ? 'ACTIVE' : 'ENDED'}
                      </span>
                    </td>
                    <td className="py-2.5 px-3 font-bold text-gray-700">{s.language}</td>
                    <td className="py-2.5 px-3 text-gray-500">
                      {s.started_at ? new Date(s.started_at).toLocaleTimeString() : 'N/A'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
