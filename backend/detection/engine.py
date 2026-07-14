import threading
import time

from config import (
    DETECTION_INTERVAL,
    LIVE_LOG_INTERVAL,
    MONITOR_INTERFACE,
    PCAP_FILE_PATHS,
    SIMULATION_MODE,
    TARGET_SSID,
    TARGET_BSSID,
)
from services.alert_service import create_alert
from services.device_service import bulk_upsert, remove_stale_devices
from services.whitelist_service import is_whitelisted
from services.email_service import send_alert, get_config
from services.access_control_service import AccessController
from detection.packet_reader import (
    FC_BEACON,
    FC_PROBE_REQ,
    FC_PROBE_RESP,
    PacketReader,
)
from config import TARGET_SSID as _TARGET_SSID
from utils.time_utils import now_str
from utils.oui_db import lookup_vendor
from utils.mac_utils import is_multicast_mac


class DetectionEngine:

    def __init__(self):
        self._running = False
        self._thread = None
        self._simulator = None
        self._detectors = []
        self._pcap_frames = []
        self._pcap_frame_index = 0
        self._live_capture = None
        self._target_bssids = {TARGET_BSSID} if TARGET_BSSID else set()
        self._observed_ap_macs = set()
        self._tick_live_empty_count = 0
        self._live_log_frame_count = 0
        self._live_log_last_time = time.time()
        self._access_controller = AccessController()
        self._load_detectors()

    def _load_detectors(self):
        from detection.deauth import DeauthDetector
        from detection.evil_twin import EvilTwinDetector
        from detection.flood import FloodDetector
        from detection.brute_force import BruteForceDetector
        from detection.illegal_access import IllegalAccessDetector
        from detection.weak_password import WeakPasswordDetector
        from detection.weak_encryption import WeakEncryptionDetector
        from detection.krack import KrackDetector

        self._detectors = [
            DeauthDetector(),
            EvilTwinDetector(),
            FloodDetector(),
            BruteForceDetector(),
            IllegalAccessDetector(),
            WeakPasswordDetector(),
            WeakEncryptionDetector(),
            KrackDetector(),
        ]

    def start(self):
        pcap_paths = self._get_pcap_paths()

        if pcap_paths:
            print("[*] PCAP回放模式")
            self._load_pcap_frames(pcap_paths)
            self._configure_detectors_for_pcap()
        elif SIMULATION_MODE:
            print("[*] 模拟模式")
            from detection.simulator import SimulatorDataGenerator
            self._simulator = SimulatorDataGenerator()
        else:
            print("[*] 真实监听模式 - 接口: {}".format(MONITOR_INTERFACE))
            if TARGET_SSID:
                self._lock_target_channel(MONITOR_INTERFACE, TARGET_SSID)
            try:
                from detection.packet_reader import LivePacketCapture
                self._live_capture = LivePacketCapture(MONITOR_INTERFACE)
                self._live_capture.start()
            except Exception as e:
                print("[!] 启动监听失败: {}".format(e))

        self._running = True
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()

    def _lock_target_channel(self, interface, ssid):
        import shutil as _shutil
        import os as _os
        import subprocess as _sp
        import time as _time

        airodump = _shutil.which("airodump-ng")
        if not airodump:
            return

        print("[*] 正在扫描 {} 的信道...".format(ssid))
        channel = self._do_airodump_scan(airodump, interface, ssid, 4)

        if not channel:
            for ch in ("1", "6", "11"):
                print("[*] 尝试信道 {}...".format(ch))
                _sp.run(
                    ["iw", "dev", interface, "set", "channel", ch],
                    capture_output=True, timeout=3,
                )
                channel = self._do_airodump_scan(airodump, interface, ssid, 2)
                if channel:
                    break

        if channel and channel.isdigit():
            print("[*] 目标 SSID {} 在信道 {}，锁定...".format(ssid, channel))
            _sp.run(
                ["iw", "dev", interface, "set", "channel", channel],
                capture_output=True, timeout=5,
            )
        else:
            print("[!] 未找到目标 SSID {} 的信道，使用当前信道".format(ssid))

    def _do_airodump_scan(self, airodump, interface, target, duration):
        import subprocess as _sp
        import os as _os
        import time as _time
        tmp = "/tmp/wifiguard-channel-scan"
        proc = _sp.Popen(
            [airodump, "--output-format", "csv", "-w", tmp, interface],
            stdout=_sp.DEVNULL, stderr=_sp.DEVNULL, start_new_session=True,
        )
        _time.sleep(duration)
        try:
            proc.terminate()
            proc.wait(timeout=4)
        except _sp.TimeoutExpired:
            proc.kill()

        csv_path = tmp + "-01.csv"
        channel = None
        try:
            with open(csv_path, "r", errors="ignore") as f:
                for line in f:
                    if target in line and "Station MAC" not in line:
                        parts = line.split(",")
                        if len(parts) >= 4:
                            channel = parts[3].strip()
                            break
        except OSError:
            pass
        finally:
            for p in [csv_path, tmp + "-01.kismet.csv", tmp + "-01.log.csv"]:
                try:
                    _os.unlink(p)
                except OSError:
                    pass
        return channel

        return bool(TARGET_SSID or TARGET_BSSID)

    def _get_pcap_paths(self):
        if not PCAP_FILE_PATHS:
            return []
        return [p.strip() for p in PCAP_FILE_PATHS.split(",") if p.strip()]

    def _load_pcap_frames(self, pcap_paths):
        for path in pcap_paths:
            try:
                reader = PacketReader(path)
                frames = list(reader.read_frames())
                self._pcap_frames.extend(frames)
            except FileNotFoundError:
                pass

    def _configure_detectors_for_pcap(self):
        ap_macs = set()
        for f in self._pcap_frames:
            if f["frameType"] == FC_BEACON:
                bssid = f.get("bssid", "") or f.get("sa", "")
                if bssid:
                    ap_macs.add(bssid)

        for detector in self._detectors:
            if hasattr(detector, "set_ap_macs"):
                detector.set_ap_macs(ap_macs)

    def stop(self):
        self._running = False
        if self._live_capture:
            self._live_capture.stop()

    def _run_loop(self):
        while self._running:
            try:
                if self._pcap_frames:
                    self._tick_pcap()
                elif self._simulator:
                    self._tick_simulation()
                elif self._live_capture:
                    self._tick_live()
                else:
                    self._tick_detectors_only()

                remove_stale_devices(120)
                time.sleep(DETECTION_INTERVAL)
            except Exception as e:
                print("[!] 检测循环异常: {}".format(e))
                time.sleep(DETECTION_INTERVAL)

    def _target_configured(self):
        return bool(TARGET_SSID or TARGET_BSSID)

    def _filter_frames_by_target(self, frames):
        if TARGET_BSSID:
            self._target_bssids.add(TARGET_BSSID)

        if TARGET_SSID:
            for f in frames:
                ft = f["frameType"]
                if ft in (FC_BEACON, FC_PROBE_RESP):
                    ssid = f.get("ssid", "").strip()
                    bssid = f.get("bssid", "") or f.get("sa", "")
                    if ssid == TARGET_SSID and bssid:
                        self._target_bssids.add(bssid)

        if not self._target_configured():
            return frames
        if not self._target_bssids:
            return []

        filtered = []
        for f in frames:
            ft = f["frameType"]
            bssid = (f.get("bssid") or "").strip()

            if bssid in self._target_bssids:
                filtered.append(f)
                continue

            probe_req_types = (FC_PROBE_REQ,)
            if ft in probe_req_types:
                continue

            da = (f.get("da") or "").strip()
            if da in self._target_bssids:
                filtered.append(f)

        return filtered

    def _infer_target_from_frames(self, frames):
        if self._target_configured() or self._target_bssids:
            return
        candidates = {}
        for f in frames:
            if f["frameType"] not in (FC_BEACON, FC_PROBE_RESP):
                continue
            ssid = (f.get("ssid") or "").strip()
            bssid = f.get("bssid", "") or f.get("sa", "")
            signal = f.get("signal")
            if not ssid or not bssid:
                continue
            best = candidates.get(ssid)
            if not best or (signal is not None and signal > best["signal"]):
                candidates[ssid] = {"bssid": bssid, "signal": signal or -100}
        if len(candidates) == 1:
            bssid = next(iter(candidates.values()))["bssid"]
            self._target_bssids.add(bssid)
            print("[*] 未配置 WIFIGUARD_NAME，临时锁定唯一SSID的BSSID: {}".format(bssid))

    def _refresh_detector_ap_macs(self, frames):
        changed = False
        for f in frames:
            if f["frameType"] not in (FC_BEACON, FC_PROBE_RESP):
                continue
            bssid = f.get("bssid", "") or f.get("sa", "")
            if bssid and bssid not in self._observed_ap_macs:
                self._observed_ap_macs.add(bssid)
                changed = True

        if not changed:
            self._sync_detector_context()
            return

        self._sync_detector_context()

    def _sync_detector_context(self):
        for detector in self._detectors:
            if hasattr(detector, "set_ap_macs"):
                detector.set_ap_macs(self._observed_ap_macs)
            if hasattr(detector, "set_target_bssids"):
                detector.set_target_bssids(self._target_bssids)

    def _extract_devices_from_frames(self, frames):
        seen = {}
        now = now_str()
        for f in frames:
            mac = f.get("sa", "")
            bssid = f.get("bssid", "")
            da = f.get("da", "")
            ssid = f.get("ssid", "")
            signal = f.get("signal")
            frame_ip = f.get("ip", "")
            pc = f.get("pairwiseCipher", "")
            gc = f.get("groupCipher", "")
            akm = f.get("akm", "")

            candidate_addrs = [mac]
            if da and not da.startswith("ff:") and ":" in da:
                candidate_addrs.append(da)
            if bssid and f["frameType"] in (FC_BEACON, FC_PROBE_RESP):
                candidate_addrs.append(bssid)

            for addr in candidate_addrs:
                if not addr or addr in seen:
                    continue
                if addr == "00:00:00:00:00:00" or addr.startswith("ff:ff:ff:ff"):
                    continue
                if is_multicast_mac(addr):
                    continue
                if addr in self._target_bssids and f["frameType"] not in (FC_BEACON, FC_PROBE_RESP):
                    continue
                status = "正常"
                if signal is not None and signal < -75:
                    status = "可疑"
                vendor = lookup_vendor(addr)
                entry = seen[addr] = seen.get(addr, {
                    "mac": addr,
                    "ip": "",
                    "ssid": "",
                    "signal": signal if signal is not None else -70,
                    "status": status,
                    "vendor": vendor,
                    "pairwiseCipher": pc,
                    "groupCipher": gc,
                    "akm": akm,
                    "bssid": bssid,
                    "first_seen": now,
                    "last_seen": now,
                })
                if ssid and not entry["ssid"]:
                    entry["ssid"] = ssid
                elif not entry["ssid"] and _TARGET_SSID:
                    entry["ssid"] = _TARGET_SSID
                if frame_ip and not entry["ip"]:
                    entry["ip"] = frame_ip
                if pc and not entry["pairwiseCipher"]:
                    entry["pairwiseCipher"] = pc
                if gc and not entry["groupCipher"]:
                    entry["groupCipher"] = gc
                if akm and not entry["akm"]:
                    entry["akm"] = akm
        devices = list(seen.values())
        if devices:
            bulk_upsert(devices)
            self._access_controller.enforce(devices, self._target_bssids, scan_all=True)

    def _tick_simulation(self):
        devices = self._simulator.tick()
        if TARGET_SSID:
            devices = [d for d in devices if d.get("ssid") == TARGET_SSID]
        bulk_upsert(devices)
        attacks = self._simulator.get_attacks()
        if attacks:
            print("[检测] 仿真模式下检测到攻击: {}".format([a.get("type") for a in attacks]))
        for attack in attacks:
            source = attack.get("sourceMac", attack.get("source_mac", ""))
            if source and is_whitelisted(source):
                print("[检测] 源MAC {} 在白名单中，跳过告警".format(source))
                continue
            create_alert(attack)
            self._maybe_send_email(attack)

    def _tick_pcap(self):
        chunk_size = DETECTION_INTERVAL * 132
        start = self._pcap_frame_index
        end = min(start + chunk_size, len(self._pcap_frames))
        batch = self._pcap_frames[start:end]
        self._pcap_frame_index = end

        if not batch:
            return

        self._infer_target_from_frames(batch)
        batch = self._filter_frames_by_target(batch)
        if not batch:
            return

        self._refresh_detector_ap_macs(batch)
        self._extract_devices_from_frames(batch)

        for detector in self._detectors:
            try:
                result = detector.analyze(batch)
                if result:
                    print("[检测] {} 检测到: {}".format(
                        type(detector).__name__, result.get("type")))
                    source = result.get("sourceMac", result.get("source_mac", ""))
                    if source and is_whitelisted(source):
                        print("[检测] 源MAC {} 在白名单中，跳过".format(source))
                        continue
                    create_alert(result)
                    self._maybe_send_email(result)
            except Exception as e:
                print("[检测] {} 检测器错误: {}".format(
                    type(detector).__name__, e))

        if self._pcap_frame_index >= len(self._pcap_frames):
            self._pcap_frame_index = 0

    def _tick_detectors_only(self):
        pass

    def _tick_live(self):
        frames = self._live_capture.drain_frames()
        if not frames:
            self._tick_live_empty_count += 1
            if self._tick_live_empty_count == 15:
                print("[!] 已等待30秒未收到数据帧，请确认:")
                print("    1. 网卡 {} 是否已开启monitor模式?".format(MONITOR_INTERFACE))
                print("    2. 运行 sudo ./scripts/setup_monitor.sh {}".format(MONITOR_INTERFACE))
            return

        self._tick_live_empty_count = 0
        self._log_live_frames(len(frames))
        self._infer_target_from_frames(frames)
        frames = self._filter_frames_by_target(frames)
        if not frames:
            return

        self._refresh_detector_ap_macs(frames)
        self._extract_devices_from_frames(frames)

        for detector in self._detectors:
            try:
                result = detector.analyze(frames)
                if result:
                    print("[检测] {} 检测到: {}".format(
                        type(detector).__name__, result.get("type")))
                    source = result.get("sourceMac", result.get("source_mac", ""))
                    if source and is_whitelisted(source):
                        continue
                    create_alert(result)
                    self._maybe_send_email(result)
            except Exception as e:
                print("[检测] {} 检测器错误: {}".format(
                    type(detector).__name__, e))

    def _log_live_frames(self, frame_count):
        self._live_log_frame_count += frame_count
        now = time.time()
        elapsed = now - self._live_log_last_time
        if elapsed < LIVE_LOG_INTERVAL:
            return
        print("[*] 监听正常: 最近{}秒收到{}个数据帧".format(
            int(elapsed), self._live_log_frame_count
        ))
        self._live_log_frame_count = 0
        self._live_log_last_time = now

    def _maybe_send_email(self, alert):
        try:
            config = get_config()
            if config["enabled"]:
                send_alert(
                    alert_type=alert["type"],
                    severity=alert["severity"],
                    source_mac=str(alert.get("sourceMac", alert.get("source_mac", ""))),
                    target_mac=str(alert.get("targetMac", alert.get("target_mac", ""))),
                    timestamp=alert["timestamp"],
                    suggestion=alert.get("suggestion", ""),
                )
        except Exception as e:
            print(f"[Email] 发送失败: {e}")
