import asyncio
import logging

from aiogram import Bot

import config
from db.database import get_db
from db.queries.subscriptions import expire_old_subscriptions

logger = logging.getLogger(__name__)


async def subscription_expiry_loop(bot: Bot) -> None:
    interval = config.SUBSCRIPTION_EXPIRY_CHECK_INTERVAL_MINUTES * 60
    logger.info(
        "Subscription expiry check loop started with %d minute interval",
        config.SUBSCRIPTION_EXPIRY_CHECK_INTERVAL_MINUTES,
    )
    while True:
        await asyncio.sleep(interval)
        await _check_expired_subscriptions(bot)


async def _check_expired_subscriptions(bot: Bot) -> None:
    try:
        async with get_db() as db:
            expired = await expire_old_subscriptions(db)
        if expired:
            logger.info("Expired and marked %d subscription(s)", expired)
            for user_tg_id in expired:
                try:
                    await bot.send_message(
                        user_tg_id,
                        "☹️ Твой доступ к HR Pro истёк.\n"
                        "Выбери тариф для продления: /start",
                    )
                except Exception as e:
                    logger.warning("Failed to notify user %s about expiry: %s", user_tg_id, e)
    except Exception as e:
        logger.error("Subscription expiry check error: %s", e, exc_info=True)
