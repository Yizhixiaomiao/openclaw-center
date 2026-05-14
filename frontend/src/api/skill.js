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

export function getSkillDetail(id) {
  return request.get(`/skills/detail/${id}`)
}

export function updateSkill(id, data) {
  return request.put(`/skills/${id}`, data)
}

export function auditSkill(id, auditStatus) {
  return request.post(`/skills/${id}/audit`, null, { params: { audit_status: auditStatus } })
}

export function deleteSkill(id) {
  return request.delete(`/skills/${id}`)
}

export function removeSkillFromMachine(skillId, machineId) {
  return request.delete(`/skills/${skillId}/machine/${machineId}`)
}

export function getSkillFiles(id) {
  return request.get(`/skills/${id}/files`)
}

export function getSkillFileContent(id, path) {
  return request.get(`/skills/${id}/files/content`, { params: { path } })
}

export function searchClawHubSkills(params) {
  return request.get('/skills/clawhub/search', { params })
}

export function listClawHubSkills(params) {
  return request.get('/skills/clawhub/list', { params })
}

export function getClawHubSkillDetail(slug) {
  return request.get(`/skills/clawhub/${slug}`)
}

export function installFromClawHub(data) {
  return request.post('/skills/clawhub/install', data)
}
