import re

def normalize_phone_number(raw_phone: str) -> str:
    """
    Centralized Indian phone-number normalization utility.
    Converts inputs like:
      - +919876543210
      - 919876543210
      - 09876543210
      - 9876543210
      - +91 98765-43210
    into the canonical E.164 representation: '+919876543210'.
    """
    if not raw_phone:
        return ""

    # Remove whitespace, hyphens, parentheses, dots
    cleaned = re.sub(r'[\s\-\(\)\.]', '', str(raw_phone).strip())

    # Handle leading +
    if cleaned.startswith('+'):
        digits_only = cleaned[1:]
    else:
        digits_only = cleaned

    if digits_only.startswith('91') and len(digits_only) == 12:
        digits_10 = digits_only[2:]
    elif digits_only.startswith('0') and len(digits_only) == 11:
        digits_10 = digits_only[1:]
    elif len(digits_only) == 10:
        digits_10 = digits_only
    else:
        # Fallback if invalid or international format
        return cleaned if cleaned.startswith('+') else f"+{cleaned}"

    return f"+91{digits_10}"
