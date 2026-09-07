"""Validation shared by registration's OTP and persistence boundaries."""
import re
import unicodedata


def validate_registration(data):
    """Return a user-facing error, or None; normalize PAN in place."""
    if data.get("role") not in {"customer", "staff"}:
        return "Please select a valid role."
    if not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", data.get("email", "")):
        return "Please enter a valid email address."
    if data.get("role") != "staff":
        return None
    age = data.get("age", "")
    if age and (not re.fullmatch(r"[0-9]{1,3}", age) or not 1 <= int(age) <= 120):
        return "Age must be a whole number between 1 and 120."
    if data.get("gender", "") not in {"", "Male", "Female", "Other", "Prefer not to say"}:
        return "Please select a valid gender."
    aadhar = data.get("aadhar", "")
    if aadhar and not re.fullmatch(r"[2-9][0-9]{11}", aadhar):
        return "Aadhaar must contain 12 digits and start with 2–9."
    data["pan"] = data.get("pan", "").upper()
    if data["pan"] and not re.fullmatch(r"[A-Z]{5}[0-9]{4}[A-Z]", data["pan"]):
        return "PAN must contain five letters, four digits, and one letter (for example, ABCDE1234F)."
    for field, limit, punctuation in (("education", 150, " .,'-/()&+"),):
        value = data.get(field, "")
        if value and (len(value) > limit or not any(c.isalpha() for c in value) or
                      any(not (c.isalpha() or unicodedata.category(c).startswith("M") or
                               c in punctuation or (field == "education" and c in "0123456789")) for c in value)):
            return f"Please enter valid {field} text (up to {limit} characters)."
    return None
