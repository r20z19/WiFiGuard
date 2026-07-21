<template>
  <div class="logs-container">
    <!-- Filter bar -->
    <el-card>
      <div class="filter-bar">
        <div class="filter-left">
          <el-radio-group v-model="levelFilter" size="small" @change="fetchLogs">
            <el-radio-button value="">全部 ({{ stats.total }})</el-radio-button>
            <el-radio-button value="ERROR">错误 ({{ stats.byLevel?.ERROR || 0 }})</el-radio-button>
            <el-radio-button value="WARNING">警告 ({{ stats.byLevel?.WARNING || 0 }})</el-radio-button>
            <el-radio-button value="INFO">信息 ({{ stats.byLevel?.INFO || 0 }})</el-radio-button>
          </el-radio-group>
          <el-select v-model="categoryFilter" placeholder="类别" size="small" clearable style="width:120px;margin-left:10px" @change="fetchLogs">
            <el-option label="全部类别" value="" />
            <el-option label="攻击检测" value="attack" />
            <el-option label="系统" value="system" />
            <el-option label="设备" value="device" />
            <el-option label="配置" value="config" />
          </el-select>
          <el-input v-model="searchQuery" placeholder="搜索日志..." size="small" clearable style="width:200px;margin-left:10px" @clear="fetchLogs" @keyup.enter="fetchLogs">
            <template #prefix><el-icon><Search /></el-icon></template>
          </el-input>
        </div>
        <div class="filter-right">
          <el-button size="small" @click="exportLog">📥 导出日志</el-button>
          <el-button size="small" type="primary" @click="fetchLogs">
            <el-icon><Refresh /></el-icon>刷新
          </el-button>
        </div>
      </div>
    </el-card>

    <!-- Log table -->
    <el-card style="margin-top:12px">
      <el-table :data="logs" style="width:100%" stripe size="small" max-height="calc(100vh - 260px)">
        <el-table-column prop="timestamp" label="时间" width="170" />
        <el-table-column prop="level" label="等级" width="75">
          <template #default="{ row }">
            <el-tag :type="levelTag(row.level)" size="small">{{ row.level }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="category" label="类别" width="80">
          <template #default="{ row }">
            <el-tag size="small" effect="plain">{{ catLabel(row.category) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="message" label="消息" min-width="250" show-overflow-tooltip />
        <el-table-column prop="detail" label="详情" min-width="200" show-overflow-tooltip>
          <template #default="{ row }">
            <span class="detail-text">{{ row.detail || '-' }}</span>
          </template>
        </el-table-column>
      </el-table>
      <el-empty v-if="logs.length === 0" description="暂无日志记录" :image-size="80" />
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { getLogs, getLogStats } from '../api'
import { ElMessage } from 'element-plus'
import api from '../api'

const logs = ref([])
const stats = reactive({ total: 0, byLevel: {} })
const levelFilter = ref('')
const categoryFilter = ref('')
const searchQuery = ref('')

function levelTag(l) {
  return l === 'ERROR' ? 'danger' : l === 'WARNING' ? 'warning' : 'info'
}
function catLabel(c) {
  return { attack: '攻击', system: '系统', device: '设备', config: '配置' }[c] || c
}

async function fetchLogs() {
  try {
    const params = { limit: 300 }
    if (levelFilter.value) params.level = levelFilter.value
    if (categoryFilter.value) params.category = categoryFilter.value
    if (searchQuery.value) params.search = searchQuery.value
    logs.value = await getLogs(params)
    const s = await getLogStats()
    Object.assign(stats, s)
  } catch (e) { console.error(e) }
}

async function exportLog() {
  try {
    const params = {}
    if (levelFilter.value) params.level = levelFilter.value
    if (categoryFilter.value) params.category = categoryFilter.value
    if (searchQuery.value) params.search = searchQuery.value
    const resp = await api.get('/logs/export', { params, responseType: 'blob' })
    // Axios interceptor returns response.data; for blob it IS the Blob
    const blob = resp instanceof Blob ? resp : new Blob([resp], { type: 'text/csv;charset=utf-8' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a'); a.href = url; a.download = 'wifiguard-logs.csv'; a.click()
    URL.revokeObjectURL(url)
    ElMessage.success('导出成功')
  } catch { ElMessage.error('导出失败') }
}

onMounted(() => fetchLogs())
</script>

<style scoped>
.logs-container { padding: 16px; }
.filter-bar { display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 10px; }
.filter-left { display: flex; align-items: center; flex-wrap: wrap; gap: 8px; }
.filter-right { display: flex; gap: 8px; }
.detail-text { font-size: 12px; color: #909399; font-family: monospace; }
</style>
