from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

import config
from db.database import get_db
from db.queries.payments import create_payment, fail_payment, get_payment, set_external_payment_id, set_payment_url
from db.queries.users import get_user, update_funnel_stage
from keyboards.inline import kb_payment_sent
from states.funnel import FunnelStates
from texts.messages import (
    PAYMENT_CHECK_RETRY,
    PAYMENT_INITIATED,
    PAYMENT_NOT_CONFIRMED,
    PAYMENT_PENDING,
    PAYMENT_SERVICE_TEMPORARY_ISSUE,
    PAYMENT_UNAVAILABLE,
)
from utils.payment_access import build_access_text, grant_access_for_payment
from utils.payment_provider import PaymentProviderError, generate_payment_url, verify_payment

router = Router()


@router.callback_query(F.data.startswith("tier:"))
async def cb_tier_selected(callback: CallbackQuery, state: FSMContext) -> None:
    tier_id = callback.data.split(":", 1)[1]
    if tier_id not in config.TIERS:
        await callback.answer("Неизвестный тариф", show_alert=True)
        return

    tier_info = config.TIERS[tier_id]
    await state.set_state(FunnelStates.TIER_SELECTED)
    await state.update_data(tier_id=tier_id)
    try:
        await callback.message.delete()
    except Exception:
        pass

    async with get_db() as db:
        user = await get_user(db, callback.from_user.id)
        payment_id = await create_payment(db, user["id"], tier_id)
        await update_funnel_stage(db, callback.from_user.id, "awaiting_payment")

    await state.set_state(FunnelStates.AWAITING_PAYMENT)
    await state.update_data(payment_id=payment_id)

    try:
        payment_url, external_id = await generate_payment_url(
            callback.from_user.id,
            tier_id,
            payment_id,
        )
    except PaymentProviderError:
        async with get_db() as db:
            await fail_payment(db, payment_id, notes="yookassa_create_failed")
        await callback.message.answer(
            PAYMENT_UNAVAILABLE.format(admin_username=config.ADMIN_USERNAME),
            parse_mode="HTML",
        )
        await callback.answer()
        return

    async with get_db() as db:
        await set_external_payment_id(db, payment_id, external_id)
        await set_payment_url(db, payment_id, payment_url)

    text = PAYMENT_INITIATED.format(
        tier_label=tier_info["label"],
        price=tier_info["price"],
        payment_url=payment_url,
    )
    await callback.message.answer(
        text,
        reply_markup=kb_payment_sent(payment_id, payment_url),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data.startswith("payment_done:"))
async def cb_payment_done(callback: CallbackQuery, state: FSMContext) -> None:
    payment_id = int(callback.data.split(":", 1)[1])

    async with get_db() as db:
        user = await get_user(db, callback.from_user.id)
        payment = await get_payment(db, payment_id)

    if not user or not payment or payment["user_id"] != user["id"]:
        await callback.answer("Платеж не найден", show_alert=True)
        return

    if payment["status"] == "confirmed":
        try:
            await callback.message.edit_reply_markup(reply_markup=None)
        except Exception:
            pass
        await callback.message.answer("Доступ уже был открыт ранее.")
        await callback.message.answer(build_access_text(payment["tier"]), parse_mode="HTML")
        await state.clear()
        await callback.answer()
        return

    external_payment_id = payment.get("external_payment_id", "")
    if not external_payment_id:
        await callback.answer(
            "Платеж еще не создан. Попробуйте выбрать тариф заново.",
            show_alert=True,
        )
        return

    verification_status = await verify_payment(external_payment_id)
    if verification_status == "pending":
        await callback.answer(PAYMENT_PENDING, show_alert=True)
        return

    if verification_status in {"provider_error", "misconfigured"}:
        await callback.answer(PAYMENT_SERVICE_TEMPORARY_ISSUE, show_alert=True)
        return

    if verification_status in {"canceled", "not_found"}:
        await callback.answer(PAYMENT_NOT_CONFIRMED, show_alert=True)
        return

    if verification_status != "succeeded":
        await callback.answer(PAYMENT_CHECK_RETRY, show_alert=True)
        return

    granted = await grant_access_for_payment(
        callback.bot,
        payment_id,
        granted_by="user_status_check",
    )
    if not granted:
        await callback.answer("Оплата уже обрабатывается.", show_alert=True)
        return

    try:
        await callback.message.edit_reply_markup(reply_markup=None)
    except Exception:
        pass

    await callback.message.answer("Оплата подтверждена, доступ открыт.")
    await state.clear()
    await callback.answer()
