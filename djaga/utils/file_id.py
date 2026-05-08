import logging
from aiogram import Bot

import config

logger = logging.getLogger(__name__)


async def upload_and_get_file_id(bot: Bot, local_path: str) -> str | None:
    try:
        from aiogram.types import FSInputFile
        video = FSInputFile(local_path)
        msg = await bot.send_video(config.ADMIN_TELEGRAM_ID, video=video)
        file_id = msg.video.file_id
        logger.info(
            "Video uploaded successfully. Add this to .env:\nVIDEO_FILE_ID=%s", file_id
        )
        return file_id
    except Exception as e:
        logger.error("Failed to upload video: %s", e)
        return None
