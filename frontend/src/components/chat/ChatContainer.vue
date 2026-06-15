<template>
  <div class="chat-container">
    <!-- 顶部导航 -->
    <header class="chat-header">
      <div class="header-left">
        <span class="logo">🌍</span>
        <span class="title">地理AI助教</span>
      </div>
      <div class="header-right">
        <span v-if="store.currentAgent" class="agent-badge">{{ agentLabel }}</span>
      </div>
    </header>

    <!-- 消息列表 -->
    <div class="message-list" ref="listRef">
      <div v-if="store.messages.length === 0" class="welcome">
        <div class="welcome-icon">🗺️</div>
        <h2>你好，我是地理AI助教</h2>
        <p>可以问我地理知识、出题练习、或者帮你算时区</p>
        <div class="quick-questions">
          <button v-for="q in quickQuestions" :key="q" class="quick-btn" @click="quickAsk(q)">
            {{ q }}
          </button>
        </div>
      </div>

      <template v-for="msg in store.messages" :key="msg.id">
        <!-- 用户消息 -->
        <div v-if="msg.type === 'user'" class="message-row user-row">
          <div class="avatar user-avatar">你</div>
          <div class="bubble user-bubble">{{ msg.data.text }}</div>
        </div>

        <!-- 工具调用 -->
        <div v-else-if="msg.type === 'tool_call'" class="tool-row">
          <ToolCallDisplay
            :tool-call="msg"
            @toggle="store.toggleMessageExpand(msg.id)"
          />
        </div>

        <!-- Agent 回答 -->
        <div v-else-if="msg.type === 'answer'" class="message-row agent-row">
          <div class="avatar agent-avatar">AI</div>
          <div class="bubble agent-bubble" v-html="renderMarkdown(msg.data.text)" />
        </div>
      </template>

      <!-- 加载中 -->
      <div v-if="store.isStreaming && !store.messages.find(m => m.type === 'answer')" class="message-row agent-row">
        <div class="avatar agent-avatar">AI</div>
        <div class="bubble agent-bubble thinking">
          <span class="dot-pulse" />
        </div>
      </div>
    </div>

    <!-- 输入区 -->
    <div class="input-area">
      <div class="input-wrapper">
        <textarea
          v-model="inputText"
          class="text-input"
          placeholder="输入地理问题，Enter 发送"
          rows="1"
          :disabled="store.isStreaming"
          @keydown.enter.exact.prevent="handleSend"
          @input="autoResize"
        />
        <button
          class="send-btn"
          :disabled="!inputText.trim() || store.isStreaming"
          @click="handleSend"
        >
          <span v-if="store.isStreaming">⏳</span>
          <span v-else>↑</span>
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, nextTick, watch, computed } from 'vue'
import { useRoute } from 'vue-router'
import { useAgentStore } from '@/stores/agent'
import { marked } from 'marked'
import ToolCallDisplay from './ToolCallDisplay.vue'

const route = useRoute()

const store = useAgentStore()
const inputText = ref('')
const listRef = ref<HTMLElement | null>(null)

const quickQuestions = [
  '什么是季风？',
  '冷锋和暖锋有什么区别？',
  '计算北纬40度冬至日正午太阳高度角',
  '出5道大气环流的选择题',
]

const agentLabel = computed(() => {
  const map: Record<string, string> = { teacher: '教学', quiz: '出题', calculator: '计算' }
  return map[store.currentAgent || ''] || store.currentAgent || ''
})

function renderMarkdown(text: string): string {
  return marked.parse(text, { breaks: true }) as string
}

function handleSend() {
  const text = inputText.value.trim()
  if (!text || store.isStreaming) return
  inputText.value = ''
  store.sendMessage(text)
}

function quickAsk(q: string) {
  store.sendMessage(q)
}

// 路由参数变化时加载对应会话
watch(
  () => route.params.sessionId,
  (sid) => {
    if (sid) store.loadSessionMessages(sid as string)
    else { store.sessionId = null; store.messages = [] }
  },
  { immediate: true },
)

function autoResize(e: Event) {
  const el = e.target as HTMLTextAreaElement
  el.style.height = 'auto'
  el.style.height = Math.min(el.scrollHeight, 120) + 'px'
}

watch(
  () => store.messages.length,
  () => nextTick(() => {
    listRef.value?.scrollTo({ top: listRef.value.scrollHeight, behavior: 'smooth' })
  }),
)
</script>

<style scoped>
.chat-container {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background: #f0f2f5;
}

/* 顶部 */
.chat-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 20px;
  background: #fff;
  border-bottom: 1px solid #e8e8e8;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 10px;
}

.logo { font-size: 24px; }

.title {
  font-size: 17px;
  font-weight: 600;
  color: #1a1a1a;
}

.agent-badge {
  font-size: 12px;
  background: #e8f4fd;
  color: #4a90d9;
  padding: 4px 10px;
  border-radius: 12px;
}

/* 欢迎页 */
.welcome {
  text-align: center;
  margin-top: 15vh;
}

.welcome-icon {
  font-size: 56px;
  margin-bottom: 16px;
}

.welcome h2 {
  font-size: 20px;
  color: #1a1a1a;
  margin-bottom: 8px;
}

.welcome p {
  color: #888;
  margin-bottom: 24px;
}

.quick-questions {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  justify-content: center;
}

.quick-btn {
  padding: 8px 16px;
  border: 1px solid #d0d0d0;
  border-radius: 20px;
  background: #fff;
  cursor: pointer;
  font-size: 13px;
  color: #555;
  transition: all 0.2s;
}

.quick-btn:hover {
  border-color: #4a90d9;
  color: #4a90d9;
  background: #f0f7ff;
}

/* 消息列表 */
.message-list {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
}

.message-row {
  display: flex;
  gap: 10px;
  margin-bottom: 18px;
  animation: fadeIn 0.3s ease;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(6px); }
  to { opacity: 1; transform: translateY(0); }
}

.user-row {
  flex-direction: row-reverse;
}

.avatar {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 13px;
  font-weight: 600;
  flex-shrink: 0;
}

.user-avatar {
  background: #4a90d9;
  color: #fff;
}

.agent-avatar {
  background: #34c759;
  color: #fff;
}

/* 气泡 */
.bubble {
  padding: 10px 16px;
  border-radius: 16px;
  font-size: 14px;
  line-height: 1.65;
  max-width: 70%;
  word-break: break-word;
}

.user-bubble {
  background: #4a90d9;
  color: #fff;
  border-bottom-right-radius: 4px;
}

.agent-bubble {
  background: #fff;
  color: #2c2c2c;
  border-bottom-left-radius: 4px;
  box-shadow: 0 1px 2px rgba(0,0,0,0.06);
}

.agent-bubble.thinking {
  padding: 14px 20px;
}

/* 工具行 */
.tool-row {
  margin-bottom: 8px;
  padding-left: 46px;
}

/* 思考动画 */
.dot-pulse {
  display: inline-block;
  width: 6px;
  height: 6px;
  background: #aaa;
  border-radius: 50%;
  animation: pulse 1.2s infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 0.3; transform: scale(0.8); }
  50% { opacity: 1; transform: scale(1.2); }
}

/* 输入区 */
.input-area {
  padding: 12px 20px 16px;
  background: #fff;
  border-top: 1px solid #e8e8e8;
}

.input-wrapper {
  display: flex;
  gap: 10px;
  align-items: flex-end;
  background: #f5f5f5;
  border-radius: 12px;
  padding: 8px 12px;
  border: 2px solid transparent;
  transition: border-color 0.2s;
}

.input-wrapper:focus-within {
  border-color: #4a90d9;
  background: #fff;
}

.text-input {
  flex: 1;
  border: none;
  background: transparent;
  font-size: 14px;
  outline: none;
  resize: none;
  font-family: inherit;
  max-height: 120px;
}

.send-btn {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  border: none;
  background: #4a90d9;
  color: #fff;
  cursor: pointer;
  font-size: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  transition: background 0.2s;
}

.send-btn:hover:not(:disabled) {
  background: #3a7bc8;
}

.send-btn:disabled {
  background: #c0c0c0;
  cursor: not-allowed;
}
</style>
