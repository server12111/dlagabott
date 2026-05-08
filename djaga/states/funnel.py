from aiogram.fsm.state import State, StatesGroup


class FunnelStates(StatesGroup):
    WELCOME = State()
    VALUE = State()
    PAIN = State()
    PRICING = State()
    TIER_SELECTED = State()
    REVIEWS = State()
    AWAITING_PAYMENT = State()
    PAID = State()
