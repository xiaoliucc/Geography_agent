/**
 * Vue Router 路由配置
 *
 * /chat/:sessionId? → 主对话界面
 * /quiz              → 做题界面
 * /dashboard         → 学习仪表盘
 * /pdf/:textbook/:page → PDF 查看器
 */

import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      redirect: '/chat',
    },
    {
      path: '/chat/:sessionId?',
      name: 'chat',
      component: () => import('@/components/chat/ChatContainer.vue'),
    },
    {
      path: '/quiz',
      name: 'quiz',
      component: () => import('@/components/quiz/QuizGenerator.vue'),
    },
    {
      path: '/dashboard',
      name: 'dashboard',
      component: () => import('@/components/dashboard/LearningDashboard.vue'),
    },
    {
      path: '/pdf/:textbook/:page',
      name: 'pdf-viewer',
      // TODO: component: () => import('@/components/answer/PDFViewer.vue'),
      component: () => import('@/App.vue'),  // 占位
    },
  ],
})

export default router
