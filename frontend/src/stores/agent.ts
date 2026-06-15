/**
 * Agent 状态管理 (Pinia Store)
 *
 * 集中管理：
 * - 消息流（user, agent, tool_call, answer, citation, ...）
 * - 当前 Agent 状态
 * - 权限请求（Map 授权弹窗）
 * - 侧边栏（会话列表 / 仪表盘）
 * - 用户档案
 *
 * ## 核心方法
 *
 * - sendMessage(text)   — 发送消息，发起 SSE 流
 * - handleSSEEvent(e)   — 处理 SSE 事件，更新 messages
 * - approveMap(yes/no)  — Map 授权确认
 * - toggleMessageExpand(id) — 折叠/展开工具调用
 */

import { defineStore } from 'pinia'
import type { Message, PermissionEvent, UserProfile, ConversationSummary } from '@/types/agent'

let _msgId = 0
function nextId(): string{
  return 'msg_' + (++_msgId)
}
function loadOrCreateUserId(): string {
  /** 生成用户 ID */
  const key = 'geo_agent_user_id'
  const stored = localStorage.getItem(key)
  if (stored) 
    return stored
  const newId = 'u_' + crypto.randomUUID().slice(0, 8) // 生成 UUID
  localStorage.setItem(key, newId)
  return newId
}

export const useAgentStore = defineStore('agent', {
  state: () => ({
    sessionId: null as string | null, // 当前会话 ID
    userId: loadOrCreateUserId(), // 用户 ID  
    messages: [] as Message[], // 消息列表
    isStreaming: false, // 是否正在流式处理
    currentAgent: null as string | null, // 当前 Agent
    currentMode: 'chat' as 'chat' | 'quiz', // 当前模式 
    pendingPermission: null as PermissionEvent | null, // 等待授权
    sidebarTab: 'conversations' as 'conversations' | 'dashboard', // 侧边栏
    conversations: [] as ConversationSummary[], // 会话列表
    userProfile: null as UserProfile | null, // 用户档案 
    lastError: null as string | null, // 最后一个错误 
  }),

  actions: {
    handleSSEEvent(event: { type: string; data: any }) {
      // TODO: 实现 SSE 事件 → messages 状态转换
      // 根据 event.type 处理：
      // - session_start → 保存 sessionId
      // - agent_start/agent_thought → 追加消息（默认折叠）
      // - tool_call → 追加 tool_call 消息（默认折叠）
      // - tool_result → 找到对应 tool_call 消息，附加结果
      // - permission_required → 设置 pendingPermission
      // - chunk → 追加/更新 answer 消息
      // - citation → 追加引用消息
      // - done → isStreaming = false, 保存会话
      // - error → 设置 lastError
      const { type, data } = event
      switch (type) {
        case 'session_start':
          this.sessionId = data.session_id
          break

        case 'agent_start':

        case 'agent_thought':
          this.currentAgent = data.agent || null
          break
        
        case 'tool_call':
          this.messages.push({
            id: nextId(),
            type: 'tool_call',
            data: {tool: data.tool, label: data.label, args: data.args},
            timestamp: Date.now(),
            expanded: false
          })
          break
        
        case 'tool_result':
          const callMsg = this.messages.findLast(
            m => m.type === 'tool_call' && m.data.tool === data.tool
          )
          if (callMsg){
            callMsg.data.result = data
            callMsg.data.resultCount = data.result_count
          }
          break

        case 'chunk':
          const last = this.messages[this.messages.length - 1]
          if (last?.type === 'answer') {
            last.data.text += data.text
          } else {
            this.messages.push({
              id: nextId(),
              type: 'answer',
              data: {text: data.text},
              timestamp: Date.now(),
            })
          }
          break
          
        case 'done':
          this.isStreaming = false
          this.saveSession()
          break

        case 'error':
          this.lastError = data.message || 'Unknown error'
          this.isStreaming = false
          break
      }
    },

    async sendMessage(text: string) {

      if (!text.trim() || this.isStreaming)
        return
      this.isStreaming = true
      this.lastError = null

      this.messages.push({
        id: nextId(),
        type: 'user',
        data: {text},
        timestamp: Date.now(),
      })

      const { startSSEStream } = await import('@/services/sse')

      try{
        await startSSEStream(
          '/api/v2/chat', 
          { 
            message: text, 
            user_id: this.userId,
            session_id: this.sessionId, 
          }, 
          (event) => this.handleSSEEvent(event)
        )
      }catch(e : any){
        this.lastError = e.message || 'Unknown error'
        this.isStreaming = false
      }
    },

    async approveMapPermission(approved: boolean) {
      // TODO: 实现
      // 1. POST /api/v2/agent/approve { call_id, approved }
      // 2. 清除 pendingPermission
    },

    toggleMessageExpand(messageId: string) {
      // TODO: 实现
      // 找到 messages 中对应 id 的消息，切换 expanded 字段
      const msg = this.messages.find(m => m.id === messageId)
      if (msg)
        msg.expanded = !msg.expanded
    },

    switchSidebarTab(tab: 'conversations' | 'dashboard') {
      this.sidebarTab = tab
    },

    setMode(mode: 'chat' | 'quiz') {
      this.currentMode = mode
    },

    async saveSession() {
      if (!this.sessionId) return

      // 用第一条用户消息作为标题
      const firstUserMsg = this.messages.find(m => m.type === 'user')
      const title = (firstUserMsg?.data?.text || '').slice(0, 30)

      // 从工具调用中提取话题
      const topics = this.messages
        .filter(m => m.type === 'tool_call' && m.data.tool === 'search_textbook')
        .map(m => m.data.args?.query || '')
        .filter((v, i, a) => a.indexOf(v) === i)  // 去重

      try {
        const { apiClient } = await import('@/services/api')
        await apiClient.post('/api/v2/user/session', {
          user_id: this.userId,
          session_id: this.sessionId,
          title,
          topics: topics.slice(0, 8),
          message_count: this.messages.length,
          summary: '',
        })
      } catch {
        /* ignore */
      }
      // 刷新侧边栏会话列表和用户档案
      await this.loadConversations()
      await this.loadUserProfile()
    },

    async loadUserProfile() {
      /**
       * 加载用户档案
       */
      const { apiClient} = await import('@/services/api')
      const res = await apiClient.get('/api/v2/user/profile', {user_id: this.userId})
      if (res.code === 0) 
        this.userProfile = res.data
    },

    async loadConversations() {
      /**
       * 加载会话列表
       */
      const { apiClient} = await import('@/services/api')
      const res = await apiClient.get('/api/v2/user/sessions', {user_id: this.userId})
      if (res.code === 0)
        this.conversations = res.data
    },

    async loadSessionMessages(sessionId: string) {
      this.sessionId = sessionId
      this.messages = []
      try {
        const { apiClient } = await import('@/services/api')
        const res = await apiClient.get(`/api/v2/user/sessions/${sessionId}/messages`)
        if (res.code === 0 && res.data?.messages) {
          this.messages = res.data.messages.map((m: any, i: number) => ({
            ...m,
            id: 'hist_' + i,
            timestamp: Date.now() - (res.data.messages.length - i) * 1000,
          }))
        }
      } catch { /* ignore */ }
    },

    async deleteSession(sessionId: string) {
      try {
        const { apiClient } = await import('@/services/api')
        await apiClient.delete(`/api/v2/user/sessions/${sessionId}`)
        // 如果删的是当前会话，清空
        if (this.sessionId === sessionId) {
          this.sessionId = null
          this.messages = []
        }
        await this.loadConversations()
      } catch { /* ignore */ }
    },
  },
})
