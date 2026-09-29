"""High-risk SMS alerts via Twilio. Credentials come from shared root .env."""

from twilio.base.exceptions import TwilioException
from twilio.rest import Client

from .config import get_env


def normalize_phone(phone: str) -> str:
    digits = "".join(ch for ch in phone if ch.isdigit() or ch == "+")
    if digits.startswith("+"):
        return digits
    return f"+{digits}"


def get_twilio_client() -> tuple[Client | None, str | None, str | None]:
    account_sid = get_env("TWILIO_ACCOUNT_SID", "") or ""
    auth_token = get_env("TWILIO_AUTH_TOKEN", "") or ""
    from_number = get_env("TWILIO_PHONE_NUMBER", "") or ""

    if not account_sid or not auth_token or not from_number:
        return None, from_number or None, "Twilio env vars missing (TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_PHONE_NUMBER)"

    return Client(account_sid, auth_token), from_number, None


def send_sms_alert(*, phone: str, text: str) -> tuple[bool, str]:
    if not phone:
        return False, "Phone number missing"

    client, from_number, config_error = get_twilio_client()
    if client is None:
        return False, config_error or "Twilio is not configured"

    try:
        message = client.messages.create(
            body=text,
            from_=from_number,
            to=normalize_phone(phone),
        )
        return True, f"SMS sent ({message.sid})"
    except TwilioException as exc:
        return False, f"Twilio error: {exc}"
    except Exception as exc:
        return False, f"SMS send failed: {exc}"


def build_high_risk_message(
    *,
    name: str,
    severity: str,
    risk: float,
    latitude: float,
    longitude: float,
) -> str:
    return (
        f"UTTARAKHAND LANDSLIDE ALERT for {name}: landslide risk near you is "
        f"{severity} ({risk:.1f}/100) at {latitude:.5f}, {longitude:.5f}. "
        f"Avoid mountain roads, hill cuts & valley slopes. Move to safer ground immediately."
    )
