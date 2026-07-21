<template>
  <div class="report-container">
    <div class="report-header">
      <h2>📊 安全报告</h2>
      <div class="header-actions">
        <span class="report-time">{{ reportTime }}</span>
        <el-button type="warning" @click="generateReport" :loading="aiReportLoading">🤖 AI 生成报告</el-button>
        <el-button type="primary" @click="exportPDF">📄 导出报告</el-button>
        <el-button @click="refreshAll">🔄 刷新数据</el-button>
      </div>
    </div>

    <!-- Security score -->
    <el-row :gutter="16" class="score-row">
      <el-col :span="8">
        <el-card shadow="hover">
          <div class="score-card">
            <el-progress type="circle" :percentage="securityScore" :width="120" :stroke-width="8" :color="scoreColor">
              <template #default="{ percentage }">
                <span class="score-num">{{ percentage }}</span>
                <span class="score-unit">分</span>
              </template>
            </el-progress>
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

    <!-- AI Generated Report -->
    <el-card v-if="aiReport" shadow="hover" style="margin-top:16px;border-left:4px solid #e6a23c">
      <template #header>
        <div style="display:flex;justify-content:space-between;align-items:center">
          <span>🤖 AI 安全分析报告</span>
          <el-button size="small" text @click="aiReport = ''">清除</el-button>
        </div>
      </template>
      <div class="ai-report-text">{{ aiReport }}</div>
    </el-card>

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

    <!-- AI Anomaly & Prediction -->
    <el-row :gutter="16" style="margin-top:16px">
      <el-col :span="12">
        <el-card shadow="hover">
          <template #header>
            <div style="display:flex;justify-content:space-between;align-items:center">
              <span>🔍 AI 异常行为检测</span>
              <el-button type="warning" size="small" @click="runAnomalyScan" :loading="anomalyLoading">执行扫描</el-button>
            </div>
          </template>
          <div v-if="anomalies.length > 0">
            <div v-for="a in anomalies" :key="a.device" class="anomaly-item" :class="'risk-'+a.risk">
              <div class="anom-header">
                <span class="anom-risk" :class="a.risk">{{ riskLabel(a.risk) }}</span>
                <span class="anom-mac mono">{{ a.device?.slice(-12) }}</span>
                <span class="anom-issue">{{ a.issue }}</span>
              </div>
              <div v-if="a.reason" class="anom-reason">📝 {{ a.reason }}</div>
              <div v-if="a.advice" class="anom-advice">💡 {{ a.advice }}</div>
            </div>
          </div>
          <el-empty v-else-if="anomalyScanned" description="未发现异常行为 ✅" :image-size="60" />
          <div v-else class="scan-placeholder">点击"执行扫描"开始 AI 异常行为分析</div>
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card shadow="hover">
          <template #header>
            <div style="display:flex;justify-content:space-between;align-items:center">
              <span>🔮 AI 攻击预测</span>
              <el-button type="warning" size="small" @click="runPrediction" :loading="predictLoading">生成预测</el-button>
            </div>
          </template>
          <div v-if="prediction">
            <template v-if="typeof prediction === 'object' && prediction.riskLevel">
              <div class="predict-card">
                <div class="predict-level" :class="prediction.riskLevel">
                  <span class="level-icon">{{ prediction.riskLevel === 'high' ? '🔴' : prediction.riskLevel === 'medium' ? '🟡' : '🟢' }}</span>
                  <span class="level-text">{{ prediction.riskLevel === 'high' ? '高风险' : prediction.riskLevel === 'medium' ? '中风险' : '低风险' }}</span>
                </div>
                <div class="predict-summary">{{ prediction.summary }}</div>
                <div v-if="prediction.reason" class="predict-reason">{{ prediction.reason }}</div>
              </div>
              <div v-if="prediction.predictions && prediction.predictions.length > 0" class="predict-list">
                <div class="predict-list-title">📋 具体威胁预测</div>
                <div v-for="(p, i) in prediction.predictions" :key="i" class="predict-item">
                  <div class="pred-header">
                    <span class="pred-prob" :class="p.probability">{{ p.probability === '高' ? '🔴' : p.probability === '中' ? '🟡' : '🟢' }} {{ p.probability }}概率</span>
                    <span class="pred-threat">{{ p.threat }}</span>
                  </div>
                  <div class="pred-meta">
                    <span v-if="p.target && p.target !== '整体网络'" class="pred-target">🎯 {{ p.target }}</span>
                  </div>
                  <div v-if="p.reason" class="pred-reason">{{ p.reason }}</div>
                  <div v-if="p.advice" class="pred-advice">💡 {{ p.advice }}</div>
                </div>
              </div>
            </template>
            <div v-else class="predict-reason">{{ prediction }}</div>
          </div>
          <el-empty v-else-if="predScanned" description="暂无预测威胁 ✅" :image-size="60" />
          <div v-else class="scan-placeholder">点击"生成预测"获取 AI 威胁预测</div>
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
import { generateAiReport, detectAnomalies, predictThreats } from '../api'
import { ElMessage } from 'element-plus'
import * as echarts from 'echarts'

const alertStore = useAlertStore()
const aiReport = ref('')
const aiReportLoading = ref(false)
const anomalies = ref([])
const anomalyLoading = ref(false)
const anomalyScanned = ref(false)
const prediction = ref(null)
const predictLoading = ref(false)
const predScanned = ref(false)

function riskLabel(r) { return r === 'high' ? '🔴 高' : r === 'medium' ? '🟡 中' : '🟢 低' }
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
  const a = (alerts.value || []).length
  const critical = (alerts.value || []).filter(a => a.severity === 'critical' || a.severity === 'high').length
  const suspicious = (devices.value || []).filter(d => d.status !== '正常').length
  const score = 100 - a * 5 - critical * 15 - suspicious * 3
  return isNaN(score) ? 100 : Math.max(0, Math.min(100, Math.round(score)))
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

async function generateReport() {
  aiReportLoading.value = true
  try {
    const summary = {
      alerts: alerts.value.map(a => ({ type: a.type, severity: a.severity, sourceMac: a.sourceMac, targetMac: a.targetMac })),
      alertCount: alerts.value.length,
      criticalCount: alerts.value.filter(a => a.severity === 'critical' || a.severity === 'high').length,
      deviceCount: devices.value.length,
      suspiciousCount: devices.value.filter(d => d.status !== '正常').length,
      whitelistCount: whitelistCount.value,
      blacklistCount: blacklistCount.value,
      securityScore: securityScore.value,
    }
    const resp = await generateAiReport({ summary })
    aiReport.value = resp.result
  } catch (e) { ElMessage.error('AI 报告生成失败，请检查 API Key') }
  aiReportLoading.value = false
}

async function runAnomalyScan() {
  anomalyLoading.value = true
  try {
    // Build attack context per device
    const deviceAttackMap = {}
    for (const a of alerts.value) {
      if (a.sourceMac) {
        if (!deviceAttackMap[a.sourceMac]) deviceAttackMap[a.sourceMac] = { asSource: [], asTarget: [] }
        deviceAttackMap[a.sourceMac].asSource.push(a.type)
      }
      if (a.targetMac) {
        if (!deviceAttackMap[a.targetMac]) deviceAttackMap[a.targetMac] = { asSource: [], asTarget: [] }
        deviceAttackMap[a.targetMac].asTarget.push(a.type)
      }
    }
    const resp = await detectAnomalies({ devices: devices.value.map(d => {
      const atkInfo = deviceAttackMap[d.mac]
      return {
        mac: d.mac, vendor: d.vendor, ssid: d.ssid, signal: d.signal,
        status: d.status, firstSeen: d.firstSeen, lastSeen: d.lastSeen,
        attackRole: atkInfo
          ? (atkInfo.asSource.length > 0 ? '攻击源(' + atkInfo.asSource.join(',') + ') ' : '')
            + (atkInfo.asTarget.length > 0 ? '被攻击目标(' + atkInfo.asTarget.join(',') + ')' : '')
          : '无攻击关联',
        attackCount: atkInfo ? atkInfo.asSource.length + atkInfo.asTarget.length : 0,
      }
    })})
    anomalies.value = Array.isArray(resp.result) ? resp.result : []
    anomalyScanned.value = true
  } catch (e) { ElMessage.error('异常检测失败：' + (e.message || '请先配置 AI 功能')) }
  anomalyLoading.value = false
}

async function runPrediction() {
  predictLoading.value = true
  try {
    const resp = await predictThreats({ current: {
      alertCount: alerts.value.length,
      alertTypes: [...new Set(alerts.value.map(a => a.type))],
      criticalCount: alerts.value.filter(a => a.severity === 'critical').length,
      highCount: alerts.value.filter(a => a.severity === 'high').length,
      deviceCount: devices.value.length,
      suspiciousCount: devices.value.filter(d => d.status !== '正常').length,
      alerts: alerts.value.slice(0, 20).map(a => ({
        type: a.type, severity: a.severity, sourceMac: a.sourceMac, targetMac: a.targetMac, timestamp: a.timestamp,
      })),
    }})
    let raw = resp.result
    if (typeof raw === 'string') { try { raw = JSON.parse(raw) } catch {} }
    prediction.value = raw
    predScanned.value = true
  } catch (e) { ElMessage.error('预测失败：' + (e.message || '请先配置 AI 功能')) }
  predictLoading.value = false
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
.score-num { font-size: 36px; font-weight: 700; color: #303133; display: block; }
.score-unit { font-size: 12px; color: #909399; }

.stat-card { text-align: center; padding: 8px; }
.stat-card.stat-danger { border-top: 3px solid #f56c6c; }
.stat-card.stat-ok { border-top: 3px solid #67c23a; }
.stat-card.stat-blue { border-top: 3px solid #409eff; }
.stat-card.stat-green { border-top: 3px solid #67c23a; }
.stat-card.stat-orange { border-top: 3px solid #e6a23c; }

.stat-num { font-size: 32px; font-weight: 700; color: #303133; }
.stat-lbl { font-size: 12px; color: #909399; margin-top: 4px; }

.mono { font-family: monospace; font-size: 12px; color: #409eff; }
.ai-report-text { font-size: 14px; color: #303133; line-height: 2; white-space: pre-wrap; }

.anomaly-item { padding: 10px 0; border-bottom: 1px solid #f5f5f5; font-size: 13px; }
.anomaly-item:last-child { border: none; }
.anom-header { display: flex; align-items: center; gap: 10px; }
.anom-risk { padding: 2px 6px; border-radius: 4px; font-size: 11px; font-weight: 600; flex-shrink: 0; }
.anom-risk.high { background: #fef0f0; color: #f56c6c; }
.anom-risk.medium { background: #fef6e8; color: #e6a23c; }
.anom-risk.low { background: #f0f9eb; color: #67c23a; }
.anom-mac { font-size: 11px; color: #409eff; flex-shrink: 0; }
.anom-issue { flex: 1; color: #303133; font-weight: 500; }
.anom-reason { margin-top: 4px; margin-left: 60px; font-size: 12px; color: #909399; line-height: 1.6; }
.anom-advice { margin-top: 2px; margin-left: 60px; font-size: 12px; color: #409eff; }

.predict-card { padding: 12px; border-radius: 10px; margin-bottom: 12px; }
.predict-card:has(.high) { background: linear-gradient(135deg, #fef0f0, #fff5f5); border: 1px solid #fbc4c4; }
.predict-card:has(.medium) { background: linear-gradient(135deg, #fef6e8, #fffaf0); border: 1px solid #f5dab0; }
.predict-card:has(.low) { background: linear-gradient(135deg, #f0f9eb, #f5faf0); border: 1px solid #c0e0b0; }

.predict-level { display: flex; align-items: center; gap: 8px; margin-bottom: 8px; }
.level-icon { font-size: 28px; }
.level-text { font-size: 20px; font-weight: 700; }
.predict-level.high .level-text { color: #d03030; }
.predict-level.medium .level-text { color: #d08000; }
.predict-level.low .level-text { color: #389e38; }

.predict-summary { font-size: 14px; color: #303133; font-weight: 500; margin-bottom: 6px; }
.predict-reason { font-size: 13px; color: #606266; line-height: 1.8; }

.predict-list { margin-top: 12px; }
.predict-list-title { font-size: 13px; font-weight: 600; color: #606266; margin-bottom: 8px; padding-bottom: 6px; border-bottom: 1px solid #eee; }

.predict-item { padding: 10px 0; border-bottom: 1px solid #f5f5f5; }
.predict-item:last-child { border: none; }
.pred-header { display: flex; align-items: center; gap: 10px; margin-bottom: 4px; }
.pred-prob { font-size: 12px; color: #606266; font-weight: 500; flex-shrink: 0; }
.pred-prob.高 { color: #d03030; }
.pred-prob.中 { color: #d08000; }
.pred-prob.低 { color: #389e38; }
.pred-threat { font-size: 14px; font-weight: 600; color: #303133; }
.pred-meta { margin-bottom: 4px; }
.pred-target { font-size: 12px; color: #409eff; font-family: monospace; }
.pred-reason { font-size: 12px; color: #909399; line-height: 1.6; margin-bottom: 2px; }
.pred-advice { font-size: 13px; color: #409eff; line-height: 1.6; }
.scan-placeholder { padding: 40px 20px; text-align: center; color: #c0c4cc; font-size: 14px; }
</style>
