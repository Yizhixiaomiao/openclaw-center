import request from '../utils/request'

export function getMachines(params) {
  return request.get('/machines', { params })
}

export function createMachine(data) {
  return request.post('/machines', data)
}

export function getMachine(id) {
  return request.get(`/machines/${id}`)
}

export function updateMachine(id, data) {
  return request.put(`/machines/${id}`, data)
}

export function updateMachineConfig(id, data) {
  return request.put(`/machines/${id}/config`, data)
}

export function updateAgentConfig(id, data) {
  return request.put(`/machines/${id}/agent-config`, data)
}

export function getMachineIps() {
  return request.get('/machines/ips')
}

export function syncMachine(id) {
  return request.post(`/machines/${id}/sync`)
}

export function uploadAgent(formData) {
  return request.post('/agent/upload', formData)
}

export function getAgentVersion() {
  return request.get('/agent/version')
}
