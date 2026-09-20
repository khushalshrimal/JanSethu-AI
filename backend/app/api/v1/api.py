from fastapi import APIRouter
from app.api.v1.endpoints import health, auth, users, facilities, doctors, appointments, phone, provider, admin, telephony_webhooks

api_router = APIRouter()
api_router.include_router(health.router, tags=["Health"])
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(users.router, prefix="/users", tags=["Users"])
api_router.include_router(facilities.router, prefix="/facilities", tags=["Facilities"])
api_router.include_router(facilities.router, prefix="/healthcare", tags=["Healthcare Discovery"])
api_router.include_router(doctors.router, prefix="/doctors", tags=["Doctors"])
api_router.include_router(appointments.router, prefix="/appointments", tags=["Appointments"])
api_router.include_router(provider.router, prefix="/provider", tags=["Provider Queue"])
api_router.include_router(admin.router, prefix="/admin", tags=["Admin Console"])
api_router.include_router(phone.router, prefix="/phone", tags=["Telephony Phone Engine"])
api_router.include_router(telephony_webhooks.router, prefix="/telephony", tags=["Telephony Webhooks & Integration"])
api_router.include_router(telephony_webhooks.router, prefix="/sms", tags=["SMS Webhooks & Delivery Callbacks"])
