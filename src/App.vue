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
          <el-icon class="icon-btn"><Setting /></el-icon>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item @click="goToSettings">系统设置</el-dropdown-item>
              <el-dropdown-item @click="goToEmailConfig">邮箱配置</el-dropdown-item>
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
  </el-container>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAlertStore } from './store/alert'

const router = useRouter()
const route = useRoute()
const alertStore = useAlertStore()

const activeMenu = computed(() => route.path)
const alertCount = computed(() => alertStore.currentAlerts.length)

const handleMenuSelect = (index) => {
  router.push(index)
}

const showAlerts = () => {
  router.push('/alerts')
}

const goToSettings = () => {
  router.push('/settings')
}

const goToEmailConfig = () => {
  router.push('/email')
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
