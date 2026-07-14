<template>
  <div class="whitelist-container">
    <el-card>
      <template #header>
        <div class="card-header">
          <div class="header-left">
            <span>设备白名单管理</span>
            <el-tag v-if="alertStore.accessListMode === 'whitelist'" type="success" size="small" class="active-badge">
              当前生效中
            </el-tag>
          </div>
          <div class="header-actions">
            <div class="toggle-wrapper">
              <span class="toggle-label">启用白名单</span>
              <el-switch
                :model-value="alertStore.accessListMode === 'whitelist'"
                @change="toggleWhitelistMode"
                active-text="开"
                inactive-text="关"
                size="large"
              />
            </div>
            <el-button type="primary" size="small" @click="showAddDialog">
              <el-icon><Plus /></el-icon>
              添加设备
            </el-button>
          </div>
        </div>
      </template>

      <el-alert
        v-if="alertStore.accessListMode !== 'whitelist'"
        title="白名单未启用"
        type="info"
        :closable="false"
        show-icon
        style="margin-bottom: 20px;"
      >
        <template #default>
          <p>白名单模式当前未启用。启用后，白名单中的设备将被视为可信设备，不会触发安全告警。注意：白名单和黑名单不能同时启用。</p>
        </template>
      </el-alert>

      <el-alert
        v-else
        title="白名单已启用"
        type="success"
        :closable="false"
        show-icon
        style="margin-bottom: 20px;"
      >
        <template #default>
          <p>白名单模式已启用，名单中的设备将不会触发安全告警。建议将已知的合法设备加入白名单。当前黑名单模式已自动关闭。</p>
        </template>
      </el-alert>

      <el-table :data="alertStore.whitelist" style="width: 100%" stripe>
        <el-table-column prop="mac" label="MAC地址" width="200">
          <template #default="{ row }">
            <span class="mac-address">{{ row.mac }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="name" label="设备名称" width="200" />
        <el-table-column prop="addedAt" label="添加时间" width="200" />
        <el-table-column label="操作" width="150" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" link @click="editDevice(row)">编辑</el-button>
            <el-button type="danger" link @click="removeDevice(row.mac)">移除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <el-empty v-if="alertStore.whitelist.length === 0" description="暂无白名单设备" />
    </el-card>
  </div>

  <el-dialog v-model="dialogVisible" :title="isEdit ? '编辑设备' : '添加设备'" width="500px">
    <el-form :model="form" label-width="100px">
      <el-form-item label="MAC地址">
        <el-input v-model="form.mac" placeholder="例: AA:BB:CC:DD:EE:FF" />
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
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useAlertStore } from '../store/alert'
import { ElMessage, ElMessageBox } from 'element-plus'

const alertStore = useAlertStore()
const dialogVisible = ref(false)
const isEdit = ref(false)
const editingMac = ref('')
const form = ref({ mac: '', name: '' })

onMounted(() => {
  alertStore.fetchWhitelist()
})

const toggleWhitelistMode = (enabled) => {
  if (!enabled) {
    // Simply turn off whitelist mode
    alertStore.setAccessListMode('')
    ElMessage.info('已关闭白名单模式')
    return
  }

  // Enabling whitelist - check if blacklist is currently active
  const prev = alertStore.accessListMode
  if (prev === 'blacklist') {
    ElMessageBox.confirm(
      '当前黑名单模式已启用，启用白名单将自动关闭黑名单模式。是否继续？',
      '切换名单模式',
      {
        confirmButtonText: '确认切换',
        cancelButtonText: '取消',
        type: 'warning'
      }
    ).then(() => {
      alertStore.setAccessListMode('whitelist')
      ElMessage.success('已切换为白名单模式，黑名单已自动关闭')
    }).catch(() => {})
    return
  }

  alertStore.setAccessListMode('whitelist')
  ElMessage.success('已启用白名单模式')
}

const showAddDialog = () => {
  isEdit.value = false
  form.value = { mac: '', name: '' }
  dialogVisible.value = true
}

const editDevice = (device) => {
  isEdit.value = true
  editingMac.value = device.mac
  form.value = { mac: device.mac, name: device.name }
  dialogVisible.value = true
}

const saveDevice = async () => {
  if (!form.value.mac || !form.value.name) {
    ElMessage.warning('请填写完整信息')
    return
  }

  try {
    if (isEdit.value) {
      await alertStore.removeFromWhitelist(editingMac.value)
      await alertStore.addToWhitelist({ mac: form.value.mac, name: form.value.name })
      ElMessage.success('设备信息已更新')
    } else {
      await alertStore.addToWhitelist({
        mac: form.value.mac,
        name: form.value.name
      })
      ElMessage.success('设备已加入白名单')
    }
    dialogVisible.value = false
  } catch (e) {
    ElMessage.error(e.message || '操作失败')
  }
}

const removeDevice = (mac) => {
  ElMessageBox.confirm('确认从白名单中移除此设备？', '提示', {
    confirmButtonText: '确认',
    cancelButtonText: '取消',
    type: 'warning'
  }).then(async () => {
    try {
      await alertStore.removeFromWhitelist(mac)
    } catch { /* store already refreshed */ }
    ElMessage.success('设备已从白名单移除')
  }).catch(() => {})
}
</script>

<style scoped>
.whitelist-container {
  padding: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 16px;
}

.toggle-wrapper {
  display: flex;
  align-items: center;
  gap: 8px;
}

.toggle-label {
  font-size: 14px;
  color: #606266;
  font-weight: 500;
}

.active-badge {
  font-size: 12px;
}

.mac-address {
  font-family: monospace;
  color: #67c23a;
}
</style>
