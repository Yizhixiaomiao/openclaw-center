import { defineStore } from 'pinia'
import { ref } from 'vue'
import { setToken, removeToken, getToken } from '../utils/auth'

export const useAuthStore = defineStore('auth', () => {
  const token = ref(getToken() || '')
  const userId = ref(null)
  const userName = ref('')
  const userRole = ref('')

  function setLogin(data) {
    token.value = data.access_token
    userId.value = data.user_id
    userName.value = data.name
    userRole.value = data.role
    setToken(data.access_token)
  }

  function logout() {
    token.value = ''
    userId.value = null
    userName.value = ''
    userRole.value = ''
    removeToken()
  }

  return { token, userId, userName, userRole, setLogin, logout }
})
