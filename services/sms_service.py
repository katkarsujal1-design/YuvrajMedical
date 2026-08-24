import logging
import os
import re
from dataclasses import dataclass
from typing import Optional
from urllib.parse import quote

import requests


logger = logging.getLogger(__name__)


class SmsServiceError(Exception):
    """Raised when an SMS request cannot be completed safely."""


@dataclass
class SmsResult:
    ok: bool
    message: str
    session_id: Optional[str] = None
    provider_status: Optional[str] = None


SMS_TEMPLATES = {
    "order_confirmed": "YuvrajMedical: Your order #{order_id} has been confirmed. We will notify you when it is ready for delivery.",
    "order_packed": "YuvrajMedical: Your order #{order_id} has been packed and is being prepared for dispatch.",
    "order_ready_for_delivery": "YuvrajMedical: Your order #{order_id} is ready for delivery.",
    "order_out_for_delivery": "YuvrajMedical: Your order #{order_id} is out for delivery.",
    "order_delivered": "YuvrajMedical: Your order #{order_id} has been delivered successfully. Thank you for choosing YuvrajMedical.",
    "order_cancelled": "YuvrajMedical: Your order #{order_id} has been cancelled.",
    "order_refunded": "YuvrajMedical: Refund for order #{order_id} has been completed.",
    "payment_successful": "YuvrajMedical: Payment for order #{order_id} has been verified successfully.",
    "payment_failed": "YuvrajMedical: Payment verification for order #{order_id} failed. Please contact support or try again.",
    "refund_initiated": "YuvrajMedical: Refund for order #{order_id} has been initiated.",
    "refund_completed": "YuvrajMedical: Refund for order #{order_id} has been completed.",
    "prescription_received": "YuvrajMedical: Your prescription request #{request_id} has been received for review.",
    "prescription_approved": "YuvrajMedical: Your prescription request #{request_id} has been approved.",
    "prescription_rejected": "YuvrajMedical: Your prescription request #{request_id} has been rejected. Please check your account for details.",
    "prescription_clarification": "YuvrajMedical: Your prescription request #{request_id} needs clarification. Please check your account.",
    "delivery_assigned": "YuvrajMedical: Your order #{order_id} has been assigned for delivery.",
    "delivery_out_for_delivery": "YuvrajMedical: Your order #{order_id} is out for delivery.",
    "delivery_delivered": "YuvrajMedical: Your order #{order_id} has been delivered.",
    "delivery_failed": "YuvrajMedical: Delivery for order #{order_id} could not be completed. Please contact support.",
}


def sms_enabled() -> bool:
    return os.getenv("SMS_ENABLED", "true").strip().lower() not in {"0", "false", "no", "off"}


def mask_phone(phone: str) -> str:
    digits = re.sub(r"\D", "", str(phone or ""))
    if len(digits) <= 4:
        return "****"
    return f"{'*' * max(0, len(digits) - 4)}{digits[-4:]}"


def normalize_indian_phone(phone: str) -> str:
    value = str(phone or "").strip()
    if not value:
        raise ValueError("Phone number is required.")

    digits = re.sub(r"\D", "", value)
    if digits.startswith("0091") and len(digits) == 14:
        digits = digits[4:]
    elif digits.startswith("91") and len(digits) == 12:
        digits = digits[2:]

    if len(digits) != 10 or not digits[0] in "6789":
        raise ValueError("Use a valid 10 digit Indian mobile number.")

    return f"+91{digits}"


def _api_key() -> Optional[str]:
    key = os.getenv("TWOFACTOR_API_KEY")
    if key and key.strip() and key.strip() != "replace_with_your_key":
        return key.strip()
    return None


def _timeout() -> int:
    try:
        return max(2, min(int(os.getenv("TWOFACTOR_TIMEOUT_SECONDS", "10")), 30))
    except ValueError:
        return 10


def _post_json(url: str, payload: dict, headers: Optional[dict] = None) -> dict:
    try:
        response = requests.post(url, json=payload, headers=headers or {}, timeout=_timeout())
        response.raise_for_status()
        return response.json()
    except ValueError as exc:
        raise SmsServiceError("SMS provider returned an invalid response.") from exc
    except requests.Timeout as exc:
        raise SmsServiceError("SMS provider timed out.") from exc
    except requests.HTTPError as exc:
        response = exc.response
        detail = ""
        if response is not None:
            detail = (response.text or "").strip().replace("\n", " ")[:180]
            raise SmsServiceError(f"SMS provider returned HTTP {response.status_code}: {detail}") from exc
        raise SmsServiceError("SMS provider request failed.") from exc
    except requests.RequestException as exc:
        raise SmsServiceError(f"SMS provider request failed: {exc.__class__.__name__}") from exc


def _post_json_body(url: str, payload: dict) -> dict:
    try:
        response = requests.post(url, json=payload, timeout=_timeout())
        response.raise_for_status()
        return response.json()
    except ValueError as exc:
        raise SmsServiceError("SMS provider returned an invalid response.") from exc
    except requests.Timeout as exc:
        raise SmsServiceError("SMS provider timed out.") from exc
    except requests.HTTPError as exc:
        response = exc.response
        if response is not None:
            detail = (response.text or "").strip().replace("\n", " ")[:180]
            raise SmsServiceError(f"SMS provider returned HTTP {response.status_code}: {detail}") from exc
        raise SmsServiceError("SMS provider request failed.") from exc
    except requests.RequestException as exc:
        raise SmsServiceError(f"SMS provider request failed: {exc.__class__.__name__}") from exc


def _post_empty_json(url: str) -> dict:
    try:
        response = requests.post(url, timeout=_timeout())
        response.raise_for_status()
        return response.json()
    except ValueError as exc:
        raise SmsServiceError("SMS provider returned an invalid response.") from exc
    except requests.Timeout as exc:
        raise SmsServiceError("SMS provider timed out.") from exc
    except requests.HTTPError as exc:
        response = exc.response
        if response is not None:
            detail = (response.text or "").strip().replace("\n", " ")[:180]
            raise SmsServiceError(f"SMS provider returned HTTP {response.status_code}: {detail}") from exc
        raise SmsServiceError("SMS provider request failed.") from exc
    except requests.RequestException as exc:
        raise SmsServiceError(f"SMS provider request failed: {exc.__class__.__name__}") from exc


def _get_json(url: str) -> dict:
    try:
        response = requests.get(url, timeout=_timeout())
        response.raise_for_status()
        return response.json()
    except ValueError as exc:
        raise SmsServiceError("SMS provider returned an invalid response.") from exc
    except requests.Timeout as exc:
        raise SmsServiceError("SMS provider timed out.") from exc
    except requests.HTTPError as exc:
        response = exc.response
        if response is not None:
            detail = (response.text or "").strip().replace("\n", " ")[:180]
            raise SmsServiceError(f"SMS provider returned HTTP {response.status_code}: {detail}") from exc
        raise SmsServiceError("SMS provider request failed.") from exc
    except requests.RequestException as exc:
        raise SmsServiceError(f"SMS provider request failed: {exc.__class__.__name__}") from exc


def send_otp(phone: str, purpose: str = "verification") -> SmsResult:
    normalized = normalize_indian_phone(phone)
    masked = mask_phone(normalized)

    if not sms_enabled():
        logger.info("SMS disabled: OTP would be requested for %s (%s)", masked, purpose)
        return SmsResult(True, "OTP generated in test mode.", session_id=f"test-{purpose}-{normalized[-4:]}", provider_status="test")

    key = _api_key()
    if not key:
        logger.warning("2Factor OTP not sent for %s: missing API key", masked)
        return SmsResult(False, "SMS service is not configured. Please contact support.", provider_status="missing_api_key")

    template = os.getenv("TWOFACTOR_OTP_TEMPLATE", "").strip()
    channel = os.getenv("TWOFACTOR_OTP_CHANNEL", "SMS").strip().upper()
    default_url = "https://2factor.in/API/V1/OTP/SEND" if channel else "https://2factor.in/API/V1"
    base_url = os.getenv("TWOFACTOR_OTP_URL", default_url).strip()

    try:
        if base_url.rstrip("/").endswith("/v1/sms/otp"):
            payload = {"apiKey": key, "to": normalized}
            if channel:
                payload["channel"] = channel
            if template:
                payload["template"] = template
                payload["template_name"] = template
            result = _post_json(base_url, payload, headers={"Content-Type": "application/json"})
        elif base_url.endswith("/OTP/SEND"):
            payload = {"to": normalized, "channel": channel or "SMS"}
            if template:
                payload["template"] = template
                payload["template_name"] = template
            result = _post_json(base_url, payload, headers={"X-API-Key": key, "Content-Type": "application/json"})
        else:
            legacy_template = f"/{template}" if template else ""
            result = _get_json(f"{base_url.rstrip('/')}/{key}/SMS/{normalized}/AUTOGEN{legacy_template}")
    except SmsServiceError as exc:
        logger.warning("2Factor OTP request failed for %s: %s", masked, exc)
        return SmsResult(False, str(exc), provider_status="request_failed")

    status = str(result.get("Status") or result.get("status") or "").lower()
    data = result.get("data") if isinstance(result.get("data"), dict) else {}
    session_id = (
        result.get("Details")
        or result.get("session_id")
        or result.get("sessionId")
        or data.get("session_id")
        or data.get("sessionId")
        or data.get("id")
    )
    if status in {"success", "sent"} and session_id:
        logger.info("2Factor OTP requested for %s (%s)", masked, purpose)
        return SmsResult(True, "OTP sent successfully.", session_id=str(session_id), provider_status=status)

    logger.warning("2Factor OTP rejected for %s: %s", masked, result)
    return SmsResult(False, "SMS provider rejected the OTP request.", provider_status=status or "rejected")


def send_manual_otp(phone: str, otp: str, purpose: str = "verification") -> SmsResult:
    normalized = normalize_indian_phone(phone)
    masked = mask_phone(normalized)
    otp_value = str(otp or "").strip()

    if not re.fullmatch(r"\d{4,8}", otp_value):
        return SmsResult(False, "OTP must be numeric.", provider_status="invalid_otp")

    if not sms_enabled():
        logger.info("SMS disabled: manual OTP would be sent to %s (%s)", masked, purpose)
        return SmsResult(True, "OTP generated in test mode.", session_id=f"local-{purpose}-{normalized[-4:]}", provider_status="test")

    key = _api_key()
    if not key:
        logger.warning("2Factor manual OTP not sent for %s: missing API key", masked)
        return SmsResult(False, "SMS service is not configured. Please contact support.", provider_status="missing_api_key")

    transport = os.getenv("TWOFACTOR_OTP_TRANSPORT", "otp_sms").strip().lower()
    template = os.getenv("TWOFACTOR_OTP_TEMPLATE", "").strip()
    sender_id = os.getenv("TWOFACTOR_SENDER_ID", "").strip()
    sms_number = re.sub(r"\D", "", normalized)[-10:]

    if transport == "transactional_sms":
        if not sender_id:
            return SmsResult(False, "TWOFACTOR_SENDER_ID is required for transactional SMS OTP.", provider_status="missing_sender_id")
        if not template:
            return SmsResult(False, "TWOFACTOR_OTP_TEMPLATE is required for transactional SMS OTP.", provider_status="missing_template")
        message_template = os.getenv(
            "TWOFACTOR_OTP_MESSAGE",
            "YuvrajMedical: Your OTP is {otp}. Do not share it with anyone."
        )
        message = message_template.format(otp=otp_value)
        base_url = os.getenv("TWOFACTOR_LEGACY_URL", "https://2factor.in/API/V1").strip().rstrip("/")
        url = f"{base_url}/{quote(key, safe='')}/ADDON_SERVICES/SEND/TSMS"
        payload = {
            "From": sender_id,
            "To": sms_number,
            "Msg": message,
            "TemplateName": template,
            "SendAt": "",
        }
        try:
            result = _post_json_body(url, payload)
        except SmsServiceError as exc:
            logger.warning("2Factor transactional OTP request failed for %s: %s", masked, exc)
            return SmsResult(False, str(exc), provider_status="request_failed")

        status = str(result.get("Status") or result.get("status") or "").lower()
        details = str(result.get("Details") or result.get("message") or "")
        if status in {"success", "sent", "queued", "submitted"}:
            logger.info("2Factor transactional OTP sent to %s (%s)", masked, purpose)
            return SmsResult(True, "OTP sent successfully.", session_id=f"local-{purpose}-{normalized[-4:]}", provider_status=status)

        logger.warning("2Factor transactional OTP rejected for %s: %s", masked, result)
        return SmsResult(False, details or "SMS provider rejected the OTP request.", provider_status=status or "rejected")

    base_url = os.getenv("TWOFACTOR_LEGACY_URL", "https://2factor.in/API/V1").strip().rstrip("/")
    legacy_template = f"/{quote(template, safe='')}" if template else ""
    url = f"{base_url}/{quote(key, safe='')}/SMS/{sms_number}/{otp_value}{legacy_template}"

    try:
        result = _post_empty_json(url)
    except SmsServiceError as exc:
        logger.warning("2Factor manual OTP request failed for %s: %s", masked, exc)
        return SmsResult(False, str(exc), provider_status="request_failed")

    status = str(result.get("Status") or result.get("status") or "").lower()
    details = str(result.get("Details") or result.get("message") or "")
    if status in {"success", "sent"}:
        logger.info("2Factor manual OTP sent to %s (%s)", masked, purpose)
        return SmsResult(True, "OTP sent successfully.", session_id=f"local-{purpose}-{normalized[-4:]}", provider_status=status)

    logger.warning("2Factor manual OTP rejected for %s: %s", masked, result)
    return SmsResult(False, details or "SMS provider rejected the OTP request.", provider_status=status or "rejected")


def verify_otp(session_id: str, otp: str) -> SmsResult:
    otp_value = str(otp or "").strip()
    if not re.fullmatch(r"\d{4,8}", otp_value):
        return SmsResult(False, "Enter a valid OTP.")

    if not session_id:
        return SmsResult(False, "OTP session is missing or expired.")

    if not sms_enabled():
        expected = os.getenv("SMS_TEST_OTP", "123456")
        ok = otp_value == expected
        logger.info("SMS disabled: OTP verification %s for test session", "succeeded" if ok else "failed")
        return SmsResult(ok, "OTP verified." if ok else "Invalid OTP.", provider_status="test")

    key = _api_key()
    if not key:
        logger.warning("2Factor OTP verify failed: missing API key")
        return SmsResult(False, "SMS service is not configured. Please contact support.", provider_status="missing_api_key")

    base_url = os.getenv("TWOFACTOR_VERIFY_URL", "https://2factor.in/API/V1").strip().rstrip("/")
    try:
        if base_url.endswith("/OTP/VERIFY"):
            result = _post_json(
                base_url,
                {"session_id": session_id, "otp": otp_value},
                headers={"X-API-Key": key, "Content-Type": "application/json"},
            )
        else:
            result = _get_json(f"{base_url}/{key}/SMS/VERIFY/{session_id}/{otp_value}")
    except SmsServiceError as exc:
        logger.warning("2Factor OTP verify request failed: %s", exc)
        return SmsResult(False, str(exc), provider_status="request_failed")

    status = str(result.get("Status") or result.get("status") or "").lower()
    details = str(result.get("Details") or result.get("message") or "").lower()
    if status in {"success", "verified"} or details == "otp matched":
        logger.info("2Factor OTP verification succeeded")
        return SmsResult(True, "OTP verified.", provider_status=status)

    logger.info("2Factor OTP verification failed with provider status %s", status or "unknown")
    return SmsResult(False, "Invalid or expired OTP.", provider_status=status or "failed")


def render_sms_template(template_key: str, **context) -> str:
    template = SMS_TEMPLATES.get(template_key)
    if not template:
        raise ValueError(f"Unknown SMS template: {template_key}")
    return template.format(**context)


def send_transactional_sms(phone: str, message: str, template_key: Optional[str] = None) -> SmsResult:
    normalized = normalize_indian_phone(phone)
    masked = mask_phone(normalized)

    if not sms_enabled():
        logger.info("SMS disabled: transactional SMS would be sent to %s using %s", masked, template_key or "freeform")
        return SmsResult(True, "SMS skipped in test mode.", provider_status="test")

    key = _api_key()
    if not key:
        logger.warning("2Factor transactional SMS not sent to %s: missing API key", masked)
        return SmsResult(False, "SMS service is not configured.", provider_status="missing_api_key")

    url = os.getenv("TWOFACTOR_TRANSACTIONAL_URL", "https://2factor.in/API/V1/TRANSACTIONAL/SEND").strip()
    sender_id = os.getenv("TWOFACTOR_SENDER_ID", "").strip()
    entity_id = os.getenv("TWOFACTOR_ENTITY_ID", "").strip()
    template_id = os.getenv(f"TWOFACTOR_TEMPLATE_{(template_key or '').upper()}", "").strip()
    fallback_template = os.getenv("TWOFACTOR_TRANSACTIONAL_TEMPLATE", "").strip()

    payload = {
        "to": normalized,
        "message": message,
    }
    if sender_id:
        payload["sender_id"] = sender_id
    if entity_id:
        payload["entity_id"] = entity_id
    if template_id:
        payload["template_id"] = template_id
    elif fallback_template:
        payload["template"] = fallback_template

    try:
        result = _post_json(url, payload, headers={"X-API-Key": key, "Content-Type": "application/json"})
    except SmsServiceError as exc:
        logger.warning("2Factor transactional SMS failed for %s: %s", masked, exc)
        return SmsResult(False, str(exc), provider_status="request_failed")

    status = str(result.get("Status") or result.get("status") or "").lower()
    if status in {"success", "sent", "queued", "submitted"}:
        logger.info("2Factor transactional SMS sent to %s using %s", masked, template_key or "freeform")
        return SmsResult(True, "SMS sent.", provider_status=status)

    logger.warning("2Factor transactional SMS rejected for %s: %s", masked, result)
    return SmsResult(False, "SMS provider rejected the message.", provider_status=status or "rejected")
