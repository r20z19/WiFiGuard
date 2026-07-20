<template>
  <div class="dashboard-container">
    <!-- View toggle bar -->
    <div class="view-toggle-bar">
      <span class="toggle-label">视图模式：</span>
      <el-button-group>
        <el-button type="primary" size="small">
          <el-icon><Grid /></el-icon>
          <span style="margin-left:4px">2D 仪表盘</span>
        </el-button>
        <el-button size="small" @click="$router.push('/map')">
          <el-icon><House /></el-icon>
          <span style="margin-left:4px">网络拓扑</span>
        </el-button>
      </el-button-group>
    </div>

    <!-- Status cards with inline trends -->
    <el-row :gutter="16" class="status-cards">
      <el-col :span="6">
        <el-card class="status-card" :class="systemStatus.class" shadow="hover" @click="$router.push('/devices')">
          <div class="card-top">
            <div class="card-icon-wrap" :class="systemStatus.class">
              <el-icon :size="28"><Cpu /></el-icon>
            </div>
            <div class="card-info">
              <div class="card-label">系统状态</div>
              <div class="card-value">{{ systemStatus.text }}</div>
            </div>
          </div>
          <div class="card-footer">
            <span>运行时长 {{ uptimeStr }}</span>
          </div>
        </el-card>
      </el-col>

      <el-col :span="6">
        <el-card class="status-card danger" shadow="hover" @click="$router.push('/alerts')">
          <div class="card-top">
            <div class="card-icon-wrap danger">
              <el-icon :size="28"><Warning /></el-icon>
            </div>
            <div class="card-info">
              <div class="card-label">当前告警</div>
              <div class="card-value">{{ alertStore.currentAlerts.length }}</div>
            </div>
          </div>
          <div class="card-footer">
            <span class="danger-text">高危 {{ criticalCount }} / 中危 {{ mediumCount }}</span>
          </div>
        </el-card>
      </el-col>

      <el-col :span="6">
        <el-card class="status-card info" shadow="hover" @click="$router.push('/devices')">
          <div class="card-top">
            <div class="card-icon-wrap info">
              <el-icon :size="28"><Cellphone /></el-icon>
            </div>
            <div class="card-info">
              <div class="card-label">在线设备</div>
              <div class="card-value">{{ alertStore.onlineDevices.length }}</div>
            </div>
          </div>
          <div class="card-footer">
            <span>正常 {{ normalDeviceCount }} / 可疑 {{ suspiciousDeviceCount }}</span>
          </div>
        </el-card>
      </el-col>

      <el-col :span="6">
        <el-card class="status-card success" shadow="hover" @click="$router.push('/alerts')">
          <div class="card-top">
            <div class="card-icon-wrap success">
              <el-icon :size="28"><Clock /></el-icon>
            </div>
            <div class="card-info">
              <div class="card-label">今日告警</div>
              <div class="card-value">{{ todayAlertCount }}</div>
            </div>
          </div>
          <div class="card-footer">
            <span>历史总计 {{ alertStore.historyAlerts.length }}</span>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- Main content area -->
    <el-row :gutter="16" class="main-content">
      <!-- Left column: alerts + suggestions -->
      <el-col :span="16">
        <!-- Current alerts table -->
        <el-card class="section-card">
          <template #header>
            <div class="card-header">
              <span>当前告警信息</span>
              <div class="header-actions">
                <el-button-group class="quick-filters">
                  <el-button size="small" :type="alertFilter === 'all' ? 'primary' : ''" @click="alertFilter = 'all'">全部</el-button>
                  <el-button size="small" :type="alertFilter === 'critical' ? 'danger' : ''" @click="alertFilter = 'critical'">严重</el-button>
                  <el-button size="small" :type="alertFilter === 'high' ? 'danger' : ''" @click="alertFilter = 'high'">高危</el-button>
                  <el-button size="small" :type="alertFilter === 'medium' ? 'warning' : ''" @click="alertFilter = 'medium'">中危</el-button>
                </el-button-group>
                <el-button type="primary" size="small" @click="$router.push('/alerts')">查看全部</el-button>
              </div>
            </div>
          </template>

          <el-table :data="filteredAlerts.slice(0, 10)" style="width: 100%" size="small" stripe>
            <el-table-column prop="type" label="攻击类型" width="120">
              <template #default="{ row }">
                <el-tag :type="getAttackTag(row.type)" size="small">{{ row.type }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="severity" label="等级" width="70">
              <template #default="{ row }">
                <el-tag :type="getSeverityType(row.severity)" size="small">{{ getSeverityLabel(row.severity) }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="sourceMac" label="源 MAC" width="150">
              <template #default="{ row }">
                <span class="mono-text">{{ row.sourceMac }}</span>
              </template>
            </el-table-column>
            <el-table-column prop="targetMac" label="目标 MAC" width="150">
              <template #default="{ row }">
                <span class="mono-text">{{ row.targetMac || '-' }}</span>
              </template>
            </el-table-column>
            <el-table-column prop="timestamp" label="时间" width="150">
              <template #default="{ row }">
                <span class="time-text">{{ formatRelative(row.timestamp) }}</span>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="120" fixed="right">
              <template #default="{ row }">
                <el-button type="primary" link size="small" @click="$router.push('/alerts')">详情</el-button>
                <el-button type="danger" link size="small" @click="handleClear(row.id)">清除</el-button>
              </template>
            </el-table-column>
          </el-table>

          <el-empty v-if="filteredAlerts.length === 0" description="暂无告警，系统运行正常 🎉" :image-size="80" />
        </el-card>

        <!-- Security suggestions -->
        <el-card class="section-card" style="margin-top:16px">
          <template #header><span>安全建议</span></template>
          <el-row :gutter="12">
            <el-col :span="8" v-for="(sug, idx) in suggestionsWithActions" :key="idx">
              <div class="suggestion-card" :class="'sev-' + sug.severity">
                <div class="sug-header">
                  <span class="sug-icon">{{ sug.icon }}</span>
                  <span class="sug-title">{{ sug.title }}</span>
                </div>
                <p class="sug-desc">{{ sug.desc }}</p>
                <el-button
                  :type="sug.severity === 'critical' ? 'danger' : sug.severity === 'high' ? 'warning' : 'primary'"
                  size="small"
                  @click="sug.action()"
                >
                  {{ sug.btnText }}
                </el-button>
              </div>
            </el-col>
          </el-row>
        </el-card>
      </el-col>

      <!-- Right column: charts -->
      <el-col :span="8">
        <!-- Attack type bar chart -->
        <el-card class="section-card">
          <template #header><span>攻击类型统计</span></template>
          <div ref="barChartRef" class="mini-chart"></div>
        </el-card>

        <!-- Attack distribution pie chart -->
        <el-card class="section-card" style="margin-top:12px">
          <template #header><span>攻击类型占比</span></template>
          <div ref="pieChartRef" class="mini-chart"></div>
        </el-card>

        <!-- Online devices quick list -->
        <el-card class="section-card" style="margin-top:12px">
          <template #header>
            <div class="card-header">
              <span>在线设备</span>
              <el-button type="primary" link size="small" @click="$router.push('/devices')">更多</el-button>
            </div>
          </template>
          <div v-for="dev in alertStore.onlineDevices.slice(0, 8)" :key="dev.mac" class="device-row">
            <div class="dev-left">
              <span class="dev-icon">{{ getDeviceEmoji(dev) }}</span>
              <div class="dev-info">
                <div class="dev-mac">{{ dev.mac }}</div>
                <div class="dev-sub">
                  <span>{{ dev.ip || '无IP' }}</span>
                  <span v-if="dev.vendor">· {{ dev.vendor }}</span>
                </div>
              </div>
            </div>
            <div class="dev-right">
              <el-tag :type="dev.status === '正常' ? 'success' : 'warning'" size="small">{{ dev.status }}</el-tag>
            </div>
          </div>
          <el-empty v-if="alertStore.onlineDevices.length === 0" description="暂无在线设备" :image-size="60" />
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, nextTick, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useAlertStore } from '../store/alert'
import * as echarts from 'echarts'

const router = useRouter()
const alertStore = useAlertStore()

const alertFilter = ref('all')
const pieChartRef = ref(null)
const barChartRef = ref(null)
let pieChart = null
let barChart = null
let resizeObs = null

const criticalCount = computed(() => alertStore.currentAlerts.filter(a => a.severity === 'critical').length)
const mediumCount = computed(() => alertStore.currentAlerts.filter(a => a.severity === 'medium').length)
const normalDeviceCount = computed(() => alertStore.onlineDevices.filter(d => d.status === '正常').length)
const suspiciousDeviceCount = computed(() => alertStore.onlineDevices.filter(d => d.status !== '正常').length)

const todayAlertCount = computed(() => {
  const today = new Date().toISOString().slice(0, 10)
  return alertStore.historyAlerts.filter(a => (a.timestamp || '').startsWith(today)).length
})

const uptimeStr = computed(() => {
  const s = alertStore.systemStatus.uptime || 0
  if (s < 60) return s + '秒'
  if (s < 3600) return Math.floor(s / 60) + '分钟'
  return Math.floor(s / 3600) + '小时'
})

const filteredAlerts = computed(() => {
  if (alertFilter.value === 'all') return alertStore.currentAlerts
  return alertStore.currentAlerts.filter(a => a.severity === alertFilter.value)
})

const systemStatus = computed(() => {
  const s = alertStore.systemStatus.status
  if (s === 'listening') return { text: '监听中', class: 'success' }
  if (s === 'initializing') return { text: '初始化中', class: 'warning' }
  return { text: s || '未知', class: 'info' }
})

// Security suggestions with actions
const suggestionsWithActions = computed(() => {
  const alerts = alertStore.currentAlerts
  const hasCritical = alerts.some(a => a.severity === 'critical')
  const hasHigh = alerts.some(a => a.severity === 'high')
  const hasDeauth = alerts.some(a => a.type === 'Deauth攻击')
  const hasEvilTwin = alerts.some(a => a.type === '钓鱼AP')
  const whiteCount = alertStore.whitelist.length
  const emailEnabled = alertStore.emailConfig.enabled

  const items = []

  if (hasCritical || hasHigh) {
    items.push({
      icon: '🚨', title: '紧急处置',
      desc: `当前有 ${alerts.filter(a => a.severity === 'critical' || a.severity === 'high').length} 条高危告警需要立即处理`,
      severity: 'critical',
      btnText: '查看并处置',
      action: () => router.push('/alerts'),
    })
  }

  if (hasDeauth || hasEvilTwin) {
    items.push({
      icon: '🛡', title: '攻击防御',
      desc: '检测到主动攻击行为，建议将攻击源 MAC 加入黑名单以阻止连接',
      severity: 'high',
      btnText: '管理黑名单',
      action: () => router.push('/blacklist'),
    })
  }

  if (!emailEnabled) {
    items.push({
      icon: '📧', title: '启用邮件通知',
      desc: '邮件推送未启用，配置后可实时接收告警通知',
      severity: 'medium',
      btnText: '配置邮箱',
      action: () => router.push('/email'),
    })
  }

  if (whiteCount === 0) {
    items.push({
      icon: '✅', title: '配置白名单',
      desc: '将可信设备加入白名单可减少误报，提高检测精度',
      severity: 'low',
      btnText: '配置白名单',
      action: () => router.push('/whitelist'),
    })
  }

  // Always show at least 3
  while (items.length < 3) {
    items.push({
      icon: 'ℹ️', title: '系统运行正常',
      desc: '当前没有检测到高危安全威胁，系统持续监控中',
      severity: 'low',
      btnText: '查看概览',
      action: () => router.push('/'),
    })
  }

  return items.slice(0, 3)
})

function getAttackTag(type) {
  const map = { 'Deauth攻击': 'danger', '钓鱼AP': 'danger', '暴力破解': 'warning', '非法接入': 'danger', 'Flood泛洪': 'warning', '弱口令': 'info', '弱加密协议': 'info', 'KRACK风险': 'danger' }
  return map[type] || 'info'
}

function getSeverityType(s) {
  const map = { critical: 'danger', high: 'danger', medium: 'warning', low: 'success' }
  return map[s] || 'info'
}

function getSeverityLabel(s) {
  const map = { critical: '严重', high: '高危', medium: '中危', low: '低危' }
  return map[s] || s
}

function formatRelative(ts) {
  if (!ts) return ''
  try {
    const diff = Date.now() - new Date(ts).getTime()
    const mins = Math.floor(diff / 60000)
    if (mins < 1) return '刚刚'
    if (mins < 60) return mins + '分钟前'
    return Math.floor(mins / 60) + '小时前'
  } catch { return ts }
}

function getDeviceEmoji(dev) {
  const v = (dev.vendor || '').toLowerCase()
  if (v.includes('apple') || v.includes('samsung') || v.includes('huawei') || v.includes('xiaomi')) return '📱'
  if (v.includes('dell') || v.includes('lenovo') || v.includes('hp') || v.includes('intel')) return '🖥'
  if (v.includes('cisco') || v.includes('aruba') || v.includes('tp-link')) return '📡'
  return '💻'
}

function handleClear(id) {
  alertStore.clearAlert(id)
}

// ---- Charts ----
function handleChartClick(params) {
  if (params.name && params.name !== '无告警') {
    router.push({ path: '/alerts', query: { type: params.name } })
  }
}

function initCharts() {
  if (barChartRef.value) {
    barChart = echarts.init(barChartRef.value)
    barChart.on('click', handleChartClick)
  }
  if (pieChartRef.value) {
    pieChart = echarts.init(pieChartRef.value)
    pieChart.on('click', handleChartClick)
  }
  resizeObs = new ResizeObserver(() => { pieChart?.resize(); barChart?.resize() })
  if (pieChartRef.value) resizeObs.observe(pieChartRef.value)
  if (barChartRef.value) resizeObs.observe(barChartRef.value)
  watch(() => alertStore.currentAlerts, refreshCharts, { deep: true })
  refreshCharts()
}

function refreshCharts() { updatePieChart(); updateBarChart() }

function updateBarChart() {
  if (!barChart) return
  const countMap = {}
  for (const a of alertStore.currentAlerts) countMap[a.type] = (countMap[a.type] || 0) + 1
  const types = Object.keys(countMap)
  const values = Object.values(countMap)
  const barColors = ['#f56c6c', '#e6a23c', '#f56c6c', '#f56c6c', '#e6a23c', '#409eff', '#409eff', '#f56c6c']
  barChart.setOption({
    tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
    grid: { left: 0, right: 26, top: 5, bottom: 0, containLabel: true },
    xAxis: { type: 'value', show: false, minInterval: 1 },
    yAxis: { type: 'category', data: types, axisLabel: { fontSize: 11, color: '#909399' }, axisLine: { show: false }, axisTick: { show: false } },
    series: [{ type: 'bar', data: values.map((v, i) => ({ value: v, itemStyle: { color: barColors[i % barColors.length], borderRadius: [0, 4, 4, 0] } })), barWidth: 16, label: { show: true, position: 'right', fontSize: 12, fontWeight: 'bold', color: '#606266' } }],
  }, true)
}

function updatePieChart() {
  if (!pieChart) return
  const countMap = {}
  for (const a of alertStore.currentAlerts) countMap[a.type] = (countMap[a.type] || 0) + 1
  const data = Object.entries(countMap).map(([name, value]) => ({ name, value }))
  const colors = ['#f56c6c', '#e6a23c', '#f56c6c', '#f56c6c', '#e6a23c', '#409eff', '#409eff', '#f56c6c']
  pieChart.setOption({
    tooltip: { trigger: 'item', formatter: '{b}: {c} ({d}%)' },
    series: [{ type: 'pie', radius: ['50%', '78%'], center: ['50%', '50%'], avoidLabelOverlap: false, itemStyle: { borderRadius: 4, borderColor: '#fff', borderWidth: 2 }, label: { show: true, position: 'outside', formatter: '{b}\n{d}%', fontSize: 11 }, emphasis: { label: { fontSize: 16, fontWeight: 'bold' } }, data: data.length > 0 ? data : [{ name: '无告警', value: 1, itemStyle: { color: '#ccc' } }], color: data.length > 0 ? colors : ['#ccc'] }],
  }, true)
}

onMounted(() => {
  alertStore.fetchSystemStatus()
  alertStore.fetchCurrentAlerts()
  alertStore.fetchOnlineDevices()
  alertStore.fetchWhitelist()
  alertStore.fetchBlacklist()
  alertStore.fetchEmailConfig()
  alertStore.fetchHistoryAlerts()
  nextTick(() => initCharts())
})

onUnmounted(() => {
  if (pieChart) pieChart.dispose()
  if (barChart) barChart.dispose()
  if (resizeObs) resizeObs.disconnect()
})
</script>

<style scoped>
.dashboard-container { padding: 16px; }

.view-toggle-bar {
  display: flex; align-items: center; justify-content: flex-end;
  margin-bottom: 14px; padding: 8px 14px;
  background: #fff; border-radius: 8px;
  box-shadow: 0 1px 4px rgba(0,0,0,0.06);
}
.toggle-label { font-size: 13px; color: #606266; margin-right: 10px; font-weight: 500; }

/* Status cards */
.status-cards { margin-bottom: 16px; }

.status-card {
  cursor: pointer;
  transition: all 0.3s;
  border-radius: 10px;
}
.status-card:hover { transform: translateY(-3px); }

.card-top {
  display: flex; align-items: center; gap: 14px;
}

.card-icon-wrap {
  width: 52px; height: 52px;
  border-radius: 12px;
  display: flex; align-items: center; justify-content: center;
  color: #fff;
}
.card-icon-wrap.success { background: linear-gradient(135deg, #67c23a, #85ce61); }
.card-icon-wrap.danger { background: linear-gradient(135deg, #f56c6c, #f89898); }
.card-icon-wrap.info { background: linear-gradient(135deg, #409eff, #79bbff); }
.card-icon-wrap.warning { background: linear-gradient(135deg, #e6a23c, #eebe77); }

.card-info { flex: 1; }
.card-label { font-size: 12px; color: #909399; margin-bottom: 2px; }
.card-value { font-size: 26px; font-weight: bold; color: #303133; }

.card-footer {
  margin-top: 10px; padding-top: 8px;
  border-top: 1px solid #ebeef5;
  font-size: 11px; color: #909399;
}
.danger-text { color: #f56c6c; }

/* Main content */
.main-content { margin-top: 16px; }

.section-card {
  border-radius: 10px;
}

.card-header {
  display: flex; justify-content: space-between; align-items: center;
}

.header-actions { display: flex; align-items: center; gap: 10px; }

.quick-filters .el-button { padding: 5px 10px; }

.mono-text { font-family: monospace; font-size: 12px; color: #409eff; }
.time-text { font-size: 11px; color: #909399; }

/* Suggestions */
.suggestion-card {
  padding: 14px;
  border-radius: 8px;
  border: 1px solid #ebeef5;
  height: 100%;
  display: flex; flex-direction: column; gap: 8px;
  transition: all 0.2s;
}
.suggestion-card:hover { box-shadow: 0 4px 12px rgba(0,0,0,0.08); }
.suggestion-card.sev-critical { border-left: 3px solid #f56c6c; background: #fef0f0; }
.suggestion-card.sev-high { border-left: 3px solid #e6a23c; background: #fef6e8; }
.suggestion-card.sev-medium { border-left: 3px solid #409eff; background: #f0f7ff; }
.suggestion-card.sev-low { border-left: 3px solid #67c23a; background: #f0faf0; }

.sug-header { display: flex; align-items: center; gap: 6px; }
.sug-icon { font-size: 16px; }
.sug-title { font-weight: 600; font-size: 13px; color: #303133; }
.sug-desc { margin: 0; font-size: 12px; color: #606266; line-height: 1.5; flex: 1; }

/* Charts */
.mini-chart { width: 100%; height: 240px; }

/* Device row */
.device-row {
  display: flex; justify-content: space-between; align-items: center;
  padding: 10px 0;
  border-bottom: 1px solid #f2f3f5;
}
.device-row:last-child { border-bottom: none; }
.dev-left { display: flex; align-items: center; gap: 8px; }
.dev-icon { font-size: 18px; }
.dev-mac { font-family: monospace; font-size: 12px; color: #303133; font-weight: 500; }
.dev-sub { font-size: 11px; color: #909399; }
.dev-right { flex-shrink: 0; }
</style>
