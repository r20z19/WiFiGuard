<template>
  <div class="topology-container">
    <div v-if="loading" class="loading-overlay">
      <el-icon class="loading-icon is-loading"><Loading /></el-icon>
      <span>加载网络拓扑...</span>
    </div>

    <!-- ====== Top bar ====== -->
    <div class="top-bar">
      <div class="top-left">
        <span class="room-label">🏠 室内网络拓扑</span>
        <el-tag :type="apOnline ? 'success' : 'warning'" effect="dark">{{ apOnline ? 'AP 在线' : 'AP 离线' }}</el-tag>
        <span class="top-info">设备 {{ devices.length }}</span>
        <span class="top-info" style="color:#67c23a">正常 {{ normalCount }}</span>
        <span v-if="activeAlerts.length" class="top-info" style="color:#f56c6c">攻击 {{ activeAlerts.length }}</span>
      </div>
      <div class="top-right">
        <el-button-group>
          <el-button @click="$router.push('/')"><el-icon :size="16"><Grid /></el-icon> 仪表盘</el-button>
          <el-button type="primary" disabled><el-icon :size="16"><House /></el-icon> 网络拓扑</el-button>
        </el-button-group>
      </div>
    </div>

    <!-- ====== Main area ====== -->
    <div class="main-area">
      <!-- LEFT panel -->
      <div class="left-panel">
        <div class="lp-section">
          <div class="lp-title">📊 实时概览</div>
          <div class="lp-stat-row">
            <div class="lp-stat">
              <span class="lps-val">{{ devices.length }}</span>
              <span class="lps-lbl">总设备</span>
            </div>
            <div class="lp-stat lp-stat-ok">
              <span class="lps-val">{{ normalCount }}</span>
              <span class="lps-lbl">正常</span>
            </div>
            <div class="lp-stat" :class="activeAlerts.length ? 'lp-stat-danger' : ''">
              <span class="lps-val">{{ activeAlerts.length }}</span>
              <span class="lps-lbl">告警</span>
            </div>
          </div>
        </div>
        <div class="lp-section">
          <div class="lp-title">📋 设备列表</div>
          <div class="lp-list">
            <div
              v-for="dev in devices" :key="dev.mac"
              class="lp-item"
              :class="{
                'lp-active': selectedMac === dev.mac,
                'lp-attacker': dev._dtype === 'attacker',
                'lp-target': dev._dtype === 'target'
              }"
              @click="selectDevice(dev)"
            >
              <img :src="getIconUrl(dev._dtype)" class="lp-icon" />
              <div class="lp-info">
                <div class="lp-name">{{ getTypeName(dev._dtype) }}</div>
                <div class="lp-mac">{{ dev.mac?.slice(-8) }}</div>
              </div>
              <div class="lp-right">
                <span v-for="b in signalBars(dev.signal)" :key="b" class="lp-bar" :class="'lp-bar-'+b"></span>
              </div>
            </div>
            <div v-if="devices.length === 0" class="lp-empty">暂无设备</div>
          </div>
        </div>
      </div>

      <!-- CENTER: Room -->
      <div class="room-area" ref="roomRef">
        <svg class="lines-layer">
          <line v-for="conn in connections" :key="conn.mac"
            :x1="apX" :y1="apY" :x2="conn.x" :y2="conn.y"
            :stroke="getDisplayColor(conn.colors) ? getDisplayColor(conn.colors) + '88' : '#4488ff22'"
            :stroke-width="conn.colors.length > 0 ? 2 : 1"
            :stroke-dasharray="conn.colors.length > 0 ? '8,4' : '10,6'"
            :class="['conn-line', conn.cls]"
          />
          <!-- AP↔device arrows at 1/3 position -->
          <template v-for="conn in connections.filter(c => c.direction === 'toDevice')" :key="'arr-td'+conn.mac">
            <polygon
              :points="calcArrowAt(apX, apY, conn.x, conn.y, 1/3)"
              :fill="getDisplayColor(conn.colors) ? getDisplayColor(conn.colors) + 'cc' : '#ff4444cc'"
              :class="['arrow-head', 'attack-active']"
            />
          </template>
          <template v-for="conn in connections.filter(c => c.direction === 'toAP')" :key="'arr-ta'+conn.mac">
            <polygon
              :points="calcArrowAt(conn.x, conn.y, apX, apY, 1/3)"
              :fill="getDisplayColor(conn.colors) ? getDisplayColor(conn.colors) + 'cc' : '#ff4444cc'"
              :class="['arrow-head', 'attack-active']"
            />
          </template>
          <line v-for="(atk, i) in attackLines" :key="'atk'+i"
            :x1="atk.x1" :y1="atk.y1" :x2="atk.x2" :y2="atk.y2"
            :stroke="atk.color + 'cc'"
            :stroke-width="atk.status === 'blocked' ? 1 : 2.5"
            :class="['attack-line', atk.status === 'blocked' ? '' : 'attack-active']"
          />
          <!-- Attacker→victim arrows at 1/3 from attacker toward victim -->
          <polygon
            v-for="(atk, i) in attackLines"
            :key="'arrow-atk'+i"
            :points="calcArrowAt(atk.x1, atk.y1, atk.x2, atk.y2, 1/3)"
            :fill="atk.color + 'ff'"
            :class="['arrow-head', atk.status === 'blocked' ? '' : 'attack-active']"
          />
        </svg>

        <div class="room-walls">
          <!-- Wall texture lines -->
          <div class="wall-top"></div>
          <div class="wall-bottom"></div>

          <!-- Door indicators -->
          <div class="door door-left"></div>
          <div class="door door-right"></div>

          <!-- Wall-mounted info displays -->
          <div class="wall-display wd-top">
            <span class="wd-icon">📶</span>
            <span class="wd-text">WiFi 网络</span>
            <span class="wd-sub">{{ apDevice?.pairwiseCipher || 'WPA2' }} 加密</span>
          </div>
          <div class="wall-display wd-bottom">
            <span class="wd-icon">⏱</span>
            <span class="wd-text">实时监控中</span>
            <span class="wd-sub">{{ new Date().toLocaleTimeString('zh-CN', {hour:'2-digit',minute:'2-digit'}) }}</span>
          </div>

          <!-- Floor with grid + signal zones -->
          <div class="floor-grid">
            <!-- Signal zones -->
            <div class="sig-zone zone-1"><span class="zone-label">优</span></div>
            <div class="sig-zone zone-2"><span class="zone-label">良</span></div>
            <div class="sig-zone zone-3"><span class="zone-label">中</span></div>
            <div class="sig-zone zone-4"><span class="zone-label">弱</span></div>
          </div>

          <!-- ====== FURNITURE (richer, more visible) ====== -->
          <div class="furn desk-area">
            <div class="furn-desk"></div>
            <div class="furn-desk-chair"></div>
            <div class="furn-label">🪑 办公区</div>
          </div>
          <div class="furn sofa-area">
            <div class="furn-sofa"></div>
            <div class="furn-coffee-table"></div>
            <div class="furn-label">🛋 客厅沙发</div>
          </div>
          <div class="furn tv-area">
            <div class="furn-tv-stand"></div>
            <div class="furn-label">📺 电视柜</div>
          </div>
          <div class="furn shelf-area">
            <div class="furn-shelf"></div>
            <div class="furn-label">📚 书架</div>
          </div>
          <div class="furn dining-area">
            <div class="furn-dining-table"></div>
            <div class="furn-label">🍽 餐桌</div>
          </div>
          <div class="furn plant-1"><span>🪴</span></div>
          <div class="furn plant-2"><span>🌿</span></div>
          <div class="furn rug"></div>

          <!-- AP Center -->
          <div class="ap-center" :class="{ 'ap-alert': activeAlerts.length > 0 }">
            <div class="ap-icon-wrap">
              <img :src="iconImgs.router" class="ap-icon-img" />
            </div>
            <div class="ap-label">AP 接入点</div>
            <div class="ap-mac">{{ apDevice?.mac || '—' }}</div>
            <div class="signal-ring ring-1"></div>
            <div class="signal-ring ring-2"></div>
            <div class="signal-ring ring-3"></div>
            <div class="signal-ring ring-4"></div>
          </div>
        </div>

        <!-- Device cards -->
        <div
          v-for="dev in positionedDevices" :key="dev.mac"
          class="device-card"
          :class="[
            dev._dtype === 'attacker' ? 'card-attacker' : '',
            dev._dtype === 'target' ? 'card-target' : '',
            selectedMac === dev.mac ? 'card-selected' : '',
            attacksForDevice(dev.mac).length > 0 && dev._dtype !== 'attacker' ? 'card-under-attack' : '',
          ]"
          :style="{ left: dev._x + 'px', top: dev._y + 'px' }"
          @click.stop="selectDevice(dev)"
          @mouseenter="hoverDevice(dev, $event)"
          @mouseleave="hoveredMac = null"
        >
          <!-- Attack flash + status badges + count -->
          <div v-if="dev._dtype === 'attacker'" class="attack-flash"></div>
          <div
            v-for="(st, si) in getDeviceStatuses(dev)"
            :key="si"
            class="device-status-badge"
            :class="st.cls"
            :style="{ top: (-10 - si * 22) + 'px' }"
          >{{ st.text }}</div>
          <div
            v-if="attacksForDevice(dev.mac).length > 0"
            class="attack-count-badge"
          >{{ attacksForDevice(dev.mac).length }}</div>
          <img :src="getIconUrl(dev._dtype)" class="card-icon" />
          <div class="card-name">{{ getTypeName(dev._dtype) }}</div>
          <div class="card-mac">{{ dev.mac?.slice(-8) }}</div>
          <div class="card-signal">
            <span v-for="b in signalBars(dev.signal)" :key="b" class="sig-bar" :class="'bar-'+b"></span>
            <span class="sig-dbm">{{ dev.signal }}</span>
          </div>
          <div class="card-dist">≈ {{ calcDistance(dev).text }}</div>
        </div>

        <!-- Attackers outside -->
        <div
          v-for="atk in positionedAttackers" :key="atk.mac"
          class="attacker-outer"
          :class="[
            { 'card-selected': selectedMac === atk.mac },
            getAttackStatus(atk) === 'blocked' ? 'attacker-blocked' : 'attacker-active',
          ]"
          :style="{ left: atk._x + 'px', top: atk._y + 'px' }"
          @click.stop="selectDevice(atk)"
          @mouseenter="hoverDevice(atk, $event)"
          @mouseleave="hoveredMac = null"
        >
          <div v-if="getAttackStatus(atk) === 'attacking'" class="attack-flash-outer"></div>
          <div
            v-for="(st, si) in getDeviceStatuses(atk)"
            :key="si"
            class="device-status-badge"
            :class="st.cls"
            :style="{ top: (-26 - si * 22) + 'px' }"
          >{{ st.text }}</div>
          <div
            v-if="attacksForDevice(atk.mac).length > 0"
            class="attack-count-badge"
            style="top:-8px;right:-8px"
          >{{ attacksForDevice(atk.mac).length }}</div>
          <img :src="iconImgs.attacker" class="atk-icon" />
          <div class="atk-label">攻击者</div>
          <div class="atk-mac">{{ atk.mac?.slice(-8) }}</div>
        </div>

        <!-- Hover tooltip -->
        <div v-if="hoveredMac && hoveredDevice"
          class="hover-card"
          :style="{ left: hoverX + 14 + 'px', top: hoverY - 14 + 'px' }"
        >
          <div class="hc-head">
            <img :src="getIconUrl(hoveredDevice._dtype)" class="hc-icon" />
            <span>{{ getTypeName(hoveredDevice._dtype) }}</span>
          </div>
          <div class="hc-row"><span>MAC</span><span class="mono">{{ hoveredDevice.mac }}</span></div>
          <div class="hc-row"><span>IP</span><span>{{ hoveredDevice.ip || '-' }}</span></div>
          <div class="hc-row"><span>信号</span><span>{{ hoveredDevice.signal }} dBm</span></div>
          <div class="hc-row"><span>距AP</span><span>≈ {{ calcDistance(hoveredDevice).text }}</span></div>
        </div>
      </div>

      <!-- RIGHT: Always-visible summary + detail -->
      <div class="right-panel" :class="{ 'rp-expanded': detailDevice && deviceAlerts.length > 0 }">
        <!-- === DEVICE SELECTED: Show full attack details === -->
        <template v-if="detailDevice">
          <div class="rp-section">
            <div class="rp-dev-header">
              <img :src="getIconUrl(detailDevice._dtype)" class="rp-dev-icon-sm" />
              <div>
                <div class="rp-dev-name-sm">{{ getTypeName(detailDevice._dtype) }}</div>
                <div class="rp-dev-mac-sm">{{ detailDevice.mac }}</div>
              </div>
              <el-button :icon="Close" circle size="small" text @click="detailDevice = null; selectedMac = null" />
            </div>
            <div class="rp-dev-meta">
              <div class="rp-meta-item"><span>IP</span><span class="mono">{{ detailDevice.ip || '-' }}</span></div>
              <div class="rp-meta-item"><span>信号</span><span :style="{color:sigColor(detailDevice.signal)}">{{ detailDevice.signal }} dBm</span></div>
              <div class="rp-meta-item"><span>距AP</span><span>≈ {{ calcDistance(detailDevice).text }}</span></div>
              <div class="rp-meta-item"><span>SSID</span><span>{{ detailDevice.ssid || '-' }}</span></div>
              <div class="rp-meta-item"><span>厂商</span><span>{{ detailDevice.vendor || '-' }}</span></div>
              <div class="rp-meta-item"><span>加密</span><span>{{ detailDevice.pairwiseCipher || '-' }}</span></div>
            </div>
            <div class="rp-actions">
              <el-button type="danger" size="small" @click="quickBlacklist(detailDevice)" :disabled="alertStore.accessListMode !== 'blacklist'">{{ alertStore.accessListMode === 'blacklist' ? '加入黑名单' : '黑名单未启用' }}</el-button>
              <el-button type="success" size="small" @click="quickWhitelist(detailDevice)" :disabled="alertStore.accessListMode !== 'whitelist'">{{ alertStore.accessListMode === 'whitelist' ? '加入白名单' : '白名单未启用' }}</el-button>
            </div>
          </div>

          <!-- ATTACK DETAILS for selected device -->
          <div class="rp-section" v-if="deviceAlerts.length > 0">
            <div class="rp-title danger">
              🚨 该设备检测到 {{ deviceAlerts.length }} 条攻击
            </div>
            <div
              v-for="a in deviceAlerts"
              :key="a.id"
              class="attack-detail-card"
              :class="'atk-severity-' + a.severity"
            >
              <div class="adc-header">
                <el-tag :type="sevType(a.severity)" size="small">{{ sevLabel(a.severity) }}</el-tag>
                <span class="adc-type">{{ a.type }}</span>
                <span class="adc-time">{{ formatTime(a.timestamp) }}</span>
              </div>
              <div class="adc-body">
                <div class="adc-row">
                  <span class="adc-label">攻击源 MAC</span>
                  <span class="mono">{{ a.sourceMac || '-' }}</span>
                </div>
                <div class="adc-row">
                  <span class="adc-label">目标 MAC</span>
                  <span class="mono">{{ a.targetMac || '-' }}</span>
                </div>
                <div class="adc-row" v-if="a.suggestion">
                  <span class="adc-label">处置建议</span>
                  <span class="adc-suggestion">{{ a.suggestion }}</span>
                </div>
              </div>
              <div class="adc-actions">
                <el-button size="small" type="danger" plain @click="quickBlacklist({mac: a.sourceMac, name: a.sourceMac})">
                  拉黑攻击源
                </el-button>
              </div>
            </div>
          </div>
          <div class="rp-section" v-else>
            <div class="rp-title" style="color:#67c23a">✅ 该设备无攻击记录</div>
            <div class="rp-safe-msg-sm">此设备当前安全，未检测到异常</div>
          </div>
        </template>

        <!-- === NO DEVICE SELECTED: Show overview === -->
        <template v-else>
          <div class="rp-section" v-if="activeAlerts.length > 0">
            <div class="rp-title danger">🚨 活跃告警 ({{ activeAlerts.length }})</div>
            <div v-for="a in activeAlerts.slice(0,5)" :key="a.id" class="rp-alert-item">
              <div>
                <div class="rp-alert-type">{{ a.type }}</div>
                <div class="rp-alert-mac">{{ a.sourceMac?.slice(-8) }} → {{ (a.targetMac || '?').slice(-8) }}</div>
              </div>
              <el-tag :type="sevType(a.severity)" size="small">{{ sevLabel(a.severity) }}</el-tag>
            </div>
          </div>
          <div class="rp-section" v-else>
            <div class="rp-title" style="color:#67c23a">✅ 安全状态</div>
            <div class="rp-safe-msg">
              <span class="rp-safe-icon">🛡️</span>
              <span>当前网络无异常攻击</span>
              <span class="rp-safe-sub">系统持续监控中</span>
            </div>
          </div>
          <div class="rp-section">
            <div class="rp-title">📊 设备类型统计</div>
            <div class="rp-bar-item"><span>📡 路由器</span><span class="rp-bar-val">1</span></div>
            <div class="rp-bar-item"><span>👤 用户设备</span><span class="rp-bar-val">{{ deviceTypeCounts.pc + deviceTypeCounts.phone }}</span></div>
            <div class="rp-bar-item" v-if="deviceTypeCounts.attacker > 0"><span>⚠️ 攻击者</span><span class="rp-bar-val" style="color:#f56c6c">{{ deviceTypeCounts.attacker }}</span></div>
          </div>
          <div class="rp-section">
            <div class="rp-title">📶 信号参考</div>
            <div class="rp-sig-row" v-for="s in sigRefs" :key="s.label">
              <span class="rp-sig-bars"><i v-for="b in 4" :key="b" class="sb" :class="b <= s.bars ? 'sb'+s.bars : 'sboff'"></i></span>
              <span>{{ s.label }}</span>
            </div>
          </div>
        </template>
      </div>
    </div>

    <!-- Bottom bar -->
    <div class="bottom-bar">
      <span class="bb-item"><img :src="iconImgs.router" class="bb-icon" /> AP</span>
      <span class="bb-item"><img :src="iconImgs.pc" class="bb-icon" /> PC</span>
      <span class="bb-item"><img :src="iconImgs.phone" class="bb-icon" /> 手机</span>
      <span class="bb-item"><img :src="iconImgs.attacker" class="bb-icon" /> 攻击者</span>
      <span class="bb-sep">|</span>
      <span class="bb-item"><span class="bb-dot green"></span> 连接</span>
      <span class="bb-item"><span class="bb-dot red pulse"></span> 攻击</span>
      <span class="bb-item"><span class="bb-dot green ring-pulse"></span> 信号波纹</span>
      <span class="bb-sep">|</span>
      <span class="bb-item" style="color:#556677;font-style:italic">💡 点击设备卡片查看详情 · 缩放浏览器可调整视图</span>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, nextTick } from 'vue'
import { Close } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { getNetworkLocations } from '../api/index'
import { useAlertStore } from '../store/alert'
import DEVICE_ICONS from '../assets/deviceIcons.json'

const loading = ref(true)
const roomRef = ref(null)
const devices = ref([])
const activeAlerts = ref([])
const selectedMac = ref(null)
const hoveredMac = ref(null)
const hoveredDevice = ref(null)
const hoverX = ref(0); const hoverY = ref(0)
const detailDevice = ref(null)

let pollTimer = null
let colorCycleTimer = null
const alertStore = useAlertStore()
const iconImgs = {}
for (const [k, v] of Object.entries(DEVICE_ICONS)) iconImgs[k] = v.replace('image://', '')

// ---- Room size ----
const apX = ref(0); const apY = ref(0)
let ROOM_W = 800; let ROOM_H = 500
let AP_X = 400; let AP_Y = 250
const ROOM_PAD = 60

function updateRoomSize() {
  if (!roomRef.value) return
  ROOM_W = roomRef.value.clientWidth
  ROOM_H = roomRef.value.clientHeight
  AP_X = ROOM_W / 2; AP_Y = ROOM_H / 2
  apX.value = AP_X; apY.value = AP_Y
}

// ---- Computed ----
const deviceTypeCounts = computed(() => ({
  router: devices.value.filter(d => d._dtype === 'router').length,
  pc: devices.value.filter(d => d._dtype === 'pc').length,
  phone: devices.value.filter(d => d._dtype === 'phone').length,
  attacker: devices.value.filter(d => d._dtype === 'attacker').length,
}))

// Attacks targeting each device
function attacksForDevice(mac) {
  return activeAlerts.value.filter(a => a.targetMac === mac || a.sourceMac === mac)
}

const apOnline = computed(() => devices.value.some(d => d._dtype === 'router'))
const apDevice = computed(() => devices.value.find(d => d._dtype === 'router') || devices.value[0] || { mac: '—' })
const normalCount = computed(() => devices.value.filter(d => d.status === '正常').length)
const deviceAlerts = computed(() => {
  if (!detailDevice.value) return []
  return activeAlerts.value.filter(a => a.sourceMac === detailDevice.value.mac || a.targetMac === detailDevice.value.mac)
})

// ---- Helpers ----
function getIconUrl(t) { return (DEVICE_ICONS[t] || DEVICE_ICONS['default']).replace('image://', '') }
function getTypeName(t) {
  return { router: '路由器', pc: '用户设备', phone: '用户设备', attacker: '攻击者' }[t] || '设备'
}
function sevType(s) { return {critical:'danger',high:'danger',medium:'warning',low:'success'}[s]||'info' }
function sevLabel(s) { return {critical:'严重',high:'高危',medium:'中危',low:'低危'}[s]||s }
function sigColor(s) { if (s >= -50) return '#67c23a'; if (s >= -70) return '#e6a23c'; return '#f56c6c' }
function signalBars(s) { if (s>=-50) return[1,2,3,4]; if(s>=-60) return[1,2,3]; if(s>=-70) return[1,2]; return[1] }

// Room-scale distance: maps the device's actual visual position to real-world meters.
// Assumes a typical home room is ~12m across, so maxRadius maps to ~6m.
const ROOM_SCALE = 6 / 300  // 300px ≈ 6m real distance (adjust based on typical room size)

function calcDistance(dev) {
  // Use the device's actual visual position relative to AP center
  if (!dev || dev._x === undefined) return { text: '?m', val: 0 }
  const dx = (dev._x + 70) - AP_X  // card center X
  const dy = (dev._y + 42) - AP_Y  // card center Y
  const pxDist = Math.sqrt(dx * dx + dy * dy)
  const meters = pxDist * ROOM_SCALE
  if (meters < 0.5) return { text: '<0.5m', val: 0.3 }
  if (meters < 1) return { text: meters.toFixed(1) + 'm', val: meters }
  return { text: Math.round(meters) + 'm', val: meters }
}

function formatTime(ts) {
  if (!ts) return ''
  try {
    const d = new Date(ts)
    const now = new Date()
    const diffMs = now - d
    const mins = Math.floor(diffMs / 60000)
    if (mins < 1) return '刚刚'
    if (mins < 60) return mins + '分钟前'
    if (mins < 1440) return Math.floor(mins / 60) + '小时前'
    return d.toLocaleString('zh-CN', { month: 'numeric', day: 'numeric', hour: '2-digit', minute: '2-digit' })
  } catch { return ts }
}
const sigRefs = [
  { bars: 4, label: '≥ -50dBm 优秀' },
  { bars: 3, label: '-50~-60 良好' },
  { bars: 2, label: '-60~-70 一般' },
  { bars: 1, label: '< -70 弱' },
]

// ---- Classification (simplified: AP, Users, Attackers) ----
let _routerMac = null  // track the one router MAC
function classify(d, allDevs) {
  // Attackers: blacklisted devices
  if (d.type === 'blacklisted') return 'attacker'
  // Only ONE router: first device with SSID or AP type
  if (d.type === 'ap' || (d.ssid && d.status === '正常')) {
    if (!_routerMac || _routerMac === d.mac) {
      _routerMac = d.mac
      return 'router'
    }
    // Other router-like devices → treat as users
  }
  const v = (d.vendor || '').toLowerCase()
  if (/apple|samsung|xiaomi|oppo|vivo|oneplus|huawei|google/.test(v)) return 'phone'
  if (/dell|lenovo|hp|intel|asustek|acer|microsoft|msi/.test(v)) return 'pc'
  return 'pc'
}

// Attack status derived from alerts + blacklist
function getAttackStatus(dev) {
  const alerts = activeAlerts.value.filter(a => a.sourceMac === dev.mac)
  if (alerts.length === 0) {
    if (dev.type === 'blacklisted') return 'blocked'
    return null
  }
  return 'attacking'
}

// Device status badges (can have multiple simultaneously)
function getDeviceStatuses(dev) {
  const statuses = []
  // Is this device an attacker?
  if (activeAlerts.value.some(a => a.sourceMac === dev.mac)) {
    statuses.push({ text: '⚡ 攻击中', cls: 'status-attacking' })
  }
  // Is this device being attacked?
  if (activeAlerts.value.some(a => a.targetMac === dev.mac)) {
    statuses.push({ text: '🎯 被攻击', cls: 'status-targeted' })
  }
  // Blacklisted but no active alerts
  if (dev.type === 'blacklisted' && statuses.length === 0) {
    statuses.push({ text: '🚫 已踢出', cls: 'status-blocked' })
  }
  return statuses
}

// ====== SECTOR-BASED SPREAD ======
const CARD_W = 155; const CARD_H = 100
// Inner rings (excellent/good signal) larger → more room for devices
// Outer rings (medium/poor) compressed → overall tighter, more orderly
// Spread across 优50% + 良25% + 中15% + 弱10%
const ringRatios = [0.10, 0.28, 0.45, 0.58, 0.68, 0.78, 0.88]

function calcRingPositions(devs) {
  const n = devs.length
  if (n === 0) return []
  const maxR = Math.min(ROOM_W, ROOM_H) / 2 - ROOM_PAD
  const sorted = [...devs].sort((a, b) => (b.signal || -70) - (a.signal || -70))
  const results = []
  for (let i = 0; i < n; i++) {
    const d = sorted[i]
    const sig = d.signal || -65
    const sigNorm = Math.max(0, Math.min(1, (sig + 90) / 60))
    const posRatio = i / n
    const blended = sigNorm * 0.7 + posRatio * 0.3
    const ringIdx = Math.min(ringRatios.length - 1, Math.floor(blended * ringRatios.length))
    const r = maxR * ringRatios[ringIdx]
    const baseAngle = (i / n) * Math.PI * 2
    const ringOffset = ringIdx * 0.3
    const angle = baseAngle + ringOffset
    results.push({ device: d, x: AP_X + Math.cos(angle) * r - 70, y: AP_Y + Math.sin(angle) * r - 42 })
  }
  return results
}

const positionedDevices = computed(() => {
  // Only users (non-router, non-attacker). Only ONE router at center.
  const normal = devices.value.filter(d => d._dtype !== 'attacker' && d._dtype !== 'router')
  return calcRingPositions(normal).map(p => ({ ...p.device, _x: p.x, _y: p.y }))
})

const positionedAttackers = computed(() => {
  const attackers = devices.value.filter(d => d._dtype === 'attacker')
  const n = attackers.length
  if (n === 0) return []
  return attackers.map((d, i) => {
    const side = i % 2
    const perRow = Math.ceil(n / 2)
    const idxInRow = Math.floor(i / 2)
    const x = 80 + (ROOM_W - 160) * ((idxInRow + 0.5) / perRow)
    const y = side === 0 ? -40 : ROOM_H + 10
    return { ...d, _x: x - 50, _y: y }
  })
})

// Color palette for different attacks
const ATTACK_COLORS = ['#ff2222', '#ff8800', '#ffdd00', '#ff44cc', '#44ddff', '#ff6644']

// Multi-color cycling state
const colorCycleIndex = ref(0)

// Assign a stable color to each unique source→target attack pair.
// Colors are stored directly on the alert object so all lookups are consistent.
function assignAlertColors(alerts) {
  const pairColors = new Map()
  let nextIdx = 0
  for (const a of alerts) {
    const key = (a.sourceMac || '?') + '→' + (a.targetMac || '?')
    if (!pairColors.has(key)) {
      pairColors.set(key, ATTACK_COLORS[nextIdx % ATTACK_COLORS.length])
      nextIdx++
    }
    a._color = pairColors.get(key)
  }
}

// Get all distinct colors for alerts involving this device
function getConnectionColors(mac) {
  const colors = []
  for (const a of activeAlerts.value) {
    if ((a.sourceMac === mac || a.targetMac === mac) && a._color) {
      if (!colors.includes(a._color)) colors.push(a._color)
    }
  }
  return colors
}

function getConnectionClass(mac) {
  const srcAlerts = activeAlerts.value.filter(a => a.sourceMac === mac)
  const tgtAlerts = activeAlerts.value.filter(a => a.targetMac === mac)
  if (srcAlerts.length > 0) return 'conn-attacking'
  if (tgtAlerts.length > 0) return 'conn-targeted'
  return ''
}

const connections = computed(() =>
  positionedDevices.value.map(d => {
    const srcAlerts = activeAlerts.value.filter(a => a.sourceMac === d.mac)
    const tgtAlerts = activeAlerts.value.filter(a => a.targetMac === d.mac)
    let direction = null  // null=no arrow, 'toDevice'=AP→device, 'toAP'=device→AP
    if (tgtAlerts.length > 0 && srcAlerts.length === 0) direction = 'toDevice'
    if (srcAlerts.length > 0) direction = 'toAP'
    return {
      mac: d.mac, x: d._x + 70, y: d._y + 42,
      colors: getConnectionColors(d.mac),
      cls: getConnectionClass(d.mac),
      direction,
    }
  })
)

// Cycle multi-color lines: one color per second, cycling through all colors
function getDisplayColor(colors) {
  if (colors.length === 0) return null
  if (colors.length === 1) return colors[0]  // single attack: always same color
  // Multiple attacks: cycle one color per second
  return colors[colorCycleIndex.value % colors.length]
}

// Arrow at specific fraction along a line (0=from x1, 1=at x2)
// Points from source toward target
function calcArrowAt(x1, y1, x2, y2, fraction) {
  const dx = x2 - x1, dy = y2 - y1
  const len = Math.sqrt(dx*dx + dy*dy) || 1
  const ux = dx / len, uy = dy / len
  // Arrow tip at fraction point
  const px_f = x1 + dx * fraction, py_f = y1 + dy * fraction
  const tipX = px_f + ux * 7
  const tipY = py_f + uy * 7
  const baseX = px_f - ux * 8
  const baseY = py_f - uy * 8
  const wing = -uy * 5, wingY = ux * 5
  return `${tipX},${tipY} ${baseX+wing},${baseY+wingY} ${baseX-wing},${baseY-wingY}`
}

// Find victim device position (may be in users or attackers list)
function findDevicePos(mac) {
  const dev = positionedDevices.value.find(d => d.mac === mac)
  if (dev) return { x: dev._x + 70, y: dev._y + 42 }
  const atk = positionedAttackers.value.find(d => d.mac === mac)
  if (atk) return { x: atk._x + 50, y: atk._y + 30 }
  return null
}

const attackLines = computed(() => {
  const lines = []
  const seen = new Set()
  for (const a of activeAlerts.value) {
    const src = positionedAttackers.value.find(d => d.mac === a.sourceMac)
    if (!src || seen.has(a.sourceMac)) continue
    seen.add(a.sourceMac)
    const victimPos = findDevicePos(a.targetMac)
    lines.push({
      x1: src._x + 50, y1: src._y + 30,
      x2: victimPos ? victimPos.x : AP_X,
      y2: victimPos ? victimPos.y : AP_Y,
      attacker: src,
      status: getAttackStatus(src),
      color: a._color || '#ff2222',
    })
  }
  return lines
})

// ---- Interaction ----
function selectDevice(dev) {
  if (selectedMac.value === dev.mac) { selectedMac.value = null; detailDevice.value = null }
  else { selectedMac.value = dev.mac; detailDevice.value = dev }
}
function hoverDevice(dev, ev) { hoveredMac.value = dev.mac; hoveredDevice.value = dev; hoverX.value = ev.clientX; hoverY.value = ev.clientY }
async function quickBlacklist(d) {
  if (alertStore.accessListMode !== 'blacklist') { ElMessage.warning('请先在黑名单页面开启黑名单模式'); return }
  try { await alertStore.addToBlacklist({ mac: d.mac, name: d.mac, reason: '拓扑添加' }) } catch {}
}
async function quickWhitelist(d) {
  if (alertStore.accessListMode !== 'whitelist') { ElMessage.warning('请先在白名单页面开启白名单模式'); return }
  try { await alertStore.addToWhitelist({ mac: d.mac, name: d.mac }) } catch {}
}

// ---- Fetch ----
async function fetchData() {
  try {
    const data = await getNetworkLocations()
    _routerMac = null
    const raw = (data.devices || []).map(d => ({ ...d, _dtype: classify(d) }))
    const alerts = data.alerts || []
    assignAlertColors(alerts)  // assign _color to each alert before reactive updates
    devices.value = raw; activeAlerts.value = alerts
    loading.value = false
  } catch (e) { console.error(e); loading.value = false }
}

onMounted(async () => {
  await nextTick(); updateRoomSize()
  window.addEventListener('resize', updateRoomSize)
  await fetchData()
  pollTimer = setInterval(fetchData, 10000)
  // Color cycle for multi-attack lines: switch every 1s
  colorCycleTimer = setInterval(() => { colorCycleIndex.value++ }, 1000)
})
onUnmounted(() => {
  if (pollTimer) clearInterval(pollTimer)
  if (colorCycleTimer) clearInterval(colorCycleTimer)
  window.removeEventListener('resize', updateRoomSize)
})
</script>

<style scoped>
.topology-container {
  width: 100%; height: calc(100vh - 60px);
  background: #0d1520; overflow: hidden; position: relative;
  font-family: 'Segoe UI', system-ui, sans-serif;
}
.loading-overlay {
  position: absolute; inset: 0; z-index: 200; display: flex; flex-direction: column;
  align-items: center; justify-content: center; gap: 14px;
  background: rgba(13,21,32,0.97); color: #88ccff; font-size: 20px;
}
.loading-icon { font-size: 56px; color: #4488ff; }

/* ====== TOP BAR ====== */
.top-bar {
  display: flex; justify-content: space-between; align-items: center;
  height: 46px; padding: 0 20px;
  background: rgba(255,255,255,0.03); border-bottom: 1px solid rgba(255,255,255,0.05);
}
.top-left { display: flex; align-items: center; gap: 14px; }
.room-label { font-size: 16px; font-weight: 600; color: #ccd8e8; }
.top-info { font-size: 13px; color: #8899aa; }
.top-right { display: flex; gap: 8px; }

/* ====== MAIN LAYOUT: 3 columns ====== */
.main-area {
  position: absolute; top: 46px; left: 0; right: 0; bottom: 40px;
  display: flex; gap: 0;
}

/* ====== LEFT PANEL (220px) ====== */
.left-panel {
  width: 220px; flex-shrink: 0;
  background: rgba(255,255,255,0.015); border-right: 1px solid rgba(255,255,255,0.05);
  display: flex; flex-direction: column; overflow-y: auto;
}
.lp-section { padding: 10px 12px; border-bottom: 1px solid rgba(255,255,255,0.04); }
.lp-title { font-size: 12px; font-weight: 700; color: #778899; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 8px; }
.lp-stat-row { display: flex; gap: 8px; }
.lp-stat {
  flex: 1; text-align: center; padding: 10px 4px;
  background: rgba(255,255,255,0.02); border-radius: 8px;
  border: 1px solid rgba(255,255,255,0.04);
}
.lp-stat-ok { border-color: rgba(103,194,58,0.15); }
.lp-stat-danger { border-color: rgba(245,108,108,0.2); }
.lps-val { display: block; font-size: 22px; font-weight: 700; color: #ccd8e8; }
.lp-stat-ok .lps-val { color: #67c23a; }
.lp-stat-danger .lps-val { color: #f56c6c; }
.lps-lbl { display: block; font-size: 10px; color: #778899; margin-top: 2px; }

.lp-list { flex: 1; overflow-y: auto; }
.lp-item {
  display: flex; align-items: center; gap: 8px;
  padding: 7px 10px; cursor: pointer; transition: all 0.15s;
  border-bottom: 1px solid rgba(255,255,255,0.015); border-radius: 6px; margin: 2px 4px;
}
.lp-item:hover { background: rgba(68,136,255,0.08); }
.lp-active { background: rgba(68,136,255,0.15) !important; border-left: 3px solid #4488ff; }
.lp-attacker { border-left: 3px solid rgba(255,68,68,0.3); }
.lp-target { border-left: 3px solid rgba(255,170,0,0.3); }
.lp-icon { width: 22px; height: 22px; flex-shrink: 0; }
.lp-info { flex: 1; min-width: 0; }
.lp-name { font-size: 12px; font-weight: 600; color: #ccd8e8; }
.lp-mac { font-size: 10px; color: #667788; font-family: monospace; }
.lp-right { display: flex; align-items: flex-end; gap: 1px; flex-shrink: 0; }
.lp-bar { width: 3px; border-radius: 1px; background: #334455; }
.lp-bar-1 { height: 5px; } .lp-bar-2 { height: 8px; } .lp-bar-3 { height: 11px; background: #e6a23c; } .lp-bar-4 { height: 14px; background: #67c23a; }
.lp-empty { text-align: center; padding: 30px; color: #556677; font-size: 13px; }

/* ====== ROOM ====== */
.room-area {
  flex: 1; position: relative; overflow: hidden;
  margin: 8px 8px 8px 8px;
}
.lines-layer { position: absolute; inset: 0; width: 100%; height: 100%; pointer-events: none; z-index: 12; }
.conn-line { transition: stroke 0.3s, stroke-width 0.3s; }
.conn-attacking { animation: conn-pulse 1s ease-in-out infinite; }
.conn-targeted { animation: conn-pulse 1s ease-in-out infinite; }
@keyframes conn-pulse {
  0%,100% { opacity: 0.3; }
  50% { opacity: 1; }
}

.attack-line { stroke-dasharray: 10,6; }
.attack-active { animation: atk-full 1s ease-in-out infinite; }
@keyframes atk-full {
  0%,100% { stroke-dashoffset: 0; opacity: 0.3; }
  50% { stroke-dashoffset: -16; opacity: 1; }
  100% { stroke-dashoffset: -32; }
}

.arrow-head { animation: arrow-blink 1s ease-in-out infinite; }
@keyframes arrow-blink {
  0%,100% { opacity: 0.25; }
  50% { opacity: 1; }
}

/* Room walls + inner details */
.room-walls {
  position: absolute; inset: 0;
  border: 3px solid #2a3a5a; border-radius: 16px;
  background: #111a28;
  box-shadow: inset 0 0 120px rgba(0,0,0,0.5), 0 0 0 8px #0a1220, 0 0 0 10px #1a2840;
  overflow: hidden;
}
.wall-top, .wall-bottom {
  position: absolute; left: 0; right: 0; height: 14px;
  background: repeating-linear-gradient(90deg, transparent, transparent 8px, rgba(68,136,255,0.03) 8px, rgba(68,136,255,0.03) 9px);
}
.wall-top { top: 0; } .wall-bottom { bottom: 0; }

/* Doors */
.door {
  position: absolute; width: 6px; height: 55px;
  background: rgba(68,136,255,0.08); border-radius: 3px;
}
.door-left { left: -3px; top: 50%; transform: translateY(-50%); }
.door-right { right: -3px; top: 50%; transform: translateY(-50%); }

/* Wall displays */
.wall-display {
  position: absolute; z-index: 3;
  background: rgba(0,0,0,0.4); border: 1px solid rgba(68,136,255,0.15);
  border-radius: 8px; padding: 8px 14px;
  display: flex; flex-direction: column; align-items: center;
}
.wd-top { top: 18px; left: 50%; transform: translateX(-50%); }
.wd-bottom { bottom: 18px; left: 50%; transform: translateX(-50%); }
.wd-icon { font-size: 18px; }
.wd-text { font-size: 13px; font-weight: 600; color: #aabbcc; margin-top: 2px; }
.wd-sub { font-size: 10px; color: #667788; margin-top: 1px; }

/* Floor grid */
.floor-grid {
  position: absolute; inset: 14px;
  background-image:
    linear-gradient(rgba(68,136,255,0.035) 1px, transparent 1px),
    linear-gradient(90deg, rgba(68,136,255,0.035) 1px, transparent 1px);
  background-size: 50px 50px;
}

/* Signal zones (concentric circles) */
.sig-zone {
  position: absolute; border-radius: 50%; border: 1px dashed rgba(255,255,255,0.04);
  top: 50%; left: 50%; transform: translate(-50%, -50%); pointer-events: none;
}
.zone-1 { width: 50%; height: 50%; border: 1.5px dashed rgba(0,255,136,0.25); background: rgba(0,255,136,0.05); }
.zone-2 { width: 75%; height: 75%; border: 1.5px dashed rgba(255,200,50,0.18); background: rgba(255,200,50,0.02); }
.zone-3 { width: 90%; height: 90%; border: 1.5px dashed rgba(255,150,0,0.12); }
.zone-4 { width: 100%; height: 100%; border: 1.5px dashed rgba(255,80,0,0.08); }
.zone-label {
  position: absolute; font-size: 13px; font-weight: 700; pointer-events: none;
}
.zone-1 .zone-label { top: 30%; left: 65%; color: rgba(0,255,136,0.50); }
.zone-2 .zone-label { top: 14%; left: 74%; color: rgba(255,200,50,0.45); }
.zone-3 .zone-label { top: 5%; left: 82%; color: rgba(255,150,0,0.40); }
.zone-4 .zone-label { top: 2%; left: 88%; color: rgba(255,80,0,0.35); }

/* ====== FURNITURE ====== */
.furn { position: absolute; z-index: 2; pointer-events: none; }
.furn-label {
  text-align: center; font-size: 12px; color: rgba(255,255,255,0.45);
  white-space: nowrap; margin-top: 6px; font-weight: 500;
}

/* Desk area (top-left) */
.desk-area { top: 6%; left: 5%; display: flex; flex-direction: column; align-items: center; }
.furn-desk { width: 120px; height: 60px; background: linear-gradient(135deg, rgba(90,110,140,0.35), rgba(70,90,120,0.25)); border-radius: 10px; border: 1px solid rgba(255,255,255,0.08); }
.furn-desk-chair { width: 35px; height: 35px; background: rgba(110,120,150,0.28); border-radius: 50%; margin-top: 8px; border: 1px solid rgba(255,255,255,0.05); }

/* Sofa (top-right) */
.sofa-area { top: 6%; right: 6%; display: flex; flex-direction: column; align-items: center; }
.furn-sofa { width: 140px; height: 55px; background: linear-gradient(90deg, rgba(120,90,130,0.32), rgba(100,70,110,0.22)); border-radius: 30px; border: 1px solid rgba(255,255,255,0.08); }
.furn-coffee-table { width: 55px; height: 40px; background: rgba(130,110,90,0.25); border-radius: 8px; margin-top: 10px; border: 1px solid rgba(255,255,255,0.05); }

/* TV (bottom center) */
.tv-area { bottom: 4%; left: 50%; transform: translateX(-50%); display: flex; flex-direction: column; align-items: center; }
.furn-tv-stand { width: 150px; height: 45px; background: linear-gradient(0deg, rgba(80,100,130,0.30), rgba(60,80,110,0.20)); border-radius: 10px; border: 1px solid rgba(255,255,255,0.06); }

/* Shelf (left mid) */
.shelf-area { top: 30%; left: 2.5%; display: flex; flex-direction: column; align-items: center; }
.furn-shelf { width: 35px; height: 110px; background: linear-gradient(90deg, rgba(130,100,80,0.30), rgba(100,80,60,0.18)); border-radius: 5px; border: 1px solid rgba(255,255,255,0.06); }

/* Dining table (bottom-left) */
.dining-area { bottom: 14%; left: 10%; display: flex; flex-direction: column; align-items: center; }
.furn-dining-table { width: 90px; height: 90px; background: rgba(100,110,140,0.28); border-radius: 50%; border: 1px solid rgba(255,255,255,0.07); }

/* Plants - more visible */
.plant-1 { top: 62%; right: 8%; font-size: 36px; opacity: 0.45; }
.plant-2 { bottom: 20%; left: 3%; font-size: 30px; opacity: 0.40; }

/* Center rug */
.rug {
  top: 50%; left: 50%; transform: translate(-50%, -50%);
  width: 22%; height: 22%;
  background: radial-gradient(ellipse, rgba(120,100,70,0.12) 0%, rgba(100,80,50,0.04) 70%, transparent);
  border-radius: 50%;
  border: 1.5px dashed rgba(255,255,255,0.06);
}

/* ====== AP CENTER ====== */
.ap-center {
  position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%);
  z-index: 15; text-align: center;
}
.ap-icon-wrap {
  width: 80px; height: 80px; margin: 0 auto;
  background: rgba(0,255,136,0.06); border: 3px solid rgba(0,255,136,0.35);
  border-radius: 50%; display: flex; align-items: center; justify-content: center;
  animation: ap-glow 2s ease-in-out infinite;
}
@keyframes ap-glow {
  0%,100% { box-shadow: 0 0 20px rgba(0,255,136,0.12), 0 0 40px rgba(0,255,136,0.06); }
  50% { box-shadow: 0 0 40px rgba(0,255,136,0.35), 0 0 80px rgba(0,255,136,0.15); }
}
.ap-center.ap-alert .ap-icon-wrap {
  border-color: rgba(255,68,68,0.45); background: rgba(255,68,68,0.05);
  animation: ap-alert-glow 1s ease-in-out infinite;
}
@keyframes ap-alert-glow {
  0%,100% { box-shadow: 0 0 20px rgba(255,68,68,0.2), 0 0 40px rgba(255,68,68,0.08); }
  50% { box-shadow: 0 0 40px rgba(255,68,68,0.5), 0 0 80px rgba(255,68,68,0.25); }
}
.ap-icon-img { width: 46px; height: 46px; }
.ap-label { margin-top: 6px; font-size: 13px; font-weight: 700; color: #dde8f0; }
.ap-mac { font-size: 10px; color: #667788; font-family: monospace; margin-top: 1px; }
.ap-ssid { font-size: 10px; color: #4488aa; margin-top: 1px; font-weight: 500; }

/* Signal rings */
.signal-ring {
  position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%);
  border: 2px solid rgba(0,255,136,0.2); border-radius: 50%; pointer-events: none;
}
.ring-1 { width: 120px; height: 120px; animation: ring-out 3s ease-out infinite; }
.ring-2 { width: 120px; height: 120px; animation: ring-out 3s ease-out 0.75s infinite; }
.ring-3 { width: 120px; height: 120px; animation: ring-out 3s ease-out 1.5s infinite; }
.ring-4 { width: 120px; height: 120px; animation: ring-out 3s ease-out 2.25s infinite; }
@keyframes ring-out {
  0% { transform: translate(-50%, -50%) scale(0.4); opacity: 0.8; }
  100% { transform: translate(-50%, -50%) scale(6); opacity: 0; }
}

/* ====== DEVICE CARDS ====== */
.device-card {
  position: absolute; z-index: 8;
  width: 140px; background: rgba(20,28,44,0.94);
  border: 1px solid rgba(68,136,255,0.25); border-radius: 12px;
  padding: 10px 8px; text-align: center; cursor: pointer;
  transition: all 0.2s; backdrop-filter: blur(4px);
}
.device-card:hover {
  border-color: rgba(68,136,255,0.7); transform: translateY(-3px) scale(1.06);
  box-shadow: 0 6px 22px rgba(68,136,255,0.3); z-index: 25;
}
.card-attacker { border-color: rgba(255,68,68,0.45); background: rgba(40,12,12,0.92); }
.card-target { border-color: rgba(255,170,0,0.45); background: rgba(40,30,10,0.92); }
.card-selected { border-color: #fff !important; box-shadow: 0 0 0 3px #fff, 0 10px 30px rgba(0,0,0,0.5) !important; z-index: 30 !important; }
.card-under-attack { border-color: rgba(255,68,68,0.55); animation: card-under-attack-pulse 1.5s ease-in-out infinite; }
@keyframes card-under-attack-pulse {
  0%,100% { box-shadow: 0 0 8px rgba(255,68,68,0.2); }
  50% { box-shadow: 0 0 20px rgba(255,68,68,0.5), 0 0 40px rgba(255,68,68,0.2); }
}

.card-icon { width: 32px; height: 32px; margin-bottom: 5px; }
.card-name { font-weight: 600; color: #dde8f0; font-size: 12px; margin-bottom: 2px; }
.card-mac { color: #667788; font-family: monospace; font-size: 10px; margin-bottom: 4px; }
.card-signal { display: flex; align-items: center; justify-content: center; gap: 1px; }
.sig-bar { width: 3px; border-radius: 1px; }
.bar-1 { height: 6px; background: #334455; } .bar-2 { height: 9px; background: #334455; }
.bar-3 { height: 13px; background: #e6a23c; } .bar-4 { height: 17px; background: #67c23a; }
.sig-dbm { font-size: 10px; color: #778899; margin-left: 4px; }
.card-dist { font-size: 10px; color: #448888; margin-top: 3px; font-weight: 500; }

/* Device status badges */
.device-status-badge {
  position: absolute; top: -10px; left: 50%; transform: translateX(-50%);
  padding: 2px 8px; border-radius: 8px;
  font-size: 11px; font-weight: 700; white-space: nowrap; z-index: 6;
  color: #fff; text-shadow: 0 1px 2px rgba(0,0,0,0.5);
}
.status-attacking { background: #ff2222; animation: badge-blink 0.8s ease-in-out infinite; }
.status-targeted { background: #ff8800; animation: badge-blink 1.2s ease-in-out infinite; }
.status-blocked { background: #667788; }

/* Attack count badge (top-right) */
.attack-count-badge {
  position: absolute; top: -8px; right: -8px;
  min-width: 20px; height: 20px; line-height: 20px;
  background: #ff2222; color: #fff;
  font-size: 11px; font-weight: 700; text-align: center;
  border-radius: 10px; z-index: 7;
  box-shadow: 0 2px 8px rgba(255,0,0,0.5);
  animation: count-pulse 1s ease-in-out infinite;
}
@keyframes count-pulse {
  0%,100% { transform: scale(1); }
  50% { transform: scale(1.12); }
}
@keyframes badge-blink {
  0%,100% { opacity: 1; }
  50% { opacity: 0.5; }
}

.attack-flash {
  position: absolute; inset: -3px; border-radius: 14px;
  border: 2px solid transparent; pointer-events: none;
  animation: atk-flash 1s ease-in-out infinite;
}
@keyframes atk-flash {
  0%,100% { border-color: transparent; box-shadow: none; }
  50% { border-color: rgba(255,68,68,0.9); box-shadow: 0 0 16px rgba(255,68,68,0.6); }
}

/* Attack badge on device cards */
.attack-badge {
  position: absolute; top: -8px; right: -8px;
  min-width: 22px; height: 22px; line-height: 22px;
  background: #ff2222; color: #fff;
  font-size: 11px; font-weight: 700; text-align: center;
  border-radius: 11px; z-index: 5;
  box-shadow: 0 2px 8px rgba(255,0,0,0.5);
  animation: badge-pulse 1s ease-in-out infinite;
}
@keyframes badge-pulse {
  0%,100% { transform: scale(1); }
  50% { transform: scale(1.15); }
}

/* Attackers */
.attacker-outer {
  position: absolute; z-index: 8;
  width: 90px; background: rgba(50,10,10,0.9);
  border: 1px solid rgba(255,68,68,0.4); border-radius: 8px;
  padding: 6px; text-align: center; cursor: pointer; transition: all 0.2s;
}
.attacker-outer:hover { border-color: rgba(255,68,68,0.8); box-shadow: 0 0 20px rgba(255,68,68,0.4); transform: scale(1.08); }
.attacker-outer.card-selected { border-color: #fff !important; box-shadow: 0 0 0 3px #fff, 0 0 30px rgba(255,68,68,0.7) !important; }
.attacker-active { border-color: rgba(255,68,68,0.55); background: rgba(50,10,10,0.92); }
.attacker-blocked { border-color: rgba(136,136,136,0.25); background: rgba(30,30,30,0.7); opacity: 0.65; }
.attacker-blocked .atk-label { color: #888 !important; }
.atk-icon { width: 26px; height: 26px; }
.atk-label { font-size: 10px; font-weight: 700; color: #f56c6c; margin-top: 2px; }
.atk-mac { font-size: 9px; color: #994444; font-family: monospace; }
.attack-flash-outer {
  position: absolute; inset: -5px; border-radius: 14px; pointer-events: none;
  animation: atk-flash 0.8s ease-in-out infinite;
}

/* Hover card */
.hover-card {
  position: absolute; z-index: 50;
  background: rgba(20,28,44,0.98); border: 1px solid rgba(68,136,255,0.35);
  border-radius: 10px; padding: 12px 16px; font-size: 12px; min-width: 190px; pointer-events: none;
}
.hc-head { display: flex; align-items: center; gap: 8px; margin-bottom: 6px; }
.hc-icon { width: 24px; height: 24px; }
.hc-head span { font-weight: 700; color: #fff; font-size: 13px; }
.hc-row { display: flex; justify-content: space-between; margin: 2px 0; color: #778899; font-size: 11px; }
.hc-row span:last-child { color: #aabbcc; }
.mono { font-family: monospace; }

/* ====== RIGHT PANEL (240px) ====== */
.right-panel {
  width: 260px; flex-shrink: 0;
  background: rgba(255,255,255,0.015); border-left: 1px solid rgba(255,255,255,0.05);
  display: flex; flex-direction: column; overflow-y: auto;
  transition: width 0.3s;
}
.rp-expanded { width: 340px; }
.rp-section { padding: 12px 14px; border-bottom: 1px solid rgba(255,255,255,0.04); }
.rp-title { font-size: 12px; font-weight: 700; color: #778899; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 8px; }
.rp-title.danger { color: #f56c6c; }

/* Alert items */
.rp-alert-item {
  display: flex; align-items: center; gap: 6px; padding: 6px 8px;
  background: rgba(255,68,68,0.04); border: 1px solid rgba(255,68,68,0.08);
  border-radius: 6px; margin-bottom: 4px; font-size: 11px;
}
.rp-alert-type { flex: 1; color: #f59898; font-weight: 500; }
.rp-alert-mac { color: #886666; font-family: monospace; font-size: 10px; }

/* Device detail */
.rp-dev-icon { width: 40px; height: 40px; display: block; margin: 0 auto; }
.rp-dev-name { text-align: center; font-weight: 700; font-size: 14px; color: #dde8f0; margin: 6px 0 2px; }
.rp-dev-mac { text-align: center; font-size: 11px; color: #667788; font-family: monospace; margin-bottom: 10px; }
.rp-info-row { display: flex; justify-content: space-between; padding: 3px 0; font-size: 12px; color: #8899aa; }
.rp-info-row span:last-child { color: #ccd8e8; text-align: right; }
.rp-actions { display: flex; gap: 6px; margin-top: 10px; }

/* Safe message */
.rp-safe-msg { display: flex; flex-direction: column; align-items: center; padding: 12px 0; color: #8899aa; font-size: 13px; }
.rp-safe-icon { font-size: 30px; margin-bottom: 6px; }
.rp-safe-sub { font-size: 11px; color: #667788; margin-top: 4px; }

/* Device type stats */
.rp-bar-item { display: flex; justify-content: space-between; padding: 4px 0; font-size: 12px; color: #8899aa; }
.rp-bar-val { font-weight: 700; color: #ccd8e8; }

/* Usage tips */
.rp-tip { font-size: 11px; color: #667788; padding: 3px 0; line-height: 1.5; }

/* Device header (compact) */
.rp-dev-header { display: flex; align-items: center; gap: 10px; }
.rp-dev-icon-sm { width: 36px; height: 36px; }
.rp-dev-name-sm { font-weight: 700; font-size: 14px; color: #dde8f0; }
.rp-dev-mac-sm { font-size: 11px; color: #667788; font-family: monospace; }
.rp-dev-meta { margin-top: 10px; }
.rp-meta-item { display: flex; justify-content: space-between; padding: 2px 0; font-size: 12px; color: #8899aa; }
.rp-meta-item span:last-child { color: #ccd8e8; text-align: right; }
.rp-safe-msg-sm { text-align: center; padding: 10px 0; font-size: 13px; color: #667788; }

/* ====== ATTACK DETAIL CARDS ====== */
.attack-detail-card {
  background: rgba(30,10,10,0.4); border: 1px solid rgba(255,68,68,0.2);
  border-radius: 10px; padding: 12px; margin-bottom: 10px;
}
.attack-detail-card.atk-severity-critical { border-color: rgba(255,0,0,0.5); background: rgba(40,5,5,0.5); }
.attack-detail-card.atk-severity-high { border-color: rgba(255,50,50,0.35); }
.attack-detail-card.atk-severity-medium { border-color: rgba(255,170,0,0.25); background: rgba(30,20,5,0.3); }
.attack-detail-card.atk-severity-low { border-color: rgba(100,180,100,0.2); background: rgba(10,20,10,0.3); }

.adc-header { display: flex; align-items: center; gap: 8px; margin-bottom: 10px; }
.adc-type { font-weight: 700; font-size: 14px; color: #ff8888; flex: 1; }
.adc-time { font-size: 11px; color: #886666; }
.adc-body { margin-bottom: 8px; }
.adc-row { display: flex; justify-content: space-between; align-items: flex-start; padding: 3px 0; gap: 8px; }
.adc-label { font-size: 11px; color: #997777; flex-shrink: 0; }
.adc-row .mono { font-size: 11px; color: #cc9999; text-align: right; word-break: break-all; }
.adc-suggestion { font-size: 12px; color: #ddaaaa; line-height: 1.5; text-align: right; flex: 1; }
.adc-actions { display: flex; gap: 6px; padding-top: 8px; border-top: 1px solid rgba(255,255,255,0.04); }

.mono { font-family: monospace; font-size: 11px; }

/* Signal reference */
.rp-sig-row { display: flex; align-items: center; gap: 8px; font-size: 11px; color: #8899aa; margin-bottom: 3px; }
.rp-sig-bars { display: flex; gap: 1px; }
.sb { width: 3px; border-radius: 1px; display: inline-block; }
.sb4 { height: 14px; background: #67c23a; } .sb3 { height: 11px; background: #a4c639; }
.sb2 { height: 8px; background: #e6a23c; } .sb1 { height: 5px; background: #f56c6c; }
.sboff { height: 14px; background: #334455; }

/* ====== BOTTOM BAR ====== */
.bottom-bar {
  position: absolute; bottom: 0; left: 0; right: 0; height: 36px;
  display: flex; align-items: center; justify-content: center; gap: 16px;
  padding: 0 20px; background: rgba(255,255,255,0.02); border-top: 1px solid rgba(255,255,255,0.04);
}
.bb-item { display: flex; align-items: center; gap: 5px; font-size: 11px; color: #778899; }
.bb-icon { width: 18px; height: 18px; object-fit: contain; }
.bb-sep { color: rgba(255,255,255,0.06); }
.bb-dot { width: 7px; height: 7px; border-radius: 50%; }
.bb-dot.green { background: #00ff88; }
.bb-dot.red { background: #ff4444; }
.bb-dot.red.pulse { animation: leg-pulse 1.5s ease-in-out infinite; }
.bb-dot.ring-pulse { border: 2px solid rgba(0,255,136,0.5); background: transparent; animation: leg-ring 2s ease-out infinite; }
@keyframes leg-pulse { 0%,100%{opacity:1} 50%{opacity:0.3} }
@keyframes leg-ring { 0%{transform:scale(0.4);opacity:1} 100%{transform:scale(2.2);opacity:0} }
</style>
