"""
LLM Provider Factory — 统一 LLM 创建入口

支持：DashScope (阿里云百炼) + DeepSeek
Agent 配置：config/agents.json

## 使用方式

```python
from config.settings import LLMFactory

# 默认模型（从 .env 读取）
llm = LLMFactory.create()

# 指定提供者和模型
llm = LLMFactory.create(provider="deepseek", model="deepseek-chat")

# 按 Agent 类型创建专用 LLM（从 agents.json 读取配置）
llm = LLMFactory.create_for_agent("teacher")
```
"""

import json
import os
import pathlib

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

load_dotenv()

_CONFIG_DIR = pathlib.Path(__file__).parent


class LLMFactory:
    """多 LLM 提供商工厂，支持按 Agent 类型独立配置模型"""

    _instances: dict = {} # 缓存实例

    _PROVIDERS = {
        "dashscope": {
            "api_key": os.getenv("DASHSCOPE_API_KEY"),
            "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
        },
        "deepseek": {
            "api_key": os.getenv("DEEPSEEK_API_KEY"),
            "base_url": "https://api.deepseek.com",
            "extra": {"extra_body": {"thinking": {"type": "disabled"}}},
        },
    }

    @classmethod
    def create(
        cls,
        provider: str = None,
        model: str = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ):
        """
        创建 LLM 实例

        Args:
            provider: 'dashscope' | 'deepseek'（默认从 LLM_PROVIDER 环境变量读取）
            model: 模型名（默认从 LLM_MODEL 环境变量读取）
            temperature: 温度参数 (0.0 ~ 1.0)
            max_tokens: 最大输出 token 数
        """
        if provider is None:
            provider = os.getenv("LLM_PROVIDER", "deepseek")
        if model is None:
            model = os.getenv("LLM_MODEL", "deepseek-v4-pro")

        cache_key = f"{provider}:{model}:{temperature}" # 缓存 key，三个变量拼接成一个字符串，生成唯一的缓存键 cache_key
        if cache_key in cls._instances:
            return cls._instances[cache_key]

        cfg = cls._PROVIDERS[provider]
        llm = ChatOpenAI(
            api_key=cfg["api_key"],
            base_url=cfg["base_url"],
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            **(cfg.get("extra", {})),
        )

        cls._instances[cache_key] = llm
        return llm

    @classmethod
    def create_for_agent(cls, agent_type: str, **kwargs):
        """
        按 Agent 类型创建 LLM 实例
        Args:
            agent_type: Agent 类型
            kwargs: 创建 LLM 参数
                provider: 'dashscope' | 'deepseek'（默认从 LLM_PROVIDER 环境变量读取）
                model: 模型名（默认从 LLM_MODEL 环境变量读取）
                temperature: 温度参数 (0.0 ~ 1.0)
                max_tokens: 模型最大输出 token 数
        """

        agents_path = _CONFIG_DIR / "agents.json"
        with open(agents_path, "r", encoding="utf-8") as f:
            all_configs = json.load(f)

        agent_cfg = all_configs.get(agent_type, {})

        # agent_cfg 作为默认值，kwargs 可覆盖
        params = {
            "provider": agent_cfg.get("provider"),
            "model": agent_cfg.get("model"),
            "temperature": agent_cfg.get("temperature", 0.7),
            "max_tokens": agent_cfg.get("max_tokens", 2048),
        }
        params.update(kwargs)
        return cls.create(**params)
