from datetime import datetime, date, time
import zoneinfo
from app.core.config import settings

def get_indian_timezone():
    """Returns Asia/Kolkata ZoneInfo timezone object."""
    try:
        return zoneinfo.ZoneInfo("Asia/Kolkata")
    except Exception:
        # Fallback if zoneinfo tz data is missing
        import datetime as dt
        return dt.timezone(dt.timedelta(hours=5, minutes=30))

def get_now_ist() -> datetime:
    """Returns current datetime in Asia/Kolkata timezone."""
    tz = get_indian_timezone()
    return datetime.now(tz)

def get_today_ist() -> date:
    """Returns current date in Asia/Kolkata timezone."""
    return get_now_ist().date()

def get_current_time_ist() -> time:
    """Returns current time in Asia/Kolkata timezone."""
    return get_now_ist().time()

# Alias for get_now_ist
get_ist_now = get_now_ist
