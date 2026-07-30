import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import {
  getSystemStatus,
  getCurrentAlerts,
  getHistoryAlerts,
  getOnlineDevices,
  getWhitelist,
  addToWhitelist as apiAddToWhitelist,
  removeFromWhitelist as apiRemoveFromWhitelist,
  getBlacklist,
  addToBlacklist as apiAddToBlacklist,
  removeFromBlacklist as apiRemoveFromBlacklist,
  getEmailConfig,
  updateEmailConfig as apiUpdateEmailConfig,
  testEmailConnection,
  getEmailRecords,
  clearAlert as apiClearAlert,
  updateAccessMode as apiUpdateAccessMode
} from '../api/index'

export const useAlertStore = defineStore('alert', () => {
  const systemStatus = ref({ status: 'initializing', uptime: 0, monitorInterface: '' })
  const currentAlerts = ref([])
  const historyAlerts = ref([])
  const onlineDevices = ref([])
  const whitelist = ref([])
  const blacklist = ref([])
  const accessMode = ref({ whitelist: false, blacklist: false })
  const emailConfig = ref({
    smtpHost: '',
    smtpPort: 465,
    email: '',
    authorizationCode: '',
    recipientEmail: '',
    enabled: false
  })
  const emailRecords = ref([])
  const loading = ref(false)

  async function fetchSystemStatus() {
    try {
      systemStatus.value = await getSystemStatus()
      // Sync access mode from backend
      accessMode.value = {
        whitelist: systemStatus.value.whitelistEnabled ?? false,
        blacklist: systemStatus.value.blacklistEnabled ?? false,
      }
    } catch (e) {
      console.error('fetchSystemStatus failed:', e)
    }
  }

  async function fetchCurrentAlerts() {
    try {
      currentAlerts.value = await getCurrentAlerts()
    } catch (e) {
      console.error('fetchCurrentAlerts failed:', e)
    }
  }

  async function fetchHistoryAlerts(params) {
    try {
      historyAlerts.value = await getHistoryAlerts(params)
    } catch (e) {
      console.error('fetchHistoryAlerts failed:', e)
    }
  }

  async function fetchOnlineDevices() {
    try {
      onlineDevices.value = await getOnlineDevices()
    } catch (e) {
      console.error('fetchOnlineDevices failed:', e)
    }
  }

  async function fetchWhitelist() {
    try {
      whitelist.value = await getWhitelist()
    } catch (e) {
      console.error('fetchWhitelist failed:', e)
    }
  }

  async function fetchBlacklist() {
    try {
      blacklist.value = await getBlacklist()
    } catch (e) {
      console.error('fetchBlacklist failed:', e)
    }
  }

  async function fetchEmailConfig() {
    try {
      emailConfig.value = await getEmailConfig()
    } catch (e) {
      console.error('fetchEmailConfig failed:', e)
    }
  }

  async function fetchEmailRecords() {
    try {
      emailRecords.value = await getEmailRecords()
    } catch (e) {
      console.error('fetchEmailRecords failed:', e)
    }
  }

  async function clearAlert(id) {
    try {
      await apiClearAlert(id)
      await fetchCurrentAlerts()
      await fetchHistoryAlerts()
    } catch (e) {
      console.error('clearAlert failed:', e)
    }
  }

  async function addAlert(alert) {
    currentAlerts.value.unshift(alert)
  }

  async function addToWhitelist(device) {
    try {
      await apiAddToWhitelist({
        mac: device.mac,
        name: device.name || `设备-${device.mac.slice(-4)}`,
        deviceType: device.deviceType || ''
      })
      await fetchWhitelist()
    } catch (e) {
      console.error('addToWhitelist failed:', e)
      throw e
    }
  }

  async function removeFromWhitelist(mac) {
    try {
      await apiRemoveFromWhitelist(mac)
      await fetchWhitelist()
    } catch (e) {
      console.error('removeFromWhitelist failed:', e)
      throw e
    }
  }

  async function addToBlacklist(device) {
    try {
      await apiAddToBlacklist({
        mac: device.mac,
        name: device.name || `设备-${device.mac.slice(-4)}`,
        reason: device.reason || '手动添加'
      })
      await fetchBlacklist()
    } catch (e) {
      console.error('addToBlacklist failed:', e)
      throw e
    }
  }

  async function removeFromBlacklist(mac) {
    try {
      await apiRemoveFromBlacklist(mac)
      await fetchBlacklist()
    } catch (e) {
      console.error('removeFromBlacklist failed:', e)
      throw e
    }
  }

  async function updateEmailConfig(config) {
    try {
      emailConfig.value = await apiUpdateEmailConfig(config)
    } catch (e) {
      console.error('updateEmailConfig failed:', e)
      throw e
    }
  }

  async function testEmail(config) {
    return await testEmailConnection(config)
  }

  // Backward-compatible getter for views that still use accessListMode
  const accessListMode = computed(() => {
    if (accessMode.value.whitelist && accessMode.value.blacklist) return 'both'
    if (accessMode.value.whitelist) return 'whitelist'
    if (accessMode.value.blacklist) return 'blacklist'
    return ''
  })

  async function setWhitelistEnabled(enabled) {
    try {
      const res = await apiUpdateAccessMode({ whitelistEnabled: enabled })
      accessMode.value.whitelist = res.whitelistEnabled
    } catch (e) {
      console.error('setWhitelistEnabled failed:', e)
      throw e
    }
  }

  async function setBlacklistEnabled(enabled) {
    try {
      const res = await apiUpdateAccessMode({ blacklistEnabled: enabled })
      accessMode.value.blacklist = res.blacklistEnabled
    } catch (e) {
      console.error('setBlacklistEnabled failed:', e)
      throw e
    }
  }

  return {
    systemStatus,
    currentAlerts,
    historyAlerts,
    onlineDevices,
    whitelist,
    blacklist,
    accessMode,
    accessListMode,
    emailConfig,
    emailRecords,
    loading,
    fetchSystemStatus,
    fetchCurrentAlerts,
    fetchHistoryAlerts,
    fetchOnlineDevices,
    fetchWhitelist,
    fetchBlacklist,
    fetchEmailConfig,
    fetchEmailRecords,
    clearAlert,
    addAlert,
    addToWhitelist,
    removeFromWhitelist,
    addToBlacklist,
    removeFromBlacklist,
    updateEmailConfig,
    testEmail,
    setWhitelistEnabled,
    setBlacklistEnabled
  }
})
