import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 10000
})

api.interceptors.request.use(
  config => {
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

export default api
