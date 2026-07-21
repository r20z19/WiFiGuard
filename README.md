# WiFiGuard

<p align="center">
  <strong>智能无线网络安全防护与入侵检测系统</strong>
</p>

<p align="center">
  集 <strong>实时监控 · 入侵检测 · 主动防御 · 可视化拓扑 · AI 智能分析 · 邮件告警</strong> 于一体
</p>

---

## 技术栈

| 层级 | 技术 |
|------|------|
| 前端框架 | Vue 3 (Composition API) + Vite 5 |
| UI 组件 | Element Plus 2.x |
| 图表 | ECharts 5 |
| 状态管理 | Pinia |
| 路由 | Vue Router 4 |
| HTTP | Axios |
| 后端 | Python Flask + Scapy |
| 数据库 | SQLite (WAL 模式) |
| AI | DeepSeek / 通义千问 / 智谱 GLM |

---

## 项目结构

```
WiFiGuard/
├── frontend/                  # Vue 3 前端
│   ├── src/
│   │   ├── api/index.js       # API 接口层
│   │   ├── assets/            # 静态资源 (CSS, JSON)
│   │   ├── components/        # 公共组件
│   │   │   └── AiPanel.vue    # AI 聊天浮动面板
│   │   ├── router/index.js    # 路由配置
│   │   ├── store/             # Pinia 状态管理
│   │   ├── views/             # 页面组件
│   │   │   ├── Dashboard.vue  # 系统概览
│   │   │   ├── Alerts.vue     # 当前告警
│   │   │   ├── History.vue    # 历史告警
│   │   │   ├── Devices.vue    # 在线设备
│   │   │   ├── Whitelist.vue  # 设备白名单
│   │   │   ├── Blacklist.vue  # 设备黑名单
│   │   │   ├── Email.vue      # 邮箱推送
│   │   │   ├── NetworkMap.vue # 网络拓扑
│   │   │   ├── Logs.vue       # 系统日志
│   │   │   ├── Report.vue     # 安全报告
│   │   │   ├── AiSettings.vue # AI 功能配置
│   │   │   └── Login.vue      # 登录页
│   │   ├── App.vue            # 根组件
│   │   └── main.js            # 入口文件
│   ├── index.html
│   ├── vite.config.js
│   └── package.json
├── backend/                   # Python Flask 后端
│   ├── app.py                 # 主入口
│   ├── database.py            # 数据库初始化
│   ├── config.py              # 配置文件
│   ├── routes/                # API 路由 (11个模块)
│   ├── services/              # 业务逻辑层
│   ├── detection/             # 8 个检测引擎
│   ├── utils/                 # 工具函数
│   └── scripts/               # 辅助脚本
└── 项目介绍.md                # 用户手册
```

---

## 功能模块

### 系统概览 (Dashboard)
- 4 张状态卡片（系统状态 / 告警 / 设备 / 今日告警），全部可点击跳转
- 攻击类型统计柱状图 + 占比饼图（点击扇区可筛选告警）
- 安全建议卡片（紧急处置 / 攻击防御 / 配置引导），每条带操作按钮
- 在线设备快速浏览列表
- 2D 仪表盘 / 网络拓扑 一键切换

### 当前告警 (Alerts)
- 实时告警列表 + 严重等级快速筛选（全部/严重/高危/中危）
- 攻击源聚合视图（按 MAC 合并显示攻击次数和类型）
- 批量操作：多选 → 批量清除 / 批量加黑名单
- 一键处置：拉黑源 MAC + 清除告警
- AI 智能解读 + 报文上下文分析
- 右侧详情面板（点"建议"展开）

### 历史告警 (History)
- 日期快捷筛选（今天 / 本周 / 本月）+ 日期范围选择器
- 攻击类型 + 状态筛选
- 统计摘要栏（严重/高危/中危/低危计数）
- 📥 导出 CSV

### 在线设备 (Devices)
- 实时在线设备列表 + 厂商 OUI 自动识别 + 设备类型图标
- 信号强度可视化 + 风险评估评分（0-100）
- 在线时长显示 + 设备指纹标签（新设备/常驻/信号异常）
- 侧滑详情抽屉：设备标识 + 网络信息 + 安全评估 + 行为时间线
- AI 智能设备识别

### 网络拓扑 (NetworkMap)
- 室内房间平面图 + 家具布局 + 信号区域环（优/良/中/弱）
- AP 居中持续扩散信号波纹 + 用户设备按信号强度分布
- 攻击者红色闪烁 + 攻击连线动态虚线 + 彩色箭头
- 设备状态徽章（攻击中 / 被攻击 / 已踢出）+ 攻击次数角标
- 左侧设备列表 + 右侧详情面板 + 悬停信息卡

### 白名单 / 黑名单
- 启用开关（互斥，同一时间只能启用一种）
- 从在线设备批量导入 + 手动添加/编辑/移除
- MAC 自动格式化（大写 + 冒号分隔）
- 实时显示名单设备在线状态
- 黑名单关联告警统计

### 邮箱推送 (Email)
- SMTP 配置（QQ / 163 / Gmail） + 授权码
- 测试连接 + 保存配置
- 推送记录查看
- 内置配置指南

### 安全报告 (Report)
- 综合安全评分（0-100 环形图）
- 安全趋势折线图 + 攻击类型饼图
- 高危设备列表
- 🤖 AI 自动生成安全报告
- 🔍 AI 异常行为检测 + 🔮 AI 攻击预测

### 系统日志 (Logs)
- 等级筛选（ERROR / WARNING / INFO）+ 类别筛选
- 关键词搜索
- 📥 导出 CSV
- 自动记录：攻击检测 / 名单变更 / 设备踢出 / 邮件发送 / 系统启动

### AI 功能 (AiSettings)
- 支持平台：DeepSeek / 通义千问 / 智谱 GLM
- API Key 配置 + 测试连接
- 功能：智能告警解读 / AI 安全顾问 / 自动报告 / 设备识别 / 异常检测 / 攻击预测
- 右下角浮动聊天面板（AI 安全顾问）

---

## 快速开始

### 5 分钟体验（模拟模式，无需网卡）

```bash
# 1. 安装后端依赖
cd backend
pip install -r requirements.txt

# 2. 安装前端并构建
cd ../frontend
npm install
npm run build

# 3. 启动
cd ../backend
python app.py
```

浏览器打开 **http://localhost:8000**，默认账户 `admin / admin`。

### 真实监听模式（需要 Monitor 网卡）

```bash
sudo ./backend/scripts/setup_monitor.sh wlan1
export WIFIGUARD_SIM=false
export WIFIGUARD_IFACE=wlan1
cd backend && python app.py
```

---

## 环境变量

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `WIFIGUARD_DB` | `backend/data/wifiguard.db` | SQLite 数据库路径 |
| `WIFIGUARD_IFACE` | `wlan1mon` | 监听网卡接口名 |
| `WIFIGUARD_SIM` | `true` | 模拟模式开关 |
| `WIFIGUARD_PCAP` | (空) | PCAP 文件路径 |
| `WIFIGUARD_INTERVAL` | `2` | 检测轮询间隔（秒） |
| `WIFIGUARD_DEBUG` | `false` | Flask 调试模式 |

---

## API 接口

| 接口 | 方法 | 说明 |
|------|:--:|------|
| `/api/system/status` | GET | 系统状态 |
| `/api/alerts/current` | GET | 当前告警 |
| `/api/alerts/history` | GET | 历史告警 |
| `/api/alerts/<id>/clear` | POST | 清除告警 |
| `/api/devices/online` | GET | 在线设备 |
| `/api/devices/whitelist` | GET/POST | 白名单管理 |
| `/api/devices/whitelist/<mac>` | DELETE | 移出白名单 |
| `/api/devices/blacklist` | GET/POST | 黑名单管理 |
| `/api/devices/blacklist/<mac>` | DELETE | 移出黑名单 |
| `/api/email/config` | GET/PUT | 邮箱配置 |
| `/api/email/test` | POST | 测试邮箱连接 |
| `/api/email/records` | GET | 推送记录 |
| `/api/auth/login` | POST | 登录 |
| `/api/auth/change-password` | POST | 修改密码 |
| `/api/geo/locations` | GET | 设备地理位置 |
| `/api/logs` | GET | 系统日志 |
| `/api/logs/stats` | GET | 日志统计 |
| `/api/logs/export` | GET | 导出日志CSV |
| `/api/ai/config` | GET/POST | AI 配置 |
| `/api/ai/interpret` | POST | AI 告警解读 |
| `/api/ai/chat` | POST | AI 对话 |
| `/api/ai/report` | POST | AI 生成报告 |
| `/api/ai/identify` | POST | AI 设备识别 |
| `/api/ai/anomalies` | POST | AI 异常检测 |
| `/api/ai/predict` | POST | AI 攻击预测 |
| `/api/ai/frames` | GET | 报文上下文查询 |

---

## 默认账户

| 字段 | 值 |
|------|------|
| 用户名 | `admin` |
| 初始密码 | `admin` |

首次登录需修改密码。忘记密码：删除 `backend/data/wifiguard.db` 重启即可重置。

---

## 许可证

本项目仅限**教育、研究和个人使用**。不得用于任何未经授权的网络攻击或非法活动。
