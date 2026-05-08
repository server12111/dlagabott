from aiosqlite import Connection


async def get_user_registrations(db: Connection, period: str) -> list[dict]:
    """Returns list of {label, count} for new users grouped by period."""
    if period == "day":
        sql = """
            SELECT strftime('%H:00', created_at) as label, COUNT(*) as count
            FROM users
            WHERE created_at >= datetime('now', '-1 day')
            GROUP BY strftime('%H', created_at)
            ORDER BY strftime('%H', created_at)
        """
    elif period == "week":
        sql = """
            SELECT strftime('%d.%m', created_at) as label, COUNT(*) as count
            FROM users
            WHERE created_at >= datetime('now', '-7 days')
            GROUP BY strftime('%Y-%m-%d', created_at)
            ORDER BY strftime('%Y-%m-%d', created_at)
        """
    elif period == "month":
        sql = """
            SELECT strftime('%d.%m', created_at) as label, COUNT(*) as count
            FROM users
            WHERE created_at >= datetime('now', '-30 days')
            GROUP BY strftime('%Y-%m-%d', created_at)
            ORDER BY strftime('%Y-%m-%d', created_at)
        """
    else:  # year
        sql = """
            SELECT strftime('%m.%Y', created_at) as label, COUNT(*) as count
            FROM users
            WHERE created_at >= datetime('now', '-365 days')
            GROUP BY strftime('%Y-%m', created_at)
            ORDER BY strftime('%Y-%m', created_at)
        """
    cursor = await db.execute(sql)
    rows = await cursor.fetchall()
    return [{"label": r[0], "count": r[1]} for r in rows]


async def get_purchase_stats(db: Connection, period: str, tier: str = "all") -> list[dict]:
    """Returns list of {label, count} for confirmed payments."""
    tier_filter = "" if tier == "all" else f"AND p.tier = '{tier}'"

    if period == "day":
        sql = f"""
            SELECT strftime('%H:00', p.initiated_at) as label, COUNT(*) as count
            FROM payments p
            WHERE p.status = 'confirmed'
              AND p.initiated_at >= datetime('now', '-1 day')
              {tier_filter}
            GROUP BY strftime('%H', p.initiated_at)
            ORDER BY strftime('%H', p.initiated_at)
        """
    elif period == "week":
        sql = f"""
            SELECT strftime('%d.%m', p.initiated_at) as label, COUNT(*) as count
            FROM payments p
            WHERE p.status = 'confirmed'
              AND p.initiated_at >= datetime('now', '-7 days')
              {tier_filter}
            GROUP BY strftime('%Y-%m-%d', p.initiated_at)
            ORDER BY strftime('%Y-%m-%d', p.initiated_at)
        """
    elif period == "month":
        sql = f"""
            SELECT strftime('%d.%m', p.initiated_at) as label, COUNT(*) as count
            FROM payments p
            WHERE p.status = 'confirmed'
              AND p.initiated_at >= datetime('now', '-30 days')
              {tier_filter}
            GROUP BY strftime('%Y-%m-%d', p.initiated_at)
            ORDER BY strftime('%Y-%m-%d', p.initiated_at)
        """
    else:  # year
        sql = f"""
            SELECT strftime('%m.%Y', p.initiated_at) as label, COUNT(*) as count
            FROM payments p
            WHERE p.status = 'confirmed'
              AND p.initiated_at >= datetime('now', '-365 days')
              {tier_filter}
            GROUP BY strftime('%Y-%m', p.initiated_at)
            ORDER BY strftime('%Y-%m', p.initiated_at)
        """
    cursor = await db.execute(sql)
    rows = await cursor.fetchall()
    return [{"label": r[0], "count": r[1]} for r in rows]


async def get_total_user_count(db: Connection) -> int:
    cursor = await db.execute("SELECT COUNT(*) FROM users")
    row = await cursor.fetchone()
    return row[0]


async def get_earnings_by_tier(db: Connection) -> dict:
    """Returns {tier: {count, total_rub}} plus overall total."""
    cursor = await db.execute(
        """
        SELECT tier, COUNT(*) as cnt, SUM(amount_rub) as total
        FROM payments
        WHERE status = 'confirmed'
        GROUP BY tier
        """
    )
    rows = await cursor.fetchall()
    result = {}
    grand_total = 0
    for row in rows:
        result[row[0]] = {"count": row[1], "total": row[2] or 0}
        grand_total += row[2] or 0
    result["__total__"] = grand_total
    return result


async def get_all_user_telegram_ids(db: Connection) -> list[int]:
    cursor = await db.execute("SELECT telegram_id FROM users")
    rows = await cursor.fetchall()
    return [r[0] for r in rows]
