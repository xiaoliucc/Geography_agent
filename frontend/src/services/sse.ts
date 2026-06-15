/**
 * SSE 流式客户端
 *
 * 将 fetch + ReadableStream 封装为事件驱动接口。
 * 支持多事件类型解析（agent_start, tool_call, chunk, done, error 等）。
 */

export async function startSSEStream(
  url: string,
  body: Record<string, any>,
  onEvent: (event: { type: string; data: any }) => void,
): Promise<void> {
  const response = await fetch(url, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Accept': 'text/event-stream',
    },
    body: JSON.stringify({ ...body, stream: true }),
  })

  if (!response.ok) {
    let message = `HTTP ${response.status}`
    try {
      const err = await response.json()
      message = err.message || err.detail || message
    } catch { /* body is not JSON */ }
    throw new Error(message)
  }

  const reader = response.body!.getReader()
  const decoder = new TextDecoder()
  let buffer = ''
  let currentEventType = ''

  try {
    while (true) {
      const { done, value } = await reader.read()
      if (done) break

      buffer += decoder.decode(value, { stream: true })
      const lines = buffer.split('\n')
      buffer = lines.pop() || ''

      for (const line of lines) {
        if (line.startsWith('event: ')) {
          currentEventType = line.slice(7).trim()
        } else if (line.startsWith('data: ')) {
          try {
            const data = JSON.parse(line.slice(6))
            onEvent({ type: currentEventType || 'message', data })
          } catch {
            // 非 JSON 行，静默跳过
          }
        }
      }
    }
  } finally {
    reader.releaseLock()
  }
}
