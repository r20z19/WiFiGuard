<template>
  <!-- Floating AI button -->
  <div class="ai-floating" v-if="aiEnabled">
    <transition name="fade">
      <div v-if="showChat" class="ai-chat-panel">
        <div class="ai-chat-header">
          <span>🤖 AI 安全顾问</span>
          <div>
            <el-button size="small" text @click="showChat = false; showConfig = true">⚙️</el-button>
            <el-button :icon="Close" circle size="small" text @click="showChat = false" />
          </div>
        </div>
        <div class="ai-chat-body" ref="chatBody">
          <div v-for="(msg, i) in chatMessages" :key="i" :class="['ai-msg', msg.role]">
            <div class="ai-msg-text">{{ msg.content }}</div>
          </div>
          <div v-if="chatLoading" class="ai-msg assistant">
            <div class="ai-msg-text typing">思考中...</div>
          </div>
        </div>
        <div class="ai-chat-input">
          <el-input v-model="chatInput" placeholder="询问 WiFi 安全问题..." size="small" @keyup.enter="sendChat" />
          <el-button type="primary" size="small" @click="sendChat" :disabled="!chatInput.trim() || chatLoading">发送</el-button>
        </div>
      </div>
    </transition>
    <el-button class="ai-fab" type="primary" circle @click="showChat = !showChat">
      <span style="font-size:22px">🤖</span>
    </el-button>
  </div>

  <!-- Config dialog (shown when AI not configured) -->
  <el-dialog v-model="showConfig" title="🤖 AI 功能配置" width="480px" :close-on-click-modal="false">
    <el-alert type="info" :closable="false" show-icon style="margin-bottom:16px">
      <p style="margin:0">配置 AI 后可使用智能告警解读和安全顾问。需要自行获取对应平台的 API Key。</p>
    </el-alert>
    <el-form label-width="80px">
      <el-form-item label="AI 平台">
        <el-select v-model="configForm.provider" style="width:100%">
          <el-option label="DeepSeek (推荐)" value="deepseek" />
          <el-option label="通义千问 (Qwen)" value="qwen" />
          <el-option label="智谱 GLM" value="glm" />
        </el-select>
      </el-form-item>
      <el-form-item label="API Key">
        <el-input v-model="configForm.apiKey" type="password" show-password placeholder="请输入 API Key" />
      </el-form-item>
      <el-form-item label="启用">
        <el-switch v-model="configForm.enabled" />
      </el-form-item>
    </el-form>
    <div class="ai-provider-tips">
      <div v-if="configForm.provider === 'deepseek'">
        <b>DeepSeek 获取方式：</b>访问 <a href="https://platform.deepseek.com" target="_blank">platform.deepseek.com</a> → 注册 → API Keys → 创建
      </div>
      <div v-if="configForm.provider === 'qwen'">
        <b>通义千问获取方式：</b>访问 <a href="https://dashscope.aliyun.com" target="_blank">dashscope.aliyun.com</a> → 开通服务 → API-KEY管理
      </div>
      <div v-if="configForm.provider === 'glm'">
        <b>智谱GLM获取方式：</b>访问 <a href="https://open.bigmodel.cn" target="_blank">open.bigmodel.cn</a> → 注册 → API Keys
      </div>
    </div>
    <template #footer>
      <el-button @click="showConfig = false">取消</el-button>
      <el-button type="primary" @click="saveConfig" :loading="saving">保存并启用</el-button>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, reactive, onMounted, nextTick, watch } from 'vue'
import { Close } from '@element-plus/icons-vue'
import { getAiConfig, saveAiConfig, chatAi } from '../api'
import { ElMessage } from 'element-plus'

const showConfig = ref(false)
const showChat = ref(false)
const chatInput = ref('')
const chatMessages = ref([])
const chatLoading = ref(false)
const chatBody = ref(null)
const saving = ref(false)
const aiEnabled = ref(false)

const configForm = reactive({
  provider: 'deepseek',
  apiKey: '',
  enabled: false,
})

// Expose for parent to call
defineExpose({ openConfig: () => { showConfig.value = true } })

async function loadConfig() {
  try {
    const cfg = await getAiConfig()
    aiEnabled.value = cfg.enabled && cfg.hasKey
  } catch {}
}

async function saveConfig() {
  saving.value = true
  try {
    await saveAiConfig({ ...configForm })
    aiEnabled.value = configForm.enabled && !!configForm.apiKey
    showConfig.value = false
    ElMessage.success('AI 配置已保存')
  } catch { ElMessage.error('保存失败') }
  saving.value = false
}

async function sendChat() {
  const q = chatInput.value.trim()
  if (!q || chatLoading.value) return
  chatMessages.value.push({ role: 'user', content: q })
  chatInput.value = ''
  chatLoading.value = true
  await nextTick()
  if (chatBody.value) chatBody.value.scrollTop = chatBody.value.scrollHeight
  try {
    const resp = await chatAi({ messages: chatMessages.value.slice(-10) })
    chatMessages.value.push({ role: 'assistant', content: resp.result })
  } catch (e) {
    chatMessages.value.push({ role: 'assistant', content: '抱歉，AI 服务暂时不可用：' + (e.message || '未知错误') })
  }
  chatLoading.value = false
  await nextTick()
  if (chatBody.value) chatBody.value.scrollTop = chatBody.value.scrollHeight
}

onMounted(() => {
  loadConfig()
})
</script>

<style scoped>
.ai-floating { position: fixed; bottom: 24px; right: 24px; z-index: 1000; }
.ai-fab { width: 52px; height: 52px; box-shadow: 0 4px 16px rgba(0,0,0,0.2); }

.ai-chat-panel {
  position: absolute; bottom: 64px; right: 0;
  width: 360px; height: 460px;
  background: #fff; border-radius: 14px;
  box-shadow: 0 8px 32px rgba(0,0,0,0.18);
  display: flex; flex-direction: column; overflow: hidden;
}
.ai-chat-header {
  display: flex; justify-content: space-between; align-items: center;
  padding: 12px 16px; border-bottom: 1px solid #eee;
  font-weight: 600; font-size: 14px;
}
.ai-chat-body { flex: 1; overflow-y: auto; padding: 12px; }
.ai-msg { margin-bottom: 10px; display: flex; }
.ai-msg.user { justify-content: flex-end; }
.ai-msg.user .ai-msg-text { background: #409eff; color: #fff; border-radius: 14px 14px 4px 14px; }
.ai-msg.assistant .ai-msg-text { background: #f0f2f5; color: #303133; border-radius: 14px 14px 14px 4px; }
.ai-msg-text { padding: 10px 14px; max-width: 85%; font-size: 13px; line-height: 1.6; white-space: pre-wrap; }
.typing { color: #909399; font-style: italic; }

.ai-chat-input { display: flex; gap: 8px; padding: 10px 12px; border-top: 1px solid #eee; }

.ai-provider-tips { margin-top: 6px; font-size: 12px; color: #909399; line-height: 1.6; }
.ai-provider-tips a { color: #409eff; }

.fade-enter-active, .fade-leave-active { transition: all 0.25s; }
.fade-enter-from, .fade-leave-to { opacity: 0; transform: translateY(10px); }
</style>
