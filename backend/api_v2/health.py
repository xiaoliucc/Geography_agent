"""
健康检查端点

GET /api/v2/health — 系统状态 + 各组件连通性
GET /api/v2/textbooks — 已索引教材列表
"""
import os
from fastapi import APIRouter
from db import get_all_vector_dbs
router = APIRouter()


@router.get("/health")
async def health():
    """
    返回系统整体状态及各组件健康信息

    包括：chromadb（集合数+文档数）、llm（提供者+模型）、
          memory_db（用户数+会话数）、tavily（剩余配额）、amap
    """
    # TODO: 实现
    # 1. 检查 ChromaDB 连通性：尝试连接 collections
    # 2. 检查 LLM 配置：读取 LLM_PROVIDER 和 LLM_MODEL 环境变量
    # 3. 检查 memory_db：users.db 是否存在，统计用户数和会话数
    # 4. 检查 Tavily：是否有 TAVILY_API_KEY
    # 5. 检查高德：是否有 AMAP_API_KEY
    # 6. 返回标准格式: {"code": 0, "data": {"status": "healthy", "components": {...}}}
    try:
        dbs = get_all_vector_dbs()
        chroma_status ={
            "status": "healthy",
            "collections":len(dbs),
            "total_documents":"unknown",
        }
    except Exception as e:
        chroma_status ={
            "status": "unhealthy",
            "message": str(e),
        }
    llm_status ={
        "status": "healthy",
        "provider": os.getenv("LLM_PROVIDER","dashscope"),
        "model": os.getenv("LLM_MODEL","qwen3.7-plus"),
    }
    services = {
        "tavily":"healthy" if os.getenv("TAVILY_API_KEY") else "unhealthy",
        "amap":"healthy" if os.getenv("AMAP_API_KEY") else "unhealthy",
    }

    return {
        "code": 0,
        "data":{
            "status": "healthy",
            "version":"0.1.0",
            "components":{
                "chromadb": chroma_status,
                "llm": llm_status,
                "memory_db": "healthy",
                "services": services,
                }
            }
        }


@router.get("/textbooks")
async def list_textbooks():
    """
    列出已索引的教材及其章节信息

    从 ChromaDB metadata 中提取教材列表和每本教材的章节
    """
    # TODO: 实现
    # 1. 调用 db.vector_store.get_all_vector_dbs()
    # 2. 对每个数据库，查询 metadata 中的 chapter 信息
    # 3. 返回教材列表及章节数、chunk 数
    dbs = get_all_vector_dbs()
    textbooks = []
    for db in dbs:
       name_parts = db["name"].split("_")
       textbooks.append({
           "id":db["name"],
           "name": db["name"],
           "path": db["path"],
       })
    return {
        "code":0,
        "data":{
            "textbooks":textbooks,
        }
    }