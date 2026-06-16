# 2026-05-18 — 登录页面增强：密码修改与新用户注册

## 概述

增强了登录页面的功能，修复了首次登录密码修改对话框不调用后端 API 的问题，新增了新用户注册功能，并将密码存储从纯 SHA-256 升级为 PBKDF2-HMAC-SHA256（带盐值）。

### 问题背景

1. 首次登录的"修改默认密码"对话框在 `Login.vue` 中只更新了本地 Pinia store 状态，从未调用 `POST /api/auth/change-password`，导致默认密码实际未被修改。
2. 系统仅支持单一默认管理员账户（`admin`），无用户注册流程。
3. 密码使用裸 SHA-256 哈希（无盐值），不符合现代安全标准。

---

## 修改文件

### `backend/services/auth_service.py`

**密码哈希升级为 PBKDF2**

- 新增常量 `PBKDF2_ITERATIONS = 600_000` 和 `PBKDF2_PREFIX = "$pbkdf2-sha256$"`
- `_hash_password(password)` 重写：使用 `hashlib.pbkdf2_hmac("sha256", ...)` + 16 字节随机盐，输出格式 `$pbkdf2-sha256$<iterations>$<salt_hex>$<hash_hex>`
- 新增 `_verify_password(password, stored_hash)`：自动识别存储格式
  - 新格式（以 `$pbkdf2-sha256$` 开头）：解析盐值和迭代次数，重新计算并比对
  - 旧格式（纯 SHA-256 十六进制）：使用旧算法比对，保证向后兼容
- `authenticate_user()` 和 `change_user_password()` 改为调用 `_verify_password()`

**新增用户注册函数**

- `register_user(username, password)` — 检查用户名唯一性，插入新用户（`is_first_login=1`），返回 JWT token

### `backend/routes/auth.py`

- 新增 `POST /api/auth/register` 端点
  - 接受 `{ "username": "...", "password": "..." }`
  - 校验：用户名 2-32 字符，密码至少 6 位
  - 成功返回 `{ "token": "<jwt>", "isFirstLogin": true }`（自动登录）
  - 用户名已存在返回 400 `{ "message": "用户名已存在" }`

### `backend/database.py`

- `_init_default_user()` 改为调用 `services.auth_service._hash_password()`（延迟导入避免循环依赖），默认管理员密码使用 PBKDF2 哈希存储

### `frontend/src/api/index.js`

- 新增 `register(data)` → `POST /api/auth/register`

### `frontend/src/store/auth.js`

- 新增 `register(credentials)` action：调用注册 API，成功后存储 token 和 userInfo
- 导出列表中新增 `register`

### `frontend/src/views/Login.vue`

**修复首次登录密码修改**

- `handleChangePassword()` 现在调用 `POST /api/auth/change-password` API（使用 `changePassword` from `../api/index`）
- 新增 `changingPwd` 加载状态，按钮添加 `:loading` 绑定
- 修改成功后清空表单字段并跳转到 Dashboard

**新增注册模式**

- 新增 `mode` ref（`'login'` / `'register'`），控制表单切换
- 登录表单添加 `v-if="mode === 'login'"`，注册表单添加 `v-else`
- 注册表单包含：用户名（2-32 字符）、密码（至少 6 位）、确认密码（一致性校验）
- `handleRegister()` 调用 `authStore.register()`，成功后显示首次登录密码修改对话框或直接跳转
- 表单底部新增 `.mode-switch` 区域：
  - 登录模式显示"没有账号？立即注册"
  - 注册模式显示"已有账号？返回登录"
- `switchMode()` 切换时清空所有表单字段

---

## 设计决策

- **PBKDF2 而非 bcrypt**：使用 stdlib `hashlib.pbkdf2_hmac` 避免在 Raspberry Pi 上编译 bcrypt 原生扩展，600,000 次迭代提供足够的暴力破解抵抗
- **向后兼容旧密码哈希**：`_verify_password()` 自动检测存储格式，已有用户无需迁移即可正常登录；登录后若修改密码则自动升级为 PBKDF2 格式
- **注册即登录**：注册成功后直接返回 JWT token，用户无需额外登录步骤
- **新用户 `is_first_login=1`**：新注册用户与默认 admin 一样，首次登录需修改密码
- **注册无权限控制**：注册端点无需管理员 token，允许任何人为系统创建账户（WiFiGuard 为内网部署工具）

---

## 使用方式

### 注册新用户

```bash
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username": "testuser", "password": "mypassword123"}'
```

### 前端操作

1. 打开 `http://localhost:3000/login`
2. 点击"立即注册"切换到注册表单
3. 填写用户名和密码后点击"注册"
4. 首次登录会弹出密码修改对话框，点击"确认修改"实际调用 API 修改密码

---

## 修复（同日更新）

### 401 拦截器导致登录失败时页面刷新

**问题**：`frontend/src/api/index.js` 的 401 响应拦截器在收到 401 状态码时无条件执行 `window.location.href = '/login'`。当登录接口因密码错误返回 401 时，用户已在 `/login` 页面，导致页面强制刷新、表单被清空，用户看不到错误提示。

**修复**：增加 `window.location.pathname !== '/login'` 判断，仅在非登录页的 401 响应时执行跳转。登录页的 401 错误正常传递给调用方，显示"用户名或密码错误"提示。

**修改文件**：`frontend/src/api/index.js`

### 注册提示优化

**问题**：注册已存在的用户名（如 `admin`）时仅显示"用户名已存在"。

**修复**：在 `authStore.register()` 中捕获该错误消息，映射为"该用户名已被注册，请直接登录"，引导用户切换到登录表单。

**修改文件**：`frontend/src/store/auth.js`
