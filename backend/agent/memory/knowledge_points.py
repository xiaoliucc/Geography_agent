"""知识点匹配 — 将用户搜索话题映射到课标知识点"""

import json
import pathlib

_KP_PATH = pathlib.Path(__file__).parent.parent.parent / "config" / "knowledge_points.json"
_KP_CACHE = None


def _load():
    global _KP_CACHE
    if _KP_CACHE is None:
        _KP_CACHE = json.loads(_KP_PATH.read_text(encoding="utf-8"))
    return _KP_CACHE


def match_knowledge_points(topic: str) -> list[dict]:
    """根据话题文本匹配最相关的知识点"""
    data = _load()
    matches = []
    for textbook_id, textbook in data.items():
        for ch_id, chapter in textbook.get("chapters", {}).items():
            for point in chapter.get("points", []):
                # 简单子串匹配（后期可换 embedding 语义匹配）
                if any(word in point for word in topic) or any(word in topic for word in point[:4]):
                    matches.append({
                        "textbook": textbook_id,
                        "chapter_id": ch_id,
                        "chapter_title": chapter["title"],
                        "point": point,
                        "score": len(set(topic) & set(point)) / max(len(topic), 1),
                    })
    # 按匹配度排序，去重
    seen = set()
    result = []
    for m in sorted(matches, key=lambda x: x["score"], reverse=True):
        if m["point"] not in seen:
            seen.add(m["point"])
            result.append(m)
    return result[:5]


def list_all_points() -> list[dict]:
    """列出所有知识点"""
    data = _load()
    result = []
    for textbook_id, textbook in data.items():
        for ch_id, chapter in textbook.get("chapters", {}).items():
            for point in chapter.get("points", []):
                result.append({
                    "textbook": textbook_id,
                    "chapter_id": ch_id,
                    "chapter_title": chapter["title"],
                    "point": point,
                })
    return result
