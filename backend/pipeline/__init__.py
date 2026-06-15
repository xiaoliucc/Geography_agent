"""Qwen-VL 共用客户端（OCR + 增强管道共用）"""
import os, base64
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), "..", "..", ".env"))
_client = None


def get_client():
    global _client
    if _client is None:
        _client = OpenAI(api_key=os.getenv("DASHSCOPE_API_KEY"),
                         base_url="https://dashscope.aliyuncs.com/compatible-mode/v1")
    return _client


def ask(prompt: str, image_b64: str = None, max_tokens: int = 500) -> str:
    """调用 Qwen-VL，可选传图"""
    content = []
    if image_b64:
        content.append({"type": "image_url", "image_url": {"url": f"data:image/png;base64,{image_b64}"}})
    content.append({"type": "text", "text": prompt})

    resp = get_client().chat.completions.create(
        model="qwen-vl-plus", messages=[{"role": "user", "content": content}],
        max_tokens=max_tokens,
    )
    return resp.choices[0].message.content or ""
