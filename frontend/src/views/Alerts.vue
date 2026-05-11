<template>
  <div class="alerts-container">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>当前告警信息</span>
          <el-button type="danger" size="small" @click="clearAllAlerts">
            清空所有告警
          </el-button>
        </div>
      </template>

      <el-table :data="alertStore.currentAlerts" style="width: 100%" stripe>
        <el-table-column prop="timestamp" label="告警时间" width="180" />
        <el-table-column prop="type" label="攻击类型" width="140">
          <template #default="{ row }">
            <el-tag :type="getAttackTypeColor(row.type)">{{ row.type }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="severity" label="严重等级" width="100">
          <template #default="{ row }">
            <el-badge :is-dot="row.severity === 'critical' || row.severity === 'high'">
              <el-tag :type="getSeverityType(row.severity)" size="small">
                {{ getSeverityLabel(row.severity) }}
              </el-tag>
            </el-badge>
          </template>
        </el-table-column>
        <el-table-column prop="sourceMac" label="源MAC地址" width="180" />
        <el-table-column prop="targetMac" label="目标MAC地址" width="180" />
        <el-table-column label="操作" width="100" fixed="right">
          <template #default="{ row }">
            <el-popover placement="left" trigger="click" width="400">
              <template #reference>
                <el-button type="primary" link>查看建议</el-button>
              </template>
              <div class="suggestion-popover">
                <h4>{{ row.type }}</h4>
                <p>{{ row.suggestion }}</p>
              </div>
            </el-popover>
            <el-button type="success" link @click="handleClear(row.id)">
              处理
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <el-empty v-if="alertStore.currentAlerts.length === 0" description="当前无告警信息，系统运行正常" />
    </el-card>

    <el-card style="margin-top: 20px;" v-if="alertStore.currentAlerts.length > 0">
      <template #header>
        <span>安全建议详情</span>
      </template>

      <el-collapse v-model="activeSuggestions">
        <el-collapse-item
          v-for="alert in alertStore.currentAlerts"
          :key="alert.id"
          :name="alert.id"
        >
          <template #title>
            <div class="collapse-title">
              <el-tag :type="getSeverityType(alert.severity)" size="small">
                {{ getSeverityLabel(alert.severity) }}
              </el-tag>
              <span class="alert-type">{{ alert.type }}</span>
              <span class="alert-time">{{ alert.timestamp }}</span>
            </div>
          </template>
          <div class="suggestion-detail">
            <el-descriptions :column="2" border>
              <el-descriptions-item label="攻击类型">{{ alert.type }}</el-descriptions-item>
              <el-descriptions-item label="严重等级">{{ getSeverityLabel(alert.severity) }}</el-descriptions-item>
              <el-descriptions-item label="源MAC地址">{{ alert.sourceMac }}</el-descriptions-item>
              <el-descriptions-item label="目标MAC地址">{{ alert.targetMac }}</el-descriptions-item>
              <el-descriptions-item label="告警时间">{{ alert.timestamp }}</el-descriptions-item>
            </el-descriptions>
            <el-alert
              title="处理建议"
              type="info"
              :closable="false"
              style="margin-top: 15px;"
              show-icon
            >
              <template #default>
                <p>{{ alert.suggestion }}</p>
              </template>
            </el-alert>
          </div>
        </el-collapse-item>
      </el-collapse>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useAlertStore } from '../store/alert'
import { ElMessage, ElMessageBox } from 'element-plus'

const alertStore = useAlertStore()
const activeSuggestions = ref([])

onMounted(() => {
  alertStore.fetchCurrentAlerts()
})

const getSeverityType = (severity) => {
  const map = {
    critical: 'danger',
    high: 'danger',
    medium: 'warning',
    low: 'success'
  }
  return map[severity] || 'info'
}

const getSeverityLabel = (severity) => {
  const map = {
    critical: '严重',
    high: '高危',
    medium: '中危',
    low: '低危'
  }
  return map[severity] || severity
}

const getAttackTypeColor = (type) => {
  const map = {
    'Deauth攻击': 'danger',
    '钓鱼AP': 'danger',
    '暴力破解': 'warning',
    '非法接入': 'danger',
    'Flood泛洪': 'warning',
    '弱口令': 'info',
    'KRACK风险': 'danger'
  }
  return map[type] || 'info'
}

const handleClear = (id) => {
  ElMessageBox.confirm('确认已处理此告警？', '提示', {
    confirmButtonText: '确认',
    cancelButtonText: '取消',
    type: 'success'
  }).then(() => {
    alertStore.clearAlert(id)
    ElMessage.success('告警已处理')
  }).catch(() => {})
}

const clearAllAlerts = () => {
  ElMessageBox.confirm('确认清空所有告警？', '警告', {
    confirmButtonText: '确认',
    cancelButtonText: '取消',
    type: 'warning'
  }).then(async () => {
    for (const alert of [...alertStore.currentAlerts]) {
      await alertStore.clearAlert(alert.id)
    }
    ElMessage.success('所有告警已清空')
  }).catch(() => {})
}
</script>

<style scoped>
.alerts-container {
  padding: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.suggestion-popover h4 {
  margin: 0 0 10px 0;
  color: #303133;
}

.suggestion-popover p {
  margin: 0;
  color: #606266;
  font-size: 13px;
  line-height: 1.6;
}

.collapse-title {
  display: flex;
  align-items: center;
  gap: 10px;
  width: 100%;
}

.alert-type {
  font-weight: bold;
  color: #303133;
}

.alert-time {
  margin-left: auto;
  color: #909399;
  font-size: 12px;
}

.suggestion-detail {
  padding: 10px;
}
</style>
