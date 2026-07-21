<template>
  <div class="ai-settings-container">
    <h2 class="page-title">🤖 AI 智能功能设置</h2>
    <p class="page-desc">配置 AI 后可使用智能告警解读、安全顾问、自动报告和设备识别功能</p>

    <!-- Status card -->
    <el-row :gutter="16" style="margin-bottom:16px">
      <el-col :span="8">
        <el-card shadow="hover">
          <div class="status-card">
            <span class="status-dot" :class="config.enabled && config.hasKey ? 'online' : 'offline'"></span>
            <div>
              <div class="status-title">{{ config.enabled && config.hasKey ? 'AI 已启用' : 'AI 未启用' }}</div>
              <div class="status-sub">{{ config.enabled && config.hasKey ? providerName + ' · 已连接' : '请配置 API Key' }}</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card shadow="hover">
          <div class="func-item">🔍 智能告警解读</div>
          <div class="func-item">💬 AI 安全顾问</div>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card shadow="hover">
          <div class="func-item">📊 自动安全报告</div>
          <div class="func-item">📱 智能设备识别</div>
        </el-card>
      </el-col>
    </el-row>

    <!-- Configuration form -->
    <el-card shadow="hover">
      <template #header><span>⚙️ 平台配置</span></template>
      <el-form label-width="100px" style="max-width:600px">
        <el-form-item label="AI 平台">
          <el-select v-model="configForm.provider" style="width:100%" @change="onProviderChange">
            <el-option label="DeepSeek（推荐 · 性价比高）" value="deepseek" />
            <el-option label="通义千问 Qwen（阿里云）" value="qwen" />
            <el-option label="智谱 GLM（清华）" value="glm" />
          </el-select>
        </el-form-item>
        <el-form-item label="API Key">
          <el-input v-model="configForm.apiKey" type="password" show-password placeholder="粘贴 API Key" />
        </el-form-item>
        <el-form-item label="启用 AI">
          <el-switch v-model="configForm.enabled" active-text="开" inactive-text="关" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="saveConfig" :loading="saving">💾 保存配置</el-button>
          <el-button @click="testConnection" :loading="testing">🔗 测试连接</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- Provider guide -->
    <el-card shadow="hover" style="margin-top:16px">
      <template #header><span>📖 获取 API Key 指南</span></template>
      <el-collapse v-model="activeGuide">
        <el-collapse-item title="DeepSeek 获取方式" name="deepseek">
          <div class="guide-step">1. 访问 <a href="https://platform.deepseek.com" target="_blank">platform.deepseek.com</a> 注册账号</div>
          <div class="guide-step">2. 进入左侧菜单 「API Keys」</div>
          <div class="guide-step">3. 点击「创建 API Key」，复制保存</div>
          <div class="guide-step">4. 粘贴到上方 API Key 输入框</div>
          <div class="guide-note">💰 费用：约 ¥1/百万 token，新用户通常有免费额度</div>
        </el-collapse-item>
        <el-collapse-item title="通义千问 Qwen 获取方式" name="qwen">
          <div class="guide-step">1. 访问 <a href="https://dashscope.aliyun.com" target="_blank">dashscope.aliyun.com</a> 登录阿里云账号</div>
          <div class="guide-step">2. 进入「API-KEY 管理」</div>
          <div class="guide-step">3. 创建新的 API Key</div>
          <div class="guide-step">4. 粘贴到上方 API Key 输入框</div>
          <div class="guide-note">💰 费用：qwen-plus 约 ¥0.8/百万 token</div>
        </el-collapse-item>
        <el-collapse-item title="智谱 GLM 获取方式" name="glm">
          <div class="guide-step">1. 访问 <a href="https://open.bigmodel.cn" target="_blank">open.bigmodel.cn</a> 注册</div>
          <div class="guide-step">2. 进入「API Keys」页面</div>
          <div class="guide-step">3. 添加新的 API Key</div>
          <div class="guide-step">4. 粘贴到上方 API Key 输入框</div>
          <div class="guide-note">💰 费用：GLM-4-Flash 免费，GLM-4 约 ¥0.1/百万 token</div>
        </el-collapse-item>
      </el-collapse>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { getAiConfig, saveAiConfig } from '../api'
import api from '../api'
import { ElMessage } from 'element-plus'

const config = reactive({ provider: 'deepseek', hasKey: false, enabled: false })
const configForm = reactive({ provider: 'deepseek', apiKey: '', enabled: false })
const saving = ref(false)
const testing = ref(false)
const activeGuide = ref('deepseek')

const providerName = computed(() => {
  return { deepseek: 'DeepSeek', qwen: '通义千问', glm: '智谱 GLM' }[config.provider] || config.provider
})

function onProviderChange(val) { activeGuide.value = val }

async function loadConfig() {
  try {
    const cfg = await getAiConfig()
    Object.assign(config, cfg)
    configForm.provider = cfg.provider
    configForm.enabled = cfg.enabled
  } catch {}
}

async function saveConfig() {
  saving.value = true
  try {
    const cfg = await saveAiConfig({ ...configForm })
    Object.assign(config, cfg)
    ElMessage.success('配置已保存')
  } catch { ElMessage.error('保存失败') }
  saving.value = false
}

async function testConnection() {
  if (!configForm.apiKey) { ElMessage.warning('请先填写 API Key'); return }
  testing.value = true
  try {
    await api.post('/ai/config', { provider: configForm.provider, apiKey: configForm.apiKey, enabled: true })
    const resp = await api.post('/ai/chat', { messages: [{ role: 'user', content: '你好，请回复"连接成功"' }] })
    if (resp.result) ElMessage.success('✅ AI 连接测试成功！' + ' — ' + resp.result.substring(0, 30))
    else ElMessage.error('连接失败')
  } catch (e) {
    ElMessage.error('连接失败：' + (e.message || '请检查 API Key 和网络'))
  }
  testing.value = false
}

onMounted(() => loadConfig())
</script>

<style scoped>
.ai-settings-container { padding: 20px; max-width: 900px; }
.page-title { font-size: 24px; color: #303133; margin: 0 0 4px; }
.page-desc { font-size: 14px; color: #909399; margin: 0 0 20px; }

.status-card { display: flex; align-items: center; gap: 14px; padding: 8px 0; }
.status-dot { width: 14px; height: 14px; border-radius: 50%; flex-shrink: 0; }
.status-dot.online { background: #67c23a; box-shadow: 0 0 8px #67c23a; }
.status-dot.offline { background: #c0c4cc; }
.status-title { font-size: 16px; font-weight: 600; color: #303133; }
.status-sub { font-size: 13px; color: #909399; margin-top: 2px; }
.func-item { padding: 6px 0; font-size: 14px; color: #606266; }

.guide-step { padding: 4px 0; font-size: 13px; color: #606266; line-height: 1.8; }
.guide-step a { color: #409eff; }
.guide-note { margin-top: 8px; padding: 8px 12px; background: #fef0f0; border-radius: 6px; font-size: 12px; color: #e6a23c; }
</style>
