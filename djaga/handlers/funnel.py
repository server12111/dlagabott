from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, FSInputFile

import config
from db.database import get_db
from db.queries.settings import get_setting, set_settings
from db.queries.users import update_funnel_stage
from keyboards.inline import (
    kb_pain,
    kb_payment_problem,
    kb_pricing,
    kb_reviews,
    kb_tier_select,
    kb_vacancy_example,
    kb_value,
    kb_welcome,
)
from states.funnel import FunnelStates
from texts.messages import PAIN, PAYMENT_PROBLEM, PRICING, REVIEWS, VACANCY_EXAMPLE, VALUE, WELCOME
from utils.env_file import set_env_values
from utils.video import answer_stored_video

router = Router()


async def _delete(callback: CallbackQuery) -> None:
    try:
        await callback.message.delete()
    except Exception:
        pass


async def _send_value(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(FunnelStates.VALUE)
    async with get_db() as db:
        await update_funnel_stage(db, callback.from_user.id, "value")
    await _delete(callback)
    await callback.message.answer(VALUE, reply_markup=kb_value())
    await callback.answer()


async def _send_pricing(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(FunnelStates.PRICING)
    async with get_db() as db:
        await update_funnel_stage(db, callback.from_user.id, "pricing")
    await _delete(callback)
    await callback.message.answer(PRICING, reply_markup=kb_pricing(), parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data == "want_access")
async def cb_want_access(callback: CallbackQuery, state: FSMContext) -> None:
    await _send_value(callback, state)


@router.callback_query(F.data == "just_look")
async def cb_just_look(callback: CallbackQuery, state: FSMContext) -> None:
    await _send_value(callback, state)


@router.callback_query(F.data == "more_details")
async def cb_more_details(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(FunnelStates.PAIN)
    async with get_db() as db:
        await update_funnel_stage(db, callback.from_user.id, "pain")
        details_file_id = await get_setting(db, "DETAILS_VIDEO_FILE_ID", config.DETAILS_VIDEO_FILE_ID)
        details_file_type = await get_setting(db, "DETAILS_VIDEO_FILE_TYPE", config.DETAILS_VIDEO_FILE_TYPE)
    await _delete(callback)
    await callback.answer()
    if details_file_id:
        try:
            await answer_stored_video(
                target=callback.message,
                file_id=details_file_id,
                file_type=details_file_type,
                caption=None,
                reply_markup=None,
            )
        except Exception:
            pass
    await callback.message.answer(PAIN, reply_markup=kb_pain())


@router.callback_query(F.data == "show_pricing")
async def cb_show_pricing(callback: CallbackQuery, state: FSMContext) -> None:
    await _send_pricing(callback, state)


@router.callback_query(F.data == "show_reviews")
async def cb_show_reviews(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(FunnelStates.REVIEWS)
    async with get_db() as db:
        await update_funnel_stage(db, callback.from_user.id, "reviews")
    await _delete(callback)
    text = REVIEWS.format(review_url=config.REVIEW_PUBLIC_URL)
    await callback.message.answer(text, reply_markup=kb_reviews())
    await callback.answer()


@router.callback_query(F.data == "payment_problem")
async def cb_payment_problem(callback: CallbackQuery, state: FSMContext) -> None:
    await _delete(callback)
    text = PAYMENT_PROBLEM.format(admin_username=config.ADMIN_USERNAME)
    await callback.message.answer(text, reply_markup=kb_payment_problem())
    await callback.answer()


@router.callback_query(F.data == "select_tier")
async def cb_select_tier(callback: CallbackQuery, state: FSMContext) -> None:
    await _delete(callback)
    await callback.message.answer("Выбери тариф:", reply_markup=kb_tier_select())
    await callback.answer()


@router.callback_query(F.data == "show_vacancy_example")
async def cb_show_vacancy_example(callback: CallbackQuery, state: FSMContext) -> None:
    await _delete(callback)
    await callback.answer()
    async with get_db() as db:
        vacancy_file_id = await get_setting(
            db, "VACANCY_VIDEO_FILE_ID", config.VACANCY_VIDEO_FILE_ID
        )
        vacancy_file_type = await get_setting(
            db, "VACANCY_VIDEO_FILE_TYPE", config.VACANCY_VIDEO_FILE_TYPE
        )

    if vacancy_file_id:
        try:
            await answer_stored_video(
                target=callback.message,
                file_id=vacancy_file_id,
                file_type=vacancy_file_type,
                caption=VACANCY_EXAMPLE,
                reply_markup=kb_vacancy_example(),
            )
            return
        except Exception:
            config.VACANCY_VIDEO_FILE_ID = ""
            await _save_vacancy_file_id("")

    if config.VACANCY_VIDEO_LOCAL_PATH:
        try:
            video = FSInputFile(config.VACANCY_VIDEO_LOCAL_PATH)
            sent = await callback.message.answer_video(
                video=video,
                caption=VACANCY_EXAMPLE,
                reply_markup=kb_vacancy_example(),
            )
            await _save_vacancy_file_id(sent.video.file_id)
        except Exception:
            await callback.message.answer(VACANCY_EXAMPLE, reply_markup=kb_vacancy_example())
    else:
        await callback.message.answer(VACANCY_EXAMPLE, reply_markup=kb_vacancy_example())


@router.callback_query(F.data == "back_to_welcome")
async def cb_back_to_welcome(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(FunnelStates.WELCOME)
    async with get_db() as db:
        await update_funnel_stage(db, callback.from_user.id, "welcome")
        video_file_id = await get_setting(db, "VIDEO_FILE_ID", config.VIDEO_FILE_ID)
        video_file_type = await get_setting(db, "VIDEO_FILE_TYPE", config.VIDEO_FILE_TYPE)
    await _delete(callback)
    await callback.answer()
    if video_file_id:
        try:
            await answer_stored_video(
                target=callback.message,
                file_id=video_file_id,
                file_type=video_file_type,
                caption=WELCOME,
                reply_markup=kb_welcome(),
            )
            return
        except Exception:
            config.VIDEO_FILE_ID = ""
            await _save_welcome_file_id("")

    if config.VIDEO_LOCAL_PATH:
        try:
            from aiogram.types import FSInputFile
            video = FSInputFile(config.VIDEO_LOCAL_PATH)
            sent = await callback.message.answer_video(
                video=video,
                caption=WELCOME,
                reply_markup=kb_welcome(),
            )
            config.VIDEO_FILE_ID = sent.video.file_id
            await _save_welcome_file_id(sent.video.file_id)
            return
        except Exception:
            pass

    await callback.message.answer(WELCOME, reply_markup=kb_welcome())


@router.callback_query(F.data == "back_to_value")
async def cb_back_to_value(callback: CallbackQuery, state: FSMContext) -> None:
    await _send_value(callback, state)


@router.callback_query(F.data == "back_to_pain")
async def cb_back_to_pain(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(FunnelStates.PAIN)
    async with get_db() as db:
        await update_funnel_stage(db, callback.from_user.id, "pain")
    await _delete(callback)
    await callback.message.answer(PAIN, reply_markup=kb_pain())
    await callback.answer()


@router.callback_query(F.data == "back_to_pricing")
async def cb_back_to_pricing(callback: CallbackQuery, state: FSMContext) -> None:
    await _send_pricing(callback, state)


async def _save_vacancy_file_id(file_id: str) -> None:
    try:
        set_env_values({"VACANCY_VIDEO_FILE_ID": file_id, "VACANCY_VIDEO_FILE_TYPE": "video"})
        config.VACANCY_VIDEO_FILE_ID = file_id
        config.VACANCY_VIDEO_FILE_TYPE = "video"
        async with get_db() as db:
            await set_settings(
                db,
                {"VACANCY_VIDEO_FILE_ID": file_id, "VACANCY_VIDEO_FILE_TYPE": "video"},
            )
    except Exception:
        pass


async def _save_welcome_file_id(file_id: str) -> None:
    try:
        set_env_values({"VIDEO_FILE_ID": file_id, "VIDEO_FILE_TYPE": "video"})
        config.VIDEO_FILE_ID = file_id
        config.VIDEO_FILE_TYPE = "video"
        async with get_db() as db:
            await set_settings(
                db,
                {"VIDEO_FILE_ID": file_id, "VIDEO_FILE_TYPE": "video"},
            )
    except Exception:
        pass
