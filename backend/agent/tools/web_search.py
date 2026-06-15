"""
网络搜索工具 — Tavily API
仅在教材无覆盖时使用，回答中必须标注 🌐网络 来源
"""

import os
from langchain_core.tools import tool


@tool
async def web_search(query: str, max_results: int = 3) -> dict:
    """搜索互联网获取补充信息。仅在教材中没有相关信息时使用。

    重要规则：
    1. 必须优先使用 search_textbook，确认教材无覆盖后才使用此工具
    2. 回答中必须明确标注 🌐网络 来源
    3. 不使用于教材已有明确答案的问题

    Args:
        query: 搜索关键词
        max_results: 返回结果数量，默认 3

    Returns:
        {"status": "success", "data": [{"title":.., "content":.., "url":..}], "source": "web"}
    """
    api_key = os.getenv("TAVILY_API_KEY")
    if not api_key:
        return {"status": "error", "error": "Tavily API key not configured", "data": [], "source": "web"}

    try:
        from tavily import TavilyClient
        client = TavilyClient(api_key=api_key)
        response = client.search(
            query=query,
            max_results=max_results,
            search_depth="advanced",
            include_answer=True,
        )
        results = [
            {
                "title": r.get("title", ""),
                "content": r.get("content", ""),
                "url": r.get("url", ""),
            }
            for r in response.get("results", [])
        ]
        return {
            "status": "success",
            "data": results,
            "source": "web",
            "metadata": {"ai_answer": response.get("answer", "")},
        }
    except Exception as e:
        return {"status": "error", "error": str(e), "data": [], "source": "web"}
