<template>
  <aside class="sidebar">
    <div class="sidebar-header">
      <span class="logo">🌍</span>
      <span class="brand">地理AI助教</span>
    </div>

    <!-- 快捷入口 -->
    <div class="nav-links">
      <router-link to="/chat" class="nav-item">💬 对话</router-link>
      <router-link to="/quiz" class="nav-item">📝 做题</router-link>
      <router-link to="/dashboard" class="nav-item">📊 报告</router-link>
    </div>

    <!-- Tab 切换 -->
    <div class="tab-bar">
      <button
        :class="['tab', { active: store.sidebarTab === 'conversations' }]"
        @click="store.switchSidebarTab('conversations')"
      >💬 会话</button>
      <button
        :class="['tab', { active: store.sidebarTab === 'dashboard' }]"
        @click="store.switchSidebarTab('dashboard')"
      >📊 学习</button>
    </div>

    <!-- 会话列表 -->
    <div v-if="store.sidebarTab === 'conversations'" class="panel">
      <button class="new-chat-btn" @click="newChat">+ 新对话</button>

      <div class="conversation-list">
        <div v-if="store.conversations.length === 0" class="empty-text">
          暂无历史会话
        </div>
        <div
          v-for="conv in store.conversations"
          :key="conv.session_id"
          class="conv-item"
          :class="{ active: conv.session_id === store.sessionId }"
          @click="$router.push(`/chat/${conv.session_id}`)"
        >
          <div class="conv-title">{{ conv.title || '未命名对话' }}</div>
          <div class="conv-meta">
            {{ conv.message_count }} 条消息
            <button class="delete-btn" @click.stop="handleDelete(conv.session_id)" title="删除">×</button>
          </div>
        </div>
      </div>
    </div>

    <!-- 学习仪表盘 -->
    <div v-if="store.sidebarTab === 'dashboard'" class="panel">
      <div v-if="store.userProfile" class="profile-card">
        <div class="profile-row">
          <span class="profile-label">年级</span>
          <span class="profile-value">{{ store.userProfile.grade || '未设置' }}</span>
        </div>
        <div class="profile-row">
          <span class="profile-label">教材</span>
          <span class="profile-value">{{ textbookLabel }}</span>
        </div>
        <div class="profile-row">
          <span class="profile-label">会话</span>
          <span class="profile-value">{{ store.userProfile.total_sessions || 0 }} 次</span>
        </div>
      </div>

      <div v-if="store.userProfile?.recent_topics?.length" class="topics-section">
        <div class="section-title">最近学习</div>
        <div v-for="t in store.userProfile.recent_topics.slice(0, 8)" :key="t" class="topic-tag">
          {{ t }}
        </div>
      </div>
    </div>
  </aside>
</template>

<script setup lang="ts">
import { computed, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useAgentStore } from '@/stores/agent'

const store = useAgentStore()
const router = useRouter()

const textbookLabel = computed(() => {
  const map: Record<string, string> = { renjiao: '人教版', lujiao: '鲁教版' }
  return map[store.userProfile?.textbook || ''] || store.userProfile?.textbook || '未设置'
})

function newChat() {
  store.sessionId = null
  store.messages = []
  store.currentAgent = null
  router.push('/chat')
}

function handleDelete(sessionId: string) {
  if (confirm('确定删除这个会话？')) {
    store.deleteSession(sessionId)
  }
}

onMounted(() => {
  store.loadUserProfile()
  store.loadConversations()
})

// 切换到仪表盘 tab 时刷新数据
watch(() => store.sidebarTab, (tab) => {
  if (tab === 'dashboard') {
    store.loadUserProfile()
  }
})
</script>

<style scoped>
.sidebar {
  width: 260px;
  height: 100vh;
  background: #1e293b;
  color: #e2e8f0;
  display: flex;
  flex-direction: column;
  flex-shrink: 0;
}

.sidebar-header {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 16px 18px 12px;
}

/* 快捷入口 */
.nav-links {
  display: flex;
  padding: 0 12px 8px;
  gap: 4px;
  border-bottom: 1px solid #334155;
}

.nav-item {
  padding: 6px 10px;
  border-radius: 6px;
  font-size: 12px;
  color: #94a3b8;
  text-decoration: none;
  transition: all 0.15s;
}

.nav-item:hover, .nav-item.router-link-active {
  background: #2d3a4f;
  color: #e2e8f0;
}

.logo { font-size: 22px; }
.brand { font-size: 15px; font-weight: 600; }

/* Tab */
.tab-bar {
  display: flex;
  border-bottom: 1px solid #334155;
}

.tab {
  flex: 1;
  padding: 10px;
  border: none;
  background: transparent;
  color: #94a3b8;
  font-size: 13px;
  cursor: pointer;
  transition: all 0.2s;
}

.tab.active {
  color: #fff;
  border-bottom: 2px solid #4a90d9;
  background: #1a2940;
}

.tab:hover:not(.active) {
  color: #cbd5e1;
}

/* Panel */
.panel {
  flex: 1;
  overflow-y: auto;
  padding: 12px;
}

.new-chat-btn {
  width: 100%;
  padding: 10px;
  border: 1px dashed #475569;
  border-radius: 8px;
  background: transparent;
  color: #94a3b8;
  font-size: 13px;
  cursor: pointer;
  margin-bottom: 12px;
  transition: all 0.2s;
}

.new-chat-btn:hover {
  border-color: #4a90d9;
  color: #4a90d9;
}

/* 会话列表 */
.conversation-list {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.conv-item {
  padding: 10px 12px;
  border-radius: 8px;
  cursor: pointer;
  transition: background 0.15s;
}

.conv-item:hover { background: #2d3a4f; }
.conv-item.active { background: #2d3a4f; border-left: 3px solid #4a90d9; }

.conv-title {
  font-size: 13px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.conv-meta {
  font-size: 11px;
  color: #64748b;
  margin-top: 4px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.delete-btn {
  background: none;
  border: none;
  color: #64748b;
  font-size: 16px;
  cursor: pointer;
  padding: 0 4px;
  line-height: 1;
  opacity: 0;
  transition: opacity 0.2s;
}

.conv-item:hover .delete-btn {
  opacity: 1;
}

.delete-btn:hover {
  color: #ef4444;
}

/* 仪表盘 */
.profile-card {
  background: #1a2940;
  border-radius: 8px;
  padding: 12px;
  margin-bottom: 16px;
}

.profile-row {
  display: flex;
  justify-content: space-between;
  padding: 6px 0;
  font-size: 13px;
}

.profile-label { color: #94a3b8; }
.profile-value { color: #e2e8f0; }

.section-title {
  font-size: 12px;
  color: #64748b;
  margin-bottom: 8px;
}

.topic-tag {
  font-size: 12px;
  padding: 6px 10px;
  background: #1a2940;
  border-radius: 6px;
  margin-bottom: 4px;
  color: #94a3b8;
}

.empty-text {
  text-align: center;
  color: #64748b;
  font-size: 13px;
  margin-top: 32px;
}
</style>
