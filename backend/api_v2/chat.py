"""
主对话端点（单 Teacher Agent + 全部工具）

POST /api/v2/chat        — 主对话入口 (SSE 流式)
POST /api/v2/agent/approve — Map 授权确认
"""

import json
import uuid

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from langchain_core.messages import HumanMessage
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver

from agent import get_checkpointer_db
from agent.agents import create_teacher_agent

router = APIRouter()


class ChatRequest(BaseModel):
    message: str
    user_id: str
    session_id: str | None = None
    stream: bool = True
    mode: str = "chat"


def _sse(event: str, data: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


def _safe_serialize(obj) -> dict:
    try:
        return json.loads(json.dumps(obj, default=str))
    except Exception:
        return {"raw": str(obj)}


@router.post("/chat")
async def chat(request: ChatRequest):
    session_id = request.session_id or f"sess_{uuid.uuid4().hex[:8]}"
    db_path = get_checkpointer_db()

    async def event_stream():
        async with AsyncSqliteSaver.from_conn_string(db_path) as checkpointer:
            graph = create_teacher_agent()
            graph.checkpointer = checkpointer
            config = {
                "configurable": {
                    "thread_id": session_id,
                    "user_id": request.user_id,
                }
            }
            initial_state = {
                "messages": [HumanMessage(content=request.message)],
            }

            yield _sse("session_start", {
                "session_id": session_id,
                "user_id": request.user_id,
            })

            async for event in graph.astream_events(initial_state, config, version="v2"):
                kind = event["event"]

                if kind == "on_tool_start":
                    tool_name = event.get("name", "")
                    tool_input = event.get("data", {}).get("input", {})
                    labels = {
                        "search_textbook": "正在检索教材...",
                        "web_search": "正在搜索网络...",
                        "generate_quiz": "正在生成题目...",
                        "evaluate_answer": "正在评估答案...",
                        "calculate": "正在计算...",
                    }
                    yield _sse("tool_call", {
                        "tool": tool_name,
                        "label": labels.get(tool_name, tool_name),
                        "args": _safe_serialize(tool_input),
                    })

                elif kind == "on_tool_end":
                    output = event.get("data", {}).get("output", {})
                    if isinstance(output, dict):
                        yield _sse("tool_result", {
                            "tool": event.get("name", ""),
                            "status": output.get("status", "success"),
                            "result_count": len(output.get("data", [])),
                            "source": output.get("source", ""),
                        })

                elif kind == "on_chat_model_stream":
                    chunk = event["data"]["chunk"]
                    if hasattr(chunk, "content") and chunk.content:
                        yield _sse("chunk", {"text": chunk.content})

            yield _sse("done", {
                "session_id": session_id,
                "message": "回答完成",
            })

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )
