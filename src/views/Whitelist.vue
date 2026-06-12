<template>
  <div class="whitelist-container">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>设备白名单管理</span>
          <el-button type="primary" size="small" @click="showAddDialog">
            <el-icon><Plus /></el-icon>
            添加设备
          </el-button>
        </div>
      </template>

      <el-alert
        title="白名单说明"
        type="success"
        :closable="false"
        style="margin-bottom: 20px;"
      >
        <template #default>
          <p>白名单中的设备将被视为可信设备，不会触发安全告警。建议将已知的合法设备加入白名单。</p>
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
import { ref } from 'vue'
import { useAlertStore } from '../store/alert'
import { ElMessage, ElMessageBox } from 'element-plus'

const alertStore = useAlertStore()
const dialogVisible = ref(false)
const isEdit = ref(false)
const editingMac = ref('')
const form = ref({ mac: '', name: '' })

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

const saveDevice = () => {
  if (!form.value.mac || !form.value.name) {
    ElMessage.warning('请填写完整信息')
    return
  }

  if (isEdit.value) {
    const index = alertStore.whitelist.findIndex(d => d.mac === editingMac.value)
    if (index !== -1) {
      alertStore.whitelist[index].name = form.value.name
    }
    ElMessage.success('设备信息已更新')
  } else {
    alertStore.addToWhitelist({
      mac: form.value.mac,
      name: form.value.name,
      addedAt: new Date().toLocaleString('zh-CN')
    })
    ElMessage.success('设备已加入白名单')
  }

  dialogVisible.value = false
}

const removeDevice = (mac) => {
  ElMessageBox.confirm('确认从白名单中移除此设备？', '提示', {
    confirmButtonText: '确认',
    cancelButtonText: '取消',
    type: 'warning'
  }).then(() => {
    alertStore.removeFromWhitelist(mac)
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

.mac-address {
  font-family: monospace;
  color: #67c23a;
}
</style>
