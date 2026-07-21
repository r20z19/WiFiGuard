<template>
  <div class="devices-container">
    <!-- Top bar -->
    <el-card class="top-card">
      <div class="top-bar">
        <div class="bar-left">
          <el-input v-model="searchQuery" placeholder="搜索 MAC / IP / 厂商..." size="small" clearable style="width:260px" prefix-icon="Search" />
          <el-tag size="small" :type="accessModeTagType">{{ accessModeText }}</el-tag>
        </div>
        <div class="bar-right">
          <el-button type="primary" size="small" @click="refreshDevices">
            <el-icon><Refresh /></el-icon>刷新
          </el-button>
        </div>
      </div>
    </el-card>

    <!-- Stats row -->
    <el-row :gutter="12" style="margin-top:12px">
      <el-col :span="6">
        <el-card shadow="hover" class="mini-stat">
          <div class="mini-num">{{ alertStore.onlineDevices.length }}</div>
          <div class="mini-label">总设备数</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover" class="mini-stat green">
          <div class="mini-num">{{ normalDevicesCount }}</div>
          <div class="mini-label">正常设备</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover" class="mini-stat orange">
          <div class="mini-num">{{ suspiciousDevicesCount }}</div>
          <div class="mini-label">可疑设备</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover" class="mini-stat blue">
          <div class="mini-num">{{ routerDeviceCount }}</div>
          <div class="mini-label">路由/AP</div>
        </el-card>
      </el-col>
    </el-row>

    <!-- Device table -->
    <el-card style="margin-top:12px">
      <el-table :data="filteredDevices" style="width: 100%" stripe @row-click="showDetail" row-style="cursor:pointer">
        <el-table-column label="类型" width="55">
          <template #default="{ row }">
            <span class="dev-type-icon">{{ getDeviceEmoji(row) }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="mac" label="MAC地址" width="170">
          <template #default="{ row }">
            <span class="mono-link">{{ row.mac }}</span>
          </template>
        </el-table-column>
        <el-table-column label="厂商" width="130">
          <template #default="{ row }">
            <span>{{ row.vendor || '-' }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="ip" label="IP地址" width="140" />
        <el-table-column prop="ssid" label="连接SSID" width="150">
          <template #default="{ row }">
            <span v-if="row.ssid" class="ssid-text">{{ row.ssid }}</span>
            <span v-else class="text-muted">-</span>
          </template>
        </el-table-column>
        <el-table-column prop="signal" label="信号强度" width="130">
          <template #default="{ row }">
            <div class="signal-cell">
              <el-progress :percentage="getSignalPercentage(row.signal)" :color="getSignalColor(row.signal)" :stroke-width="8" style="flex:1" />
              <span class="signal-dbm">{{ row.signal }} dBm</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="风险评估" width="110">
          <template #default="{ row }">
            <div class="risk-cell">
              <el-progress :percentage="calcRiskScore(row)" :color="getRiskColor(calcRiskScore(row))" :stroke-width="6" style="flex:1" />
              <span class="risk-label" :style="{ color: getRiskColor(calcRiskScore(row)) }">{{ getRiskLabel(calcRiskScore(row)) }}</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="75">
          <template #default="{ row }">
            <el-tag :type="row.status === '正常' ? 'success' : 'warning'" size="small">{{ row.status }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="在线时长" width="100">
          <template #default="{ row }">
            <span class="duration-text">{{ calcDuration(row) }}</span>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="180" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" link size="small" @click.stop="showDetail(row)">详情</el-button>
            <el-button type="success" link size="small" @click.stop="addToWhitelist(row)" :disabled="isInWhitelist(row.mac) || isInBlacklist(row.mac) || alertStore.accessListMode !== 'whitelist'" :title="alertStore.accessListMode !== 'whitelist' ? '请先开启白名单模式' : ''">白名单</el-button>
            <el-button type="danger" link size="small" @click.stop="addToBlacklist(row)" :disabled="isInBlacklist(row.mac) || isInWhitelist(row.mac) || alertStore.accessListMode !== 'blacklist'" :title="alertStore.accessListMode !== 'blacklist' ? '请先开启黑名单模式' : ''">黑名单</el-button>
          </template>
        </el-table-column>
      </el-table>
      <el-empty v-if="filteredDevices.length === 0" description="暂无在线设备" :image-size="80" />
    </el-card>

    <!-- Detail Drawer -->
    <el-drawer v-model="drawerVisible" :title="drawerTitle" size="400px" direction="rtl">
      <template v-if="detailDevice">
        <div class="drawer-section">
          <div class="drawer-section-title">设备标识
            <el-button size="small" type="warning" text @click="aiIdentify" :loading="aiIdentifying" style="margin-left:8px">🤖 AI 识别</el-button>
          </div>
          <div v-if="aiDeviceResult" class="ai-identify-result">{{ aiDeviceResult }}</div>
          <el-descriptions :column="1" border size="small">
            <el-descriptions-item label="MAC地址">
              <span class="mono">{{ detailDevice.mac }}</span>
            </el-descriptions-item>
            <el-descriptions-item label="IP地址">{{ detailDevice.ip || '无' }}</el-descriptions-item>
            <el-descriptions-item label="设备类型">
              <span class="dev-type-icon">{{ getDeviceEmoji(detailDevice) }}</span>
              {{ getDeviceTypeName(detailDevice) }}
            </el-descriptions-item>
            <el-descriptions-item label="厂商">{{ detailDevice.vendor || '未知' }}</el-descriptions-item>
          </el-descriptions>
        </div>

        <div class="drawer-section">
          <div class="drawer-section-title">网络信息</div>
          <el-descriptions :column="1" border size="small">
            <el-descriptions-item label="连接SSID">{{ detailDevice.ssid || '无' }}</el-descriptions-item>
            <el-descriptions-item label="信号强度">{{ detailDevice.signal }} dBm</el-descriptions-item>
            <el-descriptions-item label="加密方式">
              <el-tag v-if="detailDevice.pairwiseCipher" type="info" size="small">
                {{ detailDevice.pairwiseCipher }}{{ detailDevice.groupCipher && detailDevice.groupCipher !== detailDevice.pairwiseCipher ? '+' + detailDevice.groupCipher : '' }}
              </el-tag>
              <span v-else>未知</span>
            </el-descriptions-item>
            <el-descriptions-item label="AKM">{{ detailDevice.akm || '未知' }}</el-descriptions-item>
          </el-descriptions>
        </div>

        <div class="drawer-section">
          <div class="drawer-section-title">安全评估</div>
          <div class="risk-score-big">
            <el-progress type="circle" :percentage="calcRiskScore(detailDevice)" :width="100" :color="getRiskColor(calcRiskScore(detailDevice))" />
            <span class="risk-desc">{{ getRiskDesc(calcRiskScore(detailDevice)) }}</span>
          </div>
          <div class="risk-factors">
            <div class="risk-factor" v-for="f in getRiskFactors(detailDevice)" :key="f.text">
              <el-icon :color="f.good ? '#67c23a' : '#f56c6c'">
                <CircleCheck v-if="f.good" /><CircleClose v-else />
              </el-icon>
              <span>{{ f.text }}</span>
            </div>
          </div>
        </div>

        <div class="drawer-section">
          <div class="drawer-section-title">设备标签</div>
          <div class="tag-list">
            <el-tag v-if="isNewDevice(detailDevice)" type="warning" size="small">🆕 新设备</el-tag>
            <el-tag v-if="isLongTerm(detailDevice)" type="success" size="small">🏠 常驻设备</el-tag>
            <el-tag v-if="(detailDevice.signal||-70) < -70" type="warning" size="small">📶 信号异常</el-tag>
            <el-tag v-if="detailDevice.status !== '正常'" type="danger" size="small">⚠ 状态异常</el-tag>
            <el-tag v-if="isInBlacklist(detailDevice.mac)" type="danger" size="small">🚫 已拉黑</el-tag>
            <el-tag v-if="isInWhitelist(detailDevice.mac)" type="success" size="small">✅ 可信</el-tag>
            <span v-if="getTags(detailDevice).length === 0" class="no-tags">暂未标记</span>
          </div>
        </div>

        <div class="drawer-section">
          <div class="drawer-section-title">时间信息</div>
          <el-descriptions :column="1" border size="small">
            <el-descriptions-item label="首次发现">{{ detailDevice.firstSeen || '-' }}</el-descriptions-item>
            <el-descriptions-item label="最后活跃">{{ detailDevice.lastSeen || '-' }}</el-descriptions-item>
            <el-descriptions-item label="在线时长">{{ calcDuration(detailDevice) }}</el-descriptions-item>
          </el-descriptions>
        </div>

        <div class="drawer-section">
          <div class="drawer-section-title">⏱ 行为时间线</div>
          <div class="timeline">
            <div class="tl-item"><span class="tl-dot green"></span>首次发现: {{ detailDevice.firstSeen || '-' }}</div>
            <div class="tl-item"><span class="tl-dot blue"></span>最后活跃: {{ detailDevice.lastSeen || '-' }}</div>
            <div class="tl-item" v-if="deviceAlerts.length > 0"><span class="tl-dot red"></span>检测到 {{ deviceAlerts.length }} 次攻击</div>
            <div class="tl-item" v-if="isInWhitelist(detailDevice.mac)"><span class="tl-dot green"></span>已加入白名单</div>
            <div class="tl-item" v-if="isInBlacklist(detailDevice.mac)"><span class="tl-dot red"></span>已加入黑名单</div>
          </div>
        </div>

        <div class="drawer-section">
          <div class="drawer-section-title">操作</div>
          <div class="drawer-actions">
            <el-button type="success" @click="addToWhitelist(detailDevice)" :disabled="isInWhitelist(detailDevice.mac) || alertStore.accessListMode !== 'whitelist'">{{ alertStore.accessListMode === 'whitelist' ? '加入白名单' : '白名单未启用' }}</el-button>
            <el-button type="danger" @click="addToBlacklist(detailDevice)" :disabled="isInBlacklist(detailDevice.mac) || alertStore.accessListMode !== 'blacklist'">{{ alertStore.accessListMode === 'blacklist' ? '加入黑名单' : '黑名单未启用' }}</el-button>
          </div>
        </div>
      </template>
    </el-drawer>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useAlertStore } from '../store/alert'
import { ElMessage } from 'element-plus'
import { identifyDevice as aiIdentifyDevice } from '../api'
import { CircleCheck, CircleClose } from '@element-plus/icons-vue'

const alertStore = useAlertStore()
const searchQuery = ref('')
const drawerVisible = ref(false)
const detailDevice = ref(null)
const aiDeviceResult = ref('')
const aiIdentifying = ref(false)

const accessModeText = computed(() => {
  if (alertStore.accessListMode === 'whitelist') return '白名单模式'
  if (alertStore.accessListMode === 'blacklist') return '黑名单模式'
  return '未启用'
})

const accessModeTagType = computed(() => {
  if (alertStore.accessListMode === 'whitelist') return 'success'
  if (alertStore.accessListMode === 'blacklist') return 'danger'
  return 'info'
})

const drawerTitle = computed(() => {
  if (!detailDevice.value) return '设备详情'
  return getDeviceEmoji(detailDevice.value) + ' ' + getDeviceTypeName(detailDevice.value)
})

const filteredDevices = computed(() => {
  if (!searchQuery.value) return alertStore.onlineDevices
  const q = searchQuery.value.toLowerCase()
  return alertStore.onlineDevices.filter(d =>
    d.mac.toLowerCase().includes(q) || d.ip.includes(q) || (d.vendor || '').toLowerCase().includes(q) || (d.ssid || '').toLowerCase().includes(q)
  )
})

const normalDevicesCount = computed(() => alertStore.onlineDevices.filter(d => d.status === '正常').length)
const suspiciousDevicesCount = computed(() => alertStore.onlineDevices.filter(d => d.status !== '正常').length)
const routerDeviceCount = computed(() => alertStore.onlineDevices.filter(d => {
  const v = (d.vendor || '').toLowerCase()
  return d.ssid || v.includes('cisco') || v.includes('aruba') || v.includes('tp-link') || v.includes('ubiquiti') || v.includes('router')
}).length)

function getDeviceEmoji(dev) {
  const v = (dev.vendor || '').toLowerCase()
  if (v.includes('apple') || v.includes('samsung') || v.includes('xiaomi') || v.includes('oppo') || v.includes('vivo')) return '📱'
  if (v.includes('dell') || v.includes('lenovo') || v.includes('hp') || v.includes('intel') || v.includes('asus')) return '🖥'
  if (v.includes('cisco') || v.includes('aruba') || v.includes('ubiquiti') || v.includes('tp-link') || v.includes('d-link') || v.includes('netgear') || v.includes('router')) return '📡'
  if (dev.ssid) return '📡'
  return '💻'
}

function getDeviceTypeName(dev) {
  const v = (dev.vendor || '').toLowerCase()
  if (v.includes('apple') || v.includes('samsung') || v.includes('xiaomi')) return '手机/平板'
  if (v.includes('dell') || v.includes('lenovo') || v.includes('hp') || v.includes('intel')) return 'PC/笔记本'
  if (v.includes('cisco') || v.includes('aruba') || v.includes('tp-link') || dev.ssid) return '路由器/AP'
  return '网络设备'
}

function getSignalPercentage(s) { return Math.max(0, Math.min(100, (s + 100) * 2)) }

function getSignalColor(s) {
  if (s >= -50) return '#67c23a'
  if (s >= -70) return '#e6a23c'
  return '#f56c6c'
}

// Risk scoring
function calcRiskScore(dev) {
  let score = 0
  // Signal risk
  if (dev.signal < -80) score += 25
  else if (dev.signal < -70) score += 15
  // Encryption risk
  const enc = ((dev.pairwiseCipher || '') + (dev.groupCipher || '')).toLowerCase()
  if (enc.includes('wep')) score += 30
  else if (!enc || enc === 'unknown') score += 10
  else if (enc.includes('tkip') && !enc.includes('ccmp')) score += 15
  // Status
  if (dev.status === '可疑') score += 20
  // Blacklist
  if (isInBlacklist(dev.mac)) score = 100
  // Whitelist
  if (isInWhitelist(dev.mac)) score = Math.min(score, 20)

  return Math.min(100, Math.max(0, score))
}

function getRiskColor(score) {
  if (score >= 70) return '#f56c6c'
  if (score >= 40) return '#e6a23c'
  if (score >= 20) return '#409eff'
  return '#67c23a'
}

function getRiskLabel(score) {
  if (score >= 70) return '高风险'
  if (score >= 40) return '中风险'
  if (score >= 20) return '低风险'
  return '安全'
}

function getRiskDesc(score) {
  if (score >= 70) return '该设备存在严重安全风险，建议立即加入黑名单'
  if (score >= 40) return '该设备存在一定安全风险，建议密切关注'
  if (score >= 20) return '低风险设备，建议加入白名单'
  return '设备安全状态良好'
}

function getRiskFactors(dev) {
  const factors = []
  factors.push({ text: `信号强度: ${dev.signal} dBm`, good: dev.signal >= -70 })
  const enc = ((dev.pairwiseCipher || '') + (dev.groupCipher || '')).toLowerCase()
  factors.push({ text: enc ? `加密方式: ${dev.pairwiseCipher || '未知'}` : '无加密信息', good: !!enc && !enc.includes('wep') })
  factors.push({ text: `设备状态: ${dev.status}`, good: dev.status === '正常' })
  factors.push({ text: isInWhitelist(dev.mac) ? '在白名单中' : '未在白名单', good: isInWhitelist(dev.mac) })
  factors.push({ text: isInBlacklist(dev.mac) ? '在黑名单中 ⚠' : '未在黑名单', good: !isInBlacklist(dev.mac) })
  return factors
}

function calcDuration(dev) {
  try {
    const diff = Date.now() - new Date(dev.firstSeen).getTime()
    const mins = Math.floor(diff / 60000)
    if (mins < 1) return '刚刚'
    if (mins < 60) return mins + '分钟'
    if (mins < 1440) return Math.floor(mins/60) + '小时'
    return Math.floor(mins/1440) + '天'
  } catch { return '-' }
}
function isInWhitelist(mac) { return alertStore.whitelist.some(d => d.mac === mac) }
function isInBlacklist(mac) { return alertStore.blacklist.some(d => d.mac === mac) }

function isNewDevice(dev) {
  if (!dev.firstSeen) return false
  try { return (Date.now() - new Date(dev.firstSeen).getTime()) < 3600000 } catch { return false }
}
function isLongTerm(dev) {
  if (!dev.firstSeen) return false
  try { return (Date.now() - new Date(dev.firstSeen).getTime()) > 86400000 } catch { return false }
}
function getTags(dev) {
  const tags = []
  if (isNewDevice(dev)) tags.push('新设备')
  if (isLongTerm(dev)) tags.push('常驻设备')
  if ((dev.signal || -70) < -70) tags.push('信号异常')
  if (dev.status !== '正常') tags.push('状态异常')
  return tags
}

const deviceAlerts = computed(() => {
  if (!detailDevice.value) return []
  return alertStore.currentAlerts.filter(a => a.sourceMac === detailDevice.value.mac || a.targetMac === detailDevice.value.mac)
})

async function aiIdentify() {
  if (!detailDevice.value) return
  aiIdentifying.value = true; aiDeviceResult.value = ''
  try {
    const resp = await aiIdentifyDevice({ device: {
      mac: detailDevice.value.mac, vendor: detailDevice.value.vendor,
      ssid: detailDevice.value.ssid, signal: detailDevice.value.signal,
      firstSeen: detailDevice.value.firstSeen, status: detailDevice.value.status,
      pairwiseCipher: detailDevice.value.pairwiseCipher,
    }})
    aiDeviceResult.value = resp.result
  } catch { ElMessage.error('AI 识别失败') }
  aiIdentifying.value = false
}

function showDetail(row) {
  detailDevice.value = row
  drawerVisible.value = true
}

async function addToWhitelist(device) {
  try {
    await alertStore.addToWhitelist({ mac: device.mac, name: `${getDeviceTypeName(device)}-${device.mac.slice(-4)}` })
    ElMessage.success(`设备 ${device.mac} 已加入白名单`)
  } catch (e) { ElMessage.error(e.message || '加入白名单失败') }
}

async function addToBlacklist(device) {
  try {
    await alertStore.addToBlacklist({ mac: device.mac, name: `${getDeviceTypeName(device)}-${device.mac.slice(-4)}`, reason: `手动添加: 风险评估 ${calcRiskScore(device)} 分` })
    ElMessage.warning(`设备 ${device.mac} 已加入黑名单`)
  } catch (e) { ElMessage.error(e.message || '加入黑名单失败') }
}

function refreshDevices() {
  alertStore.fetchOnlineDevices()
  ElMessage.success('已刷新')
}

onMounted(() => {
  alertStore.fetchOnlineDevices()
  alertStore.fetchWhitelist()
  alertStore.fetchBlacklist()
})
</script>

<style scoped>
.devices-container { padding: 16px; }
.top-card { border-radius: 10px; }
.top-card :deep(.el-card__body) { padding: 12px 16px; }
.top-bar { display: flex; justify-content: space-between; align-items: center; gap: 12px; }
.bar-left { display: flex; align-items: center; gap: 10px; }
.bar-right { display: flex; gap: 8px; }

/* Mini stats */
.mini-stat { text-align: center; border-radius: 10px; }
.mini-stat.green { border-top: 3px solid #67c23a; }
.mini-stat.orange { border-top: 3px solid #e6a23c; }
.mini-stat.blue { border-top: 3px solid #409eff; }
.mini-num { font-size: 28px; font-weight: bold; color: #303133; }
.mini-label { font-size: 12px; color: #909399; margin-top: 4px; }

.dev-type-icon { font-size: 20px; }
.mono-link { font-family: monospace; font-size: 12px; color: #409eff; }
.ssid-text { font-weight: 500; color: #303133; }
.text-muted { color: #c0c4cc; }

.signal-cell { display: flex; align-items: center; gap: 6px; }
.signal-dbm { font-size: 11px; color: #909399; white-space: nowrap; }

.risk-cell { display: flex; align-items: center; gap: 4px; }
.risk-label { font-size: 11px; font-weight: 500; white-space: nowrap; }

/* Drawer */
.drawer-section { margin-bottom: 20px; }
.drawer-section-title { font-weight: 600; font-size: 13px; color: #303133; margin-bottom: 10px; padding-bottom: 6px; border-bottom: 1px solid #ebeef5; }
.mono { font-family: monospace; font-size: 12px; }

.risk-score-big { text-align: center; padding: 16px; }
.risk-desc { display: block; margin-top: 10px; font-size: 12px; color: #909399; }

.risk-factors { margin-top: 12px; }
.risk-factor { display: flex; align-items: center; gap: 8px; padding: 5px 0; font-size: 12px; color: #606266; }

.drawer-actions { display: flex; gap: 10px; }
.tag-list { display: flex; flex-wrap: wrap; gap: 6px; }
.no-tags { font-size: 12px; color: #c0c4cc; }
.timeline { padding: 4px 0; }
.tl-item { display: flex; align-items: center; gap: 8px; padding: 4px 0; font-size: 12px; color: #606266; }
.tl-dot { width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0; }
.tl-dot.green { background: #67c23a; }
.tl-dot.blue { background: #409eff; }
.tl-dot.red { background: #f56c6c; }
.ai-identify-result { margin-top: 6px; padding: 8px 10px; background: #fef9e7; border: 1px solid #f0d080; border-radius: 6px; font-size: 12px; color: #665500; line-height: 1.6; }
</style>
