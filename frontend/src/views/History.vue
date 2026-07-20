<template>
  <div class="history-container">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>历史告警记录</span>
          <div class="header-actions">
            <el-button-group size="small" style="margin-right:10px">
              <el-button :type="dateQuick === 'today' ? 'primary' : ''" @click="setDateQuick('today')">今天</el-button>
              <el-button :type="dateQuick === 'week' ? 'primary' : ''" @click="setDateQuick('week')">本周</el-button>
              <el-button :type="dateQuick === 'month' ? 'primary' : ''" @click="setDateQuick('month')">本月</el-button>
            </el-button-group>
            <el-date-picker
              v-model="dateRange"
              type="daterange"
              range-separator="至"
              start-placeholder="开始日期"
              end-placeholder="结束日期"
              size="small"
              style="margin-right: 10px;"
            />
            <el-select v-model="filterType" placeholder="攻击类型" size="small" clearable style="margin-right: 10px; width: 140px;">
              <el-option label="全部" value="" />
              <el-option label="Deauth攻击" value="Deauth攻击" />
              <el-option label="钓鱼AP" value="钓鱼AP" />
              <el-option label="暴力破解" value="暴力破解" />
              <el-option label="非法接入" value="非法接入" />
              <el-option label="Flood泛洪" value="Flood泛洪" />
              <el-option label="弱口令" value="弱口令" />
              <el-option label="弱加密协议" value="弱加密协议" />
              <el-option label="KRACK风险" value="KRACK风险" />
            </el-select>
            <el-select v-model="filterStatus" placeholder="状态" size="small" clearable style="width: 120px;">
              <el-option label="全部" value="" />
              <el-option label="已删除" value="已删除" />
              <el-option label="已忽略" value="已忽略" />
            </el-select>
          </div>
        </div>
      </template>

      <!-- Quick stats -->
      <el-row :gutter="12" style="margin-bottom:12px">
        <el-col :span="4"><div class="stat-mini">总计 <b>{{ filteredAlerts.length }}</b></div></el-col>
        <el-col :span="4"><div class="stat-mini red">严重 <b>{{ filteredAlerts.filter(a=>a.severity==='critical').length }}</b></div></el-col>
        <el-col :span="4"><div class="stat-mini orange">高危 <b>{{ filteredAlerts.filter(a=>a.severity==='high').length }}</b></div></el-col>
        <el-col :span="4"><div class="stat-mini yellow">中危 <b>{{ filteredAlerts.filter(a=>a.severity==='medium').length }}</b></div></el-col>
        <el-col :span="4"><div class="stat-mini">低危 <b>{{ filteredAlerts.filter(a=>a.severity==='low').length }}</b></div></el-col>
        <el-col :span="4" style="text-align:right">
          <el-button size="small" @click="exportCSV">📥 导出CSV</el-button>
        </el-col>
      </el-row>

      <el-table :data="filteredAlerts" style="width: 100%" stripe>
        <el-table-column prop="timestamp" label="告警时间" width="180" />
        <el-table-column prop="type" label="攻击类型" width="140">
          <template #default="{ row }">
            <el-tag :type="getAttackTypeColor(row.type)">{{ row.type }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="severity" label="严重等级" width="100">
          <template #default="{ row }">
            <el-tag :type="getSeverityType(row.severity)" size="small">
              {{ getSeverityLabel(row.severity) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="sourceMac" label="源MAC地址" width="180" />
        <el-table-column prop="targetMac" label="目标MAC地址" width="180" />
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.status === '已删除' ? 'danger' : 'info'" size="small">
              {{ row.status }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="100" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" link @click="showDetail(row)">详情</el-button>
          </template>
        </el-table-column>
      </el-table>

      <el-pagination
        v-if="filteredAlerts.length > 0"
        style="margin-top: 20px; justify-content: flex-end;"
        :current-page="currentPage"
        :page-size="pageSize"
        :total="filteredAlerts.length"
        layout="total, prev, pager, next"
        @current-change="handlePageChange"
      />

      <el-empty v-if="filteredAlerts.length === 0" description="暂无历史告警记录" />
    </el-card>

    <el-dialog v-model="detailVisible" title="告警详情" width="600px">
      <el-descriptions v-if="selectedAlert" :column="1" border>
        <el-descriptions-item label="告警时间">{{ selectedAlert.timestamp }}</el-descriptions-item>
        <el-descriptions-item label="攻击类型">{{ selectedAlert.type }}</el-descriptions-item>
        <el-descriptions-item label="严重等级">{{ getSeverityLabel(selectedAlert.severity) }}</el-descriptions-item>
        <el-descriptions-item label="源MAC地址">{{ selectedAlert.sourceMac }}</el-descriptions-item>
        <el-descriptions-item label="目标MAC地址">{{ selectedAlert.targetMac }}</el-descriptions-item>
        <el-descriptions-item label="状态">{{ selectedAlert.status }}</el-descriptions-item>
        <el-descriptions-item label="安全建议" v-if="selectedAlert.suggestion">
          {{ selectedAlert.suggestion }}
        </el-descriptions-item>
      </el-descriptions>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useAlertStore } from '../store/alert'
import { ElMessage } from 'element-plus'

const alertStore = useAlertStore()
const dateRange = ref([])
const filterType = ref('')
const filterStatus = ref('')
const dateQuick = ref('')

function setDateQuick(period) {
  dateQuick.value = period
  const now = new Date()
  const start = new Date()
  if (period === 'today') start.setHours(0,0,0,0)
  else if (period === 'week') start.setDate(now.getDate() - now.getDay())
  else if (period === 'month') start.setDate(1)
  dateRange.value = [start, now]
  fetchWithFilters()
}

function exportCSV() {
  const rows = filteredAlerts.value
  if (!rows.length) return ElMessage.warning('无数据可导出')
  const header = '时间,攻击类型,严重等级,源MAC,目标MAC,状态,建议'
  const csv = [header, ...rows.map(r => `"${r.timestamp}","${r.type}","${r.severity}","${r.sourceMac}","${r.targetMac||''}","${r.status}","${(r.suggestion||'').replace(/"/g,'""')}"`)].join('\n')
  const blob = new Blob(['﻿'+csv], {type:'text/csv;charset=utf-8'})
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a'); a.href=url; a.download='wifiguard-history.csv'; a.click()
  URL.revokeObjectURL(url)
  ElMessage.success('导出成功')
}
const currentPage = ref(1)
const pageSize = ref(10)
const detailVisible = ref(false)
const selectedAlert = ref(null)

onMounted(() => {
  fetchWithFilters()
})

watch([filterType, filterStatus], () => {
  fetchWithFilters()
})

function fetchWithFilters() {
  const params = {}
  if (filterType.value) params.type = filterType.value
  if (filterStatus.value) params.status = filterStatus.value
  if (dateRange.value && dateRange.value.length === 2) {
    params.startDate = dateRange.value[0]
    params.endDate = dateRange.value[1]
  }
  alertStore.fetchHistoryAlerts(params)
}

const filteredAlerts = computed(() => {
  let alerts = [...alertStore.historyAlerts]
  
  if (filterType.value) {
    alerts = alerts.filter(a => a.type === filterType.value)
  }
  
  if (filterStatus.value) {
    alerts = alerts.filter(a => a.status === filterStatus.value)
  }
  
  return alerts
})

const getSeverityType = (severity) => {
  const map = { critical: 'danger', high: 'danger', medium: 'warning', low: 'success' }
  return map[severity] || 'info'
}

const getSeverityLabel = (severity) => {
  const map = { critical: '严重', high: '高危', medium: '中危', low: '低危' }
  return map[severity] || severity
}

const getAttackTypeColor = (type) => {
  const map = {
    'Deauth攻击': 'danger', '钓鱼AP': 'danger', '暴力破解': 'warning',
    '非法接入': 'danger', 'Flood泛洪': 'warning', '弱口令': 'info', '弱加密协议': 'info', 'KRACK风险': 'danger'
  }
  return map[type] || 'info'
}

const showDetail = (alert) => {
  selectedAlert.value = alert
  detailVisible.value = true
}

const handlePageChange = (page) => {
  currentPage.value = page
}
</script>

<style scoped>
.history-container {
  padding: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-actions {
  display: flex;
  align-items: center;
}
.stat-mini { padding: 8px 10px; background:#f5f7fa; border-radius:8px; text-align:center; font-size:12px; color:#909399; }
.stat-mini b { display:block; font-size:20px; color:#303133; }
.stat-mini.red b { color:#f56c6c; }
.stat-mini.orange b, .stat-mini.yellow b { color:#e6a23c; }
</style>
