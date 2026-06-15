/**
 * REST API 客户端
 *
 * 封装非流式 API 调用（quiz, user, health 等）
 *
 * ## 使用方式
 *
 * ```typescript
 * import { apiClient } from '@/services/api'
 *
 * const profile = await apiClient.get('/api/v2/user/profile', { user_id: 'u_abc' })
 * ```
 */

import axios from 'axios'

const http = axios.create({
  baseURL: '/',
  timeout: 120000,
  headers: { 'Content-Type': 'application/json' },
})

export const apiClient = {
  async get(url: string, params?: Record<string, any>) {
    const { data } = await http.get(url, { params })
    return data
  },
  async post(url: string, body?: Record<string, any>) {
    const { data } = await http.post(url, body)
    return data
  },
  async put(url: string, body?: Record<string, any>) {
    const { data } = await http.put(url, body)
    return data
  },
  async delete(url: string) {
    const { data } = await http.delete(url)
    return data
  },
}
