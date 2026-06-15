<template>
  <div class="dashboard-page">
    <header class="dash-header">
      <button class="back-btn" @click="$router.push('/chat')">← 返回对话</button>
      <h2>📊 学习报告</h2>
    </header>

    <div v-if="store.userProfile" class="overview">
      <div class="stat-card">
        <div class="stat-number">{{ store.userProfile.total_sessions || 0 }}</div>
        <div class="stat-label">总对话次数</div>
      </div>
      <div class="stat-card">
        <div class="stat-number">{{ store.userProfile.grade || '未设置' }}</div>
        <div class="stat-label">年级</div>
      </div>
      <div class="stat-card">
        <div class="stat-number">{{ textbookLabel }}</div>
        <div class="stat-label">教材版本</div>
      </div>
    </div>

    <div v-if="store.userProfile?.recent_topics?.length" class="topics-section">
      <h3>最近学习话题</h3>
      <div class="topic-list">
        <div v-for="t in store.userProfile.recent_topics.slice(0, 10)" :key="t" class="topic-item">
          {{ t }}
        </div>
      </div>
    </div>

    <div v-if="progress.length" class="progress-section">
      <h3>知识点掌握度 ({{ progress.length }}/{{ totalPoints }})</h3>
      <div v-for="p in progress.slice(0, 15)" :key="p.topic" class="progress-item">
        <span class="progress-point">{{ p.topic }}</span>
        <span class="progress-count">{{ p.interactions }} 次互动</span>
      </div>
    </div>

    <div v-if="store.conversations.length" class="recent-section">
      <h3>历史会话</h3>
      <div v-for="conv in store.conversations.slice(0, 10)" :key="conv.session_id" class="conv-row"
        @click="$router.push(`/chat/${conv.session_id}`)">
        <span class="conv-title">{{ conv.title || '未命名' }}</span>
        <span class="conv-meta">{{ conv.message_count }} 条 · {{ conv.updated_at?.slice(0, 10) }}</span>
      </div>
    </div>

    <div v-if="!store.userProfile?.recent_topics?.length && !store.conversations.length" class="empty">
      <p>还没有学习记录</p>
      <p>去对话页面开始学习吧</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, computed, ref } from 'vue'
import { useAgentStore } from '@/stores/agent'
import { apiClient } from '@/services/api'

const store = useAgentStore()
const progress = ref<any[]>([])
const totalPoints = ref(0)

const textbookLabel = computed(() => {
  const map: Record<string, string> = { renjiao: '人教版', lujiao: '鲁教版' }
  return map[store.userProfile?.textbook || ''] || store.userProfile?.textbook || '未设置'
})

onMounted(async () => {
  store.loadUserProfile()
  store.loadConversations()
  try {
    const res = await apiClient.get('/api/v2/user/progress', { user_id: store.userId })
    if (res.code === 0) {
      progress.value = res.data.progress || []
      totalPoints.value = res.data.total_points || 0
    }
  } catch { /* ignore */ }
})
</script>

<style scoped>
.dashboard-page {
  height: 100vh;
  overflow-y: auto;
  padding: 24px;
  max-width: 800px;
  margin: 0 auto;
}

.dash-header {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 24px;
}

.overview {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
  margin-bottom: 28px;
}

.stat-card {
  background: #fff;
  border-radius: 12px;
  padding: 20px;
  text-align: center;
  box-shadow: 0 1px 4px rgba(0,0,0,0.06);
}

.stat-number {
  font-size: 28px;
  font-weight: 700;
  color: #4a90d9;
}

.stat-label {
  font-size: 12px;
  color: #888;
  margin-top: 4px;
}

.topics-section, .recent-section {
  background: #fff;
  border-radius: 12px;
  padding: 20px;
  margin-bottom: 16px;
  box-shadow: 0 1px 4px rgba(0,0,0,0.06);
}

.topics-section h3, .recent-section h3 {
  font-size: 15px;
  margin-bottom: 12px;
}

.topic-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.topic-item {
  padding: 6px 14px;
  background: #f0f7ff;
  color: #4a90d9;
  border-radius: 16px;
  font-size: 13px;
}

.conv-row {
  display: flex;
  justify-content: space-between;
  padding: 10px 0;
  border-bottom: 1px solid #f0f0f0;
  cursor: pointer;
}
.conv-row:hover { background: #fafafa; }

.conv-title { font-size: 14px; }
.conv-meta { font-size: 12px; color: #888; }

.empty { text-align: center; color: #999; padding: 60px 0; }

.progress-section {
  background: #fff;
  border-radius: 12px;
  padding: 20px;
  margin-bottom: 16px;
  box-shadow: 0 1px 4px rgba(0,0,0,0.06);
}

.progress-section h3 {
  font-size: 15px;
  margin-bottom: 12px;
}

.progress-item {
  display: flex;
  justify-content: space-between;
  padding: 8px 0;
  border-bottom: 1px solid #f0f0f0;
  font-size: 13px;
}

.progress-point { color: #333; }
.progress-count { color: #4a90d9; font-weight: 600; }

.back-btn {
  background: none; border: none; color: #4a90d9; cursor: pointer; font-size: 14px;
}
</style>
