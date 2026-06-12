import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useAlertStore = defineStore('alert', () => {
  const currentAlerts = ref([
    {
      id: 1,
      type: 'Deauth攻击',
      severity: 'high',
      sourceMac: 'AA:BB:CC:DD:EE:01',
      targetMac: 'AA:BB:CC:DD:EE:02',
      timestamp: '2026-05-11 14:32:15',
      suggestion: '检测到Deauth泛洪攻击，建议启用802.11w PMF保护，并检查AP是否配置了最大去认证速率限制。'
    },
    {
      id: 2,
      type: '钓鱼AP',
      severity: 'critical',
      sourceMac: 'FF:EE:DD:CC:BB:01',
      targetMac: 'Unknown',
      timestamp: '2026-05-11 14:28:42',
      suggestion: '发现疑似钓鱼AP（Evil Twin），SSID与合法AP相似。建议立即断开连接并报告网络管理员。'
    }
  ])

  const historyAlerts = ref([
    {
      id: 101,
      type: '暴力破解',
      severity: 'medium',
      sourceMac: '11:22:33:44:55:01',
      targetMac: '11:22:33:44:55:02',
      timestamp: '2026-05-10 09:15:30',
      status: '已处理'
    },
    {
      id: 102,
      type: '非法接入',
      severity: 'high',
      sourceMac: '66:77:88:99:AA:01',
      targetMac: 'Unknown',
      timestamp: '2026-05-09 16:42:18',
      status: '已处理'
    },
    {
      id: 103,
      type: 'Flood泛洪',
      severity: 'medium',
      sourceMac: 'BB:CC:DD:EE:FF:01',
      targetMac: 'BB:CC:DD:EE:FF:02',
      timestamp: '2026-05-08 11:23:45',
      status: '已忽略'
    }
  ])

  const onlineDevices = ref([
    {
      mac: 'AA:BB:CC:DD:EE:01',
      ip: '192.168.1.100',
      ssid: 'WiFiGuard-Network',
      signal: -45,
      status: '正常',
      firstSeen: '2026-05-11 08:00:00',
      lastSeen: '2026-05-11 14:35:22'
    },
    {
      mac: 'AA:BB:CC:DD:EE:02',
      ip: '192.168.1.101',
      ssid: 'WiFiGuard-Network',
      signal: -62,
      status: '正常',
      firstSeen: '2026-05-11 09:30:15',
      lastSeen: '2026-05-11 14:35:18'
    },
    {
      mac: '11:22:33:44:55:03',
      ip: '192.168.1.105',
      ssid: 'WiFiGuard-Network',
      signal: -78,
      status: '可疑',
      firstSeen: '2026-05-11 13:15:00',
      lastSeen: '2026-05-11 14:34:55'
    }
  ])

  const whitelist = ref([
    { mac: 'AA:BB:CC:DD:EE:01', name: '管理员手机', addedAt: '2026-05-01 10:00:00' },
    { mac: 'AA:BB:CC:DD:EE:02', name: '办公电脑', addedAt: '2026-05-01 10:05:00' },
    { mac: 'AA:BB:CC:DD:EE:03', name: '会议室AP', addedAt: '2026-05-02 14:30:00' }
  ])

  const blacklist = ref([
    { mac: 'FF:EE:DD:CC:BB:01', name: '可疑钓鱼AP', reason: 'Evil Twin攻击', addedAt: '2026-05-10 16:20:00' },
    { mac: '11:22:33:44:55:01', name: '攻击设备', reason: '暴力破解攻击', addedAt: '2026-05-09 09:45:00' }
  ])

  const emailConfig = ref({
    smtpHost: 'smtp.qq.com',
    smtpPort: 465,
    email: 'your_email@qq.com',
    authorizationCode: '',
    recipientEmail: 'admin@company.com',
    enabled: false
  })

  function addAlert(alert) {
    currentAlerts.value.unshift(alert)
  }

  function clearAlert(id) {
    const index = currentAlerts.value.findIndex(a => a.id === id)
    if (index !== -1) {
      const alert = currentAlerts.value.splice(index, 1)[0]
      alert.status = '已处理'
      historyAlerts.value.unshift(alert)
    }
  }

  function addToWhitelist(device) {
    whitelist.value.push(device)
  }

  function removeFromWhitelist(mac) {
    whitelist.value = whitelist.value.filter(d => d.mac !== mac)
  }

  function addToBlacklist(device) {
    blacklist.value.push(device)
  }

  function removeFromBlacklist(mac) {
    blacklist.value = blacklist.value.filter(d => d.mac !== mac)
  }

  function updateEmailConfig(config) {
    emailConfig.value = { ...emailConfig.value, ...config }
  }

  return {
    currentAlerts,
    historyAlerts,
    onlineDevices,
    whitelist,
    blacklist,
    emailConfig,
    addAlert,
    clearAlert,
    addToWhitelist,
    removeFromWhitelist,
    addToBlacklist,
    removeFromBlacklist,
    updateEmailConfig
  }
})
