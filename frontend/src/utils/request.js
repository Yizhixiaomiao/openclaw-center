import axios from 'axios'
import { ElMessage } from 'element-plus'
import { getToken, removeToken } from './auth'

const request = axios.create({
  baseURL: '/api',
  timeout: 15000,
})

request.interceptors.request.use(
  (config) => {
    const token = getToken()
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => Promise.reject(error)
)

request.interceptors.response.use(
  (response) => response.data,
  (error) => {
    const msg = error.response?.data?.detail || error.message || '请求失败'
    if (error.response?.status === 401) {
      removeToken()
      window.location.href = '/login'
    } else {
      ElMessage.error(msg)
    }
    return Promise.reject(error)
  }
)

export default request
