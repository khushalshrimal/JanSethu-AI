from pydantic import BaseModel
from typing import Optional
from app.models.enums import Language

class AppointmentNotificationContext(BaseModel):
    appointment_id: int
    patient_name: str
    doctor_name: str
    facility_name: str
    department_name: str
    appointment_date: str
    start_time: str
    end_time: Optional[str] = None
    confirmation_code: str
    cancellation_reason: Optional[str] = "Patient request"
    queue_token: Optional[str] = None
    language: Language = Language.HI

TEMPLATES = {
    "APPOINTMENT_CONFIRMED": {
        Language.HI: (
            "JanSethu Healthcare Appointment Confirmed\n"
            "Ref: {confirmation_code}\n"
            "Facility: {facility_name}\n"
            "Doctor: {doctor_name} ({department_name})\n"
            "Date: {appointment_date}\n"
            "Time: {start_time}\n"
            "Please arrive 15 minutes before your slot."
        ),
        Language.MR: (
            "JanSethu Healthcare Appointment Confirmed\n"
            "Ref: {confirmation_code}\n"
            "Facility: {facility_name}\n"
            "Doctor: {doctor_name} ({department_name})\n"
            "Date: {appointment_date}\n"
            "Time: {start_time}\n"
            "Please arrive 15 minutes before your slot."
        ),
        Language.EN: (
            "JanSethu Healthcare Appointment Confirmed\n"
            "Ref: {confirmation_code}\n"
            "Facility: {facility_name}\n"
            "Doctor: {doctor_name} ({department_name})\n"
            "Date: {appointment_date}\n"
            "Time: {start_time}\n"
            "Please arrive 15 minutes before your slot."
        )
    },
    "APPOINTMENT_CHECKIN": {
        Language.HI: (
            "JanSethu OPD Check-in Confirmed\n"
            "Ref: {confirmation_code}\n"
            "Queue Token: {queue_token}\n"
            "Facility: {facility_name}\n"
            "Doctor: {doctor_name}\n"
            "Please wait for your queue token to be called."
        ),
        Language.MR: (
            "JanSethu OPD Check-in Confirmed\n"
            "Ref: {confirmation_code}\n"
            "Queue Token: {queue_token}\n"
            "Facility: {facility_name}\n"
            "Doctor: {doctor_name}\n"
            "Please wait for your queue token to be called."
        ),
        Language.EN: (
            "JanSethu OPD Check-in Confirmed\n"
            "Ref: {confirmation_code}\n"
            "Queue Token: {queue_token}\n"
            "Facility: {facility_name}\n"
            "Doctor: {doctor_name}\n"
            "Please wait for your queue token to be called."
        )
    },
    "APPOINTMENT_RESCHEDULED": {
        Language.HI: (
            "JanSethu Healthcare Appointment Rescheduled\n"
            "Ref: {confirmation_code}\n"
            "Facility: {facility_name}\n"
            "Doctor: {doctor_name}\n"
            "New Date: {appointment_date}\n"
            "New Time: {start_time}\n"
            "Please arrive 15 minutes before your new slot."
        ),
        Language.MR: (
            "JanSethu Healthcare Appointment Rescheduled\n"
            "Ref: {confirmation_code}\n"
            "Facility: {facility_name}\n"
            "Doctor: {doctor_name}\n"
            "New Date: {appointment_date}\n"
            "New Time: {start_time}\n"
            "Please arrive 15 minutes before your new slot."
        ),
        Language.EN: (
            "JanSethu Healthcare Appointment Rescheduled\n"
            "Ref: {confirmation_code}\n"
            "Facility: {facility_name}\n"
            "Doctor: {doctor_name}\n"
            "New Date: {appointment_date}\n"
            "New Time: {start_time}\n"
            "Please arrive 15 minutes before your new slot."
        )
    },
    "APPOINTMENT_CANCELLED": {
        Language.HI: (
            "JanSethu Healthcare Appointment Cancelled\n"
            "Ref: {confirmation_code}\n"
            "Facility: {facility_name}\n"
            "Doctor: {doctor_name}\n"
            "Reason: {cancellation_reason}"
        ),
        Language.MR: (
            "JanSethu Healthcare Appointment Cancelled\n"
            "Ref: {confirmation_code}\n"
            "Facility: {facility_name}\n"
            "Doctor: {doctor_name}\n"
            "Reason: {cancellation_reason}"
        ),
        Language.EN: (
            "JanSethu Healthcare Appointment Cancelled\n"
            "Ref: {confirmation_code}\n"
            "Facility: {facility_name}\n"
            "Doctor: {doctor_name}\n"
            "Reason: {cancellation_reason}"
        )
    },
    "APPOINTMENT_REMINDER": {
        Language.HI: (
            "JanSethu Healthcare Reminder:\n"
            "Your appointment with {doctor_name} at {facility_name} is scheduled for {appointment_date} at {start_time}.\n"
            "Confirmation: {confirmation_code}"
        ),
        Language.MR: (
            "JanSethu Healthcare Reminder:\n"
            "Your appointment with {doctor_name} at {facility_name} is scheduled for {appointment_date} at {start_time}.\n"
            "Confirmation: {confirmation_code}"
        ),
        Language.EN: (
            "JanSethu Healthcare Reminder:\n"
            "Your appointment with {doctor_name} at {facility_name} is scheduled for {appointment_date} at {start_time}.\n"
            "Confirmation: {confirmation_code}"
        )
    }
}

def render_notification_template(event_type: str, ctx: AppointmentNotificationContext) -> str:
    lang = ctx.language or Language.HI
    event_dict = TEMPLATES.get(event_type.upper(), TEMPLATES["APPOINTMENT_CONFIRMED"])
    template = event_dict.get(lang, event_dict.get(Language.EN, event_dict[Language.HI]))

    # Doctor name formatting
    doc_name = ctx.doctor_name
    if doc_name and not doc_name.startswith("Dr."):
        doc_name = f"Dr. {doc_name}"

    return template.format(
        confirmation_code=ctx.confirmation_code,
        facility_name=ctx.facility_name,
        doctor_name=doc_name,
        department_name=ctx.department_name,
        appointment_date=ctx.appointment_date,
        start_time=ctx.start_time,
        cancellation_reason=ctx.cancellation_reason or "Patient request",
        queue_token=ctx.queue_token or "N/A"
    )
