import request from '../utils/request'

export function getDeployTasks(params) {
  return request.get('/deploy-tasks', { params })
}

export function createDeployTask(data) {
  return request.post('/deploy-tasks', data)
}

export function getDeployTask(id) {
  return request.get(`/deploy-tasks/${id}`)
}
