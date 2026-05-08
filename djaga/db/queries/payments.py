from datetime import datetime
from aiosqlite import Connection
import config


async def create_payment(db: Connection, user_id: int, tier: str) -> int:
    tier_info = config.TIERS[tier]
    cursor = await db.execute(
        """
        INSERT INTO payments (user_id, tier, amount_rub, status, payment_url, confirmation_method)
        VALUES (?, ?, ?, 'initiated', ?, ?)
        """,
        (user_id, tier, tier_info["price"], "", "yookassa_api"),
    )
    await db.commit()
    return cursor.lastrowid


async def get_payment(db: Connection, payment_id: int) -> dict | None:
    cursor = await db.execute(
        "SELECT * FROM payments WHERE id = ?", (payment_id,)
    )
    row = await cursor.fetchone()
    return dict(row) if row else None


async def set_external_payment_id(db: Connection, payment_id: int, external_payment_id: str) -> None:
    await db.execute(
        "UPDATE payments SET external_payment_id = ? WHERE id = ?",
        (external_payment_id, payment_id),
    )
    await db.commit()


async def set_payment_url(db: Connection, payment_id: int, payment_url: str) -> None:
    await db.execute(
        "UPDATE payments SET payment_url = ? WHERE id = ?",
        (payment_url, payment_id),
    )
    await db.commit()


async def get_pending_yookassa_payments(db: Connection) -> list[dict]:
    cursor = await db.execute(
        """
        SELECT * FROM payments
        WHERE status = 'initiated'
          AND external_payment_id IS NOT NULL
          AND external_payment_id != ''
        ORDER BY initiated_at ASC
        """
    )
    rows = await cursor.fetchall()
    return [dict(row) for row in rows]


async def confirm_payment(db: Connection, payment_id: int,
                           subscription_id: int | None = None) -> None:
    now = datetime.utcnow().isoformat()
    await db.execute(
        """
        UPDATE payments SET
            status = 'confirmed',
            confirmed_at = ?,
            subscription_id = COALESCE(?, subscription_id)
        WHERE id = ?
        """,
        (now, subscription_id, payment_id),
    )
    await db.commit()


async def fail_payment(db: Connection, payment_id: int, notes: str = "") -> None:
    await db.execute(
        "UPDATE payments SET status = 'failed', notes = ? WHERE id = ?",
        (notes, payment_id),
    )
    await db.commit()
