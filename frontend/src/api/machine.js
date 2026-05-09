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
