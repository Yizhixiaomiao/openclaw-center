import request from '../utils/request'

export function getMonitorOverview() {
  return request.get('/monitor/overview')
}

export function getMonitorMachines(params) {
  return request.get('/monitor/machines', { params })
}

export function getMonitorLogs(params) {
  return request.get('/monitor/logs', { params })
}

export function getMonitorAlerts() {
  return request.get('/monitor/alerts')
}

export function getUsageTrend(days = 7) {
  return request.get('/monitor/usage-trend', { params: { days } })
}

export function getMachineStats() {
  return request.get('/monitor/machine-stats')
}

export function getSkillRanking(limit = 10) {
  return request.get('/monitor/skill-ranking', { params: { limit } })
}

export function getDeployStats() {
  return request.get('/monitor/deploy-stats')
}
