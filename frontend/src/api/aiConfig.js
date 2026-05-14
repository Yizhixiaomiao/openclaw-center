import request from '../utils/request'

export function getAIConfigs(params) {
  return request.get('/ai-configs', { params })
}

export function createAIConfig(data) {
  return request.post('/ai-configs', data)
}

export function getAIConfig(id) {
  return request.get(`/ai-configs/${id}`)
}

export function updateAIConfig(id, data) {
  return request.put(`/ai-configs/${id}`, data)
}

export function deleteAIConfig(id) {
  return request.delete(`/ai-configs/${id}`)
}

export function testConnection(data) {
  return request.post('/ai-configs/test-connection', data)
}

export function setActiveConfig(id) {
  return request.post(`/ai-configs/${id}/set-active`)
}

export function testConfigConnection(id) {
  return request.post(`/ai-configs/${id}/test`)
}

export function getActiveConfig() {
  return request.get('/ai-configs/active')
}
