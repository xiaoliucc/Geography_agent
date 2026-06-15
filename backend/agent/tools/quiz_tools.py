"""
出题与批改工具
"""

import json
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage


@tool
async def generate_quiz(
    topic: str,
    question_count: int = 5,
    difficulty: str = "medium",
    question_types: str = "multiple_choice,short_answer",
) -> dict:
    """根据指定主题和难度生成地理测试题。

    适用场景：学生主动要求做题、测试、练习。

    Args:
        topic: 测试主题
        question_count: 题目数量，默认 5
        difficulty: easy | medium | hard
        question_types: 题型，逗号分隔

    Returns:
        {"status": "success", "data": {"title": "...", "questions": [...]}}
    """
    from config.settings import LLMFactory

    types_list = [t.strip() for t in question_types.split(",")]
    llm = LLMFactory.create_for_agent("quiz")

    prompt = f"""你是一位高中地理出题老师。请生成 {question_count} 道地理测试题。

主题：{topic}
难度：{difficulty}
题型：{', '.join(types_list)}

请只输出纯 JSON，不要加任何解释或 markdown 标记。JSON 结构示例：
{{
    "title": "大气环流 - 巩固练习",
    "questions": [
        {{
            "id": 1,
            "type": "multiple_choice",
            "question": "题目正文",
            "options": ["A. 选项A", "B. 选项B", "C. 选项C", "D. 选项D"],
            "answer": "B",
            "explanation": "解析",
            "difficulty": "medium",
            "knowledge_point": "考查知识点",
            "chapter_ref": "教材出处"
        }}
    ]
}}

要求：
1. 每道题标注 knowledge_point 和 chapter_ref
2. 选择题必须有 4 个选项，选项要有迷惑性
3. 简答题提供参考答案
4. 难度分布：easy 40%, medium 40%, hard 20%"""

    try:
        response = await llm.ainvoke([HumanMessage(content=prompt)])
        content = response.content.strip()
        if not content:
            return {"status": "error", "error": "LLM returned empty", "source": "computed"}

        # 提取 JSON（可能被 markdown 包裹）
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0]
        elif "```" in content:
            content = content.split("```")[1].split("```")[0]
        quiz_data = json.loads(content)
        return {"status": "success", "data": quiz_data, "source": "computed"}
    except json.JSONDecodeError as e:
        return {"status": "error", "error": f"JSON parse failed: {e}", "data_raw": content[:200], "source": "computed"}
    except Exception as e:
        return {"status": "error", "error": str(e), "source": "computed"}


@tool
async def evaluate_answer(question: str, student_answer: str) -> dict:
    """评估学生答案，给出评分和详细反馈。

    Args:
        question: 原题
        student_answer: 学生答案

    Returns:
        {"status": "success", "data": {"score": 8.5, "feedback": "...", ...}}
    """
    from config.settings import LLMFactory

    llm = LLMFactory.create_for_agent("quiz", max_tokens=1024)

    prompt = f"""你是一位高中地理老师，正在批改学生答案。

原题：{question}
学生答案：{student_answer}

请只输出纯 JSON：
{{
    "score": 8,
    "is_correct": true,
    "feedback": "整体评价",
    "point_by_point": [
        {{"point": "知识点", "status": "correct", "comment": "说明"}}
    ],
    "improvement": "改进建议"
}}"""

    try:
        response = await llm.ainvoke([HumanMessage(content=prompt)])
        content = response.content.strip()
        if not content:
            return {"status": "error", "error": "LLM returned empty", "source": "computed"}

        if "```" in content:
            content = content.split("```")[1].split("```")[0]
            if content.startswith("json"):
                content = content[4:]
        result = json.loads(content)
        return {"status": "success", "data": result, "source": "computed"}
    except Exception as e:
        return {"status": "error", "error": str(e), "source": "computed"}
