<template>
  <div class="devices-container">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>在线设备信息</span>
          <div class="header-actions">
            <el-input
              v-model="searchQuery"
              placeholder="搜索MAC/IP地址"
              size="small"
              clearable
              style="width: 200px; margin-right: 10px;"
              prefix-icon="Search"
            />
            <el-button type="primary" size="small" @click="refreshDevices">
              <el-icon><Refresh /></el-icon>
              刷新
            </el-button>
          </div>
        </div>
      </template>

      <el-table :data="filteredDevices" style="width: 100%" stripe>
        <el-table-column prop="mac" label="MAC地址" width="180">
          <template #default="{ row }">
            <span class="mac-address">{{ row.mac }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="ip" label="IP地址" width="150" />
        <el-table-column prop="ssid" label="连接SSID" width="180" />
        <el-table-column prop="signal" label="信号强度" width="120">
          <template #default="{ row }">
            <el-progress
              :percentage="getSignalPercentage(row.signal)"
              :color="getSignalColor(row.signal)"
              :stroke-width="10"
            />
          </template>
        </el-table-column>
        <el-table-column prop="status" label="设备状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.status === '正常' ? 'success' : 'warning'" size="small">
              {{ row.status }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="firstSeen" label="首次发现" width="180" />
        <el-table-column prop="lastSeen" label="最后活跃" width="180" />
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button
              type="success"
              link
              @click="addToWhitelist(row)"
              :disabled="isInWhitelist(row.mac)"
            >
              加入白名单
            </el-button>
            <el-button
              type="danger"
              link
              @click="addToBlacklist(row)"
              :disabled="isInBlacklist(row.mac)"
            >
              加入黑名单
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <el-empty v-if="filteredDevices.length === 0" description="暂无在线设备" />
    </el-card>

    <el-card style="margin-top: 20px;">
      <template #header>
        <span>设备统计</span>
      </template>

      <el-row :gutter="20">
        <el-col :span="8">
          <el-statistic title="总设备数" :value="alertStore.onlineDevices.length" />
        </el-col>
        <el-col :span="8">
          <el-statistic title="正常设备" :value="normalDevicesCount">
            <template #suffix>
              <el-icon style="color: #67c23a;"><Check /></el-icon>
            </template>
          </el-statistic>
        </el-col>
        <el-col :span="8">
          <el-statistic title="可疑设备" :value="suspiciousDevicesCount">
            <template #suffix>
              <el-icon style="color: #e6a23c;"><Warning /></el-icon>
            </template>
          </el-statistic>
        </el-col>
      </el-row>
    </el-card>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useAlertStore } from '../store/alert'
import { ElMessage } from 'element-plus'

const alertStore = useAlertStore()
const searchQuery = ref('')

const filteredDevices = computed(() => {
  if (!searchQuery.value) return alertStore.onlineDevices
  const query = searchQuery.value.toLowerCase()
  return alertStore.onlineDevices.filter(
    d => d.mac.toLowerCase().includes(query) || d.ip.includes(query)
  )
})

const normalDevicesCount = computed(() =>
  alertStore.onlineDevices.filter(d => d.status === '正常').length
)

const suspiciousDevicesCount = computed(() =>
  alertStore.onlineDevices.filter(d => d.status === '可疑').length
)

const getSignalPercentage = (signal) => {
  return Math.max(0, Math.min(100, (signal + 100) * 2))
}

const getSignalColor = (signal) => {
  if (signal >= -50) return '#67c23a'
  if (signal >= -70) return '#e6a23c'
  return '#f56c6c'
}

const isInWhitelist = (mac) => {
  return alertStore.whitelist.some(d => d.mac === mac)
}

const isInBlacklist = (mac) => {
  return alertStore.blacklist.some(d => d.mac === mac)
}

const addToWhitelist = (device) => {
  alertStore.addToWhitelist({
    mac: device.mac,
    name: `设备-${device.mac.slice(-4)}`,
    addedAt: new Date().toLocaleString('zh-CN')
  })
  ElMessage.success(`设备 ${device.mac} 已加入白名单`)
}

const addToBlacklist = (device) => {
  alertStore.addToBlacklist({
    mac: device.mac,
    name: `设备-${device.mac.slice(-4)}`,
    reason: '手动添加',
    addedAt: new Date().toLocaleString('zh-CN')
  })
  ElMessage.warning(`设备 ${device.mac} 已加入黑名单`)
}

const refreshDevices = () => {
  ElMessage.success('设备列表已刷新')
}
</script>

<style scoped>
.devices-container {
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

.mac-address {
  font-family: monospace;
  color: #409eff;
}
</style>
