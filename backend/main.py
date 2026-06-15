"""
统一 FastAPI 入口

启动方式:
    cd backend
    venv\Scripts\activate
    python main.py

    或: uvicorn main:app --reload --host 0.0.0.0 --port 8000
"""

from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from api_v2.middleware import RequestIDMiddleware,LoggingMiddleware

base_dir = Path(__file__).resolve().parent  # backend/
materials_dir = base_dir.parent / "materials"  # 项目根目录/materials

# ── 创建应用 ──
app = FastAPI(
    title="RAG Geography Agent",
    version="2.0.0",
    description="高中地理智能教学 Agent 系统"
)


app.add_middleware(
    CORSMiddleware, #CORSMiddleware配置跨域策略，允许指定源、凭证及所有方法头；
    allow_origins=["http://localhost:5173", "http://localhost:5174", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(RequestIDMiddleware),#RequestIDMiddleware用于生成请求ID
app.add_middleware(LoggingMiddleware) #LoggingMiddleware负责记录日志。旨在增强API的安全性、可追踪性及可观测性。


# ── API ──
from api_v2.health import router as health_router
from api_v2.user import router as user_router
from api_v2.chat import router as chat_router
from api_v2.quiz import router as quiz_router

app.include_router(health_router, prefix="/api/v2")
app.include_router(user_router, prefix="/api/v2")
app.include_router(chat_router, prefix="/api/v2")
app.include_router(quiz_router, prefix="/api/v2")

# ── 旧版 API（向后兼容，后续挂载） ──
# from legacy_api import router as legacy_router
# app.include_router(legacy_router, prefix="/api")

# ── 静态文件 ──
app.mount("/materials", StaticFiles(directory=materials_dir), name="materials")


@app.get("/")
async def root():
    """
    根路由，返回 API 文档
    """
    return {"message": "RAG Geography Agent API v2.0.0", "docs": "/docs"}

# ── 启动入口 ──
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
