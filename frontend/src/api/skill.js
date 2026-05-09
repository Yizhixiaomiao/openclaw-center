import request from '../utils/request'

export function getSkills(params) {
  return request.get('/skills', { params })
}

export function createSkill(data) {
  return request.post('/skills', data)
}

export function getSkill(id) {
  return request.get(`/skills/${id}`)
}

export function updateSkill(id, data) {
  return request.put(`/skills/${id}`, data)
}

export function auditSkill(id, auditStatus) {
  return request.post(`/skills/${id}/audit`, null, { params: { audit_status: auditStatus } })
}
