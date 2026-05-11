# WiFiGuard

智能无线入侵检测与预警系统 — Web 可视化管理与告警平台

## 项目架构

```
WiFiGuard/
├── frontend/                # Vue 3 SPA
│   ├── src/
│   │   ├── api/index.js     # 15 个 REST API 接口定义
│   │   ├── store/alert.js   # Pinia 状态管理
│   │   ├── views/           # 7 个页面（Dashboard, Alerts, History, Devices, Whitelist, Blacklist, Email）
│   │   ├── router/index.js  # Vue Router
│   │   └── App.vue          # 根组件
│   ├── vite.config.js       # Vite 配置（端口 3000，代理 /api -> :8000）
│   └── package.json
├── backend/                 # Flask 后端
│   ├── app.py               # 入口，Flask 工厂
│   ├── config.py            # 配置（数据库路径、模拟模式、检测间隔）
│   ├── database.py          # SQLite 初始化，6 张表
│   ├── routes/              # API 路由层（system, alerts, devices, whitelist, blacklist, email）
│   ├── services/            # 业务逻辑层
│   ├── detection/           # 检测引擎（7 个检测器 + 模拟器）
│   ├── attack_scripts/      # 攻击演示脚本
│   ├── utils/               # 工具函数
│   └── requirements.txt     # Python 依赖
└── .gitignore
```

## 功能模块

### 前端（Vue 3 + Element Plus + Pinia）

| 页面 | 功能 |
|------|------|
| 系统概览 Dashboard | 系统状态、告警/设备数量统计、安全建议、快捷配置入口 |
| 当前告警 Alerts | 实时告警列表、7 种攻击类型、严重等级、安全建议、告警处理 |
| 历史告警 History | 历史记录查询、攻击类型/日期/状态筛选、详情查看 |
| 在线设备 Devices | 在线设备列表、信号强度可视化、正常/可疑标识、快速加入黑白名单 |
| 设备白名单 Whitelist | 可信设备管理，白名单内设备不触发告警 |
| 设备黑名单 Blacklist | 威胁设备管理，黑名单设备触发高危告警 |
| 邮箱推送 Email | QQ/163/Gmail SMTP 配置、连接测试、推送记录 |

### 后端攻击检测（7 种）

| 检测模块 | 说明 | 严重等级 |
|----------|------|----------|
| Deauth 攻击 | 检测去认证帧泛洪，区分正常断连与恶意攻击 | high |
| Evil Twin 钓鱼 | 检测同 SSID 不同 BSSID 的伪造 AP | critical |
| Flood 泛洪 | 检测异常高频数据包传输 | medium |
| 暴力破解 | 检测短时间内大量认证失败 | medium |
| 非法接入 | 检测不在白名单中的新设备接入 | high |
| 弱口令风险 | 评估当前 WiFi 密码强度 | low |
| KRACK 风险 | 检测 WEP/WPA/TKIP 等不安全加密协议 | critical |

### 后端 API（15 个端点）

```
GET    /api/system/status
GET    /api/alerts/current
GET    /api/alerts/history
POST   /api/alerts/:id/clear
GET    /api/devices/online
GET    /api/devices/whitelist
POST   /api/devices/whitelist
DELETE /api/devices/whitelist/:mac
GET    /api/devices/blacklist
POST   /api/devices/blacklist
DELETE /api/devices/blacklist/:mac
GET    /api/email/config
PUT    /api/email/config
POST   /api/email/test
GET    /api/email/records
```

## 安装和运行

### 环境要求

**前端：** Node.js >= 16, npm >= 8
**后端：** Python 3.11, miniconda

### 后端

```bash
# 创建 conda 环境
conda create -n wifiguard python=3.11 -y
conda activate wifiguard

# 安装依赖
cd backend
pip install -r requirements.txt

# 启动（默认模拟模式，无需监听网卡）
python app.py
```

后端运行在 `http://localhost:8000`。模拟模式下检测引擎会自动生成虚拟设备数据和攻击告警。

**环境变量：**
| 变量 | 默认值 | 说明 |
|------|--------|------|
| `WIFIGUARD_DB` | `backend/data/wifiguard.db` | SQLite 数据库路径 |
| `WIFIGUARD_IFACE` | `wlan1mon` | 监听网卡（非模拟模式） |
| `WIFIGUARD_SIM` | `true` | 模拟模式开关，开发时保持 `true` |
| `WIFIGUARD_INTERVAL` | `2` | 检测间隔（秒） |
| `WIFIGUARD_SMTP_HOST` | `smtp.qq.com` | 邮件 SMTP 服务器 |
| `WIFIGUARD_SMTP_PORT` | `465` | SMTP 端口 |

### 前端

```bash
cd frontend
npm install
npm run dev
```

访问 `http://localhost:3000`，Vite 自动代理 `/api` 到后端 `:8000`。

### 生产部署

```bash
# 构建前端
cd frontend && npm run build

# 将 dist/ 部署到 Flask 静态目录，或使用 nginx 反向代理
```

## 攻击演示脚本

以下脚本需要在树莓派 + 监听网卡（monitor 模式）环境下运行：

```bash
cd backend/attack_scripts

# 单独测试
sudo ./simulate_deauth.sh wlan1mon
sudo ./simulate_evil_twin.sh wlan1
sudo ./simulate_flood.sh wlan1mon
sudo ./simulate_brute_force.sh wlan1mon
sudo ./simulate_illegal.sh wlan1

# 完整演示
sudo ./simulate_all.sh wlan1mon
```
