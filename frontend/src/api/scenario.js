import request from '../utils/request'

export function getScenarios(params) {
  return request.get('/scenarios', { params })
}

export function createScenario(data) {
  return request.post('/scenarios', data)
}

export function getScenario(id) {
  return request.get(`/scenarios/${id}`)
}

export function updateScenario(id, data) {
  return request.put(`/scenarios/${id}`, data)
}

export function deleteScenario(id) {
  return request.delete(`/scenarios/${id}`)
}
