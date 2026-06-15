"""
中间件：请求追踪 + 日志 + CORS
"""

# TODO: 实现以下中间件

# 1. RequestIDMiddleware
#    - 从 X-Request-Id 请求头读取或自动生成 request_id
#    - 存储在 request.state.request_id
#    - 响应头添加 X-Request-Id

# 2. LoggingMiddleware
#    - 记录每个请求的 method + path + status_code + elapsed_ms
#    - 使用 logging 标准库

# 3. CORS（开发环境）
#    - 允许 localhost:5173, localhost:5174
#    - 用 fastapi.middleware.cors.CORSMiddleware

import uuid
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

class RequestIDMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get("X-Request-Id",str(uuid.uuid4())[:8])
        request.state.request_id = request_id
        response = await call_next(request)
        response.headers["X-Request-Id"] = request_id
        return response
    

import logging
import time

logger = logging.getLogger("api")

class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        response = await call_next(request)
        elapsed = int((time.time() - start_time) * 1000)
        logger.info(
            "%s %s → %s (%.0f ms)",
            request.method,
            request.url.path,
            response.status_code,
            elapsed,
        )
        return response