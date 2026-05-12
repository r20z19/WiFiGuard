# WiFiGuard

智能无线入侵检测与预警系统 — Web 可视化管理与告警平台

## 项目架构

```
WiFiGuard/
├── frontend/                # Vue 3 SPA
│   ├── src/
│   │   ├── api/index.js     # API 接口定义（含认证接口）
│   │   ├── store/
│   │   │   ├── alert.js     # Pinia 状态管理（告警/设备）
│   │   │   └── auth.js      # 认证状态管理
│   │   ├── views/           # 8 个页面（含登录页）
│   │   ├── router/index.js  # Vue Router（含路由守卫）
│   │   └── App.vue          # 根组件
│   ├── vite.config.js       # 端口 3000，代理 /api -> :8000
│   └── package.json
├── backend/                 # Flask 后端
│   ├── app.py               # 入口，Flask 工厂
│   ├── config.py            # 配置（可通过环境变量覆盖）
│   ├── database.py          # SQLite 初始化，7 张表（含用户认证）
│   ├── routes/              # API 路由层
│   ├── services/            # 业务逻辑层
│   ├── detection/           # 检测引擎（7 个检测器 + 模拟器）
│   ├── attack_scripts/      # 攻击演示脚本
│   ├── utils/               # 工具函数
│   └── requirements.txt     # Python 依赖
└── .gitignore
```

## 功能模块

### 前端页面

| 页面 | 功能 |
|------|------|
| 登录 Login | 用户认证，首次登录自动修改默认密码（123123） |
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

## 后端 API（18 个端点）

### 认证接口

```
POST   /api/auth/login                 # 用户登录 {username, password} -> {token, isFirstLogin}
GET    /api/auth/verify                # 验证登录状态 -> {valid, username, isFirstLogin}
POST   /api/auth/change-password       # 修改密码 {oldPassword, newPassword}
```

### 业务接口

```
GET    /api/system/status          # 系统状态
GET    /api/alerts/current         # 当前告警列表
GET    /api/alerts/history         # 历史告警（支持 ?type=&status=&startDate=&endDate=）
POST   /api/alerts/:id/clear       # 清除告警（移入历史）
GET    /api/devices/online         # 在线设备列表
GET    /api/devices/whitelist      # 白名单列表
POST   /api/devices/whitelist      # 添加到白名单 {mac, name}
DELETE /api/devices/whitelist/:mac # 从白名单移除
GET    /api/devices/blacklist      # 黑名单列表
POST   /api/devices/blacklist      # 添加到黑名单 {mac, name, reason}
DELETE /api/devices/blacklist/:mac # 从黑名单移除
GET    /api/email/config           # 邮箱配置
PUT    /api/email/config           # 更新邮箱配置
POST   /api/email/test             # 测试邮箱连接
GET    /api/email/records          # 推送记录
```

所有业务接口（除登录外）均需在请求头中携带 `Authorization: Bearer <token>`。

## 环境要求

| 组件 | 要求 |
|------|------|
| Python | 3.11（通过 miniconda 管理） |
| Node.js | >= 16 |
| npm | >= 8 |
| OS | Linux（开发）/ Raspberry Pi（部署） |
| 硬件 | USB 监听网卡（仅非模拟模式需要，支持 monitor 模式） |

## 安装和运行

### 1. 安装系统依赖

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
# 通常是 wlan0 或 wlan1

# 关闭网卡
sudo ip link set wlan1 down

# 切换到 monitor 模式（创建 wlan1mon）
sudo iwconfig wlan1 mode monitor
# 或使用 airmon-ng
sudo airmon-ng start wlan1

# 确认 monitor 模式已启用
iwconfig wlan1mon
# 应该显示 Mode:Monitor
```

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

### 6. 启动系统

**开发模式（模拟器，无需监听网卡）：**

```bash
# 终端 1：启动后端
conda activate wifiguard
cd backend
pip install -r requirements.txt
python app.py
# Flask 运行在 http://localhost:8000

# 终端 2：启动前端
cd frontend
npm install
npm run dev
# Vite 运行在 http://localhost:3000
```

打开浏览器访问 `http://localhost:3000`，自动跳转到登录页面。

### 7. 用户认证

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

### 监听网卡模式

连接真实监听网卡后，关闭模拟模式：

```bash
# 1. 将网卡切换为 monitor 模式
sudo airmon-ng start wlan1

# 2. 设置环境变量
export WIFIGUARD_SIM=false
export WIFIGUARD_IFACE=wlan1mon

# 3. 启动后端
python app.py
```

此时检测引擎从模拟器切换到真实数据采集（具体采集逻辑在各 detector 的 `analyze()` 方法中实现）。

## 环境变量

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `WIFIGUARD_DB` | `backend/data/wifiguard.db` | SQLite 数据库路径 |
| `WIFIGUARD_IFACE` | `wlan1mon` | 监听网卡接口名 |
| `WIFIGUARD_SIM` | `true` | 模拟模式（`true`=无需网卡，`false`=真实监听） |
| `WIFIGUARD_INTERVAL` | `2` | 检测引擎轮询间隔（秒） |
| `WIFIGUARD_SMTP_HOST` | `smtp.qq.com` | 邮件 SMTP 服务器 |
| `WIFIGUARD_SMTP_PORT` | `465` | SMTP 端口 |

## 攻击演示脚本

这些脚本用于在真实网络环境中测试检测系统，**需要 root 权限和 monitor 模式网卡**。

所有攻击脚本**必须手动指定目标**，不会自动选择目标，避免误伤他人网络。

### 第一步：扫描

```bash
cd backend/attack_scripts

# 确保网卡处于 monitor 模式
sudo airmon-ng check kill
sudo airmon-ng start wlan1

# 扫描周围网络（10 秒），自动检测你的当前连接并给出推荐命令
sudo ./scan.sh wlan1mon
```

输出示例：

```
你的连接
  SSID : MyWiFi
  BSSID: 46:C3:E1:A9:01:7E

扫描到的 AP 列表
  BSSID              信道  SSID
  46:C3:E1:A9:01:7E    11  MyWiFi
  AA:BB:CC:DD:EE:03     6  NeighborWiFi

推荐命令
  sudo ./simulate_deauth.sh wlan1mon 46:C3:E1:A9:01:7E FF:FF:FF:FF:FF:FF
  sudo ./simulate_evil_twin.sh wlan1 "MyWiFi" 11
  ...
```

### 第二步：执行攻击

复制 `scan.sh` 输出的推荐命令执行，或自行拼接：

```bash
# Deauth 去认证攻击
#   参数: <monitor接口> <AP的MAC> <客户端MAC> [攻击次数]
sudo ./simulate_deauth.sh wlan1mon AA:BB:CC:DD:EE:03 DE:AD:BE:EF:00:01 50
# 广播去认证（踢掉所有客户端）用 FF:FF:FF:FF:FF:FF
sudo ./simulate_deauth.sh wlan1mon AA:BB:CC:DD:EE:03 FF:FF:FF:FF:FF:FF

# Evil Twin 钓鱼 AP
#   参数: <普通接口> <SSID> <信道>
sudo ./simulate_evil_twin.sh wlan1 "MyWiFi" 11

# Flood 泛洪攻击
#   参数: <monitor接口> <AP的MAC>
sudo ./simulate_flood.sh wlan1mon AA:BB:CC:DD:EE:03

# 暴力破解
#   参数: <monitor接口> <AP的MAC> [字典路径]
sudo ./simulate_brute_force.sh wlan1mon AA:BB:CC:DD:EE:03
sudo ./simulate_brute_force.sh wlan1mon AA:BB:CC:DD:EE:03 /path/to/rockyou.txt

# MAC 欺骗非法接入
#   参数: <普通接口> <伪造MAC地址>
sudo ./simulate_illegal.sh wlan1 DE:AD:BE:EF:00:01

# 一键完整演示（自动锁定你当前连接的 WiFi，执行前需按 Enter 确认）
sudo ./simulate_all.sh wlan1mon
```

**注意**：攻击脚本仅用于授权的安全测试和教育目的。在未授权网络上使用属于违法行为。

## 邮箱推送配置

支持 QQ 邮箱、163 邮箱、Gmail 的 SMTP 推送。

**QQ 邮箱示例：**
1. 登录 QQ 邮箱网页版 → 设置 → 账户
2. 找到 POP3/IMAP/SMTP 服务，开启 IMAP/SMTP
3. 按提示发送短信获取**授权码**（非邮箱密码）
4. 在 WiFiGuard 邮箱推送页面填写：
   - SMTP 服务器：`smtp.qq.com`
   - 端口：`465`
   - 发件邮箱：`your_email@qq.com`
   - 授权码：上一步获取的授权码
   - 收件邮箱：接收告警的邮箱
5. 点击"测试连接"验证配置

## 生产部署

### 树莓派部署

```bash
# 1. 构建前端
cd frontend && npm run build

# 2. 将 dist/ 复制到后端
cp -r dist ../backend/

# 3. 修改 app.py 添加静态文件服务
# 或使用 nginx 反向代理：
#   - Flask 监听 127.0.0.1:8000
#   - nginx 代理 /api 到 Flask，/ 到 dist/

# 4. 使用 systemd 管理服务（可选）
sudo cat > /etc/systemd/system/wifiguard.service << 'EOF'
[Unit]
Description=WiFiGuard Backend
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/WiFiGuard/backend
Environment="WIFIGUARD_SIM=false"
Environment="WIFIGUARD_IFACE=wlan1mon"
ExecStart=/home/pi/.conda/envs/wifiguard/bin/python app.py
Restart=on-failure

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl enable wifiguard
sudo systemctl start wifiguard
```

## 常见问题

**Q: 启动后端时告警数量翻倍？**
A: Flask debug 模式的 reloader 会 fork 子进程，导致检测引擎运行两次。`app.py` 已设置 `use_reloader=False`。如果手动改为 `True` 会出现此问题。

**Q: monitor 模式切换失败（`SET failed: Device or resource busy`）？**
A: 网卡正被 NetworkManager 占用。先执行 `sudo airmon-ng check kill` 关闭干扰进程，再切换模式。重启后自动恢复。

**Q: `aireplay-ng: command not found`？**
A: 未安装 aircrack-ng 套件，参见上方系统依赖安装部分。
