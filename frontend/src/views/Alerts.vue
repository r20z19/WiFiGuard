<template>
  <div class="alerts-container">
    <!-- Filter bar -->
    <el-card class="filter-card">
      <div class="filter-bar">
        <div class="filter-left">
          <el-radio-group v-model="severityFilter" size="small" @change="onFilterChange">
            <el-radio-button value="all">全部 ({{ alertStore.currentAlerts.length }})</el-radio-button>
            <el-radio-button value="critical">严重 ({{ counts.critical }})</el-radio-button>
            <el-radio-button value="high">高危 ({{ counts.high }})</el-radio-button>
            <el-radio-button value="medium">中危 ({{ counts.medium }})</el-radio-button>
            <el-radio-button value="low">低危 ({{ counts.low }})</el-radio-button>
          </el-radio-group>
          <el-select v-model="typeFilter" placeholder="攻击类型" size="small" clearable style="width:140px;margin-left:12px" @change="onFilterChange">
            <el-option label="全部类型" value="" />
            <el-option v-for="t in attackTypes" :key="t" :label="t" :value="t" />
          </el-select>
        </div>
        <div class="filter-right">
          <span v-if="selectedRows.length > 0" class="selected-info">已选 {{ selectedRows.length }} 项</span>
          <el-button
            v-if="selectedRows.length > 0"
            type="danger" size="small"
            @click="batchClear"
          >
            批量清除
          </el-button>
          <el-button
            v-if="selectedRows.length > 0"
            type="warning" size="small"
            @click="batchBlacklist"
          >
            批量加黑名单
          </el-button>
          <el-button type="danger" size="small" plain @click="clearAllAlerts" :disabled="alertStore.currentAlerts.length === 0">
            清空全部
          </el-button>
        </div>
      </div>
    </el-card>

    <!-- Aggregated view -->
    <el-card style="margin-top:12px" v-if="groupedAlerts.length > 0">
      <template #header>
        <span>攻击源聚合视图</span>
      </template>
      <div class="aggregate-list">
        <div v-for="grp in groupedAlerts.slice(0, 6)" :key="grp.sourceMac" class="agg-item" @click="filterBySource(grp.sourceMac)">
          <div class="agg-left">
            <span class="agg-mac mono">{{ grp.sourceMac }}</span>
            <div class="agg-types">
              <el-tag v-for="t in grp.types" :key="t" :type="getAttackTag(t)" size="small" class="agg-tag">{{ t }}</el-tag>
            </div>
          </div>
          <div class="agg-right">
            <span class="agg-count">{{ grp.count }} 次攻击</span>
            <el-tag :type="getSeverityType(grp.maxSeverity)" size="small">{{ getSeverityLabel(grp.maxSeverity) }}</el-tag>
          </div>
        </div>
      </div>
    </el-card>

    <!-- Main alert table -->
    <el-card style="margin-top:12px">
      <template #header>
        <div class="card-header">
          <span>告警列表</span>
          <el-button type="primary" size="small" @click="refreshAlerts">
            <el-icon><Refresh /></el-icon>刷新
          </el-button>
        </div>
      </template>

      <el-table
        :data="filteredAlerts"
        style="width: 100%"
        stripe
        @selection-change="onSelectionChange"
        ref="tableRef"
      >
        <el-table-column type="selection" width="40" />
        <el-table-column prop="timestamp" label="告警时间" width="165" sortable />
        <el-table-column prop="type" label="攻击类型" width="130" sortable>
          <template #default="{ row }">
            <el-tag :type="getAttackTag(row.type)" size="small">{{ row.type }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="severity" label="严重等级" width="85" sortable>
          <template #default="{ row }">
            <el-tag :type="getSeverityType(row.severity)" size="small">{{ getSeverityLabel(row.severity) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="sourceMac" label="源MAC地址" width="160" sortable>
          <template #default="{ row }">
            <span class="mono">{{ row.sourceMac }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="targetMac" label="目标MAC地址" width="160">
          <template #default="{ row }">
            <span class="mono">{{ row.targetMac || '-' }}</span>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" link size="small" @click="toggleExpand(row)">建议</el-button>
            <el-button type="warning" link size="small" @click="quickBlacklist(row)">加黑名单</el-button>
            <el-button type="danger" link size="small" @click="handleDelete(row.id)">删除</el-button>
          </template>
        </el-table-column>

        <!-- Expandable row -->
        <template #expanded="scope">
          <div class="expanded-content">
            <el-descriptions :column="2" border size="small">
              <el-descriptions-item label="攻击类型">{{ scope.row.type }}</el-descriptions-item>
              <el-descriptions-item label="严重等级">
                <el-tag :type="getSeverityType(scope.row.severity)" size="small">{{ getSeverityLabel(scope.row.severity) }}</el-tag>
              </el-descriptions-item>
              <el-descriptions-item label="源MAC地址">
                {{ scope.row.sourceMac }}
                <span v-if="findDevice(scope.row.sourceMac)" class="device-hint">
                  ({{ findDevice(scope.row.sourceMac).vendor || '未知厂商' }})
                </span>
              </el-descriptions-item>
              <el-descriptions-item label="目标MAC地址">
                {{ scope.row.targetMac || '-' }}
                <span v-if="scope.row.targetMac && findDevice(scope.row.targetMac)" class="device-hint">
                  ({{ findDevice(scope.row.targetMac).vendor || '未知厂商' }})
                </span>
              </el-descriptions-item>
              <el-descriptions-item label="告警时间">{{ scope.row.timestamp }}</el-descriptions-item>
            </el-descriptions>
            <el-alert
              title="安全建议"
              type="info"
              :closable="false"
              show-icon
              style="margin-top:12px"
            >
              <p style="margin:0;line-height:1.6">{{ scope.row.suggestion }}</p>
            </el-alert>
            <div class="expanded-actions">
              <el-button type="danger" size="small" @click="oneClickDispose(scope.row)">⚡ 一键处置(拉黑+清除)</el-button>
              <el-button size="small" @click="quickBlacklist(scope.row)">加黑名单</el-button>
              <el-button size="small" @click="handleDelete(scope.row.id)">忽略</el-button>
            </div>
          </div>
        </template>
      </el-table>

      <el-empty v-if="filteredAlerts.length === 0" description="当前无告警信息，系统运行正常" :image-size="80" />
    </el-card>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { useAlertStore } from '../store/alert'
import { ElMessage, ElMessageBox } from 'element-plus'

const route = useRoute()
const alertStore = useAlertStore()
const severityFilter = ref('all')
const typeFilter = ref('')
const selectedRows = ref([])
const tableRef = ref(null)
const expands = ref([])

const attackTypes = ['Deauth攻击', '钓鱼AP', '暴力破解', '非法接入', 'Flood泛洪', '弱口令', '弱加密协议', 'KRACK风险']

const counts = computed(() => ({
  critical: alertStore.currentAlerts.filter(a => a.severity === 'critical').length,
  high: alertStore.currentAlerts.filter(a => a.severity === 'high').length,
  medium: alertStore.currentAlerts.filter(a => a.severity === 'medium').length,
  low: alertStore.currentAlerts.filter(a => a.severity === 'low').length,
}))

const filteredAlerts = computed(() => {
  let list = [...alertStore.currentAlerts]
  if (severityFilter.value !== 'all') {
    list = list.filter(a => a.severity === severityFilter.value)
  }
  if (typeFilter.value) {
    list = list.filter(a => a.type === typeFilter.value)
  }
  return list
})

// Group alerts by source MAC
const groupedAlerts = computed(() => {
  const map = new Map()
  for (const a of alertStore.currentAlerts) {
    if (!map.has(a.sourceMac)) {
      map.set(a.sourceMac, { sourceMac: a.sourceMac, types: new Set(), count: 0, maxSeverity: a.severity })
    }
    const g = map.get(a.sourceMac)
    g.types.add(a.type)
    g.count++
    if (severityWeight(a.severity) > severityWeight(g.maxSeverity)) g.maxSeverity = a.severity
  }
  return [...map.values()]
    .map(g => ({ ...g, types: [...g.types] }))
    .sort((a, b) => b.count - a.count)
})

function severityWeight(s) {
  const w = { critical: 4, high: 3, medium: 2, low: 1 }
  return w[s] || 0
}

function getAttackTag(t) {
  const map = { 'Deauth攻击': 'danger', '钓鱼AP': 'danger', '暴力破解': 'warning', '非法接入': 'danger', 'Flood泛洪': 'warning', '弱口令': 'info', '弱加密协议': 'info', 'KRACK风险': 'danger' }
  return map[t] || 'info'
}

function getSeverityType(s) {
  const map = { critical: 'danger', high: 'danger', medium: 'warning', low: 'success' }
  return map[s] || 'info'
}

function getSeverityLabel(s) {
  const map = { critical: '严重', high: '高危', medium: '中危', low: '低危' }
  return map[s] || s
}

function onFilterChange() {
  selectedRows.value = []
}

function findDevice(mac) {
  return alertStore.onlineDevices.find(d => d.mac === mac) || null
}

function filterBySource(mac) {
  typeFilter.value = ''
  // Find which types this source triggers and select the first or just filter differently
  // We can't filter by MAC directly, but we can show the user
  ElMessage.info(`过滤源 MAC: ${mac}（请查看下方列表）`)
}

function onSelectionChange(rows) {
  selectedRows.value = rows
}

function toggleExpand(row) {
  if (tableRef.value) {
    tableRef.value.toggleRowExpansion(row)
  }
}

const handleDelete = (id) => {
  ElMessageBox.confirm('确认删除此告警？', '提示', {
    confirmButtonText: '确认', cancelButtonText: '取消', type: 'warning'
  }).then(async () => {
    await alertStore.clearAlert(id)
    ElMessage.success('告警已删除')
    selectedRows.value = []
  }).catch(() => {})
}

const batchClear = () => {
  ElMessageBox.confirm(`确认清除选中的 ${selectedRows.value.length} 条告警？`, '批量操作', {
    confirmButtonText: '确认', cancelButtonText: '取消', type: 'warning'
  }).then(async () => {
    for (const row of selectedRows.value) {
      await alertStore.clearAlert(row.id)
    }
    ElMessage.success(`已清除 ${selectedRows.value.length} 条告警`)
    selectedRows.value = []
  }).catch(() => {})
}

const clearAllAlerts = () => {
  ElMessageBox.confirm('确认清空所有告警？', '警告', {
    confirmButtonText: '确认', cancelButtonText: '取消', type: 'warning'
  }).then(async () => {
    const all = [...alertStore.currentAlerts]
    for (const alert of all) {
      await alertStore.clearAlert(alert.id)
    }
    ElMessage.success('所有告警已清空')
  }).catch(() => {})
}

const oneClickDispose = async (row) => {
  if (alertStore.accessListMode !== 'blacklist') {
    ElMessage.warning('请先在黑名单页面开启黑名单模式')
    return
  }
  try {
    await alertStore.addToBlacklist({ mac: row.sourceMac, name: `攻击设备-${row.sourceMac?.slice(-4) || ''}`, reason: `一键处置: ${row.type}` })
    await alertStore.clearAlert(row.id)
    ElMessage.success(`已拉黑 ${row.sourceMac} 并清除告警`)
  } catch (e) { ElMessage.error('处置失败') }
}

const quickBlacklist = async (row) => {
  if (alertStore.accessListMode !== 'blacklist') {
    ElMessage.warning('请先在黑名单页面开启黑名单模式')
    return
  }
  try {
    await alertStore.addToBlacklist({
      mac: row.sourceMac,
      name: `攻击设备-${row.sourceMac?.slice(-4) || 'unknown'}`,
      reason: `检测到${row.type}攻击`
    })
    ElMessage.warning(`已将 ${row.sourceMac} 加入黑名单`)
    alertStore.fetchBlacklist()
  } catch (e) {
    ElMessage.error(e.message || '加入黑名单失败')
  }
}

const batchBlacklist = async () => {
  ElMessageBox.confirm(`将选中的 ${selectedRows.value.length} 个攻击源 MAC 加入黑名单？`, '批量操作', {
    confirmButtonText: '确认', cancelButtonText: '取消', type: 'warning'
  }).then(async () => {
    let count = 0
    const seen = new Set()
    for (const row of selectedRows.value) {
      if (seen.has(row.sourceMac)) continue
      seen.add(row.sourceMac)
      try {
        await alertStore.addToBlacklist({
          mac: row.sourceMac,
          name: `攻击设备-${row.sourceMac?.slice(-4) || 'unknown'}`,
          reason: `批量添加: ${row.type}`
        })
        count++
      } catch {}
    }
    ElMessage.warning(`已将 ${count} 个设备加入黑名单`)
    selectedRows.value = []
  }).catch(() => {})
}

const refreshAlerts = () => {
  alertStore.fetchCurrentAlerts()
  ElMessage.success('已刷新')
}

onMounted(() => {
  if (route.query.type) typeFilter.value = route.query.type
  alertStore.fetchCurrentAlerts()
  alertStore.fetchBlacklist()
  alertStore.fetchOnlineDevices()
})
</script>

<style scoped>
.alerts-container { padding: 16px; }

.filter-card { border-radius: 10px; }
.filter-card :deep(.el-card__body) { padding: 12px 16px; }

.filter-bar {
  display: flex; justify-content: space-between; align-items: center;
  flex-wrap: wrap; gap: 10px;
}

.filter-left { display: flex; align-items: center; flex-wrap: wrap; gap: 8px; }
.filter-right { display: flex; align-items: center; gap: 8px; }
.selected-info { font-size: 13px; color: #f56c6c; font-weight: 500; }

.card-header { display: flex; justify-content: space-between; align-items: center; }
.mono { font-family: monospace; font-size: 12px; color: #409eff; }

/* Aggregate view */
.aggregate-list { display: flex; flex-wrap: wrap; gap: 8px; }

.agg-item {
  display: flex; align-items: center; justify-content: space-between; gap: 12px;
  padding: 10px 14px;
  border: 1px solid #ebeef5; border-radius: 8px;
  cursor: pointer; transition: all 0.2s;
  min-width: 260px; flex: 1;
}
.agg-item:hover { border-color: #409eff; background: #f0f7ff; }

.agg-left { display: flex; align-items: center; gap: 8px; }
.agg-mac { font-size: 12px; color: #303133; font-weight: 500; }
.agg-types { display: flex; gap: 4px; flex-wrap: wrap; }
.agg-tag { font-size: 11px; }

.agg-right { display: flex; align-items: center; gap: 8px; flex-shrink: 0; }
.agg-count { font-size: 12px; color: #909399; white-space: nowrap; }

/* Expanded row */
.expanded-content { padding: 12px 40px; }
.expanded-actions { margin-top: 12px; display: flex; gap: 8px; }
.device-hint { font-size: 12px; color: #67c23a; margin-left: 4px; }
</style>
