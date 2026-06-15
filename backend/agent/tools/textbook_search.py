"""
教材检索工具 — 包装 db 模块的 ChromaDB 搜索
"""

from langchain_core.tools import tool


@tool
async def search_textbook(
    query: str,
    top_k: int = 5,
    chapter_id: str = "",
) -> dict:
    """搜索高中地理教材内容。回答地理知识问题时优先使用此工具。

    适用场景：学生提问地理概念、原理、现象时。
    不适用：数值计算（用 calculate）、出题请求（用 generate_quiz）。

    Args:
        query: 搜索关键词，建议使用地理术语
        top_k: 返回结果数量，默认 5
        chapter_id: 可选，限定章节，如 "bixiu_1_ch2"

    Returns:
        {
            "status": "success",
            "data": [{"content": "...", "metadata": {...}, "distance": 0.23}],
            "source": "local"
        }
    """
    from db import embed_text, search_textbook as _search

    try:
        embedding = await embed_text(query)
        results = await _search(
            embedding,
            top_k=top_k,
            chapter_id=chapter_id or None,
        )
        # 截断每条结果，省 token
        MAX_CHARS = 400
        for r in results:
            if len(r.get("content", "")) > MAX_CHARS:
                r["content"] = r["content"][:MAX_CHARS] + "..."
        return {
            "status": "success",
            "data": results[:top_k],
            "source": "local",
        }
    except Exception as e:
        return {"status": "error", "error": str(e), "data": [], "source": "local"}
