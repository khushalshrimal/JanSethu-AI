import React from 'react';
import { useLocation, Link, useNavigate } from 'react-router-dom';
import { CheckCircle, Calendar, Clock, MapPin, User, Phone, ShieldCheck, Printer, ArrowRight, Home } from 'lucide-react';

export default function BookingConfirmation() {
  const location = useLocation();
  const navigate = useNavigate();
  const appointment = location.state?.appointment;

  if (!appointment) {
    return (
      <div className="max-w-md mx-auto my-12 bg-white p-8 rounded-3xl border border-slate-200 text-center space-y-4">
        <div className="p-3 bg-amber-100 text-amber-800 rounded-full w-fit mx-auto">
          <Calendar className="w-8 h-8" />
        </div>
        <h2 className="text-xl font-black text-slate-900">No Booking Ticket Found</h2>
        <p className="text-xs text-slate-500">
          Please navigate through facility doctor selection to book an OPD slot.
        </p>
        <Link
          to="/facilities"
          className="inline-block px-5 py-2.5 bg-sky-700 text-white rounded-xl text-xs font-bold"
        >
          Browse Healthcare Facilities
        </Link>
      </div>
    );
  }

  const handlePrint = () => {
    window.print();
  };

  return (
    <div className="max-w-xl mx-auto my-6 px-4 space-y-6">
      {/* Top Banner */}
      <div className="bg-emerald-600 text-white p-6 rounded-3xl text-center space-y-2 shadow-lg">
        <div className="w-12 h-12 bg-white/20 text-white rounded-2xl flex items-center justify-center mx-auto">
          <CheckCircle className="w-8 h-8 text-white" />
        </div>
        <h1 className="text-2xl font-black tracking-tight">Appointment Confirmed!</h1>
        <p className="text-xs text-emerald-100 font-medium">
          Your OPD slot has been locked in the JanSethu database.
        </p>
      </div>

      {/* Ticket Card */}
      <div className="bg-white p-6 sm:p-8 rounded-3xl border-2 border-slate-200 shadow-md space-y-6 relative overflow-hidden print:border-none print:shadow-none">
        <div className="bg-sky-50 border border-sky-200 p-4 rounded-2xl text-center space-y-1">
          <span className="text-[10px] font-black uppercase text-sky-800 tracking-wider">
            Backend Confirmation Ticket Code
          </span>
          <div className="text-2xl sm:text-3xl font-black font-mono text-sky-900 tracking-wider">
            {appointment.confirmation_code || 'JS-2026-UNKNOWN'}
          </div>
          <div className="text-xs font-bold text-slate-600 pt-1 flex items-center justify-center gap-2">
            <span className="bg-emerald-100 text-emerald-800 px-2 py-0.5 rounded text-[11px] uppercase font-black">
              STATUS: {appointment.status || 'CONFIRMED'}
            </span>
            {appointment.queue_number && (
              <span className="bg-amber-100 text-amber-900 px-2 py-0.5 rounded text-[11px] font-extrabold">
                Token #{appointment.queue_number}
              </span>
            )}
          </div>
        </div>

        {/* Doctor & Facility Info */}
        <div className="space-y-3 text-xs border-b border-slate-100 pb-4">
          <h3 className="text-xs font-black text-slate-400 uppercase tracking-wider">
            Healthcare Provider Info
          </h3>

          <div className="flex items-start justify-between">
            <div>
              <p className="font-black text-slate-900 text-base">
                Dr. {appointment.doctor_name || 'OPD Specialist'}
              </p>
              <p className="text-sky-700 font-bold">{appointment.department_name || 'General OPD'}</p>
            </div>
            <div className="text-right">
              <span className="font-extrabold text-emerald-700 bg-emerald-50 px-2 py-1 rounded border border-emerald-200">
                ₹{appointment.consultation_fee || 0} OPD Fee
              </span>
            </div>
          </div>

          <p className="text-slate-600 font-medium flex items-center gap-1.5">
            <MapPin className="w-4 h-4 text-sky-600 flex-shrink-0" />
            <span>{appointment.facility_name || 'Healthcare Facility'}</span>
          </p>
        </div>

        {/* Date & Time Slot */}
        <div className="grid grid-cols-2 gap-4 text-xs border-b border-slate-100 pb-4">
          <div className="bg-slate-50 p-3 rounded-2xl border border-slate-100 space-y-1">
            <span className="text-[10px] font-bold text-slate-400 uppercase flex items-center gap-1">
              <Calendar className="w-3.5 h-3.5 text-sky-600" />
              Appointment Date
            </span>
            <p className="font-black text-slate-900 text-sm">{appointment.date}</p>
          </div>

          <div className="bg-slate-50 p-3 rounded-2xl border border-slate-100 space-y-1">
            <span className="text-[10px] font-bold text-slate-400 uppercase flex items-center gap-1">
              <Clock className="w-3.5 h-3.5 text-sky-600" />
              OPD Time Slot
            </span>
            <p className="font-black text-slate-900 text-sm">
              {appointment.start_time} - {appointment.end_time}
            </p>
          </div>
        </div>

        {/* Patient Info */}
        <div className="space-y-2 text-xs border-b border-slate-100 pb-4">
          <h3 className="text-xs font-black text-slate-400 uppercase tracking-wider">
            Patient Information
          </h3>

          <div className="grid grid-cols-2 gap-2 text-slate-700 font-medium">
            <p><strong>Name:</strong> {appointment.patient_name}</p>
            <p><strong>Phone:</strong> {appointment.patient_phone}</p>
            {appointment.patient_age && <p><strong>Age:</strong> {appointment.patient_age} yrs</p>}
            {appointment.patient_gender && <p><strong>Gender:</strong> {appointment.patient_gender}</p>}
          </div>
          {appointment.reason && (
            <p className="text-slate-600 pt-1 text-[11px]">
              <strong>Reason:</strong> {appointment.reason}
            </p>
          )}
        </div>

        {/* SMS Dispatch Notice */}
        <div className="bg-emerald-50 border border-emerald-200 p-3.5 rounded-2xl text-emerald-950 text-xs font-semibold flex items-center gap-2">
          <ShieldCheck className="w-5 h-5 text-emerald-600 flex-shrink-0" />
          <div>
            <p className="font-bold">SMS Dispatch Queued</p>
            <p className="text-[11px] text-emerald-800">
              Development SMS notification recorded for <strong>{appointment.patient_phone}</strong>.
            </p>
          </div>
        </div>
      </div>

      {/* Action Buttons */}
      <div className="flex flex-col sm:flex-row gap-3 print:hidden">
        <button
          onClick={handlePrint}
          className="flex-1 py-3 bg-slate-100 hover:bg-slate-200 text-slate-800 rounded-2xl font-bold text-xs transition flex items-center justify-center gap-2 border border-slate-300"
        >
          <Printer className="w-4 h-4" />
          <span>Print / Save Ticket</span>
        </button>

        <Link
          to="/my-appointments"
          className="flex-1 py-3 bg-sky-700 hover:bg-sky-800 text-white rounded-2xl font-bold text-xs transition shadow-sm flex items-center justify-center gap-2"
        >
          <span>View My Appointments</span>
          <ArrowRight className="w-4 h-4" />
        </Link>
      </div>
    </div>
  );
}
