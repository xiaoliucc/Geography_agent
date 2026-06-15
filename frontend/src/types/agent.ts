/**
 * Agent 系统 TypeScript 类型定义
 *
 * 覆盖 SSE 事件、消息、用户档案、试题等全部数据结构
 */

// ── SSE 事件类型 ──

export type SSEEventType =
  | 'session_start'
  | 'agent_start'
  | 'agent_thought'
  | 'tool_call'
  | 'tool_result'
  | 'permission_required'
  | 'chunk'
  | 'citation'
  | 'done'
  | 'error'

export interface AgentEvent {
  type: SSEEventType
  data: Record<string, any>
}

// ── 消息类型 ──

export type MessageType =
  | 'user'
  | 'agent_start'
  | 'agent_thought'
  | 'tool_call'
  | 'tool_result'
  | 'answer'
  | 'citation'
  | 'done'
  | 'error'

export interface Message {
  id: string
  type: MessageType
  data: Record<string, any>
  timestamp: number
  expanded?: boolean  // tool_call 是否展开
}

// ── 权限请求 ──

export interface PermissionEvent {
  call_id: string
  tool: string
  label: string
  args: Record<string, any>
  reason: string
}

// ── 引用 ──

export interface Citation {
  textbook: string
  page: number
  chapter: string
  snippet: string
}

// ── 用户档案 ──

export interface UserProfile {
  user_id: string
  grade: string
  textbook: string
  recent_topics: string[]
  total_sessions: number
  is_new?: boolean
}

// ── 会话摘要 ──

export interface ConversationSummary {
  session_id: string
  title: string
  topics: string[]
  message_count: number
  created_at: string
  updated_at: string
}

// ── 试题 ──

export interface QuizQuestion {
  id: number
  type: 'multiple_choice' | 'fill_blank' | 'short_answer'
  question: string
  options?: string[]
  answer: string
  explanation: string
  difficulty: 'easy' | 'medium' | 'hard'
  knowledge_point: string
  chapter_ref: string
}

export interface QuizOutput {
  title: string
  questions: QuizQuestion[]
  total_time: string
  scoring: Record<string, number>
}

export interface EvaluationResult {
  score: number
  is_correct: boolean
  feedback: string
  point_by_point: Array<{
    point: string
    status: 'correct' | 'partial' | 'missing' | 'incorrect'
    comment: string
  }>
  reference_answer: string
  improvement: string
}
