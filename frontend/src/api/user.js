import request from '../utils/request'

export function getUsers(params) {
  return request.get('/users', { params })
}

export function createUser(data) {
  return request.post('/users', data)
}

export function getUser(id) {
  return request.get(`/users/${id}`)
}

export function updateUser(id, data) {
  return request.put(`/users/${id}`, data)
}

export function getUserProfile(id) {
  return request.get(`/users/${id}/profile`)
}

export function updateUserProfile(id, data) {
  return request.put(`/users/${id}/profile`, data)
}

export function getUserScenarios(id) {
  return request.get(`/users/${id}/scenarios`)
}

export function deleteUser(id) {
  return request.delete(`/users/${id}`)
}
