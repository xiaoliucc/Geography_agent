"""
记忆系统 — L1 对话记忆 (LangGraph AsyncSqliteSaver)

每次请求在 event_stream 内部创建新的 checkpointer，
用完即弃，避免连接重用问题。

## 使用方式

```python
from agent import get_checkpointer_db

db_path = get_checkpointer_db()
async with AsyncSqliteSaver.from_conn_string(db_path) as checkpointer:
    graph = compile_supervisor(checkpointer=checkpointer)
    config = {"configurable": {"thread_id": session_id}}
    result = await graph.ainvoke(initial_state, config)
```
"""

import os

MEMORY_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "memory")


def get_checkpointer_db() -> str:
    """获取 checkpointer 数据库路径，确保目录存在"""
    os.makedirs(MEMORY_DIR, exist_ok=True)
    return os.path.join(MEMORY_DIR, "conversations.db")
