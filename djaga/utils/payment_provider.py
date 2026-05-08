import logging
import uuid
from typing import Literal

import requests

import config

logger = logging.getLogger(__name__)

API_BASE_URL = "https://api.yookassa.ru/v3"


class PaymentProviderError(Exception):
    pass


PaymentVerificationStatus = Literal[
    "succeeded",
    "pending",
    "canceled",
    "not_found",
    "provider_error",
    "misconfigured",
]


def _get_session() -> requests.Session:
    session = requests.Session()
    session.trust_env = False
    session.proxies = {
        "http": None,
        "https": None,
    }
    return session


def _assert_yookassa_configured() -> None:
    if not config.YOOKASSA_ENABLED:
        raise PaymentProviderError("YooKassa credentials are missing")


async def generate_payment_url(user_id: int, tier: str, payment_db_id: int) -> tuple[str, str]:
    """
    Returns (payment_url, external_payment_id).
    Payment links are generated via YooKassa HTTP API.
    """
    _assert_yookassa_configured()
    tier_info = config.TIERS[tier]

    payload = {
        "amount": {
            "value": f"{tier_info['price']}.00",
            "currency": "RUB",
        },
        "confirmation": {
            "type": "redirect",
            "return_url": config.YOOKASSA_RETURN_URL or f"https://t.me/{config.ADMIN_USERNAME}",
        },
        "capture": True,
        "description": f"HR Pro - {tier_info['label']} (user {user_id}, payment {payment_db_id})",
        "metadata": {
            "user_id": str(user_id),
            "tier": tier,
            "payment_db_id": str(payment_db_id),
        },
    }

    session = _get_session()
    try:
        response = session.post(
            f"{API_BASE_URL}/payments",
            auth=(config.YOOKASSA_SHOP_ID, config.YOOKASSA_SECRET_KEY),
            headers={"Idempotence-Key": str(uuid.uuid4())},
            json=payload,
            timeout=30,
        )
        response.raise_for_status()
        data = response.json()
        payment_url = data["confirmation"]["confirmation_url"]
        external_id = data["id"]
        logger.info("YooKassa payment created: %s for user %s", external_id, user_id)
        return payment_url, external_id
    except requests.RequestException as e:
        details = ""
        if getattr(e, "response", None) is not None:
            details = e.response.text[:500]
        logger.error("YooKassa payment creation failed: %s %s", e, details)
        raise PaymentProviderError("Failed to create YooKassa payment") from e
    finally:
        session.close()


async def verify_payment(external_payment_id: str) -> PaymentVerificationStatus:
    if not external_payment_id:
        return "not_found"

    if not config.YOOKASSA_ENABLED:
        return "misconfigured"

    session = _get_session()
    try:
        response = session.get(
            f"{API_BASE_URL}/payments/{external_payment_id}",
            auth=(config.YOOKASSA_SHOP_ID, config.YOOKASSA_SECRET_KEY),
            timeout=30,
        )

        if response.status_code == 401:
            logger.error("YooKassa verify_payment unauthorized for payment %s", external_payment_id)
            return "misconfigured"

        if response.status_code == 404:
            return "not_found"

        response.raise_for_status()
        data = response.json()
        status = data.get("status")

        if status == "succeeded":
            return "succeeded"
        if status in {"pending", "waiting_for_capture"}:
            return "pending"
        if status == "canceled":
            return "canceled"

        logger.warning("YooKassa verify_payment returned unknown status '%s' for %s", status, external_payment_id)
        return "provider_error"
    except requests.RequestException as e:
        details = ""
        if getattr(e, "response", None) is not None:
            details = e.response.text[:500]
        logger.error("YooKassa verify_payment failed: %s %s", e, details)
        return "provider_error"
    finally:
        session.close()