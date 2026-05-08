import logging

from aiogram import Bot

import config
from db.database import get_db
from db.queries.payments import confirm_payment, get_payment
from db.queries.subscriptions import create_subscription, link_subscription_to_payment
from db.queries.users import get_user_by_id, update_funnel_stage
from texts.messages import ACCESS_GRANTED, ACCESS_GRANTED_VIP, ADMIN_PAYMENT_CONFIRMED

logger = logging.getLogger(__name__)


def build_access_text(tier: str) -> str:
    template = ACCESS_GRANTED_VIP if tier == "vip" else ACCESS_GRANTED
    return template.format(
        channel_link=config.CHANNEL_INVITE_LINK,
        vacancy_link=config.VACANCY_GROUP_INVITE_LINK,
        admin_username=config.ADMIN_USERNAME,
    )


def build_admin_payment_text(user: dict, payment: dict) -> str:
    name = f"{user.get('first_name') or ''} {user.get('last_name') or ''}".strip()
    username = f"@{user['username']}" if user.get("username") else "без username"
    user_info = f"{name} ({username}) [<code>{user['telegram_id']}</code>]"
    tier_label = config.TIERS[payment["tier"]]["label"]
    return ADMIN_PAYMENT_CONFIRMED.format(
        user_info=user_info,
        tier_label=tier_label,
        price=payment["amount_rub"],
        payment_id=payment["id"],
    )


async def notify_admins_about_confirmed_payment(bot: Bot, user: dict, payment: dict) -> None:
    admin_text = build_admin_payment_text(user, payment)
    for admin_id in config.ADMIN_IDS:
        try:
            await bot.send_message(
                admin_id,
                admin_text,
                parse_mode="HTML",
            )
        except Exception:
            logger.warning(
                "Failed to notify admin %s about confirmed payment %s",
                admin_id,
                payment["id"],
            )


async def grant_access_for_payment(
    bot: Bot,
    payment_id: int,
    *,
    notify_user: bool = True,
    granted_by: str = "payment",
) -> bool:
    async with get_db() as db:
        payment = await get_payment(db, payment_id)
        if not payment:
            logger.warning("Payment %s not found while granting access", payment_id)
            return False

        if payment["status"] == "confirmed":
            return False

        user = await get_user_by_id(db, payment["user_id"])
        if not user:
            logger.warning("User %s not found for payment %s", payment["user_id"], payment_id)
            return False

        subscription_id = await create_subscription(
            db,
            user["id"],
            payment["tier"],
            granted_by=granted_by,
        )
        await confirm_payment(db, payment_id, subscription_id)
        await link_subscription_to_payment(db, subscription_id, payment_id)
        await update_funnel_stage(db, user["telegram_id"], "paid")

    if notify_user:
        await bot.send_message(
            user["telegram_id"],
            build_access_text(payment["tier"]),
            parse_mode="HTML",
        )

    await notify_admins_about_confirmed_payment(bot, user, payment)

    logger.info("Access granted for payment %s via %s", payment_id, granted_by)
    return True
