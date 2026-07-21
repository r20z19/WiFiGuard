<template>
  <router-view v-if="!authStore.isLoggedIn || authStore.isFirstLogin" />
  <el-container v-else class="app-container">
    <!-- Header -->
    <el-header class="app-header">
      <div class="header-left">
        <el-button class="collapse-btn" text @click="isCollapsed = !isCollapsed">
          <el-icon :size="20"><Fold v-if="!isCollapsed" /><Expand v-else /></el-icon>
        </el-button>
        <el-icon class="logo-icon"><Monitor /></el-icon>
        <h1 class="app-title">WiFiGuard</h1>
        <el-divider direction="vertical" />
        <!-- Breadcrumb -->
        <el-breadcrumb separator="/" class="breadcrumb">
          <el-breadcrumb-item :to="{ path: '/' }">首页</el-breadcrumb-item>
          <el-breadcrumb-item v-if="currentRouteName">{{ currentRouteName }}</el-breadcrumb-item>
        </el-breadcrumb>
      </div>
      <div class="header-right">
        <el-tooltip :content="isDark ? '切换亮色模式' : '切换暗色模式'" placement="bottom">
          <el-button class="theme-btn" text @click="toggleTheme">
            {{ isDark ? '☀️' : '🌙' }}
          </el-button>
        </el-tooltip>
        <!-- System status indicator -->
        <el-tooltip :content="'系统状态: ' + (systemStatusText)" placement="bottom">
          <span class="status-indicator">
            <span class="status-dot" :class="systemStatusClass"></span>
            <span class="status-text">{{ systemStatusText }}</span>
          </span>
        </el-tooltip>
        <!-- Alert bell with dropdown -->
        <el-popover placement="bottom-end" :width="320" trigger="click">
          <template #reference>
            <el-badge :value="alertCount" :hidden="alertCount === 0" class="alert-badge">
              <el-icon class="icon-btn"><Bell /></el-icon>
            </el-badge>
          </template>
          <div class="notify-panel">
            <div class="notify-header">
              <span>告警通知</span>
              <el-button type="primary" link size="small" @click="$router.push('/alerts')">查看全部</el-button>
            </div>
            <div v-if="alertStore.currentAlerts.length === 0" class="notify-empty">暂无告警</div>
            <div
              v-for="alert in alertStore.currentAlerts.slice(0, 5)"
              :key="alert.id"
              class="notify-item"
              @click="$router.push('/alerts')"
            >
              <span class="notify-dot" :class="'severity-' + alert.severity"></span>
              <div class="notify-body">
                <span class="notify-type">{{ alert.type }}</span>
                <span class="notify-mac">{{ alert.sourceMac?.slice(0, 17) }}</span>
                <span class="notify-time">{{ formatRelativeTime(alert.timestamp) }}</span>
              </div>
            </div>
          </div>
        </el-popover>
        <!-- User dropdown -->
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
      <!-- Collapsible Sidebar -->
      <el-aside :width="isCollapsed ? '64px' : '220px'" class="app-aside" :class="{ collapsed: isCollapsed }">
        <el-menu
          :default-active="activeMenu"
          class="side-menu"
          :collapse="isCollapsed"
          router
        >
          <el-menu-item index="/">
            <el-icon><Odometer /></el-icon>
            <span>系统概览</span>
          </el-menu-item>
          <el-menu-item index="/alerts">
            <el-icon><Warning /></el-icon>
            <span>当前告警<el-badge v-if="!isCollapsed" :value="alertCount" :hidden="alertCount === 0" class="menu-badge" /></span>
          </el-menu-item>
          <el-menu-item index="/history">
            <el-icon><Clock /></el-icon>
            <span>历史告警</span>
          </el-menu-item>
          <el-menu-item index="/devices">
            <el-icon><Cellphone /></el-icon>
            <span>在线设备<el-badge v-if="!isCollapsed" :value="deviceCount" :hidden="deviceCount === 0" class="menu-badge" type="info" /></span>
          </el-menu-item>
          <el-menu-item index="/whitelist">
            <el-icon><Check /></el-icon>
            <span>设备白名单</span>
            <el-tag v-if="!isCollapsed && alertStore.accessListMode === 'whitelist'" size="small" type="success" class="mode-tag">启用</el-tag>
          </el-menu-item>
          <el-menu-item index="/blacklist">
            <el-icon><Close /></el-icon>
            <span>设备黑名单</span>
            <el-tag v-if="!isCollapsed && alertStore.accessListMode === 'blacklist'" size="small" type="danger" class="mode-tag">启用</el-tag>
          </el-menu-item>
          <el-menu-item index="/email">
            <el-icon><Message /></el-icon>
            <span>邮箱推送</span>
          </el-menu-item>
          <el-menu-item index="/map">
            <el-icon><House /></el-icon>
            <span>网络拓扑</span>
          </el-menu-item>
          <el-menu-item index="/logs">
            <el-icon><Document /></el-icon>
            <span>系统日志</span>
          </el-menu-item>
          <el-menu-item index="/report">
            <el-icon><DataAnalysis /></el-icon>
            <span>安全报告</span>
          </el-menu-item>
          <el-menu-item index="/ai">
            <el-icon><Cpu /></el-icon>
            <span>AI 功能</span>
          </el-menu-item>
        </el-menu>
      </el-aside>

      <el-main class="app-main">
        <router-view />
      </el-main>
    </el-container>

    <!-- AI Panel (floating) -->
    <AiPanel ref="aiPanelRef" />

    <!-- Change Password Dialog -->
    <el-dialog v-model="showChangePwdDialog" title="修改密码" width="400px" :close-on-click-modal="false">
      <el-form ref="changePwdFormRef" :model="changePwdForm" :rules="changePwdRules" label-width="80px">
        <el-form-item label="旧密码" prop="oldPassword">
          <el-input v-model="changePwdForm.oldPassword" type="password" placeholder="请输入旧密码" show-password />
        </el-form-item>
        <el-form-item label="新密码" prop="newPassword">
          <el-input v-model="changePwdForm.newPassword" type="password" placeholder="请输入新密码" show-password />
        </el-form-item>
        <el-form-item label="确认密码" prop="confirmPassword">
          <el-input v-model="changePwdForm.confirmPassword" type="password" placeholder="请再次输入新密码" show-password />
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
import { Fold, Expand } from '@element-plus/icons-vue'
import AiPanel from './components/AiPanel.vue'

const router = useRouter()
const aiPanelRef = ref(null)
const route = useRoute()
const alertStore = useAlertStore()
const authStore = useAuthStore()

const isCollapsed = ref(false)
const isDark = ref(localStorage.getItem('theme') === 'dark')

function toggleTheme() {
  isDark.value = !isDark.value
  localStorage.setItem('theme', isDark.value ? 'dark' : 'light')
  document.documentElement.className = isDark.value ? 'dark' : ''
}

// Apply theme on mount
if (isDark.value) document.documentElement.className = 'dark'

const activeMenu = computed(() => route.path)
const alertCount = computed(() => alertStore.currentAlerts.length)
const deviceCount = computed(() => alertStore.onlineDevices.length)

const currentRouteName = computed(() => {
  const map = {
    '/': '系统概览',
    '/alerts': '当前告警',
    '/history': '历史告警',
    '/devices': '在线设备',
    '/whitelist': '设备白名单',
    '/blacklist': '设备黑名单',
    '/email': '邮箱推送',
    '/map': '网络拓扑',
    '/logs': '系统日志',
    '/report': '安全报告',
    '/ai': 'AI 功能',
  }
  return map[route.path] || ''
})

const systemStatusText = computed(() => {
  const s = alertStore.systemStatus.status
  if (s === 'listening') return '监听中'
  if (s === 'initializing') return '初始化中'
  return s || '未知'
})

const systemStatusClass = computed(() => {
  const s = alertStore.systemStatus.status
  if (s === 'listening') return 'online'
  if (s === 'initializing') return 'warn'
  return 'offline'
})

function formatRelativeTime(ts) {
  if (!ts) return ''
  try {
    const diff = Date.now() - new Date(ts).getTime()
    const mins = Math.floor(diff / 60000)
    if (mins < 1) return '刚刚'
    if (mins < 60) return mins + '分钟前'
    const hours = Math.floor(mins / 60)
    if (hours < 24) return hours + '小时前'
    return Math.floor(hours / 24) + '天前'
  } catch { return ts }
}

let pollTimer = null
let prevAlertIds = new Set()

function checkNewAlerts() {
  const alerts = alertStore.currentAlerts
  for (const a of alerts) {
    if (!prevAlertIds.has(a.id) && (a.severity === 'critical' || a.severity === 'high')) {
      if ('Notification' in window && Notification.permission === 'granted') {
        new Notification('⚠️ WiFiGuard 高危告警', { body: `${a.type} — ${a.sourceMac}`, icon: '/favicon.ico' })
      }
    }
  }
  prevAlertIds = new Set(alerts.map(a => a.id))
}

onMounted(() => {
  if (!authStore.isLoggedIn || authStore.isFirstLogin) return
  if ('Notification' in window && Notification.permission === 'default') {
    Notification.requestPermission()
  }
  alertStore.fetchSystemStatus()
  alertStore.fetchCurrentAlerts()
  alertStore.fetchOnlineDevices()
  pollTimer = setInterval(() => {
    alertStore.fetchCurrentAlerts().then(checkNewAlerts)
    alertStore.fetchSystemStatus()
  }, 5000)
})

onUnmounted(() => {
  if (pollTimer) clearInterval(pollTimer)
})

const handleLogout = async () => {
  try {
    await ElMessageBox.confirm('确定要退出登录吗？', '提示', {
      confirmButtonText: '确定', cancelButtonText: '取消', type: 'warning'
    })
    authStore.logout()
    router.push('/login')
  } catch {}
}

// Password change
const showChangePwdDialog = ref(false)
const changePwdFormRef = ref(null)
const changePwdForm = reactive({ oldPassword: '', newPassword: '', confirmPassword: '' })

const validateConfirmPassword = (rule, value, callback) => {
  if (value !== changePwdForm.newPassword) callback(new Error('两次输入的密码不一致'))
  else callback()
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

const showChangePassword = () => { showChangePwdDialog.value = true }

const handleUpdatePassword = async () => {
  if (!changePwdFormRef.value) return
  await changePwdFormRef.value.validate(async (valid) => {
    if (!valid) return
    try {
      await apiChangePassword({ oldPassword: changePwdForm.oldPassword, newPassword: changePwdForm.newPassword })
      showChangePwdDialog.value = false
      ElMessage.success('密码修改成功')
      changePwdForm.oldPassword = ''
      changePwdForm.newPassword = ''
      changePwdForm.confirmPassword = ''
    } catch { ElMessage.error('密码修改失败，请检查旧密码是否正确') }
  })
}
</script>

<style scoped>
.app-container { height: 100vh; }

.app-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
  color: white;
  padding: 0 16px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.15);
  z-index: 100;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 10px;
}

.collapse-btn {
  color: rgba(255,255,255,0.8);
  padding: 4px;
}
.collapse-btn:hover { color: #fff; background: rgba(255,255,255,0.1); }

.logo-icon { font-size: 28px; color: #67c23a; }

.app-title {
  margin: 0;
  font-size: 20px;
  font-weight: bold;
  white-space: nowrap;
}

.breadcrumb {
  margin-left: 4px;
}
.breadcrumb :deep(.el-breadcrumb__item) { font-size: 13px; }
.breadcrumb :deep(.el-breadcrumb__inner) { color: rgba(255,255,255,0.7); font-weight: normal; }
.breadcrumb :deep(.el-breadcrumb__inner.is-link:hover) { color: #fff; }
.breadcrumb :deep(.el-breadcrumb__separator) { color: rgba(255,255,255,0.4); }
.breadcrumb :deep(.el-breadcrumb__item:last-child .el-breadcrumb__inner) { color: #fff; }

.header-right {
  display: flex;
  align-items: center;
  gap: 14px;
}

/* System status */
.status-indicator {
  display: flex;
  align-items: center;
  gap: 5px;
  font-size: 12px;
  color: rgba(255,255,255,0.75);
}

.status-dot {
  width: 8px; height: 8px;
  border-radius: 50%;
  display: inline-block;
}
.status-dot.online { background: #67c23a; box-shadow: 0 0 6px #67c23a; animation: status-pulse 2s infinite; }
.status-dot.warn { background: #e6a23c; box-shadow: 0 0 6px #e6a23c; }
.status-dot.offline { background: #909399; }

@keyframes status-pulse {
  0%, 100% { box-shadow: 0 0 4px #67c23a; }
  50% { box-shadow: 0 0 10px #67c23a, 0 0 20px #67c23a44; }
}

.theme-btn { font-size: 18px; color: rgba(255,255,255,0.8); padding: 4px; }
.theme-btn:hover { color: #fff; background: rgba(255,255,255,0.1); }

.icon-btn {
  font-size: 18px;
  cursor: pointer;
  transition: all 0.3s;
  color: white;
}
.icon-btn:hover { color: #67c23a; transform: scale(1.1); }

.user-info {
  display: flex;
  align-items: center;
  gap: 6px;
  cursor: pointer;
  color: white;
  transition: all 0.3s;
}
.user-info:hover { color: #67c23a; }
.username { font-size: 13px; }

.alert-badge {
  cursor: pointer;
}

.menu-badge {
  margin-left: 6px;
  display: inline-flex;
  vertical-align: middle;
}

/* Notification panel */
.notify-panel { max-height: 300px; overflow-y: auto; }

.notify-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 4px 8px;
  border-bottom: 1px solid #ebeef5;
  font-weight: bold;
  font-size: 14px;
}

.notify-empty {
  padding: 24px;
  text-align: center;
  color: #909399;
  font-size: 13px;
}

.notify-item {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  padding: 10px 4px;
  border-bottom: 1px solid #f2f3f5;
  cursor: pointer;
  transition: background 0.2s;
}
.notify-item:hover { background: #f5f7fa; }

.notify-dot {
  width: 8px; height: 8px;
  border-radius: 50%;
  margin-top: 4px;
  flex-shrink: 0;
}
.notify-dot.severity-critical { background: #f56c6c; box-shadow: 0 0 4px #f56c6c; }
.notify-dot.severity-high { background: #f56c6c; }
.notify-dot.severity-medium { background: #e6a23c; }
.notify-dot.severity-low { background: #67c23a; }

.notify-body {
  display: flex;
  flex-direction: column;
  gap: 2px;
  font-size: 12px;
}

.notify-type { font-weight: 600; color: #303133; }

.notify-mac {
  font-family: monospace;
  color: #909399;
  font-size: 11px;
}

.notify-time {
  color: #c0c4cc;
  font-size: 10px;
}

/* Sidebar */
.app-aside {
  background: #fff;
  box-shadow: 2px 0 8px rgba(0,0,0,0.05);
  transition: width 0.3s;
  overflow: hidden;
}

.app-aside.collapsed .mode-tag { display: none; }

.side-menu {
  border-right: none;
  height: 100%;
}

.mode-tag {
  margin-left: auto;
  margin-right: 8px;
}

.app-main {
  background: #f0f2f5;
  padding: 16px;
  overflow-y: auto;
}
</style>
