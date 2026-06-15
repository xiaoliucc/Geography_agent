<template>
  <div class="quiz-page">
    <header class="quiz-header">
      <button class="back-btn" @click="$router.push('/chat')">← 返回对话</button>
      <h2>📝 地理练习题</h2>
    </header>

    <!-- 出题表单 -->
    <div v-if="!quizData && !loading" class="quiz-form">
      <div class="form-group">
        <label>测试主题</label>
        <input v-model="topic" class="form-input" placeholder="如：大气环流、季风、板块构造" />
      </div>
      <div class="form-row">
        <div class="form-group">
          <label>题目数量</label>
          <select v-model="questionCount" class="form-select">
            <option :value="3">3 题</option>
            <option :value="5">5 题</option>
            <option :value="10">10 题</option>
          </select>
        </div>
        <div class="form-group">
          <label>难度</label>
          <select v-model="difficulty" class="form-select">
            <option value="easy">简单</option>
            <option value="medium">中等</option>
            <option value="hard">困难</option>
          </select>
        </div>
      </div>
      <div class="form-group">
        <label>题型</label>
        <div class="type-checkboxes">
          <label class="checkbox-label">
            <input type="checkbox" value="multiple_choice" v-model="questionTypes" /> 选择题
          </label>
          <label class="checkbox-label">
            <input type="checkbox" value="short_answer" v-model="questionTypes" /> 简答题
          </label>
        </div>
      </div>
      <button class="generate-btn" :disabled="!topic.trim()" @click="generate">生成题目</button>
    </div>

    <!-- 加载中 -->
    <div v-if="loading" class="loading-state">
      <div class="spinner" />
      <p>正在生成题目...</p>
    </div>

    <!-- 答题区 -->
    <div v-if="quizData && !submitted" class="quiz-area">
      <h3>{{ quizData.title }}</h3>
      <div v-for="(q, i) in quizData.questions" :key="i" class="question-card">
        <div class="q-header">
          <span class="q-number">第 {{ Number(i) + 1 }} 题</span>
          <span class="q-type">{{ typeLabel(q.type) }}</span>
          <span class="q-difficulty">{{ diffLabel(q.difficulty) }}</span>
        </div>
        <div class="q-body" v-html="renderMarkdown(q.question)" />

        <!-- 选择题 -->
        <div v-if="q.type === 'multiple_choice'" class="options">
          <label v-for="(opt, j) in q.options" :key="j" class="option" :class="{ selected: answers[Number(i)] === opt[0] }">
            <input type="radio" :name="'q' + i" :value="opt[0]" v-model="answers[Number(i)]" />
            {{ opt }}
          </label>
        </div>

        <!-- 简答题 -->
        <textarea
          v-else
          v-model="answers[Number(i)]"
          class="answer-input"
          rows="3"
          placeholder="输入你的答案..."
        />
      </div>
      <button class="submit-btn" @click="submit">提交答案</button>
    </div>

    <!-- 结果 -->
    <div v-if="submitted && evalResult" class="result-area">
      <h3>📊 答题结果</h3>
      <div class="score-card">
        <div class="score-number">{{ evalResult.score }}</div>
        <div class="score-label">/ 10 分</div>
      </div>
      <p class="feedback">{{ evalResult.feedback }}</p>
      <div v-for="(p, i) in evalResult.point_by_point" :key="i" class="point-item" :class="p.status">
        <span class="point-status">{{ statusIcon(p.status) }}</span>
        <span>{{ p.point }}: {{ p.comment }}</span>
      </div>
      <button class="back-btn" @click="reset">重新出题</button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { marked } from 'marked'
import { apiClient } from '@/services/api'
import { useAgentStore } from '@/stores/agent'

const store = useAgentStore()

const topic = ref('')
const questionCount = ref(5)
const difficulty = ref('medium')
const questionTypes = ref(['multiple_choice', 'short_answer'])
const loading = ref(false)

const quizData = ref<any>(null)
const answers = ref<string[]>([])
const submitted = ref(false)
const evalResult = ref<any>(null)

function typeLabel(t: string) {
  const map: Record<string, string> = { multiple_choice: '选择题', short_answer: '简答题' }
  return map[t] || t
}

function diffLabel(d: string) {
  const map: Record<string, string> = { easy: '⭐', medium: '⭐⭐', hard: '⭐⭐⭐' }
  return map[d] || d
}

function statusIcon(s: string) {
  const map: Record<string, string> = { correct: '✅', partial: '⚠️', missing: '❌', incorrect: '❌' }
  return map[s] || '•'
}

function renderMarkdown(text: string) {
  return marked.parse(text, { breaks: true }) as string
}

async function generate() {
  loading.value = true
  const res = await apiClient.post('/api/v2/quiz/generate', {
    topic: topic.value,
    question_count: questionCount.value,
    difficulty: difficulty.value,
    question_types: questionTypes.value.join(','),
    user_id: store.userId,
  })
  if (res.code === 0) {
    quizData.value = res.data
    answers.value = quizData.value.questions.map(() => '')
    submitted.value = false
    evalResult.value = null
  }
  loading.value = false
}

async function submit() {
  if (!quizData.value) return
  // 逐个评估简答题
  const results: any[] = []
  let totalScore = 0
  for (let i = 0; i < quizData.value.questions.length; i++) {
    const q = quizData.value.questions[i]
    if (q.type === 'multiple_choice') {
      const correct = answers.value[i] === q.answer
      results.push({
        point: q.knowledge_point || q.question.slice(0, 20),
        status: correct ? 'correct' : 'incorrect',
        comment: correct ? '正确' : `正确答案是 ${q.answer}`,
      })
      if (correct) totalScore += 1
    } else {
      // 简答题调后端评估
      try {
        const res = await apiClient.post('/api/v2/quiz/evaluate', {
          question: q.question,
          student_answer: answers.value[i],
          user_id: store.userId,
        })
        if (res.code === 0) {
          results.push(...res.data.point_by_point)
          totalScore += res.data.score
        }
      } catch {
        results.push({ point: q.question.slice(0, 20), status: 'missing', comment: '评估失败' })
      }
    }
  }
  const maxScore = quizData.value.questions.length * 2
  evalResult.value = {
    score: Math.round((totalScore / maxScore) * 10 * 10) / 10,
    feedback: totalScore > maxScore * 0.7 ? '掌握得不错！' : totalScore > maxScore * 0.4 ? '还需加强' : '建议重新学习该知识点',
    point_by_point: results,
  }
  submitted.value = true
}

function reset() {
  quizData.value = null
  evalResult.value = null
  submitted.value = false
}
</script>

<style scoped>
.quiz-page {
  height: 100vh;
  overflow-y: auto;
  padding: 24px;
  max-width: 800px;
  margin: 0 auto;
}

.quiz-header {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 24px;
}

.quiz-header h2 { font-size: 20px; }

/* 出题表单 */
.quiz-form {
  background: #fff;
  border-radius: 12px;
  padding: 24px;
  box-shadow: 0 1px 4px rgba(0,0,0,0.06);
}

.form-group { margin-bottom: 16px; }
.form-group label { display: block; font-size: 13px; color: #555; margin-bottom: 6px; }
.form-input, .form-select {
  width: 100%;
  padding: 10px 14px;
  border: 1px solid #d0d0d0;
  border-radius: 8px;
  font-size: 14px;
}
.form-row { display: flex; gap: 16px; }
.form-row .form-group { flex: 1; }
.generate-btn {
  width: 100%;
  padding: 12px;
  background: #4a90d9;
  color: #fff;
  border: none;
  border-radius: 8px;
  font-size: 15px;
  cursor: pointer;
}
.generate-btn:disabled { background: #b0c4de; cursor: not-allowed; }

/* 题目卡片 */
.quiz-area { padding: 20px 0; }
.quiz-area h3 { margin-bottom: 20px; }
.question-card {
  background: #fff;
  border-radius: 12px;
  padding: 20px;
  margin-bottom: 16px;
  box-shadow: 0 1px 4px rgba(0,0,0,0.06);
}
.q-header { display: flex; gap: 12px; margin-bottom: 12px; font-size: 13px; }
.q-number { font-weight: 600; }
.q-type, .q-difficulty { color: #888; }

.options { display: flex; flex-direction: column; gap: 8px; margin-top: 12px; }
.option {
  display: flex; align-items: center; gap: 8px;
  padding: 10px 14px; border: 1px solid #e0e0e0; border-radius: 8px; cursor: pointer;
}
.option.selected { border-color: #4a90d9; background: #f0f7ff; }
.answer-input {
  width: 100%; margin-top: 12px; padding: 10px;
  border: 1px solid #d0d0d0; border-radius: 8px;
}

.submit-btn {
  padding: 12px 32px; background: #34c759; color: #fff;
  border: none; border-radius: 8px; font-size: 15px; cursor: pointer;
}

/* 结果 */
.result-area { padding: 20px 0; }
.score-card {
  text-align: center; padding: 24px; background: #fff; border-radius: 12px;
  box-shadow: 0 1px 4px rgba(0,0,0,0.06); margin: 16px 0;
}
.score-number { font-size: 48px; font-weight: 700; color: #4a90d9; }
.feedback { text-align: center; color: #555; margin-bottom: 20px; }
.point-item { padding: 8px 0; font-size: 14px; border-bottom: 1px solid #f0f0f0; }
.point-item.correct { color: #2e7d32; }
.point-item.partial { color: #e67e22; }
.point-item.missing, .point-item.incorrect { color: #c0392b; }

.back-btn {
  background: none; border: none; color: #4a90d9; cursor: pointer; font-size: 14px;
}
.back-btn:hover { text-decoration: underline; }

.loading-state { text-align: center; padding: 60px 0; }
.spinner {
  width: 40px; height: 40px; border: 4px solid #e0e0e0;
  border-top-color: #4a90d9; border-radius: 50%;
  animation: spin 0.8s linear infinite; margin: 0 auto 16px;
}
@keyframes spin { to { transform: rotate(360deg); } }
</style>
