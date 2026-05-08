"""
Aiohttp web server for receiving YooKassa payment notifications.

YooKassa sends POST to /yookassa/webhook when a payment status changes.
Configure the webhook URL in your YooKassa dashboard:
  https://<YOOKASSA_WEBHOOK_HOST>/yookassa/webhook

Requirements:
  - Server must be publicly accessible (white IP or domain)
  - For local testing use ngrok: ngrok http 8080
"""

import json
import logging
from aiohttp import web
from aiogram import Bot

import config
from db.database import get_db
from db.queries.payments import get_payment
from utils.payment_access import grant_access_for_payment

logger = logging.getLogger(__name__)


async def handle_yookassa_webhook(request: web.Request) -> web.Response:
    bot: Bot = request.app["bot"]

    try:
        body = await request.json()
    except Exception:
        return web.Response(status=400, text="Invalid JSON")

    event_type = body.get("event", "")
    if event_type != "payment.succeeded":
        return web.Response(status=200, text="OK")

    try:
        payment_obj = body.get("object", {})
        external_id = payment_obj.get("id", "")
        status = payment_obj.get("status", "")
        metadata = payment_obj.get("metadata", {})

        if status != "succeeded":
            return web.Response(status=200, text="OK")

        payment_db_id = int(metadata.get("payment_db_id", 0))
        user_telegram_id = int(metadata.get("user_id", 0))

        if not payment_db_id or not user_telegram_id:
            logger.warning("Webhook: missing metadata in payment %s", external_id)
            return web.Response(status=200, text="OK")

        async with get_db() as db:
            payment = await get_payment(db, payment_db_id)
            if not payment:
                logger.warning("Webhook: payment %s not found in DB", payment_db_id)
                return web.Response(status=200, text="OK")

            stored_external_id = payment.get("external_payment_id") or ""
            if not stored_external_id or stored_external_id != external_id:
                logger.warning(
                    "Webhook: external payment id mismatch for payment %s (stored=%s, incoming=%s)",
                    payment_db_id,
                    stored_external_id,
                    external_id,
                )
                return web.Response(status=200, text="OK")

            if payment["status"] == "confirmed":
                return web.Response(status=200, text="OK")

        granted = await grant_access_for_payment(
            bot,
            payment_db_id,
            granted_by="yookassa_webhook",
        )
        if granted:
            logger.info("Webhook: access granted to user %s for payment %s", user_telegram_id, payment_db_id)

    except Exception as e:
        logger.error("Webhook processing error: %s", e, exc_info=True)
        return web.Response(status=500, text="Internal error")

    return web.Response(status=200, text="OK")


async def start_webhook_server(bot: Bot) -> None:
    if not config.YOOKASSA_WEBHOOK_ENABLED:
        logger.info("YooKassa webhook server not started (disabled by config)")
        return

    if not config.YOOKASSA_ENABLED or not config.YOOKASSA_WEBHOOK_HOST:
        logger.info("YooKassa webhook server not started (keys or host not set)")
        return

    app = web.Application()
    app["bot"] = bot
    app.router.add_post("/yookassa/webhook", handle_yookassa_webhook)

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", config.YOOKASSA_WEBHOOK_PORT)
    await site.start()
    logger.info(
        "YooKassa webhook server started on port %s → %s/yookassa/webhook",
        config.YOOKASSA_WEBHOOK_PORT,
        config.YOOKASSA_WEBHOOK_HOST,
    )
