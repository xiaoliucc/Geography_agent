"""
L2 用户档案 — CRUD 操作(增删改查)

使用 aiosqlite 异步 SQLite，所有操作通过 get_db() 获取连接。
"""

import os
import json
import aiosqlite

from .models import SCHEMA_SQL

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "..", "memory", "users.db")


async def get_db():
    """获取数据库连接，自动建表 + 迁移"""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    db = await aiosqlite.connect(DB_PATH)
    db.row_factory = aiosqlite.Row
    await db.executescript(SCHEMA_SQL)
    await db.commit()

    # 迁移：确保 session_id 有唯一约束（修复历史数据重复问题）
    cursor = await db.execute(
        "SELECT name FROM pragma_index_list('conversation_summaries') "
        "WHERE name = 'idx_session_unique'"
    )
    has_index = await cursor.fetchone()
    if not has_index:
        # 清理重复行：保留每个 session_id 中 id 最大的那条
        await db.execute(
            "DELETE FROM conversation_summaries WHERE id NOT IN "
            "(SELECT MAX(id) FROM conversation_summaries GROUP BY session_id)"
        )
        await db.execute(
            "CREATE UNIQUE INDEX idx_session_unique ON conversation_summaries(session_id)"
        )
        await db.commit()

    return db


async def get_or_create_user(user_id: str) -> dict:
    """获取用户档案，不存在则创建新记录"""
    # TODO: 实现
    # 1. get_db()
    # 2. SELECT * FROM user_profiles WHERE user_id = ?
    # 3. 如果不存在，INSERT 一条新记录（只填 user_id）
    # 4. commit() 并返回 dict
    # 5. 记得关闭连接或使用 async with
    db = await get_db()
    cursor = await db.execute("SELECT * FROM user_profiles WHERE user_id = ?", (user_id,))
    row = await cursor.fetchone()
    
    if row is None:
        await db.execute("INSERT INTO user_profiles (user_id) VALUES (?)", (user_id,))
        await db.commit()
        await db.close()
        return {
            "user_id": user_id,
            "grade": None,
            "textbook": "renjiao",
            "is_new": True,
        }
    
    await db.close()
    return dict(row)



async def update_user_profile(user_id: str, **fields) -> dict:
    """更新用户档案（grade, textbook 等允许的字段）"""
    # TODO: 实现
    # 1. 过滤只允许 grade, textbook 字段
    # 2. UPDATE user_profiles SET ... WHERE user_id = ?
    # 3. 同时更新 updated_at = datetime('now')
    # 4. 返回更新后的档案
    allowen = {"grade", "textbook"}
    updates = {k: v for k, v in fields.items() if k in allowen and v}
    if not updates:
        return await get_or_create_user(user_id)
    
    set_parts = ", ".join(f"{k} = ?" for k in updates)
    values = list(updates.values())
    values.append(user_id)
    
    db = await get_db()
    await db.execute(
        f"UPDATE user_profiles SET {set_parts}, updated_at = datetime('now') WHERE user_id = ?",
        values,
    )
    await db.commit()
    await db.close()
    return await get_or_create_user(user_id)

async def save_session_summary(
    user_id: str,
    session_id: str,
    topics: list[str],
    summary: str,
    title: str = "",
    message_count: int = 0,
):
    """保存或更新会话摘要（UPSERT：冲突时更新）"""
    db = await get_db()
    await db.execute(
        """INSERT INTO conversation_summaries
           (user_id, session_id, topics, summary, title, message_count, updated_at)
           VALUES (?, ?, ?, ?, ?, ?, datetime('now'))
           ON CONFLICT(session_id) DO UPDATE SET
               topics = excluded.topics,
               summary = excluded.summary,
               title = excluded.title,
               message_count = excluded.message_count,
               updated_at = datetime('now')""",
        (user_id, session_id, json.dumps(topics, ensure_ascii=False), summary, title, message_count),
    )
    await db.commit()
    await db.close()
    

async def list_sessions(user_id: str, limit: int = 20, offset: int = 0) -> list[dict]:
    """获取用户会话列表，按更新时间倒序"""

    db = await get_db()
    cursor = await db.execute(
        "SELECT session_id, title, topics, message_count, created_at, updated_at "
        "FROM conversation_summaries WHERE user_id = ? "
        "ORDER BY updated_at DESC LIMIT ? OFFSET ?",
        (user_id, limit, offset),
    )
    rows = await cursor.fetchall()
    await db.close()
    return [dict(row) for row in rows]

async def delete_session(session_id: str):
    """删除指定会话摘要"""
    db = await get_db()
    await db.execute("DELETE FROM conversation_summaries WHERE session_id = ?", (session_id,))
    await db.commit()
    await db.close()


async def record_interaction(user_id: str, chapter_id: str, topic: str):
    """记录一次学习互动（L3 预留）"""
    # TODO: 实现
    # 1. INSERT OR REPLACE (ON CONFLICT ... DO UPDATE)
    # 2. interactions + 1, last_reviewed = datetime('now')
    db = await get_db()
    await db.execute(
        """INSERT INTO learning_progress
           (user_id, chapter_id, topic, interactions, last_reviewed)
           VALUES (?, ?, ?, 1, datetime('now'))
           ON CONFLICT(user_id, chapter_id, topic) DO UPDATE SET
               interactions = interactions + 1,
               last_reviewed = datetime('now')""",
        (user_id, chapter_id, topic),
    )
    await db.commit()
    await db.close()