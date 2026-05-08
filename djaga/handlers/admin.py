import asyncio
import logging

from aiogram import Bot, F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import BufferedInputFile, CallbackQuery, Message

import config
from db.database import get_db
from db.queries.stats import (
    get_all_user_telegram_ids,
    get_earnings_by_tier,
    get_purchase_stats,
    get_total_user_count,
    get_user_registrations,
)
from db.queries.settings import get_setting, set_settings
from db.queries.subscriptions import (
    extend_subscription,
    get_user_subscriptions,
    update_subscription_status,
)
from db.queries.users import get_user
from keyboards.admin import kb_admin_main, kb_admin_periods, kb_admin_purchase_filters, kb_broadcast_confirm, kb_tariff_menu, kb_tariff_user_actions, kb_tariff_extend_days, kb_tariff_choose_tier, kb_tariff_create_confirm
from states.admin import AdminStates
from utils.charts import create_bar_chart
from utils.env_file import set_env_values
from utils.video import get_video_file_id_and_type

router = Router()
logger = logging.getLogger(__name__)

PERIOD_NAMES = {
    "day": "за день",
    "week": "за 7 дней",
    "month": "за месяц",
    "year": "за год",
}
TIER_NAMES = {
    "all": "все тарифы",
    "test_1r": "Тест (1 рубль)",
    "test_7d": "Тест (7 дней)",
    "pro_30d": "Профи (30 дней)",
    "vip": "VIP",
}


def _is_admin(user_id: int) -> bool:
    return user_id in config.ADMIN_IDS


@router.message(Command("admin"))
async def cmd_admin(message: Message, state: FSMContext) -> None:
    if not _is_admin(message.from_user.id):
        return
    await state.set_state(AdminStates.MAIN)
    await message.answer(
        "<b>Админ-панель HR Pro</b>",
        parse_mode="HTML",
        reply_markup=kb_admin_main(),
    )


@router.callback_query(F.data == "adm:back")
async def cb_adm_back(callback: CallbackQuery, state: FSMContext) -> None:
    if not _is_admin(callback.from_user.id):
        return
    await state.set_state(AdminStates.MAIN)
    try:
        await callback.message.delete()
    except Exception:
        pass
    await callback.message.answer(
        "<b>Админ-панель HR Pro</b>",
        parse_mode="HTML",
        reply_markup=kb_admin_main(),
    )
    await callback.answer()


@router.callback_query(F.data == "adm:users")
async def cb_adm_users(callback: CallbackQuery, state: FSMContext) -> None:
    if not _is_admin(callback.from_user.id):
        return
    await state.set_state(AdminStates.USER_STATS)
    await state.update_data(period="day")
    try:
        await callback.message.delete()
    except Exception:
        pass
    await _send_user_stats(callback, "day")
    await callback.answer()


@router.callback_query(F.data.startswith("adm_usr:period:"))
async def cb_adm_usr_period(callback: CallbackQuery, state: FSMContext) -> None:
    if not _is_admin(callback.from_user.id):
        return
    period = callback.data.split(":")[2]
    try:
        await callback.message.delete()
    except Exception:
        pass
    await _send_user_stats(callback, period)
    await callback.answer()


async def _send_user_stats(callback: CallbackQuery, period: str) -> None:
    async with get_db() as db:
        rows = await get_user_registrations(db, period)
        total = await get_total_user_count(db)

    labels = [r["label"] for r in rows] or ["—"]
    values = [r["count"] for r in rows] or [0]
    title = f"Новые пользователи {PERIOD_NAMES[period]}"

    chart = create_bar_chart(labels, values, title, color="#89b4fa")
    photo = BufferedInputFile(chart.read(), filename="users.png")

    caption = (
        f"<b>Статистика пользователей {PERIOD_NAMES[period]}</b>\n\n"
        f"Новых за период: <b>{sum(values)}</b>\n"
        f"Всего в боте: <b>{total}</b>"
    )
    await callback.message.answer_photo(
        photo=photo,
        caption=caption,
        parse_mode="HTML",
        reply_markup=kb_admin_periods("adm_usr", active=period),
    )


@router.callback_query(F.data == "adm:purchases")
async def cb_adm_purchases(callback: CallbackQuery, state: FSMContext) -> None:
    if not _is_admin(callback.from_user.id):
        return
    await state.set_state(AdminStates.PURCHASE_STATS)
    try:
        await callback.message.delete()
    except Exception:
        pass
    await _send_purchase_stats(callback, "day", "all")
    await callback.answer()


@router.callback_query(F.data.startswith("adm_buy:period:"))
async def cb_adm_buy_period(callback: CallbackQuery, state: FSMContext) -> None:
    if not _is_admin(callback.from_user.id):
        return
    parts = callback.data.split(":")
    period, tier = parts[2], parts[3]
    try:
        await callback.message.delete()
    except Exception:
        pass
    await _send_purchase_stats(callback, period, tier)
    await callback.answer()


@router.callback_query(F.data.startswith("adm_buy:tier:"))
async def cb_adm_buy_tier(callback: CallbackQuery, state: FSMContext) -> None:
    if not _is_admin(callback.from_user.id):
        return
    parts = callback.data.split(":")
    period, tier = parts[2], parts[3]
    try:
        await callback.message.delete()
    except Exception:
        pass
    await _send_purchase_stats(callback, period, tier)
    await callback.answer()


async def _send_purchase_stats(callback: CallbackQuery, period: str, tier: str) -> None:
    async with get_db() as db:
        rows = await get_purchase_stats(db, period, tier)
        earnings = await get_earnings_by_tier(db)

    labels = [r["label"] for r in rows] or ["—"]
    values = [r["count"] for r in rows] or [0]
    tier_label = TIER_NAMES.get(tier, tier)
    title = f"Покупки {PERIOD_NAMES[period]} — {tier_label}"

    chart = create_bar_chart(labels, values, title, color="#a6e3a1")
    photo = BufferedInputFile(chart.read(), filename="purchases.png")

    grand_total = earnings.pop("__total__", 0)
    lines = []
    tier_map = {
        "test_7d": "Тест",
        "pro_30d": "Профи",
        "vip": "VIP",
    }
    for current_tier, data in earnings.items():
        lines.append(
            f"{tier_map.get(current_tier, current_tier)}: {data['count']} шт. — "
            f"<b>{data['total']:,} ₽</b>".replace(",", " ")
        )

    earnings_text = "\n".join(lines) if lines else "Пока нет продаж"
    caption = (
        f"<b>Статистика покупок {PERIOD_NAMES[period]}</b>\n"
        f"Тариф: <b>{tier_label}</b>\n\n"
        f"Покупок за период: <b>{sum(values)}</b>\n\n"
        f"<b>Заработок по тарифам:</b>\n{earnings_text}\n\n"
        f"<b>Итого со всех тарифов: {grand_total:,} ₽</b>".replace(",", " ")
    )
    await callback.message.answer_photo(
        photo=photo,
        caption=caption,
        parse_mode="HTML",
        reply_markup=kb_admin_purchase_filters(active_period=period, active_tier=tier),
    )


@router.callback_query(F.data == "adm:broadcast")
async def cb_adm_broadcast(callback: CallbackQuery, state: FSMContext) -> None:
    if not _is_admin(callback.from_user.id):
        return
    await state.set_state(AdminStates.BROADCAST_WAITING)
    try:
        await callback.message.delete()
    except Exception:
        pass
    await callback.message.answer(
        "<b>Рассылка</b>\n\n"
        "Отправь сообщение для рассылки.\n"
        "Поддерживается: текст, фото, видео.\n\n"
        "Введи /admin для отмены.",
        parse_mode="HTML",
    )
    await callback.answer()


@router.message(AdminStates.BROADCAST_WAITING)
async def msg_broadcast_content(message: Message, state: FSMContext) -> None:
    if not _is_admin(message.from_user.id):
        return

    await state.update_data(
        bc_chat_id=message.chat.id,
        bc_message_id=message.message_id,
    )
    await state.set_state(AdminStates.BROADCAST_CONFIRM)

    await message.answer(
        "Вот так будет выглядеть рассылка.\n\nПодтвердить отправку всем пользователям?",
        reply_markup=kb_broadcast_confirm(),
    )


@router.callback_query(F.data == "adm_bc:confirm")
async def cb_bc_confirm(callback: CallbackQuery, state: FSMContext, bot: Bot) -> None:
    if not _is_admin(callback.from_user.id):
        return

    data = await state.get_data()
    bc_chat_id = data.get("bc_chat_id")
    bc_message_id = data.get("bc_message_id")
    await state.set_state(AdminStates.MAIN)

    try:
        await callback.message.delete()
    except Exception:
        pass

    async with get_db() as db:
        user_ids = await get_all_user_telegram_ids(db)

    status_msg = await callback.message.answer(
        f"Начинаю рассылку... 0 / {len(user_ids)}"
    )

    sent, failed = 0, 0
    for i, uid in enumerate(user_ids):
        try:
            await bot.copy_message(
                chat_id=uid,
                from_chat_id=bc_chat_id,
                message_id=bc_message_id,
            )
            sent += 1
        except Exception:
            failed += 1

        if (i + 1) % 20 == 0:
            try:
                await status_msg.edit_text(
                    f"Рассылка... {i + 1} / {len(user_ids)}"
                )
            except Exception:
                pass
        await asyncio.sleep(0.05)

    await status_msg.edit_text(
        f"Рассылка завершена.\n\n"
        f"Отправлено: <b>{sent}</b>\n"
        f"Ошибок: <b>{failed}</b>",
        parse_mode="HTML",
        reply_markup=kb_admin_main(),
    )
    await callback.answer()


@router.callback_query(F.data == "adm_bc:cancel")
async def cb_bc_cancel(callback: CallbackQuery, state: FSMContext) -> None:
    if not _is_admin(callback.from_user.id):
        return
    await state.set_state(AdminStates.MAIN)
    try:
        await callback.message.delete()
    except Exception:
        pass
    await callback.message.answer("Рассылка отменена.", reply_markup=kb_admin_main())
    await callback.answer()


@router.callback_query(F.data == "adm:tariff_menu")
async def cb_adm_tariff_menu(callback: CallbackQuery, state: FSMContext) -> None:
    if not _is_admin(callback.from_user.id):
        return
    await state.set_state(AdminStates.TARIFF_MENU)
    try:
        await callback.message.delete()
    except Exception:
        pass
    await callback.message.answer(
        "<b>Управление тарифами</b>\n\nВыбери действие:",
        parse_mode="HTML",
        reply_markup=kb_tariff_menu(),
    )
    await callback.answer()


@router.callback_query(F.data == "adm:tariff_find")
async def cb_adm_tariff_find(callback: CallbackQuery, state: FSMContext) -> None:
    if not _is_admin(callback.from_user.id):
        return
    await state.set_state(AdminStates.TARIFF_FIND_USER)
    try:
        await callback.message.delete()
    except Exception:
        pass
    await callback.message.answer(
        "<b>Поиск пользователя</b>\n\n"
        "Введи Telegram ID или username (с @) пользователя:",
        parse_mode="HTML",
    )
    await callback.answer()


@router.message(AdminStates.TARIFF_FIND_USER)
async def msg_tariff_find_user(message: Message, state: FSMContext) -> None:
    if not _is_admin(message.from_user.id):
        return

    query = message.text.strip()
    user = None

    if query.lstrip("-").isdigit():
        async with get_db() as db:
            user = await get_user(db, int(query))
    elif query.startswith("@"):
        async with get_db() as db:
            cursor = await db.execute(
                "SELECT * FROM users WHERE username = ?", (query[1:],)
            )
            row = await cursor.fetchone()
            user = dict(row) if row else None
    else:
        async with get_db() as db:
            cursor = await db.execute(
                "SELECT * FROM users WHERE username = ? OR CAST(telegram_id AS TEXT) = ?",
                (query, query),
            )
            row = await cursor.fetchone()
            user = dict(row) if row else None

    if not user:
        await message.answer("Пользователь не найден. Попробуй ещё раз:")
        return

    subs = await get_user_subscriptions(db, user["id"])

    await state.set_state(AdminStates.TARIFF_USER_FOUND)
    await state.update_data(found_user_id=user["id"], found_tg_id=user["telegram_id"])

    name = f"{user.get('first_name', '')} {user.get('last_name', '')}".strip() or "—"
    lines = [f"<b>Пользователь:</b> {name} (<code>{user['telegram_id']}</code>)"]
    lines.append(f"<b>Username:</b> @{user['username']}" if user.get("username") else "")

    if not subs:
        lines.append("\n<i>Нет подписок</i>")
    else:
        lines.append("")
        for s in subs:
            status_icon = {"active": "✅", "expired": "❌", "cancelled": "🚫"}.get(s["status"], "⚪")
            expires_str = s["expires_at"][:16] if s["expires_at"] else "∞"
            tier_label = config.TIERS.get(s["tier"], {}).get("label", s["tier"])
            lines.append(
                f"{status_icon} <b>{tier_label}</b> — {s['status']}\n"
                f"   истекает: {expires_str} | id={s['id']}"
            )

    lines.append("\nВыбери подписку для действия:")

    text = "\n".join(lines)
    await message.answer(text, parse_mode="HTML")

    if subs:
        for sub in subs:
            await message.answer(
                f"Подписка #{sub['id']}: {config.TIERS.get(sub['tier'], {}).get('label', sub['tier'])}",
                reply_markup=kb_tariff_user_actions(sub["id"], sub["status"]),
            )
    await message.answer("Или создай новую:", reply_markup=kb_tariff_choose_tier())


@router.callback_query(F.data.startswith("adm_t:extend:"))
async def cb_adm_tariff_extend(callback: CallbackQuery, state: FSMContext) -> None:
    if not _is_admin(callback.from_user.id):
        return
    subscription_id = int(callback.data.split(":")[2])
    await state.update_data(tariff_sub_id=subscription_id)
    await state.set_state(AdminStates.TARIFF_EXTEND_DAYS)
    try:
        await callback.message.delete()
    except Exception:
        pass
    await callback.message.answer(
        f"Продление подписки #{subscription_id}\n\nВыбери количество дней:",
        reply_markup=kb_tariff_extend_days(subscription_id),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("adm_t:extdays:"))
async def cb_adm_tariff_extdays(callback: CallbackQuery, state: FSMContext) -> None:
    if not _is_admin(callback.from_user.id):
        return
    parts = callback.data.split(":")
    subscription_id = int(parts[2])
    days = int(parts[3])

    data = await state.get_data()
    user_tg_id = data.get("found_tg_id")

    await extend_subscription(None, subscription_id, days)

    await state.set_state(AdminStates.TARIFF_USER_FOUND)
    try:
        await callback.message.delete()
    except Exception:
        pass
    await callback.message.answer(
        f"✅ Подписка #{subscription_id} продлена на {days} дн.",
        reply_markup=kb_admin_main(),
    )

    if user_tg_id:
        try:
            await callback.bot.send_message(
                user_tg_id,
                f"✅ Твоя подписка продлена на {days} дн. Спасибо!",
            )
        except Exception:
            pass
    await callback.answer()


@router.callback_query(F.data.startswith("adm_t:revoke:"))
async def cb_adm_tariff_revoke(callback: CallbackQuery, state: FSMContext) -> None:
    if not _is_admin(callback.from_user.id):
        return
    subscription_id = int(callback.data.split(":")[2])

    data = await state.get_data()
    user_tg_id = data.get("found_tg_id")

    await update_subscription_status(None, subscription_id, "cancelled")

    await state.set_state(AdminStates.TARIFF_USER_FOUND)
    try:
        await callback.message.delete()
    except Exception:
        pass
    await callback.message.answer(
        f"🚫 Подписка #{subscription_id} отключена.",
        reply_markup=kb_admin_main(),
    )

    if user_tg_id:
        try:
            await callback.bot.send_message(
                user_tg_id,
                "🚫 Твой доступ к HR Pro был отключён администратором.",
            )
        except Exception:
            pass
    await callback.answer()


@router.callback_query(F.data.startswith("adm_t:activate:"))
async def cb_adm_tariff_activate(callback: CallbackQuery, state: FSMContext) -> None:
    if not _is_admin(callback.from_user.id):
        return
    subscription_id = int(callback.data.split(":")[2])

    data = await state.get_data()
    user_tg_id = data.get("found_tg_id")

    await update_subscription_status(None, subscription_id, "active")

    await state.set_state(AdminStates.TARIFF_USER_FOUND)
    try:
        await callback.message.delete()
    except Exception:
        pass
    await callback.message.answer(
        f"✅ Подписка #{subscription_id} активирована.",
        reply_markup=kb_admin_main(),
    )

    if user_tg_id:
        try:
            await callback.bot.send_message(
                user_tg_id,
                "✅ Доступ к HR Pro восстановлен!",
            )
        except Exception:
            pass
    await callback.answer()


@router.callback_query(F.data.startswith("adm_t:ctier:"))
async def cb_adm_tariff_ctier(callback: CallbackQuery, state: FSMContext) -> None:
    if not _is_admin(callback.from_user.id):
        return
    tier_id = callback.data.split(":")[2]
    await state.update_data(new_sub_tier=tier_id)
    await state.set_state(AdminStates.TARIFF_CREATE_TIER)
    try:
        await callback.message.delete()
    except Exception:
        pass
    tier_label = config.TIERS[tier_id]["label"]
    await callback.message.answer(
        f"<b>Создание подписки</b>\n\n"
        f"Тариф: <b>{tier_label}</b>\n\n"
        f"Введи Telegram ID пользователя:",
        parse_mode="HTML",
    )
    await callback.answer()


@router.message(AdminStates.TARIFF_CREATE_TIER)
async def msg_tariff_create_user_id(message: Message, state: FSMContext) -> None:
    if not _is_admin(message.from_user.id):
        return

    query = message.text.strip()
    if not query.lstrip("-").isdigit():
        await message.answer("Некорректный Telegram ID. Введи числовой ID:")
        return

    user = await get_user(None, int(query))
    if not user:
        await message.answer("Пользователь с таким Telegram ID не найден. Введи другой ID:")
        return

    data = await state.get_data()
    tier_id = data["new_sub_tier"]
    tier_label = config.TIERS[tier_id]["label"]

    await state.update_data(new_sub_user_id=user["id"])
    await state.set_state(AdminStates.TARIFF_CREATE_DAYS)

    await message.answer(
        f"<b>Подтверждение</b>\n\n"
        f"Пользователь: <b>{user.get('first_name', '')} {user.get('last_name', '')}</b> "
        f"(<code>{user['telegram_id']}</code>)\n"
        f"Тариф: <b>{tier_label}</b>\n\n"
        f"Введи количество дней (или 0 для VIP/без срока):",
        parse_mode="HTML",
    )


@router.message(AdminStates.TARIFF_CREATE_DAYS)
async def msg_tariff_create_days(message: Message, state: FSMContext) -> None:
    if not _is_admin(message.from_user.id):
        return

    days_input = message.text.strip()
    if not days_input.isdigit():
        await message.answer("Некорректное число. Введи количество дней:")
        return

    days = int(days_input)
    data = await state.get_data()
    user_id = data["new_sub_user_id"]
    tier_id = data["new_sub_tier"]
    user_tg_id = (await get_user(None, user_id))["telegram_id"]
    tier_label = config.TIERS[tier_id]["label"]

    from datetime import datetime, timedelta
    from db.queries.subscriptions import create_subscription

    async with get_db() as db:
        await create_subscription(db, user_id, tier_id, granted_by="admin_manual")
        await update_funnel_stage(db, user_tg_id, "paid")

    await state.set_state(AdminStates.MAIN)
    await message.answer(
        f"✅ Подписка <b>{tier_label}</b> создана для пользователя {user_tg_id}.",
        parse_mode="HTML",
        reply_markup=kb_admin_main(),
    )

    try:
        await message.bot.send_message(
            user_tg_id,
            f"✅ Администратор открыл тебе доступ: <b>{tier_label}</b>.\n"
            f"Добро пожаловать!",
            parse_mode="HTML",
        )
    except Exception:
        pass


@router.callback_query(F.data == "adm:set_gif")
async def cb_adm_set_gif(callback: CallbackQuery, state: FSMContext) -> None:
    if not _is_admin(callback.from_user.id):
        return
    await state.set_state(AdminStates.SET_WELCOME_GIF)
    try:
        await callback.message.delete()
    except Exception:
        pass
    async with get_db() as db:
        current_file_id = await get_setting(db, "VIDEO_FILE_ID", config.VIDEO_FILE_ID)
    current_text = "установлено ✅" if current_file_id else "не установлено ❌"
    await callback.message.answer(
        f"<b>Видео приветствия</b>\nТекущее: {current_text}\n\n"
        "Отправь видео — оно будет показываться пользователям при /start.\n\n"
        "Введи /admin для отмены.",
        parse_mode="HTML",
    )
    await callback.answer()


@router.message(AdminStates.SET_WELCOME_GIF)
async def msg_set_welcome_gif(message: Message, state: FSMContext) -> None:
    if not _is_admin(message.from_user.id):
        return

    file_id, file_type = get_video_file_id_and_type(message)

    if not file_id:
        await message.answer("Отправь видео файл.")
        return

    _save_video_file_id_to_env(file_id, file_type or "video")
    async with get_db() as db:
        await set_settings(
            db,
            {
                "VIDEO_FILE_ID": file_id,
                "VIDEO_FILE_TYPE": file_type or "video",
            },
        )

    await state.set_state(AdminStates.MAIN)
    await message.answer(
        "✅ Видео приветствия обновлено! Будет показываться при /start.",
        reply_markup=kb_admin_main(),
    )


@router.callback_query(F.data == "adm:set_vacancy_video")
async def cb_adm_set_vacancy_video(callback: CallbackQuery, state: FSMContext) -> None:
    if not _is_admin(callback.from_user.id):
        return
    await state.set_state(AdminStates.SET_VACANCY_VIDEO)
    try:
        await callback.message.delete()
    except Exception:
        pass
    async with get_db() as db:
        current_file_id = await get_setting(
            db, "VACANCY_VIDEO_FILE_ID", config.VACANCY_VIDEO_FILE_ID
        )
    current_text = "установлено ✅" if current_file_id else "не установлено ❌"
    await callback.message.answer(
        f"<b>Видео примера вакансий</b>\nТекущее: {current_text}\n\n"
        "Отправь видео — оно будет показываться при нажатии кнопки «Пример вакансий».\n\n"
        "Введи /admin для отмены.",
        parse_mode="HTML",
    )
    await callback.answer()


@router.message(AdminStates.SET_VACANCY_VIDEO)
async def msg_set_vacancy_video(message: Message, state: FSMContext) -> None:
    if not _is_admin(message.from_user.id):
        return

    file_id, file_type = get_video_file_id_and_type(message)
    if not file_id:
        await message.answer("Отправь видео файл.")
        return

    _save_vacancy_video_file_id_to_env(file_id, file_type or "video")
    async with get_db() as db:
        await set_settings(
            db,
            {
                "VACANCY_VIDEO_FILE_ID": file_id,
                "VACANCY_VIDEO_FILE_TYPE": file_type or "video",
            },
        )

    await state.set_state(AdminStates.MAIN)
    await message.answer(
        "✅ Видео примера вакансий обновлено! Будет показываться по кнопке «Пример вакансий».",
        reply_markup=kb_admin_main(),
    )


@router.callback_query(F.data == "adm:set_details_video")
async def cb_adm_set_details_video(callback: CallbackQuery, state: FSMContext) -> None:
    if not _is_admin(callback.from_user.id):
        return
    await state.set_state(AdminStates.SET_DETAILS_VIDEO)
    try:
        await callback.message.delete()
    except Exception:
        pass
    async with get_db() as db:
        current_file_id = await get_setting(db, "DETAILS_VIDEO_FILE_ID", config.DETAILS_VIDEO_FILE_ID)
    current_text = "установлено ✅" if current_file_id else "не установлено ❌"
    await callback.message.answer(
        f"<b>Видео под кнопку «Подробнее»</b>\nТекущее: {current_text}\n\n"
        "Отправь видео — оно будет показываться пользователям при нажатии кнопки «Подробнее».\n\n"
        "Введи /admin для отмены.",
        parse_mode="HTML",
    )
    await callback.answer()


@router.message(AdminStates.SET_DETAILS_VIDEO)
async def msg_set_details_video(message: Message, state: FSMContext) -> None:
    if not _is_admin(message.from_user.id):
        return

    file_id, file_type = get_video_file_id_and_type(message)
    if not file_id:
        await message.answer("Отправь видео файл.")
        return

    _save_details_video_file_id_to_env(file_id, file_type or "video")
    async with get_db() as db:
        await set_settings(
            db,
            {
                "DETAILS_VIDEO_FILE_ID": file_id,
                "DETAILS_VIDEO_FILE_TYPE": file_type or "video",
            },
        )

    await state.set_state(AdminStates.MAIN)
    await message.answer(
        "✅ Видео под кнопку «Подробнее» обновлено!",
        reply_markup=kb_admin_main(),
    )


@router.callback_query(F.data == "adm:add_admin")
async def cb_adm_add_admin(callback: CallbackQuery, state: FSMContext) -> None:
    if not _is_admin(callback.from_user.id):
        return
    await state.set_state(AdminStates.ADD_ADMIN)
    try:
        await callback.message.delete()
    except Exception:
        pass
    current = ", ".join(str(i) for i in config.ADMIN_IDS)
    await callback.message.answer(
        f"<b>Добавить админа</b>\n\n"
        f"Текущие админы: <code>{current}</code>\n\n"
        "Отправь Telegram ID нового админа:",
        parse_mode="HTML",
    )
    await callback.answer()


@router.message(AdminStates.ADD_ADMIN)
async def msg_add_admin(message: Message, state: FSMContext) -> None:
    if not _is_admin(message.from_user.id):
        return

    text = message.text.strip() if message.text else ""
    if not text.lstrip("-").isdigit():
        await message.answer("Некорректный ID. Введи числовой Telegram ID:")
        return

    new_id = int(text)
    if new_id in config.ADMIN_IDS:
        await message.answer(
            f"ID <code>{new_id}</code> уже является админом.",
            parse_mode="HTML",
            reply_markup=kb_admin_main(),
        )
        await state.set_state(AdminStates.MAIN)
        return

    config.ADMIN_IDS.append(new_id)
    _save_admin_ids_to_env(config.ADMIN_IDS)

    await state.set_state(AdminStates.MAIN)
    await message.answer(
        f"✅ Админ <code>{new_id}</code> добавлен.",
        parse_mode="HTML",
        reply_markup=kb_admin_main(),
    )


def _save_admin_ids_to_env(admin_ids: list) -> None:
    try:
        ids_str = ",".join(str(i) for i in admin_ids)
        set_env_values({"ADMIN_TELEGRAM_ID": ids_str})
    except Exception as e:
        logger.error(f"Failed to save admin ids: {e}")


def _save_video_file_id_to_env(file_id: str, file_type: str) -> None:
    try:
        set_env_values({"VIDEO_FILE_ID": file_id, "VIDEO_FILE_TYPE": file_type})
        config.VIDEO_FILE_ID = file_id
        config.VIDEO_FILE_TYPE = file_type
    except Exception as e:
        logger.error(f"Failed to save video file_id: {e}")


def _save_vacancy_video_file_id_to_env(file_id: str, file_type: str) -> None:
    try:
        set_env_values(
            {
                "VACANCY_VIDEO_FILE_ID": file_id,
                "VACANCY_VIDEO_FILE_TYPE": file_type,
            }
        )
        config.VACANCY_VIDEO_FILE_ID = file_id
        config.VACANCY_VIDEO_FILE_TYPE = file_type
    except Exception as e:
        logger.error(f"Failed to save vacancy video file_id: {e}")


def _save_details_video_file_id_to_env(file_id: str, file_type: str) -> None:
    try:
        set_env_values(
            {
                "DETAILS_VIDEO_FILE_ID": file_id,
                "DETAILS_VIDEO_FILE_TYPE": file_type,
            }
        )
        config.DETAILS_VIDEO_FILE_ID = file_id
        config.DETAILS_VIDEO_FILE_TYPE = file_type
    except Exception as e:
        logger.error(f"Failed to save details video file_id: {e}")


async def update_funnel_stage(db, telegram_id: int, stage: str) -> None:
    await db.execute(
        "UPDATE users SET funnel_stage = ? WHERE telegram_id = ?",
        (stage, telegram_id),
    )
    await db.commit()
