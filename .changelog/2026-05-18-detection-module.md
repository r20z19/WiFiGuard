h# 2026-05-18 — 实现基于真实数据包的检测模块

## 概述

基于 `test/testcase/` 中的真实 Wi-Fi 抓包数据（global-01.cap、handshake-01.cap），完整实现了 7 种攻击检测器。检测器通过滑动时间窗口分析 802.11 帧，当超过阈值时产生告警。支持三种运行模式：Simulation、Pcap 重放、Live 监控。

### 数据包分析

#### global-01.cap（266 秒，35,367 个数据包）

| 帧类型 | 数量 | 说明 |
|---|---|---|
| Deauth | 11,408 | 来自 `b4:77:48:58:38:a3` 的去认证泛洪攻击 |
| Probe Response | 3,018 | 单秒内最高 1,259 个（泛洪攻击） |
| Auth | 39 | 3 个不同客户端 MAC 尝试认证 |
| EAPOL M1/M2/M3/M4 | 136/6/250/4 | WPA 四次握手 |
| Beacon | 1 | SSID `525a`，BSSID `b4:77:48:58:38:a3` |
| 关联请求 | 14 | 客户端关联尝试 |

**安全配置**：WPA2-AES (CCMP) + PSK，RSN 版本 1，不涉及 TKIP/WEP。

#### handshake-01.cap（24 秒，12,143 个数据包）

| 帧类型 | 数量 | 说明 |
|---|---|---|
| Deauth | 11,302 | 去认证泛洪 |
| Probe Response | 138 | 探测响应 |
| Auth | 9 | 来自 `38:d5:7a:87:bb:0b` 的认证尝试 |
| EAPOL M1/M2/M3/M4 | 126/2/246/0 | WPA 握手捕获 |

---

## 新增文件

### `backend/detection/packet_reader.py`

802.11 pcap 文件读取器，通过 `tshark` 子进程读取 pcap 文件，解析每一帧为字典结构。

**提取的 tshark 字段**（8 个已验证可用字段）：
- `wlan.fc.type_subtype` — 帧类型/子类型（十六进制）
- `wlan.sa` / `wlan.da` — 源/目标 MAC 地址
- `wlan.bssid` — BSSID
- `wlan.ssid` — SSID（十六进制编码）
- `frame.time` — 微秒精度时间戳
- `radiotap.dbm_antsignal` — RSSI 信号强度 (dBm)
- `_ws.col.Info` — 人类可读的帧摘要（用于检测 EAPOL 密钥消息、认证状态等）

**安全信息提取**：`get_beacon_security_info()` 对第一个信标帧运行 `tshark -V`，通过正则表达式提取：
- RSN 版本
- 组播密码套件（AES / TKIP / WEP）
- 成对密码套件
- AKM 套件（PSK 等）
- 是否使用 WPA1 / 是否使用 TKIP / 是否使用 WEP

**常量定义**：
- WLAN 帧类型：`FC_DEAUTH`、`FC_AUTH`、`FC_BEACON`、`FC_PROBE_RESP`、`FC_ASSOC_REQ` 等
- EAPOL 密钥消息模式：Message 1/2/3/4 of 4
- 密码套件类型：WEP-40、TKIP、AES-CCMP、WEP-104

### `test/test_detection.py`

独立测试脚本，遍历帧块并调用全部 7 个检测器，报告每个捕获文件的告警数量，根据已知 pcap 内容验证预期结果。

用法：
```bash
conda run -n wifiguard python test/test_detection.py           # 默认：global-01.cap
conda run -n wifiguard python test/test_detection.py --all     # 两个捕获文件都测
conda run -n wifiguard python test/test_detection.py --pcap <path>
```

---

## 修改文件

### `backend/detection/base.py`

- `analyze()` 签名从 `analyze(self, devices)` 改为 `analyze(self, frames)` — 现在接收帧字典列表
- 新增 `reset()` 方法，供有状态检测器实现

### `backend/detection/deauth.py` — Deauth 泛洪检测

**攻击原理**：攻击者发送大量去认证帧（802.11 管理帧，类型 0x000c），强制客户端断开连接。常用工具：MDK4、aireplay-ng。

**检测逻辑**：
- 按源 MAC 维护去认证帧时间戳的滑动窗口（10 秒，阈值 = 30 帧）
- 告警后清空该 MAC 的计数器
- 60 秒冷却时间：同一 MAC 在冷却期内不会重复告警

**真实数据验证**：global-01.cap 中有 11,408 个去认证帧，来自 `b4:77:48:58:38:a3`（AP MAC 被欺骗）。在 10 秒窗口内触发达 512-638 帧，远超阈值。检测器告警 1 次后正确进入冷却。

### `backend/detection/flood.py` — 管理帧泛洪检测

**攻击原理**：攻击者用探测响应或信标帧淹没无线信道，消耗信道资源。常见工具：MDK4 beacon flood mode。

**检测逻辑**：
- 两个并行滑动窗口（1 秒）：
  - 探测响应计数器：同一源 MAC 每秒 >100 个探测响应
  - 管理帧计数器：同一源 MAC 每秒 >200 个信标+探测响应
- 排除去认证帧（由 DeauthDetector 单独处理）
- 60 秒冷却时间

**真实数据验证**：global-01.cap 有 3,018 个探测响应，1,259 个集中在一个秒桶内，来自 `b4:77:48:58:38:a3`。检测器告警 1 次。

### `backend/detection/brute_force.py` — 暴力破解检测

**攻击原理**：攻击者反复发送认证帧尝试猜测 WiFi 密码（在线字典攻击）。

**检测逻辑**：
- 按客户端 MAC 统计认证帧，30 秒滑动窗口，阈值 = 5 次
- 过滤掉来自已知 AP MAC 的帧（AP 发送认证响应，不是攻击）
- `set_ap_macs()` 方法由引擎调用，传入信标发送者 MAC 集合
- 60 秒冷却时间

**真实数据验证**：global-01.cap 共 39 个认证帧。客户端 `38:d5:7a:87:bb:0b` 发送 6 次认证。AP `b4:77:48:58:38:a3` 的 26 个认证帧被正确过滤（是响应而非攻击）。检测器告警 1 次。

### `backend/detection/evil_twin.py` — 钓鱼 AP 检测

**攻击原理**：攻击者创建与合法网络 SSID 完全相同的伪造 AP，诱骗客户端连接以窃取凭据。

**检测逻辑**：
- 从信标和探测响应帧中维护 `(SSID) → {BSSID 集合}` 映射表
- 当同一 SSID 被 ≥2 个不同 BSSID 广播时触发告警
- 去重：每个 SSID 只告警一次

**真实数据验证**：两个捕获文件中都只有 1 个 SSID（`525a`）和 1 个 BSSID（`b4:77:48:58:38:a3`）。未检测到钓鱼 AP（正确）。

### `backend/detection/illegal_access.py` — 非法接入检测

**攻击原理**：未经授权的设备通过认证或关联帧尝试连接到网络。

**检测逻辑**：
- 跟踪未知 MAC 地址的认证帧和关联请求帧
- 第 2 次尝试时告警（避免因单次探测产生误报）
- 通过 `set_known_macs()` 可预先填入合法 MAC
- 通过 `set_ap_macs()` 排除 AP MAC

**真实数据验证**：检测到 3 个客户端 MAC（`38:d5:7a:87:bb:0b`、`46:69:ba:0d:50:f6`、`4a:8a:5f:7c:30:d6`）各触发 1 次告警，共 3 次。

### `backend/detection/weak_password.py` — 弱口令检测

**攻击原理**：使用默认/弱密码或弱加密的网络，攻击者可通过捕获 WPA 握手包后进行离线字典攻击（aircrack-ng、hashcat）。

**检测逻辑**：
- 在帧信息中检测不安全加密协议（WEP、WPA1）
- 将 SSID 与常见弱/默认模式匹配（TP-LINK、D-Link、NETGEAR、CMCC、admin 等）
- 仅检查一次（`_beacon_checked` 标志），避免重复告警

**真实数据验证**：网络使用 WPA2-AES (CCMP) 加密，SSID `525a` 不匹配已知弱模式。未产生告警（正确）。

### `backend/detection/krack.py` — KRACK 漏洞检测

**攻击原理**：使用 WPA2-TKIP 或 WPA1 的网络存在密钥重装攻击（KRACK - Key Reinstallation Attack）漏洞。WEP 已被完全破解。

**检测逻辑**：
- 扫描帧信息中是否包含 "TKIP"、"WEP" 或 "WPA Version" 字样
- 检测到任意一个时告警
- 仅检查一次，避免重复告警

**真实数据验证**：网络使用 WPA2-AES (CCMP)，不涉及 TKIP 或 WEP。未产生告警（正确）。

### `backend/detection/engine.py` — 检测引擎更新

新增 **Pcap 重放模式**，作为第三种运行模式：

| 模式 | 触发条件 | 行为 |
|---|---|---|
| Pcap 重放 | 设置 `WIFIGUARD_PCAP` 环境变量 | 从 pcap 加载帧，分批送入检测器 |
| Simulation | `WIFIGUARD_SIM=true`（默认），未设置 pcap | 使用 SimulatorDataGenerator 生成虚拟设备和攻击 |
| 仅检测器 | simulation=false，未设置 pcap | 检测器处理在线设备数据 |

**Pcap 重放工作流**：
1. `start()` — 检测 pcap 路径，加载全部帧到内存
2. `_configure_detectors_for_pcap()` — 通过信标帧发现 AP MAC，调用检测器的 `set_ap_macs()`
3. `_tick_pcap()` — 每个检测间隔，按平均包速率（~132 包/秒 × 检测间隔）将下一批帧送入全部检测器
4. 循环重放：到达末尾后从索引 0 重新开始

### `backend/config.py`

新增配置项：
- `PCAP_FILE_PATHS` — 逗号分隔的 pcap 文件路径，由 `WIFIGUARD_PCAP` 环境变量控制

---

## 检测结果汇总

### global-01.cap

| 攻击类型 | 告警数 | 正确性 | 源 MAC |
|---|---|---|---|
| Deauth 攻击 | 1 | ✓ | `b4:77:48:58:38:a3` |
| Flood 泛洪 | 1 | ✓ | `b4:77:48:58:38:a3` |
| 暴力破解 | 1 | ✓ | `38:d5:7a:87:bb:0b` |
| 钓鱼 AP | 0 | ✓ | — |
| 非法接入 | 3 | ✓ | `38:...:0b`, `46:...:f6`, `4a:...:d6` |
| 弱口令 | 0 | ✓ | — |
| KRACK 风险 | 0 | ✓ | — |
| **总计** | **6** | | |

### handshake-01.cap

| 攻击类型 | 告警数 | 正确性 | 源 MAC |
|---|---|---|---|
| Deauth 攻击 | 1 | ✓ | `b4:77:48:58:38:a3` |
| Flood 泛洪 | 1 | ✓ | `b4:77:48:58:38:a3` |
| 暴力破解 | 1 | ✓ | `38:d5:7a:87:bb:0b` |
| 钓鱼 AP | 0 | ✓ | — |
| 非法接入 | 1 | ✓ | `38:d5:7a:87:bb:0b` |
| 弱口令 | 0 | ✓ | — |
| KRACK 风险 | 0 | ✓ | — |
| **总计** | **4** | | |

---

## 设计决策

- **零外部依赖**：数据包读取完全通过系统自带的 `tshark` 子进程实现，不需要 pyshark 或 scapy
- **有状态检测器**：每个检测器维护内部滑动窗口，支持跨检测周期累积数据以实现准确的攻击模式识别
- **冷却机制**：Deauth 和 BruteForce 检测器包含冷却定时器，防止同一攻击者的重复告警淹没用户界面
- **AP 感知**：引擎自动从信标帧发现 AP MAC 地址，并通过 `set_ap_macs()` 传递给检测器，避免将 AP 合法行为（如认证响应）误判为攻击
- **帧信息解析**：使用 `_ws.col.Info` 字段进行 EAPOL/加密检测，避免依赖不可用的 tshark 树字段名（该版本 tshark 中 `wlan_mgt.rsn.*` 字段不可用）
- **向后兼容**：现有 Simulation 模式不受影响；未设置 `WIFIGUARD_PCAP` 环境变量时，引擎行为与之前完全一致

## 使用方式

```bash
# 运行检测测试
conda run -n wifiguard python test/test_detection.py --all

# 在 pcap 模式下启动后端
WIFIGUARD_SIM=false WIFIGUARD_PCAP=test/testcase/global-01.cap python app.py

# 使用多个 pcap 文件
WIFIGUARD_SIM=false WIFIGUARD_PCAP=test/testcase/global-01.cap,test/testcase/handshake-01.cap python app.py
```
