from datetime import datetime, timedelta
from aiosqlite import Connection
import config


async def create_subscription(db: Connection, user_id: int, tier: str,
                               granted_by: str = "payment") -> int:
    tier_info = config.TIERS[tier]
    now = datetime.utcnow()
    expires_at = None
    if tier_info["days"] is not None:
        expires_at = (now + timedelta(days=tier_info["days"])).isoformat()

    cursor = await db.execute(
        """
        INSERT INTO subscriptions (user_id, tier, price_rub, status, starts_at, expires_at, granted_by)
        VALUES (?, ?, ?, 'active', ?, ?, ?)
        """,
        (user_id, tier, tier_info["price"], now.isoformat(), expires_at, granted_by),
    )
    await db.commit()
    return cursor.lastrowid


async def get_active_subscription(db: Connection, user_id: int) -> dict | None:
    cursor = await db.execute(
        """
        SELECT * FROM subscriptions
        WHERE user_id = ? AND status = 'active'
          AND (expires_at IS NULL OR datetime(expires_at) > datetime('now'))
        ORDER BY created_at DESC LIMIT 1
        """,
        (user_id,),
    )
    row = await cursor.fetchone()
    return dict(row) if row else None


async def link_subscription_to_payment(db: Connection, subscription_id: int,
                                        payment_id: int) -> None:
    await db.execute(
        "UPDATE payments SET subscription_id = ? WHERE id = ?",
        (subscription_id, payment_id),
    )
    await db.commit()


async def expire_old_subscriptions(db: Connection) -> list[int]:
    """Set status='expired' for active subscriptions past expires_at.
    Returns list of telegram_ids of affected users.
    """
    cursor = await db.execute(
        """
        UPDATE subscriptions
        SET status = 'expired', updated_at = datetime('now')
        WHERE status = 'active'
          AND expires_at IS NOT NULL
          AND datetime(expires_at) < datetime('now')
        """
    )
    await db.commit()

    if cursor.rowcount == 0:
        return []

    # fetch user telegram_ids for notification
    cursor = await db.execute(
        """
        SELECT u.telegram_id FROM users u
        JOIN subscriptions s ON s.user_id = u.id
        WHERE s.status = 'expired'
          AND s.updated_at = datetime('now')
        """
    )
    rows = await cursor.fetchall()
    return [row[0] for row in rows]


async def get_user_subscriptions(db: Connection, user_id: int) -> list[dict]:
    cursor = await db.execute(
        "SELECT * FROM subscriptions WHERE user_id = ? ORDER BY created_at DESC",
        (user_id,),
    )
    rows = await cursor.fetchall()
    return [dict(row) for row in rows]


async def update_subscription_status(db: Connection, subscription_id: int,
                                     status: str) -> None:
    await db.execute(
        "UPDATE subscriptions SET status = ?, updated_at = datetime('now') WHERE id = ?",
        (status, subscription_id),
    )
    await db.commit()


async def extend_subscription(db: Connection, subscription_id: int,
                              days: int) -> None:
    cursor = await db.execute(
        "SELECT expires_at FROM subscriptions WHERE id = ?",
        (subscription_id,),
    )
    row = await cursor.fetchone()
    if not row:
        return

    from datetime import datetime, timedelta

    current_expires = row[0]
    if current_expires is None:
        return

    current_dt = datetime.fromisoformat(current_expires)
    now = datetime.utcnow()
    if current_dt < now:
        new_expires = (now + timedelta(days=days)).isoformat()
    else:
        new_expires = (current_dt + timedelta(days=days)).isoformat()

    await db.execute(
        "UPDATE subscriptions SET expires_at = ?, updated_at = datetime('now') WHERE id = ?",
        (new_expires, subscription_id),
    )
    await db.commit()
