import subprocess
import sys

subprocess.run(
    [sys.executable, "-m", "pip", "install", "-q",
     "aiosqlite", "python-dotenv", "matplotlib", "pillow"],
    check=True,
)

import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import BotCommand, MenuButtonCommands

import config
from db.database import init_db
from handlers import admin, errors, funnel, payment, start
from middlewares.user_middleware import UserMiddleware
from tasks.reminders import reminder_loop
from tasks.payment_status import payment_status_loop
from tasks.subscription_expiry import subscription_expiry_loop
from webhook.server import start_webhook_server

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


async def main() -> None:
    await init_db()
    logger.info("Database initialized")

    bot = Bot(token=config.BOT_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())

    dp.update.middleware(UserMiddleware())

    dp.include_router(admin.router)
    dp.include_router(start.router)
    dp.include_router(funnel.router)
    dp.include_router(payment.router)
    dp.include_router(errors.router)

    await bot.set_my_commands([BotCommand(command="start", description="Запустить бота")])
    await bot.set_chat_menu_button(menu_button=MenuButtonCommands())
    await bot.delete_webhook(drop_pending_updates=False)

    asyncio.create_task(reminder_loop(bot))
    logger.info("Reminder loop started")

    asyncio.create_task(payment_status_loop(bot))
    logger.info("Payment polling loop started")

    asyncio.create_task(subscription_expiry_loop(bot))
    logger.info("Subscription expiry check loop started")

    if config.YOOKASSA_WEBHOOK_ENABLED:
        asyncio.create_task(start_webhook_server(bot))
        logger.info("YooKassa webhook server task started")
    else:
        logger.info("YooKassa webhook server disabled, polling mode only")

    logger.info("Bot started, polling...")
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())


if __name__ == "__main__":
    asyncio.run(main())
