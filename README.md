# 🌍 地理AI助教 (Geography AI Tutor)

> 基于 RAG + Agent 的高中地理智能问答系统，支持教材检索、网络搜索、地理计算、智能出题与批改。

[![Tech Stack](https://img.shields.io/badge/stack-FastAPI%20+%20Vue%203%20+%20LangGraph-blue)](#)
[![LLM](https://img.shields.io/badge/LLM-Qwen--Plus%20%7C%20DeepSeek-green)](#)
[![License](https://img.shields.io/badge/license-MIT-orange)](#)

---

## ✨ 功能特性

- **💬 智能对话** — 高中地理知识问答，支持教材检索 + 联网搜索
- **📝 出题练习** — 按知识点自动生成选择题/简答题，AI 批改反馈
- **🧮 地理计算** — 时区换算、太阳高度角、人口增长等计算
- **📊 学习仪表盘** — 统计对话次数、学习话题、知识点掌握度
- **📚 多教材支持** — 人教版必修一 + OCR 扫描件识别
- **🧠 长期记忆** — 三层记忆系统：对话上下文 + 用户档案 + 学习进度

---

## 🏗️ 架构

```
用户 → Vue 3 前端 (SSE) → FastAPI 后端
                              └── Teacher Agent (qwen-plus)
                                   ├── search_textbook   → ChromaDB 教材检索
                                   ├── web_search        → Tavily 网络搜索
                                   ├── calculate         → Python 地理计算
                                   ├── generate_quiz     → LLM 出题
                                   └── evaluate_answer   → LLM 批改
```

**单 Agent 架构**：一个全能 "地老师" 持有 5 个工具，砍掉 Supervisor 路由，更稳定更快。

---

## 🛠️ 技术栈

| 层 | 技术 |
|---|------|
| **后端** | FastAPI · LangGraph · LangChain · ChromaDB · SQLite |
| **前端** | Vue 3.5 · TypeScript · Vite 7 · Pinia · Vue Router |
| **LLM** | 阿里云百炼 Qwen-Plus (主力) · DeepSeek (备选) |
| **嵌入** | DashScope text-embedding-v4 |
| **搜索** | Tavily Search API |
| **OCR** | Qwen-VL (扫描件教材识别) |

---

## 🚀 快速开始

### 前置条件

- Python 3.11+
- Node.js 18+
- 阿里云百炼 API Key ([免费申请](https://dashscope.aliyun.com/))
- Tavily API Key ([免费额度](https://tavily.com/))

### 1. 克隆仓库

```bash
git clone https://github.com/YOUR_USERNAME/Geography-1.0.git
cd Geography-1.0
```

### 2. 配置 API Key

```bash
set DASHSCOPE_API_KEY=your_dashscope_api_key
set TAVILY_API_KEY=your_tavily_api_key
```

### 3. 安装后端

```bash
cd backend
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS / Linux
pip install -r requirements.txt
```

### 4. 安装前端

```bash
cd frontend
npm install
```

### 5. 启动服务

**方式一：一键启动（Windows）**

双击项目根目录的 `start.bat`

**方式二：手动启动**

```bash
# 终端 1 — 后端 (端口 8000)
cd backend
venv\Scripts\activate
python main.py

# 终端 2 — 前端 (端口 5173)
cd frontend
npm run dev
```

浏览器访问 **http://localhost:5173**，开始使用！

---

## 📁 项目结构

```
Geography-1.0/
├── backend/                          # FastAPI 后端
│   ├── main.py                       # 入口 (uvicorn)
│   ├── config/                       # LLM工厂 + Agent配置 + 提示词
│   │   ├── settings.py               # LLMFactory (DashScope/DeepSeek)
│   │   ├── agents.json               # 模型配置
│   │   └── prompts/                  # 中文提示词
│   ├── db/                           # ChromaDB 向量数据库封装
│   ├── agent/
│   │   ├── agents/                   # 单 Teacher Agent 定义
│   │   ├── tools/                    # 5 个工具函数
│   │   │   ├── textbook_search.py    # ChromaDB 教材检索
│   │   │   ├── web_search.py         # Tavily 网络搜索
│   │   │   ├── calculator.py         # 安全沙箱地理计算
│   │   │   ├── quiz_tools.py         # 出题 + 批改
│   │   │   └── system_tools.py       # 系统信息工具
│   │   └── memory/                   # 三层记忆系统
│   │       ├── user_profile.py       # L2 用户档案 CRUD
│   │       └── knowledge_points.py   # 课标知识点匹配
│   ├── api_v2/                       # REST API (12 个端点)
│   ├── pipeline/                     # PDF 处理管道
│   │   ├── digital.py                # 电子版 PDF 提取
│   │   ├── ocr.py                    # Qwen-VL OCR 识别
│   │   ├── classifier.py             # PDF 类型检测
│   │   └── gui.py                    # tkinter 导入工具
│   └── test_e2e.py                   # 端到端测试
│
├── frontend/src/                     # Vue 3 前端
│   ├── stores/agent.ts               # Pinia 状态管理
│   ├── services/                     # SSE + REST 客户端
│   ├── components/
│   │   ├── chat/                     # 聊天界面 + 工具调用卡片
│   │   ├── sidebar/                  # 侧边栏 (会话/学习)
│   │   ├── quiz/                     # 出题页面
│   │   └── dashboard/                # 学习报告仪表盘
│   ├── types/agent.ts                # TypeScript 类型
│   └── router/                       # Vue Router 配置
│
├── memory/                           # SQLite 运行时数据
├── materials/                        # 教材 PDF + ChromaDB
├── start.bat                         # 一键启动脚本
└── .gitignore
```

---

## 🔌 API 端点

| 方法 | 端点 | 说明 |
|------|------|------|
| `POST` | `/api/v2/chat` | SSE 流式对话 |
| `POST` | `/api/v2/quiz/generate` | 生成试题 |
| `POST` | `/api/v2/quiz/evaluate` | 批改答案 |
| `GET` | `/api/v2/user/profile` | 用户档案 |
| `PUT` | `/api/v2/user/profile` | 更新档案 |
| `GET` | `/api/v2/user/sessions` | 会话历史 |
| `POST` | `/api/v2/user/session` | 保存会话 |
| `DELETE` | `/api/v2/user/sessions/{id}` | 删除会话 |
| `GET` | `/api/v2/user/progress` | 学习进度 |
| `GET` | `/api/v2/health` | 健康检查 |
| `GET` | `/api/v2/textbooks` | 已索引教材 |

---

## 🙏 致谢

- [LangGraph](https://github.com/langchain-ai/langgraph) — Agent 编排框架
- [ChromaDB](https://www.trychroma.com/) — 向量数据库
- [Tavily](https://tavily.com/) — AI 搜索引擎
- 教材内容版权归人民教育出版社所有，仅用于教育研究

---

## 📄 License

MIT License — 详见 [LICENSE](LICENSE) 文件
