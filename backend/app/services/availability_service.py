from sqlalchemy.orm import Session
from datetime import date, time, datetime, timedelta
from typing import List, Tuple, Optional
from fastapi import HTTPException, status
from app.models.doctor import Doctor, DoctorAvailability, DoctorScheduleException
from app.models.facility import Facility, Department
from app.models.appointment import Appointment
from app.models.enums import AppointmentStatus, FacilityStatus, DepartmentStatus, DoctorStatus, ExceptionType
from app.schemas.doctor import SlotStatusEnum, SlotResponse, DoctorAvailabilityQueryResponse
from app.utils.timezone import get_today_ist, get_current_time_ist

def time_to_minutes(t: time) -> int:
    return t.hour * 60 + t.minute

def minutes_to_time_str(minutes: int) -> str:
    h = minutes // 60
    m = minutes % 60
    return f"{h:02d}:{m:02d}"

class AvailabilityResult(dict):
    def __iter__(self):
        yield self.get("is_available", False)
        yield self.get("reason", "")

class AvailabilityService:
    @staticmethod
    def generate_doctor_slots(
        db: Session,
        doctor_id: int,
        target_date: date
    ) -> DoctorAvailabilityQueryResponse:
        # 1. Fetch Doctor and verify active/operational status
        doc = db.query(Doctor).filter(Doctor.id == doctor_id, Doctor.is_active == True).first()
        if not doc or (hasattr(doc, "status") and doc.status == DoctorStatus.INACTIVE):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Active Doctor with ID {doctor_id} not found."
            )

        if hasattr(doc, "status") and doc.status == DoctorStatus.ON_LEAVE:
            fac = db.query(Facility).filter(Facility.id == doc.facility_id).first()
            dept = db.query(Department).filter(Department.id == doc.department_id).first()
            return DoctorAvailabilityQueryResponse(
                doctor_id=doc.id,
                doctor_name=doc.name,
                facility_id=fac.id if fac else 0,
                facility_name=fac.name if fac else "",
                department_id=dept.id if dept else 0,
                department_name=dept.name if dept else "",
                requested_date=target_date,
                timezone="Asia/Kolkata",
                slots=[]
            )

        fac = db.query(Facility).filter(Facility.id == doc.facility_id, Facility.is_active == True).first()
        if not fac or (hasattr(fac, "status") and fac.status == FacilityStatus.INACTIVE):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Doctor's facility is inactive or not found."
            )

        if hasattr(fac, "status") and fac.status == FacilityStatus.TEMPORARILY_UNAVAILABLE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Facility '{fac.name}' is temporarily unavailable for OPD appointments."
            )

        dept = db.query(Department).filter(Department.id == doc.department_id, Department.is_active == True).first()
        if not dept or (hasattr(dept, "status") and dept.status == DepartmentStatus.INACTIVE):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Doctor's department is inactive or not found."
            )

        # 2. Determine Day of Week (0=Monday, 6=Sunday)
        day_of_week = target_date.weekday()

        # 3. Fetch DoctorAvailability for this day
        availabilities = db.query(DoctorAvailability).filter(
            DoctorAvailability.doctor_id == doctor_id,
            DoctorAvailability.day_of_week == day_of_week,
            DoctorAvailability.is_active == True
        ).all()

        # 4. Fetch existing Confirmed/Pending Appointments for this doctor on target_date
        existing_appointments = db.query(Appointment).filter(
            Appointment.doctor_id == doctor_id,
            Appointment.appointment_date == target_date,
            Appointment.status.in_([AppointmentStatus.CONFIRMED, AppointmentStatus.PENDING, AppointmentStatus.BOOKED])
        ).all()
        booked_start_times = {apt.start_time.strftime("%H:%M") for apt in existing_appointments}

        # 5. Fetch DoctorScheduleExceptions (Leave/Blocked time/Custom hours) on target_date
        schedule_exceptions = db.query(DoctorScheduleException).filter(
            DoctorScheduleException.doctor_id == doctor_id,
            DoctorScheduleException.date == target_date,
            DoctorScheduleException.is_active == True
        ).all()

        # Check if custom hours exception applies
        custom_hours_exc = [e for e in schedule_exceptions if hasattr(e, "exception_type") and e.exception_type == ExceptionType.CUSTOM_HOURS]

        # Timezone-aware date & time checks (Asia/Kolkata)
        today_ist = get_today_ist()
        current_time_ist = get_current_time_ist()
        current_time_mins = time_to_minutes(current_time_ist)
        is_past_date = target_date < today_ist
        is_today = target_date == today_ist

        generated_slots: List[SlotResponse] = []

        # Doctor on Leave check
        is_doctor_on_leave = (hasattr(doc, "status") and doc.status == DoctorStatus.ON_LEAVE)

        # 6. Slot Generator Loop
        for avail in availabilities:
            duration = avail.slot_duration_minutes or 30
            start_mins = time_to_minutes(avail.start_time)
            end_mins = time_to_minutes(avail.end_time)

            curr_mins = start_mins
            while curr_mins + duration <= end_mins:
                s_str = minutes_to_time_str(curr_mins)
                e_str = minutes_to_time_str(curr_mins + duration)
                slot_time_obj = time(curr_mins // 60, curr_mins % 60)

                slot_status = SlotStatusEnum.AVAILABLE
                status_reason = None

                if is_doctor_on_leave:
                    slot_status = SlotStatusEnum.UNAVAILABLE
                    status_reason = "Doctor is currently on leave"
                elif is_past_date or (is_today and curr_mins < current_time_mins):
                    slot_status = SlotStatusEnum.PAST
                    status_reason = "Slot time has passed"

                if slot_status == SlotStatusEnum.AVAILABLE and custom_hours_exc:
                    # Verify slot falls within custom hours
                    in_custom = False
                    for c_exc in custom_hours_exc:
                        c_start = time_to_minutes(c_exc.start_time)
                        c_end = time_to_minutes(c_exc.end_time)
                        if curr_mins >= c_start and (curr_mins + duration) <= c_end:
                            in_custom = True
                            break
                    if not in_custom:
                        slot_status = SlotStatusEnum.BLOCKED
                        status_reason = "Outside custom OPD hours exception"

                # Check 2: Doctor Schedule Exception / Blocked Time (Leaves, Holidays, Emergency Duty)
                if slot_status == SlotStatusEnum.AVAILABLE:
                    for exc in schedule_exceptions:
                        if hasattr(exc, "exception_type") and exc.exception_type == ExceptionType.CUSTOM_HOURS:
                            continue
                        exc_start = time_to_minutes(exc.start_time)
                        exc_end = time_to_minutes(exc.end_time)
                        if not (curr_mins + duration <= exc_start or curr_mins >= exc_end):
                            slot_status = SlotStatusEnum.BLOCKED
                            status_reason = exc.reason or "Doctor Unavailable / On Leave"
                            break

                # Check 3: Existing Confirmed Booking
                if slot_status == SlotStatusEnum.AVAILABLE:
                    if slot_time_obj.strftime("%H:%M") in booked_start_times:
                        slot_status = SlotStatusEnum.BOOKED
                        status_reason = "Slot reserved by existing appointment"

                generated_slots.append(SlotResponse(
                    start_time=s_str,
                    end_time=e_str,
                    status=slot_status,
                    reason=status_reason
                ))
                curr_mins += duration

        return DoctorAvailabilityQueryResponse(
            doctor_id=doc.id,
            doctor_name=doc.name,
            facility_id=fac.id,
            facility_name=fac.name,
            department_id=dept.id,
            department_name=dept.name,
            requested_date=target_date,
            timezone="Asia/Kolkata",
            slots=generated_slots
        )

    @staticmethod
    def check_slot_availability(
        db: Session,
        doctor_id: int,
        target_date: date,
        start_time: time,
        facility_id: Optional[int] = None,
        department_id: Optional[int] = None,
        end_time: Optional[time] = None
    ) -> dict:
        """
        Reusable pre-check service used before creating appointments in any channel.
        Returns dict: {"is_available": bool, "status": str, "reason": str}
        """
        doc = db.query(Doctor).filter(Doctor.id == doctor_id, Doctor.is_active == True).first()
        if not doc or (hasattr(doc, "status") and doc.status == DoctorStatus.INACTIVE):
            return AvailabilityResult({"is_available": False, "status": "DOCTOR_INACTIVE", "reason": "Doctor is inactive or does not exist."})

        if hasattr(doc, "status") and doc.status == DoctorStatus.ON_LEAVE:
            return AvailabilityResult({"is_available": False, "status": "DOCTOR_ON_LEAVE", "reason": "Doctor is currently on leave."})

        fac_id = facility_id or doc.facility_id
        fac = db.query(Facility).filter(Facility.id == fac_id, Facility.is_active == True).first()
        if not fac or (hasattr(fac, "status") and fac.status == FacilityStatus.INACTIVE):
            return AvailabilityResult({"is_available": False, "status": "FACILITY_INACTIVE", "reason": "Facility is inactive or does not exist."})

        if hasattr(fac, "status") and fac.status == FacilityStatus.TEMPORARILY_UNAVAILABLE:
            return AvailabilityResult({"is_available": False, "status": "FACILITY_UNAVAILABLE", "reason": f"Facility '{fac.name}' is temporarily unavailable for OPD appointments."})

        dept_id = department_id or doc.department_id
        dept = db.query(Department).filter(Department.id == dept_id, Department.is_active == True).first()
        if not dept or (hasattr(dept, "status") and dept.status == DepartmentStatus.INACTIVE):
            return AvailabilityResult({"is_available": False, "status": "DEPARTMENT_INACTIVE", "reason": "Department is inactive or not found."})

        if doc.facility_id != fac_id or doc.department_id != dept_id:
            return AvailabilityResult({"is_available": False, "status": "MISMATCH", "reason": "Doctor is not assigned to the specified facility and department."})

        # Date & Time past checks
        today_ist = get_today_ist()
        if target_date < today_ist:
            return AvailabilityResult({"is_available": False, "status": "PAST", "reason": "Cannot book appointment in the past."})

        if target_date == today_ist:
            if time_to_minutes(start_time) <= time_to_minutes(get_current_time_ist()):
                return AvailabilityResult({"is_available": False, "status": "PAST", "reason": "Slot time has already passed today."})

        # Calculate slot end time if missing
        if not end_time:
            duration = 30
            if doc.availabilities:
                duration = doc.availabilities[0].slot_duration_minutes or 30
            dt_start = datetime.combine(target_date, start_time)
            dt_end = dt_start + timedelta(minutes=duration)
            end_time = dt_end.time()

        # Schedule Exception Check
        exceptions = db.query(DoctorScheduleException).filter(
            DoctorScheduleException.doctor_id == doctor_id,
            DoctorScheduleException.date == target_date,
            DoctorScheduleException.is_active == True
        ).all()

        custom_hours_exc = [e for e in exceptions if hasattr(e, "exception_type") and e.exception_type == ExceptionType.CUSTOM_HOURS]
        if custom_hours_exc:
            s_mins = time_to_minutes(start_time)
            e_mins = time_to_minutes(end_time)
            in_custom = False
            for c_exc in custom_hours_exc:
                c_start = time_to_minutes(c_exc.start_time)
                c_end = time_to_minutes(c_exc.end_time)
                if s_mins >= c_start and e_mins <= c_end:
                    in_custom = True
                    break
            if not in_custom:
                return AvailabilityResult({"is_available": False, "status": "BLOCKED", "reason": "Slot is outside doctor's custom OPD hours exception."})

        for exc in exceptions:
            if hasattr(exc, "exception_type") and exc.exception_type == ExceptionType.CUSTOM_HOURS:
                continue
            exc_start = time_to_minutes(exc.start_time)
            exc_end = time_to_minutes(exc.end_time)
            s_mins = time_to_minutes(start_time)
            e_mins = time_to_minutes(end_time)
            if not (e_mins <= exc_start or s_mins >= exc_end):
                return AvailabilityResult({"is_available": False, "status": "BLOCKED", "reason": exc.reason or "Doctor Unavailable / On Leave"})

        # Booked Slot Check
        booked = db.query(Appointment).filter(
            Appointment.doctor_id == doctor_id,
            Appointment.appointment_date == target_date,
            Appointment.start_time == start_time,
            Appointment.status.in_([AppointmentStatus.BOOKED, AppointmentStatus.CONFIRMED, AppointmentStatus.PENDING])
        ).first()
        if booked:
            return AvailabilityResult({"is_available": False, "status": "BOOKED", "reason": "Slot is already booked by another appointment."})

        return AvailabilityResult({"is_available": True, "status": "AVAILABLE", "reason": "Slot is available for booking."})

# Standalone function alias for backward compatibility
def check_slot_availability(
    db: Session,
    doctor_id: int,
    target_date: date,
    start_time: time,
    facility_id: Optional[int] = None,
    department_id: Optional[int] = None,
    end_time: Optional[time] = None
) -> dict:
    return AvailabilityService.check_slot_availability(
        db, doctor_id, target_date, start_time, facility_id, department_id, end_time
    )
