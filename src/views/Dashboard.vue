<template>
  <div class="dashboard-container">
    <el-row :gutter="20" class="status-cards">
      <el-col :span="6">
        <el-card class="status-card" :class="systemStatus.class">
          <div class="card-content">
            <el-icon class="card-icon"><Cpu /></el-icon>
            <div class="card-info">
              <div class="card-label">系统状态</div>
              <div class="card-value">{{ systemStatus.text }}</div>
            </div>
          </div>
        </el-card>
      </el-col>

      <el-col :span="6">
        <el-card class="status-card danger">
          <div class="card-content">
            <el-icon class="card-icon"><Warning /></el-icon>
            <div class="card-info">
              <div class="card-label">当前告警</div>
              <div class="card-value">{{ alertStore.currentAlerts.length }}</div>
            </div>
          </div>
        </el-card>
      </el-col>

      <el-col :span="6">
        <el-card class="status-card info">
          <div class="card-content">
            <el-icon class="card-icon"><Cellphone /></el-icon>
            <div class="card-info">
              <div class="card-label">在线设备</div>
              <div class="card-value">{{ alertStore.onlineDevices.length }}</div>
            </div>
          </div>
        </el-card>
      </el-col>

      <el-col :span="6">
        <el-card class="status-card success">
          <div class="card-content">
            <el-icon class="card-icon"><Clock /></el-icon>
            <div class="card-info">
              <div class="card-label">历史告警</div>
              <div class="card-value">{{ alertStore.historyAlerts.length }}</div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20" class="main-content">
      <el-col :span="16">
        <el-card class="alerts-card">
          <template #header>
            <div class="card-header">
              <span>当前告警信息</span>
              <el-button type="primary" size="small" @click="$router.push('/alerts')">
                查看全部
              </el-button>
            </div>
          </template>

          <el-table :data="alertStore.currentAlerts.slice(0, 5)" style="width: 100%">
            <el-table-column prop="type" label="攻击类型" width="120" />
            <el-table-column prop="severity" label="严重等级" width="100">
              <template #default="{ row }">
                <el-tag :type="getSeverityType(row.severity)" size="small">
                  {{ getSeverityLabel(row.severity) }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="sourceMac" label="源MAC" width="180" />
            <el-table-column prop="timestamp" label="时间" width="180" />
            <el-table-column label="操作" width="100">
              <template #default="{ row }">
                <el-button type="primary" link @click="alertStore.clearAlert(row.id)">
                  处理
                </el-button>
              </template>
            </el-table-column>
          </el-table>

          <el-empty v-if="alertStore.currentAlerts.length === 0" description="暂无告警信息" />
        </el-card>

        <el-card class="suggestions-card" style="margin-top: 20px;">
          <template #header>
            <span>安全建议</span>
          </template>

          <div v-if="currentSuggestion" class="suggestion-content">
            <el-alert
              :title="currentSuggestion.type"
              :type="getSeverityType(currentSuggestion.severity)"
              :closable="false"
              show-icon
            >
              <template #default>
                <p>{{ currentSuggestion.suggestion }}</p>
              </template>
            </el-alert>
          </div>

          <el-empty v-else description="暂无安全建议" />
        </el-card>
      </el-col>

      <el-col :span="8">
        <el-card class="devices-card">
          <template #header>
            <div class="card-header">
              <span>在线设备</span>
              <el-button type="primary" link @click="$router.push('/devices')">
                更多
              </el-button>
            </div>
          </template>

          <div v-for="device in alertStore.onlineDevices.slice(0, 5)" :key="device.mac" class="device-item">
            <div class="device-info">
              <div class="device-mac">{{ device.mac }}</div>
              <div class="device-ip">{{ device.ip }}</div>
            </div>
            <el-tag :type="device.status === '正常' ? 'success' : 'warning'" size="small">
              {{ device.status }}
            </el-tag>
          </div>

          <el-empty v-if="alertStore.onlineDevices.length === 0" description="暂无在线设备" />
        </el-card>

        <el-card class="config-card" style="margin-top: 20px;">
          <template #header>
            <span>快速配置</span>
          </template>

          <div class="config-item" @click="$router.push('/whitelist')">
            <el-icon><Check /></el-icon>
            <span>设备白名单 ({{ alertStore.whitelist.length }})</span>
          </div>
          <div class="config-item" @click="$router.push('/blacklist')">
            <el-icon><Close /></el-icon>
            <span>设备黑名单 ({{ alertStore.blacklist.length }})</span>
          </div>
          <div class="config-item" @click="$router.push('/email')">
            <el-icon><Message /></el-icon>
            <span>邮箱推送 {{ alertStore.emailConfig.enabled ? '(已启用)' : '(未启用)' }}</span>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useAlertStore } from '../store/alert'

const alertStore = useAlertStore()

const systemStatus = computed(() => {
  return {
    text: '监听中',
    class: 'success'
  }
})

const currentSuggestion = computed(() => {
  return alertStore.currentAlerts.length > 0 ? alertStore.currentAlerts[0] : null
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
</script>

<style scoped>
.dashboard-container {
  padding: 20px;
}

.status-cards {
  margin-bottom: 20px;
}

.status-card {
  cursor: pointer;
  transition: all 0.3s;
}

.status-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.card-content {
  display: flex;
  align-items: center;
  gap: 16px;
}

.card-icon {
  font-size: 48px;
  color: #409eff;
}

.card-label {
  font-size: 14px;
  color: #909399;
}

.card-value {
  font-size: 24px;
  font-weight: bold;
  color: #303133;
}

.status-card.success .card-icon {
  color: #67c23a;
}

.status-card.danger .card-icon {
  color: #f56c6c;
}

.status-card.info .card-icon {
  color: #409eff;
}

.status-card.warning .card-icon {
  color: #e6a23c;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.device-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 0;
  border-bottom: 1px solid #ebeef5;
}

.device-item:last-child {
  border-bottom: none;
}

.device-mac {
  font-family: monospace;
  font-size: 13px;
  color: #303133;
}

.device-ip {
  font-size: 12px;
  color: #909399;
}

.config-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px;
  cursor: pointer;
  border-radius: 4px;
  transition: background 0.3s;
}

.config-item:hover {
  background: #f5f7fa;
}

.suggestion-content {
  padding: 10px 0;
}
</style>
