"""
异常处理 + 错误码体系

## 错误码

    1xxx: 请求参数错误
    4xxx: Agent 执行错误
    5xxx: 外部服务错误
    9xxx: 系统内部错误

## 使用方式

```python
from api_v2.exceptions import APIError, api_error_handler

raise APIError(code=4001, message="Agent 执行超时", http_status=504)

@router.post("/chat")
@api_error_handler
async def chat(...):
    ...
```
"""

from fastapi.responses import JSONResponse
import functools
import logging

logger = logging.getLogger(__name__) # 日志

_ERROR_MAP = { # 自定义错误码映射
    ValueError: (1002,400),
    TypeError: (1002, 400),
    TimeoutError: (4001,504),
    ConnectionError: (5004, 502),
}

class APIError(Exception):
    """统一 API 异常"""
    def __init__(self, code: int, message: str, http_status: int = 500, detail: dict = None):
        self.code = code
        self.message = message
        self.http_status = http_status
        self.detail = detail or {}


def api_error_handler(func):
    """
    装饰器：统一捕获异常并返回标准 JSON 格式

    将 Python 异常映射为结构化错误响应：
    {
        "code": 4001,
        "message": "...",
        "data": null,
        "request_id": "..."
    }
    """
    @functools.wraps(func) # 保留元数据
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except APIError as e:
            return JSONResponse(
                status_code=e.http_status,
                content={
                    "code": e.code,
                    "message": e.message,
                    "data": None,
                    "detail": e.detail
                }
            )
        except Exception as e:
            for exc__type,(code,http_status) in _ERROR_MAP.items():
                if isinstance(e, exc__type):
                    return JSONResponse(
                        status_code=http_status,
                        content={
                            "code": code,
                            "message": str(e),
                            "data": None,
                            "detail": {}
                        }
                    )
        logger.exception("Unhandled error in %s", func.__name__)
        return JSONResponse(
            status_code=500,
            content={
                "code": 9001,
                "message": "系统内部错误",
                "data": None,
                "detail": {}
            }
        )
    return wrapper
