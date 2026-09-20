import React, { useState, useEffect } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import { getFacilityDetails, getFacilityDepartments } from '../services/facilityService';
import { getDoctors } from '../services/doctorService';
import { Building2, MapPin, Phone, ShieldAlert, User, Calendar, ArrowLeft, RefreshCw, Stethoscope, Clock } from 'lucide-react';

export default function FacilityDetails() {
  const { id } = useParams();
  const navigate = useNavigate();

  const [facility, setFacility] = useState(null);
  const [departments, setDepartments] = useState([]);
  const [selectedDeptId, setSelectedDeptId] = useState(null);
  const [doctors, setDoctors] = useState([]);
  const [loadingFacility, setLoadingFacility] = useState(true);
  const [loadingDoctors, setLoadingDoctors] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchFacilityInfo = async () => {
      setLoadingFacility(true);
      setError(null);
      try {
        const facData = await getFacilityDetails(id);
        setFacility(facData);
        const deptsData = await getFacilityDepartments(id);
        setDepartments(deptsData);
        if (deptsData && deptsData.length > 0) {
          setSelectedDeptId(deptsData[0].id);
        }
      } catch (err) {
        setError(err.response?.data?.detail || 'Failed to load facility details.');
      } finally {
        setLoadingFacility(false);
      }
    };
    fetchFacilityInfo();
  }, [id]);

  useEffect(() => {
    const fetchDoctorsList = async () => {
      if (!id) return;
      setLoadingDoctors(true);
      try {
        const params = { facility_id: id };
        if (selectedDeptId) {
          params.department_id = selectedDeptId;
        }
        const docsData = await getDoctors(params);
        setDoctors(docsData);
      } catch (err) {
        console.error('Error loading doctors:', err);
      } finally {
        setLoadingDoctors(false);
      }
    };
    fetchDoctorsList();
  }, [id, selectedDeptId]);

  if (loadingFacility) {
    return (
      <div className="bg-white p-12 rounded-3xl border border-slate-200 text-center space-y-3 my-8">
        <RefreshCw className="w-8 h-8 text-sky-600 animate-spin mx-auto" />
        <p className="text-xs font-bold text-slate-600">Loading Facility Details & Departments...</p>
      </div>
    );
  }

  if (error || !facility) {
    return (
      <div className="space-y-4 my-8">
        <Link to="/facilities" className="text-xs font-bold text-sky-700 hover:underline flex items-center gap-1">
          <ArrowLeft className="w-4 h-4" /> Back to Facilities
        </Link>
        <div className="bg-rose-50 border border-rose-200 p-6 rounded-3xl text-rose-900 text-xs font-bold">
          {error || 'Healthcare facility not found.'}
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6 py-2">
      <Link to="/facilities" className="text-xs font-bold text-sky-700 hover:underline inline-flex items-center gap-1">
        <ArrowLeft className="w-4 h-4" /> Back to Healthcare Facilities List
      </Link>

      {/* Facility Header Card */}
      <div className="bg-white p-6 sm:p-8 rounded-3xl border border-slate-200 shadow-sm space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-4">
          <div className="space-y-2">
            <div className="flex items-center gap-2">
              <span className="bg-sky-100 text-sky-800 text-[10px] font-black px-2.5 py-0.5 rounded-full uppercase">
                {facility.category}
              </span>
              {facility.has_emergency_24x7 && (
                <span className="bg-rose-100 text-rose-800 text-[10px] font-black px-2.5 py-0.5 rounded-full uppercase flex items-center gap-1">
                  <ShieldAlert className="w-3 h-3 text-rose-600" />
                  24x7 Emergency OPD
                </span>
              )}
            </div>

            <h1 className="text-2xl sm:text-3xl font-black text-slate-900 leading-tight">
              {facility.name}
            </h1>

            <p className="text-xs text-slate-600 font-medium flex items-start gap-1.5">
              <MapPin className="w-4 h-4 text-sky-600 flex-shrink-0 mt-0.5" />
              <span>
                {facility.address}, {facility.village ? `${facility.village}, ` : ''}{facility.district}, {facility.state} - {facility.pincode}
              </span>
            </p>
          </div>

          {facility.phone && (
            <a
              href={`tel:${facility.phone}`}
              className="px-4 py-2.5 bg-emerald-50 hover:bg-emerald-100 text-emerald-800 border border-emerald-300 rounded-2xl text-xs font-bold transition flex items-center gap-2 w-fit"
            >
              <Phone className="w-4 h-4 text-emerald-600" />
              <span>Call Facility: {facility.phone}</span>
            </a>
          )}
        </div>
      </div>

      {/* Department Tabs Bar */}
      <div className="space-y-3">
        <h2 className="text-lg font-black text-slate-900 flex items-center gap-2">
          <Stethoscope className="w-5 h-5 text-sky-700" />
          OPD Departments
        </h2>

        {departments.length === 0 ? (
          <p className="text-xs text-slate-500 font-semibold bg-white p-4 rounded-2xl border border-slate-200">
            No active departments registered for this facility yet.
          </p>
        ) : (
          <div className="flex items-center gap-2 overflow-x-auto pb-2 scrollbar-none">
            <button
              onClick={() => setSelectedDeptId(null)}
              className={`px-4 py-2 rounded-xl text-xs font-bold transition flex-shrink-0 ${
                selectedDeptId === null
                  ? 'bg-sky-800 text-white shadow-sm'
                  : 'bg-white hover:bg-slate-100 text-slate-700 border border-slate-200'
              }`}
            >
              All Departments
            </button>
            {departments.map((dept) => (
              <button
                key={dept.id}
                onClick={() => setSelectedDeptId(dept.id)}
                className={`px-4 py-2 rounded-xl text-xs font-bold transition flex-shrink-0 ${
                  selectedDeptId === dept.id
                    ? 'bg-sky-800 text-white shadow-sm'
                    : 'bg-white hover:bg-slate-100 text-slate-700 border border-slate-200'
                }`}
              >
                {dept.name}
              </button>
            ))}
          </div>
        )}
      </div>

      {/* Doctor List */}
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <h3 className="text-base font-extrabold text-slate-800">
            Available Doctors ({doctors.length})
          </h3>
        </div>

        {loadingDoctors ? (
          <div className="bg-white p-8 rounded-3xl border border-slate-200 text-center space-y-2">
            <RefreshCw className="w-6 h-6 text-sky-600 animate-spin mx-auto" />
            <p className="text-xs font-bold text-slate-500">Querying Doctors Schedule...</p>
          </div>
        ) : doctors.length === 0 ? (
          <div className="bg-amber-50 border border-amber-200 p-6 rounded-3xl text-center text-xs font-semibold text-slate-700">
            No doctors found for this selected department.
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {doctors.map((doc) => (
              <div
                key={doc.id}
                className="bg-white p-5 rounded-3xl border border-slate-200 shadow-sm space-y-4 flex flex-col justify-between"
              >
                <div className="space-y-2">
                  <div className="flex items-start justify-between gap-2">
                    <span className="bg-slate-100 text-slate-700 text-[10px] font-black px-2 py-0.5 rounded-full uppercase">
                      {doc.department_name || 'General OPD'}
                    </span>
                    <span className="text-xs font-black text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded-md border border-emerald-200">
                      ₹{doc.consultation_fee || 0} OPD Fee
                    </span>
                  </div>

                  <div className="flex items-start gap-3">
                    <div className="w-12 h-12 rounded-2xl bg-sky-100 text-sky-800 flex items-center justify-center font-black text-lg flex-shrink-0">
                      Dr
                    </div>
                    <div>
                      <h4 className="font-black text-slate-900 text-base leading-tight">
                        {doc.full_name}
                      </h4>
                      <p className="text-xs text-slate-500 font-semibold">{doc.qualification}</p>
                      <p className="text-[11px] text-slate-400 font-medium mt-0.5">
                        Languages: {doc.languages_spoken || 'Hindi, English'}
                      </p>
                    </div>
                  </div>

                  <div className="pt-2 text-xs text-slate-600 space-y-1 bg-slate-50 p-3 rounded-2xl border border-slate-100">
                    <p className="font-bold text-slate-700 flex items-center gap-1">
                      <Clock className="w-3.5 h-3.5 text-sky-600" />
                      OPD Room: {doc.opd_room_number || 'Room 101'}
                    </p>
                    <p className="text-[11px] text-slate-500">
                      Max Patients per slot: {doc.max_patients_per_slot || 1}
                    </p>
                  </div>
                </div>

                <div className="pt-2 border-t border-slate-100">
                  <button
                    onClick={() => navigate(`/booking?doctor_id=${doc.id}&facility_id=${id}`)}
                    className="w-full py-2.5 bg-amber-400 hover:bg-amber-300 text-slate-950 font-black text-xs rounded-xl transition shadow-sm flex items-center justify-center gap-1.5"
                  >
                    <Calendar className="w-4 h-4" />
                    <span>Check Dynamic Time Slots & Book</span>
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
