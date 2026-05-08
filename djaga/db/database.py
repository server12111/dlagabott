from contextlib import asynccontextmanager

import aiosqlite

import config
from db.models import (
    CREATE_USERS_TABLE,
    CREATE_SUBSCRIPTIONS_TABLE,
    CREATE_PAYMENTS_TABLE,
    CREATE_SETTINGS_TABLE,
    CREATE_INDEXES,
)


REQUIRED_PAYMENTS_COLUMNS: dict[str, str] = {
    "external_payment_id": "TEXT",
    "payment_url": "TEXT",
    "confirmation_method": "TEXT DEFAULT 'yookassa_link'",
    "confirmed_at": "DATETIME",
    "notes": "TEXT",
}


async def _ensure_payments_schema(db: aiosqlite.Connection) -> None:
    cursor = await db.execute("PRAGMA table_info(payments)")
    rows = await cursor.fetchall()
    existing_columns = {row[1] for row in rows}

    for column_name, column_sql in REQUIRED_PAYMENTS_COLUMNS.items():
        if column_name in existing_columns:
            continue
        await db.execute(f"ALTER TABLE payments ADD COLUMN {column_name} {column_sql}")


async def init_db() -> None:
    async with aiosqlite.connect(config.DB_PATH) as db:
        await db.execute(CREATE_USERS_TABLE)
        await db.execute(CREATE_SUBSCRIPTIONS_TABLE)
        await db.execute(CREATE_PAYMENTS_TABLE)
        await db.execute(CREATE_SETTINGS_TABLE)
        await _ensure_payments_schema(db)
        for idx_sql in CREATE_INDEXES:
            await db.execute(idx_sql)
        await db.commit()


@asynccontextmanager
async def get_db():
    async with aiosqlite.connect(config.DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        yield db
