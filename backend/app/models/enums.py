import enum

class UserRole(str, enum.Enum):
    CUSTOMER = "CUSTOMER"
    PROVIDER = "PROVIDER"
    ADMIN = "ADMIN"

class AppointmentStatus(str, enum.Enum):
    BOOKED = "BOOKED"
    PENDING = "PENDING"
    CONFIRMED = "CONFIRMED"
    IN_PROGRESS = "IN_PROGRESS"
    CANCELLED = "CANCELLED"
    COMPLETED = "COMPLETED"
    NO_SHOW = "NO_SHOW"

class BookingChannel(str, enum.Enum):
    PWA = "PWA"
    PHONE = "PHONE"
    ADMIN = "ADMIN"
    PROVIDER = "PROVIDER"

class FacilityType(str, enum.Enum):
    PHC = "PHC"
    CHC = "CHC"
    PRIMARY_HEALTH_CENTRE = "PRIMARY_HEALTH_CENTRE"
    COMMUNITY_HEALTH_CENTRE = "COMMUNITY_HEALTH_CENTRE"
    DISTRICT_HOSPITAL = "DISTRICT_HOSPITAL"
    GOVERNMENT_HOSPITAL = "GOVERNMENT_HOSPITAL"
    PRIVATE_HOSPITAL = "PRIVATE_HOSPITAL"
    SPECIALTY_HOSPITAL = "SPECIALTY_HOSPITAL"
    CLINIC = "CLINIC"
    DIAGNOSTIC_CENTRE = "DIAGNOSTIC_CENTRE"
    EMERGENCY_CENTRE = "EMERGENCY_CENTRE"

class AmbulanceStatus(str, enum.Enum):
    AVAILABLE = "AVAILABLE"
    ON_TRIP = "ON_TRIP"
    AT_FACILITY = "AT_FACILITY"
    MAINTENANCE = "MAINTENANCE"
    OFFLINE = "OFFLINE"

class AmbulanceType(str, enum.Enum):
    BASIC_LIFE_SUPPORT = "BASIC_LIFE_SUPPORT"
    ADVANCED_LIFE_SUPPORT = "ADVANCED_LIFE_SUPPORT"
    PATIENT_TRANSPORT = "PATIENT_TRANSPORT"
    NEONATAL = "NEONATAL"

class SlotStatus(str, enum.Enum):
    AVAILABLE = "AVAILABLE"
    BOOKED = "BOOKED"
    CANCELLED = "CANCELLED"
    BLOCKED = "BLOCKED"

class CallSessionStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"

class NotificationStatus(str, enum.Enum):
    QUEUED = "QUEUED"
    PENDING = "PENDING"
    SENDING = "SENDING"
    SENT = "SENT"
    DELIVERED = "DELIVERED"
    FAILED = "FAILED"
    RETRYING = "RETRYING"

class Language(str, enum.Enum):
    EN = "EN"
    HI = "HI"
    MR = "MR"

class FacilityStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    TEMPORARILY_UNAVAILABLE = "TEMPORARILY_UNAVAILABLE"
    INACTIVE = "INACTIVE"

class DepartmentStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"

class DoctorStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    ON_LEAVE = "ON_LEAVE"
    INACTIVE = "INACTIVE"

class ExceptionType(str, enum.Enum):
    LEAVE = "LEAVE"
    HOLIDAY = "HOLIDAY"
    EMERGENCY_DUTY = "EMERGENCY_DUTY"
    CUSTOM_HOURS = "CUSTOM_HOURS"

class VisitStatus(str, enum.Enum):
    NOT_CHECKED_IN = "NOT_CHECKED_IN"
    WAITING = "WAITING"
    IN_CONSULTATION = "IN_CONSULTATION"
    COMPLETED = "COMPLETED"
    NO_SHOW = "NO_SHOW"

