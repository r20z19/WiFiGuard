# WiFiGuard 前端 - 安装说明

## 问题原因
当前IDE的沙箱环境存在WSL路径兼容性问题，需要通过WSL终端直接执行安装命令。

## 解决方案

请在你的 **WSL终端** 中依次执行以下命令：

```bash
# 1. 进入项目目录
cd /home/derder/wifi_security/frontend

# 2. 清理旧的依赖（如果存在）
rm -rf node_modules package-lock.json

# 3. 安装依赖
npm install

# 4. 启动开发服务器
npm run dev
```

## 如果遇到 esbuild 安装问题

如果 `npm install` 仍然失败，可以尝试以下替代方案：

### 方案1：使用 yarn
```bash
# 安装 yarn
npm install -g yarn

# 使用 yarn 安装依赖
yarn install

# 启动开发服务器
yarn dev
```

### 方案2：使用 pnpm
```bash
# 安装 pnpm
npm install -g pnpm

# 使用 pnpm 安装依赖
pnpm install

# 启动开发服务器
pnpm dev
```

### 方案3：跳过 esbuild 可选依赖
```bash
npm install --ignore-scripts
npm rebuild esbuild
npm run dev
```

## 成功后访问

启动成功后，在浏览器访问：
- http://localhost:3000

## 完整的功能模块

✅ 系统概览 - 状态卡片、告警统计、安全建议
✅ 当前告警 - 实时告警列表、处理建议
✅ 历史告警 - 筛选、分页、详情查看
✅ 在线设备 - 信号强度、状态监控
✅ 设备白名单 - 添加/编辑/移除
✅ 设备黑名单 - 添加/编辑/移除
✅ 邮箱推送 - SMTP配置、授权码、推送记录
