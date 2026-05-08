import asyncio
import logging
from aiogram import Bot

import config
from db.database import get_db
from db.queries.users import get_users_for_reminder, update_reminder_info
from keyboards.inline import kb_back_to_pricing
from texts.messages import REMINDER

logger = logging.getLogger(__name__)


async def reminder_loop(bot: Bot) -> None:
    interval = config.REMINDER_CHECK_INTERVAL_MINUTES * 60
    while True:
        await asyncio.sleep(interval)
        await _send_reminders(bot)


async def _send_reminders(bot: Bot) -> None:
    try:
        async with get_db() as db:
            users = await get_users_for_reminder(
                db,
                delay_hours=config.REMINDER_DELAY_HOURS,
                max_count=config.REMINDER_MAX_COUNT,
            )
        for user in users:
            try:
                await bot.send_message(
                    user["telegram_id"],
                    REMINDER,
                    reply_markup=kb_back_to_pricing(),
                )
                async with get_db() as db:
                    await update_reminder_info(db, user["telegram_id"])
            except Exception as e:
                logger.warning("Failed to send reminder to %s: %s", user["telegram_id"], e)
    except Exception as e:
        logger.error("Reminder loop error: %s", e)
