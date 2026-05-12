<template>
  <el-container class="app-container">
    <el-header class="app-header">
      <div class="header-left">
        <el-icon class="logo-icon"><Monitor /></el-icon>
        <h1 class="app-title">WiFiGuard</h1>
        <span class="app-subtitle">智能无线入侵检测与预警系统</span>
      </div>
      <div class="header-right">
        <el-badge :value="alertCount" :hidden="alertCount === 0" class="alert-badge">
          <el-icon @click="showAlerts" class="icon-btn"><Bell /></el-icon>
        </el-badge>
        <el-dropdown>
          <span class="user-info">
            <el-icon class="icon-btn"><User /></el-icon>
            <span class="username">{{ authStore.userInfo.username }}</span>
          </span>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item @click="showChangePassword">修改密码</el-dropdown-item>
              <el-dropdown-item divided @click="handleLogout">退出登录</el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </div>
    </el-header>

    <el-container>
      <el-aside width="220px" class="app-aside">
        <el-menu
          :default-active="activeMenu"
          class="side-menu"
          router
          @select="handleMenuSelect"
        >
          <el-menu-item index="/">
            <el-icon><Odometer /></el-icon>
            <span>系统概览</span>
          </el-menu-item>
          <el-menu-item index="/alerts">
            <el-icon><Warning /></el-icon>
            <span>当前告警</span>
          </el-menu-item>
          <el-menu-item index="/history">
            <el-icon><Clock /></el-icon>
            <span>历史告警</span>
          </el-menu-item>
          <el-menu-item index="/devices">
            <el-icon><Cellphone /></el-icon>
            <span>在线设备</span>
          </el-menu-item>
          <el-menu-item index="/whitelist">
            <el-icon><Check /></el-icon>
            <span>设备白名单</span>
          </el-menu-item>
          <el-menu-item index="/blacklist">
            <el-icon><Close /></el-icon>
            <span>设备黑名单</span>
          </el-menu-item>
          <el-menu-item index="/email">
            <el-icon><Message /></el-icon>
            <span>邮箱推送</span>
          </el-menu-item>
        </el-menu>
      </el-aside>

      <el-main class="app-main">
        <router-view />
      </el-main>
    </el-container>

    <el-dialog
      v-model="showChangePwdDialog"
      title="修改密码"
      width="400px"
      :close-on-click-modal="false"
    >
      <el-form
        ref="changePwdFormRef"
        :model="changePwdForm"
        :rules="changePwdRules"
        label-width="80px"
      >
        <el-form-item label="旧密码" prop="oldPassword">
          <el-input
            v-model="changePwdForm.oldPassword"
            type="password"
            placeholder="请输入旧密码"
            show-password
          />
        </el-form-item>
        <el-form-item label="新密码" prop="newPassword">
          <el-input
            v-model="changePwdForm.newPassword"
            type="password"
            placeholder="请输入新密码"
            show-password
          />
        </el-form-item>
        <el-form-item label="确认密码" prop="confirmPassword">
          <el-input
            v-model="changePwdForm.confirmPassword"
            type="password"
            placeholder="请再次输入新密码"
            show-password
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showChangePwdDialog = false">取消</el-button>
        <el-button type="primary" @click="handleUpdatePassword">确认修改</el-button>
      </template>
    </el-dialog>
  </el-container>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, reactive } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAlertStore } from './store/alert'
import { useAuthStore } from './store/auth'
import { changePassword as apiChangePassword } from './api/index'
import { ElMessage, ElMessageBox } from 'element-plus'

const router = useRouter()
const route = useRoute()
const alertStore = useAlertStore()
const authStore = useAuthStore()

const activeMenu = computed(() => route.path)
const alertCount = computed(() => alertStore.currentAlerts.length)

let pollTimer = null

onMounted(() => {
  alertStore.fetchSystemStatus()
  alertStore.fetchCurrentAlerts()
  alertStore.fetchOnlineDevices()
  pollTimer = setInterval(() => {
    alertStore.fetchCurrentAlerts()
  }, 5000)
})

onUnmounted(() => {
  if (pollTimer) clearInterval(pollTimer)
})

const handleMenuSelect = (index) => {
  router.push(index)
}

const showAlerts = () => {
  router.push('/alerts')
}

const handleLogout = async () => {
  try {
    await ElMessageBox.confirm('确定要退出登录吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    authStore.logout()
    router.push('/login')
  } catch {
  }
}

const showChangePwdDialog = ref(false)
const changePwdFormRef = ref(null)

const changePwdForm = reactive({
  oldPassword: '',
  newPassword: '',
  confirmPassword: ''
})

const validateConfirmPassword = (rule, value, callback) => {
  if (value !== changePwdForm.newPassword) {
    callback(new Error('两次输入的密码不一致'))
  } else {
    callback()
  }
}

const changePwdRules = {
  oldPassword: [{ required: true, message: '请输入旧密码', trigger: 'blur' }],
  newPassword: [
    { required: true, message: '请输入新密码', trigger: 'blur' },
    { min: 6, message: '密码长度至少6位', trigger: 'blur' }
  ],
  confirmPassword: [
    { required: true, message: '请再次输入新密码', trigger: 'blur' },
    { validator: validateConfirmPassword, trigger: 'blur' }
  ]
}

const showChangePassword = () => {
  showChangePwdDialog.value = true
}

const handleUpdatePassword = async () => {
  if (!changePwdFormRef.value) return
  await changePwdFormRef.value.validate(async (valid) => {
    if (!valid) return
    try {
      await apiChangePassword({
        oldPassword: changePwdForm.oldPassword,
        newPassword: changePwdForm.newPassword
      })
      showChangePwdDialog.value = false
      ElMessage.success('密码修改成功')
      changePwdForm.oldPassword = ''
      changePwdForm.newPassword = ''
      changePwdForm.confirmPassword = ''
    } catch (e) {
      ElMessage.error('密码修改失败，请检查旧密码是否正确')
    }
  })
}
</script>

<style scoped>
.app-container {
  height: 100vh;
}

.app-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
  color: white;
  padding: 0 24px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
}

.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.logo-icon {
  font-size: 32px;
  color: #67c23a;
}

.app-title {
  margin: 0;
  font-size: 24px;
  font-weight: bold;
}

.app-subtitle {
  font-size: 12px;
  opacity: 0.8;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 16px;
}

.icon-btn {
  font-size: 20px;
  cursor: pointer;
  transition: all 0.3s;
  color: white;
}

.icon-btn:hover {
  color: #67c23a;
  transform: scale(1.1);
}

.user-info {
  display: flex;
  align-items: center;
  gap: 6px;
  cursor: pointer;
  color: white;
  transition: all 0.3s;
}

.user-info:hover {
  color: #67c23a;
}

.username {
  font-size: 14px;
}

.alert-badge {
  cursor: pointer;
}

.app-aside {
  background: #fff;
  box-shadow: 2px 0 8px rgba(0, 0, 0, 0.05);
}

.side-menu {
  border-right: none;
  height: 100%;
}

.app-main {
  background: #f0f2f5;
  padding: 20px;
  overflow-y: auto;
}
</style>
