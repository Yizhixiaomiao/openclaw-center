import request from '../utils/request'

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

export function getUserPrompts(params) {
  return request.get('/prompts/user-prompts', { params })
}

export function createUserPrompt(data) {
  return request.post('/prompts/user-prompts', data)
}

export function updateUserPrompt(id, data) {
  return request.put(`/prompts/user-prompts/${id}`, data)
}
