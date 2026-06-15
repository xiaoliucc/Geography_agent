"""
向量数据库封装 — ChromaDB 检索 + DashScope 嵌入

将旧项目 rag_system.py 中的 search() 和 embed_text() 逻辑
封装为可复用的工具层。

## 使用方式

```python
from db import search_textbook, embed_text, get_all_vector_dbs

# 嵌入查询
embedding = await embed_text("大气环流")

# 检索
results = await search_textbook(embedding, top_k=5, chapter_id="bixiu_1_ch2")

# 列出已索引教材
dbs = get_all_vector_dbs()
```
"""

import os
import hashlib
import chromadb
import dashscope
from chromadb.config import Settings
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), "..", "..", ".env"))

# materials/processed/ 的绝对路径
MATERIALS_DIR = os.path.join(
    os.path.dirname(__file__), "..", "..", "materials", "processed"
)
# 嵌入缓存（进程内，避免重复 API 调用）
_embedding_cache: dict = {}

CHROMADB_SETTINGS = Settings(
    persist_directory="",# 数据库保存路径
    allow_reset=True,# 是否允许重置数据库
    is_persistent=True,# 是否持久化数据库
)

def get_all_vector_dbs() -> list[dict]:
    """
    列出所有已索引的教材向量数据库

    Returns:
        [{
            "name": "教材名",
            "path": "数据库路径",
            "collection": "向量集合名",
        }, ...]
    """
    vector_dbs = []
    if not os.path.exists(MATERIALS_DIR):
        return vector_dbs
    
    for root, dirs, _ in os.walk(MATERIALS_DIR):
        """
        root: 路径 str
        dirs: 子文件夹名称 list
        files: 文件名称 list
        """
        if "vector_db" in dirs:
            # 计算数据库绝对存储路径
            db_path = os.path.join(root, "vector_db")
            # 计算相对路径
            rel_path = os.path.relpath(root, MATERIALS_DIR)
            # 计算数据库名称 相对路径中的路径分隔符替换为下划线
            db_name = rel_path.replace(os.sep, "_")

            vector_dbs.append({
                "name": db_name,
                "path": db_path,
                "collection": "geography_full",
            })
    return vector_dbs
      
    

async def embed_text(text: str) -> list[float]:
    """
    文本嵌入（DashScope text-embedding-v4），带进程内缓存

    Args:
        text: 待嵌入文本

    Returns:
        1024 维浮点向量
    """
    text_bytes = text.encode("utf-8") # 计算文本的哈希值
    cache_key = hashlib.md5(text_bytes).hexdigest() # 创建 ChromaDB 客户端
    
    # 从缓存中获取嵌入向量
    if cache_key in _embedding_cache:
        return _embedding_cache[cache_key]

    # 创建 DashScope API 客户端
    resp = dashscope.TextEmbedding.call(
        model="text-embedding-v4",
        input=text,
        api_key=os.getenv("DASHSCOPE_API_KEY"),
        )
    
    # 检查 API 调用是否成功
    if resp.status_code != 200:
        raise Exception(f"DashScope API 调用失败: {resp.message}")
    
    
    """
    {
        "request_id": "...",
        "output": {
            "embeddings": [
                {
                    "embedding": [
                        0.123,
                        0.456,
                        ...
                    ],
                    "input": "..."
                }
            ]
        }
    }
    """
    embedding = resp.output["embeddings"][0]["embedding"] # 返回嵌入向量
    
    _embedding_cache[cache_key] = embedding # 缓存嵌入向量
    
    return embedding # 返回嵌入向量
    

async def search_textbook(
    query_embedding: list[float],
    top_k: int = 5,
    chapter_id: str = None,
    textbook_filter: list[str] = None,
) -> list[dict]:
    
    all_dbs = get_all_vector_dbs()
    if not all_dbs:
        return []
    if textbook_filter and isinstance(textbook_filter, list):
        all_dbs = [db for db in all_dbs if db["name"] in textbook_filter]
        if not all_dbs:
            return []
    all_results = []
    for db_info in all_dbs:
        db_path = db_info["path"]
        db_name = db_info["name"]
        coll_name = db_info["collection"]
        
        client = chromadb.PersistentClient(
            path=db_path,
            settings=CHROMADB_SETTINGS,
        )
        try:
            collection = client.get_collection(name=coll_name) # 获取向量集合
        except Exception as e:
            print(f"向量数据库 {db_name} 创建失败: {e}")
            continue
        
        where_filter = {}
        if chapter_id:
            where_filter["chapter_id"] = chapter_id
            
        query_params = {
            "query_embeddings": [query_embedding], # 查询向量
            "n_results": top_k, # 返回数量
        }
        if where_filter:
            query_params["where"] = where_filter
        
        res = collection.query(**query_params) # 查询向量数据库 **解包query_params
        
        documents = res.get("documents", [[]])[0]
        metadatas = res.get("metadatas", [[]])[0]
        distances = res.get("distances", [[]])[0]
    
        for doc, meta,dist in zip(documents, metadatas,distances):
            if not doc or not meta:
                continue
            item = {
                "content": doc,
                "metadata": meta,
                "distance": dist,
                "source": "local",
                "textbook": db_name,
            }
            all_results.append(item)
    
    all_results.sort(key=lambda x: x["distance"])
    final_results = all_results[:top_k]
    return final_results