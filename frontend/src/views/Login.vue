<template>
  <div class="login-container">
    <div class="login-background">
      <div class="wave wave-1"></div>
      <div class="wave wave-2"></div>
      <div class="wave wave-3"></div>
    </div>
    <div class="login-card">
      <div class="login-header">
        <div class="logo-wrapper">
          <el-icon class="logo-icon"><Monitor /></el-icon>
        </div>
        <h1 class="app-title">WiFiGuard</h1>
        <p class="app-subtitle">智能无线入侵检测与预警系统</p>
      </div>
      <el-form
        ref="loginFormRef"
        :model="loginForm"
        :rules="loginRules"
        class="login-form"
        @submit.prevent="handleLogin"
      >
        <el-form-item prop="username">
          <el-input
            v-model="loginForm.username"
            placeholder="请输入用户名"
            size="large"
            :prefix-icon="User"
            @keyup.enter="handleLogin"
          />
        </el-form-item>
        <el-form-item prop="password">
          <el-input
            v-model="loginForm.password"
            type="password"
            placeholder="请输入密码"
            size="large"
            show-password
            :prefix-icon="Lock"
            @keyup.enter="handleLogin"
          />
        </el-form-item>
        <el-form-item>
          <el-button
            type="primary"
            size="large"
            class="login-button"
            :loading="loading"
            @click="handleLogin"
          >
            {{ loading ? '登录中...' : '登 录' }}
          </el-button>
        </el-form-item>
      </el-form>
    </div>

    <el-dialog
      v-model="showChangePassword"
      title="修改默认密码"
      width="400px"
      :close-on-click-modal="false"
    >
      <div class="password-change-tip">
        <el-icon class="tip-icon"><WarningFilled /></el-icon>
        <span>首次登录，请修改默认密码</span>
      </div>
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
        <el-button type="primary" @click="handleChangePassword">确认修改</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { User, Lock, Monitor, WarningFilled } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { useAuthStore } from '../store/auth'

const router = useRouter()
const authStore = useAuthStore()
const loading = ref(false)
const loginFormRef = ref(null)
const showChangePassword = ref(false)
const changePwdFormRef = ref(null)

const loginForm = reactive({
  username: '',
  password: ''
})

const loginRules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }]
}

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

const handleLogin = async () => {
  if (!loginFormRef.value) return
  await loginFormRef.value.validate(async (valid) => {
    if (!valid) return
    loading.value = true
    try {
      const result = await authStore.login(loginForm)
      if (result.success) {
        ElMessage.success('登录成功')
        if (result.isFirstLogin) {
          showChangePassword.value = true
        } else {
          router.push('/')
        }
      } else {
        ElMessage.error(result.message || '登录失败')
      }
    } catch (e) {
      ElMessage.error('登录失败，请检查网络连接')
    } finally {
      loading.value = false
    }
  })
}

const handleChangePassword = async () => {
  if (!changePwdFormRef.value) return
  await changePwdFormRef.value.validate(async (valid) => {
    if (!valid) return
    try {
      authStore.setUserInfo({
        username: loginForm.username,
        isFirstLogin: false
      })
      showChangePassword.value = false
      ElMessage.success('密码修改成功')
      router.push('/')
    } catch (e) {
      ElMessage.error('密码修改失败')
    }
  })
}
</script>

<style scoped>
.login-container {
  height: 100vh;
  display: flex;
  justify-content: center;
  align-items: center;
  background: linear-gradient(135deg, #1e3c72 0%, #2a5298 50%, #667eea 100%);
  position: relative;
  overflow: hidden;
}

.login-background {
  position: absolute;
  width: 100%;
  height: 100%;
  top: 0;
  left: 0;
}

.wave {
  position: absolute;
  bottom: -100px;
  left: 0;
  width: 200%;
  height: 200px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 45%;
  animation: wave 10s linear infinite;
}

.wave-1 {
  animation-duration: 8s;
  bottom: -50px;
  background: rgba(255, 255, 255, 0.15);
}

.wave-2 {
  animation-duration: 12s;
  bottom: -80px;
  background: rgba(255, 255, 255, 0.1);
}

.wave-3 {
  animation-duration: 15s;
  bottom: -120px;
  background: rgba(255, 255, 255, 0.05);
}

@keyframes wave {
  0% {
    transform: translateX(0) rotate(0deg);
  }
  50% {
    transform: translateX(-25%) rotate(180deg);
  }
  100% {
    transform: translateX(-50%) rotate(360deg);
  }
}

.login-card {
  width: 420px;
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(10px);
  border-radius: 20px;
  padding: 40px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
  z-index: 1;
}

.login-header {
  text-align: center;
  margin-bottom: 30px;
}

.logo-wrapper {
  width: 80px;
  height: 80px;
  background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
  border-radius: 20px;
  display: flex;
  justify-content: center;
  align-items: center;
  margin: 0 auto 20px;
  box-shadow: 0 8px 20px rgba(30, 60, 114, 0.3);
}

.logo-icon {
  font-size: 40px;
  color: #67c23a;
}

.app-title {
  margin: 0 0 8px;
  font-size: 28px;
  font-weight: bold;
  color: #1e3c72;
}

.app-subtitle {
  margin: 0;
  font-size: 14px;
  color: #666;
}

.login-form {
  margin-top: 30px;
}

.login-form :deep(.el-input__wrapper) {
  padding: 12px 16px;
  border-radius: 10px;
}

.login-form :deep(.el-form-item) {
  margin-bottom: 20px;
}

.login-button {
  width: 100%;
  height: 48px;
  font-size: 18px;
  border-radius: 10px;
  margin-top: 10px;
  background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
  border: none;
}

.login-button:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 20px rgba(30, 60, 114, 0.4);
}

.password-change-tip {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 16px;
  background: #fef0f0;
  border-radius: 8px;
  margin-bottom: 20px;
  color: #f56c6c;
  font-weight: 500;
}

.tip-icon {
  font-size: 18px;
}
</style>
