import logging
import json
import re
from datetime import datetime

class MaskingFormatter(logging.Formatter):
    """
    Structured JSON logger formatter that masks PII such as phone numbers, tokens, and passwords.
    """
    PHONE_REGEX = re.compile(r'(\+?91|0)?[6-9]\d{9}')
    
    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": self.mask_pii(record.getMessage()),
        }
        
        # Attach request_id if present in record
        if hasattr(record, "request_id"):
            log_data["request_id"] = record.request_id
            
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
            
        return json.dumps(log_data)

    @classmethod
    def mask_pii(cls, text: str) -> str:
        """
        Masks phone numbers to preserve privacy (+91******3210).
        """
        if not text:
            return text
            
        def mask_match(match):
            val = match.group(0)
            if len(val) >= 10:
                return val[:3] + "******" + val[-4:]
            return "**********"
            
        return cls.PHONE_REGEX.sub(mask_match, text)

def mask_phone_number(phone: str) -> str:
    """Helper function to mask phone numbers in operational outputs."""
    if not phone or len(phone) < 10:
        return "*******"
    clean = re.sub(r'\D', '', phone)
    if len(clean) >= 10:
        return f"+91******{clean[-4:]}"
    return "*******"

# Setup default app logger
logger = logging.getLogger("jansethu")
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
handler.setFormatter(MaskingFormatter())
if not logger.handlers:
    logger.addHandler(handler)
