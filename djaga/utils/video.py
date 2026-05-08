from typing import Any

from aiogram.types import Message


def get_video_file_id_and_type(message: Message) -> tuple[str | None, str | None]:
    if message.video:
        return message.video.file_id, "video"
    if message.animation:
        return message.animation.file_id, "animation"
    if (
        message.document
        and message.document.mime_type
        and message.document.mime_type.startswith("video/")
    ):
        return message.document.file_id, "document"
    return None, None


async def answer_stored_video(
    target: Any,
    file_id: str,
    file_type: str,
    caption: str,
    reply_markup: Any,
):
    if file_type == "animation":
        return await target.answer_animation(
            animation=file_id,
            caption=caption,
            reply_markup=reply_markup,
        )
    if file_type == "document":
        return await target.answer_document(
            document=file_id,
            caption=caption,
            reply_markup=reply_markup,
        )
    return await target.answer_video(
        video=file_id,
        caption=caption,
        reply_markup=reply_markup,
    )
