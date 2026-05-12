# WiFi 审计助手

基于 `aircrack-ng` 的多阶段自动化 WiFi 审计脚本，适用于 Kali Linux。

## 前置准备

1. **插入 USB 无线网卡**（需支持 monitor 模式，如 MT7601U / RTL8812AU 等）
2. **安装 aircrack-ng 套件**（Kali 默认已装，若缺失则手动安装）：

```bash
sudo apt update && sudo apt install -y aircrack-ng
```

3. **以 root 运行**：

```bash
sudo python3 wifi_attack.py
```

## 阶段说明

| 阶段 | 功能 | 说明 |
|------|------|------|
| 1 | 检查环境 | 验证 aircrack-ng 套件是否完整 |
| 2 | 启用监控模式 | `airmon-ng start`，执行后 `iwconfig` 确认 Mode:Monitor |
| 3 | 扫描目标 AP | `airodump-ng` 扫描，手动输入 BSSID/信道/ESSID |
| 4 | 抓握手包 | 弹两个终端：airodump-ng 监听 + aireplay-ng deauth 踢客户端，出现 `[WPA handshake]` 后按 Enter |
| 5 | 手动 Deauth | 弹新终端执行 `aireplay-ng -0 0`，用于补刀 |
| 6 | 字典爆破 | 弹新终端执行 `aircrack-ng -w` 破解握手包 |
| 7 | 钓鱼 AP | `airbase-ng` 创建同名虚假 AP（Evil Twin） |
| 8 | WiFi 泛洪 | `mdk4` 三种泛洪（deauth/beacon/probe） |
| 9 | 清理关闭 | 停止全局抓包、关闭监控模式、恢复网络服务 |

## 特性

- **全局后台抓包**：阶段 3 选定目标后自动启动，全程抓取该信道所有流量，程序退出才停止
- **多终端并行**：抓包、deauth、爆破、钓鱼、泛洪均在新终端窗口中执行，互不阻塞
- **参数持久化**：输入的网卡名、BSSID、信道、字典路径等自动保存到 `~/.wifi_attack_config.json`，下次运行直接回车确认
- **全自动模式**：`[A]` 一键执行 1→2→3→4→5→6→7→8→9，每阶段可后退/跳回菜单
- **单步执行**：独立选择任意阶段，完成后返回菜单

## 使用流程

```text
1. 插网卡 → sudo python3 wifi_attack.py
2. [2] 启用监控模式 → 输入网卡名
3. [3] 扫描 → 选目标 → 输入 BSSID / CH / ESSID
4. [4] 抓握手包 → 等终端出现 [WPA handshake] → Enter
5. [6] 字典爆破 → 弹终端跑 aircrack-ng
6. [7] 钓鱼 AP → 弹终端跑 airbase-ng
7. [8] WiFi 泛洪 → 弹终端跑 mdk4
8. [9] 清理关闭
```

## 文件说明

| 文件 | 用途 |
|------|------|
| `wifi_attack.py` | 主脚本 |
| `~/.wifi_attack_config.json` | 持久化参数配置 |
| `/tmp/global_capture/` | 全局抓包保存目录（可自定义） |
| `/tmp/handshake/` | 握手包保存目录（可自定义） |

## 注意事项

- 必须 **root** 权限运行
- 无线网卡必须支持 **monitor 模式**
- 抓握手包时需要目标 AP 有在线客户端（否则 deauth 无效）
- `mdk4` 在首次使用阶段 8 时会自动 `apt install`
