"""
Quiz 端点 (Phase 3)

POST /api/v2/quiz/generate  — 生成试题
POST /api/v2/quiz/evaluate   — 批改答案
"""

from fastapi import APIRouter
from pydantic import BaseModel

from agent.tools.quiz_tools import generate_quiz, evaluate_answer

router = APIRouter()


class QuizGenerateRequest(BaseModel):
    topic: str
    question_count: int = 5
    difficulty: str = "medium"
    question_types: str = "multiple_choice,short_answer"
    exam_style: str = "gaokao"
    user_id: str = ""


class QuizEvaluateRequest(BaseModel):
    question: str
    student_answer: str
    user_id: str = ""


@router.post("/quiz/generate")
async def generate(request: QuizGenerateRequest):
    result = await generate_quiz.ainvoke({
        "topic": request.topic,
        "question_count": request.question_count,
        "difficulty": request.difficulty,
        "question_types": request.question_types,
    })
    if result["status"] == "success":
        return {"code": 0, "data": result["data"]}
    return {"code": 5002, "message": result.get("error", "生成失败"), "data": None}


@router.post("/quiz/evaluate")
async def evaluate(request: QuizEvaluateRequest):
    result = await evaluate_answer.ainvoke({
        "question": request.question,
        "student_answer": request.student_answer,
    })
    if result["status"] == "success":
        return {"code": 0, "data": result["data"]}
    return {"code": 5002, "message": result.get("error", "评估失败"), "data": None}
