import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 10000
})

api.interceptors.request.use(
  config => {
    const token = localStorage.getItem('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  error => {
    return Promise.reject(error)
  }
)

api.interceptors.response.use(
  response => {
    return response.data
  },
  error => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token')
      localStorage.removeItem('username')
      localStorage.removeItem('isFirstLogin')
      if (window.location.pathname !== '/login') {
        window.location.href = '/login'
      }
    }
    if (error.response?.data?.error) {
      error.message = error.response.data.error
    }
    console.error('API Error:', error)
    return Promise.reject(error)
  }
)

export const getSystemStatus = () => api.get('/system/status')

export const getCurrentAlerts = () => api.get('/alerts/current')

export const getHistoryAlerts = (params) => api.get('/alerts/history', { params })

export const getOnlineDevices = () => api.get('/devices/online')

export const getWhitelist = () => api.get('/devices/whitelist')

export const addToWhitelist = (data) => api.post('/devices/whitelist', data)

export const removeFromWhitelist = (mac) => api.delete(`/devices/whitelist/${mac}`)

export const getBlacklist = () => api.get('/devices/blacklist')

export const addToBlacklist = (data) => api.post('/devices/blacklist', data)

export const removeFromBlacklist = (mac) => api.delete(`/devices/blacklist/${mac}`)

export const getEmailConfig = () => api.get('/email/config')

export const updateEmailConfig = (data) => api.put('/email/config', data)

export const testEmailConnection = (data) => api.post('/email/test', data)

export const getEmailRecords = () => api.get('/email/records')

export const clearAlert = (id) => api.post(`/alerts/${id}/clear`)

export const login = (data) => api.post('/auth/login', data)

export const verifyLogin = () => api.get('/auth/verify')

export const changePassword = (data) => api.post('/auth/change-password', data)

export const getNetworkLocations = () => api.get('/geo/locations')

export const getIpLocation = (ip) => api.get('/geo/ip', { params: { ip } })

export const getLogs = (params) => api.get('/logs', { params })
export const getLogStats = () => api.get('/logs/stats')
export const exportLogs = (params) => api.get('/logs/export', { params, responseType: 'blob' })

export const getAiConfig = () => api.get('/ai/config')
export const saveAiConfig = (data) => api.post('/ai/config', data)
export const interpretAlert = (alert) => api.post('/ai/interpret', alert)
export const chatAi = (data) => api.post('/ai/chat', data)
export const generateAiReport = (data) => api.post('/ai/report', data)
export const identifyDevice = (data) => api.post('/ai/identify', data)
export const detectAnomalies = (data) => api.post('/ai/anomalies', data)
export const predictThreats = (data) => api.post('/ai/predict', data)

export default api
