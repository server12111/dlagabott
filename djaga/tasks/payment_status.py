import asyncio
import logging

from aiogram import Bot

import config
from db.database import get_db
from db.queries.payments import get_pending_yookassa_payments
from utils.payment_access import grant_access_for_payment
from utils.payment_provider import verify_payment

logger = logging.getLogger(__name__)


async def payment_status_loop(bot: Bot) -> None:
    if not config.YOOKASSA_ENABLED:
        logger.info("YooKassa payment polling is disabled (keys not set)")
        return

    interval = config.YOOKASSA_POLL_INTERVAL_SECONDS
    logger.info("YooKassa payment polling started with %s second interval", interval)

    while True:
        await _check_pending_payments(bot)
        await asyncio.sleep(interval)


async def _check_pending_payments(bot: Bot) -> None:
    try:
        async with get_db() as db:
            pending_payments = await get_pending_yookassa_payments(db)

        for payment in pending_payments:
            external_payment_id = payment.get("external_payment_id", "")
            if not external_payment_id:
                continue

            verification_status = await verify_payment(external_payment_id)
            if verification_status == "succeeded":
                await grant_access_for_payment(
                    bot,
                    payment["id"],
                    granted_by="yookassa_poll",
                )
                continue

            if verification_status in {"provider_error", "misconfigured"}:
                logger.warning(
                    "Payment polling verification issue for payment %s: %s",
                    payment["id"],
                    verification_status,
                )
    except Exception as e:
        logger.error("Payment polling error: %s", e, exc_info=True)
