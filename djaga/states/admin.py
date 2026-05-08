from aiogram.fsm.state import State, StatesGroup


class AdminStates(StatesGroup):
    MAIN = State()
    USER_STATS = State()
    PURCHASE_STATS = State()
    BROADCAST_WAITING = State()
    BROADCAST_CONFIRM = State()
    TARIFF_MENU = State()
    TARIFF_FIND_USER = State()
    TARIFF_USER_FOUND = State()
    TARIFF_EXTEND_DAYS = State()
    TARIFF_CREATE_TIER = State()
    TARIFF_CREATE_DAYS = State()
    SET_WELCOME_GIF = State()
    SET_VACANCY_VIDEO = State()
    SET_DETAILS_VIDEO = State()
    ADD_ADMIN = State()
