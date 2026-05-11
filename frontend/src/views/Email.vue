<template>
  <div class="email-container">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>邮箱推送配置</span>
          <el-switch
            v-model="alertStore.emailConfig.enabled"
            active-text="启用推送"
            inactive-text="停用推送"
            @change="handleToggle"
          />
        </div>
      </template>

      <el-alert
        title="邮箱推送说明"
        type="info"
        :closable="false"
        style="margin-bottom: 20px;"
      >
        <template #default>
          <p>配置邮箱推送后，当系统检测到无线攻击行为时，将自动向指定邮箱发送告警邮件。支持SMTP协议，兼容主流邮箱服务。</p>
        </template>
      </el-alert>

      <el-form :model="alertStore.emailConfig" label-width="120px" style="max-width: 600px;">
        <el-form-item label="SMTP服务器">
          <el-input v-model="alertStore.emailConfig.smtpHost" placeholder="例: smtp.qq.com" />
        </el-form-item>

        <el-form-item label="SMTP端口">
          <el-input-number v-model="alertStore.emailConfig.smtpPort" :min="1" :max="65535" />
          <span class="form-tip">常用端口: 465(SSL), 587(TLS), 25(普通)</span>
        </el-form-item>

        <el-divider />

        <el-form-item label="发件邮箱">
          <el-input v-model="alertStore.emailConfig.email" placeholder="例: your_email@qq.com" />
        </el-form-item>

        <el-form-item label="授权码">
          <el-input
            v-model="alertStore.emailConfig.authorizationCode"
            type="password"
            placeholder="请输入邮箱授权码"
            show-password
          />
          <span class="form-tip">授权码非邮箱密码，需在邮箱设置中生成</span>
        </el-form-item>

        <el-divider />

        <el-form-item label="收件邮箱">
          <el-input v-model="alertStore.emailConfig.recipientEmail" placeholder="例: admin@company.com" />
        </el-form-item>

        <el-form-item>
          <el-button type="primary" @click="saveConfig">保存配置</el-button>
          <el-button @click="testConnection">测试连接</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-card style="margin-top: 20px;">
      <template #header>
        <span>推送记录</span>
      </template>

      <el-table :data="pushRecords" style="width: 100%" stripe>
        <el-table-column prop="time" label="推送时间" width="180" />
        <el-table-column prop="alertType" label="告警类型" width="140" />
        <el-table-column prop="recipient" label="收件邮箱" width="200" />
        <el-table-column prop="status" label="推送状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.status === '成功' ? 'success' : 'danger'" size="small">
              {{ row.status }}
            </el-tag>
          </template>
        </el-table-column>
      </el-table>

      <el-empty v-if="pushRecords.length === 0" description="暂无推送记录" />
    </el-card>

    <el-card style="margin-top: 20px;">
      <template #header>
        <span>邮箱配置指南</span>
      </template>

      <el-collapse>
        <el-collapse-item title="QQ邮箱配置" name="qq">
          <div class="guide-content">
            <ol>
              <li>登录QQ邮箱网页版</li>
              <li>进入「设置」→「账户」</li>
              <li>找到「POP3/IMAP/SMTP/Exchange/CardDAV/CalDAV服务」</li>
              <li>开启「IMAP/SMTP服务」</li>
              <li>按提示发送短信获取授权码</li>
              <li>SMTP服务器: <code>smtp.qq.com</code>，端口: <code>465</code></li>
            </ol>
          </div>
        </el-collapse-item>

        <el-collapse-item title="163邮箱配置" name="163">
          <div class="guide-content">
            <ol>
              <li>登录163邮箱网页版</li>
              <li>进入「设置」→「POP3/SMTP/IMAP」</li>
              <li>开启「SMTP服务」</li>
              <li>生成授权码</li>
              <li>SMTP服务器: <code>smtp.163.com</code>，端口: <code>465</code></li>
            </ol>
          </div>
        </el-collapse-item>

        <el-collapse-item title="Gmail邮箱配置" name="gmail">
          <div class="guide-content">
            <ol>
              <li>登录Google账号</li>
              <li>进入「管理您的Google账号」→「安全性」</li>
              <li>开启「两步验证」</li>
              <li>生成应用专用密码</li>
              <li>SMTP服务器: <code>smtp.gmail.com</code>，端口: <code>587</code></li>
            </ol>
          </div>
        </el-collapse-item>
      </el-collapse>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useAlertStore } from '../store/alert'
import { ElMessage } from 'element-plus'

const alertStore = useAlertStore()

const pushRecords = ref([])

onMounted(() => {
  alertStore.fetchEmailConfig()
  refreshRecords()
})

async function refreshRecords() {
  try {
    await alertStore.fetchEmailRecords()
    pushRecords.value = alertStore.emailRecords
  } catch { /* ignore */ }
}

const handleToggle = async (enabled) => {
  try {
    await alertStore.updateEmailConfig({ ...alertStore.emailConfig, enabled })
    if (enabled) {
      ElMessage.success('邮箱推送已启用')
    } else {
      ElMessage.info('邮箱推送已停用')
    }
  } catch {
    alertStore.emailConfig.enabled = !enabled
    ElMessage.error('保存失败，请重试')
  }
}

const saveConfig = async () => {
  try {
    await alertStore.updateEmailConfig(alertStore.emailConfig)
    ElMessage.success('邮箱配置已保存')
  } catch {
    ElMessage.error('保存失败')
  }
}

const testConnection = async () => {
  if (!alertStore.emailConfig.email || !alertStore.emailConfig.authorizationCode) {
    ElMessage.warning('请先填写邮箱和授权码')
    return
  }

  ElMessage.info('正在测试连接...')
  try {
    const result = await alertStore.testEmail(alertStore.emailConfig)
    if (result.success) {
      ElMessage.success(result.message)
    } else {
      ElMessage.error(result.message)
    }
  } catch {
    ElMessage.error('连接测试失败')
  }
}
</script>

<style scoped>
.email-container {
  padding: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.form-tip {
  display: block;
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
}

.guide-content {
  padding: 10px;
}

.guide-content ol {
  padding-left: 20px;
}

.guide-content li {
  margin-bottom: 8px;
  line-height: 1.6;
}

.guide-content code {
  background: #f5f7fa;
  padding: 2px 6px;
  border-radius: 4px;
  color: #e6a23c;
  font-family: monospace;
}
</style>
