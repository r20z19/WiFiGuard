# 2026-05-27 — 实现 Live 监控模式（真实网卡实时抓包检测）

## 概述

在 Simulation 和 Pcap 重放模式之外，新增第三种运行模式：**Live 监控模式**。通过 USB 无线网卡（Ralink MT7601U）的监听模式（Monitor Mode），使用 tshark 实时抓取 802.11 帧，送入 7 个检测器进行实时攻击检测。

此前 `_tick_detectors_only()` 路径向检测器传递的是 SQLite 设备记录（仅有 mac/ip/ssid/signal 等字段），而检测器需要帧级别的 `frameType`/`sa`/`da`/`bssid`/`info` 字段，导致所有检测器静默返回 None，Live 模式完全不可用。

## 修改文件

### `backend/detection/packet_reader.py`

- `TSHARK_FIELDS` 和 `_parse_tshark_line()` 提取为模块级常量/函数，供 `PacketReader` 和新类 `LivePacketCapture` 共享
- 新增 `LivePacketCapture` 类：
  - `start()` 启动 `tshark -i <iface>` 子进程后台抓包
  - daemon 线程持续读取 stdout，解析帧并放入 `queue.Queue` 缓冲区
  - `drain_frames()` 非阻塞排空缓冲区，返回帧列表
  - `stop()` 终止 tshark 子进程（先 terminate，5s 超时后 kill）

### `backend/detection/engine.py`

- 新增 `_live_capture` 属性和 `_tick_live()` 方法
- `start()` 中当 `SIMULATION_MODE=false` 且未设置 pcap 时，初始化 `LivePacketCapture`
- `_run_loop()` 中新增 `elif self._live_capture` 分支
- `stop()` 中清理 live capture 子进程
- 初始化失败时打印警告并回退到 `_tick_detectors_only()`

### `backend/config.py`

- 为 `MONITOR_INTERFACE` 和 `SIMULATION_MODE` 添加文档注释

## 新增文件

### `backend/scripts/setup_monitor.sh`

将无线网卡切换为监听模式的辅助脚本：

```bash
sudo ./backend/scripts/setup_monitor.sh [interface]
```

## 使用方式

```bash
# 1. 启用监听模式
sudo ./backend/scripts/setup_monitor.sh wlp0s20f0u1

# 2. 启动 Live 模式后端
WIFIGUARD_SIM=false WIFIGUARD_IFACE=wlp0s20f0u1 python app.py
```

## 验证结果

在 Live 模式下运行，已成功从环境 WiFi 流量中检测到真实告警：
- **暴力破解**：MAC `b0:47:e9:e5:4d:45` 向 `de:5e:8a:36:14:46` 发送大量认证帧
- **非法接入**：同一源 MAC 尝试未授权网络接入

## 设计决策

- **线程安全**：使用 `queue.Queue` 作为帧缓冲区，reader 线程写入，engine tick 线程排空
- **零新依赖**：Live 抓包完全通过系统自带的 `tshark -i` 实现，与 Pcap 模式共享解析逻辑
- **非阻塞排空**：`drain_frames()` 不等待数据，每次 tick 排空当前所有缓冲帧，由 `DETECTION_INTERVAL`（默认 2s）自然控制批处理粒度
- **优雅降级**：tshark 进程意外退出或接口不可用时，reader 线程静默退出，不导致引擎崩溃
