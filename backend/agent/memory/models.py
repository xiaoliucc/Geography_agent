"""
L2 用户档案 — SQLite CRUD

初版实现：user_profiles + conversation_summaries 两张表
L3 learning_progress 表已建，数据写入预留。

## 使用方式

```python
from agent.memory.user_profile import (
    get_or_create_user,
    update_user_profile,
    save_session_summary,
    list_sessions,
    record_interaction,
)
```
"""

# 建表 SQL（首次调用 get_db() 时自动执行）
SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS user_profiles (
    user_id      TEXT PRIMARY KEY,
    grade        TEXT DEFAULT '',
    textbook     TEXT DEFAULT 'renjiao',
    created_at   TEXT DEFAULT (datetime('now')),
    updated_at   TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS conversation_summaries (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id       TEXT NOT NULL,
    session_id    TEXT NOT NULL UNIQUE,
    title         TEXT DEFAULT '',
    topics        TEXT DEFAULT '[]',
    summary       TEXT DEFAULT '',
    message_count INTEGER DEFAULT 0,
    created_at    TEXT DEFAULT (datetime('now')),
    updated_at    TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (user_id) REFERENCES user_profiles(user_id)
);

CREATE TABLE IF NOT EXISTS learning_progress (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id        TEXT NOT NULL,
    chapter_id     TEXT NOT NULL,
    chapter_name   TEXT DEFAULT '',
    topic          TEXT DEFAULT '',
    interactions   INTEGER DEFAULT 1,
    quiz_attempts  INTEGER DEFAULT 0,
    avg_quiz_score REAL DEFAULT 0,
    mastery_level  TEXT DEFAULT '基础',
    last_reviewed  TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (user_id) REFERENCES user_profiles(user_id),
    UNIQUE(user_id, chapter_id, topic)
);

CREATE INDEX IF NOT EXISTS idx_summaries_user
    ON conversation_summaries(user_id, updated_at DESC);
CREATE INDEX IF NOT EXISTS idx_progress_user
    ON learning_progress(user_id, chapter_id);
"""
