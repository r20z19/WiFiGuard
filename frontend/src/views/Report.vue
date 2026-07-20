<template>
  <div class="report-container">
    <div class="report-header">
      <h2>📊 安全报告</h2>
      <div class="header-actions">
        <span class="report-time">{{ reportTime }}</span>
        <el-button type="primary" @click="exportPDF">📄 导出报告</el-button>
        <el-button @click="refreshAll">🔄 刷新数据</el-button>
      </div>
    </div>

    <!-- Security score -->
    <el-row :gutter="16" class="score-row">
      <el-col :span="8">
        <el-card shadow="hover">
          <div class="score-card">
            <el-progress type="circle" :percentage="securityScore" :width="120" :color="scoreColor" />
            <div class="score-info">
              <div class="score-label">综合安全评分</div>
              <div class="score-desc">{{ scoreDesc }}</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="16">
        <el-card shadow="hover">
          <template #header><span>本周安全趋势</span></template>
          <div ref="trendChartRef" style="height:160px"></div>
        </el-card>
      </el-col>
    </el-row>

    <!-- Stats grid -->
    <el-row :gutter="16" style="margin-top:16px">
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card" :class="alerts.length > 0 ? 'stat-danger' : 'stat-ok'">
          <div class="stat-num">{{ alerts.length }}</div>
          <div class="stat-lbl">活跃告警</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card stat-blue">
          <div class="stat-num">{{ devices.length }}</div>
          <div class="stat-lbl">在线设备</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card stat-green">
          <div class="stat-num">{{ whitelistCount }}</div>
          <div class="stat-lbl">受信任设备</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card stat-orange">
          <div class="stat-num">{{ blacklistCount }}</div>
          <div class="stat-lbl">已拉黑设备</div>
        </el-card>
      </el-col>
    </el-row>

    <!-- Attack breakdown -->
    <el-row :gutter="16" style="margin-top:16px">
      <el-col :span="12">
        <el-card shadow="hover">
          <template #header><span>攻击类型分布</span></template>
          <div ref="typeChartRef" style="height:280px"></div>
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card shadow="hover">
          <template #header><span>🔴 高危设备列表</span></template>
          <el-table :data="highRiskDevices" size="small" max-height="280">
            <el-table-column label="设备" width="50">
              <template #default="{ row }"><span style="font-size:18px">{{ row.icon }}</span></template>
            </el-table-column>
            <el-table-column prop="mac" label="MAC" width="140">
              <template #default="{ row }"><span class="mono">{{ row.mac?.slice(-12) }}</span></template>
            </el-table-column>
            <el-table-column label="风险" width="70">
              <template #default="{ row }">
                <el-tag :type="row.score >= 70 ? 'danger' : 'warning'" size="small">{{ row.score }}分</el-tag>
              </template>
            </el-table-column>
            <el-table-column label="原因" min-width="120">
              <template #default="{ row }">{{ row.reason }}</template>
            </el-table-column>
          </el-table>
          <el-empty v-if="highRiskDevices.length === 0" description="无高危设备 🎉" :image-size="60" />
        </el-card>
      </el-col>
    </el-row>

    <!-- Recent alerts -->
    <el-card shadow="hover" style="margin-top:16px">
      <template #header><span>最近攻击事件</span></template>
      <el-table :data="alerts.slice(0, 10)" size="small">
        <el-table-column prop="timestamp" label="时间" width="160" />
        <el-table-column prop="type" label="攻击类型" width="120">
          <template #default="{ row }"><el-tag :type="attackTag(row.type)" size="small">{{ row.type }}</el-tag></template>
        </el-table-column>
        <el-table-column prop="severity" label="等级" width="70">
          <template #default="{ row }"><el-tag :type="sevType(row.severity)" size="small">{{ sevLabel(row.severity) }}</el-tag></template>
        </el-table-column>
        <el-table-column prop="sourceMac" label="攻击源" width="150">
          <template #default="{ row }"><span class="mono">{{ row.sourceMac }}</span></template>
        </el-table-column>
        <el-table-column prop="targetMac" label="目标" width="150">
          <template #default="{ row }"><span class="mono">{{ row.targetMac || '-' }}</span></template>
        </el-table-column>
      </el-table>
      <el-empty v-if="alerts.length === 0" description="无攻击事件" :image-size="60" />
    </el-card>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, nextTick } from 'vue'
import { useAlertStore } from '../store/alert'
import * as echarts from 'echarts'

const alertStore = useAlertStore()
const trendChartRef = ref(null)
const typeChartRef = ref(null)
let trendChart = null
let typeChart = null

const alerts = computed(() => alertStore.currentAlerts)
const devices = computed(() => alertStore.onlineDevices)
const whitelistCount = computed(() => alertStore.whitelist.length)
const blacklistCount = computed(() => alertStore.blacklist.length)
const reportTime = computed(() => new Date().toLocaleString('zh-CN'))

const securityScore = computed(() => {
  const a = alerts.value.length
  const critical = alerts.value.filter(a => a.severity === 'critical' || a.severity === 'high').length
  const suspicious = devices.value.filter(d => d.status !== '正常').length
  let score = 100 - a * 5 - critical * 15 - suspicious * 3
  return Math.max(0, Math.min(100, Math.round(score)))
})

const scoreColor = computed(() => securityScore.value >= 80 ? '#67c23a' : securityScore.value >= 50 ? '#e6a23c' : '#f56c6c')
const scoreDesc = computed(() => securityScore.value >= 80 ? '网络安全状况良好' : securityScore.value >= 50 ? '存在一定安全风险' : '需要立即处理安全问题')

const highRiskDevices = computed(() => {
  return devices.value
    .filter(d => d.status === '可疑' || (d.signal || -70) < -75)
    .map(d => ({
      ...d,
      icon: getIcon(d),
      score: calcScore(d),
      reason: d.status === '可疑' ? '设备状态异常' : (d.signal || -70) < -75 ? '信号极弱，可能远距离攻击' : '未知',
    }))
    .sort((a, b) => b.score - a.score)
    .slice(0, 8)
})

function getIcon(d) {
  const v = (d.vendor || '').toLowerCase()
  if (v.includes('apple') || v.includes('samsung')) return '📱'
  if (v.includes('dell') || v.includes('lenovo') || v.includes('hp')) return '🖥'
  return '💻'
}
function calcScore(d) { return d.status !== '正常' ? 75 : (d.signal || -70) < -75 ? 55 : 30 }

function attackTag(t) {
  const m = { 'Deauth攻击': 'danger', '钓鱼AP': 'danger', '暴力破解': 'warning', '非法接入': 'danger', 'Flood泛洪': 'warning' }
  return m[t] || 'info'
}
function sevType(s) { return { critical: 'danger', high: 'danger', medium: 'warning', low: 'success' }[s] || 'info' }
function sevLabel(s) { return { critical: '严重', high: '高危', medium: '中危', low: '低危' }[s] || s }

function initCharts() {
  if (trendChartRef.value) {
    trendChart = echarts.init(trendChartRef.value)
    trendChart.setOption({
      grid: { left: 0, right: 10, top: 10, bottom: 0, containLabel: true },
      xAxis: { type: 'category', data: ['周一', '周二', '周三', '周四', '周五', '周六', '周日'], axisLabel: { fontSize: 11 } },
      yAxis: { type: 'value', minInterval: 1, show: false },
      series: [{
        type: 'line', data: [0, 0, 0, 0, 0, 0, alerts.value.length],
        smooth: true, symbol: 'circle', symbolSize: 6,
        areaStyle: { color: 'rgba(245,108,108,0.1)' },
        lineStyle: { color: '#f56c6c', width: 2 },
        itemStyle: { color: '#f56c6c' },
      }],
    }, true)
  }
  if (typeChartRef.value) {
    typeChart = echarts.init(typeChartRef.value)
    const m = {}
    for (const a of alerts.value) m[a.type] = (m[a.type] || 0) + 1
    const d = Object.entries(m).map(([n, v]) => ({ name: n, value: v }))
    typeChart.setOption({
      tooltip: { trigger: 'item' },
      series: [{ type: 'pie', radius: ['45%', '75%'], center: ['50%', '50%'], data: d.length ? d : [{ name: '无', value: 1, itemStyle: { color: '#ccc' } }], label: { fontSize: 11 } }],
    }, true)
  }
}

function exportPDF() { window.print() }

async function refreshAll() {
  await Promise.all([
    alertStore.fetchSystemStatus(), alertStore.fetchCurrentAlerts(),
    alertStore.fetchOnlineDevices(), alertStore.fetchWhitelist(), alertStore.fetchBlacklist(),
  ])
  initCharts()
}

onMounted(async () => {
  await refreshAll()
  nextTick(() => initCharts())
})
</script>

<style scoped>
.report-container { padding: 16px; }
.report-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
.report-header h2 { margin: 0; font-size: 22px; color: #303133; }
.header-actions { display: flex; align-items: center; gap: 12px; }
.report-time { font-size: 13px; color: #909399; }

.score-row { margin-bottom: 0; }
.score-card { display: flex; align-items: center; gap: 24px; padding: 16px; }
.score-info { flex: 1; }
.score-label { font-size: 18px; font-weight: 700; color: #303133; margin-bottom: 6px; }
.score-desc { font-size: 13px; color: #909399; }

.stat-card { text-align: center; padding: 8px; }
.stat-card.stat-danger { border-top: 3px solid #f56c6c; }
.stat-card.stat-ok { border-top: 3px solid #67c23a; }
.stat-card.stat-blue { border-top: 3px solid #409eff; }
.stat-card.stat-green { border-top: 3px solid #67c23a; }
.stat-card.stat-orange { border-top: 3px solid #e6a23c; }

.stat-num { font-size: 32px; font-weight: 700; color: #303133; }
.stat-lbl { font-size: 12px; color: #909399; margin-top: 4px; }

.mono { font-family: monospace; font-size: 12px; color: #409eff; }
</style>
