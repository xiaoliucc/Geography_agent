# RAG_Geography → Agent 系统升级方案（最终版 v3）

## Context

将基于 RAG 的高中地理智能问答系统升级为具备 Tool-Use + 长期记忆的 Agent 系统。
技术栈：**FastAPI + Vue 3 + TypeScript + Vite + ChromaDB + LangGraph**。

---

## 一、架构：单 Agent + 多工具

经过实践验证，简化为 **1 个全能 Teacher Agent + 5 个工具**，砍掉 Supervisor 和多 Agent 路由。

```
用户问题
  → Teacher Agent (qwen-plus)
     ├── search_textbook  ← ChromaDB 教材检索
     ├── web_search       ← Tavily 网络搜索
     ├── calculate        ← Python math 地理计算
     ├── generate_quiz    ← LLM 生成测试题
     └── evaluate_answer  ← LLM 批改答案
  → SSE 流式回答
```

**简化理由**：
- 高中地理 80%+ 的提问只需要 Teacher 处理
- Supervisor 路由增加 1 次额外 LLM 调用（延迟 + 成本）
- 多 Agent 带来路由错误和循环风险
- 单 Agent 更稳定、更快、更易调试

---

## 二、记忆系统

| 层级 | 状态 | 说明 |
|------|------|------|
| L1 会话记忆 | ✅ AsyncSqliteSaver | 自动管理，按 session 隔离 |
| L2 用户档案 | ✅ SQLite | 年级/教材/最近话题 |
| L3 学习进度 | ❌ 预留 | 表已建，后期做知识点级追踪 |

---

## 三、LLM 提供商

| 提供商 | 默认模型 | 用途 |
|--------|---------|------|
| 阿里云百炼 (DashScope) | qwen-plus | 主力 |
| DeepSeek | deepseek-chat | 备选 |

---

## 四、技术栈

后端：FastAPI + LangGraph + LangChain + ChromaDB + aiosqlite + Tavily
前端：Vue 3.5 + TypeScript + Vite 7 + Pinia + Vue Router 4.5 + marked

---

## 五、项目结构

```
Geography-1.0/
├── backend/
│   ├── main.py              ← FastAPI 入口
│   ├── config/
│   │   ├── settings.py      ← LLMFactory
│   │   ├── agents.json      ← Agent 模型配置
│   │   └── prompts/         ← 中文提示词
│   ├── db/__init__.py       ← ChromaDB + 嵌入
│   ├── agent/
│   │   ├── __init__.py      ← L1 记忆
│   │   ├── agents/          ← 单 Teacher Agent
│   │   ├── tools/           ← 5 个工具
│   │   └── memory/          ← L2 用户档案
│   └── api_v2/              ← API 端点
├── frontend/src/
│   ├── stores/agent.ts      ← Pinia Store
│   ├── services/            ← SSE + API 客户端
│   ├── components/          ← Chat, Quiz, Dashboard, Sidebar
│   └── types/agent.ts       ← TS 类型
├── memory/                  ← SQLite 运行时
└── materials/               ← ChromaDB + 教材图片
```

---

## 六、API 端点

| 端点 | 状态 |
|------|------|
| `POST /api/v2/chat` | ✅ SSE 流式对话 |
| `POST /api/v2/quiz/generate` | ✅ 生成试题 |
| `POST /api/v2/quiz/evaluate` | ✅ 批改答案 |
| `GET/PUT /api/v2/user/profile` | ✅ 用户档案 |
| `GET/POST /api/v2/user/sessions` | ✅ 会话历史 |
| `GET /api/v2/health` | ✅ 健康检查 |
| `GET /api/v2/textbooks` | ✅ 教材列表 |
| `GET /materials/*` | ✅ 静态文件 |

---

## 七、验证结果

- 对话：单问题不循环，SSE 流式正常
- 计算："东八区14点西五区几点" → calculate 工具正确调用
- 出题：Quiz 页面生成题目 + 批改正常
- 会话历史：保存消息数 + 标题，侧边栏可查看

---

## 八、待做事项

- [ ] Map 工具（高德 API → 静态图片检索 降级）
- [ ] L3 知识点级学习进度
- [ ] DeepSeek thinking 模式兼容
- [ ] 登录 + 数据加密
- [ ] PDF 分类处理管道
- [ ] Token 优化（对话压缩）
