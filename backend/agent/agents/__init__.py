"""
Agent 定义（简化版）

单 Teacher Agent 包含全部工具：
- search_textbook / web_search — 信息检索
- calculate — 地理计算
- generate_quiz / evaluate_answer — 出题与批改
"""

import pathlib
from langgraph.prebuilt import create_react_agent
from config.settings import LLMFactory

_PROMPT_DIR = pathlib.Path(__file__).parent.parent.parent / "config" / "prompts"


def _load_persona(name: str) -> str:
    p = _PROMPT_DIR / "personas" / f"{name}.md"
    return p.read_text(encoding="utf-8") if p.exists() else ""


def _load_skills(*names: str) -> str:
    parts = []
    for name in names:
        p = _PROMPT_DIR / "skills" / f"{name}.md"
        if p.exists():
            parts.append(p.read_text(encoding="utf-8"))
    return "\n\n".join(parts)


def create_teacher_agent():
    """创建全能教学助教，包含所有工具"""
    from agent.tools.textbook_search import search_textbook
    from agent.tools.web_search import web_search
    from agent.tools.calculator import calculate
    from agent.tools.quiz_tools import generate_quiz, evaluate_answer
    from agent.tools.system_tools import list_available_textbooks

    llm = LLMFactory.create_for_agent("teacher")
    system = _load_persona("teacher") + "\n\n" + _load_skills("quiz_format")

    return create_react_agent(
        llm,
        [search_textbook, web_search, calculate, generate_quiz, evaluate_answer, list_available_textbooks],
        prompt=system,
    )
