import os

from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN: str = os.environ["BOT_TOKEN"]
_admin_ids_raw = os.getenv("ADMIN_TELEGRAM_ID", "0")
ADMIN_IDS: list[int] = [int(x.strip()) for x in _admin_ids_raw.split(",") if x.strip()]
ADMIN_TELEGRAM_ID: int = ADMIN_IDS[0] if ADMIN_IDS else 0
ADMIN_USERNAME: str = os.getenv("ADMIN_USERNAME", "admin")

REVIEW_CHAT_URL: str = os.getenv("REVIEW_CHAT_URL", "https://t.me/+F8Oi8ax3KZJjZTk6")
CHANNEL_PUBLIC_URL: str = os.getenv("CHANNEL_PUBLIC_URL", "https://t.me/hrproworklive")
REVIEW_PUBLIC_URL: str = os.getenv("REVIEW_PUBLIC_URL", "https://t.me/HRpro_Reviews")
CHANNEL_INVITE_LINK: str = os.getenv("CHANNEL_INVITE_LINK", "https://t.me/+oQ6_sipkBv9mZDM6")
VACANCY_GROUP_INVITE_LINK: str = os.getenv("VACANCY_GROUP_INVITE_LINK", "https://t.me/+ckcOSXBqbnQxZDg6")

DB_PATH: str = os.getenv("DB_PATH", "./hr_pro.db")
VIDEO_FILE_ID: str = os.getenv("VIDEO_FILE_ID", "")
VIDEO_FILE_TYPE: str = os.getenv("VIDEO_FILE_TYPE", "video")
VIDEO_LOCAL_PATH: str = os.getenv("VIDEO_LOCAL_PATH", "")
ANIMATION_FILE_ID: str = os.getenv("ANIMATION_FILE_ID", "")
VACANCY_VIDEO_FILE_ID: str = os.getenv("VACANCY_VIDEO_FILE_ID", "")
VACANCY_VIDEO_FILE_TYPE: str = os.getenv("VACANCY_VIDEO_FILE_TYPE", "video")
VACANCY_VIDEO_LOCAL_PATH: str = os.getenv("VACANCY_VIDEO_LOCAL_PATH", "")
DETAILS_VIDEO_FILE_ID: str = os.getenv("DETAILS_VIDEO_FILE_ID", "")
DETAILS_VIDEO_FILE_TYPE: str = os.getenv("DETAILS_VIDEO_FILE_TYPE", "video")

YOOKASSA_SHOP_ID: str = os.getenv("YOOKASSA_SHOP_ID", "")
YOOKASSA_SECRET_KEY: str = os.getenv("YOOKASSA_SECRET_KEY", "")
YOOKASSA_WEBHOOK_HOST: str = os.getenv("YOOKASSA_WEBHOOK_HOST", "")
YOOKASSA_WEBHOOK_PORT: int = int(os.getenv("YOOKASSA_WEBHOOK_PORT", "8080"))
YOOKASSA_WEBHOOK_ENABLED: bool = os.getenv("YOOKASSA_WEBHOOK_ENABLED", "false").lower() in {"1", "true", "yes", "on"}
YOOKASSA_RETURN_URL: str = os.getenv("YOOKASSA_RETURN_URL", "")
YOOKASSA_ENABLED: bool = bool(YOOKASSA_SHOP_ID and YOOKASSA_SECRET_KEY)

REMINDER_DELAY_HOURS: int = int(os.getenv("REMINDER_DELAY_HOURS", "24"))
REMINDER_MAX_COUNT: int = int(os.getenv("REMINDER_MAX_COUNT", "3"))
REMINDER_CHECK_INTERVAL_MINUTES: int = int(os.getenv("REMINDER_CHECK_INTERVAL_MINUTES", "60"))

YOOKASSA_POLL_INTERVAL_SECONDS: int = int(os.getenv("YOOKASSA_POLL_INTERVAL_SECONDS", "30"))

SUBSCRIPTION_EXPIRY_CHECK_INTERVAL_MINUTES: int = int(os.getenv("SUBSCRIPTION_EXPIRY_CHECK_INTERVAL_MINUTES", "60"))

TIERS: dict = {
    "test_7d": {
        "label": "Тест (7 дней)",
        "price": 750,
        "days": 7,
    },
    "pro_30d": {
        "label": "Профи (30 дней)",
        "price": 1600,
        "days": 30,
    },
    "vip": {
        "label": "VIP",
        "price": 10000,
        "days": None,
    },
}
