from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

PERIODS = [
    ("За день", "day"),
    ("За 7 дней", "week"),
    ("За месяц", "month"),
    ("За год", "year"),
]

TIERS_FILTER = [
    ("Все тарифы", "all"),
    ("Тест 1₽", "test_1r"),
    ("Тест", "test_7d"),
    ("Профи", "pro_30d"),
    ("VIP", "vip"),
]

TIER_OPTIONS = [
    ("Тест (1₽)", "test_1r"),
    ("Тест (7 дн.)", "test_7d"),
    ("Профи (30 дн.)", "pro_30d"),
    ("VIP", "vip"),
]


def kb_admin_main() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="Статистика пользователей", callback_data="adm:users")
    builder.button(text="Статистика покупок", callback_data="adm:purchases")
    builder.button(text="Управление тарифами", callback_data="adm:tariff_menu")
    builder.button(text="Рассылка", callback_data="adm:broadcast")
    builder.button(text="Установить видео приветствия", callback_data="adm:set_gif")
    builder.button(text="Установить видео примера вакансий", callback_data="adm:set_vacancy_video")
    builder.button(text="Установить видео «Подробнее»", callback_data="adm:set_details_video")
    builder.button(text="Добавить админа", callback_data="adm:add_admin")
    builder.adjust(1)
    return builder.as_markup()


def kb_admin_periods(prefix: str, active: str = "day") -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for label, key in PERIODS:
        text = f"• {label}" if key == active else label
        builder.button(text=text, callback_data=f"{prefix}:period:{key}")
    builder.button(text="← Назад", callback_data="adm:back")
    builder.adjust(4, 1)
    return builder.as_markup()


def kb_admin_purchase_filters(active_period: str = "day", active_tier: str = "all") -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for label, key in PERIODS:
        text = f"• {label}" if key == active_period else label
        builder.button(text=text, callback_data=f"adm_buy:period:{key}:{active_tier}")
    builder.adjust(4)
    for label, key in TIERS_FILTER:
        text = f"• {label}" if key == active_tier else label
        builder.button(text=text, callback_data=f"adm_buy:tier:{active_period}:{key}")
    builder.adjust(4, 4)
    builder.button(text="← Назад", callback_data="adm:back")
    builder.adjust(4, 4, 1)
    return builder.as_markup()


def kb_broadcast_confirm() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="Отправить всем", callback_data="adm_bc:confirm", style="success")
    builder.button(text="Отмена", callback_data="adm_bc:cancel", style="danger")
    builder.adjust(1)
    return builder.as_markup()


def kb_tariff_menu() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="Поиск пользователя", callback_data="adm:tariff_find")
    builder.button(text="Активные подписки", callback_data="adm:tariff_active")
    builder.adjust(1)
    builder.button(text="← Назад", callback_data="adm:back")
    return builder.as_markup()


def kb_tariff_user_actions(subscription_id: int, status: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    if status == "active":
        builder.button(text="Продлить", callback_data=f"adm_t:extend:{subscription_id}")
        builder.button(text="Отключить", callback_data=f"adm_t:revoke:{subscription_id}")
    elif status in {"expired", "cancelled"}:
        builder.button(text="Активировать", callback_data=f"adm_t:activate:{subscription_id}")
    builder.button(text="← К списку", callback_data="adm:tariff_find")
    builder.adjust(2)
    return builder.as_markup()


def kb_tariff_extend_days(subscription_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for days in [1, 7, 14, 30]:
        builder.button(text=f"{days} дн.", callback_data=f"adm_t:extdays:{subscription_id}:{days}")
    builder.button(text="← Отмена", callback_data="adm:tariff_find")
    builder.adjust(4)
    return builder.as_markup()


def kb_tariff_choose_tier() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for label, key in TIER_OPTIONS:
        builder.button(text=label, callback_data=f"adm_t:ctier:{key}")
    builder.button(text="← Отмена", callback_data="adm:tariff_menu")
    builder.adjust(2)
    return builder.as_markup()


def kb_tariff_create_confirm() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="Создать", callback_data="adm_t:confirm_create")
    builder.button(text="Отмена", callback_data="adm:tariff_menu")
    builder.adjust(2)
    return builder.as_markup()
