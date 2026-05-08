from datetime import datetime
from aiosqlite import Connection


async def upsert_user(db: Connection, telegram_id: int, username: str | None,
                      first_name: str | None, last_name: str | None,
                      language_code: str | None) -> None:
    now = datetime.utcnow().isoformat()
    await db.execute(
        """
        INSERT INTO users (telegram_id, username, first_name, last_name, language_code, last_seen_at)
        VALUES (?, ?, ?, ?, ?, ?)
        ON CONFLICT(telegram_id) DO UPDATE SET
            username = excluded.username,
            first_name = excluded.first_name,
            last_name = excluded.last_name,
            language_code = excluded.language_code,
            last_seen_at = excluded.last_seen_at
        """,
        (telegram_id, username, first_name, last_name, language_code, now),
    )
    await db.commit()


async def get_user(db: Connection, telegram_id: int) -> dict | None:
    cursor = await db.execute(
        "SELECT * FROM users WHERE telegram_id = ?", (telegram_id,)
    )
    row = await cursor.fetchone()
    return dict(row) if row else None


async def get_user_by_id(db: Connection, user_id: int) -> dict | None:
    cursor = await db.execute(
        "SELECT * FROM users WHERE id = ?", (user_id,)
    )
    row = await cursor.fetchone()
    return dict(row) if row else None


async def update_funnel_stage(db: Connection, telegram_id: int, stage: str) -> None:
    await db.execute(
        "UPDATE users SET funnel_stage = ? WHERE telegram_id = ?",
        (stage, telegram_id),
    )
    await db.commit()


async def update_reminder_info(db: Connection, telegram_id: int) -> None:
    now = datetime.utcnow().isoformat()
    await db.execute(
        """
        UPDATE users SET
            last_reminder_sent_at = ?,
            reminder_count = reminder_count + 1
        WHERE telegram_id = ?
        """,
        (now, telegram_id),
    )
    await db.commit()


async def get_users_for_reminder(db: Connection, delay_hours: int, max_count: int) -> list[dict]:
    cursor = await db.execute(
        """
        SELECT u.* FROM users u
        LEFT JOIN subscriptions s ON s.user_id = u.id AND s.status = 'active'
        WHERE u.funnel_stage IN ('pricing', 'reviews', 'awaiting_payment')
          AND s.id IS NULL
          AND u.reminder_count < ?
          AND (
              u.last_reminder_sent_at IS NULL
              OR datetime(u.last_reminder_sent_at, '+' || ? || ' hours') < datetime('now')
          )
          AND datetime(u.last_seen_at, '+' || ? || ' hours') < datetime('now')
        """,
        (max_count, delay_hours, delay_hours),
    )
    rows = await cursor.fetchall()
    return [dict(r) for r in rows]
