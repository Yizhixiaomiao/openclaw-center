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
