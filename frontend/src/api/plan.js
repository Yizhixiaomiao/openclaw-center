import request from '../utils/request'

export function getPlans(params) {
  return request.get('/coding-plans', { params })
}

export function createPlan(data) {
  return request.post('/coding-plans', data)
}

export function getPlan(id) {
  return request.get(`/coding-plans/${id}`)
}

export function updatePlan(id, data) {
  return request.put(`/coding-plans/${id}`, data)
}

export function getPlanBindings(planId) {
  return request.get(`/coding-plans/${planId}/bindings`)
}

export function createPlanBinding(planId, data) {
  return request.post(`/coding-plans/${planId}/bindings`, data)
}

export function getPlanCostStats(planId) {
  return request.get(`/coding-plans/${planId}/cost-stats`)
}

export function deletePlan(id) {
  return request.delete(`/coding-plans/${id}`)
}

export function probeApi(data) {
  return request.post('/coding-plans/probe-api', data)
}
