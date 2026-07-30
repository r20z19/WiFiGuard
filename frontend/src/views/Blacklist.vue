<template>
  <div class="blacklist-container">
    <el-card>
      <template #header>
        <div class="card-header">
          <div class="header-left">
            <span>设备黑名单管理</span>
            <el-tag v-if="alertStore.accessMode.blacklist" type="danger" size="small">当前生效中</el-tag>
          </div>
          <div class="header-actions">
            <div class="toggle-wrapper">
              <span class="toggle-label">启用黑名单</span>
              <el-switch :model-value="alertStore.accessMode.blacklist" @change="toggleBlacklistMode" active-text="开" inactive-text="关" size="large" />
            </div>
            <el-button type="warning" size="small" @click="showImportDialog">
              <el-icon><Plus /></el-icon>从在线设备导入
            </el-button>
            <el-button type="danger" size="small" plain @click="showAddDialog">
              <el-icon><Plus /></el-icon>手动添加
            </el-button>
          </div>
        </div>
      </template>

      <el-alert v-if="!alertStore.accessMode.blacklist" title="黑名单未启用" type="info" :closable="false" show-icon style="margin-bottom:16px">
        <p style="margin:0">黑名单模式未启用。当前不会对任何设备执行踢出操作。开启后，名单中的设备将被自动断开连接。</p>
      </el-alert>
      <el-alert v-else title="黑名单模式生效中" type="error" :closable="false" show-icon style="margin-bottom:16px">
        <p style="margin:0;line-height:1.8">
          当前黑名单模式已生效：<br/>
          <b>• 黑名单设备</b>：一旦尝试接入将被立即踢出网络，并触发安全告警<br/>
          <b>• 其他设备</b>：不受影响，可正常连接和使用网络
        </p>
      </el-alert>

      <!-- Stats -->
      <el-row :gutter="12" style="margin-bottom:16px">
        <el-col :span="8">
          <div class="stat-box danger"><span class="stat-num">{{ alertStore.blacklist.length }}</span><span class="stat-lbl">黑名单设备</span></div>
        </el-col>
        <el-col :span="8">
          <div class="stat-box orange"><span class="stat-num">{{ onlineBlacklistedCount }}</span><span class="stat-lbl">当前在线</span></div>
        </el-col>
        <el-col :span="8">
          <div class="stat-box"><span class="stat-num">{{ alertCountRelated }}</span><span class="stat-lbl">关联告警</span></div>
        </el-col>
      </el-row>

      <el-table :data="alertStore.blacklist" style="width:100%" stripe>
        <el-table-column prop="mac" label="MAC地址" width="200">
          <template #default="{ row }">
            <span class="mono-red">{{ row.mac }}</span>
            <el-tag v-if="isOnline(row.mac)" type="danger" size="small" effect="dark" style="margin-left:6px">在线⚠</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="name" label="设备名称" width="150" />
        <el-table-column prop="reason" label="加入原因" min-width="180" />
        <el-table-column label="在线信息" width="160">
          <template #default="{ row }">
            <span v-if="findOnline(row.mac)" class="online-info">
              {{ findOnline(row.mac).ip || '-' }}
            </span>
            <span v-else class="text-muted">不在线</span>
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
      <el-empty v-if="alertStore.blacklist.length === 0" description="暂无黑名单设备，点击上方按钮添加" :image-size="80" />
    </el-card>

    <!-- Add/Edit Dialog -->
    <el-dialog v-model="dialogVisible" :title="isEdit ? '编辑设备' : '添加设备'" width="500px">
      <el-form :model="form" label-width="100px">
        <el-form-item label="MAC地址">
          <el-input v-model="form.mac" placeholder="AA:BB:CC:DD:EE:FF" @input="formatMac" />
        </el-form-item>
        <el-form-item label="设备名称">
          <el-input v-model="form.name" placeholder="例: 可疑AP" />
        </el-form-item>
        <el-form-item label="加入原因">
          <el-input v-model="form.reason" type="textarea" placeholder="例: 检测到Deauth攻击" :rows="2" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="danger" @click="saveDevice">确定</el-button>
      </template>
    </el-dialog>

    <!-- Batch Import Dialog -->
    <el-dialog v-model="importVisible" title="从在线设备导入黑名单" width="650px">
      <div class="import-hint">选择要加入黑名单的在线设备（可选择可疑设备或陌生设备）</div>
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
        <el-table-column label="状态" width="80">
          <template #default="{ row }">
            <el-tag :type="row.status === '正常' ? 'success' : 'warning'" size="small">{{ row.status }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="原因" min-width="120">
          <template #default="{ row }">
            <el-tag v-if="row.status === '可疑'" type="warning" size="small">可疑设备</el-tag>
            <el-tag v-else-if="row.signal < -75" type="warning" size="small">信号弱</el-tag>
            <span v-else style="color:#909399;font-size:12px">手动选择</span>
          </template>
        </el-table-column>
      </el-table>
      <div class="import-selected" v-if="importSelected.length > 0">已选 <b>{{ importSelected.length }}</b> 个设备</div>
      <template #footer>
        <el-button @click="importVisible = false">取消</el-button>
        <el-button type="danger" @click="batchImport" :disabled="importSelected.length === 0">
          加入黑名单 ({{ importSelected.length }})
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
const form = ref({ mac: '', name: '', reason: '' })
const importSelected = ref([])
const importTableRef = ref(null)

const onlineBlacklistedCount = computed(() =>
  alertStore.blacklist.filter(b => alertStore.onlineDevices.some(d => d.mac.toLowerCase() === b.mac.toLowerCase())).length
)

const alertCountRelated = computed(() =>
  alertStore.currentAlerts.filter(a =>
    alertStore.blacklist.some(b => b.mac === a.sourceMac || b.mac === a.targetMac)
  ).length
)

const importableDevices = computed(() =>
  alertStore.onlineDevices.filter(d =>
    !alertStore.blacklist.some(b => b.mac === d.mac) &&
    !alertStore.whitelist.some(w => w.mac === d.mac)
  )
)

function isOnline(mac) { return alertStore.onlineDevices.some(d => d.mac.toLowerCase() === mac.toLowerCase()) }
function findOnline(mac) { return alertStore.onlineDevices.find(d => d.mac.toLowerCase() === mac.toLowerCase()) }

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
  for (let i = 0; i < val.length; i += 2) parts.push(val.slice(i, i + 2))
  form.value.mac = parts.join(':')
}

async function toggleBlacklistMode(enabled) {
  try {
    await alertStore.setBlacklistEnabled(enabled)
    ElMessage.success(enabled ? '已启用黑名单模式' : '已关闭黑名单模式')
  } catch (e) {
    ElMessage.error('切换失败: ' + (e.message || '未知错误'))
  }
}

function showAddDialog() { isEdit.value = false; form.value = { mac: '', name: '', reason: '' }; dialogVisible.value = true }
function showImportDialog() { importVisible.value = true; importSelected.value = [] }

function editDevice(device) {
  isEdit.value = true; editingMac.value = device.mac
  form.value = { mac: device.mac, name: device.name, reason: device.reason }
  dialogVisible.value = true
}

async function saveDevice() {
  if (!form.value.mac || !form.value.name || !form.value.reason) { ElMessage.warning('请填写完整信息'); return }
  try {
    if (isEdit.value) {
      await alertStore.removeFromBlacklist(editingMac.value)
      await alertStore.addToBlacklist({ mac: form.value.mac, name: form.value.name, reason: form.value.reason })
      ElMessage.success('设备信息已更新')
    } else {
      await alertStore.addToBlacklist({ mac: form.value.mac, name: form.value.name, reason: form.value.reason })
      ElMessage.warning('设备已加入黑名单')
    }
    dialogVisible.value = false
  } catch (e) { ElMessage.error(e.message || '操作失败') }
}

function removeDevice(mac) {
  ElMessageBox.confirm('确认从黑名单中移除此设备？', '提示', {
    confirmButtonText: '确认', cancelButtonText: '取消', type: 'warning'
  }).then(async () => {
    await alertStore.removeFromBlacklist(mac)
    ElMessage.success('设备已从黑名单移除')
  }).catch(() => {})
}

function onImportSelect(rows) { importSelected.value = rows }

async function batchImport() {
  let count = 0
  for (const dev of importSelected.value) {
    try {
      const reason = dev.status === '可疑' ? '可疑设备，批量导入' : `手动导入 - 信号: ${dev.signal}dBm`
      await alertStore.addToBlacklist({ mac: dev.mac, name: `${getDeviceEmoji(dev)} 设备-${dev.mac.slice(-4)}`, reason })
      count++
    } catch {}
  }
  ElMessage.warning(`已将 ${count} 个设备加入黑名单`)
  importVisible.value = false
  importSelected.value = []
}

onMounted(() => {
  alertStore.fetchSystemStatus()
  alertStore.fetchBlacklist()
  alertStore.fetchOnlineDevices()
  alertStore.fetchCurrentAlerts()
})
</script>

<style scoped>
.blacklist-container { padding: 16px; }
.card-header { display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 10px; }
.header-left { display: flex; align-items: center; gap: 12px; }
.header-actions { display: flex; align-items: center; gap: 12px; }
.toggle-wrapper { display: flex; align-items: center; gap: 8px; }
.toggle-label { font-size: 13px; color: #606266; font-weight: 500; }
.mono-red { font-family: monospace; font-size: 12px; color: #f56c6c; }
.stat-box { text-align: center; padding: 12px; background: #f5f7fa; border-radius: 8px; }
.stat-box.danger { border-left: 3px solid #f56c6c; }
.stat-box.orange { border-left: 3px solid #e6a23c; }
.stat-num { display: block; font-size: 22px; font-weight: bold; color: #303133; }
.stat-lbl { font-size: 11px; color: #909399; }
.online-info { font-size: 12px; color: #606266; font-family: monospace; }
.text-muted { font-size: 12px; color: #c0c4cc; }
.import-hint { margin-bottom: 12px; padding: 8px 12px; background: #fef0f0; border-radius: 6px; font-size: 13px; color: #f56c6c; }
.import-selected { margin-top: 10px; font-size: 13px; color: #303133; }
</style>
