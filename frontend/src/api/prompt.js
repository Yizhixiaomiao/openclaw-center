import request from '../utils/request'
import { getToken } from '../utils/auth'

export function getTemplates(params) {
  return request.get('/prompts/templates', { params })
}

export function createTemplate(data) {
  return request.post('/prompts/templates', data)
}

export function getTemplate(id) {
  return request.get(`/prompts/templates/${id}`)
}

export function updateTemplate(id, data) {
  return request.put(`/prompts/templates/${id}`, data)
}

export function publishTemplate(id) {
  return request.post(`/prompts/templates/${id}/publish`)
}

export function rollbackTemplate(id, version) {
  return request.post(`/prompts/templates/${id}/rollback`, null, { params: { version } })
}

export function copyTemplate(id) {
  return request.post(`/prompts/templates/${id}/copy`)
}

export function deleteTemplate(id) {
  return request.delete(`/prompts/templates/${id}`)
}

export function getUserPrompts(params) {
  return request.get('/prompts/user-prompts', { params })
}

export function createUserPrompt(data) {
  return request.post('/prompts/user-prompts', data)
}

export function updateUserPrompt(id, data) {
  return request.put(`/prompts/user-prompts/${id}`, data)
}

export function aiGeneratePrompt(data, onChunk, onDone, onError) {
  const token = getToken()
  fetch('/api/prompts/ai-generate', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`,
    },
    body: JSON.stringify(data),
  })
    .then(async (resp) => {
      if (!resp.ok) {
        const err = await resp.json().catch(() => ({ detail: `请求失败 (HTTP ${resp.status})` }))
        onError(err.detail || '请求失败')
        return
      }
      const reader = resp.body.getReader()
      const decoder = new TextDecoder()
      let buffer = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop() || ''

        for (const line of lines) {
          if (!line.startsWith('data: ')) continue
          const payload = line.slice(6).trim()
          if (payload === '[DONE]') {
            onDone()
            return
          }
          try {
            const parsed = JSON.parse(payload)
            if (parsed.error) {
              onError(parsed.error)
              return
            }
            if (parsed.content) {
              onChunk(parsed.content)
            }
          } catch {}
        }
      }
      onDone()
    })
    .catch((e) => {
      onError(e.message || '网络错误')
    })
}
