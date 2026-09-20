import React, { useState, useEffect } from 'react';
import { adminService } from '../../services/adminService';
import AdminTelephony from './AdminTelephony';

export default function AdminConsole() {
  const [activeTab, setActiveTab] = useState('overview'); // overview, facilities, doctors, audit, emergency, telephony
  const [metrics, setMetrics] = useState(null);
  const [facilities, setFacilities] = useState([]);
  const [doctors, setDoctors] = useState([]);
  const [auditLogs, setAuditLogs] = useState([]);
  const [emergencyContacts, setEmergencyContacts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [successMsg, setSuccessMsg] = useState(null);

  // New Doctor Form State
  const [newDoc, setNewDoc] = useState({
    facility_id: '',
    department_id: '',
    name: '',
    qualification: 'MBBS, MD',
    specialization: 'General Medicine',
    phone_number: '',
    consultation_type: 'OPD_IN_PERSON'
  });

  // New Facility Form State
  const [newFac, setNewFac] = useState({
    name: '',
    facility_type: 'PRIMARY_HEALTH_CENTER',
    district: 'Pune',
    block: 'Indapur',
    village: 'Indapur Village',
    pincode: '413132',
    phone_number: '+912111223344',
    latitude: 18.118,
    longitude: 74.908
  });

  // New Emergency Contact State
  const [newEmg, setNewEmg] = useState({
    name: '',
    phone_number: '',
    contact_type: 'AMBULANCE',
    priority: 1
  });

  const loadData = async () => {
    try {
      setLoading(true);
      setError(null);
      const [dash, facs, docs, logs, emg] = await Promise.all([
        adminService.getDashboard(),
        adminService.getFacilities(),
        adminService.getDoctors(),
        adminService.getAuditLogs({ limit: 50 }),
        adminService.getEmergencyContacts()
      ]);
      setMetrics(dash);
      setFacilities(facs);
      setDoctors(docs);
      setAuditLogs(logs);
      setEmergencyContacts(emg);

      if (facs.length > 0 && !newDoc.facility_id) {
        setNewDoc(prev => ({
          ...prev,
          facility_id: facs[0].id,
          department_id: facs[0].departments?.[0]?.id || 1
        }));
      }
    } catch (err) {
      console.error("Failed to load admin data:", err);
      setError("Failed to load admin console data. Ensure you have Admin role permissions.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleToggleFacility = async (facId, currentStatus) => {
    try {
      setSuccessMsg(null);
      await adminService.toggleFacilityStatus(facId, !currentStatus);
      setSuccessMsg(`Facility #${facId} status toggled successfully.`);
      loadData();
    } catch (err) {
      alert("Failed to toggle facility status: " + err.message);
    }
  };

  const handleToggleDoctor = async (docId, currentStatus) => {
    try {
      setSuccessMsg(null);
      await adminService.toggleDoctorStatus(docId, !currentStatus);
      setSuccessMsg(`Doctor #${docId} status toggled successfully.`);
      loadData();
    } catch (err) {
      alert("Failed to toggle doctor status: " + err.message);
    }
  };

  const handleCreateFacility = async (e) => {
    e.preventDefault();
    try {
      setSuccessMsg(null);
      await adminService.createFacility(newFac);
      setSuccessMsg(`Facility "${newFac.name}" onboarded successfully.`);
      setNewFac({
        name: '',
        facility_type: 'PRIMARY_HEALTH_CENTER',
        district: 'Pune',
        block: 'Indapur',
        village: 'Indapur Village',
        pincode: '413132',
        phone_number: '+912111223344',
        latitude: 18.118,
        longitude: 74.908
      });
      loadData();
    } catch (err) {
      alert("Failed to create facility: " + (err.response?.data?.detail || err.message));
    }
  };

  const handleCreateDoctor = async (e) => {
    e.preventDefault();
    try {
      setSuccessMsg(null);
      await adminService.createDoctor({
        ...newDoc,
        facility_id: parseInt(newDoc.facility_id),
        department_id: parseInt(newDoc.department_id)
      });
      setSuccessMsg(`Doctor "${newDoc.name}" onboarded with automatic 7-day recurring OPD schedule.`);
      setNewDoc(prev => ({ ...prev, name: '', phone_number: '' }));
      loadData();
    } catch (err) {
      alert("Failed to create doctor: " + (err.response?.data?.detail || err.message));
    }
  };

  const handleCreateEmergency = async (e) => {
    e.preventDefault();
    try {
      setSuccessMsg(null);
      await adminService.createEmergencyContact(newEmg);
      setSuccessMsg(`Emergency contact "${newEmg.name}" created.`);
      setNewEmg({ name: '', phone_number: '', contact_type: 'AMBULANCE', priority: 1 });
      loadData();
    } catch (err) {
      alert("Failed to create emergency contact: " + err.message);
    }
  };

  const handleDeleteEmergency = async (contactId) => {
    if (!window.confirm("Delete this emergency contact?")) return;
    try {
      await adminService.deleteEmergencyContact(contactId);
      setSuccessMsg("Emergency contact deleted.");
      loadData();
    } catch (err) {
      alert("Failed to delete contact: " + err.message);
    }
  };

  if (loading) {
    return (
      <div className="max-w-7xl mx-auto px-4 py-8 text-center text-gray-600">
        <div className="inline-block animate-spin rounded-full h-8 w-8 border-4 border-slate-700 border-t-transparent mb-4"></div>
        <p>Loading Admin Operations Console...</p>
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
      <div className="flex flex-col md:flex-row md:items-center justify-between mb-8 bg-slate-900 text-white p-6 rounded-2xl shadow-lg">
        <div>
          <span className="text-xs font-bold uppercase tracking-wider bg-slate-800 px-3 py-1 rounded-full text-slate-300">System Operations</span>
          <h1 className="text-2xl font-extrabold mt-2">JanSethu AI Admin Operations Console</h1>
          <p className="text-slate-400 text-sm">Facility Management • Doctor Onboarding • Audit Trail • Emergency Services</p>
        </div>
        <div className="mt-4 md:mt-0 flex gap-2">
          <button onClick={loadData} className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-white text-sm font-semibold rounded-xl transition">
            🔄 Refresh Console
          </button>
        </div>
      </div>

      {successMsg && (
        <div className="mb-6 bg-emerald-50 border border-emerald-200 text-emerald-800 px-4 py-3 rounded-xl text-sm font-medium">
          ✅ {successMsg}
        </div>
      )}

      {/* Navigation Tabs */}
      <div className="flex space-x-2 border-b border-gray-200 mb-8 overflow-x-auto pb-2">
        {[
          { id: 'overview', label: '📊 System Overview' },
          { id: 'facilities', label: '🏥 Facilities Management' },
          { id: 'doctors', label: '👨‍⚕️ Doctors & Schedules' },
          { id: 'telephony', label: '📞 Telephony & Sessions' },
          { id: 'audit', label: '📜 Audit Log Trail' },
          { id: 'emergency', label: '🚨 Emergency Contacts' }
        ].map(t => (
          <button
            key={t.id}
            onClick={() => setActiveTab(t.id)}
            className={`px-4 py-2.5 rounded-xl font-bold text-sm transition whitespace-nowrap ${
              activeTab === t.id
                ? 'bg-slate-900 text-white shadow-sm'
                : 'bg-white text-gray-600 hover:bg-gray-100 border border-gray-100'
            }`}
          >
            {t.label}
          </button>
        ))}
      </div>

      {/* OVERVIEW TAB */}
      {activeTab === 'overview' && (
        <div className="space-y-8">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="bg-white p-5 rounded-2xl border border-gray-100 shadow-sm">
              <div className="text-xs font-semibold text-gray-500 uppercase">Total Facilities</div>
              <div className="text-3xl font-black text-gray-900 mt-1">{metrics?.total_facilities || 0}</div>
            </div>
            <div className="bg-white p-5 rounded-2xl border border-gray-100 shadow-sm">
              <div className="text-xs font-semibold text-gray-500 uppercase">Active Doctors</div>
              <div className="text-3xl font-black text-emerald-600 mt-1">{metrics?.active_doctors || 0} / {metrics?.total_doctors || 0}</div>
            </div>
            <div className="bg-white p-5 rounded-2xl border border-gray-100 shadow-sm">
              <div className="text-xs font-semibold text-gray-500 uppercase">Today's Appointments</div>
              <div className="text-3xl font-black text-blue-600 mt-1">{metrics?.today_appointments || 0}</div>
            </div>
            <div className="bg-white p-5 rounded-2xl border border-gray-100 shadow-sm">
              <div className="text-xs font-semibold text-gray-500 uppercase">Registered Providers</div>
              <div className="text-3xl font-black text-purple-600 mt-1">{metrics?.total_providers || 0}</div>
            </div>
          </div>
        </div>
      )}

      {/* FACILITIES TAB */}
      {activeTab === 'facilities' && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          <div className="lg:col-span-2 bg-white p-6 rounded-2xl shadow-sm border border-gray-100">
            <h2 className="text-lg font-bold text-gray-900 mb-4">Healthcare Facilities</h2>
            <div className="space-y-3">
              {facilities.map(fac => (
                <div key={fac.id} className="p-4 border border-gray-100 rounded-xl flex items-center justify-between gap-4">
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="font-bold text-gray-900">{fac.name}</span>
                      <span className="text-xs bg-slate-100 text-slate-800 px-2 py-0.5 rounded">{fac.facility_type}</span>
                    </div>
                    <div className="text-xs text-gray-500 mt-1">
                      {fac.village}, {fac.block}, {fac.district} • Pincode: {fac.pincode}
                    </div>
                  </div>
                  <button
                    onClick={() => handleToggleFacility(fac.id, fac.is_active)}
                    className={`text-xs font-bold px-3 py-1.5 rounded-lg transition ${
                      fac.is_active ? 'bg-emerald-100 text-emerald-800 hover:bg-emerald-200' : 'bg-red-100 text-red-800 hover:bg-red-200'
                    }`}
                  >
                    {fac.is_active ? 'Active (Click to Deactivate)' : 'Inactive (Click to Activate)'}
                  </button>
                </div>
              ))}
            </div>
          </div>

          <div className="bg-white p-6 rounded-2xl shadow-sm border border-gray-100">
            <h2 className="text-lg font-bold text-gray-900 mb-4">Onboard New Facility</h2>
            <form onSubmit={handleCreateFacility} className="space-y-3 text-xs">
              <div>
                <label className="font-semibold text-gray-700">Facility Name</label>
                <input
                  type="text"
                  value={newFac.name}
                  onChange={(e) => setNewFac({ ...newFac, name: e.target.value })}
                  placeholder="e.g. Sub-District Hospital Indapur"
                  className="w-full px-3 py-2 border rounded-lg mt-1"
                  required
                />
              </div>
              <div>
                <label className="font-semibold text-gray-700">Facility Type</label>
                <select
                  value={newFac.facility_type}
                  onChange={(e) => setNewFac({ ...newFac, facility_type: e.target.value })}
                  className="w-full px-3 py-2 border rounded-lg mt-1"
                >
                  <option value="PRIMARY_HEALTH_CENTER">Primary Health Center (PHC)</option>
                  <option value="COMMUNITY_HEALTH_CENTER">Community Health Center (CHC)</option>
                  <option value="SUB_CENTER">Sub-Center</option>
                  <option value="DISTRICT_HOSPITAL">District Hospital</option>
                </select>
              </div>
              <div>
                <label className="font-semibold text-gray-700">District</label>
                <input
                  type="text"
                  value={newFac.district}
                  onChange={(e) => setNewFac({ ...newFac, district: e.target.value })}
                  className="w-full px-3 py-2 border rounded-lg mt-1"
                  required
                />
              </div>
              <div>
                <label className="font-semibold text-gray-700">Village / Town</label>
                <input
                  type="text"
                  value={newFac.village}
                  onChange={(e) => setNewFac({ ...newFac, village: e.target.value })}
                  className="w-full px-3 py-2 border rounded-lg mt-1"
                  required
                />
              </div>
              <div>
                <label className="font-semibold text-gray-700">Pincode</label>
                <input
                  type="text"
                  value={newFac.pincode}
                  onChange={(e) => setNewFac({ ...newFac, pincode: e.target.value })}
                  className="w-full px-3 py-2 border rounded-lg mt-1"
                  required
                />
              </div>
              <button type="submit" className="w-full py-2.5 bg-slate-900 text-white font-bold rounded-xl shadow mt-2">
                Onboard Facility
              </button>
            </form>
          </div>
        </div>
      )}

      {/* DOCTORS TAB */}
      {activeTab === 'doctors' && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          <div className="lg:col-span-2 bg-white p-6 rounded-2xl shadow-sm border border-gray-100">
            <h2 className="text-lg font-bold text-gray-900 mb-4">Doctor Registry</h2>
            <div className="space-y-3">
              {doctors.map(doc => (
                <div key={doc.id} className="p-4 border border-gray-100 rounded-xl flex items-center justify-between gap-4">
                  <div>
                    <div className="font-bold text-gray-900">{doc.name}</div>
                    <div className="text-xs text-gray-500 mt-0.5">
                      {doc.specialization} ({doc.qualification}) • Phone: {doc.phone_number || 'N/A'}
                    </div>
                  </div>
                  <button
                    onClick={() => handleToggleDoctor(doc.id, doc.is_active)}
                    className={`text-xs font-bold px-3 py-1.5 rounded-lg transition ${
                      doc.is_active ? 'bg-emerald-100 text-emerald-800 hover:bg-emerald-200' : 'bg-red-100 text-red-800 hover:bg-red-200'
                    }`}
                  >
                    {doc.is_active ? 'Active' : 'Inactive'}
                  </button>
                </div>
              ))}
            </div>
          </div>

          <div className="bg-white p-6 rounded-2xl shadow-sm border border-gray-100">
            <h2 className="text-lg font-bold text-gray-900 mb-4">Onboard Doctor Profile</h2>
            <form onSubmit={handleCreateDoctor} className="space-y-3 text-xs">
              <div>
                <label className="font-semibold text-gray-700">Assigned Facility</label>
                <select
                  value={newDoc.facility_id}
                  onChange={(e) => {
                    const fid = parseInt(e.target.value);
                    const selectedFac = facilities.find(f => f.id === fid);
                    setNewDoc({
                      ...newDoc,
                      facility_id: fid,
                      department_id: selectedFac?.departments?.[0]?.id || 1
                    });
                  }}
                  className="w-full px-3 py-2 border rounded-lg mt-1"
                >
                  {facilities.map(f => (
                    <option key={f.id} value={f.id}>{f.name}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="font-semibold text-gray-700">Doctor Full Name</label>
                <input
                  type="text"
                  value={newDoc.name}
                  onChange={(e) => setNewDoc({ ...newDoc, name: e.target.value })}
                  placeholder="e.g. Dr. Sunita Deshmukh"
                  className="w-full px-3 py-2 border rounded-lg mt-1"
                  required
                />
              </div>
              <div>
                <label className="font-semibold text-gray-700">Specialization</label>
                <input
                  type="text"
                  value={newDoc.specialization}
                  onChange={(e) => setNewDoc({ ...newDoc, specialization: e.target.value })}
                  className="w-full px-3 py-2 border rounded-lg mt-1"
                  required
                />
              </div>
              <div>
                <label className="font-semibold text-gray-700">Phone Number</label>
                <input
                  type="text"
                  value={newDoc.phone_number}
                  onChange={(e) => setNewDoc({ ...newDoc, phone_number: e.target.value })}
                  placeholder="+91-9876543210"
                  className="w-full px-3 py-2 border rounded-lg mt-1"
                />
              </div>
              <button type="submit" className="w-full py-2.5 bg-slate-900 text-white font-bold rounded-xl shadow mt-2">
                Create Doctor Profile
              </button>
            </form>
          </div>
        </div>
      )}

      {/* AUDIT LOG TAB */}
      {activeTab === 'audit' && (
        <div className="bg-white p-6 rounded-2xl shadow-sm border border-gray-100">
          <h2 className="text-lg font-bold text-gray-900 mb-4">System Operational Audit Log</h2>
          <div className="overflow-x-auto">
            <table className="w-full text-xs text-left border-collapse">
              <thead>
                <tr className="border-b border-gray-200 text-gray-500 uppercase font-semibold">
                  <th className="py-2.5 px-3">ID</th>
                  <th className="py-2.5 px-3">Action</th>
                  <th className="py-2.5 px-3">Entity</th>
                  <th className="py-2.5 px-3">Entity ID</th>
                  <th className="py-2.5 px-3">User Email</th>
                  <th className="py-2.5 px-3">Timestamp</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {auditLogs.map(l => (
                  <tr key={l.id} className="hover:bg-gray-50">
                    <td className="py-2 px-3 font-mono font-bold text-gray-700">#{l.id}</td>
                    <td className="py-2 px-3">
                      <span className="bg-slate-100 text-slate-900 font-semibold px-2 py-0.5 rounded">{l.action}</span>
                    </td>
                    <td className="py-2 px-3 text-gray-600">{l.entity_type}</td>
                    <td className="py-2 px-3 text-gray-600">{l.entity_id || 'N/A'}</td>
                    <td className="py-2 px-3 text-gray-800 font-medium">{l.user_email || 'System'}</td>
                    <td className="py-2 px-3 text-gray-500">{new Date(l.created_at).toLocaleString()}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* EMERGENCY CONTACTS TAB */}
      {activeTab === 'emergency' && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          <div className="lg:col-span-2 bg-white p-6 rounded-2xl shadow-sm border border-gray-100">
            <h2 className="text-lg font-bold text-gray-900 mb-4">Emergency Service Directory</h2>
            <div className="space-y-3">
              {emergencyContacts.map(c => (
                <div key={c.id} className="p-4 border border-gray-100 rounded-xl flex items-center justify-between gap-4">
                  <div>
                    <div className="font-bold text-gray-900">{c.name}</div>
                    <div className="text-xs text-gray-500">
                      📞 {c.phone_number} • Type: {c.contact_type} • Priority: {c.priority}
                    </div>
                  </div>
                  <button
                    onClick={() => handleDeleteEmergency(c.id)}
                    className="text-xs font-bold text-red-600 hover:text-red-800 px-3 py-1 bg-red-50 hover:bg-red-100 rounded-lg transition"
                  >
                    Delete
                  </button>
                </div>
              ))}
            </div>
          </div>

          <div className="bg-white p-6 rounded-2xl shadow-sm border border-gray-100">
            <h2 className="text-lg font-bold text-gray-900 mb-4">Add Emergency Contact</h2>
            <form onSubmit={handleCreateEmergency} className="space-y-3 text-xs">
              <div>
                <label className="font-semibold text-gray-700">Contact Name</label>
                <input
                  type="text"
                  value={newEmg.name}
                  onChange={(e) => setNewEmg({ ...newEmg, name: e.target.value })}
                  placeholder="e.g. 108 Ambulance Dispatch"
                  className="w-full px-3 py-2 border rounded-lg mt-1"
                  required
                />
              </div>
              <div>
                <label className="font-semibold text-gray-700">Phone Number</label>
                <input
                  type="text"
                  value={newEmg.phone_number}
                  onChange={(e) => setNewEmg({ ...newEmg, phone_number: e.target.value })}
                  placeholder="108"
                  className="w-full px-3 py-2 border rounded-lg mt-1"
                  required
                />
              </div>
              <div>
                <label className="font-semibold text-gray-700">Type</label>
                <select
                  value={newEmg.contact_type}
                  onChange={(e) => setNewEmg({ ...newEmg, contact_type: e.target.value })}
                  className="w-full px-3 py-2 border rounded-lg mt-1"
                >
                  <option value="AMBULANCE">Ambulance</option>
                  <option value="HELPLINE">Emergency Helpline</option>
                  <option value="BLOOD_BANK">Blood Bank</option>
                </select>
              </div>
              <button type="submit" className="w-full py-2.5 bg-slate-900 text-white font-bold rounded-xl shadow mt-2">
                Add Contact
              </button>
            </form>
          </div>
        </div>
      )}

      {/* TELEPHONY TAB */}
      {activeTab === 'telephony' && <AdminTelephony />}
    </div>
  );
}
