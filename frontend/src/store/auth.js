import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { login as apiLogin, verifyLogin as apiVerifyLogin } from '../api/index'

export const useAuthStore = defineStore('auth', () => {
  const token = ref(localStorage.getItem('token') || '')
  const isFirstLogin = ref(localStorage.getItem('isFirstLogin') !== 'false')
  const userInfo = ref({
    username: localStorage.getItem('username') || '',
    isDefaultPassword: isFirstLogin.value
  })

  const isLoggedIn = computed(() => !!token.value)

  function setToken(newToken) {
    token.value = newToken
    localStorage.setItem('token', newToken)
  }

  function setUserInfo(info) {
    userInfo.value = info
    localStorage.setItem('username', info.username || '')
    if (info.isFirstLogin !== undefined) {
      isFirstLogin.value = info.isFirstLogin
      localStorage.setItem('isFirstLogin', info.isFirstLogin ? 'true' : 'false')
    }
  }

  function logout() {
    token.value = ''
    userInfo.value = { username: '', isDefaultPassword: true }
    localStorage.removeItem('token')
    localStorage.removeItem('username')
    localStorage.removeItem('isFirstLogin')
  }

  async function login(credentials) {
    try {
      const response = await apiLogin(credentials)
      if (response.token) {
        setToken(response.token)
        setUserInfo({
          username: credentials.username,
          isFirstLogin: response.isFirstLogin || false
        })
        return { success: true, isFirstLogin: response.isFirstLogin || false }
      }
      return { success: false, message: response.message || '登录失败' }
    } catch (e) {
      return { success: false, message: '登录失败，请检查网络连接' }
    }
  }

  async function verifyLogin() {
    if (!token.value) {
      return { success: false }
    }
    try {
      const response = await apiVerifyLogin()
      if (response.valid) {
        setUserInfo({
          username: response.username,
          isFirstLogin: response.isFirstLogin || false
        })
        return { success: true }
      }
      logout()
      return { success: false }
    } catch (e) {
      logout()
      return { success: false }
    }
  }

  return {
    token,
    isLoggedIn,
    userInfo,
    isFirstLogin,
    login,
    logout,
    verifyLogin,
    setUserInfo
  }
})
