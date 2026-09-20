import React, { useState, useEffect } from 'react';
import { useSearchParams, useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { getDoctorAvailability, getDoctorDetails } from '../services/doctorService';
import { createAppointment } from '../services/appointmentService';
import { getFacilityDetails } from '../services/facilityService';
import { Calendar, Clock, User, Phone, CheckCircle, AlertCircle, RefreshCw, ArrowLeft, Stethoscope, MapPin } from 'lucide-react';

export default function DoctorDetails() {
  const [searchParams] = useSearchParams();
  const doctorId = searchParams.get('doctor_id');
  const facilityId = searchParams.get('facility_id');
  const navigate = useNavigate();
  const { user, isAuthenticated } = useAuth();

  // Helper to format YYYY-MM-DD
  const formatDateStr = (dateObj) => dateObj.toISOString().split('T')[0];

  const todayStr = formatDateStr(new Date());

  const [selectedDate, setSelectedDate] = useState(todayStr);
  const [doctor, setDoctor] = useState(null);
  const [facility, setFacility] = useState(null);
  const [availability, setAvailability] = useState(null);
  const [loadingDoc, setLoadingDoc] = useState(true);
  const [loadingSlots, setLoadingSlots] = useState(false);
  const [error, setError] = useState(null);

  const [selectedSlot, setSelectedSlot] = useState(null);
  const [bookingLoading, setBookingLoading] = useState(false);
  const [bookingError, setBookingError] = useState(null);

  const [patientForm, setPatientForm] = useState({
    patient_name: user?.full_name || '',
    patient_phone: user?.phone || '',
    patient_age: 30,
    patient_gender: 'MALE',
    reason: 'Routine OPD Consultation',
  });

  // Generate date options (Next 7 Days)
  const dateOptions = Array.from({ length: 7 }, (_, i) => {
    const d = new Date();
    d.setDate(d.getDate() + i);
    const dateStr = formatDateStr(d);
    const dayName = i === 0 ? 'Today' : i === 1 ? 'Tomorrow' : d.toLocaleDateString('en-US', { weekday: 'short' });
    const formattedDate = d.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
    return { dateStr, dayName, formattedDate };
  });

  useEffect(() => {
    if (user) {
      setPatientForm((prev) => ({
        ...prev,
        patient_name: user.full_name || prev.patient_name,
        patient_phone: user.phone || prev.patient_phone,
      }));
    }
  }, [user]);

  useEffect(() => {
    const fetchDocAndFac = async () => {
      if (!doctorId) return;
      setLoadingDoc(true);
      try {
        const docData = await getDoctorDetails(doctorId);
        setDoctor(docData);

        if (facilityId || docData.facility_id) {
          const facData = await getFacilityDetails(facilityId || docData.facility_id);
          setFacility(facData);
        }
      } catch (err) {
        setError(err.response?.data?.detail || 'Failed to load doctor profile.');
      } finally {
        setLoadingDoc(false);
      }
    };
    fetchDocAndFac();
  }, [doctorId, facilityId]);

  const fetchSlots = async (dateStr) => {
    if (!doctorId) return;
    setLoadingSlots(true);
    setBookingError(null);
    try {
      const availData = await getDoctorAvailability(doctorId, dateStr);
      setAvailability(availData);
      setSelectedSlot(null); // Reset slot selection on date change
    } catch (err) {
      setBookingError(err.response?.data?.detail || 'Failed to load availability slots.');
    } finally {
      setLoadingSlots(false);
    }
  };

  useEffect(() => {
    fetchSlots(selectedDate);
  }, [doctorId, selectedDate]);

  const handlePatientFormChange = (e) => {
    setPatientForm({ ...patientForm, [e.target.name]: e.target.value });
  };

  const handleConfirmBooking = async (e) => {
    e.preventDefault();
    if (!selectedSlot) {
      setBookingError('Please select an available OPD time slot.');
      return;
    }
    if (!patientForm.patient_name || !patientForm.patient_phone) {
      setBookingError('Please enter patient name and mobile number.');
      return;
    }

    setBookingLoading(true);
    setBookingError(null);

    try {
      const payload = {
        doctor_id: doctorId,
        date: selectedDate,
        start_time: selectedSlot.start_time,
        end_time: selectedSlot.end_time,
        patient_name: patientForm.patient_name,
        patient_phone: patientForm.patient_phone,
        patient_age: Number(patientForm.patient_age),
        patient_gender: patientForm.patient_gender,
        reason: patientForm.reason,
      };

      const result = await createAppointment(payload);
      // Navigate to booking confirmation screen
      navigate('/confirmation', { state: { appointment: result } });
    } catch (err) {
      const status = err.response?.status;
      const detail = err.response?.data?.detail;

      if (status === 409) {
        setBookingError('⚠️ CONFLICT ALERT: This slot was just booked by another user or phone call. Please select another slot.');
        // Refresh availability grid automatically
        fetchSlots(selectedDate);
      } else {
        setBookingError(detail || 'Failed to book appointment. Please try again.');
      }
    } finally {
      setBookingLoading(false);
    }
  };

  if (loadingDoc) {
    return (
      <div className="bg-white p-12 rounded-3xl border border-slate-200 text-center space-y-3 my-8">
        <RefreshCw className="w-8 h-8 text-sky-600 animate-spin mx-auto" />
        <p className="text-xs font-bold text-slate-600">Loading Doctor & OPD Schedule...</p>
      </div>
    );
  }

  if (error || !doctor) {
    return (
      <div className="space-y-4 my-8">
        <Link to="/facilities" className="text-xs font-bold text-sky-700 hover:underline flex items-center gap-1">
          <ArrowLeft className="w-4 h-4" /> Back to Facilities
        </Link>
        <div className="bg-rose-50 border border-rose-200 p-6 rounded-3xl text-rose-900 text-xs font-bold">
          {error || 'Doctor profile not found.'}
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6 py-2">
      <Link
        to={facility ? `/facilities/${facility.id}` : '/facilities'}
        className="text-xs font-bold text-sky-700 hover:underline inline-flex items-center gap-1"
      >
        <ArrowLeft className="w-4 h-4" /> Back to {facility?.name || 'Facility'}
      </Link>

      {/* Doctor Info Card */}
      <div className="bg-white p-6 sm:p-8 rounded-3xl border border-slate-200 shadow-sm space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-4">
          <div className="flex items-start gap-4">
            <div className="w-16 h-16 rounded-2xl bg-amber-400 text-slate-950 flex items-center justify-center font-black text-2xl flex-shrink-0">
              Dr
            </div>
            <div className="space-y-1">
              <div className="flex items-center gap-2">
                <span className="bg-sky-100 text-sky-800 text-[10px] font-black px-2.5 py-0.5 rounded-full uppercase">
                  {doctor.department_name || 'OPD Department'}
                </span>
                <span className="text-xs font-black text-emerald-800 bg-emerald-50 px-2 py-0.5 rounded-md border border-emerald-200">
                  ₹{doctor.consultation_fee || 0} OPD Fee
                </span>
              </div>
              <h1 className="text-2xl font-black text-slate-900 leading-tight">{doctor.full_name}</h1>
              <p className="text-xs text-slate-600 font-semibold">{doctor.qualification}</p>
              {facility && (
                <p className="text-xs text-slate-500 font-medium flex items-center gap-1 pt-1">
                  <MapPin className="w-3.5 h-3.5 text-sky-600" />
                  <span>{facility.name} ({facility.district})</span>
                </p>
              )}
            </div>
          </div>

          <div className="bg-slate-50 p-3.5 rounded-2xl border border-slate-200 text-xs text-slate-700 space-y-1">
            <p className="font-bold flex items-center gap-1">
              <Clock className="w-3.5 h-3.5 text-sky-600" />
              OPD Room: {doctor.opd_room_number || '101'}
            </p>
            <p className="text-[11px] text-slate-500">
              Languages: {doctor.languages_spoken || 'Hindi, English'}
            </p>
          </div>
        </div>
      </div>

      {/* Date Selector Bar */}
      <div className="space-y-3">
        <h2 className="text-base font-black text-slate-900 flex items-center gap-2">
          <Calendar className="w-5 h-5 text-sky-700" />
          Select Appointment Date
        </h2>

        <div className="flex items-center gap-2 overflow-x-auto pb-2 scrollbar-none">
          {dateOptions.map((item) => (
            <button
              key={item.dateStr}
              onClick={() => setSelectedDate(item.dateStr)}
              className={`p-3 rounded-2xl text-center min-w-[90px] border transition ${
                selectedDate === item.dateStr
                  ? 'bg-sky-800 border-sky-800 text-white shadow-md font-bold'
                  : 'bg-white hover:bg-slate-50 border-slate-200 text-slate-700 font-semibold'
              }`}
            >
              <div className="text-[10px] uppercase font-extrabold opacity-80">{item.dayName}</div>
              <div className="text-xs font-black mt-0.5">{item.formattedDate}</div>
            </button>
          ))}
        </div>
      </div>

      {/* Dynamic Slot Grid */}
      <div className="bg-white p-6 rounded-3xl border border-slate-200 shadow-sm space-y-4">
        <div className="flex items-center justify-between border-b border-slate-100 pb-3">
          <div>
            <h3 className="text-base font-black text-slate-900">
              Real Dynamic OPD Time Slots ({selectedDate})
            </h3>
            <p className="text-[11px] text-slate-500 font-medium">
              Calculated live from doctor availability schedule and existing database bookings
            </p>
          </div>
          <button
            onClick={() => fetchSlots(selectedDate)}
            disabled={loadingSlots}
            className="p-2 text-sky-700 hover:bg-sky-50 rounded-xl transition"
            title="Refresh slots"
          >
            <RefreshCw className={`w-4 h-4 ${loadingSlots ? 'animate-spin' : ''}`} />
          </button>
        </div>

        {bookingError && (
          <div className="p-4 bg-rose-50 border border-rose-200 text-rose-900 rounded-2xl text-xs font-bold flex items-start gap-2">
            <AlertCircle className="w-4 h-4 flex-shrink-0 mt-0.5" />
            <span>{bookingError}</span>
          </div>
        )}

        {loadingSlots ? (
          <div className="py-12 text-center space-y-2">
            <RefreshCw className="w-6 h-6 text-sky-600 animate-spin mx-auto" />
            <p className="text-xs font-bold text-slate-500">Querying DB Availability Engine...</p>
          </div>
        ) : availability?.reason === 'DOCTOR_NOT_SCHEDULED' ? (
          <div className="py-8 text-center bg-amber-50 rounded-2xl border border-amber-200 text-amber-900 text-xs font-semibold">
            Doctor is not scheduled on this day of the week ({availability.day_of_week}). Please select another date.
          </div>
        ) : !availability?.slots || availability.slots.length === 0 ? (
          <div className="py-8 text-center bg-slate-50 rounded-2xl text-xs text-slate-500 font-semibold">
            No OPD slots available for this date.
          </div>
        ) : (
          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-2.5">
            {availability.slots.map((slot, index) => {
              const isSelected =
                selectedSlot?.start_time === slot.start_time && selectedSlot?.end_time === slot.end_time;

              let btnClasses = '';
              let badgeText = '';

              if (slot.status === 'AVAILABLE') {
                btnClasses = isSelected
                  ? 'bg-emerald-600 text-white border-emerald-600 ring-2 ring-emerald-400 font-bold shadow-md'
                  : 'bg-emerald-50 hover:bg-emerald-100 text-emerald-950 border-emerald-300 font-semibold';
                badgeText = 'Available';
              } else if (slot.status === 'BOOKED') {
                btnClasses = 'bg-slate-100 text-slate-400 border-slate-200 cursor-not-allowed line-through';
                badgeText = 'Booked';
              } else if (slot.status === 'BLOCKED') {
                btnClasses = 'bg-amber-100 text-amber-700 border-amber-300 cursor-not-allowed';
                badgeText = 'Blocked';
              } else {
                btnClasses = 'bg-slate-50 text-slate-300 border-slate-100 cursor-not-allowed';
                badgeText = 'Past';
              }

              return (
                <button
                  key={`${slot.start_time}-${index}`}
                  disabled={slot.status !== 'AVAILABLE'}
                  onClick={() => setSelectedSlot(slot)}
                  className={`p-3 rounded-2xl border text-center transition flex flex-col items-center justify-center space-y-1 ${btnClasses}`}
                >
                  <span className="text-xs font-black tracking-tight">{slot.start_time}</span>
                  <span className={`text-[9px] font-extrabold uppercase px-1.5 py-0.5 rounded ${
                    slot.status === 'AVAILABLE'
                      ? isSelected ? 'bg-emerald-700 text-white' : 'bg-emerald-200 text-emerald-900'
                      : 'bg-slate-200 text-slate-600'
                  }`}>
                    {badgeText}
                  </span>
                </button>
              );
            })}
          </div>
        )}
      </div>

      {/* Booking Form (Visible when slot is selected) */}
      {selectedSlot && (
        <form onSubmit={handleConfirmBooking} className="bg-white p-6 sm:p-8 rounded-3xl border-2 border-emerald-400 shadow-md space-y-4">
          <div className="flex items-center justify-between border-b border-slate-100 pb-3">
            <div>
              <h3 className="text-lg font-black text-slate-900 flex items-center gap-2">
                <CheckCircle className="w-5 h-5 text-emerald-600" />
                Confirm Appointment Slot
              </h3>
              <p className="text-xs text-slate-500 font-semibold">
                Selected: <strong className="text-emerald-700">{selectedDate} at {selectedSlot.start_time} - {selectedSlot.end_time}</strong>
              </p>
            </div>
            <span className="text-xs font-black text-emerald-800 bg-emerald-100 px-3 py-1 rounded-full">
              OPD Slot Reserved
            </span>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs">
            <div>
              <label className="block font-bold text-slate-700 uppercase mb-1">Patient Full Name *</label>
              <input
                type="text"
                name="patient_name"
                value={patientForm.patient_name}
                onChange={handlePatientFormChange}
                placeholder="Patient Full Name"
                className="w-full px-3 py-2.5 bg-slate-50 border border-slate-300 rounded-xl font-medium outline-none focus:ring-2 focus:ring-emerald-500"
                required
              />
            </div>

            <div>
              <label className="block font-bold text-slate-700 uppercase mb-1">Mobile Phone (for SMS Confirmation) *</label>
              <input
                type="text"
                name="patient_phone"
                value={patientForm.patient_phone}
                onChange={handlePatientFormChange}
                placeholder="+919876543210"
                className="w-full px-3 py-2.5 bg-slate-50 border border-slate-300 rounded-xl font-medium outline-none focus:ring-2 focus:ring-emerald-500"
                required
              />
            </div>

            <div>
              <label className="block font-bold text-slate-700 uppercase mb-1">Patient Age</label>
              <input
                type="number"
                name="patient_age"
                value={patientForm.patient_age}
                onChange={handlePatientFormChange}
                className="w-full px-3 py-2.5 bg-slate-50 border border-slate-300 rounded-xl font-medium outline-none"
              />
            </div>

            <div>
              <label className="block font-bold text-slate-700 uppercase mb-1">Gender</label>
              <select
                name="patient_gender"
                value={patientForm.patient_gender}
                onChange={handlePatientFormChange}
                className="w-full px-3 py-2.5 bg-slate-50 border border-slate-300 rounded-xl font-medium outline-none"
              >
                <option value="MALE">Male</option>
                <option value="FEMALE">Female</option>
                <option value="OTHER">Other</option>
              </select>
            </div>
          </div>

          <div>
            <label className="block text-xs font-bold text-slate-700 uppercase mb-1">Reason for Visit / Symptoms</label>
            <input
              type="text"
              name="reason"
              value={patientForm.reason}
              onChange={handlePatientFormChange}
              placeholder="e.g. Fever, cough, routine checkup..."
              className="w-full px-3 py-2.5 bg-slate-50 border border-slate-300 rounded-xl text-xs font-medium outline-none"
            />
          </div>

          <button
            type="submit"
            disabled={bookingLoading}
            className="w-full py-3 bg-emerald-600 hover:bg-emerald-500 text-white rounded-xl font-black text-sm transition shadow-md flex items-center justify-center gap-2"
          >
            {bookingLoading ? (
              <>
                <RefreshCw className="w-4 h-4 animate-spin" />
                <span>Creating Real Database Appointment...</span>
              </>
            ) : (
              <>
                <CheckCircle className="w-5 h-5" />
                <span>Confirm & Reserve OPD Appointment</span>
              </>
            )}
          </button>
        </form>
      )}
    </div>
  );
}
