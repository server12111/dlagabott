import logging
from aiogram import Router
from aiogram.types import ErrorEvent

router = Router()
logger = logging.getLogger(__name__)


@router.errors()
async def global_error_handler(event: ErrorEvent) -> None:
    logger.error("Unhandled error: %s", event.exception, exc_info=event.exception)
    try:
        update = event.update
        message = getattr(update, "message", None) or getattr(
            getattr(update, "callback_query", None), "message", None
        )
        if message:
            await message.answer("Что-то пошло не так. Попробуй позже или напиши менеджеру.")
    except Exception:
        pass
