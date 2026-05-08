from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message, FSInputFile
from aiogram.fsm.context import FSMContext

import config
from states.funnel import FunnelStates
from keyboards.inline import kb_welcome
from texts.messages import WELCOME
from db.database import get_db
from db.queries.settings import get_setting, set_settings
from db.queries.users import update_funnel_stage
from utils.env_file import set_env_values
from utils.video import answer_stored_video

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext) -> None:
    await state.set_state(FunnelStates.WELCOME)

    async with get_db() as db:
        await update_funnel_stage(db, message.from_user.id, "welcome")
        video_file_id = await get_setting(db, "VIDEO_FILE_ID", config.VIDEO_FILE_ID)
        video_file_type = await get_setting(db, "VIDEO_FILE_TYPE", config.VIDEO_FILE_TYPE)

    if video_file_id:
        try:
            await answer_stored_video(
                target=message,
                file_id=video_file_id,
                file_type=video_file_type,
                caption=WELCOME,
                reply_markup=kb_welcome(),
            )
            return
        except Exception:
            config.VIDEO_FILE_ID = ""
            await _save_file_id("")

    if config.VIDEO_LOCAL_PATH:
        try:
            video = FSInputFile(config.VIDEO_LOCAL_PATH)
            sent = await message.answer_video(
                video=video,
                caption=WELCOME,
                reply_markup=kb_welcome(),
            )
            await _save_file_id(sent.video.file_id)
            return
        except Exception:
            pass

    await message.answer(WELCOME, reply_markup=kb_welcome())


async def _save_file_id(file_id: str) -> None:
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
