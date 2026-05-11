<template>
  <div class="blacklist-container">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>设备黑名单管理</span>
          <el-button type="danger" size="small" @click="showAddDialog">
            <el-icon><Plus /></el-icon>
            添加设备
          </el-button>
        </div>
      </template>

      <el-alert
        title="黑名单说明"
        type="error"
        :closable="false"
        style="margin-bottom: 20px;"
      >
        <template #default>
          <p>黑名单中的设备将被标记为威胁设备，一旦检测到将立即触发安全告警。建议将已知的攻击设备或可疑设备加入黑名单。</p>
        </template>
      </el-alert>

      <el-table :data="alertStore.blacklist" style="width: 100%" stripe>
        <el-table-column prop="mac" label="MAC地址" width="200">
          <template #default="{ row }">
            <span class="mac-address">{{ row.mac }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="name" label="设备名称" width="150" />
        <el-table-column prop="reason" label="加入原因" width="200" />
        <el-table-column prop="addedAt" label="添加时间" width="200" />
        <el-table-column label="操作" width="150" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" link @click="editDevice(row)">编辑</el-button>
            <el-button type="danger" link @click="removeDevice(row.mac)">移除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <el-empty v-if="alertStore.blacklist.length === 0" description="暂无黑名单设备" />
    </el-card>
  </div>

  <el-dialog v-model="dialogVisible" :title="isEdit ? '编辑设备' : '添加设备'" width="500px">
    <el-form :model="form" label-width="100px">
      <el-form-item label="MAC地址">
        <el-input v-model="form.mac" placeholder="例: AA:BB:CC:DD:EE:FF" />
      </el-form-item>
      <el-form-item label="设备名称">
        <el-input v-model="form.name" placeholder="例: 可疑AP" />
      </el-form-item>
      <el-form-item label="加入原因">
        <el-input v-model="form.reason" type="textarea" placeholder="例: 检测到Deauth攻击" />
      </el-form-item>
    </el-form>
    <template #footer>
      <el-button @click="dialogVisible = false">取消</el-button>
      <el-button type="danger" @click="saveDevice">确定</el-button>
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
const form = ref({ mac: '', name: '', reason: '' })

onMounted(() => {
  alertStore.fetchBlacklist()
})

const showAddDialog = () => {
  isEdit.value = false
  form.value = { mac: '', name: '', reason: '' }
  dialogVisible.value = true
}

const editDevice = (device) => {
  isEdit.value = true
  editingMac.value = device.mac
  form.value = { mac: device.mac, name: device.name, reason: device.reason }
  dialogVisible.value = true
}

const saveDevice = async () => {
  if (!form.value.mac || !form.value.name || !form.value.reason) {
    ElMessage.warning('请填写完整信息')
    return
  }

  try {
    if (isEdit.value) {
      await alertStore.removeFromBlacklist(editingMac.value)
      await alertStore.addToBlacklist({ mac: form.value.mac, name: form.value.name, reason: form.value.reason })
      ElMessage.success('设备信息已更新')
    } else {
      await alertStore.addToBlacklist({
        mac: form.value.mac,
        name: form.value.name,
        reason: form.value.reason
      })
      ElMessage.warning('设备已加入黑名单')
    }
    dialogVisible.value = false
  } catch {
    ElMessage.error('操作失败')
  }
}

const removeDevice = (mac) => {
  ElMessageBox.confirm('确认从黑名单中移除此设备？', '提示', {
    confirmButtonText: '确认',
    cancelButtonText: '取消',
    type: 'warning'
  }).then(async () => {
    try {
      await alertStore.removeFromBlacklist(mac)
    } catch { /* store already refreshed */ }
    ElMessage.success('设备已从黑名单移除')
  }).catch(() => {})
}
</script>

<style scoped>
.blacklist-container {
  padding: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.mac-address {
  font-family: monospace;
  color: #f56c6c;
}
</style>
