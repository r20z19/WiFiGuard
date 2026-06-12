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
