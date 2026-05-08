from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

import config


def kb_welcome() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="Да, хочу доступ", callback_data="want_access", style="success")
    builder.button(text="Просто посмотреть", callback_data="just_look")
    builder.button(text="Наш паблик", url=config.CHANNEL_PUBLIC_URL)
    builder.adjust(1)
    return builder.as_markup()


def kb_value() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="Подробнее", callback_data="more_details")
    builder.button(text="Тарифы", callback_data="show_pricing", style="success")
    builder.button(text="Пример вакансий", callback_data="show_vacancy_example")
    builder.button(text="← Назад", callback_data="back_to_welcome")
    builder.adjust(2, 1, 1)
    return builder.as_markup()


def kb_pain() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="Тарифы", callback_data="show_pricing", style="success")
    builder.button(text="Пример вакансий", callback_data="show_vacancy_example")
    builder.button(text="← Назад", callback_data="back_to_value")
    builder.adjust(1)
    return builder.as_markup()


def kb_pricing() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(
        text=f"🥉 Купить Тест — {config.TIERS['test_7d']['price']} ₽",
        callback_data="tier:test_7d",
        style="success",
    )
    builder.button(
        text=f"🥈 Купить Профи — {config.TIERS['pro_30d']['price']} ₽",
        callback_data="tier:pro_30d",
        style="success",
    )
    builder.button(
        text=f"🥇 Купить VIP — {config.TIERS['vip']['price']} ₽",
        callback_data="tier:vip",
        style="success",
    )
    builder.button(text="Проблема с оплатой", callback_data="payment_problem", style="danger")
    builder.button(text="Отзывы", callback_data="show_reviews")
    builder.button(text="← Назад", callback_data="back_to_pain")
    builder.adjust(1)
    return builder.as_markup()


def kb_reviews() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="Оплатить", callback_data="select_tier", style="success")
    builder.button(text="Проблема с оплатой", callback_data="payment_problem", style="danger")
    builder.button(text="← Назад", callback_data="back_to_pricing")
    builder.adjust(1)
    return builder.as_markup()


def kb_vacancy_example() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="Оплатить", callback_data="select_tier", style="success")
    builder.button(text="← Назад к тарифам", callback_data="back_to_pricing")
    builder.adjust(1)
    return builder.as_markup()


def kb_tier_select() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(
        text=f"{config.TIERS['test_7d']['label']} — {config.TIERS['test_7d']['price']} ₽",
        callback_data="tier:test_7d",
        style="success",
    )
    builder.button(
        text=f"{config.TIERS['pro_30d']['label']} — {config.TIERS['pro_30d']['price']} ₽",
        callback_data="tier:pro_30d",
        style="success",
    )
    builder.button(
        text=f"{config.TIERS['vip']['label']} — {config.TIERS['vip']['price']} ₽",
        callback_data="tier:vip",
        style="success",
    )
    builder.button(text="← Назад к тарифам", callback_data="back_to_pricing")
    builder.adjust(1)
    return builder.as_markup()


def kb_payment_sent(payment_id: int, payment_url: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="Оплатить", url=payment_url)
    builder.button(
        text="Проверить оплату",
        callback_data=f"payment_done:{payment_id}",
        style="success",
    )
    builder.button(text="↩️ Назад к тарифам", callback_data="back_to_pricing")
    builder.adjust(1)
    return builder.as_markup()


def kb_payment_problem() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="← Назад к тарифам", callback_data="back_to_pricing")
    builder.adjust(1)
    return builder.as_markup()


def kb_back_to_pricing() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="Вернуться к тарифам", callback_data="back_to_pricing")
    return builder.as_markup()
