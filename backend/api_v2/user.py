"""
用户相关端点

GET  /api/v2/user/profile?user_id=xxx       — 获取用户档案
PUT  /api/v2/user/profile                    — 更新用户档案
GET  /api/v2/user/sessions?user_id=xxx       — 会话列表
POST /api/v2/user/session                    — 保存会话摘要
GET  /api/v2/user/sessions/{session_id}/messages — 获取会话消息
DELETE /api/v2/user/sessions/{session_id}         — 删除会话
GET  /api/v2/user/progress?user_id=xxx            — 获取学习进度
"""

import json
import pathlib
from fastapi import APIRouter, Query
from pydantic import BaseModel
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver

from agent import get_checkpointer_db
import agent.memory.user_profile
from agent.memory.knowledge_points import match_knowledge_points

router = APIRouter()


class UpdateProfileRequest(BaseModel):
    user_id: str
    grade: str = ""
    textbook: str = "renjiao"


class SaveSessionRequest(BaseModel):
    user_id: str
    session_id: str
    topics: list[str] = []
    summary: str = ""
    title: str = ""
    message_count: int = 0


# ── TODO: 实现以下端点 ──

@router.get("/user/profile")
async def get_profile(user_id: str = Query(...)):
    """
    获取用户档案。如果用户不存在，自动创建并返回 is_new=True。
    计算 total_sessions 和 recent_topics。
    """
    user = await agent.memory.user_profile.get_or_create_user(user_id)

    # 补充统计数据：总会话数 + 最近话题
    db = await agent.memory.user_profile.get_db()
    cursor = await db.execute(
        "SELECT COUNT(*) as cnt FROM conversation_summaries WHERE user_id = ?",
        (user_id,),
    )
    row = await cursor.fetchone()
    user["total_sessions"] = row["cnt"] if row else 0

    cursor = await db.execute(
        "SELECT topics FROM conversation_summaries WHERE user_id = ? "
        "ORDER BY updated_at DESC LIMIT 5",
        (user_id,),
    )
    rows = await cursor.fetchall()
    recent_topics: list[str] = []
    for r in rows:
        try:
            topics = json.loads(r["topics"]) if isinstance(r["topics"], str) else (r["topics"] or [])
            for t in topics:
                if t and t not in recent_topics:
                    recent_topics.append(t)
        except (json.JSONDecodeError, TypeError):
            pass
    user["recent_topics"] = recent_topics[:10]
    await db.close()

    return {
        "code": 0,
        "data": user,
    }

@router.put("/user/profile")
async def update_profile(request: UpdateProfileRequest):
    """
    更新用户档案。允许更新 grade 和 textbook 字段。
    """
    # TODO: 调用 agent.memory.user_profile.update_user_profile(...)
    user = await agent.memory.user_profile.update_user_profile(
        request.user_id,
        grade=request.grade,
        textbook=request.textbook,
    )
    return {
        "code": 0,
        "data": user,
    }


@router.get("/user/sessions")
async def list_sessions(
    user_id: str = Query(...),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    """
    获取用户的历史会话列表，按更新时间倒序排列。
    """
    # TODO: 调用 agent.memory.user_profile.list_sessions(user_id, limit, offset)
    user = await agent.memory.user_profile.list_sessions(user_id, limit, offset)
    return {
        "code": 0,
        "data": user,
    }


@router.post("/user/session")
async def save_session(request: SaveSessionRequest):
    """
    保存会话摘要（对话结束后由前端异步调用）。
    """
    # TODO: 调用 agent.memory.user_profile.save_session_summary(...)
    # TODO: 对每个 topic 调用 agent.memory.user_profile.record_interaction(...)
    await agent.memory.user_profile.save_session_summary(
        request.user_id,
        request.session_id,
        request.topics,
        request.summary,
        request.title,
        request.message_count,
    )
    # L3: 匹配知识点并记录互动
    for topic in request.topics:
        for kp in match_knowledge_points(topic):
            await agent.memory.user_profile.record_interaction(
                request.user_id,
                f"{kp['textbook']}_{kp['chapter_id']}",
                kp["point"],
            )
    return {
        "code": 0,
        "data": {"saved": True},
    }


@router.get("/user/sessions/{session_id}/messages")
async def get_session_messages(session_id: str):
    """获取指定会话的历史消息（从 LangGraph checkpointer 读取）"""
    db_path = get_checkpointer_db()
    async with AsyncSqliteSaver.from_conn_string(db_path) as cp:
        state = await cp.aget_tuple({"configurable": {"thread_id": session_id}})
        if not state or not state.checkpoint:
            return {"code": 0, "data": {"messages": []}}

        channel_values = state.checkpoint.get("channel_values", {})
        raw_messages = channel_values.get("messages", [])

        messages = []
        for m in raw_messages:
            msg_type = type(m).__name__
            content = m.content if hasattr(m, "content") else str(m)
            if msg_type == "HumanMessage":
                messages.append({"type": "user", "data": {"text": content}})
            elif msg_type == "AIMessage":
                messages.append({"type": "answer", "data": {"text": content}})
            elif msg_type == "ToolMessage":
                messages.append({"type": "tool_result", "data": {"text": content}})

    return {"code": 0, "data": {"messages": messages}}


@router.delete("/user/sessions/{session_id}")
async def delete_session(session_id: str):
    """删除指定会话"""
    await agent.memory.user_profile.delete_session(session_id)
    return {"code": 0, "data": {"deleted": True}}


@router.get("/user/progress")
async def get_progress(user_id: str = Query(...)):
    """获取用户的学习进度（按知识点维度）"""
    from agent.memory.knowledge_points import list_all_points
    import aiosqlite
    import json

    db_path = (
        pathlib.Path(__file__).parent.parent.parent / "memory" / "users.db"
    )
    db = await aiosqlite.connect(str(db_path))
    db.row_factory = aiosqlite.Row

    cursor = await db.execute(
        "SELECT chapter_id, topic, interactions, last_reviewed "
        "FROM learning_progress WHERE user_id = ? "
        "ORDER BY interactions DESC LIMIT 50",
        (user_id,),
    )
    rows = await cursor.fetchall()
    await db.close()

    progress = [dict(r) for r in rows]
    all_points = list_all_points()

    return {
        "code": 0,
        "data": {
            "progress": progress,
            "total_points": len(all_points),
            "learned_points": len(progress),
        },
    }
