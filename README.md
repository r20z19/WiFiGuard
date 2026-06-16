# WiFiGuard 前端系统

智能无线入侵检测与预警系统 - Web可视化管理与告警平台

## 技术栈

- Vue 3 - 渐进式JavaScript框架
- Vite - 下一代前端构建工具
- Element Plus - Vue 3 UI组件库
- Pinia - Vue状态管理
- Vue Router - Vue路由管理
- Axios - HTTP客户端

## 项目结构

```
frontend/
├── src/
│   ├── api/              # API接口
│   │   └── index.js
│   ├── assets/           # 静态资源
│   │   └── global.css
│   ├── components/       # 组件
│   ├── router/           # 路由配置
│   │   └── index.js
│   ├── store/            # 状态管理
│   │   └── alert.js
│   ├── views/            # 页面
│   │   ├── Dashboard.vue    # 系统概览
│   │   ├── Alerts.vue       # 当前告警
│   │   ├── History.vue      # 历史告警
│   │   ├── Devices.vue      # 在线设备
│   │   ├── Whitelist.vue    # 设备白名单
│   │   ├── Blacklist.vue    # 设备黑名单
│   │   └── Email.vue        # 邮箱推送
│   ├── App.vue           # 根组件
│   └── main.js           # 入口文件
├── index.html
├── vite.config.js
└── package.json
```

## 功能模块

### 1. 系统概览 (Dashboard)
- 系统状态显示：正在初始化 / 监听中
- 当前告警数量统计
- 在线设备数量统计
- 历史告警数量统计
- 快速安全建议展示
- 快捷配置入口

### 2. 当前告警 (Alerts)
- 实时告警列表
- 攻击类型分类（Deauth攻击、钓鱼AP、暴力破解等7类）
- 严重等级标识（严重/高危/中危/低危）
- 安全建议详情
- 告警处理功能

### 3. 历史告警 (History)
- 历史告警记录查询
- 日期范围筛选
- 攻击类型筛选
- 处理状态筛选
- 告警详情查看

### 4. 在线设备 (Devices)
- 实时在线设备列表
- MAC地址、IP地址、SSID显示
- 信号强度可视化
- 设备状态标识（正常/可疑）
- 快速加入白名单/黑名单

### 5. 设备白名单 (Whitelist)
- 白名单设备管理
- 添加/编辑/移除设备
- MAC地址和设备名称配置

### 6. 设备黑名单 (Blacklist)
- 黑名单设备管理
- 添加/编辑/移除设备
- 加入原因记录

### 7. 邮箱推送 (Email)
- SMTP服务器配置
- 邮箱授权码配置
- 收件邮箱配置
- 推送开关控制
- 连接测试功能
- 推送记录查看
- 主流邮箱配置指南（QQ/163/Gmail）

## 安装和运行

### 环境要求
- Node.js >= 16.0.0
- npm >= 8.0.0

### 安装依赖

#### Ubuntu / Debian

```bash
# 基础工具
sudo apt update
sudo apt install -y git curl

# 无线攻击演示工具（仅运行攻击脚本时需要）
sudo apt install -y aircrack-ng   # aireplay-ng, airodump-ng, aircrack-ng
sudo apt install -y hostapd        # 伪造 AP
sudo apt install -y mdk4           # MDK4 泛洪攻击工具
sudo apt install -y macchanger     # MAC 地址欺骗
```

#### Arch Linux

```bash
sudo pacman -S aircrack-ng hostapd mdk4 macchanger
```

#### Raspberry Pi (Raspberry Pi OS)

```bash
sudo apt update
sudo apt install -y aircrack-ng hostapd mdk4 macchanger
# 注意：部分包名可能与 Ubuntu 不同，以 apt search 为准
```

### 2. 配置监听网卡

攻击检测需要一个支持 **monitor 模式** 的无线网卡（USB 外接或内置）。

```bash
# 查看无线网卡
iwconfig
# 找到你的 USB 无线网卡，通常是 wlan1、wlp0s20f0u1 等

# 使用项目自带的脚本一键切换（推荐）
sudo ./backend/scripts/setup_monitor.sh <网卡接口名>

# 或手动切换
sudo ip link set <网卡接口名> down
sudo iw dev <网卡接口名> set type monitor
sudo ip link set <网卡接口名> up

# 确认 monitor 模式已启用
iw dev <网卡接口名> info | grep type
# 应该显示 type monitor
```

**注意**：`setup_monitor.sh` 使用 `iw` 命令，不会重命名网卡。如果习惯使用 `airmon-ng`，它会把网卡重命名为 `wlan1mon`，此时需将 `WIFIGUARD_IFACE` 设置为 `wlan1mon`。

### 3. 安装 Python 环境

```bash
# 安装 miniconda（如未安装）
# https://docs.conda.io/en/latest/miniconda.html

# 创建 Python 3.11 虚拟环境
conda create -n wifiguard python=3.11 -y
conda activate wifiguard
```

### 4. 安装后端依赖

```bash
cd backend
pip install -r requirements.txt
```

### 5. 安装前端依赖

```bash
cd frontend
npm install
```

### 开发模式

```bash
npm run dev
```

访问 http://localhost:3000

### 生产构建

```bash
npm run build
```

### 预览构建结果

```bash
npm run preview
```

### 6. 用户认证

**默认凭据：**

| 字段 | 值 |
|------|------|
| 用户名 | `admin` |
| 初始密码 | `123123` |

首次登录成功后，系统会弹出修改密码对话框，请及时修改默认密码。

每次访问系统时，都需要先登录认证，未登录用户会被自动重定向到登录页面。

## 运行模式

### 模拟模式（默认）

`SIMULATION_MODE=true`（默认），不需要监听网卡。后端内置的 `SimulatorDataGenerator` 会自动：
- 生成 8 台虚拟在线设备
- 按时间线注入 7 种攻击告警（Deauth、Evil Twin、Flood 等）
- 适用于开发调试和功能演示

### 监听网卡模式（Live 实时监测）

连接真实监听网卡后，系统通过 tshark 实时抓取 802.11 帧，送入 7 个检测器进行攻击识别。

```bash
# 1. 将网卡切换为 monitor 模式
sudo ./backend/scripts/setup_monitor.sh <网卡接口名>

# 2. 设置环境变量并启动后端
export WIFIGUARD_SIM=false
export WIFIGUARD_IFACE=<网卡接口名>   # 与上一步一致
cd backend && python app.py
```

工作流程：
1. `LivePacketCapture` 后台运行 `tshark -i <接口>`，持续抓取 802.11 帧
2. daemon 线程解析帧并放入线程安全队列
3. 检测引擎每 2 秒排空队列，将帧批量送入 7 个检测器
4. 检测器通过滑动时间窗口分析帧数据，超过阈值时产生告警

### Pcap 重放模式

从预录制的 pcap 文件中读取帧进行离线检测，适合回放历史数据或调试：

```bash
WIFIGUARD_SIM=false WIFIGUARD_PCAP=test/testcase/global-01.cap python app.py
```

## 环境变量

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `WIFIGUARD_DB` | `backend/data/wifiguard.db` | SQLite 数据库路径 |
| `WIFIGUARD_IFACE` | `wlan1mon` | 监听网卡接口名 |
| `WIFIGUARD_SIM` | `true` | 模拟模式（`true`=无需网卡，`false`=真实监听） |
| `WIFIGUARD_PCAP` | (空) | Pcap 文件路径（逗号分隔多个），设置后优先于模拟/监听模式 |
| `WIFIGUARD_INTERVAL` | `2` | 检测引擎轮询间隔（秒） |
| `WIFIGUARD_SMTP_HOST` | `smtp.qq.com` | 邮件 SMTP 服务器 |
| `WIFIGUARD_SMTP_PORT` | `465` | SMTP 端口 |

## 攻击演示脚本

这些脚本用于在真实网络环境中测试检测系统，**需要 root 权限和 monitor 模式网卡**。

所有攻击脚本**必须手动指定目标**，不会自动选择目标，避免误伤他人网络。

### 第一步：扫描

```bash
npm run preview
```

## API接口说明

前端通过 `/api` 路径代理访问后端API，后端服务默认运行在 `http://localhost:8000`。

主要接口：
- `GET /api/system/status` - 获取系统状态
- `GET /api/alerts/current` - 获取当前告警
- `GET /api/alerts/history` - 获取历史告警
- `GET /api/devices/online` - 获取在线设备
- `GET /api/devices/whitelist` - 获取白名单
- `POST /api/devices/whitelist` - 添加到白名单
- `DELETE /api/devices/whitelist/:mac` - 从白名单移除
- `GET /api/devices/blacklist` - 获取黑名单
- `POST /api/devices/blacklist` - 添加到黑名单
- `DELETE /api/devices/blacklist/:mac` - 从黑名单移除
- `GET /api/email/config` - 获取邮箱配置
- `PUT /api/email/config` - 更新邮箱配置
- `POST /api/email/test` - 测试邮箱连接

## 注意事项

1. 当前版本使用模拟数据进行演示，实际使用时需要连接后端API
2. 邮箱配置中的授权码不是邮箱密码，需要在邮箱设置中生成
3. 建议在封闭测试环境中进行攻击模拟测试
