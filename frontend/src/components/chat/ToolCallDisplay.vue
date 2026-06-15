<template>
  <div class="tool-display" :class="{ expanded: msg.expanded }">
    <div class="tool-bar" @click="$emit('toggle')">
      <span class="tool-icon">{{ icon }}</span>
      <span class="tool-label">{{ label }}</span>
      <span v-if="resultText" class="tool-result-text">{{ resultText }}</span>
      <span class="tool-chevron">{{ msg.expanded ? '▲' : '▼' }}</span>
    </div>

    <div v-if="msg.expanded" class="tool-detail">
      <div class="detail-row">
        <span class="detail-label">工具:</span>
        <code>{{ msg.data.tool }}</code>
      </div>
      <div v-if="msg.data.args" class="detail-row">
        <span class="detail-label">参数:</span>
        <code>{{ JSON.stringify(msg.data.args) }}</code>
      </div>
      <div v-if="msg.data.result" class="detail-row">
        <span class="detail-label">状态:</span>
        <span>{{ msg.data.result.status }}</span>
        <span v-if="msg.data.result.result_count !== undefined">
          · {{ msg.data.result.result_count }} 条结果
        </span>
        <span v-if="msg.data.result.source">
          · {{ sourceLabel(msg.data.result.source) }}
        </span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{
  toolCall: Record<string, any>
}>()

defineEmits<{ toggle: [] }>()

const msg = computed(() => props.toolCall as any)

const icons: Record<string, string> = {
  search_textbook: '📚',
  web_search: '🌐',
  calculate: '🔢',
  generate_quiz: '📝',
  evaluate_answer: '✅',
  transfer_to_calculator: '🧮',
  transfer_to_teacher: '👨‍🏫',
  transfer_to_quiz: '📝',
}

const icon = computed(() => icons[msg.value.data.tool] || '🔧')

const label = computed(() => msg.value.data.label || msg.value.data.tool)

const resultText = computed(() => {
  const r = msg.value.data
  if (r.resultCount !== undefined) {
    return `${r.resultCount} 条结果`
  }
  return ''
})

function sourceLabel(s: string): string {
  const map: Record<string, string> = { local: '📚教材', web: '🌐网络', computed: '💡计算' }
  return map[s] || s
}
</script>

<style scoped>
.tool-display {
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  overflow: hidden;
  background: #fafafa;
}

.tool-bar {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  cursor: pointer;
  user-select: none;
  font-size: 13px;
}

.tool-bar:hover {
  background: #f0f0f0;
}

.tool-icon {
  font-size: 16px;
}

.tool-label {
  color: #555;
}

.tool-result-text {
  color: #888;
  font-size: 12px;
}

.tool-chevron {
  margin-left: auto;
  color: #aaa;
  font-size: 10px;
}

.tool-detail {
  padding: 8px 12px 12px;
  border-top: 1px solid #e8e8e8;
  background: #fff;
}

.detail-row {
  margin-top: 6px;
  font-size: 12px;
}

.detail-label {
  color: #888;
  margin-right: 6px;
}

.detail-row code {
  font-size: 12px;
  background: #f0f0f0;
  padding: 2px 6px;
  border-radius: 4px;
  word-break: break-all;
}
</style>
