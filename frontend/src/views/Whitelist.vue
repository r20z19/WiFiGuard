<template>
  <div class="whitelist-container">
    <el-card>
      <template #header>
        <div class="card-header">
          <div class="header-left">
            <span>设备白名单管理</span>
            <el-tag v-if="alertStore.accessListMode === 'whitelist'" type="success" size="small">当前生效中</el-tag>
          </div>
          <div class="header-actions">
            <div class="toggle-wrapper">
              <span class="toggle-label">启用白名单</span>
              <el-switch :model-value="alertStore.accessListMode === 'whitelist'" @change="toggleWhitelistMode" active-text="开" inactive-text="关" size="large" />
            </div>
            <el-button type="primary" size="small" @click="showImportDialog">
              <el-icon><Plus /></el-icon>从在线设备导入
            </el-button>
            <el-button type="success" size="small" plain @click="showAddDialog">
              <el-icon><Plus /></el-icon>手动添加
            </el-button>
          </div>
        </div>
      </template>

      <el-alert v-if="alertStore.accessListMode !== 'whitelist'" title="白名单未启用" type="info" :closable="false" show-icon style="margin-bottom:16px">
        <p style="margin:0">白名单模式当前未启用。启用后白名单中的设备将被视为可信设备，不会触发安全告警。</p>
      </el-alert>
      <el-alert v-else title="白名单已启用" type="success" :closable="false" show-icon style="margin-bottom:16px">
        <p style="margin:0">白名单模式已启用，名单中的设备将不会触发安全告警。建议将已知合法设备加入白名单。</p>
      </el-alert>

      <!-- Stats -->
      <el-row :gutter="12" style="margin-bottom:16px">
        <el-col :span="8">
          <div class="stat-box"><span class="stat-num">{{ alertStore.whitelist.length }}</span><span class="stat-lbl">白名单设备</span></div>
        </el-col>
        <el-col :span="8">
          <div class="stat-box green"><span class="stat-num">{{ matchedOnlineCount }}</span><span class="stat-lbl">当前在线</span></div>
        </el-col>
        <el-col :span="8">
          <div class="stat-box blue"><span class="stat-num">{{ protectedCount }}</span><span class="stat-lbl">受保护</span></div>
        </el-col>
      </el-row>

      <el-table :data="alertStore.whitelist" style="width:100%" stripe>
        <el-table-column prop="mac" label="MAC地址" width="200">
          <template #default="{ row }">
            <span class="mono-green">{{ row.mac }}</span>
            <el-tag v-if="isOnline(row.mac)" type="success" size="small" effect="plain" style="margin-left:6px">在线</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="name" label="设备名称" width="180" />
        <el-table-column label="在线信息" min-width="200">
          <template #default="{ row }">
            <span v-if="findOnline(row.mac)" class="online-info">
              IP: {{ findOnline(row.mac).ip || '-' }} · 信号: {{ findOnline(row.mac).signal }} dBm
            </span>
            <span v-else class="text-muted">当前不在线</span>
          </template>
        </el-table-column>
        <el-table-column prop="addedAt" label="添加时间" width="180" />
        <el-table-column label="操作" width="150" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" link size="small" @click="editDevice(row)">编辑</el-button>
            <el-button type="danger" link size="small" @click="removeDevice(row.mac)">移除</el-button>
          </template>
        </el-table-column>
      </el-table>
      <el-empty v-if="alertStore.whitelist.length === 0" description="暂无白名单设备，点击上方按钮添加" :image-size="80" />
    </el-card>

    <!-- Add/Edit Dialog -->
    <el-dialog v-model="dialogVisible" :title="isEdit ? '编辑设备' : '添加设备'" width="500px">
      <el-form :model="form" label-width="100px">
        <el-form-item label="MAC地址">
          <el-input v-model="form.mac" placeholder="AA:BB:CC:DD:EE:FF" @input="formatMac" />
        </el-form-item>
        <el-form-item label="设备名称">
          <el-input v-model="form.name" placeholder="例: 办公室电脑" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="saveDevice">确定</el-button>
      </template>
    </el-dialog>

    <!-- Batch Import Dialog -->
    <el-dialog v-model="importVisible" title="从在线设备导入" width="650px">
      <div class="import-hint">
        选择要加入白名单的在线设备（已加入名单的设备不会显示）
      </div>
      <el-table :data="importableDevices" style="width:100%" max-height="400" @selection-change="onImportSelect" ref="importTableRef">
        <el-table-column type="selection" width="45" />
        <el-table-column label="类型" width="55">
          <template #default="{ row }"><span style="font-size:18px">{{ getDeviceEmoji(row) }}</span></template>
        </el-table-column>
        <el-table-column prop="mac" label="MAC地址" width="170" />
        <el-table-column label="厂商" width="120">
          <template #default="{ row }">{{ row.vendor || '-' }}</template>
        </el-table-column>
        <el-table-column prop="ip" label="IP地址" width="130" />
        <el-table-column label="状态">
          <template #default="{ row }">
            <el-tag :type="row.status === '正常' ? 'success' : 'warning'" size="small">{{ row.status }}</el-tag>
          </template>
        </el-table-column>
      </el-table>
      <div class="import-selected" v-if="importSelected.length > 0">
        已选 <b>{{ importSelected.length }}</b> 个设备
      </div>
      <template #footer>
        <el-button @click="importVisible = false">取消</el-button>
        <el-button type="primary" @click="batchImport" :disabled="importSelected.length === 0">
          导入 {{ importSelected.length > 0 ? importSelected.length : '' }} 个设备
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useAlertStore } from '../store/alert'
import { ElMessage, ElMessageBox } from 'element-plus'

const alertStore = useAlertStore()
const dialogVisible = ref(false)
const importVisible = ref(false)
const isEdit = ref(false)
const editingMac = ref('')
const form = ref({ mac: '', name: '' })
const importSelected = ref([])
const importTableRef = ref(null)

const matchedOnlineCount = computed(() =>
  alertStore.whitelist.filter(w => alertStore.onlineDevices.some(d => d.mac === w.mac)).length
)
const protectedCount = computed(() => alertStore.whitelist.length)

const importableDevices = computed(() =>
  alertStore.onlineDevices.filter(d =>
    !alertStore.whitelist.some(w => w.mac === d.mac) &&
    !alertStore.blacklist.some(b => b.mac === d.mac)
  )
)

function isOnline(mac) { return alertStore.onlineDevices.some(d => d.mac === mac) }

function findOnline(mac) { return alertStore.onlineDevices.find(d => d.mac === mac) }

function getDeviceEmoji(dev) {
  const v = (dev.vendor || '').toLowerCase()
  if (v.includes('apple') || v.includes('samsung')) return '📱'
  if (v.includes('dell') || v.includes('lenovo') || v.includes('hp')) return '🖥'
  if (v.includes('cisco') || v.includes('tp-link') || dev.ssid) return '📡'
  return '💻'
}

function formatMac() {
  let val = form.value.mac.replace(/[^a-fA-F0-9]/g, '').toUpperCase()
  if (val.length > 12) val = val.slice(0, 12)
  const parts = []
  for (let i = 0; i < val.length; i += 2) {
    parts.push(val.slice(i, i + 2))
  }
  form.value.mac = parts.join(':')
}

function toggleWhitelistMode(enabled) {
  if (!enabled) { alertStore.setAccessListMode(''); ElMessage.info('已关闭白名单模式'); return }
  if (alertStore.accessListMode === 'blacklist') {
    ElMessageBox.confirm('当前黑名单模式已启用，启用白名单将自动关闭黑名单。是否继续？', '切换名单模式', {
      confirmButtonText: '确认切换', cancelButtonText: '取消', type: 'warning'
    }).then(() => {
      alertStore.setAccessListMode('whitelist')
      ElMessage.success('已切换为白名单模式')
    }).catch(() => {})
    return
  }
  alertStore.setAccessListMode('whitelist')
  ElMessage.success('已启用白名单模式')
}

function showAddDialog() { isEdit.value = false; form.value = { mac: '', name: '' }; dialogVisible.value = true }
function showImportDialog() { importVisible.value = true; importSelected.value = [] }

function editDevice(device) {
  isEdit.value = true; editingMac.value = device.mac
  form.value = { mac: device.mac, name: device.name }
  dialogVisible.value = true
}

async function saveDevice() {
  if (!form.value.mac || !form.value.name) { ElMessage.warning('请填写完整信息'); return }
  try {
    if (isEdit.value) {
      await alertStore.removeFromWhitelist(editingMac.value)
      await alertStore.addToWhitelist({ mac: form.value.mac, name: form.value.name })
      ElMessage.success('设备信息已更新')
    } else {
      await alertStore.addToWhitelist({ mac: form.value.mac, name: form.value.name })
      ElMessage.success('设备已加入白名单')
    }
    dialogVisible.value = false
  } catch (e) { ElMessage.error(e.message || '操作失败') }
}

function removeDevice(mac) {
  ElMessageBox.confirm('确认从白名单中移除此设备？', '提示', {
    confirmButtonText: '确认', cancelButtonText: '取消', type: 'warning'
  }).then(async () => {
    await alertStore.removeFromWhitelist(mac)
    ElMessage.success('设备已从白名单移除')
  }).catch(() => {})
}

function onImportSelect(rows) { importSelected.value = rows }

async function batchImport() {
  let count = 0
  for (const dev of importSelected.value) {
    try {
      await alertStore.addToWhitelist({ mac: dev.mac, name: `${getDeviceEmoji(dev)} 设备-${dev.mac.slice(-4)}` })
      count++
    } catch {}
  }
  ElMessage.success(`已导入 ${count} 个设备到白名单`)
  importVisible.value = false
  importSelected.value = []
}

onMounted(() => {
  alertStore.fetchWhitelist()
  alertStore.fetchOnlineDevices()
})
</script>

<style scoped>
.whitelist-container { padding: 16px; }
.card-header { display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 10px; }
.header-left { display: flex; align-items: center; gap: 12px; }
.header-actions { display: flex; align-items: center; gap: 12px; }
.toggle-wrapper { display: flex; align-items: center; gap: 8px; }
.toggle-label { font-size: 13px; color: #606266; font-weight: 500; }
.mono-green { font-family: monospace; font-size: 12px; color: #67c23a; }

.stat-box { text-align: center; padding: 12px; background: #f5f7fa; border-radius: 8px; }
.stat-box.green { border-left: 3px solid #67c23a; }
.stat-box.blue { border-left: 3px solid #409eff; }
.stat-num { display: block; font-size: 22px; font-weight: bold; color: #303133; }
.stat-lbl { font-size: 11px; color: #909399; }

.online-info { font-size: 12px; color: #606266; }
.text-muted { font-size: 12px; color: #c0c4cc; }

.import-hint { margin-bottom: 12px; padding: 8px 12px; background: #f0f7ff; border-radius: 6px; font-size: 13px; color: #409eff; }
.import-selected { margin-top: 10px; font-size: 13px; color: #303133; }
</style>
